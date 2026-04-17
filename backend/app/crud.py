from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models import Order, OrderItem, Product, User
from app.schemas import OrderCreate, ProductCreate, ProductUpdate, UserCreate


def create_user(db: Session, payload: UserCreate) -> User:
    normalized_email = payload.email.strip().lower()
    user = User(
        name=payload.name,
        email=normalized_email,
        hashed_password=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_user_by_email(db: Session, email: str) -> User | None:
    normalized_email = email.strip().lower()
    return db.scalar(select(User).where(User.email == normalized_email))


def create_product(db: Session, seller_id: int, payload: ProductCreate) -> Product:
    product = Product(seller_id=seller_id, **payload.model_dump())
    db.add(product)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise ValueError("SKU already exists for this seller") from exc
    db.refresh(product)
    return product


def list_products(
    db: Session,
    seller_id: int,
    search: str | None = None,
    include_archived: bool = False,
) -> list[Product]:
    stmt = select(Product).where(Product.seller_id == seller_id)
    if not include_archived:
        stmt = stmt.where(Product.is_active.is_(True))
    if search:
        pattern = f"%{search}%"
        stmt = stmt.where(
            or_(
                Product.title.ilike(pattern),
                Product.sku.ilike(pattern),
                Product.marketplace.ilike(pattern),
            )
        )
    stmt = stmt.order_by(Product.id.desc())
    return list(db.scalars(stmt).all())


def get_product(
    db: Session,
    seller_id: int,
    product_id: int,
    include_archived: bool = False,
) -> Product | None:
    stmt = select(Product).where(Product.seller_id == seller_id, Product.id == product_id)
    if not include_archived:
        stmt = stmt.where(Product.is_active.is_(True))
    return db.scalar(stmt)


def update_product(db: Session, product: Product, payload: ProductUpdate) -> Product:
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(product, field, value)
    db.add(product)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise ValueError("SKU already exists for this seller") from exc
    db.refresh(product)
    return product


def delete_product(db: Session, product: Product) -> None:
    product.is_active = False
    db.add(product)
    db.commit()


def get_dashboard_summary(db: Session, seller_id: int) -> dict:
    total_products = db.scalar(
        select(func.count())
        .select_from(Product)
        .where(Product.seller_id == seller_id, Product.is_active.is_(True))
    ) or 0
    low_stock_items = db.scalar(
        select(func.count())
        .select_from(Product)
        .where(Product.seller_id == seller_id, Product.is_active.is_(True), Product.stock < 10)
    ) or 0
    average_price = db.scalar(
        select(func.avg(Product.sell_price))
        .where(Product.seller_id == seller_id, Product.is_active.is_(True))
    ) or 0.0
    total_orders = db.scalar(
        select(func.count()).select_from(Order).where(Order.seller_id == seller_id)
    ) or 0
    total_sales = db.scalar(
        select(func.sum(Order.total_amount)).where(Order.seller_id == seller_id)
    ) or 0.0
    total_units_sold = db.scalar(
        select(func.sum(OrderItem.quantity))
        .join(Order, Order.id == OrderItem.order_id)
        .where(Order.seller_id == seller_id)
    ) or 0

    return {
        "total_products": int(total_products),
        "low_stock_items": int(low_stock_items),
        "average_price": round(float(average_price), 2),
        "total_orders": int(total_orders),
        "total_sales": round(float(total_sales), 2),
        "total_units_sold": int(total_units_sold),
    }


def create_order(db: Session, seller_id: int, payload: OrderCreate) -> Order:
    order = Order(
        seller_id=seller_id,
        order_number=payload.order_number,
        marketplace=payload.marketplace,
        total_amount=0.0,
    )
    db.add(order)
    db.flush()

    total = Decimal("0.00")
    for item in payload.items:
        product = get_product(db, seller_id=seller_id, product_id=item.product_id)
        if product is None:
            raise ValueError(f"Product {item.product_id} not found for this seller")

        unit_price = Decimal(str(item.unit_price)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        order_item = OrderItem(
            order_id=order.id,
            product_id=item.product_id,
            quantity=item.quantity,
            unit_price=unit_price,
        )
        total += Decimal(item.quantity) * unit_price
        db.add(order_item)

    order.total_amount = total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    db.add(order)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise ValueError("Order number already exists for this seller") from exc
    db.refresh(order)
    return order


def list_orders(db: Session, seller_id: int, search: str | None = None) -> list[Order]:
    stmt = select(Order).where(Order.seller_id == seller_id)
    if search:
        pattern = f"%{search}%"
        stmt = stmt.where(
            or_(
                Order.order_number.ilike(pattern),
                Order.marketplace.ilike(pattern),
            )
        )
    stmt = stmt.order_by(Order.id.desc())
    return list(db.scalars(stmt).all())


def get_dashboard_overview(db: Session, user: User) -> dict:
    products = list_products(db, seller_id=user.id)
    orders = list_orders(db, seller_id=user.id)

    marketplace_counts = defaultdict(lambda: {"listings": 0, "price_total": 0.0})
    listing_status = [{"label": "Active", "value": len(products)}] if products else []
    inventory_bands_map = {"Low stock": 0, "Watch list": 0, "Healthy": 0}
    order_by_product = defaultdict(lambda: {"revenue": 0.0, "units_sold": 0})
    recent_sales = []
    trend_map = defaultdict(lambda: {"revenue": 0.0, "units": 0})

    for product in products:
        bucket = marketplace_counts[product.marketplace]
        bucket["listings"] += 1
        bucket["price_total"] += float(product.sell_price)
        if product.stock <= 10:
            inventory_bands_map["Low stock"] += 1
        elif product.stock <= 50:
            inventory_bands_map["Watch list"] += 1
        else:
            inventory_bands_map["Healthy"] += 1

    for order in orders:
        units = sum(item.quantity for item in order.items)
        day = order.created_at.date().isoformat()
        trend_map[day]["revenue"] += float(order.total_amount)
        trend_map[day]["units"] += int(units)

        first_item = order.items[0] if order.items else None
        product_lookup = next((p for p in products if first_item and p.id == first_item.product_id), None)
        recent_sales.append(
            {
                "sale_date": order.created_at.isoformat(),
                "sku": product_lookup.sku if product_lookup else order.order_number,
                "title": product_lookup.title if product_lookup else order.marketplace,
                "units_sold": units,
                "revenue": round(float(order.total_amount), 2),
            }
        )

        for item in order.items:
            order_by_product[item.product_id]["units_sold"] += int(item.quantity)
            order_by_product[item.product_id]["revenue"] += float(item.quantity * item.unit_price)

    top_listings = []
    for product in products:
        perf = order_by_product[product.id]
        top_listings.append(
            {
                "sku": product.sku,
                "title": product.title,
                "marketplace": product.marketplace,
                "status": "active",
                "quantity": product.stock,
                "price": round(float(product.sell_price), 2),
                "competitor_low_price": None,
                "revenue": round(float(perf["revenue"]), 2),
                "units_sold": int(perf["units_sold"]),
            }
        )
    top_listings.sort(key=lambda item: (item["revenue"], item["units_sold"]), reverse=True)

    revenue_trend = [
        {"day": day, "revenue": round(float(data["revenue"]), 2), "units": int(data["units"])}
        for day, data in sorted(trend_map.items())[-14:]
    ]

    marketplace_mix = [
        {
            "marketplace": marketplace,
            "listings": int(data["listings"]),
            "avg_price": (
                round(float(data["price_total"]) / int(data["listings"]), 2)
                if int(data["listings"])
                else 0.0
            ),
        }
        for marketplace, data in sorted(
            marketplace_counts.items(),
            key=lambda item: int(item[1]["listings"]),
            reverse=True,
        )
    ]

    summary = get_dashboard_summary(db, seller_id=user.id)
    return {
        "source": "seller_intelligence",
        "seller_display_name": user.name,
        "company_name": None,
        "total_listings": len(products),
        "active_listings": len(products),
        "low_stock_items": summary["low_stock_items"],
        "total_sales": round(float(summary["total_sales"]), 2),
        "total_units_sold": summary["total_units_sold"],
        "average_listing_price": round(float(summary["average_price"]), 2),
        "prime_listings": 0,
        "marketplace_mix": marketplace_mix,
        "revenue_trend": revenue_trend,
        "top_listings": top_listings[:8],
        "recent_sales": recent_sales[:8],
        "listing_status": listing_status,
        "inventory_bands": [
            {"label": label, "value": value}
            for label, value in inventory_bands_map.items()
            if value > 0
        ],
    }
