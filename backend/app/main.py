from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.core.config import get_settings
from app.core.security import create_access_token, decode_access_token, verify_password
from app.db import Base, engine, get_db
from app.services.agent import run_agent_task
from app.services.predictor import predictor

app = FastAPI(title="Seller Intelligence API", version="0.1.0")
settings = get_settings()
security = HTTPBearer()

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> models.User:
    token = credentials.credentials
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


@app.get("/dashboard/summary", response_model=schemas.DashboardSummary)
def dashboard_summary(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return crud.get_dashboard_summary(db, seller_id=current_user.id)


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
    return crud.create_product(db, seller_id=current_user.id, payload=payload)


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
    return crud.update_product(db, product=product, payload=payload)


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
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return crud.list_orders(db, seller_id=current_user.id)


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
    recommended_price, confidence, model_name = predictor.predict(payload)
    crud.create_buybox_prediction(
        db=db,
        seller_id=current_user.id,
        features=payload,
        recommended_price=recommended_price,
        confidence=confidence,
        model_name=model_name,
    )
    return schemas.BuyboxPredictionOut(
        recommended_price=recommended_price,
        confidence=confidence,
        model_name=model_name,
    )


@app.post("/agent/chat", response_model=schemas.AgentChatResponse)
def agent_chat(
    payload: schemas.AgentChatRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return run_agent_task(db=db, user=current_user, payload=payload)
