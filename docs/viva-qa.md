# Viva Preparation

## 1) What is the main objective of your project?

The project is a seller management platform where users can manage products, track orders, and view dashboard metrics from one place.

## 2) Why did you choose React and FastAPI?

React helps build the frontend quickly with reusable UI parts. FastAPI gives clean API routing, validation, and fast development in Python.

## 3) How do you protect seller data?

I use JWT authentication and seller-scoped database queries. Every important record is connected to the logged-in seller.

## 4) How is total sales calculated?

When an order is created, `total_amount` is calculated from `quantity * unit_price` for all order items. Dashboard sales metrics are aggregated from those order totals.

## 5) How do you handle stock tracking?

Each product stores a stock value. The dashboard counts low-stock items, and the inventory page also supports quick restocking.

## 6) What security check did you implement in order creation?

Before creating an order item, the backend checks that the selected product belongs to the logged-in seller.

## 7) Why did you use SQLAlchemy?

It gives readable model-based database code and works well with FastAPI for CRUD operations.

## 8) Why is product deletion a soft delete?

Soft delete keeps old order references valid and avoids breaking historical sales data.

## 9) Why did you use PostgreSQL?

PostgreSQL is reliable, structured, and a good fit for relational data like users, products, orders, and order items.

## 10) What improvements can you add later?

I can add better reporting, richer filtering, and more detailed sales analytics.
