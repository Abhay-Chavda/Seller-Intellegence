"""Backward-compatible re-export for legacy imports.

Tool implementations now live in `app.tools/*` grouped by domain.
"""

from app.tools.registry import TOOL_SPECS, execute_tool, list_tool_definitions

__all__ = ["TOOL_SPECS", "execute_tool", "list_tool_definitions"]
