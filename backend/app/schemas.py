from datetime import datetime

from pydantic import BaseModel, Field


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
    role: str
    subscription_type: str

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
    marketplace_mix: list[DashboardMarketplaceMix]
    revenue_trend: list[DashboardRevenuePoint]
    top_listings: list[DashboardTopListing]
    recent_sales: list[DashboardRecentSale]
    listing_status: list[DashboardCategoryCount]
    inventory_bands: list[DashboardCategoryCount]


class AdminSummary(BaseModel):
    total_users: int
    admin_users: int
    demo_subscriptions: int
    users_with_agents: int
    total_orders: int
    total_products: int
    total_sales: float


class AdminSubscriptionStat(BaseModel):
    subscription_type: str
    users_count: int


class AdminUserUsage(BaseModel):
    id: int
    name: str
    email: str
    role: str
    subscription_type: str
    created_at: datetime
    products_count: int
    orders_count: int
    total_sales: float
    last_order_at: datetime | None
    last_product_update_at: datetime | None
    agent_name: str | None
    agent_version: str | None
    project_endpoint: str | None
    agent_updated_at: datetime | None


class AdminAgentUsage(BaseModel):
    seller_id: int
    seller_name: str
    seller_email: str
    subscription_type: str
    agent_name: str
    agent_version: str
    project_endpoint: str | None
    agent_updated_at: datetime
    orders_count: int
    products_count: int
    total_sales: float
