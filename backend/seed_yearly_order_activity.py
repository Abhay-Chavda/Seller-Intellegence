#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import random
from collections import defaultdict
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

import psycopg
from dotenv import load_dotenv


ROOT_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = Path(__file__).resolve().parent

MONTH_MULTIPLIERS = {
    1: 0.92,
    2: 0.95,
    3: 0.99,
    4: 1.03,
    5: 1.07,
    6: 1.1,
    7: 1.14,
    8: 1.08,
    9: 1.04,
    10: 1.12,
    11: 1.28,
    12: 1.22,
}

WEEKDAY_MULTIPLIERS = {
    0: 1.02,
    1: 1.06,
    2: 1.08,
    3: 1.1,
    4: 1.16,
    5: 0.74,
    6: 0.58,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Seed dense 1-year order activity for each non-admin seller.",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=365,
        help="How many trailing days of history to seed. Default: 365.",
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


def daily_signal(current_day: date, seller_id: int) -> float:
    seller_bias = 0.92 + (seller_id % 4) * 0.07
    return (
        MONTH_MULTIPLIERS[current_day.month]
        * WEEKDAY_MULTIPLIERS[current_day.weekday()]
        * seller_bias
    )


def orders_for_day(rng: random.Random, current_day: date, seller_id: int) -> int:
    signal = daily_signal(current_day, seller_id)
    primary_probability = min(0.9, max(0.24, 0.46 * signal))

    orders = 0
    if rng.random() < primary_probability:
        orders += 1
    if rng.random() < primary_probability * 0.44:
        orders += 1
    if rng.random() < primary_probability * 0.18:
        orders += 1

    if current_day.month in {11, 12} and rng.random() < 0.08:
        orders += 1
    if current_day.weekday() == 4 and rng.random() < 0.1:
        orders += 1

    return orders


def choose_items(
    rng: random.Random,
    products: list[tuple[int, str, Decimal]],
    current_day: date,
) -> tuple[str, list[tuple[int, int, Decimal]], Decimal]:
    item_count = min(len(products), 1 + int(rng.random() < 0.42) + int(rng.random() < 0.16))
    selected_products = rng.sample(products, k=item_count)

    total_amount = Decimal("0.00")
    order_items: list[tuple[int, int, Decimal]] = []
    price_multiplier = Decimal(
        str(
            0.94
            + (MONTH_MULTIPLIERS[current_day.month] - 0.9) * 0.08
            + rng.random() * 0.12
        )
    )

    for product_id, _marketplace, sell_price in selected_products:
        quantity = 1 + int(rng.random() < 0.48) + int(rng.random() < 0.14)
        unit_price = to_money(max(Decimal("0.01"), sell_price * price_multiplier))
        total_amount += Decimal(quantity) * unit_price
        order_items.append((product_id, quantity, unit_price))

    marketplace = selected_products[0][1]
    return marketplace, order_items, to_money(total_amount)


def main() -> None:
    args = parse_args()
    if args.days <= 0:
        raise RuntimeError("--days must be > 0")

    database_url, schema = load_config()
    today = datetime.now(UTC).date()
    start_day = today - timedelta(days=args.days - 1)

    inserted_orders = 0
    skipped_orders = 0
    inserted_items = 0
    seller_order_counts: dict[int, int] = defaultdict(int)

    with psycopg.connect(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT p.id, p.seller_id, p.marketplace, p.sell_price
                FROM {schema}.products p
                JOIN {schema}.users u ON u.id = p.seller_id
                WHERE p.is_active IS TRUE
                  AND u.role <> 'admin'
                ORDER BY p.seller_id, p.id
                """
            )
            products_by_seller: dict[int, list[tuple[int, str, Decimal]]] = defaultdict(list)
            for product_id, seller_id, marketplace, sell_price in cur.fetchall():
                products_by_seller[seller_id].append((product_id, marketplace, Decimal(sell_price)))

            if not products_by_seller:
                print("No active seller products found. Nothing to seed.")
                return

            for seller_id, products in products_by_seller.items():
                cur.execute(
                    f"""
                    SELECT order_number
                    FROM {schema}.orders
                    WHERE seller_id = %s
                      AND order_number LIKE %s
                    """,
                    (seller_id, f"YEARLY-{seller_id}-%"),
                )
                existing_order_numbers = {row[0] for row in cur.fetchall()}

                order_rows: list[tuple[int, str, str, Decimal, datetime]] = []
                order_item_plans: list[tuple[str, int, int, Decimal]] = []
                new_order_numbers: list[str] = []

                for offset in range(args.days):
                    current_day = start_day + timedelta(days=offset)
                    day_rng = random.Random(f"yearly-activity:{seller_id}:{current_day.isoformat()}")
                    daily_order_count = orders_for_day(day_rng, current_day, seller_id)

                    for slot in range(1, daily_order_count + 1):
                        order_number = f"YEARLY-{seller_id}-{current_day.strftime('%Y%m%d')}-{slot:02d}"
                        if order_number in existing_order_numbers:
                            skipped_orders += 1
                            continue

                        marketplace, order_items, total_amount = choose_items(day_rng, products, current_day)
                        created_at = datetime(
                            current_day.year,
                            current_day.month,
                            current_day.day,
                            8 + day_rng.randint(0, 12),
                            day_rng.randint(0, 59),
                            day_rng.randint(0, 59),
                        )

                        order_rows.append(
                            (seller_id, order_number, marketplace, total_amount, created_at)
                        )
                        new_order_numbers.append(order_number)
                        for product_id, quantity, unit_price in order_items:
                            order_item_plans.append((order_number, product_id, quantity, unit_price))

                if not order_rows:
                    print(f"Seller {seller_id}: no new yearly orders needed")
                    conn.commit()
                    continue

                cur.executemany(
                    f"""
                    INSERT INTO {schema}.orders
                        (seller_id, order_number, marketplace, total_amount, created_at)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (seller_id, order_number) DO NOTHING
                    """,
                    order_rows,
                )

                cur.execute(
                    f"""
                    SELECT id, order_number
                    FROM {schema}.orders
                    WHERE seller_id = %s
                      AND order_number = ANY(%s)
                    """,
                    (seller_id, new_order_numbers),
                )
                order_id_map = {order_number: order_id for order_id, order_number in cur.fetchall()}

                order_item_rows = [
                    (order_id_map[order_number], product_id, quantity, unit_price)
                    for order_number, product_id, quantity, unit_price in order_item_plans
                    if order_number in order_id_map
                ]

                if order_item_rows:
                    cur.executemany(
                        f"""
                        INSERT INTO {schema}.order_items
                            (order_id, product_id, quantity, unit_price)
                        VALUES (%s, %s, %s, %s)
                        """,
                        order_item_rows,
                    )

                conn.commit()

                seller_order_counts[seller_id] += len(order_rows)
                inserted_orders += len(order_rows)
                inserted_items += len(order_item_rows)
                print(
                    f"Seller {seller_id}: +{len(order_rows)} orders, +{len(order_item_rows)} items"
                )

    print(f"Inserted orders: {inserted_orders}")
    print(f"Skipped existing orders: {skipped_orders}")
    print(f"Inserted order items: {inserted_items}")
    for seller_id in sorted(seller_order_counts):
        print(f"Seller {seller_id}: +{seller_order_counts[seller_id]} orders")


if __name__ == "__main__":
    main()
