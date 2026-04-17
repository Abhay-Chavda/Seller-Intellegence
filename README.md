# Seller Intelligence

Seller Intelligence is a FastAPI backend for seller operations and AI tool-calling.

## What this repo contains

- `backend/`: FastAPI backend, SQLAlchemy models, tool implementations
- `frontend/`: React frontend
- `Tools/`: Azure Foundry tool metadata files
- `render.yaml`: Render blueprint for tools-only API deployment

## Backend architecture

Two backend entrypoints are available:

- Full API: `app.main:app`
  - Includes auth, dashboard, products, orders, prediction, agent chat, and tools routes.
- Tools-only API: `app.tools_api.app:app`
  - Dedicated API for Foundry integration.
  - Includes only auth + `/tools/*` routes.

## Tool implementation (Python)

Tools are implemented file-wise by domain in `backend/app/tools/`:

- `dashboard_tools.py`
- `listing_tools.py`
- `order_tools.py`
- `buybox_tools.py`
- `registry.py` (combines all tools)

## Setup

From repo root:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
```

For frontend local work:

```bash
cd frontend && npm install
```

Create env file:

```bash
cp backend/.env.example backend/.env
```

Set required values in `backend/.env`:

- `DATABASE_URL`
- `JWT_SECRET_KEY`
- `DATABASE_SCHEMA` (if using non-public schema)
- `BUYBOX_API_URL` (optional external model API)
- `BUYBOX_API_TIMEOUT_SECONDS` (optional)

## Run locally

Full API:

```bash
uvicorn app.main:app --reload --app-dir backend --reload-dir backend/app
```

Tools-only API:

```bash
uvicorn app.tools_api.app:app --reload --app-dir backend --reload-dir backend/app
```

or:

```bash
./backend/run_tools_api.sh
```

## Render deployment

If deploying tools-only API (recommended for Foundry):

- Build command:
  - `pip install -r backend/requirements.txt`
- Start command:
  - `uvicorn app.tools_api.app:app --host 0.0.0.0 --port $PORT --app-dir backend`
- Or use `render.yaml` blueprint in this repo.

If deploying full API:

- Start command:
  - `uvicorn app.main:app --host 0.0.0.0 --port $PORT --app-dir backend`

## Tools API endpoints

Tools-only API exposes:

- `POST /auth/signup`
- `POST /auth/login`
- `GET /auth/me`
- `GET /tools`
- `GET /tools/foundry-manifest`
- `POST /tools/invoke`
- `POST /tools/get_dashboard_overview`
- `POST /tools/get_dashboard_summary`
- `POST /tools/list_products`
- `POST /tools/create_product`
- `POST /tools/update_product`
- `POST /tools/archive_product`
- `POST /tools/list_orders`
- `POST /tools/create_order`
- `POST /tools/predict_buybox`
- `GET /foundry/agent`
- `POST /foundry/agent/create`

## Azure Foundry integration

Use one of these URLs from your deployed service:

- OpenAPI spec: `https://<your-domain>/openapi.json`
- Tool manifest: `https://<your-domain>/tools/foundry-manifest`

Auth for tool calls:

- Header: `Authorization: Bearer <access_token>`
- Generate token via `POST /auth/login`

Create one Foundry agent per user:

- Call `POST /foundry/agent/create` with body:
  - `connection_id` (optional): defaults to server env `FOUNDRY_CONNECTION_ID`
  - `openapi_spec` (optional): inline OpenAPI JSON object
  - `openapi_spec_url` (optional): defaults to server env `FOUNDRY_TOOLS_OPENAPI_URL`
  - `agent_name` (optional): defaults to `seller-intelligence-agent-<user_id>`
- Call `GET /foundry/agent` to fetch the saved agent mapping for the logged-in user.

Agent chat routing:

- `POST /agent/chat` now routes through the user's saved Foundry agent.
- If agent does not exist for the user, API returns 400 and asks to create it first.

## Tool metadata files

JSON metadata files are in `Tools/`:

- `seller_intelligence_tools.json` (combined)
- `dashboard_tools.json`
- `listing_tools.json`
- `order_tools.json`
- `buybox_tools.json`

## Core tables used by tools

- `products`
- `orders`
- `order_items`
- `buybox_predictions`
- `competitor_price_records`

## Notes

- `/tools/foundry-manifest` is public metadata only.
- `/tools/*` operations require auth.
- Generated artifacts (`node_modules`, `dist`, logs, caches, `.env`, local DB files) are ignored by `.gitignore`.
