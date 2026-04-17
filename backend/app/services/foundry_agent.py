import re
from typing import Any

import httpx
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.core.config import get_settings
from app.tools.registry import TOOL_SPECS

settings = get_settings()
ALLOWED_TOOL_PATHS = {f"/tools/{tool_name}" for tool_name in TOOL_SPECS.keys()}


def _download_openapi_spec(spec_url: str) -> dict[str, Any]:
    response = httpx.get(spec_url, timeout=20.0)
    response.raise_for_status()
    spec = response.json()
    if not isinstance(spec, dict):
        raise ValueError("OpenAPI response is not a valid JSON object")
    return spec


def _normalize_operation_id(value: str, fallback: str) -> str:
    # Foundry requires operationId characters to be letters, "_" or "-".
    normalized = re.sub(r"[^A-Za-z_-]", "_", value)
    normalized = re.sub(r"_+", "_", normalized).strip("_")
    return normalized or fallback


def _letter_suffix(index: int) -> str:
    letters = "abcdefghijklmnopqrstuvwxyz"
    base = len(letters)
    value = index + 1
    suffix = ""
    while value > 0:
        value -= 1
        suffix = letters[value % base] + suffix
        value //= base
    return suffix


def _prepare_openapi_for_foundry(raw_spec: dict[str, Any]) -> dict[str, Any]:
    spec: dict[str, Any] = dict(raw_spec)
    paths = spec.get("paths")
    if not isinstance(paths, dict):
        raise ValueError("OpenAPI spec does not contain a valid 'paths' object")

    filtered_paths: dict[str, Any] = {
        path: value for path, value in paths.items() if path in ALLOWED_TOOL_PATHS
    }
    if not filtered_paths:
        raise ValueError("OpenAPI spec does not include /tools endpoints required for Foundry")

    used_operation_ids: set[str] = set()
    for path, path_item in filtered_paths.items():
        if not isinstance(path_item, dict):
            continue
        for method, operation in path_item.items():
            if method.lower() not in {"get", "post", "put", "patch", "delete", "options", "head"}:
                continue
            if not isinstance(operation, dict):
                continue
            original_operation_id = str(operation.get("operationId") or f"{method}_{path}")
            normalized_operation_id = _normalize_operation_id(
                original_operation_id,
                fallback="tool_call",
            )
            suffix = 0
            unique_operation_id = normalized_operation_id
            while unique_operation_id in used_operation_ids:
                unique_operation_id = f"{normalized_operation_id}_{_letter_suffix(suffix)}"
                suffix += 1
            used_operation_ids.add(unique_operation_id)
            operation["operationId"] = unique_operation_id
            operation["security"] = [{"bearerAuth": []}]

    spec["paths"] = filtered_paths
    components = spec.setdefault("components", {})
    if not isinstance(components, dict):
        components = {}
        spec["components"] = components
    security_schemes = components.setdefault("securitySchemes", {})
    if not isinstance(security_schemes, dict):
        security_schemes = {}
        components["securitySchemes"] = security_schemes
    security_schemes["bearerAuth"] = {
        "type": "apiKey",
        "name": "Authorization",
        "in": "header",
    }
    spec["security"] = [{"bearerAuth": []}]
    return spec


def get_user_foundry_agent(db: Session, user: models.User) -> models.UserFoundryAgent | None:
    return crud.get_user_foundry_agent(db, seller_id=user.id)


def create_user_foundry_agent(
    db: Session,
    user: models.User,
    payload: schemas.FoundryAgentCreateRequest,
) -> schemas.FoundryAgentCreateResponse:
    existing = crud.get_user_foundry_agent(db, seller_id=user.id)
    if existing is not None:
        return schemas.FoundryAgentCreateResponse(
            created=False,
            agent=schemas.FoundryAgentOut.model_validate(existing),
        )

    project_endpoint = settings.foundry_project_endpoint.strip()
    model_name = settings.foundry_model_deployment_name.strip()
    spec_url = (payload.openapi_spec_url or settings.foundry_tools_openapi_url).strip()
    provided_spec = payload.openapi_spec
    connection_id = (payload.connection_id or settings.foundry_connection_id).strip()
    agent_name = (
        payload.agent_name.strip()
        if payload.agent_name and payload.agent_name.strip()
        else f"{settings.foundry_agent_name_prefix}-{user.id}"
    )

    if not project_endpoint:
        raise ValueError("FOUNDRY_PROJECT_ENDPOINT is not configured")
    if not model_name:
        raise ValueError("FOUNDRY_MODEL_DEPLOYMENT_NAME is not configured")
    if provided_spec is None and not spec_url:
        raise ValueError("OpenAPI spec URL is required")
    if not connection_id:
        raise ValueError("FOUNDRY_CONNECTION_ID is not configured")

    raw_spec = provided_spec if provided_spec is not None else _download_openapi_spec(spec_url)
    prepared_spec = _prepare_openapi_for_foundry(raw_spec)

    try:
        from azure.ai.projects import AIProjectClient
        from azure.ai.projects.models import PromptAgentDefinition
        from azure.identity import DefaultAzureCredential
    except Exception as exc:
        raise ValueError(
            "Azure Foundry SDK packages are missing. Install azure-ai-projects and azure-identity."
        ) from exc

    project = AIProjectClient(
        endpoint=project_endpoint,
        credential=DefaultAzureCredential(),
    )

    openapi_tool = {
        "type": "openapi",
        "openapi": {
            "name": "seller_intelligence_tools",
            "description": "Seller Intelligence tools API integration.",
            "spec": prepared_spec,
            "auth": {
                "type": "project_connection",
                "security_scheme": {
                    "project_connection_id": connection_id,
                },
            },
        },
    }

    agent = project.agents.create_version(
        agent_name=agent_name,
        definition=PromptAgentDefinition(
            model=model_name,
            instructions=(
                "You are a seller intelligence agent. Use tools to answer user questions with seller data."
            ),
            tools=[openapi_tool],
        ),
    )

    record = crud.create_user_foundry_agent(
        db=db,
        seller_id=user.id,
        agent_name=agent.name,
        agent_version=str(agent.version),
        model=model_name,
        connection_id=connection_id,
        openapi_spec_url=spec_url or "<inline>",
    )
    return schemas.FoundryAgentCreateResponse(
        created=True,
        agent=schemas.FoundryAgentOut.model_validate(record),
    )
