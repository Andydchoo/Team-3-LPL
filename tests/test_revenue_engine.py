import json
import unittest
from copy import deepcopy
from decimal import Decimal
from pathlib import Path

from revenue_engine import get_case_evidence, get_revenue_case
from revenue_engine.calculations import (
    annualize_impact, calculate_actual_fee, calculate_expected_fee,
    compare_expected_vs_actual,
)
from revenue_engine.cases import build_revenue_case

ROOT = Path(__file__).resolve().parent.parent


class FinancialCalculationTests(unittest.TestCase):
    def test_anderson_expected_fee(self):
        self.assertEqual(calculate_expected_fee(1200000, "0.01"), Decimal("12000.00"))

    def test_anderson_actual_fee(self):
        self.assertEqual(calculate_actual_fee(1200000, "0.0075"), Decimal("9000.00"))

    def test_anderson_difference(self):
        result = compare_expected_vs_actual("12000", "9000")
        self.assertEqual(result["annual_difference"], Decimal("3000.00"))
        self.assertEqual(result["impact_direction"], "potential_underbilling")

    def test_overbilling_has_positive_magnitude_and_separate_direction(self):
        result = compare_expected_vs_actual("6400", "8000")
        self.assertEqual(result["annual_difference"], Decimal("1600.00"))
        self.assertEqual(result["impact_direction"], "potential_overbilling")

    def test_equal_fees_have_no_discrepancy(self):
        result = compare_expected_vs_actual("9000", "9000")
        self.assertEqual(result["annual_difference"], Decimal("0.00"))
        self.assertEqual(result["impact_direction"], "no_discrepancy")

    def test_rounding_uses_decimal_half_up(self):
        self.assertEqual(calculate_expected_fee("100.5", "0.01"), Decimal("1.01"))

    def test_explicit_billable_asset_exclusion(self):
        full = calculate_expected_fee(1000000, "0.008")
        excluded = calculate_expected_fee(1000000, "0.008", excluded_assets=250000)
        self.assertEqual(full - excluded, Decimal("2000.00"))

    def test_annualization_uses_billing_frequency(self):
        for amount, frequency in [(2250, "quarterly"), (750, "monthly"), (9000, "annual")]:
            with self.subTest(frequency=frequency):
                self.assertEqual(annualize_impact(amount, frequency), Decimal("9000.00"))
        with self.assertRaises(ValueError):
            annualize_impact(2250, "weekly")

    def test_invalid_financial_values_are_rejected(self):
        for aum, rate, excluded in [
            (-1, "0.01", 0), (100, "1.1", 0), (100, "-0.01", 0),
            (100, "0.01", 101), (100, "0.01", -1),
            (True, "0.01", 0), ("NaN", "0.01", 0), ("Infinity", "0.01", 0),
        ]:
            with self.subTest(aum=aum, rate=rate, excluded=excluded):
                with self.assertRaises(ValueError):
                    calculate_expected_fee(aum, rate, excluded_assets=excluded)


class AndersonCaseTests(unittest.TestCase):
    def setUp(self):
        self.definition = json.loads((ROOT / "data/demo/cases/CASE-001.json").read_text())
        self.evidence = get_case_evidence("CASE-001")

    def test_case_contains_computed_finding_and_source_references(self):
        case = get_revenue_case("CASE-001")
        self.assertEqual(case["expected_annual_fee"], 12000)
        self.assertEqual(case["actual_annual_fee"], 9000)
        self.assertEqual(case["annual_difference"], 3000)
        self.assertEqual(case["impact_direction"], "potential_underbilling")
        self.assertEqual(case["status"], "requires_review")
        self.assertEqual(case["as_of_date"], "2026-01-01")
        self.assertEqual(case["evidence_ids"], [e["evidence_id"] for e in self.evidence])
        self.assertEqual(len(self.evidence), 3)
        json.dumps(case)
        json.dumps(self.evidence)

    def test_exception_applies_through_its_last_valid_day(self):
        self.definition["as_of_date"] = "2025-12-31"
        case = build_revenue_case(self.definition, self.evidence)
        self.assertEqual(case["expected_rate"], 0.0075)
        self.assertEqual(case["expected_annual_fee"], 9000)
        self.assertEqual(case["annual_difference"], 0)
        self.assertEqual(case["status"], "no_discrepancy")
        self.assertEqual(case["anomaly_type"], "none")

    def test_exception_applies_on_its_first_valid_day(self):
        self.definition["as_of_date"] = "2025-01-01"
        self.assertEqual(build_revenue_case(self.definition, self.evidence)["expected_rate"], 0.0075)

    def test_amounts_are_computed_from_evidence_instead_of_hardcoded(self):
        self.evidence[0]["content"]["annual_rate"] = 0.0125
        case = build_revenue_case(self.definition, self.evidence)
        self.assertEqual(case["expected_annual_fee"], 15000)
        self.assertEqual(case["annual_difference"], 6000)

    def test_unknown_case_ids_are_rejected_by_both_tools(self):
        for tool in [get_revenue_case, get_case_evidence]:
            for case_id in ["CASE-999", "../../README"]:
                with self.subTest(tool=tool.__name__, case_id=case_id):
                    with self.assertRaises(KeyError):
                        tool(case_id)

    def test_callers_cannot_mutate_future_case_or_evidence_results(self):
        case = get_revenue_case("CASE-001")
        case["evidence_ids"].clear()
        self.evidence[0]["content"]["annual_rate"] = 0.99
        self.assertEqual(get_revenue_case("CASE-001")["expected_annual_fee"], 12000)
        self.assertEqual(len(get_revenue_case("CASE-001")["evidence_ids"]), 3)
        self.assertEqual(get_case_evidence("CASE-001")[0]["content"]["annual_rate"], 0.01)

    def test_missing_agreement_requires_review(self):
        with self.assertRaises(ValueError):
            build_revenue_case(self.definition, self.evidence[1:])

    def test_conflicting_agreements_require_review(self):
        conflict = deepcopy(self.evidence[0])
        conflict["evidence_id"] = "conflicting_agreement"
        conflict["content"]["annual_rate"] = 0.02
        with self.assertRaises(ValueError):
            build_revenue_case(self.definition, self.evidence + [conflict])

    def test_missing_authorization_requires_review(self):
        self.evidence[1]["content"]["authorization_status"] = "discussion_only"
        with self.assertRaises(ValueError):
            build_revenue_case(self.definition, self.evidence)

    def test_invalid_exception_date_range_requires_review(self):
        self.evidence[1]["content"]["effective_date"] = "2026-01-01"
        with self.assertRaises(ValueError):
            build_revenue_case(self.definition, self.evidence)

    def test_expired_or_future_agreements_are_rejected(self):
        for update in [{"expiration_date": "2025-12-31"}, {"effective_date": "2027-01-01"}]:
            with self.subTest(update=update):
                evidence = deepcopy(self.evidence)
                evidence[0]["content"].update(update)
                with self.assertRaises(ValueError):
                    build_revenue_case(self.definition, evidence)

    def test_malformed_or_unsupported_pricing_is_rejected(self):
        for field, value in [("calculation_method", "marginal"), ("as_of_date", "invalid")]:
            with self.subTest(field=field):
                definition = dict(self.definition, **{field: value})
                with self.assertRaises(ValueError):
                    build_revenue_case(definition, self.evidence)
        del self.evidence[0]["content"]["annual_rate"]
        with self.assertRaises(ValueError):
            build_revenue_case(self.definition, self.evidence)

    def test_case_evidence_must_match_requested_case(self):
        self.evidence[0]["case_id"] = "CASE-002"
        with self.assertRaises(ValueError):
            build_revenue_case(self.definition, self.evidence)

    def test_case_evidence_must_match_household(self):
        self.evidence[0]["content"]["household"] = "Patel Household"
        with self.assertRaises(ValueError):
            build_revenue_case(self.definition, self.evidence)

    def test_incomplete_evidence_envelopes_are_rejected(self):
        for field in ["evidence_id", "title", "source_path", "content"]:
            with self.subTest(field=field):
                evidence = deepcopy(self.evidence)
                del evidence[0][field]
                with self.assertRaises(ValueError):
                    build_revenue_case(self.definition, evidence)


if __name__ == "__main__":
    unittest.main()
