# Seller Intelligence Tool APIs

This folder contains Azure Foundry tool metadata for Seller Intelligence.

- Manifest file: `seller_intelligence_tools.json`
- Domain-wise files:
  - `dashboard_tools.json`
  - `listing_tools.json`
  - `order_tools.json`
  - `buybox_tools.json`
- Backend tool endpoints are exposed under `/tools/*` in FastAPI.
- Render JSON manifest endpoint: `/tools/foundry-manifest`
- Recommended dedicated API entrypoint for deployment: `app.tools_api.app:app`
- Optional Render blueprint: `render.yaml`

## Backend Tool Folder Structure

Tools are now organized file-wise in `backend/app/tools`:

- `dashboard_tools.py` -> dashboard tools
- `listing_tools.py` -> product/listing tools
- `order_tools.py` -> order tools
- `buybox_tools.py` -> buybox prediction tool
- `registry.py` -> combined registry used by APIs

Dedicated tools API routes live in `backend/app/tools_api/`.

## Tool-to-table mapping

- `get_dashboard_overview` -> `products`, `orders`, `order_items`
- `get_dashboard_summary` -> `products`, `orders`, `order_items`
- `list_products`, `create_product`, `update_product`, `archive_product` -> `products`
- `list_orders`, `create_order` -> `orders`, `order_items`, `products`
- `predict_buybox` -> `products`, `competitor_price_records`, `buybox_predictions`

`predict_buybox` tool arguments are intentionally minimal (`sku`, `SellPrice`, `ShippingPrice`, `MinCompetitorPrice`, `PositiveFeedbackPercent`, `IsFBA`); backend derives the remaining model features.

## Auth

All `/tools/*` APIs require JWT bearer auth from `/auth/login`.
`/tools/foundry-manifest` is public metadata only (no seller data).

## Buybox model API

Set custom external model API in backend `.env`:

- `BUYBOX_API_URL=https://<your-model-api-endpoint>`
- `BUYBOX_API_TIMEOUT_SECONDS=8`

When the external API is unavailable, backend falls back to local model and then heuristic logic.
