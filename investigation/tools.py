"""Tool specs and local dispatch for the Bedrock investigation agent."""

from __future__ import annotations

import json
from typing import Any, Callable

from revenue_engine import get_revenue_case

# Step 1: only get_revenue_case is registered with Bedrock.
TOOL_HANDLERS: dict[str, Callable[..., Any]] = {
    "get_revenue_case": get_revenue_case,
}

GET_REVENUE_CASE_TOOL = {
    "toolSpec": {
        "name": "get_revenue_case",
        "description": (
            "Return the deterministic RevenueTwin financial finding for a case_id. "
            "Use this before explaining any fee discrepancy. Do not invent numbers."
        ),
        "inputSchema": {
            "json": {
                "type": "object",
                "properties": {
                    "case_id": {
                        "type": "string",
                        "description": "Revenue case identifier, e.g. CASE-001",
                    }
                },
                "required": ["case_id"],
            }
        },
    }
}


def tool_config_one_tool() -> dict:
    return {"tools": [GET_REVENUE_CASE_TOOL]}


def dispatch_tool(name: str, tool_input: dict) -> str:
    """Execute a registered tool and return a JSON string for Bedrock toolResult."""
    handler = TOOL_HANDLERS.get(name)
    if handler is None:
        return json.dumps({"error": f"Unknown tool: {name}"})
    try:
        if name == "get_revenue_case":
            result = handler(tool_input["case_id"])
        else:
            result = handler(**tool_input)
        return json.dumps(result)
    except KeyError as exc:
        return json.dumps({"error": f"Unknown case: {exc}"})
    except (OSError, ValueError) as exc:
        return json.dumps({"error": str(exc)})
