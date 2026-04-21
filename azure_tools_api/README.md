# Azure Tools API

This package is a separate deployable FastAPI service for:

- seller tools
- Azure Foundry agent linking or creation
- agent chat for the website

It now supports the Foundry-style variables you showed, including:

- `AZURE_EXISTING_AGENT_ID`
- `AZURE_EXISTING_AIPROJECT_ENDPOINT`
- `AZURE_AI_PROJECT_ENDPOINT`
- `AZURE_AI_MODEL_DEPLOYMENT_NAME`

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

## Env handling

For local development, the app now loads:

- `azure_tools_api/.env`

There is also an example file:

- `azure_tools_api/.env.example`

Supported endpoint aliases:

- `PROJECT_ENDPOINT`
- `AZURE_AI_PROJECT_ENDPOINT`
- `AZURE_EXISTING_AIPROJECT_ENDPOINT`

Supported model aliases:

- `MODEL_DEPLOYMENT_NAME`
- `AZURE_AI_MODEL_DEPLOYMENT_NAME`

Existing-agent mode:

- If `AZURE_EXISTING_AGENT_ID` is set, `POST /agent/create` links that Foundry agent into the local app record instead of creating a new one.
- Supported formats:
  - `AgentName`
  - `AgentName:2`
- If different agents or users need different Foundry agent references, do not keep changing global env.
  Send `existing_agent_id` and `project_endpoint` in `POST /agent/create` and the API stores them per agent record.

Create-new-agent mode:

- If `AZURE_EXISTING_AGENT_ID` is not set, `POST /agent/create` creates a new Foundry agent version using the configured model deployment.

## Per-agent config

Global env should only hold defaults that are shared by the service.

Per-agent values should go in the create request:

```json
{
  "agent_name": "WillowAgent",
  "instructions": "Help with orders and inventory",
  "existing_agent_id": "WillowAgent:1",
  "project_endpoint": "https://amar-0558-resource.services.ai.azure.com/api/projects/amar-0558"
}
```

Optional create-new overrides:

```json
{
  "agent_name": "seller-agent-42",
  "instructions": "Help with products",
  "model_deployment_name": "gpt-5.2-chat",
  "project_endpoint": "https://amar-0558-resource.services.ai.azure.com/api/projects/amar-0558"
}
```

Only these values are needed at runtime for agent routing:

- `existing_agent_id`
- `project_endpoint`

The following variables from the Foundry export are metadata for provisioning and are not required for normal chat routing in this API:

- `AZURE_ENV_NAME`
- `AZURE_LOCATION`
- `AZURE_SUBSCRIPTION_ID`
- `AZURE_EXISTING_AIPROJECT_RESOURCE_ID`
- `AZURE_EXISTING_RESOURCE_ID`
- `AZD_ALLOW_NON_EMPTY_FOLDER`

## Authentication note

The Foundry endpoint variables identify which project and which agent to use. They do not authenticate the SDK by themselves.

This package uses `DefaultAzureCredential()`, so one of these must be true:

- local dev: you ran `az login` or `azd auth login`
- Azure-hosted runtime: managed identity is available
- non-Azure host such as Render: set `AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, and `AZURE_CLIENT_SECRET`

## Demo mode

For a demo on your own machine, use the local developer flow:

```bash
az login
./azure_tools_api/run_dev.sh
```

For this mode, the main env values are:

- `DATABASE_URL`
- `DATABASE_SCHEMA`
- `JWT_SECRET_KEY`
- `PUBLIC_BASE_URL`
- `PROJECT_ENDPOINT`
- `MODEL_DEPLOYMENT_NAME`

You do not need:

- `AZURE_CLIENT_ID`
- `AZURE_TENANT_ID`
- `AZURE_CLIENT_SECRET`

as long as `az login` is active for the same user account and that account has access to the Foundry project.

## Local run

From repo root:

```bash
./azure_tools_api/run_dev.sh
```

## Deploy to Render

Use:

- `azure_tools_api/render.yaml`

Or configure manually:

- Build command: `pip install -r azure_tools_api/requirements.txt`
- Start command: `uvicorn azure_tools_api.main:app --host 0.0.0.0 --port $PORT`

## Give to Azure

OpenAPI:

- `https://your-domain.onrender.com/openapi.json`

Docs:

- `https://your-domain.onrender.com/docs`
