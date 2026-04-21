from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy import select, text

from app.db import engine
from app.models import Order, OrderItem, Product, User


PRODUCT_TEMPLATES = [
    {"title": "Wireless Earbuds Pro", "sku": "AUDIO-BUDS", "price": Decimal("79.99"), "stock": 42, "marketplace": "Amazon"},
    {"title": "Stainless Steel Water Bottle", "sku": "HOME-BOTTLE", "price": Decimal("24.99"), "stock": 9, "marketplace": "Amazon"},
    {"title": "Yoga Mat Premium", "sku": "FIT-MAT", "price": Decimal("34.50"), "stock": 18, "marketplace": "Shopify"},
    {"title": "Desk Lamp Minimal", "sku": "HOME-LAMP", "price": Decimal("44.00"), "stock": 27, "marketplace": "Walmart"},
    {"title": "Laptop Sleeve 15in", "sku": "TECH-SLEEVE", "price": Decimal("29.99"), "stock": 63, "marketplace": "Amazon UK"},
    {"title": "Organic Cotton T-Shirt", "sku": "APP-TSHIRT", "price": Decimal("19.95"), "stock": 31, "marketplace": "Shopify"},
    {"title": "Ceramic Coffee Mug", "sku": "HOME-MUG", "price": Decimal("16.75"), "stock": 14, "marketplace": "Amazon"},
    {"title": "Mechanical Keyboard", "sku": "TECH-KEYBOARD", "price": Decimal("94.90"), "stock": 7, "marketplace": "Amazon US"},
]

YEARLY_MARKETPLACES = ["Amazon", "Shopify", "Walmart", "Amazon UK", "Amazon US"]


def money(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def utc_now_naive() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def build_yearly_order_blueprints(seller_id: int) -> list[dict]:
    blueprints: list[dict] = []
    product_count = len(PRODUCT_TEMPLATES)
    seller_shift = seller_id % product_count

    for week in range(52):
        marketplace = YEARLY_MARKETPLACES[(week + seller_id) % len(YEARLY_MARKETPLACES)]
        first_product = (week + seller_shift) % product_count
        second_product = (week + seller_shift + 3) % product_count
        third_product = (week + seller_shift + 5) % product_count

        items = [(first_product, 1 + (week % 3))]
        if week % 2 == 0:
            items.append((second_product, 1 + ((week + seller_id) % 2)))
        if week % 5 == 0:
            items.append((third_product, 1))

        blueprints.append(
            {
                "marketplace": marketplace,
                "days_ago": (51 - week) * 7,
                "items": items,
            }
        )

    return blueprints


def reset_demo_tables(connection, schema: str) -> None:
    for table in [
        "agent_tasks",
        "buybox_predictions",
        "user_foundry_agents",
        "azure_agent_records",
        "competitor_price_records",
        "order_items",
        "orders",
        "products",
    ]:
        connection.execute(text(f"DELETE FROM {schema}.{table}"))


def build_product_rows(seller_id: int) -> list[dict]:
    rows: list[dict] = []
    seller_code = str(seller_id).zfill(2)
    now = utc_now_naive()

    for index, template in enumerate(PRODUCT_TEMPLATES, start=1):
        created_at = now - timedelta(days=360 - index * 21 - (seller_id % 5))
        rows.append(
            {
                "seller_id": seller_id,
                "title": template["title"],
                "sku": f"{template['sku']}-{seller_code}-{index}",
                "sell_price": money(template["price"] + Decimal(str((seller_id % 3) * 1.25))),
                "stock": int(template["stock"] + (seller_id % 4) * 3),
                "marketplace": template["marketplace"],
                "is_active": True,
                "created_at": created_at,
                "updated_at": created_at,
            }
        )

    return rows


def main() -> None:
    schema = Product.__table__.schema or "public"

    with engine.begin() as connection:
        reset_demo_tables(connection, schema)

        sellers = connection.execute(
            select(User.id, User.email)
            .where(User.role != "admin")
            .order_by(User.created_at.asc(), User.id.asc())
        ).mappings().all()

        now = utc_now_naive()

        for seller in sellers:
            seller_id = seller["id"]
            product_rows = build_product_rows(seller_id)
            product_result = connection.execute(
                Product.__table__.insert().returning(
                    Product.id,
                    Product.sell_price,
                ),
                product_rows,
            )
            inserted_products = product_result.fetchall()

            price_by_index = {
                index: money(Decimal(str(row.sell_price)))
                for index, row in enumerate(inserted_products)
            }
            product_id_by_index = {
                index: row.id
                for index, row in enumerate(inserted_products)
            }

            for order_index, blueprint in enumerate(build_yearly_order_blueprints(seller_id), start=1):
                created_at = now - timedelta(days=blueprint["days_ago"], hours=(order_index % 9) + 1)
                total_amount = Decimal("0.00")
                item_rows: list[dict] = []

                for product_index, quantity in blueprint["items"]:
                    unit_price = price_by_index[product_index]
                    total_amount += unit_price * quantity
                    item_rows.append(
                        {
                            "product_id": product_id_by_index[product_index],
                            "quantity": quantity,
                            "unit_price": unit_price,
                        }
                    )

                order_id = connection.execute(
                    Order.__table__.insert().returning(Order.id),
                    [
                        {
                            "seller_id": seller_id,
                            "order_number": f"ORD-{seller_id}-{created_at.strftime('%Y%m%d')}-{order_index:03d}",
                            "marketplace": blueprint["marketplace"],
                            "total_amount": money(total_amount),
                            "created_at": created_at,
                        }
                    ],
                ).scalar_one()

                connection.execute(
                    OrderItem.__table__.insert(),
                    [
                        {
                            "order_id": order_id,
                            **item_row,
                        }
                        for item_row in item_rows
                    ],
                )

    print(f"Seeded 1 year of demo catalog and order data for {len(sellers)} non-admin user(s).")


if __name__ == "__main__":
    main()
