import os
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT_DIR / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from fastapi import Body, Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app import crud, models, schemas as core_schemas
from app.core.config import get_settings
from app.core.security import create_access_token, decode_access_token, verify_password
from app.db import Base, engine, get_db

from azure_tools_api import agent_models as _agent_models  # noqa: F401
from azure_tools_api.agent_service import (
    build_agent_openapi_spec,
    create_or_update_agent,
    get_agent_record,
    get_agent_record_by_key,
    run_agent_chat,
)
from azure_tools_api.schemas import (
    AgentChatMessage,
    AgentChatRequest,
    AgentChatResponse,
    AgentCreateRequest,
    AgentCreateResponse,
    ArchiveProductResult,
    ArchiveProductToolArgs,
    CurrentAgentResponse,
    ListOrdersToolArgs,
    ListProductsToolArgs,
    ToolDefinition,
    ToolInvokeRequest,
    ToolInvokeResponse,
    UpdateProductToolArgs,
)
from azure_tools_api.tool_registry import execute_tool, list_tool_definitions

app = FastAPI(
    title="Seller Intelligence Tools API",
    version="1.1.0",
    description=(
        "Standalone tools + agent API for Azure integration. "
        "It exposes seller tools, agent creation, and agent chat endpoints."
    ),
)
settings = get_settings()
security = HTTPBearer(auto_error=False)
AGENT_CHAT_HISTORY: dict[int, list[dict[str, str]]] = {}

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)


def get_public_base_url(request: Request) -> str:
    configured = os.getenv("PUBLIC_BASE_URL", "").strip()
    if configured:
        return configured.rstrip("/")
    return str(request.base_url).rstrip("/")


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: Session = Depends(get_db),
) -> models.User:
    token = credentials.credentials.strip() if credentials and credentials.credentials else ""
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header",
        )
    subject = decode_access_token(token)
    if subject is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    user = crud.get_user_by_email(db, subject)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


def get_agent_owner_by_key(agent_key: str, db: Session) -> models.User:
    record = get_agent_record_by_key(db, agent_key)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent key not found")

    user = db.get(models.User, record.seller_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent owner not found")
    return user


def to_history_models(history: list[dict[str, str]]) -> list[AgentChatMessage]:
    return [AgentChatMessage.model_validate(item) for item in history]


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "seller-tools-api"}


@app.get("/", response_class=HTMLResponse)
def root():
    return """
    <!doctype html>
    <html lang="en">
      <head>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <title>Seller Intelligence Tools API</title>
        <style>
          body { font-family: Arial, sans-serif; margin: 0; background: #0f172a; color: #e2e8f0; }
          main { max-width: 920px; margin: 0 auto; padding: 48px 24px; }
          h1 { margin-bottom: 12px; }
          p, li { line-height: 1.6; }
          .card { background: #111827; border: 1px solid #334155; border-radius: 16px; padding: 20px; margin-top: 20px; }
          a { color: #38bdf8; text-decoration: none; }
          code { background: #1e293b; padding: 2px 6px; border-radius: 6px; }
        </style>
      </head>
      <body>
        <main>
          <h1>Seller Intelligence Tools API</h1>
          <p>This service exposes both the tool API and the Azure agent API used by the website.</p>
          <div class="card">
            <h2>Useful links</h2>
            <ul>
              <li><a href="/docs">Swagger Docs</a></li>
              <li><a href="/openapi.json">OpenAPI JSON</a></li>
              <li><a href="/health">Health Check</a></li>
            </ul>
          </div>
          <div class="card">
            <h2>Website endpoints</h2>
            <ul>
              <li><code>POST /auth/login</code></li>
              <li><code>GET /auth/me</code></li>
              <li><code>GET /agent/current</code></li>
              <li><code>POST /agent/create</code></li>
              <li><code>POST /agent/chat</code></li>
              <li><code>POST /agent/chat/reset</code></li>
            </ul>
          </div>
          <div class="card">
            <h2>Tool endpoints</h2>
            <ul>
              <li><code>GET /tools</code></li>
              <li><code>POST /tools/invoke</code></li>
              <li><code>POST /tools/get_dashboard_overview</code></li>
              <li><code>POST /tools/get_dashboard_summary</code></li>
              <li><code>POST /tools/list_products</code></li>
              <li><code>POST /tools/create_product</code></li>
              <li><code>POST /tools/update_product</code></li>
              <li><code>POST /tools/archive_product</code></li>
              <li><code>POST /tools/list_orders</code></li>
              <li><code>POST /tools/create_order</code></li>
            </ul>
          </div>
        </main>
      </body>
    </html>
    """


@app.post("/auth/signup", response_model=core_schemas.UserOut, status_code=status.HTTP_201_CREATED)
def signup(payload: core_schemas.UserCreate, db: Session = Depends(get_db)):
    existing = crud.get_user_by_email(db, payload.email)
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already exists")
    return crud.create_user(db, payload)


@app.post("/auth/login", response_model=core_schemas.Token)
def login(payload: core_schemas.LoginRequest, db: Session = Depends(get_db)):
    user = crud.get_user_by_email(db, payload.email)
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    token = create_access_token(subject=user.email)
    return core_schemas.Token(access_token=token)


@app.get("/auth/me", response_model=core_schemas.UserOut)
def me(current_user: models.User = Depends(get_current_user)):
    return current_user


@app.get("/agent/current", response_model=CurrentAgentResponse)
def current_agent(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    record = get_agent_record(db, seller_id=current_user.id)
    return CurrentAgentResponse(agent=record)


@app.post("/agent/create", response_model=AgentCreateResponse)
def create_agent(
    payload: AgentCreateRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    try:
        created, record = create_or_update_agent(
            db=db,
            user=current_user,
            base_url=get_public_base_url(request),
            custom_instructions=payload.instructions,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    AGENT_CHAT_HISTORY.pop(current_user.id, None)
    return AgentCreateResponse(created=created, agent=record)


@app.post("/agent/chat", response_model=AgentChatResponse)
def agent_chat(
    payload: AgentChatRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    record = get_agent_record(db, seller_id=current_user.id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not created for this user",
        )

    if payload.reset_history:
        history = []
    elif payload.history:
        history = [item.model_dump() for item in payload.history]
    else:
        history = AGENT_CHAT_HISTORY.get(current_user.id, [])

    try:
        reply = run_agent_chat(record=record, prompt=payload.prompt, history=history)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Agent chat failed: {exc}",
        ) from exc

    updated_history = [
        *history,
        {"role": "user", "content": payload.prompt.strip()},
        {"role": "assistant", "content": reply},
    ][-20:]
    AGENT_CHAT_HISTORY[current_user.id] = updated_history

    return AgentChatResponse(
        reply=reply,
        history=to_history_models(updated_history),
    )


@app.post("/agent/chat/reset")
def reset_agent_chat(current_user: models.User = Depends(get_current_user)):
    AGENT_CHAT_HISTORY.pop(current_user.id, None)
    return {"ok": True}


@app.get("/agent/openapi")
def current_agent_openapi(
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    record = get_agent_record(db, seller_id=current_user.id)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not created for this user")
    return build_agent_openapi_spec(
        base_url=get_public_base_url(request),
        agent_key=record.agent_key,
    )


@app.get("/tools", response_model=list[ToolDefinition])
def list_tools(current_user: models.User = Depends(get_current_user)):
    _ = current_user
    return list_tool_definitions()


@app.post("/tools/invoke", response_model=ToolInvokeResponse)
def invoke_tool(
    payload: ToolInvokeRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    try:
        result = execute_tool(
            db=db,
            user=current_user,
            tool_name=payload.tool_name,
            arguments=payload.arguments,
        )
    except ValidationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=exc.errors()) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return ToolInvokeResponse(tool_name=payload.tool_name, result=result)


@app.post("/tools/get_dashboard_overview", response_model=core_schemas.DashboardOverview)
def tool_get_dashboard_overview(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return execute_tool(db=db, user=current_user, tool_name="get_dashboard_overview", arguments={})


@app.post("/tools/get_dashboard_summary", response_model=core_schemas.DashboardSummary)
def tool_get_dashboard_summary(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return execute_tool(db=db, user=current_user, tool_name="get_dashboard_summary", arguments={})


@app.post("/tools/list_products", response_model=list[core_schemas.ProductOut])
def tool_list_products(
    payload: ListProductsToolArgs = Body(default_factory=ListProductsToolArgs),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return execute_tool(
        db=db,
        user=current_user,
        tool_name="list_products",
        arguments=payload.model_dump(exclude_none=True),
    )


@app.post("/tools/create_product", response_model=core_schemas.ProductOut, status_code=status.HTTP_201_CREATED)
def tool_create_product(
    payload: core_schemas.ProductCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    try:
        return execute_tool(
            db=db,
            user=current_user,
            tool_name="create_product",
            arguments=payload.model_dump(),
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@app.post("/tools/update_product", response_model=core_schemas.ProductOut)
def tool_update_product(
    payload: UpdateProductToolArgs,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    try:
        return execute_tool(
            db=db,
            user=current_user,
            tool_name="update_product",
            arguments=payload.model_dump(exclude_none=True),
        )
    except ValueError as exc:
        if str(exc) == "Product not found":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@app.post("/tools/archive_product", response_model=ArchiveProductResult)
def tool_archive_product(
    payload: ArchiveProductToolArgs,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    try:
        return execute_tool(
            db=db,
            user=current_user,
            tool_name="archive_product",
            arguments=payload.model_dump(),
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@app.post("/tools/list_orders", response_model=list[core_schemas.OrderOut])
def tool_list_orders(
    payload: ListOrdersToolArgs = Body(default_factory=ListOrdersToolArgs),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return execute_tool(
        db=db,
        user=current_user,
        tool_name="list_orders",
        arguments=payload.model_dump(exclude_none=True),
    )


@app.post("/tools/create_order", response_model=core_schemas.OrderOut, status_code=status.HTTP_201_CREATED)
def tool_create_order(
    payload: core_schemas.OrderCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    try:
        return execute_tool(
            db=db,
            user=current_user,
            tool_name="create_order",
            arguments=payload.model_dump(),
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@app.post("/agent-tools/{agent_key}/get_dashboard_overview", response_model=core_schemas.DashboardOverview)
def agent_tool_get_dashboard_overview(
    agent_key: str,
    db: Session = Depends(get_db),
):
    user = get_agent_owner_by_key(agent_key, db)
    return execute_tool(db=db, user=user, tool_name="get_dashboard_overview", arguments={})


@app.post("/agent-tools/{agent_key}/get_dashboard_summary", response_model=core_schemas.DashboardSummary)
def agent_tool_get_dashboard_summary(
    agent_key: str,
    db: Session = Depends(get_db),
):
    user = get_agent_owner_by_key(agent_key, db)
    return execute_tool(db=db, user=user, tool_name="get_dashboard_summary", arguments={})


@app.post("/agent-tools/{agent_key}/list_products", response_model=list[core_schemas.ProductOut])
def agent_tool_list_products(
    agent_key: str,
    payload: ListProductsToolArgs = Body(default_factory=ListProductsToolArgs),
    db: Session = Depends(get_db),
):
    user = get_agent_owner_by_key(agent_key, db)
    return execute_tool(
        db=db,
        user=user,
        tool_name="list_products",
        arguments=payload.model_dump(exclude_none=True),
    )


@app.post("/agent-tools/{agent_key}/create_product", response_model=core_schemas.ProductOut, status_code=status.HTTP_201_CREATED)
def agent_tool_create_product(
    agent_key: str,
    payload: core_schemas.ProductCreate,
    db: Session = Depends(get_db),
):
    user = get_agent_owner_by_key(agent_key, db)
    try:
        return execute_tool(
            db=db,
            user=user,
            tool_name="create_product",
            arguments=payload.model_dump(),
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@app.post("/agent-tools/{agent_key}/update_product", response_model=core_schemas.ProductOut)
def agent_tool_update_product(
    agent_key: str,
    payload: UpdateProductToolArgs,
    db: Session = Depends(get_db),
):
    user = get_agent_owner_by_key(agent_key, db)
    try:
        return execute_tool(
            db=db,
            user=user,
            tool_name="update_product",
            arguments=payload.model_dump(exclude_none=True),
        )
    except ValueError as exc:
        if str(exc) == "Product not found":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@app.post("/agent-tools/{agent_key}/archive_product", response_model=ArchiveProductResult)
def agent_tool_archive_product(
    agent_key: str,
    payload: ArchiveProductToolArgs,
    db: Session = Depends(get_db),
):
    user = get_agent_owner_by_key(agent_key, db)
    try:
        return execute_tool(
            db=db,
            user=user,
            tool_name="archive_product",
            arguments=payload.model_dump(),
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@app.post("/agent-tools/{agent_key}/list_orders", response_model=list[core_schemas.OrderOut])
def agent_tool_list_orders(
    agent_key: str,
    payload: ListOrdersToolArgs = Body(default_factory=ListOrdersToolArgs),
    db: Session = Depends(get_db),
):
    user = get_agent_owner_by_key(agent_key, db)
    return execute_tool(
        db=db,
        user=user,
        tool_name="list_orders",
        arguments=payload.model_dump(exclude_none=True),
    )


@app.post("/agent-tools/{agent_key}/create_order", response_model=core_schemas.OrderOut, status_code=status.HTTP_201_CREATED)
def agent_tool_create_order(
    agent_key: str,
    payload: core_schemas.OrderCreate,
    db: Session = Depends(get_db),
):
    user = get_agent_owner_by_key(agent_key, db)
    try:
        return execute_tool(
            db=db,
            user=user,
            tool_name="create_order",
            arguments=payload.model_dump(),
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
