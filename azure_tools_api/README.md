# Azure Tools API

This package is a separate deployable API for:

- seller tools
- Azure agent creation
- agent chat for the website

## Main endpoints

Auth:

- `POST /auth/signup`
- `POST /auth/login`
- `GET /auth/me`

Agent:

- `GET /agent/current`
- `POST /agent/create`
- `POST /agent/chat`
- `POST /agent/chat/reset`
- `GET /agent/openapi`

Authenticated tool endpoints:

- `GET /tools`
- `POST /tools/invoke`
- `POST /tools/get_dashboard_overview`
- `POST /tools/get_dashboard_summary`
- `POST /tools/list_products`
- `POST /tools/create_product`
- `POST /tools/update_product`
- `POST /tools/archive_product`
- `POST /tools/list_orders`
- `POST /tools/create_order`

Anonymous agent tool endpoints:

- `POST /agent-tools/{agent_key}/get_dashboard_overview`
- `POST /agent-tools/{agent_key}/get_dashboard_summary`
- `POST /agent-tools/{agent_key}/list_products`
- `POST /agent-tools/{agent_key}/create_product`
- `POST /agent-tools/{agent_key}/update_product`
- `POST /agent-tools/{agent_key}/archive_product`
- `POST /agent-tools/{agent_key}/list_orders`
- `POST /agent-tools/{agent_key}/create_order`

## Local run

From repo root:

```bash
./azure_tools_api/run_dev.sh
```

## Deploy to Render

Use the file:

- `azure_tools_api/render.yaml`

Or create the service manually with:

- Build command: `pip install -r azure_tools_api/requirements.txt`
- Start command: `uvicorn azure_tools_api.main:app --host 0.0.0.0 --port $PORT --app-dir .`

## Give to Azure

If you need the service OpenAPI itself:

- `https://your-domain.onrender.com/openapi.json`

Docs:

- `https://your-domain.onrender.com/docs`
