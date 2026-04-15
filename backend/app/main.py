from fastapi import Body, Depends, FastAPI, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import httpx
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.core.config import get_settings
from app.core.security import create_access_token, decode_access_token, verify_password
from app.db import Base, engine, get_db
from app.services.agent import run_agent_task
from app.services.foundry_agent import create_user_foundry_agent, get_user_foundry_agent
from app.services.predictor import predictor
from app.tools import build_foundry_manifest, execute_tool, list_tool_definitions

app = FastAPI(title="Seller Intelligence API", version="0.1.0")
settings = get_settings()
security = HTTPBearer(auto_error=False)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)


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


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/")
def root():
    """Avoid 404 when opening the API URL in a browser; interactive docs live at /docs."""
    return RedirectResponse(url="/docs")


@app.post("/auth/signup", response_model=schemas.UserOut, status_code=status.HTTP_201_CREATED)
def signup(payload: schemas.UserCreate, db: Session = Depends(get_db)):
    existing = crud.get_user_by_email(db, payload.email)
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already exists")
    return crud.create_user(db, payload)


@app.post("/auth/login", response_model=schemas.Token)
def login(payload: schemas.LoginRequest, db: Session = Depends(get_db)):
    user = crud.get_user_by_email(db, payload.email)
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    
    token = create_access_token(subject=user.email)
    return schemas.Token(access_token=token)


@app.get("/auth/me", response_model=schemas.UserOut)
def me(current_user: models.User = Depends(get_current_user)):
    return current_user


@app.get("/foundry/agent", response_model=schemas.FoundryAgentOut)
def get_foundry_agent(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    record = get_user_foundry_agent(db=db, user=current_user)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Foundry agent not created")
    return record


@app.post("/foundry/agent/create", response_model=schemas.FoundryAgentCreateResponse)
def create_foundry_agent(
    payload: schemas.FoundryAgentCreateRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    try:
        return create_user_foundry_agent(db=db, user=current_user, payload=payload)
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to fetch OpenAPI spec: {exc}",
        ) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to create Foundry agent: {exc}",
        ) from exc


@app.get("/dashboard/summary", response_model=schemas.DashboardSummary)
def dashboard_summary(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return crud.get_dashboard_summary(db, seller_id=current_user.id)


@app.get("/dashboard/overview", response_model=schemas.DashboardOverview)
def dashboard_overview(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return crud.get_dashboard_overview(db, user=current_user)


@app.get("/products", response_model=list[schemas.ProductOut])
def get_products(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return crud.list_products(db, seller_id=current_user.id)


@app.post("/products", response_model=schemas.ProductOut, status_code=status.HTTP_201_CREATED)
def create_product(
    payload: schemas.ProductCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    try:
        return crud.create_product(db, seller_id=current_user.id, payload=payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@app.put("/products/{product_id}", response_model=schemas.ProductOut)
def update_product(
    product_id: int,
    payload: schemas.ProductUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    product = crud.get_product(db, seller_id=current_user.id, product_id=product_id)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    try:
        return crud.update_product(db, product=product, payload=payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@app.delete("/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    product = crud.get_product(db, seller_id=current_user.id, product_id=product_id)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    crud.delete_product(db, product=product)


@app.get("/orders", response_model=list[schemas.OrderOut])
def get_orders(
    search: str | None = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return crud.list_orders(db, seller_id=current_user.id, search=search)


@app.post("/orders", response_model=schemas.OrderOut, status_code=status.HTTP_201_CREATED)
def create_order(
    payload: schemas.OrderCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    try:
        return crud.create_order(db, seller_id=current_user.id, payload=payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@app.post("/predict/buybox", response_model=schemas.BuyboxPredictionOut)
def predict_buybox(
    payload: schemas.BuyboxFeatureInput,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    # Fetch real competitor history from DB for this SKU
    history_records = db.query(models.CompetitorPriceRecord).join(models.Product).filter(
        models.Product.sku == payload.sku,
        models.Product.seller_id == current_user.id
    ).all()
    
    # Format for the predictor
    history = [
        {
            "price": r.price,
            "is_fba": r.is_fba,
            "feedback_count": r.feedback_count,
            "feedback_rating": r.feedback_rating
        }
        for r in history_records
    ]

    # PROPER Feature Engineering: Enrich the 4 user inputs to 18 points
    enriched_features = predictor.enrich_features(payload, history=history)

    recommended_price, confidence, model_name = predictor.predict(enriched_features, history=history)
    crud.create_buybox_prediction(
        db=db,
        seller_id=current_user.id,
        features=enriched_features, # Save the full vector
        recommended_price=recommended_price,
        confidence=confidence,
        model_name=model_name,
    )
    return schemas.BuyboxPredictionOut(
        recommended_price=recommended_price,
        confidence=confidence,
        model_name=model_name,
    )


@app.get("/tools", response_model=list[schemas.ToolDefinition])
def list_tools(
    current_user: models.User = Depends(get_current_user),
):
    # Endpoint is authenticated so Azure Foundry can call tools in seller context.
    _ = current_user
    return list_tool_definitions()


@app.get("/tools/foundry-manifest")
def tools_foundry_manifest(request: Request):
    # Public tool manifest endpoint designed for Render-hosted registration in Azure Foundry.
    base_url = str(request.base_url).rstrip("/")
    return build_foundry_manifest(base_url=base_url)


@app.post("/tools/invoke", response_model=schemas.ToolInvokeResponse)
def invoke_tool(
    payload: schemas.ToolInvokeRequest,
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
    return schemas.ToolInvokeResponse(tool_name=payload.tool_name, result=result)


@app.post("/tools/get_dashboard_overview", response_model=schemas.DashboardOverview)
def tool_get_dashboard_overview(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return execute_tool(db=db, user=current_user, tool_name="get_dashboard_overview", arguments={})


@app.post("/tools/get_dashboard_summary", response_model=schemas.DashboardSummary)
def tool_get_dashboard_summary(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return execute_tool(db=db, user=current_user, tool_name="get_dashboard_summary", arguments={})


@app.post("/tools/list_products", response_model=list[schemas.ProductOut])
def tool_list_products(
    payload: schemas.ListProductsToolArgs = Body(default_factory=schemas.ListProductsToolArgs),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return execute_tool(
        db=db,
        user=current_user,
        tool_name="list_products",
        arguments=payload.model_dump(exclude_none=True),
    )


@app.post("/tools/create_product", response_model=schemas.ProductOut, status_code=status.HTTP_201_CREATED)
def tool_create_product(
    payload: schemas.ProductCreate,
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


@app.post("/tools/update_product", response_model=schemas.ProductOut)
def tool_update_product(
    payload: schemas.UpdateProductToolArgs,
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


@app.post("/tools/archive_product", response_model=schemas.ArchiveProductResult)
def tool_archive_product(
    payload: schemas.ArchiveProductToolArgs,
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


@app.post("/tools/list_orders", response_model=list[schemas.OrderOut])
def tool_list_orders(
    payload: schemas.ListOrdersToolArgs = Body(default_factory=schemas.ListOrdersToolArgs),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return execute_tool(
        db=db,
        user=current_user,
        tool_name="list_orders",
        arguments=payload.model_dump(exclude_none=True),
    )


@app.post("/tools/create_order", response_model=schemas.OrderOut, status_code=status.HTTP_201_CREATED)
def tool_create_order(
    payload: schemas.OrderCreate,
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


@app.post("/tools/predict_buybox", response_model=schemas.BuyboxPredictionOut)
def tool_predict_buybox(
    payload: schemas.PredictBuyboxToolArgs,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return execute_tool(
        db=db,
        user=current_user,
        tool_name="predict_buybox",
        arguments=payload.model_dump(),
    )


@app.post("/agent/chat", response_model=schemas.AgentChatResponse)
def agent_chat(
    payload: schemas.AgentChatRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return run_agent_task(db=db, user=current_user, payload=payload)
