import os
import re
import secrets
from typing import Any, TYPE_CHECKING

# Avoid importing heavy dependencies (sqlalchemy, app) at module import time to
# prevent import-time failures in environments where those packages may be
# incompatible or not installed. Use TYPE_CHECKING imports for type hints.
if TYPE_CHECKING:
    from sqlalchemy.orm import Session  # type: ignore
    from app import models  # type: ignore
else:
    Session = object
    models = None

# Import AzureAgentRecord only inside functions to avoid importing SQLAlchemy at
# module import time (some environments have SQLAlchemy import-time issues).
from .tool_registry import list_tool_definitions

DEFAULT_AGENT_INSTRUCTIONS = """
You are a seller operations assistant for Seller Intelligence.
Use the available Seller Intelligence tools whenever the user asks about dashboard numbers, products, inventory, or orders.
Ask short follow-up questions when required information is missing.
Do not invent product IDs, order numbers, prices, or stock values.
Keep answers clear and practical.
""".strip()


def _clean_env_value(value: str) -> str:
    return value.strip().strip('"').strip("'")


def _normalize_project_endpoint(value: str) -> str:
    cleaned = _clean_env_value(value).rstrip("/")
    if not cleaned:
        return ""
    if "/api/projects/" in cleaned:
        return cleaned

    default_project_endpoint = _get_env(
        "PROJECT_ENDPOINT",
        "AZURE_AI_PROJECT_ENDPOINT",
        "AZURE_EXISTING_AIPROJECT_ENDPOINT",
        "FOUNDRY_PROJECT_ENDPOINT",
    ).rstrip("/")
    if default_project_endpoint and (
        cleaned == default_project_endpoint
        or default_project_endpoint.startswith(cleaned)
    ):
        return default_project_endpoint
    return cleaned


def _get_env(*names: str) -> str:
    for name in names:
        value = _clean_env_value(os.getenv(name, ""))
        if value:
            return value
    return ""


def _require_env(*names: str) -> str:
    value = _get_env(*names)
    if value:
        return value
    raise ValueError(f"Missing required environment variable. Expected one of: {', '.join(names)}")


def _sanitize_agent_name(value: str) -> str:
    sanitized = re.sub(r"[^a-zA-Z0-9-]+", "-", value).strip("-").lower()
    return sanitized[:63] or "seller-agent"


def _format_azure_error(exc: Exception) -> str:
    message = str(exc).strip()
    lowered = message.lower()
    if (
        "defaultazurecredential" in lowered
        or "azureclicredential" in lowered
        or "credentialunavailableerror" in lowered
        or "clientauthenticationerror" in lowered
        or "please run 'az login'" in lowered
        or "az login" in lowered
    ):
        return (
            "Azure authentication failed. For local demo usage, run `az login` in your terminal "
            "and make sure your account can access the Foundry project."
        )
    return message or "Azure request failed."


def get_project_endpoint(override: str | None = None) -> str:
    if override:
        cleaned = _normalize_project_endpoint(override)
        if cleaned:
            return cleaned
    return _normalize_project_endpoint(_require_env(
        "PROJECT_ENDPOINT",
        "AZURE_AI_PROJECT_ENDPOINT",
        "AZURE_EXISTING_AIPROJECT_ENDPOINT",
        "FOUNDRY_PROJECT_ENDPOINT",
    ))


def parse_existing_agent_reference(raw_value: str | None) -> tuple[str, str | None] | None:
    if not raw_value:
        return None

    cleaned = _clean_env_value(raw_value)
    if not cleaned:
        return None

    if ":" in cleaned:
        agent_name, version = cleaned.rsplit(":", 1)
        return agent_name.strip(), version.strip() or None
    return cleaned, None


def get_existing_agent_reference() -> tuple[str, str | None] | None:
    return parse_existing_agent_reference(_get_env("AZURE_EXISTING_AGENT_ID"))


def get_project_client(project_endpoint: str | None = None):
    try:
        from azure.identity import DefaultAzureCredential
        from azure.ai.projects import AIProjectClient
    except Exception as exc:
        raise ValueError(
            "Azure SDK packages are missing. Install azure-ai-projects, azure-identity, and openai."
        ) from exc

    endpoint = get_project_endpoint(project_endpoint)
    return AIProjectClient(
        endpoint=endpoint,
        credential=DefaultAzureCredential(),
    )


def get_model_deployment_name(override: str | None = None) -> str:
    if override:
        cleaned = _clean_env_value(override)
        if cleaned:
            return cleaned
    return _require_env(
        "MODEL_DEPLOYMENT_NAME",
        "AZURE_AI_MODEL_DEPLOYMENT_NAME",
        "FOUNDRY_MODEL_DEPLOYMENT_NAME",
    )


def get_agent_record(db: "Session", seller_id: int) -> "AzureAgentRecord | None":
    from .agent_models import AzureAgentRecord

    return db.query(AzureAgentRecord).filter(AzureAgentRecord.seller_id == seller_id).one_or_none()


def get_agent_record_by_key(db: "Session", agent_key: str) -> "AzureAgentRecord | None":
    from .agent_models import AzureAgentRecord

    return db.query(AzureAgentRecord).filter(AzureAgentRecord.agent_key == agent_key).one_or_none()


def delete_agent_record(db: "Session", seller_id: int) -> bool:
    record = get_agent_record(db, seller_id=seller_id)
    if record is None:
        return False
    db.delete(record)
    db.commit()
    return True


def build_agent_openapi_spec(base_url: str, agent_key: str) -> dict[str, Any]:
    spec: dict[str, Any] = {
        "openapi": "3.1.0",
        "info": {
            "title": "Seller Intelligence Agent Tools",
            "version": "1.0.0",
            "description": "Anonymous agent tool endpoints scoped by agent key.",
        },
        "servers": [{"url": base_url}],
        "paths": {},
    }

    for tool in list_tool_definitions():
        path = f"/agent-tools/{agent_key}/{tool.name}"
        operation: dict[str, Any] = {
            "operationId": tool.name,
            "summary": tool.description,
            "description": tool.description,
            "responses": {
                "200": {
                    "description": "Successful tool response",
                    "content": {
                        "application/json": {
                            "schema": tool.output_schema,
                        }
                    },
                }
            },
        }

        properties = tool.input_schema.get("properties", {})
        required = tool.input_schema.get("required", [])
        if properties or required:
            operation["requestBody"] = {
                "required": True,
                "content": {
                    "application/json": {
                        "schema": tool.input_schema,
                    }
                },
            }

        spec["paths"][path] = {"post": operation}

    return spec


def _build_openapi_tool(base_url: str, agent_key: str):
    try:
        from azure.ai.projects.models import (
            OpenApiAnonymousAuthDetails,
            OpenApiFunctionDefinition,
            OpenApiTool,
        )
    except Exception as exc:
        raise ValueError(
            "Azure SDK packages are missing. Install azure-ai-projects, azure-identity, and openai."
        ) from exc

    spec = build_agent_openapi_spec(base_url=base_url, agent_key=agent_key)
    return OpenApiTool(
        openapi=OpenApiFunctionDefinition(
            name="seller_intelligence_tools",
            spec=spec,
            description="Seller Intelligence dashboard, product, and order tools.",
            auth=OpenApiAnonymousAuthDetails(),
        )
    )


def create_or_update_agent(
    db: "Session",
    user: "models.User",
    base_url: str,
    custom_instructions: str | None = None,
    existing_agent_id: str | None = None,
    project_endpoint: str | None = None,
    model_deployment_name: str | None = None,
    agent_name_override: str | None = None,
) -> tuple[bool, "AzureAgentRecord"]:
    # import model here to avoid import-time SQLAlchemy issues
    from .agent_models import AzureAgentRecord

    existing = get_agent_record(db, seller_id=user.id)
    created = existing is None
    existing_agent_reference = parse_existing_agent_reference(existing_agent_id) or get_existing_agent_reference()
    resolved_project_endpoint = (
        _normalize_project_endpoint(project_endpoint or "")
        or (existing.project_endpoint if existing and existing.project_endpoint else "")
        or get_project_endpoint()
    )

    agent_prefix = _get_env("AGENT_NAME_PREFIX") or "seller-agent"
    agent_name = (
        _sanitize_agent_name(agent_name_override)
        if agent_name_override and _clean_env_value(agent_name_override)
        else existing.agent_name
        if existing
        else _sanitize_agent_name(f"{agent_prefix}-{user.id}")
    )
    agent_key = existing.agent_key if existing else secrets.token_urlsafe(24)

    extra_text = (custom_instructions or "").strip()
    if extra_text:
        instructions = f"{DEFAULT_AGENT_INSTRUCTIONS}\n\nUser context:\n{extra_text}"
    elif existing:
        instructions = existing.instructions
    else:
        instructions = DEFAULT_AGENT_INSTRUCTIONS

    try:
        from azure.ai.projects.models import PromptAgentDefinition
    except Exception as exc:
        raise ValueError(
            "Azure SDK packages are missing. Install azure-ai-projects, azure-identity, and openai."
        ) from exc

    openapi_tool = _build_openapi_tool(base_url=base_url, agent_key=agent_key)
    resolved_agent_name = existing_agent_reference[0] if existing_agent_reference and existing_agent_reference[0] else agent_name

    try:
        project = get_project_client(resolved_project_endpoint)
        agent = project.agents.create_version(
            agent_name=resolved_agent_name,
            definition=PromptAgentDefinition(
                model=get_model_deployment_name(model_deployment_name),
                instructions=instructions,
                tools=[openapi_tool],
            ),
        )
    except Exception as exc:
        raise ValueError(_format_azure_error(exc)) from exc

    record = existing or AzureAgentRecord(
        seller_id=user.id,
        agent_key=agent_key,
        agent_name=resolved_agent_name,
        agent_id=str(agent.id),
        agent_version=str(agent.version),
        project_endpoint=resolved_project_endpoint,
        instructions=instructions,
    )
    record.agent_id = str(agent.id)
    record.agent_name = str(agent.name)
    record.agent_version = str(agent.version)
    record.project_endpoint = resolved_project_endpoint
    record.instructions = instructions

    db.add(record)
    db.commit()
    db.refresh(record)
    return created, record


def extract_output_text(response: Any) -> str:
    output_text = getattr(response, "output_text", None)
    if isinstance(output_text, str) and output_text.strip():
        return output_text.strip()

    dump = None
    if hasattr(response, "model_dump"):
        dump = response.model_dump()
    elif isinstance(response, dict):
        dump = response

    if not isinstance(dump, dict):
        return "No response text returned by the agent."

    fallback_text = dump.get("output_text")
    if isinstance(fallback_text, str) and fallback_text.strip():
        return fallback_text.strip()

    chunks: list[str] = []
    for item in dump.get("output", []) or []:
        if not isinstance(item, dict) or item.get("type") != "message":
            continue
        for block in item.get("content", []) or []:
            if not isinstance(block, dict):
                continue
            text_val = block.get("text")
            if isinstance(text_val, str) and text_val.strip():
                chunks.append(text_val.strip())
            elif isinstance(text_val, dict):
                value = text_val.get("value")
                if isinstance(value, str) and value.strip():
                    chunks.append(value.strip())

    if chunks:
        return "\n".join(chunks)
    return "No response text returned by the agent."


def run_agent_chat(
    record: "AzureAgentRecord",
    prompt: str,
    history: list[dict[str, str]] | None = None,
) -> str:
    cleaned_prompt = prompt.strip()
    if not cleaned_prompt:
        raise ValueError("Prompt cannot be empty")

    try:
        project = get_project_client(record.project_endpoint)
        openai = project.get_openai_client()
    except Exception as exc:
        raise ValueError(_format_azure_error(exc)) from exc

    input_items: list[dict[str, str]] = []
    for item in history or []:
        role = (item.get("role") or "").strip()
        content = (item.get("content") or "").strip()
        if role in {"user", "assistant"} and content:
            input_items.append({"role": role, "content": content})
    input_items.append({"role": "user", "content": cleaned_prompt})

    try:
        response = openai.responses.create(
            input=input_items,
            extra_body={
                "agent_reference": {
                    "name": record.agent_name,
                    "type": "agent_reference",
                    "version": record.agent_version,
                }
            },
            store=False,
        )
    except Exception as exc:
        raise ValueError(_format_azure_error(exc)) from exc
    return extract_output_text(response)
