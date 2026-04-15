from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    products: Mapped[list["Product"]] = relationship(back_populates="seller")
    orders: Mapped[list["Order"]] = relationship(back_populates="seller")
    predictions: Mapped[list["BuyboxPrediction"]] = relationship(back_populates="seller")
    agent_tasks: Mapped[list["AgentTask"]] = relationship(back_populates="seller")
    foundry_agent: Mapped["UserFoundryAgent"] = relationship(
        back_populates="seller",
        uselist=False,
    )


class Product(Base):
    __tablename__ = "products"
    __table_args__ = (
        CheckConstraint("sell_price >= 0", name="ck_products_sell_price_non_negative"),
        CheckConstraint("stock >= 0", name="ck_products_stock_non_negative"),
        Index(
            "uq_products_seller_sku_active",
            "seller_id",
            "sku",
            unique=True,
            postgresql_where=text("is_active IS TRUE"),
            sqlite_where=text("is_active = 1"),
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    seller_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    title: Mapped[str] = mapped_column(String(255))
    sku: Mapped[str] = mapped_column(String(100), index=True)
    sell_price: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    stock: Mapped[int] = mapped_column(Integer, default=0)
    marketplace: Mapped[str] = mapped_column(String(100), default="Amazon")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    seller: Mapped["User"] = relationship(back_populates="products")
    order_items: Mapped[list["OrderItem"]] = relationship(back_populates="product")


class Order(Base):
    __tablename__ = "orders"
    __table_args__ = (
        UniqueConstraint("seller_id", "order_number", name="uq_orders_seller_order_number"),
        CheckConstraint("total_amount >= 0", name="ck_orders_total_amount_non_negative"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    seller_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    order_number: Mapped[str] = mapped_column(String(120), index=True)
    marketplace: Mapped[str] = mapped_column(String(100), default="Amazon")
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    seller: Mapped["User"] = relationship(back_populates="orders")
    items: Mapped[list["OrderItem"]] = relationship(back_populates="order", lazy="selectin")


class OrderItem(Base):
    __tablename__ = "order_items"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_order_items_quantity_positive"),
        CheckConstraint("unit_price >= 0", name="ck_order_items_unit_price_non_negative"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), index=True)
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"))

    order: Mapped["Order"] = relationship(back_populates="items")
    product: Mapped["Product"] = relationship(back_populates="order_items")


class BuyboxPrediction(Base):
    __tablename__ = "buybox_predictions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    seller_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    sku: Mapped[str] = mapped_column(String(100), index=True)
    recommended_price: Mapped[float] = mapped_column(Float)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    model_name: Mapped[str] = mapped_column(String(100), default="fallback")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    seller: Mapped["User"] = relationship(back_populates="predictions")


class AgentTask(Base):
    __tablename__ = "agent_tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    seller_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    prompt: Mapped[str] = mapped_column(String(1000))
    action: Mapped[str] = mapped_column(String(120))
    result: Mapped[str] = mapped_column(String(2000))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    seller: Mapped["User"] = relationship(back_populates="agent_tasks")


class CompetitorPriceRecord(Base):
    __tablename__ = "competitor_price_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), index=True)
    competitor_name: Mapped[str] = mapped_column(String(100), default="Competitor")
    price: Mapped[float] = mapped_column(Float)
    is_fba: Mapped[bool] = mapped_column(Boolean, default=True)
    feedback_count: Mapped[int] = mapped_column(Integer, default=0)
    feedback_rating: Mapped[float] = mapped_column(Float, default=0.0)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    product: Mapped["Product"] = relationship(backref="competitor_history")


class UserFoundryAgent(Base):
    __tablename__ = "user_foundry_agents"
    __table_args__ = (
        UniqueConstraint("seller_id", name="uq_user_foundry_agents_seller_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    seller_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    agent_name: Mapped[str] = mapped_column(String(200), index=True)
    agent_version: Mapped[str] = mapped_column(String(40))
    model: Mapped[str] = mapped_column(String(120))
    connection_id: Mapped[str] = mapped_column(String(500))
    openapi_spec_url: Mapped[str] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    seller: Mapped["User"] = relationship(back_populates="foundry_agent")
