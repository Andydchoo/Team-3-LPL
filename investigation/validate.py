"""Parse and validate Investigation dictionaries against the shared contract."""

from __future__ import annotations

import json
import re
from typing import Any

from revenue_engine.contracts import Investigation

STATUSES = frozenset(
    {
        "supported_explanation",
        "partial_explanation",
        "conflicting_evidence",
        "insufficient_evidence",
        "investigation_error",
    }
)
STRENGTHS = frozenset({"high", "medium", "low"})

_FENCE_RE = re.compile(r"```(?:json)?\s*(.*?)```", re.DOTALL | re.IGNORECASE)
_THINKING_RE = re.compile(r"<thinking>.*?</thinking>", re.DOTALL | re.IGNORECASE)


def investigation_error(case_id: str, summary: str) -> Investigation:
    return {
        "case_id": case_id,
        "investigation_status": "investigation_error",
        "likely_cause": None,
        "summary": summary,
        "evidence_strength": "low",
        "evidence_used": [],
        "uncertainties": ["Structured investigation output was unavailable."],
        "recommended_action": (
            "Retain the deterministic financial finding and route the case "
            "to authorized human review."
        ),
        "requires_human_review": True,
    }


def extract_json_object(text: str) -> dict[str, Any]:
    """Pull the first JSON object from model text (fences / thinking allowed)."""
    cleaned = _THINKING_RE.sub("", text or "").strip()
    if not cleaned:
        raise ValueError("Model returned empty text")

    candidates: list[str] = []
    fenced = _FENCE_RE.findall(cleaned)
    candidates.extend(fenced)
    candidates.append(cleaned)

    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start != -1 and end != -1 and end > start:
        candidates.append(cleaned[start : end + 1])

    last_error: Exception | None = None
    for candidate in candidates:
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError as exc:
            last_error = exc
            continue
        if isinstance(parsed, dict):
            return parsed
        last_error = ValueError("JSON payload was not an object")
    raise ValueError(f"Could not parse Investigation JSON: {last_error}")


def validate_investigation(
    raw: dict[str, Any],
    *,
    case_id: str,
    allowed_evidence_ids: set[str],
) -> Investigation:
    """Validate/normalize model output into a contract Investigation."""
    if not isinstance(raw, dict):
        raise ValueError("Investigation must be a JSON object")

    status = raw.get("investigation_status")
    if status not in STATUSES:
        raise ValueError(f"Invalid investigation_status: {status!r}")

    strength = raw.get("evidence_strength")
    if strength not in STRENGTHS:
        raise ValueError(f"Invalid evidence_strength: {strength!r}")

    summary = raw.get("summary")
    if not isinstance(summary, str) or not summary.strip():
        raise ValueError("summary must be a non-empty string")

    recommended = raw.get("recommended_action")
    if not isinstance(recommended, str) or not recommended.strip():
        raise ValueError("recommended_action must be a non-empty string")

    likely_cause = raw.get("likely_cause")
    if likely_cause is not None and not isinstance(likely_cause, str):
        raise ValueError("likely_cause must be a string or null")

    uncertainties = raw.get("uncertainties", [])
    if not isinstance(uncertainties, list) or not all(
        isinstance(item, str) for item in uncertainties
    ):
        raise ValueError("uncertainties must be an array of strings")

    evidence_used_raw = raw.get("evidence_used", [])
    if not isinstance(evidence_used_raw, list):
        raise ValueError("evidence_used must be an array")

    evidence_used = []
    for item in evidence_used_raw:
        if not isinstance(item, dict):
            raise ValueError("evidence_used items must be objects")
        evidence_id = item.get("evidence_id")
        finding = item.get("finding")
        if not isinstance(evidence_id, str) or not evidence_id.strip():
            raise ValueError("evidence_used.evidence_id must be a non-empty string")
        if evidence_id not in allowed_evidence_ids:
            raise ValueError(f"Unknown evidence_id in evidence_used: {evidence_id}")
        if not isinstance(finding, str) or not finding.strip():
            raise ValueError("evidence_used.finding must be a non-empty string")
        evidence_used.append(
            {"evidence_id": evidence_id, "finding": finding.strip()}
        )

    returned_case_id = raw.get("case_id", case_id)
    if returned_case_id != case_id:
        raise ValueError(
            f"case_id mismatch: expected {case_id}, got {returned_case_id}"
        )

    return {
        "case_id": case_id,
        "investigation_status": status,
        "likely_cause": likely_cause.strip() if isinstance(likely_cause, str) else None,
        "summary": summary.strip(),
        "evidence_strength": strength,
        "evidence_used": evidence_used,
        "uncertainties": [item.strip() for item in uncertainties if item.strip()],
        "recommended_action": recommended.strip(),
        "requires_human_review": True,
    }
