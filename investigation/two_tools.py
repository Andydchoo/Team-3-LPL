"""Step 2: prove Bedrock can call get_revenue_case and get_case_evidence."""

from __future__ import annotations

import json
import os
from typing import Any

from integration.bedrock_runtime import create_bedrock_client
from botocore.exceptions import BotoCoreError, ClientError

from .tools import dispatch_tool, tool_config_both_tools

DEFAULT_REGION = "us-east-1"
DEFAULT_MODEL_ID = "amazon.nova-lite-v1:0"
MAX_TURNS = 6
REQUIRED_TOOLS = ("get_revenue_case", "get_case_evidence")

SYSTEM_PROMPT = (
    "You are the RevenueTwin investigation agent. "
    "For this smoke test you MUST call both tools for case_id CASE-001: "
    "1) get_revenue_case, then 2) get_case_evidence. "
    "Do not invent financial numbers or documents. "
    "After both tools return, reply with one short sentence naming the "
    "household and how many evidence documents were returned."
)


def _model_id() -> str:
    return os.environ.get("BEDROCK_MODEL_ID", DEFAULT_MODEL_ID)


def _region() -> str:
    return (
        os.environ.get("AWS_REGION")
        or os.environ.get("AWS_DEFAULT_REGION")
        or DEFAULT_REGION
    )


def _text_from_content(content: list[dict[str, Any]]) -> str:
    parts = [block["text"] for block in content if "text" in block]
    return "\n".join(parts).strip()


def _tool_uses(content: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [block["toolUse"] for block in content if "toolUse" in block]


def _called_tool_names(tool_calls: list[dict[str, Any]]) -> set[str]:
    return {call["name"] for call in tool_calls}


def run_two_tool_smoke(case_id: str = "CASE-001") -> dict[str, Any]:
    """Ask Bedrock to call both investigation tools and return a debug summary.

    Raises ClientError/BotoCoreError on AWS failures so the caller can see them.
    """
    client = create_bedrock_client()
    messages: list[dict[str, Any]] = [
        {
            "role": "user",
            "content": [
                {
                    "text": (
                        f"Run the two-tool smoke test for {case_id}. "
                        "Call get_revenue_case first, then get_case_evidence."
                    )
                }
            ],
        }
    ]

    tool_calls: list[dict[str, Any]] = []
    final_text = ""

    for _ in range(MAX_TURNS):
        response = client.converse(
            modelId=_model_id(),
            system=[{"text": SYSTEM_PROMPT}],
            messages=messages,
            toolConfig=tool_config_both_tools(),
        )
        output_message = response["output"]["message"]
        content = output_message["content"]
        stop_reason = response.get("stopReason")
        messages.append(output_message)

        uses = _tool_uses(content)
        if uses:
            tool_result_content = []
            for use in uses:
                name = use["name"]
                tool_input = use.get("input") or {}
                tool_use_id = use["toolUseId"]
                payload = dispatch_tool(name, tool_input)
                tool_calls.append(
                    {
                        "name": name,
                        "input": tool_input,
                        "result_preview": payload[:500],
                    }
                )
                tool_result_content.append(
                    {
                        "toolResult": {
                            "toolUseId": tool_use_id,
                            "content": [{"json": json.loads(payload)}],
                        }
                    }
                )
            messages.append({"role": "user", "content": tool_result_content})
            continue

        final_text = _text_from_content(content)
        called = _called_tool_names(tool_calls)
        missing = [name for name in REQUIRED_TOOLS if name not in called]
        return {
            "ok": not missing,
            "model_id": _model_id(),
            "region": _region(),
            "stop_reason": stop_reason,
            "tool_calls": tool_calls,
            "tools_called": sorted(called),
            "missing_tools": missing,
            "assistant_text": final_text,
        }

    called = _called_tool_names(tool_calls)
    missing = [name for name in REQUIRED_TOOLS if name not in called]
    return {
        "ok": not missing,
        "model_id": _model_id(),
        "region": _region(),
        "stop_reason": "max_turns",
        "tool_calls": tool_calls,
        "tools_called": sorted(called),
        "missing_tools": missing,
        "assistant_text": final_text,
        "error": "Exceeded max converse turns before a final text reply",
    }


def main() -> int:
    print(f"Region: {_region()}")
    print(f"Model:  {_model_id()}")
    print(
        "Calling Bedrock Converse "
        "(two tools: get_revenue_case, get_case_evidence)..."
    )
    try:
        summary = run_two_tool_smoke("CASE-001")
    except (ClientError, BotoCoreError) as exc:
        print("AWS/Bedrock error:")
        print(exc)
        return 1

    print(json.dumps(summary, indent=2))
    if not summary.get("ok"):
        missing = summary.get("missing_tools") or REQUIRED_TOOLS
        print(f"Smoke test failed: missing tool call(s): {', '.join(missing)}")
        return 1
    print("Smoke test passed: Bedrock called get_revenue_case and get_case_evidence.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
