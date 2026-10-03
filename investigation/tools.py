"""Tool specs and local dispatch for the Bedrock investigation agent."""

from __future__ import annotations

import json
from typing import Any, Callable

from revenue_engine import get_case_evidence, get_revenue_case

TOOL_HANDLERS: dict[str, Callable[..., Any]] = {
    "get_revenue_case": get_revenue_case,
    "get_case_evidence": get_case_evidence,
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

GET_CASE_EVIDENCE_TOOL = {
    "toolSpec": {
        "name": "get_case_evidence",
        "description": (
            "Return the ordered list of evidence documents for a case_id. "
            "Use this after get_revenue_case to inspect agreements, exceptions, "
            "and billing configuration. Do not invent documents."
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
    """Step 1: only get_revenue_case."""
    return {"tools": [GET_REVENUE_CASE_TOOL]}


def tool_config_both_tools() -> dict:
    """Step 2: get_revenue_case and get_case_evidence."""
    return {"tools": [GET_REVENUE_CASE_TOOL, GET_CASE_EVIDENCE_TOOL]}


def dispatch_tool(name: str, tool_input: dict) -> str:
    """Execute a registered tool and return a JSON string for Bedrock toolResult."""
    handler = TOOL_HANDLERS.get(name)
    if handler is None:
        return json.dumps({"error": f"Unknown tool: {name}"})
    try:
        if name in ("get_revenue_case", "get_case_evidence"):
            result = handler(tool_input["case_id"])
        else:
            result = handler(**tool_input)
        # Bedrock Converse toolResult json must be an object, not an array.
        if name == "get_case_evidence":
            return json.dumps({"case_id": tool_input["case_id"], "evidence": result})
        return json.dumps(result)
    except KeyError as exc:
        return json.dumps({"error": f"Unknown case: {exc}"})
    except (OSError, ValueError) as exc:
        return json.dumps({"error": str(exc)})
