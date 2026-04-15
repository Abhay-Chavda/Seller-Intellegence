-- 001_harden_core_tables.sql
-- Applies schema hardening for product/order tables:
-- - soft delete for products (is_active)
-- - monetary precision via NUMERIC(12,2)
-- - uniqueness for active SKU per seller and order number per seller
-- - non-negative/positive check constraints

ALTER TABLE __SCHEMA__.products
ADD COLUMN IF NOT EXISTS is_active BOOLEAN;

UPDATE __SCHEMA__.products
SET is_active = TRUE
WHERE is_active IS NULL;

ALTER TABLE __SCHEMA__.products
ALTER COLUMN is_active SET DEFAULT TRUE;

ALTER TABLE __SCHEMA__.products
ALTER COLUMN is_active SET NOT NULL;

ALTER TABLE __SCHEMA__.products
ALTER COLUMN sell_price TYPE NUMERIC(12,2)
USING ROUND(COALESCE(sell_price, 0)::numeric, 2);

ALTER TABLE __SCHEMA__.orders
ALTER COLUMN total_amount TYPE NUMERIC(12,2)
USING ROUND(COALESCE(total_amount, 0)::numeric, 2);

ALTER TABLE __SCHEMA__.order_items
ALTER COLUMN unit_price TYPE NUMERIC(12,2)
USING ROUND(COALESCE(unit_price, 0)::numeric, 2);

-- If active duplicates exist, keep latest record active and deactivate older ones.
WITH ranked AS (
    SELECT
        id,
        ROW_NUMBER() OVER (
            PARTITION BY seller_id, sku
            ORDER BY updated_at DESC NULLS LAST, created_at DESC NULLS LAST, id DESC
        ) AS rn
    FROM __SCHEMA__.products
    WHERE is_active IS TRUE
)
UPDATE __SCHEMA__.products p
SET is_active = FALSE, updated_at = NOW()
FROM ranked r
WHERE p.id = r.id
  AND r.rn > 1;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'ck_products_sell_price_non_negative'
          AND connamespace = '__SCHEMA__'::regnamespace
    ) THEN
        ALTER TABLE __SCHEMA__.products
        ADD CONSTRAINT ck_products_sell_price_non_negative CHECK (sell_price >= 0);
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'ck_products_stock_non_negative'
          AND connamespace = '__SCHEMA__'::regnamespace
    ) THEN
        ALTER TABLE __SCHEMA__.products
        ADD CONSTRAINT ck_products_stock_non_negative CHECK (stock >= 0);
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'ck_orders_total_amount_non_negative'
          AND connamespace = '__SCHEMA__'::regnamespace
    ) THEN
        ALTER TABLE __SCHEMA__.orders
        ADD CONSTRAINT ck_orders_total_amount_non_negative CHECK (total_amount >= 0);
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'ck_order_items_quantity_positive'
          AND connamespace = '__SCHEMA__'::regnamespace
    ) THEN
        ALTER TABLE __SCHEMA__.order_items
        ADD CONSTRAINT ck_order_items_quantity_positive CHECK (quantity > 0);
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'ck_order_items_unit_price_non_negative'
          AND connamespace = '__SCHEMA__'::regnamespace
    ) THEN
        ALTER TABLE __SCHEMA__.order_items
        ADD CONSTRAINT ck_order_items_unit_price_non_negative CHECK (unit_price >= 0);
    END IF;
END $$;

CREATE UNIQUE INDEX IF NOT EXISTS uq_products_seller_sku_active
ON __SCHEMA__.products (seller_id, sku)
WHERE is_active IS TRUE;

CREATE UNIQUE INDEX IF NOT EXISTS uq_orders_seller_order_number
ON __SCHEMA__.orders (seller_id, order_number);

CREATE INDEX IF NOT EXISTS ix_products_is_active
ON __SCHEMA__.products (is_active);
