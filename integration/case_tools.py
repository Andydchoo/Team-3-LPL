"""AI-owner handoff: the same read-only case tools using private S3 evidence."""

from revenue_engine import get_revenue_case as local_revenue_case
from revenue_engine.cases import build_revenue_case

from .s3_evidence import get_case_evidence


def get_revenue_case(case_id: str) -> dict:
    # Local case data supplies engine-owned household/AUM/date metadata. All fee
    # calculations remain in the engine and use the same S3 source evidence that
    # the investigator reads; no copied arithmetic or independent AI findings.
    metadata = local_revenue_case(case_id)
    return build_revenue_case(metadata, get_case_evidence(case_id))


__all__ = ["get_revenue_case", "get_case_evidence"]
