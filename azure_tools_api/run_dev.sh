#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
PORT="${PORT:-8001}"

if [[ -x "$ROOT/.venv/bin/python" ]]; then
  exec "$ROOT/.venv/bin/python" -m uvicorn azure_tools_api.main:app --host 127.0.0.1 --port "$PORT" --reload --app-dir . --reload-dir azure_tools_api --reload-dir backend/app
fi

if [[ -x "$ROOT/backend/.venv/bin/python" ]]; then
  exec "$ROOT/backend/.venv/bin/python" -m uvicorn azure_tools_api.main:app --host 127.0.0.1 --port "$PORT" --reload --app-dir . --reload-dir azure_tools_api --reload-dir backend/app
fi

exec uvicorn azure_tools_api.main:app --host 127.0.0.1 --port "$PORT" --reload --app-dir . --reload-dir azure_tools_api --reload-dir backend/app
