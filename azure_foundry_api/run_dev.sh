#!/usr/bin/env bash
# Run dedicated Azure Foundry API from repo root or any path.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
export PYTHONPATH="$ROOT/backend:${PYTHONPATH:-}"

if [[ -x "$ROOT/.venv/bin/python" ]]; then
  exec "$ROOT/.venv/bin/python" -m uvicorn azure_foundry_api.app.main:app \
    --reload \
    --app-dir "$ROOT" \
    --reload-dir "$ROOT/azure_foundry_api" \
    --reload-dir "$ROOT/backend/app"
fi

if [[ -x "$ROOT/backend/.venv/bin/python" ]]; then
  exec "$ROOT/backend/.venv/bin/python" -m uvicorn azure_foundry_api.app.main:app \
    --reload \
    --app-dir "$ROOT" \
    --reload-dir "$ROOT/azure_foundry_api" \
    --reload-dir "$ROOT/backend/app"
fi

exec uvicorn azure_foundry_api.app.main:app \
  --reload \
  --app-dir "$ROOT" \
  --reload-dir "$ROOT/azure_foundry_api" \
  --reload-dir "$ROOT/backend/app"
