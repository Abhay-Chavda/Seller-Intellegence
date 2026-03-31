# System Architecture (My WAD Project)

## Problem I am solving

Sellers usually manage products, prices, and sales across multiple marketplaces.  
I built one web app where a seller can:

- manage products and listings,
- track total sales and order metrics,
- run buybox price prediction,
- use a chat-style agent to trigger common tasks.

## Tech stack and why I selected it

- **React + TypeScript (frontend):** fast UI development, reusable components, and type safety.
- **FastAPI (backend):** simple and clean REST APIs, built-in validation using Pydantic.
- **Neon PostgreSQL (database):** cloud Postgres with easy setup for student projects.
- **SQLAlchemy ORM:** readable model-based database access.
- **JWT auth:** standard approach for stateless API authentication.
- **Model inference in Python:** easy integration with my trained buybox model.

## High-level flow

1. Seller logs in and receives JWT.
2. Frontend calls protected API endpoints with token.
3. Backend scopes queries by `seller_id` so each seller only sees own data.
4. Buybox endpoint runs ML model/fallback logic and stores prediction history.
5. Agent endpoint interprets chat prompt and executes allowed actions.

## Database entities

- `users`
- `products`
- `orders`
- `order_items`
- `buybox_predictions`
- `agent_tasks`

## Design choices I can explain in viva

- I kept **seller-level data isolation** in all business queries.
- I added a server-side validation in order creation so sellers cannot place orders on another seller's products.
- I implemented fallback buybox logic so demo still works even if model file is missing.
- I structured features in phases (MVP -> analytics -> prediction -> agent) for iterative development.

## Future improvements

- Integrate live Azure Foundry tool-calling in `/agent/chat`.
- Add charts and date-range analytics on frontend.
- Add role-based admin and audit log UI.
