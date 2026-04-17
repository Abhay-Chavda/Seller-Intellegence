from typing import Any

from sqlalchemy.orm import Session

from app import crud, schemas
from app.core.config import get_settings
from app.models import User

settings = get_settings()


def _extract_output_text(response: Any) -> str:
    output_text = getattr(response, "output_text", None)
    if isinstance(output_text, str) and output_text.strip():
        return output_text.strip()

    dump = None
    if hasattr(response, "model_dump"):
        dump = response.model_dump()
    elif isinstance(response, dict):
        dump = response

    if not isinstance(dump, dict):
        return "No response text returned by Foundry agent."

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
                continue
            if isinstance(text_val, dict):
                value = text_val.get("value")
                if isinstance(value, str) and value.strip():
                    chunks.append(value.strip())
                    continue

    if chunks:
        return "\n".join(chunks)

    return "No response text returned by Foundry agent."


def run_agent_task(db: Session, user: User, payload: schemas.AgentChatRequest) -> schemas.AgentChatResponse:
    prompt = payload.prompt.strip()
    if not prompt:
        raise ValueError("Prompt cannot be empty")

    record = crud.get_user_foundry_agent(db, seller_id=user.id)
    if record is None:
        raise ValueError("Foundry agent is not created for this user. Call /foundry/agent/create first.")

    project_endpoint = settings.foundry_project_endpoint.strip()
    if not project_endpoint:
        raise ValueError("FOUNDRY_PROJECT_ENDPOINT is not configured")

    try:
        from azure.ai.projects import AIProjectClient
        from azure.identity import DefaultAzureCredential
    except Exception as exc:
        raise ValueError(
            "Azure Foundry SDK packages are missing. Install azure-ai-projects and azure-identity."
        ) from exc

    project = AIProjectClient(
        endpoint=project_endpoint,
        credential=DefaultAzureCredential(),
    )
    openai = project.get_openai_client()

    agent_reference = {
        "name": record.agent_name,
        "version": record.agent_version,
        "type": "agent_reference",
    }

    response = openai.responses.create(
        input=prompt,
        extra_body={"agent_reference": agent_reference},
    )
    result = _extract_output_text(response)
    action = "foundry_agent_chat"
    crud.create_agent_task(db, user.id, prompt, action, result)
    return schemas.AgentChatResponse(action=action, result=result)
