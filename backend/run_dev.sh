#!/usr/bin/env bash
# Run API with reload watching only app code (avoids .venv WatchFiles spam).
# From project root:  ./backend/run_dev.sh
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
exec uvicorn app.main:app --reload --app-dir backend --reload-dir backend/app
