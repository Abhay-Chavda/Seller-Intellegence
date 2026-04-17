from pathlib import Path
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

# Ensure backend/app is importable as package name `app`.
ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.core.config import get_settings
from app.db import Base, engine

from .routes import router

settings = get_settings()

app = FastAPI(
    title="Seller Intelligence Azure Foundry API",
    version="1.0.0",
    description=(
        "Standalone Azure Foundry tools API package for Seller Intelligence. "
        "Includes auth, tool registry, direct tool invoke endpoints, and Foundry agent setup endpoints."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)
app.include_router(router)


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "azure_foundry_api"}


@app.get("/", response_class=HTMLResponse)
def root_page() -> str:
    return """
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Seller Intelligence Azure Foundry API</title>
    <style>
      body {
        font-family: Arial, sans-serif;
        margin: 0;
        background: #0f172a;
        color: #e2e8f0;
      }
      .wrap {
        max-width: 920px;
        margin: 0 auto;
        padding: 36px 20px 50px;
      }
      h1 {
        margin: 0 0 10px;
        font-size: 28px;
      }
      p {
        color: #cbd5e1;
        line-height: 1.6;
      }
      .card {
        background: #111827;
        border: 1px solid #1f2937;
        border-radius: 12px;
        padding: 16px;
        margin-top: 18px;
      }
      a {
        color: #60a5fa;
        text-decoration: none;
      }
      a:hover {
        text-decoration: underline;
      }
      ul {
        margin: 10px 0 0 18px;
      }
      code {
        background: #1f2937;
        border-radius: 6px;
        padding: 2px 6px;
      }
    </style>
  </head>
  <body>
    <div class="wrap">
      <h1>Seller Intelligence Azure Foundry API</h1>
      <p>
        This dedicated API package is prepared for Azure Foundry tool integration.
        Use the links below for setup and testing.
      </p>

      <div class="card">
        <strong>Quick Links</strong>
        <ul>
          <li><a href="/docs">Swagger Docs</a></li>
          <li><a href="/openapi.json">OpenAPI Spec</a></li>
          <li><a href="/tools/foundry-manifest">Foundry Tool Manifest</a></li>
          <li><a href="/health">Health Check</a></li>
        </ul>
      </div>

      <div class="card">
        <strong>Auth Header</strong>
        <p>For tool calls, send <code>Authorization: Bearer &lt;access_token&gt;</code>.</p>
        <p>Create token via <code>POST /auth/login</code>.</p>
      </div>

      <div class="card">
        <strong>Core Endpoints</strong>
        <ul>
          <li><code>GET /tools</code></li>
          <li><code>POST /tools/invoke</code></li>
          <li><code>POST /tools/get_dashboard_overview</code></li>
          <li><code>POST /tools/list_products</code></li>
          <li><code>POST /tools/create_order</code></li>
          <li><code>POST /tools/predict_buybox</code></li>
          <li><code>GET /foundry/agent</code></li>
          <li><code>POST /foundry/agent/create</code></li>
        </ul>
      </div>
    </div>
  </body>
</html>
"""
