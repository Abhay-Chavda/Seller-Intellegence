from dataclasses import dataclass
from typing import Any, Callable

from pydantic import BaseModel, TypeAdapter
from sqlalchemy.orm import Session

from app import crud, models, schemas as core_schemas

from .schemas import (
    ArchiveProductResult,
    ArchiveProductToolArgs,
    ListOrdersToolArgs,
    ListProductsToolArgs,
    ToolDefinition,
    ToolNoArgs,
    UpdateProductToolArgs,
)


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    args_model: type[BaseModel]
    output_schema: dict[str, Any]
    handler: Callable[[Session, models.User, BaseModel], Any]


def json_schema(model_type: Any) -> dict[str, Any]:
    if hasattr(model_type, "model_json_schema"):
        return model_type.model_json_schema()
    return TypeAdapter(model_type).json_schema()


def _dashboard_overview(
    db: Session,
    user: models.User,
    _: BaseModel,
) -> dict[str, Any]:
    return crud.get_dashboard_overview(db, user=user)


def _dashboard_summary(
    db: Session,
    user: models.User,
    _: BaseModel,
) -> dict[str, Any]:
    return crud.get_dashboard_summary(db, seller_id=user.id)


def _list_products(
    db: Session,
    user: models.User,
    args: ListProductsToolArgs,
) -> list[dict[str, Any]]:
    products = crud.list_products(
        db,
        seller_id=user.id,
        search=args.search,
        include_archived=args.include_archived,
    )
    return [core_schemas.ProductOut.model_validate(product).model_dump(mode="json") for product in products]


def _create_product(
    db: Session,
    user: models.User,
    args: core_schemas.ProductCreate,
) -> dict[str, Any]:
    product = crud.create_product(db, seller_id=user.id, payload=args)
    return core_schemas.ProductOut.model_validate(product).model_dump(mode="json")


def _update_product(
    db: Session,
    user: models.User,
    args: UpdateProductToolArgs,
) -> dict[str, Any]:
    product = crud.get_product(db, seller_id=user.id, product_id=args.product_id)
    if product is None:
        raise ValueError("Product not found")

    payload = core_schemas.ProductUpdate(
        title=args.title,
        sku=args.sku,
        sell_price=args.sell_price,
        stock=args.stock,
        marketplace=args.marketplace,
    )
    updated = crud.update_product(db, product=product, payload=payload)
    return core_schemas.ProductOut.model_validate(updated).model_dump(mode="json")


def _archive_product(
    db: Session,
    user: models.User,
    args: ArchiveProductToolArgs,
) -> dict[str, Any]:
    product = crud.get_product(db, seller_id=user.id, product_id=args.product_id)
    if product is None:
        raise ValueError("Product not found")
    crud.delete_product(db, product=product)
    return ArchiveProductResult(product_id=args.product_id, archived=True).model_dump(mode="json")


def _list_orders(
    db: Session,
    user: models.User,
    args: ListOrdersToolArgs,
) -> list[dict[str, Any]]:
    orders = crud.list_orders(db, seller_id=user.id, search=args.search)
    return [core_schemas.OrderOut.model_validate(order).model_dump(mode="json") for order in orders]


def _create_order(
    db: Session,
    user: models.User,
    args: core_schemas.OrderCreate,
) -> dict[str, Any]:
    order = crud.create_order(db, seller_id=user.id, payload=args)
    return core_schemas.OrderOut.model_validate(order).model_dump(mode="json")


TOOL_SPECS: dict[str, ToolSpec] = {
    "get_dashboard_overview": ToolSpec(
        name="get_dashboard_overview",
        description="Get the full seller dashboard overview for the logged-in user.",
        args_model=ToolNoArgs,
        output_schema=json_schema(core_schemas.DashboardOverview),
        handler=_dashboard_overview,
    ),
    "get_dashboard_summary": ToolSpec(
        name="get_dashboard_summary",
        description="Get top-level dashboard numbers for the logged-in user.",
        args_model=ToolNoArgs,
        output_schema=json_schema(core_schemas.DashboardSummary),
        handler=_dashboard_summary,
    ),
    "list_products": ToolSpec(
        name="list_products",
        description="List products for the logged-in user.",
        args_model=ListProductsToolArgs,
        output_schema=json_schema(list[core_schemas.ProductOut]),
        handler=_list_products,
    ),
    "create_product": ToolSpec(
        name="create_product",
        description="Create a new product for the logged-in user.",
        args_model=core_schemas.ProductCreate,
        output_schema=json_schema(core_schemas.ProductOut),
        handler=_create_product,
    ),
    "update_product": ToolSpec(
        name="update_product",
        description="Update a product for the logged-in user.",
        args_model=UpdateProductToolArgs,
        output_schema=json_schema(core_schemas.ProductOut),
        handler=_update_product,
    ),
    "archive_product": ToolSpec(
        name="archive_product",
        description="Archive a product for the logged-in user.",
        args_model=ArchiveProductToolArgs,
        output_schema=json_schema(ArchiveProductResult),
        handler=_archive_product,
    ),
    "list_orders": ToolSpec(
        name="list_orders",
        description="List orders for the logged-in user.",
        args_model=ListOrdersToolArgs,
        output_schema=json_schema(list[core_schemas.OrderOut]),
        handler=_list_orders,
    ),
    "create_order": ToolSpec(
        name="create_order",
        description="Create a new order for the logged-in user.",
        args_model=core_schemas.OrderCreate,
        output_schema=json_schema(core_schemas.OrderOut),
        handler=_create_order,
    ),
}


def list_tool_definitions() -> list[ToolDefinition]:
    return [
        ToolDefinition(
            name=spec.name,
            description=spec.description,
            input_schema=spec.args_model.model_json_schema(),
            output_schema=spec.output_schema,
        )
        for spec in TOOL_SPECS.values()
    ]


def execute_tool(
    db: Session,
    user: models.User,
    tool_name: str,
    arguments: dict[str, Any] | None = None,
) -> Any:
    spec = TOOL_SPECS.get(tool_name)
    if spec is None:
        raise ValueError(f"Unknown tool '{tool_name}'")

    parsed_args = spec.args_model.model_validate(arguments or {})
    return spec.handler(db, user, parsed_args)
