"""Deterministic RevenueTwin tools. Importing this package performs no I/O."""

from .cases import get_case_evidence, get_revenue_case

__all__ = ["get_revenue_case", "get_case_evidence"]
