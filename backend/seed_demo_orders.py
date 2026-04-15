#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import random
from collections import defaultdict
from datetime import UTC, datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

import psycopg
from dotenv import load_dotenv


ROOT_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = Path(__file__).resolve().parent


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Seed demo orders into the configured PostgreSQL database.",
    )
    parser.add_argument(
        "--orders-per-seller",
        type=int,
        default=8,
        help="Number of demo orders to create for each seller that has active products.",
    )
    return parser.parse_args()


def load_config() -> tuple[str, str]:
    load_dotenv(BACKEND_DIR / ".env")
    load_dotenv(ROOT_DIR / ".env", override=False)

    database_url = os.getenv("DATABASE_URL", "").strip()
    if not database_url:
        raise RuntimeError("DATABASE_URL is missing in backend/.env or project .env")
    if not database_url.startswith(("postgresql+psycopg://", "postgresql://")):
        raise RuntimeError("This script supports only PostgreSQL DATABASE_URL values")

    schema = os.getenv("DATABASE_SCHEMA", "public").strip() or "public"
    normalized = database_url.replace("postgresql+psycopg://", "postgresql://", 1)
    return normalized, schema


def to_money(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def main() -> None:
    args = parse_args()
    database_url, schema = load_config()

    if args.orders_per_seller <= 0:
        raise RuntimeError("--orders-per-seller must be > 0")

    now = datetime.now(UTC)
    date_tag = now.strftime("%Y%m%d")

    inserted_orders = 0
    skipped_orders = 0
    inserted_items = 0

    with psycopg.connect(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT id, seller_id, marketplace, sell_price
                FROM {schema}.products
                WHERE is_active IS TRUE
                ORDER BY seller_id, id
                """
            )
            products_by_seller: dict[int, list[tuple[int, str, Decimal]]] = defaultdict(list)
            for product_id, seller_id, marketplace, sell_price in cur.fetchall():
                products_by_seller[seller_id].append((product_id, marketplace, Decimal(sell_price)))

            if not products_by_seller:
                print("No active products found. Nothing to seed.")
                return

            for seller_id, products in products_by_seller.items():
                seller_rng = random.Random(seller_id * 1009 + now.day)
                max_items = min(3, len(products))
                for i in range(1, args.orders_per_seller + 1):
                    order_number = f"DEMO-{date_tag}-{seller_id}-{i:03d}"
                    cur.execute(
                        f"""
                        SELECT 1
                        FROM {schema}.orders
                        WHERE seller_id = %s AND order_number = %s
                        """,
                        (seller_id, order_number),
                    )
                    if cur.fetchone():
                        skipped_orders += 1
                        continue

                    item_count = seller_rng.randint(1, max_items)
                    selected = seller_rng.sample(products, k=item_count)

                    total_amount = Decimal("0.00")
                    order_items: list[tuple[int, Decimal]] = []
                    for product_id, _marketplace, sell_price in selected:
                        qty = seller_rng.randint(1, 4)
                        multiplier = Decimal(str(seller_rng.uniform(0.92, 1.08)))
                        unit_price = to_money(max(Decimal("0.01"), sell_price * multiplier))
                        total_amount += Decimal(qty) * unit_price
                        order_items.append((product_id, qty, unit_price))

                    created_at = now - timedelta(
                        days=seller_rng.randint(0, 13),
                        hours=seller_rng.randint(0, 23),
                        minutes=seller_rng.randint(0, 59),
                    )
                    marketplace = selected[0][1]

                    cur.execute(
                        f"""
                        INSERT INTO {schema}.orders
                            (seller_id, order_number, marketplace, total_amount, created_at)
                        VALUES (%s, %s, %s, %s, %s)
                        RETURNING id
                        """,
                        (seller_id, order_number, marketplace, to_money(total_amount), created_at),
                    )
                    order_id = cur.fetchone()[0]

                    for product_id, qty, unit_price in order_items:
                        cur.execute(
                            f"""
                            INSERT INTO {schema}.order_items
                                (order_id, product_id, quantity, unit_price)
                            VALUES (%s, %s, %s, %s)
                            """,
                            (order_id, product_id, qty, unit_price),
                        )
                        inserted_items += 1

                    inserted_orders += 1

        conn.commit()

    print(f"Inserted orders: {inserted_orders}")
    print(f"Skipped existing orders: {skipped_orders}")
    print(f"Inserted order items: {inserted_items}")


if __name__ == "__main__":
    main()
