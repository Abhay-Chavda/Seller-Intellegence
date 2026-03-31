from pydantic import BaseModel, EmailStr, Field


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=6, max_length=100)


class UserOut(BaseModel):
    id: int
    name: str
    email: EmailStr

    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class ProductBase(BaseModel):
    title: str
    sku: str
    sell_price: float
    stock: int
    marketplace: str


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    title: str | None = None
    sku: str | None = None
    sell_price: float | None = None
    stock: int | None = None
    marketplace: str | None = None


class ProductOut(ProductBase):
    id: int
    seller_id: int

    class Config:
        from_attributes = True


class DashboardSummary(BaseModel):
    total_products: int
    low_stock_items: int
    average_price: float
    total_orders: int
    total_sales: float
    total_units_sold: int


class OrderItemCreate(BaseModel):
    product_id: int
    quantity: int = Field(ge=1)
    unit_price: float = Field(ge=0)


class OrderCreate(BaseModel):
    order_number: str
    marketplace: str
    items: list[OrderItemCreate]


class OrderItemOut(BaseModel):
    id: int
    product_id: int
    quantity: int
    unit_price: float

    class Config:
        from_attributes = True


class OrderOut(BaseModel):
    id: int
    seller_id: int
    order_number: str
    marketplace: str
    total_amount: float
    items: list[OrderItemOut]

    class Config:
        from_attributes = True


class BuyboxFeatureInput(BaseModel):
    sku: str = "UNKNOWN"
    SellPrice: float
    ShippingPrice: float
    TotalPrice: float
    MinCompetitorPrice: float
    MinTotalPriceInSnapshot: float
    PriceGap: float
    TotalPriceGap: float
    PriceGapPercent: float
    PriceRank: float
    PriceRankNormalized: float
    TotalCompetitorsInSnapshot: float
    PositiveFeedbackPercent: float
    MaxFeedbackInSnapshot: float
    FeedbackGapFromMax: float
    IsMinSellPrice: float
    IsMinTotalPrice: float
    IsFBA: float


class BuyboxPredictionOut(BaseModel):
    recommended_price: float
    confidence: float
    model_name: str


class AgentChatRequest(BaseModel):
    prompt: str


class AgentChatResponse(BaseModel):
    action: str
    result: str
