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
