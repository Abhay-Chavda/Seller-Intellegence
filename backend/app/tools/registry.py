from typing import Any

from sqlalchemy.orm import Session

from app import models, schemas

from .base import ToolSpec, foundry_arguments_schema
from .buybox_tools import BUYBOX_TOOL_SPECS
from .dashboard_tools import DASHBOARD_TOOL_SPECS
from .listing_tools import LISTING_TOOL_SPECS
from .order_tools import ORDER_TOOL_SPECS

TOOL_SPECS: dict[str, ToolSpec] = {}
TOOL_SPECS.update(DASHBOARD_TOOL_SPECS)
TOOL_SPECS.update(LISTING_TOOL_SPECS)
TOOL_SPECS.update(ORDER_TOOL_SPECS)
TOOL_SPECS.update(BUYBOX_TOOL_SPECS)


def list_tool_definitions() -> list[schemas.ToolDefinition]:
    return [
        schemas.ToolDefinition(
            name=spec.name,
            description=spec.description,
            input_schema=foundry_arguments_schema(spec.args_model),
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

    args_model = spec.args_model.model_validate(arguments or {})
    return spec.handler(db, user, args_model)


def build_foundry_manifest(base_url: str) -> dict[str, Any]:
    tools = []
    for spec in TOOL_SPECS.values():
        tools.append(
            {
                "name": spec.name,
                "description": spec.description,
                "method": "POST",
                "path": f"/tools/{spec.name}",
                "arguments": foundry_arguments_schema(spec.args_model),
            }
        )

    return {
        "version": "1.0.0",
        "service": "seller_intelligence_tools",
        "base_url": base_url,
        "auth": {
            "type": "bearer_jwt",
            "login_endpoint": "/auth/login",
            "header": "Authorization: Bearer <token>",
        },
        "tools": tools,
    }
