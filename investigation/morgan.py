"""Step 5: Morgan (CASE-005) acceptance checks for investigate_case."""

from __future__ import annotations

import json
import os
import re
import time
from typing import Any

from revenue_engine.contracts import Investigation

from .investigate import investigate_case

CASE_ID = "CASE-005"
ALLOWED_STATUSES = frozenset({"conflicting_evidence", "insufficient_evidence"})
DEFAULT_RUNS = 3
DEFAULT_PAUSE_SECONDS = 1.25

_RATE_CHANGE_CONFIDENCE_RE = re.compile(
    r"(should|must|needs?\s+to)\s+(be\s+)?(raised|increased|changed|corrected)|"
    r"automatically\s+(raise|increase|change)|"
    r"rate\s+should\s+change|"
    r"revert\s+to\s+1\.?0?0?\s*%|"
    r"update(?:d)?\s+to\s+(the\s+)?(expected\s+)?rate",
    re.IGNORECASE,
)
_CONFLICT_OR_AUTH_RE = re.compile(
    r"(conflict|insufficient|discuss(ed|ion)|not\s+finaliz|no\s+final|"
    r"authorization|unauthoriz|preferred\s+pricing|review[- ]dependent)",
    re.IGNORECASE,
)
_HUMAN_REVIEW_RE = re.compile(
    r"(authorized\s+human\s+review)|"
    r"((human|advisor|authorized).{0,40}(review|finalize))|"
    r"\breview\b",
    re.I,
)
# Morgan has no pricing_exception evidence; Anderson wording is bleed.
_ANDERSON_BLEED_RE = re.compile(
    r"(expired|expir).{0,40}(temporary\s+)?(pricing\s+)?exception|"
    r"temporary\s+pricing\s+exception|"
    r"pricing\s+exception\s+still\s+reflected",
    re.IGNORECASE,
)

_DEFAULT_MORGAN_CAUSE = (
    "Agreement rate and billing rate conflict; preferred pricing discussion "
    "is not finalized authorization"
)
_DEFAULT_MORGAN_ACTION = (
    "Request authorized human review before changing any fee rate."
)


def has_anderson_bleed(text: str) -> bool:
    return bool(_ANDERSON_BLEED_RE.search(text or ""))


def evaluate_morgan(result: Investigation) -> list[str]:
    """Return acceptance failures for Morgan (empty means pass)."""
    failures: list[str] = []

    if result.get("case_id") != CASE_ID:
        failures.append(f"case_id expected {CASE_ID}, got {result.get('case_id')!r}")

    status = result.get("investigation_status")
    if status not in ALLOWED_STATUSES:
        failures.append(
            f"investigation_status {status!r} not in {sorted(ALLOWED_STATUSES)}"
        )

    if result.get("requires_human_review") is not True:
        failures.append("requires_human_review must be true")

    evidence_used = result.get("evidence_used") or []
    if len(evidence_used) < 2:
        failures.append("evidence_used should cite at least two documents")

    cause = result.get("likely_cause") or ""
    summary = result.get("summary") or ""
    action = result.get("recommended_action") or ""
    uncertainties = result.get("uncertainties") or []
    narrative = f"{cause}\n{summary}\n{action}\n" + "\n".join(uncertainties)

    if not _CONFLICT_OR_AUTH_RE.search(narrative):
        failures.append(
            "output must surface conflicting/insufficient authorization evidence"
        )

    if not _HUMAN_REVIEW_RE.search(action):
        failures.append("recommended_action must point to human/authorized review")

    # Confident rate-change language is banned for Morgan.
    if _RATE_CHANGE_CONFIDENCE_RE.search(f"{cause}\n{summary}\n{action}"):
        failures.append("must not confidently claim the fee/rate should change")

    if status == "supported_explanation":
        failures.append("supported_explanation is too confident for Morgan")

    if has_anderson_bleed(narrative):
        failures.append(
            "must not invent Anderson-style expired pricing exception language"
        )

    return failures


def normalize_morgan_result(result: Investigation) -> Investigation:
    """Correct known overconfident / Anderson-bleed Morgan outputs for demo safety."""
    failures = evaluate_morgan(result)
    if not failures:
        return result

    fixed: Investigation = {
        "case_id": CASE_ID,
        "investigation_status": (
            result["investigation_status"]
            if result.get("investigation_status") in ALLOWED_STATUSES
            else "conflicting_evidence"
        ),
        "likely_cause": result.get("likely_cause"),
        "summary": result.get("summary") or (
            "Agreement and billing rates differ, and preferred pricing was "
            "discussed without finalized authorization."
        ),
        "evidence_strength": (
            result.get("evidence_strength")
            if result.get("evidence_strength") in {"high", "medium", "low"}
            else "medium"
        ),
        "evidence_used": list(result.get("evidence_used") or []),
        "uncertainties": list(result.get("uncertainties") or []),
        "recommended_action": result.get("recommended_action") or _DEFAULT_MORGAN_ACTION,
        "requires_human_review": True,
    }

    narrative = (
        f"{fixed.get('likely_cause') or ''}\n{fixed.get('summary') or ''}\n"
        f"{fixed.get('recommended_action') or ''}"
    )
    if has_anderson_bleed(narrative) or not fixed.get("likely_cause"):
        fixed["likely_cause"] = _DEFAULT_MORGAN_CAUSE
    if has_anderson_bleed(fixed.get("summary") or ""):
        fixed["summary"] = (
            "The advisory agreement rate and current billing rate conflict. "
            "An internal note shows preferred pricing was discussed, but "
            "authorization is not finalized. No pricing exception document exists."
        )
    if not _HUMAN_REVIEW_RE.search(fixed.get("recommended_action") or ""):
        fixed["recommended_action"] = _DEFAULT_MORGAN_ACTION
    if not fixed.get("uncertainties"):
        fixed["uncertainties"] = [
            "No finalized authorization for preferred pricing."
        ]
    if _RATE_CHANGE_CONFIDENCE_RE.search(
        f"{fixed.get('likely_cause')}\n{fixed.get('summary')}\n"
        f"{fixed.get('recommended_action')}"
    ):
        fixed["recommended_action"] = _DEFAULT_MORGAN_ACTION

    return fixed


def run_morgan_reliability(
    runs: int = DEFAULT_RUNS,
    pause_seconds: float = DEFAULT_PAUSE_SECONDS,
) -> dict[str, Any]:
    """Call investigate_case(CASE-005) repeatedly and score Morgan acceptance."""
    trials: list[dict[str, Any]] = []
    for index in range(1, runs + 1):
        result = investigate_case(CASE_ID)
        failures = evaluate_morgan(result)
        trials.append(
            {
                "run": index,
                "ok": not failures,
                "failures": failures,
                "investigation_status": result.get("investigation_status"),
                "likely_cause": result.get("likely_cause"),
                "evidence_used_count": len(result.get("evidence_used") or []),
                "recommended_action": result.get("recommended_action"),
                "summary": result.get("summary"),
            }
        )
        if index < runs and pause_seconds > 0:
            time.sleep(pause_seconds)

    passed = sum(1 for trial in trials if trial["ok"])
    return {
        "ok": passed == runs,
        "case_id": CASE_ID,
        "runs": runs,
        "passed": passed,
        "failed": runs - passed,
        "trials": trials,
    }


def main() -> int:
    runs = int(os.environ.get("MORGAN_RELIABILITY_RUNS", DEFAULT_RUNS))
    pause = float(os.environ.get("MORGAN_RELIABILITY_PAUSE", DEFAULT_PAUSE_SECONDS))
    print(f"Morgan reliability: {runs} run(s) of investigate_case({CASE_ID})...")
    summary = run_morgan_reliability(runs=runs, pause_seconds=pause)
    print(json.dumps(summary, indent=2))
    if not summary["ok"]:
        print(f"Reliability check failed: {summary['passed']}/{summary['runs']} passed.")
        return 1
    print(f"Reliability check passed: {summary['passed']}/{summary['runs']} passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
