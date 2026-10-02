"""Shared JSON-facing types for the five RevenueTwin owners.

Monetary arithmetic stays in Decimal until the JSON boundary. See
docs/CONTRACTS.md for semantics and contracts/revenuetwin.schema.json for
machine-readable validation. These types do not imply implemented AI or AWS.
"""

from typing import Literal, Protocol, TypedDict

ImpactDirection = Literal[
    "potential_underbilling", "potential_overbilling", "no_discrepancy",
    "review_dependent",
]
ReviewDecision = Literal["send_for_review", "investigate_further", "dismiss"]


class RevenueCase(TypedDict):
    case_id: str
    household: str
    anomaly_type: str
    aum: float
    expected_rate: float | None
    actual_rate: float | None
    expected_annual_fee: float | None
    actual_annual_fee: float | None
    annual_difference: float | None
    impact_direction: ImpactDirection
    evidence_ids: list[str]
    status: Literal["requires_review", "no_discrepancy"]
    as_of_date: str
    calculation_method: Literal["flat", "volume", "marginal", "review_dependent"]


class Evidence(TypedDict):
    evidence_id: str
    case_id: str
    evidence_type: str
    title: str
    source_path: str
    content: dict


class EvidenceFinding(TypedDict):
    evidence_id: str
    finding: str


class Investigation(TypedDict):
    case_id: str
    investigation_status: Literal[
        "supported_explanation", "partial_explanation", "conflicting_evidence",
        "insufficient_evidence", "investigation_error",
    ]
    likely_cause: str | None
    summary: str
    evidence_strength: Literal["high", "medium", "low"]
    evidence_used: list[EvidenceFinding]
    uncertainties: list[str]
    recommended_action: str
    requires_human_review: Literal[True]


class ReviewRecord(TypedDict):
    review_id: str
    case_id: str
    decision: ReviewDecision
    actor: Literal["human"]
    recorded_at: str


class InvestigateCase(Protocol):
    def __call__(self, case_id: str) -> Investigation: ...


class RecordReview(Protocol):
    def __call__(self, case_id: str, decision: ReviewDecision) -> ReviewRecord: ...
