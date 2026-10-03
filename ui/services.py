"""Stable frontend service boundary.

The Streamlit screens import only these functions. Other owners can replace the
mock implementations behind this module without editing ``app.py`` or the UI.
The public shapes intentionally match ``docs/CONTRACTS.md``.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


def get_revenue_case(case_id: str) -> dict[str, Any]:
    """Load a deterministic case, using the real engine for CASE-001."""
    if case_id == "CASE-001":
        from revenue_engine import get_revenue_case as engine_get_revenue_case

        return engine_get_revenue_case(case_id)

    cases = {
        "CASE-002": {
            "case_id": "CASE-002", "household": "Patel Household",
            "anomaly_type": "agreement_amendment", "aum": 800_000.0,
            "expected_rate": 0.008, "actual_rate": 0.01,
            "expected_annual_fee": 6_400.0, "actual_annual_fee": 8_000.0,
            "annual_difference": 1_600.0,
            "impact_direction": "potential_overbilling", "evidence_ids": [],
            "status": "requires_review", "as_of_date": "2026-01-01",
            "calculation_method": "flat",
        },
        "CASE-003": {
            "case_id": "CASE-003", "household": "Chen Household",
            "anomaly_type": "household_breakpoint", "aum": 2_000_000.0,
            "expected_rate": 0.00875, "actual_rate": 0.01,
            "expected_annual_fee": 17_500.0, "actual_annual_fee": 20_000.0,
            "annual_difference": 2_500.0,
            "impact_direction": "potential_overbilling", "evidence_ids": [],
            "status": "requires_review", "as_of_date": "2026-01-01",
            "calculation_method": "marginal",
        },
        "CASE-004": {
            "case_id": "CASE-004", "household": "Ramirez Household",
            "anomaly_type": "asset_exclusion", "aum": 250_000.0,
            "expected_rate": 0.008, "actual_rate": 0.008,
            "expected_annual_fee": 0.0, "actual_annual_fee": 2_000.0,
            "annual_difference": 2_000.0,
            "impact_direction": "potential_overbilling", "evidence_ids": [],
            "status": "requires_review", "as_of_date": "2026-01-01",
            "calculation_method": "review_dependent",
        },
        "CASE-005": {
            "case_id": "CASE-005", "household": "Morgan Household",
            "anomaly_type": "conflicting_evidence", "aum": 0.0,
            "expected_rate": None, "actual_rate": 0.0075,
            "expected_annual_fee": None, "actual_annual_fee": None,
            "annual_difference": None, "impact_direction": "review_dependent",
            "evidence_ids": [], "status": "requires_review",
            "as_of_date": "2026-01-01", "calculation_method": "review_dependent",
        },
    }
    if case_id not in cases:
        raise KeyError(case_id)
    return cases[case_id]


def get_case_evidence(case_id: str) -> list[dict[str, Any]]:
    """Return evidence through the engine/storage boundary."""
    if case_id == "CASE-001":
        from revenue_engine import get_case_evidence as engine_get_case_evidence

        return engine_get_case_evidence(case_id)

    mock_evidence: dict[str, list[dict[str, Any]]] = {
        "CASE-002": [
            {
                "evidence_id": "patel_amendment",
                "case_id": "CASE-002",
                "evidence_type": "advisory_agreement",
                "title": "Executed Advisory Fee Schedule Rider (Bilateral Amendment)",
                "source_path": "evidence/patel/amendment.json",
                "content": {
                    "household": "Patel Household",
                    "annual_rate": 0.0080,
                    "effective_date": "2025-10-15",
                    "expiration_date": None,
                    "pricing_method": "flat",
                    "clause": "Private Wealth Tier: Reduced rate of 80 bps upon account aggregate exceeding $750,000",
                },
            },
            {
                "evidence_id": "patel_custodian_billing",
                "case_id": "CASE-002",
                "evidence_type": "billing_configuration",
                "title": "Custodian Fee Master Billing Profile",
                "source_path": "evidence/patel/custodian_billing.json",
                "content": {
                    "household": "Patel Household",
                    "annual_rate": 0.0100,
                    "billable_aum": 800_000.0,
                    "effective_date": "2024-01-01",
                    "status": "active (stale schedule)",
                },
            },
        ],
        "CASE-003": [
            {
                "evidence_id": "chen_tier_schedule",
                "case_id": "CASE-003",
                "evidence_type": "advisory_agreement",
                "title": "Advisory Agreement Schedule B - Tiered Breakpoint Schedule",
                "source_path": "evidence/chen/schedule_b.json",
                "content": {
                    "household": "Chen Household",
                    "annual_rate": 0.00875,
                    "effective_date": "2024-06-01",
                    "pricing_method": "marginal",
                    "breakpoints": "Tier 1: $0-$1M @ 1.00% | Tier 2: $1M+ @ 0.75% (Effective blended: 0.875%)",
                },
            },
            {
                "evidence_id": "chen_custodian_billing",
                "case_id": "CASE-003",
                "evidence_type": "billing_configuration",
                "title": "Custodian Sub-Account Billing Profile",
                "source_path": "evidence/chen/billing.json",
                "content": {
                    "household": "Chen Household",
                    "annual_rate": 0.0100,
                    "billable_aum": 2_000_000.0,
                    "status": "active (billed as standalone flat tiers)",
                },
            },
        ],
        "CASE-004": [
            {
                "evidence_id": "ramirez_exclusion_rider",
                "case_id": "CASE-004",
                "evidence_type": "advisory_agreement",
                "title": "Advisory Agreement Rider - Asset Exclusion Stipulation",
                "source_path": "evidence/ramirez/rider.json",
                "content": {
                    "household": "Ramirez Household",
                    "annual_rate": 0.0,
                    "effective_date": "2024-09-01",
                    "pricing_method": "flat",
                    "exclusion_note": "Account #529-RAM (College Savings) expressly excluded from billable AUM",
                },
            },
            {
                "evidence_id": "ramirez_custodian_billing",
                "case_id": "CASE-004",
                "evidence_type": "billing_configuration",
                "title": "Custodian Fee Debit Record",
                "source_path": "evidence/ramirez/billing.json",
                "content": {
                    "household": "Ramirez Household",
                    "annual_rate": 0.0080,
                    "billable_aum": 250_000.0,
                    "status": "active (inappropriately flagged billable)",
                },
            },
        ],
        "CASE-005": [
            {
                "evidence_id": "morgan_lpl_feed",
                "case_id": "CASE-005",
                "evidence_type": "advisory_agreement",
                "title": "LPL Custodial Feed Master",
                "source_path": "evidence/morgan/lpl_feed.json",
                "content": {
                    "household": "Morgan Household",
                    "annual_rate": 0.0075,
                    "billable_aum": 2_100_000.0,
                    "status": "active custody",
                },
            },
            {
                "evidence_id": "morgan_external_custody",
                "case_id": "CASE-005",
                "evidence_type": "billing_configuration",
                "title": "External Custody Feed (Schwab Institutional)",
                "source_path": "evidence/morgan/external_custody.json",
                "content": {
                    "household": "Morgan Household",
                    "annual_rate": 0.0075,
                    "billable_aum": 1_350_000.0,
                    "status": "unlinked tax-ID / duplicate registration",
                },
            },
        ],
    }
    return mock_evidence.get(case_id, [])


def investigate_case(case_id: str) -> dict[str, Any]:
    """Return a contract-shaped investigation until AI integration is connected.

    An eventual ``investigation`` package can provide a live implementation
    without requiring changes in the Streamlit presentation layer.
    """
    try:
        from investigation import investigate_case as live_investigate_case
    except ImportError:
        live_investigate_case = None
    if live_investigate_case is not None:
        return live_investigate_case(case_id)

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
            "likely_cause": "Multi-Custodian Asset Attribution & Tax-ID Mismatch",
            "summary": (
                "Conflicting custodian records between LPL custody ($2.1M) and Schwab custody ($1.35M) show discordant trust registration "
                "details and unlinked Tax IDs. Deterministic automated calculation is paused pending human compliance verification."
            ),
            "evidence_strength": "medium",
            "evidence_used": [
                {"evidence_id": "morgan_lpl_feed", "finding": "LPL records show $2.1M AUM in Primary Living Trust."},
                {"evidence_id": "morgan_external_custody", "finding": "Schwab feed indicates $1.35M in Revocable Trust with unlinked tax identifiers."},
            ],
            "uncertainties": ["Multi-custodian tax aggregation requires manual compliance verification."],
            "recommended_action": "Route case to senior operations officer to verify cross-custodial trust aggregation before billing run.",
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
    """Return a session-only review until AWS persistence is connected."""
    try:
        from integration import record_review as live_record_review
    except ImportError:
        live_record_review = None
    if live_record_review is not None:
        return live_record_review(case_id, decision)

    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    return {
        "review_id": f"REV-{uuid4().hex[:8].upper()}",
        "case_id": case_id,
        "decision": decision,
        "actor": "human",
        "recorded_at": timestamp,
    }

