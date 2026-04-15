# Seller Intelligence Platform

## 📌 Overview

A backend system designed to help sellers manage products, track orders, and gain insights using data analytics and intelligent automation.

---

## 🚀 Features

* Product and inventory management
* Order tracking system
* BuyBox price prediction integration
* Agent-based automation (in progress)

---

## 🛠️ Tech Stack

<<<<<<< Updated upstream
* Python
* FastAPI / Backend APIs
* Database (SQLite / PostgreSQL)
=======
1. From the **project root** (`WADReact/`), create and activate a virtual environment:
   - `python3 -m venv .venv`
   - `source .venv/bin/activate` (macOS/Linux) or `.venv\Scripts\activate` (Windows)
2. Install **all** backend dependencies (required — do not skip):
   - `pip install -r backend/requirements.txt`
3. Create environment file:
   - Copy `backend/.env.example` to `backend/.env`
   - Set `DATABASE_URL` to your Neon connection string
4. Apply DB migrations (required for existing databases):
   - `python backend/run_migrations.py`
5. Run the API **using the same venv** where you ran `pip install`:
   - `uvicorn app.main:app --reload --app-dir backend --reload-dir backend/app`
>>>>>>> Stashed changes

---

## 📂 Project Structure

```
app/
 ├── routes/
 ├── models/
 ├── services/
 └── database/
```

---

## ▶️ How to Run

```bash
pip install -r requirements.txt
python main.py
```

---

## 📊 Future Improvements

* AI agent integration for automation
* Dashboard UI
* Advanced analytics

---

## ⚠️ Status

🚧 Work in progress — actively developing new features

---

## 👨‍💻 Author

<<<<<<< Updated upstream
Abhay Chavda
=======
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
- Migrations live in `backend/migrations/postgres/` and are applied using `python backend/run_migrations.py`.

## API Endpoints Added in Phase 2

- `GET /orders`
- `POST /orders`
- `POST /predict/buybox`
- `POST /agent/chat`

## Tool APIs for Azure Foundry

The backend now exposes dedicated tool endpoints for Azure Foundry agent tool-calling:

- `GET /tools` (tool catalog + schemas)
- `POST /tools/invoke` (dynamic invocation by tool name)
- `POST /tools/get_dashboard_overview`
- `POST /tools/get_dashboard_summary`
- `POST /tools/list_products`
- `POST /tools/create_product`
- `POST /tools/update_product`
- `POST /tools/archive_product`
- `POST /tools/list_orders`
- `POST /tools/create_order`
- `POST /tools/predict_buybox`
- `GET /tools/foundry-manifest` (Render-friendly JSON manifest for Azure Foundry)

Tool metadata for registration lives in:

- `Tools/seller_intelligence_tools.json`
- `Tools/dashboard_tools.json`
- `Tools/listing_tools.json`
- `Tools/order_tools.json`
- `Tools/buybox_tools.json`
- `Tools/README.md`

Tool implementation files are grouped by domain in `backend/app/tools/`.

## Demo Data (Orders)

- Seed fake demo orders for all sellers with active products:
  - `python backend/seed_demo_orders.py --orders-per-seller 8`
- Demo order numbers are prefixed with `DEMO-YYYYMMDD-...`, so you can search them easily from Orders UI/API.

## Model File

- Default path: `backend/model/best_model.pkl` (or set `BUYBOX_MODEL_PATH` in `backend/.env`).
- External model API can be configured with `BUYBOX_API_URL` (+ optional `BUYBOX_API_TIMEOUT_SECONDS`).
- `scikit-learn` is listed in `requirements.txt` so pickled sklearn models can load.
- If the model file is missing or fails to load, the fallback heuristic predictor is used for demo continuity.

## Next Phase (Planned)

- Azure Foundry live LLM integration in agent orchestration layer
- Marketplace listing-level analytics and charts
- Prediction history UI and exports

## Project Documentation

- Architecture and design reasoning: `docs/architecture.md`
- Viva preparation Q&A: `docs/viva-qa.md`
>>>>>>> Stashed changes
