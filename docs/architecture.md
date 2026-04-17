# System Architecture

## Problem

The project helps a seller manage product listings and orders from one web app.

## Stack

- React + TypeScript for the frontend
- FastAPI for backend APIs
- SQLAlchemy ORM for database access
- PostgreSQL for persistent storage
- JWT authentication for seller login

## High-level flow

1. Seller logs in and receives a JWT token.
2. Frontend sends that token with protected API requests.
3. Backend scopes all data by `seller_id`.
4. Products and orders are stored in the database.
5. Dashboard metrics are calculated from those product and order records.

## Main database entities

- `users`
- `products`
- `orders`
- `order_items`

## Design choices

- Seller-level data isolation is enforced in all important queries.
- Order creation checks that a seller can only create orders for their own products.
- Product deletion is a soft delete so historical order data remains valid.
- The frontend keeps the code simple and direct, without heavy patterns.
