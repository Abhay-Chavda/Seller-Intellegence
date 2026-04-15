from typing import Any

from sqlalchemy.orm import Session

from app import crud, models, schemas

from .base import ToolSpec, json_schema


def _list_products(
    db: Session,
    user: models.User,
    args: schemas.ListProductsToolArgs,
) -> list[dict[str, Any]]:
    products = crud.list_products(
        db,
        seller_id=user.id,
        search=args.search,
        include_archived=args.include_archived,
    )
    return [
        schemas.ProductOut.model_validate(product).model_dump(mode="json")
        for product in products
    ]


def _create_product(
    db: Session,
    user: models.User,
    args: schemas.ProductCreate,
) -> dict[str, Any]:
    product = crud.create_product(db, seller_id=user.id, payload=args)
    return schemas.ProductOut.model_validate(product).model_dump(mode="json")


def _update_product(
    db: Session,
    user: models.User,
    args: schemas.UpdateProductToolArgs,
) -> dict[str, Any]:
    product = crud.get_product(db, seller_id=user.id, product_id=args.product_id)
    if product is None:
        raise ValueError("Product not found")
    updated = crud.update_product(db, product=product, payload=args.to_product_update())
    return schemas.ProductOut.model_validate(updated).model_dump(mode="json")


def _archive_product(
    db: Session,
    user: models.User,
    args: schemas.ArchiveProductToolArgs,
) -> dict[str, Any]:
    product = crud.get_product(db, seller_id=user.id, product_id=args.product_id)
    if product is None:
        raise ValueError("Product not found")
    crud.delete_product(db, product=product)
    return {"product_id": args.product_id, "archived": True}


LISTING_TOOL_SPECS: dict[str, ToolSpec] = {
    "list_products": ToolSpec(
        name="list_products",
        description="List seller products with optional search and archived toggle.",
        args_model=schemas.ListProductsToolArgs,
        output_schema=json_schema(list[schemas.ProductOut]),
        handler=_list_products,
    ),
    "create_product": ToolSpec(
        name="create_product",
        description="Create a new product listing for the current seller.",
        args_model=schemas.ProductCreate,
        output_schema=json_schema(schemas.ProductOut),
        handler=_create_product,
    ),
    "update_product": ToolSpec(
        name="update_product",
        description="Update an existing seller product by product_id.",
        args_model=schemas.UpdateProductToolArgs,
        output_schema=json_schema(schemas.ProductOut),
        handler=_update_product,
    ),
    "archive_product": ToolSpec(
        name="archive_product",
        description="Archive (soft-delete) a seller product by product_id.",
        args_model=schemas.ArchiveProductToolArgs,
        output_schema=json_schema(schemas.ArchiveProductResult),
        handler=_archive_product,
    ),
}
