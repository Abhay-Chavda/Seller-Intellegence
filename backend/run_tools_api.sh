#!/usr/bin/env bash
# Run dedicated tools-only API with reload watching backend app code.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ -x "$ROOT/.venv/bin/python" ]]; then
  exec "$ROOT/.venv/bin/python" -m uvicorn app.tools_api.app:app --reload --app-dir backend --reload-dir backend/app
fi

if [[ -x "$ROOT/backend/.venv/bin/python" ]]; then
  exec "$ROOT/backend/.venv/bin/python" -m uvicorn app.tools_api.app:app --reload --app-dir backend --reload-dir backend/app
fi

exec uvicorn app.tools_api.app:app --reload --app-dir backend --reload-dir backend/app
