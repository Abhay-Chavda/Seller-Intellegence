from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models import AgentTask, BuyboxPrediction, Order, OrderItem, Product, User
from app.schemas import (
    BuyboxFeatureInput,
    OrderCreate,
    ProductCreate,
    ProductUpdate,
    UserCreate,
)


def create_user(db: Session, payload: UserCreate) -> User:
    user = User(
        name=payload.name,
        email=payload.email.lower(),
        hashed_password=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == email.lower()))


def create_product(db: Session, seller_id: int, payload: ProductCreate) -> Product:
    product = Product(seller_id=seller_id, **payload.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


def list_products(db: Session, seller_id: int) -> list[Product]:
    stmt = select(Product).where(Product.seller_id == seller_id).order_by(Product.id.desc())
    return list(db.scalars(stmt).all())


def get_product(db: Session, seller_id: int, product_id: int) -> Product | None:
    stmt = select(Product).where(Product.seller_id == seller_id, Product.id == product_id)
    return db.scalar(stmt)


def update_product(db: Session, product: Product, payload: ProductUpdate) -> Product:
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(product, field, value)
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


def delete_product(db: Session, product: Product) -> None:
    db.delete(product)
    db.commit()


def get_dashboard_summary(db: Session, seller_id: int) -> dict:
    total_products = db.scalar(
        select(func.count()).select_from(Product).where(Product.seller_id == seller_id)
    ) or 0
    low_stock_items = db.scalar(
        select(func.count())
        .select_from(Product)
        .where(Product.seller_id == seller_id, Product.stock < 10)
    ) or 0
    average_price = db.scalar(
        select(func.avg(Product.sell_price)).where(Product.seller_id == seller_id)
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

    total = 0.0
    for item in payload.items:
        # Security check: a seller can only create orders for their own products.
        product = get_product(db, seller_id=seller_id, product_id=item.product_id)
        if product is None:
            raise ValueError(f"Product {item.product_id} not found for this seller")

        order_item = OrderItem(
            order_id=order.id,
            product_id=item.product_id,
            quantity=item.quantity,
            unit_price=item.unit_price,
        )
        total += item.quantity * item.unit_price
        db.add(order_item)

    order.total_amount = round(total, 2)
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


def list_orders(db: Session, seller_id: int) -> list[Order]:
    stmt = select(Order).where(Order.seller_id == seller_id).order_by(Order.id.desc())
    return list(db.scalars(stmt).all())


def create_buybox_prediction(
    db: Session,
    seller_id: int,
    features: BuyboxFeatureInput,
    recommended_price: float,
    confidence: float,
    model_name: str,
) -> BuyboxPrediction:
    prediction = BuyboxPrediction(
        seller_id=seller_id,
        sku=features.sku,
        recommended_price=recommended_price,
        confidence=confidence,
        model_name=model_name,
    )
    db.add(prediction)
    db.commit()
    db.refresh(prediction)
    return prediction


def create_agent_task(
    db: Session,
    seller_id: int,
    prompt: str,
    action: str,
    result: str,
) -> AgentTask:
    task = AgentTask(seller_id=seller_id, prompt=prompt, action=action, result=result)
    db.add(task)
    db.commit()
    db.refresh(task)
    return task
