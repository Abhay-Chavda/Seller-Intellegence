from fastapi import APIRouter, Body, Depends, HTTPException, Request, status
import httpx
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.core.security import create_access_token, verify_password
from app.db import get_db
from app.services.foundry_agent import create_user_foundry_agent, get_user_foundry_agent
from app.tools import build_foundry_manifest, execute_tool, list_tool_definitions

from .auth import get_current_user

router = APIRouter()


@router.post("/auth/signup", response_model=schemas.UserOut, status_code=status.HTTP_201_CREATED)
def signup(payload: schemas.UserCreate, db: Session = Depends(get_db)):
    existing = crud.get_user_by_email(db, payload.email)
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already exists")
    return crud.create_user(db, payload)


@router.post("/auth/login", response_model=schemas.Token)
def login(payload: schemas.LoginRequest, db: Session = Depends(get_db)):
    user = crud.get_user_by_email(db, payload.email)
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    token = create_access_token(subject=user.email)
    return schemas.Token(access_token=token)


@router.get("/auth/me", response_model=schemas.UserOut)
def me(current_user: models.User = Depends(get_current_user)):
    return current_user


@router.get("/foundry/agent", response_model=schemas.FoundryAgentOut)
def get_foundry_agent(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    record = get_user_foundry_agent(db=db, user=current_user)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Foundry agent not created")
    return record


@router.post("/foundry/agent/create", response_model=schemas.FoundryAgentCreateResponse)
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


@router.get("/tools", response_model=list[schemas.ToolDefinition])
def list_tools(current_user: models.User = Depends(get_current_user)):
    _ = current_user
    return list_tool_definitions()


@router.get("/tools/foundry-manifest")
def tools_foundry_manifest(request: Request):
    base_url = str(request.base_url).rstrip("/")
    return build_foundry_manifest(base_url=base_url)


@router.post("/tools/invoke", response_model=schemas.ToolInvokeResponse)
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


@router.post("/tools/get_dashboard_overview", response_model=schemas.DashboardOverview)
def tool_get_dashboard_overview(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return execute_tool(db=db, user=current_user, tool_name="get_dashboard_overview", arguments={})


@router.post("/tools/get_dashboard_summary", response_model=schemas.DashboardSummary)
def tool_get_dashboard_summary(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return execute_tool(db=db, user=current_user, tool_name="get_dashboard_summary", arguments={})


@router.post("/tools/list_products", response_model=list[schemas.ProductOut])
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


@router.post("/tools/create_product", response_model=schemas.ProductOut, status_code=status.HTTP_201_CREATED)
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


@router.post("/tools/update_product", response_model=schemas.ProductOut)
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


@router.post("/tools/archive_product", response_model=schemas.ArchiveProductResult)
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


@router.post("/tools/list_orders", response_model=list[schemas.OrderOut])
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


@router.post("/tools/create_order", response_model=schemas.OrderOut, status_code=status.HTTP_201_CREATED)
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


@router.post("/tools/predict_buybox", response_model=schemas.BuyboxPredictionOut)
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
