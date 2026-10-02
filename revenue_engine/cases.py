"""Local CASE-001 adapter behind the stable frontend and investigation tools."""

import json
from datetime import date
from pathlib import Path

from .calculations import (
    calculate_actual_fee, calculate_expected_fee, compare_expected_vs_actual,
    decimal_value,
)
from .contracts import Evidence, RevenueCase

DEMO_DIR = Path(__file__).resolve().parent.parent / "data" / "demo"
CASE_FILES = {"CASE-001": DEMO_DIR / "cases" / "CASE-001.json"}


def _load_json(path: Path):
    with path.open(encoding="utf-8") as stream:
        return json.load(stream)


def _load_definition(case_id: str) -> dict:
    if case_id not in CASE_FILES:
        raise KeyError(f"Unknown revenue case: {case_id}")
    definition = _load_json(CASE_FILES[case_id])
    if not isinstance(definition, dict) or definition.get("case_id") != case_id:
        raise ValueError("Case definition does not match the requested case")
    return definition


def _validate_evidence(record: Evidence, definition: dict) -> None:
    if not isinstance(record, dict):
        raise ValueError("Evidence must be a document object")
    for field in ["evidence_id", "case_id", "evidence_type", "title", "source_path"]:
        if not isinstance(record.get(field), str) or not record[field]:
            raise ValueError(f"Evidence requires a nonempty {field}")
    if not isinstance(record.get("content"), dict):
        raise ValueError("Evidence content must be an object")
    if record["case_id"] != definition["case_id"]:
        raise ValueError("Evidence belongs to a different case")
    household = record["content"].get("household")
    if household is not None and household != definition["household"]:
        raise ValueError("Evidence belongs to a different household")


def _load_evidence(definition: dict) -> list[Evidence]:
    records = []
    seen_ids = set()
    for source_path in definition["evidence_paths"]:
        path = (DEMO_DIR / source_path).resolve()
        if not path.is_relative_to(DEMO_DIR.resolve()):
            raise ValueError("Evidence path must remain inside the demo directory")
        record = _load_json(path)
        _validate_evidence(record, definition)
        if record["source_path"] != source_path:
            raise ValueError("Evidence source path does not match its stored location")
        if record["evidence_id"] in seen_ids:
            raise ValueError("Evidence IDs must be unique within a case")
        seen_ids.add(record["evidence_id"])
        records.append(record)
    return records


def _build_revenue_case(definition: dict, evidence: list[Evidence]) -> RevenueCase:
    """Compute a flat case from authoritative synthetic records and an explicit date.

    Only an explicitly authorized, dated pricing exception overrides an agreement.
    Missing, conflicting or unsupported records raise ValueError for human review.
    """
    if definition["calculation_method"] != "flat":
        raise ValueError("This milestone supports flat pricing only")
    as_of = date.fromisoformat(definition["as_of_date"])
    by_type = {}
    seen_ids = set()
    for record in evidence:
        _validate_evidence(record, definition)
        if record["evidence_id"] in seen_ids:
            raise ValueError("Evidence IDs must be unique within a case")
        seen_ids.add(record["evidence_id"])
        if record["evidence_type"] not in {
            "advisory_agreement", "billing_configuration", "pricing_exception",
        }:
            raise ValueError("Unsupported evidence requires human review")
        if record["evidence_type"] in by_type:
            raise ValueError("Conflicting evidence types require human review")
        by_type[record["evidence_type"]] = record["content"]
    if "advisory_agreement" not in by_type or "billing_configuration" not in by_type:
        raise ValueError("Agreement and billing evidence are required")
    agreement = by_type["advisory_agreement"]
    billing = by_type["billing_configuration"]
    if agreement["pricing_method"] != "flat":
        raise ValueError("The agreement does not specify supported flat pricing")
    if date.fromisoformat(agreement["effective_date"]) > as_of:
        raise ValueError("Agreement is not yet effective on the evaluation date")
    expires = agreement.get("expiration_date")
    if expires and as_of > date.fromisoformat(expires):
        raise ValueError("Agreement is expired on the evaluation date")
    if billing["status"] != "active" or date.fromisoformat(billing["effective_date"]) > as_of:
        raise ValueError("Billing configuration is not active on the evaluation date")

    expected_rate = decimal_value(agreement["annual_rate"])
    exception = by_type.get("pricing_exception")
    if exception:
        start = date.fromisoformat(exception["effective_date"])
        end = date.fromisoformat(exception["expiration_date"])
        if end < start:
            raise ValueError("Pricing exception ends before it starts")
        if exception["authorization_status"] != "authorized":
            raise ValueError("Pricing authorization requires human review")
        if start <= as_of <= end:
            expected_rate = decimal_value(exception["annual_rate"])

    expected_fee = calculate_expected_fee(definition["aum"], expected_rate)
    actual_rate = decimal_value(billing["annual_rate"])
    actual_fee = calculate_actual_fee(billing["billable_aum"], actual_rate)
    comparison = compare_expected_vs_actual(expected_fee, actual_fee)
    has_difference = comparison["annual_difference"] != 0
    return {
        "case_id": definition["case_id"],
        "household": definition["household"],
        "anomaly_type": definition["anomaly_type"] if has_difference else "none",
        "aum": float(decimal_value(definition["aum"])),
        "expected_rate": float(expected_rate),
        "actual_rate": float(actual_rate),
        "expected_annual_fee": float(expected_fee),
        "actual_annual_fee": float(actual_fee),
        "annual_difference": float(comparison["annual_difference"]),
        "impact_direction": comparison["impact_direction"],
        "evidence_ids": [record["evidence_id"] for record in evidence],
        "status": "requires_review" if has_difference else "no_discrepancy",
        "as_of_date": definition["as_of_date"],
        "calculation_method": "flat",
    }


def build_revenue_case(definition: dict, evidence: list[Evidence]) -> RevenueCase:
    """Build a financial finding; malformed source shapes fail as ValueError."""
    try:
        return _build_revenue_case(definition, evidence)
    except (KeyError, TypeError) as exc:
        raise ValueError("Malformed case or evidence record") from exc


def get_revenue_case(case_id: str) -> RevenueCase:
    definition = _load_definition(case_id)
    try:
        return build_revenue_case(definition, _load_evidence(definition))
    except (KeyError, TypeError) as exc:
        raise ValueError("Malformed case or evidence record") from exc


def get_case_evidence(case_id: str) -> list[Evidence]:
    definition = _load_definition(case_id)
    try:
        return _load_evidence(definition)
    except (KeyError, TypeError) as exc:
        raise ValueError("Malformed case or evidence record") from exc
