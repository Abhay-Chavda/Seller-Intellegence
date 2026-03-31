# Seller Intelligence Platform (WAD Project)

This repository contains a full-stack starter for your Web Application Development project:

- `frontend/` React + TypeScript app for sellers
- `backend/` FastAPI + SQLAlchemy API with JWT auth and seller-scoped product tracking

## Implemented (Phase 1 + Phase 2)

- Multi-seller signup/login
- JWT-protected API
- Seller dashboard summary (total products, low stock items, average price)
- Product CRUD foundation (create/list/update/delete)
- Orders module with total sales tracking
- Buybox prediction endpoint with trained model support and fallback heuristic
- Agent chat endpoint for sales summary and buybox tasks
- Neon-ready database config via `DATABASE_URL`

## My Design Notes (for explanation)

- I built this in phases so I could test each module independently.
- I kept seller data isolated using `seller_id` in queries.
- I used a fallback buybox logic so the project is runnable even without model artifact.
- I added server-side validation for order creation to avoid cross-seller product mapping.

## Backend Setup

1. From the **project root** (`WADReact/`), create and activate a virtual environment:
   - `python3 -m venv .venv`
   - `source .venv/bin/activate` (macOS/Linux) or `.venv\Scripts\activate` (Windows)
2. Install **all** backend dependencies (required — do not skip):
   - `pip install -r backend/requirements.txt`
3. Create environment file:
   - Copy `backend/.env.example` to `backend/.env`
   - Set `DATABASE_URL` to your Neon connection string
4. Run the API **using the same venv** where you ran `pip install`:
   - `uvicorn app.main:app --reload --app-dir backend --reload-dir backend/app`

API runs at `http://localhost:8000`.

**Why `--reload-dir backend/app`?**  
Without it, uvicorn watches the whole project folder (including `.venv`). `pip install` or any change under `.venv` triggers noisy `WatchFiles detected changes in '.venv/...' Reloading...` warnings and extra restarts. Watching only `backend/app` avoids that.

Shortcut from project root: `./backend/run_dev.sh` (same flags).

### Troubleshooting: `ModuleNotFoundError: No module named 'sqlalchemy'`

This means the Python process running `uvicorn` does not have dependencies installed.

- Activate your venv, then run: `pip install -r backend/requirements.txt`
- Start uvicorn again from that same terminal (same venv).
- If you use `pyenv` or multiple Pythons, run: `which python` and `which uvicorn` — they should both point inside `.venv`.

### Troubleshooting: `WARNING: WatchFiles detected changes in '.venv/...' Reloading...`

Harmless but noisy: the reloader is watching `.venv`. Use the command above with `--reload-dir backend/app`, or run without auto-reload: `uvicorn app.main:app --app-dir backend` (no `--reload`).

### Pip notice: `[notice] A new release of pip is available`

Optional. You can ignore it or run `pip install --upgrade pip` inside the venv.

### Troubleshooting: browser / React shows network error; server logs `OPTIONS ... 400 Bad Request`

Your frontend URL must match **CORS** settings. `http://localhost:5173` and `http://127.0.0.1:5173` are **different origins**.

- In `backend/.env`, set both (comma-separated):

  `CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173`

- Restart uvicorn after editing `.env`.

### Opening the API in the browser

- `http://127.0.0.1:8000/` redirects to `/docs` (Swagger UI).
- The seller UI is the React app: `npm run dev` → usually `http://localhost:5173`.

## Frontend Setup

1. Install dependencies:
   - `cd frontend && npm install`
2. Run dev server:
   - `npm run dev`

App runs at `http://localhost:5173`.

## Neon DB Notes

- Use a Neon Postgres URL in `backend/.env`.
- For quick local testing, default SQLite works if `DATABASE_URL` is omitted.

## API Endpoints Added in Phase 2

- `GET /orders`
- `POST /orders`
- `POST /predict/buybox`
- `POST /agent/chat`

## Model File

- Default path: `backend/model/best_model.pkl` (or set `BUYBOX_MODEL_PATH` in `backend/.env`).
- `scikit-learn` is listed in `requirements.txt` so pickled sklearn models can load.
- If the model file is missing or fails to load, the fallback heuristic predictor is used for demo continuity.

## Next Phase (Planned)

- Azure Foundry live LLM integration in agent orchestration layer
- Marketplace listing-level analytics and charts
- Prediction history UI and exports

## Project Documentation

- Architecture and design reasoning: `docs/architecture.md`
- Viva preparation Q&A: `docs/viva-qa.md`
