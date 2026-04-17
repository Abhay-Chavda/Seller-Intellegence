# Azure Tools API

This is a standalone tools API package for Azure integration and Render deployment.

## What it exposes

- `POST /auth/signup`
- `POST /auth/login`
- `GET /auth/me`
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

## Run locally

From the project root:

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

After deployment, provide Azure the OpenAPI URL:

- `https://your-domain.onrender.com/openapi.json`

Swagger docs will be at:

- `https://your-domain.onrender.com/docs`

The package shares the same backend business logic and database models, so the data stays consistent with the main website.
