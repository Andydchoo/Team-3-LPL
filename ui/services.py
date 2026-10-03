"""Stable frontend service boundary.

The Streamlit screens import only these functions. Other owners can replace the
mock implementations behind this module without editing ``app.py`` or the UI.
The public shapes intentionally match ``docs/CONTRACTS.md``.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from integration.service_boundary import (
    IntegrationUnavailable, backend_mode, integration_error_message, require_live_case,
)


def get_revenue_case(case_id: str) -> dict[str, Any]:
    """Load a deterministic case through the selected storage backend."""
    if backend_mode() == "aws":
        require_live_case(case_id)
        from integration.case_tools import get_revenue_case as aws_get_revenue_case

        return aws_get_revenue_case(case_id)
    from revenue_engine import get_revenue_case as engine_get_revenue_case

    return engine_get_revenue_case(case_id)


def get_case_evidence(case_id: str) -> list[dict[str, Any]]:
    """Return evidence through the engine/storage boundary."""
    if backend_mode() == "aws":
        require_live_case(case_id)
        from integration.case_tools import get_case_evidence as aws_get_case_evidence

        return aws_get_case_evidence(case_id)
    from revenue_engine import get_case_evidence as engine_get_case_evidence

    return engine_get_case_evidence(case_id)


def investigate_case(case_id: str) -> dict[str, Any]:
    """Use the explicit backend; AWS errors never become mock explanations."""
    if backend_mode() == "aws":
        require_live_case(case_id)
        from integration.investigation_adapter import investigate_case as live_investigate_case

        return live_investigate_case(case_id)
    return _mock_investigate_case(case_id)


def _mock_investigate_case(case_id: str) -> dict[str, Any]:

    investigations: dict[str, dict[str, Any]] = {
        "CASE-001": {
            "case_id": "CASE-001",
            "investigation_status": "supported_explanation",
            "likely_cause": "Expired temporary pricing exception",
            "summary": (
                "The current 0.75% billing configuration matches a temporary pricing "
                "exception that ended on December 31, 2025. The active agreement is "
                "1.00%, so the case should be reviewed before the next billing cycle."
            ),
            "evidence_strength": "high",
            "evidence_used": [
                {"evidence_id": "anderson_agreement", "finding": "Active agreement specifies 1.00%."},
                {"evidence_id": "anderson_exception", "finding": "Authorized 0.75% exception ended December 31, 2025."},
                {"evidence_id": "anderson_billing", "finding": "Current billing configuration remains 0.75%."},
            ],
            "uncertainties": [],
            "recommended_action": "Send the exception and billing configuration to the responsible advisor or operations reviewer to revert to 1.00%.",
            "requires_human_review": True,
        },
        "CASE-002": {
            "case_id": "CASE-002",
            "investigation_status": "supported_explanation",
            "likely_cause": "Fee Schedule Amendment Not Implemented at Custodian",
            "summary": (
                "A bilateral fee schedule rider executed on October 15, 2025 reduced the client's "
                "annual advisory fee from 1.00% to 0.80% upon qualifying for the Private Wealth Tier ($750k+). "
                "The custodian billing platform was never updated with the new rider rate, resulting in a $1,600/year overbilling."
            ),
            "evidence_strength": "high",
            "evidence_used": [
                {"evidence_id": "patel_amendment", "finding": "Executed amendment sets annual rate at 0.80%."},
                {"evidence_id": "patel_custodian_billing", "finding": "Custodian fee configuration still charging legacy 1.00% rate."},
            ],
            "uncertainties": [],
            "recommended_action": "Submit fee correction ticket to custodian desk and issue a $400 quarterly credit adjustment to client account.",
            "requires_human_review": True,
        },
        "CASE-003": {
            "case_id": "CASE-003",
            "investigation_status": "supported_explanation",
            "likely_cause": "Unapplied Household Breakpoint Tier",
            "summary": (
                "The Chen Household crossed the $2.0M breakpoint tier qualifying for 0.75% on balances exceeding $1.0M "
                "(blended effective rate of 0.875%). Sub-accounts were billed as standalone accounts at 1.00%, creating an overcharge of $2,500/year."
            ),
            "evidence_strength": "high",
            "evidence_used": [
                {"evidence_id": "chen_tier_schedule", "finding": "Schedule B establishes 0.875% blended rate across $2M aggregated AUM."},
                {"evidence_id": "chen_custodian_billing", "finding": "Sub-accounts billed individually at non-aggregated 1.00% flat rate."},
            ],
            "uncertainties": [],
            "recommended_action": "Link sub-accounts under unified household billing profile in custodian master and credit excess fees.",
            "requires_human_review": True,
        },
        "CASE-004": {
            "case_id": "CASE-004",
            "investigation_status": "supported_explanation",
            "likely_cause": "Excluded 529 Account Inappropriately Marked Billable",
            "summary": (
                "Executed agreement Schedule C explicitly stipulates that the Ramirez 529 College Savings account ($250,000) "
                "is excluded from advisory fee assessment. The account was mistakenly mapped as billable in the custodian feed, causing $2,000/yr overcharge."
            ),
            "evidence_strength": "high",
            "evidence_used": [
                {"evidence_id": "ramirez_exclusion_rider", "finding": "Agreement Rider explicitly excludes 529 College Savings accounts from billable AUM."},
                {"evidence_id": "ramirez_custodian_billing", "finding": "Custodian fee engine debited 0.80% on $250k excluded balance."},
            ],
            "uncertainties": [],
            "recommended_action": "Toggle custodian asset classification to 'Non-Billable / Excluded' and initiate client fee refund memo.",
            "requires_human_review": True,
        },
        "CASE-005": {
            "case_id": "CASE-005",
            "investigation_status": "conflicting_evidence",
            "likely_cause": "Preferred pricing discussion lacks finalized authorization",
            "summary": (
                "The agreement records 1.00% while billing records 0.75%. The "
                "advisor note documents a discussion about extending preferred "
                "pricing, without finalized authorization. Financial impact "
                "remains review-dependent."
            ),
            "evidence_strength": "medium",
            "evidence_used": [
                {"evidence_id": "morgan_agreement", "finding": "Agreement records a 1.00% annual rate."},
                {"evidence_id": "morgan_billing", "finding": "Billing records a 0.75% annual rate."},
                {"evidence_id": "morgan_internal_note", "finding": "Discussion-only note is not finalized authorization."},
            ],
            "uncertainties": ["Finalized authorization for preferred pricing is unavailable."],
            "recommended_action": "Route the case to authorized human review before any pricing decision.",
            "requires_human_review": True,
        },
    }

    if case_id in investigations:
        return investigations[case_id]

    return {
        "case_id": case_id,
        "investigation_status": "insufficient_evidence",
        "likely_cause": "Additional evidence is required",
        "summary": "This case requires additional documentation from custodial feeds.",
        "evidence_strength": "low",
        "evidence_used": [],
        "uncertainties": ["Live evidence retrieval pending."],
        "recommended_action": "Keep the case in human review until evidence is available.",
        "requires_human_review": True,
    }


def record_review(case_id: str, decision: str) -> dict[str, Any]:
    """Persist in AWS mode; keep the explicitly local demo session-only."""
    if backend_mode() == "aws":
        require_live_case(case_id)
        from integration import record_review as live_record_review

        return live_record_review(case_id, decision)
    if decision not in {"send_for_review", "investigate_further", "dismiss"}:
        raise IntegrationUnavailable("Choose Send for Review, Investigate Further or Dismiss.")
    get_revenue_case(case_id)
    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    return {
        "review_id": f"REV-{uuid4().hex[:8].upper()}",
        "case_id": case_id,
        "decision": decision,
        "actor": "human",
        "recorded_at": timestamp,
    }

