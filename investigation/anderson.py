"""Step 4: repeated Anderson (CASE-001) acceptance checks for investigate_case."""

from __future__ import annotations

import json
import os
import re
import time
from typing import Any

from revenue_engine.contracts import Investigation

from .investigate import investigate_case

CASE_ID = "CASE-001"
ALLOWED_STATUSES = frozenset({"supported_explanation", "partial_explanation"})
DEFAULT_RUNS = 3
DEFAULT_PAUSE_SECONDS = 1.25

_AUTO_RAISE_RE = re.compile(
    r"(automatically\s+(raise|increase|change)|should\s+be\s+raised|"
    r"must\s+raise\s+the\s+fee|auto[- ]?adjust)",
    re.IGNORECASE,
)
_EXCEPTION_RE = re.compile(
    r"(expired|expir).{0,40}(exception|pricing)|"
    r"(temporary|pricing)\s+exception|"
    r"exception.{0,40}(ended|expir)",
    re.IGNORECASE,
)
_HUMAN_REVIEW_RE = re.compile(r"(human|advisor|authorized).{0,20}review|review", re.I)


def evaluate_anderson(result: Investigation) -> list[str]:
    """Return a list of acceptance failures (empty means pass)."""
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
    if not evidence_used:
        failures.append("evidence_used is empty")

    cause = result.get("likely_cause") or ""
    summary = result.get("summary") or ""
    narrative = f"{cause}\n{summary}"
    if not _EXCEPTION_RE.search(narrative):
        failures.append(
            "likely_cause/summary must reference an expired/temporary pricing exception"
        )

    action = result.get("recommended_action") or ""
    if not _HUMAN_REVIEW_RE.search(action):
        failures.append("recommended_action must point to human/authorized review")

    banned_text = f"{cause}\n{summary}\n{action}"
    if _AUTO_RAISE_RE.search(banned_text):
        failures.append("must not recommend automatically raising/changing the fee")

    return failures


def run_anderson_reliability(
    runs: int = DEFAULT_RUNS,
    pause_seconds: float = DEFAULT_PAUSE_SECONDS,
) -> dict[str, Any]:
    """Call investigate_case repeatedly and score Anderson acceptance."""
    trials: list[dict[str, Any]] = []
    for index in range(1, runs + 1):
        result = investigate_case(CASE_ID)
        failures = evaluate_anderson(result)
        trials.append(
            {
                "run": index,
                "ok": not failures,
                "failures": failures,
                "investigation_status": result.get("investigation_status"),
                "likely_cause": result.get("likely_cause"),
                "evidence_used_count": len(result.get("evidence_used") or []),
                "recommended_action": result.get("recommended_action"),
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
    runs = int(os.environ.get("ANDERSON_RELIABILITY_RUNS", DEFAULT_RUNS))
    pause = float(os.environ.get("ANDERSON_RELIABILITY_PAUSE", DEFAULT_PAUSE_SECONDS))
    print(f"Anderson reliability: {runs} run(s) of investigate_case({CASE_ID})...")
    summary = run_anderson_reliability(runs=runs, pause_seconds=pause)
    print(json.dumps(summary, indent=2))
    if not summary["ok"]:
        print(
            f"Reliability check failed: {summary['passed']}/{summary['runs']} passed."
        )
        return 1
    print(f"Reliability check passed: {summary['passed']}/{summary['runs']} passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
