from typing import Any

from sqlalchemy.orm import Session

from app import crud, models, schemas

from .base import ToolSpec, json_schema


def _dashboard_overview(
    db: Session,
    user: models.User,
    _: schemas.ToolNoArgs,
) -> dict[str, Any]:
    return crud.get_dashboard_overview(db, user=user)


def _dashboard_summary(
    db: Session,
    user: models.User,
    _: schemas.ToolNoArgs,
) -> dict[str, Any]:
    return crud.get_dashboard_summary(db, seller_id=user.id)


DASHBOARD_TOOL_SPECS: dict[str, ToolSpec] = {
    "get_dashboard_overview": ToolSpec(
        name="get_dashboard_overview",
        description="Fetch detailed dashboard analytics for the current seller account.",
        args_model=schemas.ToolNoArgs,
        output_schema=json_schema(schemas.DashboardOverview),
        handler=_dashboard_overview,
    ),
    "get_dashboard_summary": ToolSpec(
        name="get_dashboard_summary",
        description="Fetch top-level dashboard KPIs (products, sales, orders, units).",
        args_model=schemas.ToolNoArgs,
        output_schema=json_schema(schemas.DashboardSummary),
        handler=_dashboard_summary,
    ),
}
