from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator


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


class ArchiveProductToolArgs(BaseModel):
    product_id: int = Field(gt=0)


class ListOrdersToolArgs(BaseModel):
    search: str | None = None


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
    ]
    arguments: dict[str, Any] = Field(default_factory=dict)


class ToolInvokeResponse(BaseModel):
    tool_name: str
    result: Any


class AgentOut(BaseModel):
    id: int
    seller_id: int
    agent_id: str
    agent_name: str
    agent_version: str
    instructions: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CurrentAgentResponse(BaseModel):
    agent: AgentOut | None


class AgentCreateRequest(BaseModel):
    instructions: str | None = None


class AgentCreateResponse(BaseModel):
    created: bool
    agent: AgentOut


class AgentChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1)


class AgentChatRequest(BaseModel):
    prompt: str = Field(min_length=1)
    history: list[AgentChatMessage] = Field(default_factory=list)
    reset_history: bool = False


class AgentChatResponse(BaseModel):
    reply: str
    history: list[AgentChatMessage]
