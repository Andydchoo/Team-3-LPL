"""Step 3: investigate_case returns a schema-shaped Investigation via Bedrock."""

from __future__ import annotations

import json
import os
from typing import Any

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from revenue_engine import get_case_evidence
from revenue_engine.contracts import Investigation

from .tools import dispatch_tool, tool_config_both_tools
from .validate import (
    extract_json_object,
    investigation_error,
    validate_investigation,
)

DEFAULT_REGION = "us-east-1"
DEFAULT_MODEL_ID = "amazon.nova-lite-v1:0"
MAX_TURNS = 8
REQUIRED_TOOLS = ("get_revenue_case", "get_case_evidence")

SYSTEM_PROMPT = """You are the RevenueTwin investigation agent.

Architecture rules:
- Deterministic tools own financial numbers. Never recalculate fees or invent rates.
- Call get_revenue_case(case_id), then get_case_evidence(case_id).
- Explain using only tool results. Do not invent documents, approvals, or dates.
- Never recommend automatically changing a fee. Recommend authorized human review.
- Do not say the fee should automatically be raised.
- Prefer investigation_status supported_explanation when evidence clearly shows an
  expired temporary pricing exception still reflected in billing.
- If evidence includes only a discussion note without finalized authorization, or
  impact_direction/calculation_method is review_dependent, use
  conflicting_evidence or insufficient_evidence. Do not confidently claim the
  contractual rate should change.
- Do not expose chain-of-thought. Do not invent numerical confidence percentages.

After both tools have returned, respond with ONLY a single JSON object (no markdown)
matching this shape:
{
  "case_id": "<same case_id>",
  "investigation_status": "supported_explanation|partial_explanation|conflicting_evidence|insufficient_evidence|investigation_error",
  "likely_cause": "<short cause or null>",
  "summary": "<concise evidence-grounded summary>",
  "evidence_strength": "high|medium|low",
  "evidence_used": [{"evidence_id": "<id from tools>", "finding": "<what it shows>"}],
  "uncertainties": ["<gap or ambiguity>"],
  "recommended_action": "<human review action>",
  "requires_human_review": true
}

requires_human_review must always be true.
evidence_used.evidence_id values must come from get_case_evidence.
recommended_action must explicitly include the phrase "authorized human review".
"""


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


def _run_converse(case_id: str) -> tuple[str, set[str]]:
    """Run tool-use turns; return final assistant text and tool names called."""
    client = boto3.client("bedrock-runtime", region_name=_region())
    messages: list[dict[str, Any]] = [
        {
            "role": "user",
            "content": [
                {
                    "text": (
                        f"Investigate case {case_id}. "
                        "Call get_revenue_case, then get_case_evidence, "
                        "then return the Investigation JSON object only."
                    )
                }
            ],
        }
    ]
    called: set[str] = set()

    for _ in range(MAX_TURNS):
        response = client.converse(
            modelId=_model_id(),
            system=[{"text": SYSTEM_PROMPT}],
            messages=messages,
            toolConfig=tool_config_both_tools(),
        )
        output_message = response["output"]["message"]
        content = output_message["content"]
        messages.append(output_message)

        uses = _tool_uses(content)
        if uses:
            tool_result_content = []
            for use in uses:
                name = use["name"]
                tool_input = use.get("input") or {}
                called.add(name)
                payload = dispatch_tool(name, tool_input)
                tool_result_content.append(
                    {
                        "toolResult": {
                            "toolUseId": use["toolUseId"],
                            "content": [{"json": json.loads(payload)}],
                        }
                    }
                )
            messages.append({"role": "user", "content": tool_result_content})
            continue

        return _text_from_content(content), called

    raise TimeoutError("Exceeded max converse turns before Investigation JSON")


def investigate_case(case_id: str) -> Investigation:
    """Investigate a revenue case with Bedrock tool use; return Investigation."""
    try:
        evidence = get_case_evidence(case_id)
    except KeyError:
        return investigation_error(case_id, f"Unknown case_id: {case_id}")
    except (OSError, ValueError) as exc:
        return investigation_error(case_id, f"Evidence load failed: {exc}")

    allowed_ids = {item["evidence_id"] for item in evidence}

    try:
        final_text, called = _run_converse(case_id)
    except (ClientError, BotoCoreError) as exc:
        return investigation_error(case_id, f"Bedrock error: {exc}")
    except (TimeoutError, json.JSONDecodeError, KeyError, TypeError) as exc:
        return investigation_error(case_id, f"Investigation loop failed: {exc}")

    missing = [name for name in REQUIRED_TOOLS if name not in called]
    if missing:
        return investigation_error(
            case_id,
            "Model did not call required tools: " + ", ".join(missing),
        )

    try:
        raw = extract_json_object(final_text)
        return validate_investigation(
            raw,
            case_id=case_id,
            allowed_evidence_ids=allowed_ids,
        )
    except ValueError as exc:
        return investigation_error(case_id, f"Invalid Investigation output: {exc}")


def main() -> int:
    case_id = "CASE-001"
    print(f"Region: {_region()}")
    print(f"Model:  {_model_id()}")
    print(f"Investigating {case_id}...")
    result = investigate_case(case_id)
    print(json.dumps(result, indent=2))

    if result["investigation_status"] == "investigation_error":
        print("Smoke test failed: investigation_error")
        return 1
    if result["case_id"] != case_id:
        print("Smoke test failed: case_id mismatch")
        return 1
    if result["requires_human_review"] is not True:
        print("Smoke test failed: requires_human_review must be true")
        return 1
    if not result["evidence_used"]:
        print("Smoke test failed: evidence_used is empty")
        return 1
    print("Smoke test passed: investigate_case returned structured Investigation.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
