# Viva Preparation (Likely Questions + Answers)

## 1) What is the main objective of your project?

My objective is to build a seller intelligence platform where sellers can manage product data, track sales, and get buybox price recommendations from a trained model. I also added an agent interface for task-based interaction.

## 2) Why did you choose React and FastAPI?

React helps me build reusable and responsive UI quickly. FastAPI gives fast REST API development with automatic request validation and clean code structure in Python.

## 3) How do you ensure data privacy between sellers?

I use JWT authentication and seller-scoped queries. Every key table is linked with `seller_id`, and backend endpoints fetch/update only records for the authenticated seller.

## 4) How is total sales calculated?

When orders are created, `total_amount` is computed from `quantity * unit_price` for each order item. Dashboard metrics aggregate all orders of that seller to calculate total sales and total units sold.

## 5) What model inputs are used for buybox prediction?

I use features including price fields, competitor price gap fields, rank fields, competition count, feedback-related fields, and fulfillment flag (`IsFBA`), based on my trained dataset.

## 6) What happens if model file is missing?

I implemented a fallback heuristic predictor, so API remains functional for demo/testing. This avoids app failure during deployment or local run.

## 7) How does your agent work currently?

Currently it is an action router endpoint (`/agent/chat`) that maps prompts to safe actions like sales summary and buybox prediction. It logs each task in `agent_tasks` for traceability.

## 8) What is one security check you implemented yourself?

In order creation, backend verifies the selected product belongs to the logged-in seller before creating the order item. This prevents cross-seller data misuse.

## 9) Why Neon DB?

Neon gives managed PostgreSQL, easy connection from FastAPI, and is suitable for cloud-based student projects without complex infra setup.

## 10) What are your next improvements?

I plan to integrate Azure Foundry real tool-calling in the agent, add richer analytics charts, and provide prediction history filtering/export.
