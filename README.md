# Seller Intelligence

Seller Intelligence is a web application for seller operations.

## Features

- JWT-based signup and login
- Dashboard overview with revenue, units sold, catalog size, and low-stock tracking
- Inventory management with search, add, edit, archive, export, and quick restock
- Orders management with search, date filters, create order, and export

## Project structure

- `backend/`: FastAPI API, SQLAlchemy models, and database scripts
- `frontend/`: React + TypeScript frontend
- `docs/`: short project notes for architecture and viva preparation

## Setup

From repo root:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
```

For frontend:

```bash
cd frontend
npm install
```

Create your env file:

```bash
cp backend/.env.example backend/.env
```

Set these values in `backend/.env`:

- `DATABASE_URL`
- `JWT_SECRET_KEY`
- `DATABASE_SCHEMA` if you are not using `public`

## Run locally

Backend:

```bash
./backend/run_dev.sh
```

Frontend:

```bash
cd frontend
npm run dev
```

## Main API endpoints

- `POST /auth/signup`
- `POST /auth/login`
- `GET /auth/me`
- `GET /dashboard/summary`
- `GET /dashboard/overview`
- `GET /products`
- `POST /products`
- `PUT /products/{product_id}`
- `DELETE /products/{product_id}`
- `GET /orders`
- `POST /orders`
