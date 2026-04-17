# Azure Foundry API Package

This folder contains a dedicated API package meant for Azure Foundry tool registration.

## Entry Point

- App import: `azure_foundry_api.app.main:app`
- Root page: `GET /` (custom landing page with setup links)

## Run Locally

From repo root:

```bash
./azure_foundry_api/run_dev.sh
```

Server URLs:

- `http://127.0.0.1:8000/` (landing page)
- `http://127.0.0.1:8000/docs`
- `http://127.0.0.1:8000/openapi.json`
- `http://127.0.0.1:8000/tools/foundry-manifest`

## API Capabilities

- Auth:
  - `POST /auth/signup`
  - `POST /auth/login`
  - `GET /auth/me`
- Tools:
  - `GET /tools`
  - `POST /tools/invoke`
  - Direct tool endpoints under `/tools/*`
- Foundry agent lifecycle:
  - `GET /foundry/agent`
  - `POST /foundry/agent/create`

## Deployment

Use the same environment variables as backend (`backend/.env.example`).

Example start command:

```bash
PYTHONPATH=backend uvicorn azure_foundry_api.app.main:app --host 0.0.0.0 --port $PORT --app-dir .
```
