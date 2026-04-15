from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: str
    password: str = Field(min_length=6, max_length=100)


class UserOut(BaseModel):
    id: int
    name: str
    email: str

    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    email: str
    password: str


class ProductBase(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    sku: str = Field(min_length=1, max_length=100)
    sell_price: float = Field(ge=0)
    stock: int = Field(ge=0)
    marketplace: str = Field(min_length=1, max_length=100)


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    title: str | None = None
    sku: str | None = None
    sell_price: float | None = Field(default=None, ge=0)
    stock: int | None = Field(default=None, ge=0)
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
    order_number: str = Field(min_length=1, max_length=120)
    marketplace: str = Field(min_length=1, max_length=100)
    items: list[OrderItemCreate] = Field(min_length=1)


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
    created_at: datetime
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


class DashboardCategoryCount(BaseModel):
    label: str
    value: int


class DashboardMarketplaceMix(BaseModel):
    marketplace: str
    listings: int
    avg_price: float


class DashboardRevenuePoint(BaseModel):
    day: str
    revenue: float
    units: int


class DashboardTopListing(BaseModel):
    sku: str
    title: str
    marketplace: str
    status: str
    quantity: int
    price: float
    competitor_low_price: float | None
    revenue: float
    units_sold: int


class DashboardRecentSale(BaseModel):
    sale_date: str
    sku: str
    title: str
    units_sold: int
    revenue: float


class DashboardAgentRun(BaseModel):
    name: str
    task_type: str
    status: str
    created_at: str


class DashboardOverview(BaseModel):
    source: str
    seller_display_name: str
    company_name: str | None
    total_listings: int
    active_listings: int
    low_stock_items: int
    total_sales: float
    total_units_sold: int
    average_listing_price: float
    prime_listings: int
    total_agents: int
    marketplace_mix: list[DashboardMarketplaceMix]
    revenue_trend: list[DashboardRevenuePoint]
    top_listings: list[DashboardTopListing]
    recent_sales: list[DashboardRecentSale]
    agent_status: list[DashboardCategoryCount]
    recent_agent_runs: list[DashboardAgentRun]
    listing_status: list[DashboardCategoryCount]
    inventory_bands: list[DashboardCategoryCount]


class CompetitorRecordOut(BaseModel):
    id: int
    product_id: int
    competitor_name: str
    price: float
    is_fba: bool
    feedback_count: int
    feedback_rating: float
    timestamp: datetime

    class Config:
        from_attributes = True


class ToolNoArgs(BaseModel):
    pass


class ListProductsToolArgs(BaseModel):
    search: str | None = None
    include_archived: bool = False


class UpdateProductToolArgs(BaseModel):
    product_id: int = Field(gt=0)
    title: str | None = Field(default=None, min_length=1, max_length=255)
    sku: str | None = Field(default=None, min_length=1, max_length=100)
    sell_price: float | None = Field(default=None, ge=0)
    stock: int | None = Field(default=None, ge=0)
    marketplace: str | None = Field(default=None, min_length=1, max_length=100)

    @model_validator(mode="after")
    def require_any_field(self) -> "UpdateProductToolArgs":
        if (
            self.title is None
            and self.sku is None
            and self.sell_price is None
            and self.stock is None
            and self.marketplace is None
        ):
            raise ValueError("At least one product field must be provided for update")
        return self

    def to_product_update(self) -> ProductUpdate:
        return ProductUpdate(
            title=self.title,
            sku=self.sku,
            sell_price=self.sell_price,
            stock=self.stock,
            marketplace=self.marketplace,
        )


class ArchiveProductToolArgs(BaseModel):
    product_id: int = Field(gt=0)


class ListOrdersToolArgs(BaseModel):
    search: str | None = None


class PredictBuyboxToolArgs(BaseModel):
    sku: str = Field(min_length=1, max_length=100)
    SellPrice: float = Field(ge=0)
    ShippingPrice: float = Field(default=0, ge=0)
    MinCompetitorPrice: float = Field(ge=0)
    PositiveFeedbackPercent: float = Field(default=95.0, ge=0, le=100)
    IsFBA: float = Field(default=1.0)

    def to_feature_input(self) -> BuyboxFeatureInput:
        total_price = self.SellPrice + self.ShippingPrice
        price_gap = self.SellPrice - self.MinCompetitorPrice
        price_gap_percent = (
            (price_gap / self.MinCompetitorPrice) * 100 if self.MinCompetitorPrice > 0 else 0.0
        )
        return BuyboxFeatureInput(
            sku=self.sku,
            SellPrice=self.SellPrice,
            ShippingPrice=self.ShippingPrice,
            TotalPrice=total_price,
            MinCompetitorPrice=self.MinCompetitorPrice,
            MinTotalPriceInSnapshot=self.MinCompetitorPrice,
            PriceGap=price_gap,
            TotalPriceGap=price_gap,
            PriceGapPercent=price_gap_percent,
            PriceRank=1.0,
            PriceRankNormalized=1.0,
            TotalCompetitorsInSnapshot=0.0,
            PositiveFeedbackPercent=self.PositiveFeedbackPercent,
            MaxFeedbackInSnapshot=100.0,
            FeedbackGapFromMax=100.0 - self.PositiveFeedbackPercent,
            IsMinSellPrice=1.0 if self.SellPrice <= self.MinCompetitorPrice else 0.0,
            IsMinTotalPrice=1.0 if total_price <= self.MinCompetitorPrice else 0.0,
            IsFBA=self.IsFBA,
        )


class ArchiveProductResult(BaseModel):
    product_id: int
    archived: bool


class ToolDefinition(BaseModel):
    name: str
    description: str
    input_schema: dict[str, Any]
    output_schema: dict[str, Any]


class ToolInvokeRequest(BaseModel):
    tool_name: Literal[
        "get_dashboard_overview",
        "get_dashboard_summary",
        "list_products",
        "create_product",
        "update_product",
        "archive_product",
        "list_orders",
        "create_order",
        "predict_buybox",
    ]
    arguments: dict[str, Any] = Field(default_factory=dict)


class ToolInvokeResponse(BaseModel):
    tool_name: str
    result: Any
