from dataclasses import dataclass
from typing import Any, Callable

from pydantic import BaseModel, TypeAdapter
from sqlalchemy.orm import Session

from app import models


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    args_model: type[BaseModel]
    output_schema: dict[str, Any]
    handler: Callable[[Session, models.User, BaseModel], Any]


def json_schema(model: type[BaseModel] | Any) -> dict[str, Any]:
    if isinstance(model, type) and issubclass(model, BaseModel):
        return model.model_json_schema()
    return TypeAdapter(model).json_schema()


def foundry_arguments_schema(model: type[BaseModel]) -> dict[str, Any]:
    """
    Build a compact schema for Azure Foundry/OpenAPI-style tool registration.
    """
    schema = json_schema(model)
    schema.pop("title", None)
    schema.pop("description", None)
    if schema.get("type") == "object":
        schema.setdefault("properties", {})
        schema.setdefault("additionalProperties", False)
    return schema
