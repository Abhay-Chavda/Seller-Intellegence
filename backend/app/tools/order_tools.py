from typing import Any

from sqlalchemy.orm import Session

from app import crud, models, schemas

from .base import ToolSpec, json_schema


def _list_orders(
    db: Session,
    user: models.User,
    args: schemas.ListOrdersToolArgs,
) -> list[dict[str, Any]]:
    orders = crud.list_orders(db, seller_id=user.id, search=args.search)
    return [schemas.OrderOut.model_validate(order).model_dump(mode="json") for order in orders]


def _create_order(
    db: Session,
    user: models.User,
    args: schemas.OrderCreate,
) -> dict[str, Any]:
    order = crud.create_order(db, seller_id=user.id, payload=args)
    return schemas.OrderOut.model_validate(order).model_dump(mode="json")


ORDER_TOOL_SPECS: dict[str, ToolSpec] = {
    "list_orders": ToolSpec(
        name="list_orders",
        description="List seller orders with optional search by order number or marketplace.",
        args_model=schemas.ListOrdersToolArgs,
        output_schema=json_schema(list[schemas.OrderOut]),
        handler=_list_orders,
    ),
    "create_order": ToolSpec(
        name="create_order",
        description="Create an order with one or more order items for seller products.",
        args_model=schemas.OrderCreate,
        output_schema=json_schema(schemas.OrderOut),
        handler=_create_order,
    ),
}
