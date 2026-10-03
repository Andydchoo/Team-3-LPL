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

    return failures


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
