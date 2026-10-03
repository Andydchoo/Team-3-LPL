"""Financial acceptance tests for CASE-002..004 (Patel, Chen, Ramirez)."""

import json
import unittest
from copy import deepcopy
from pathlib import Path

from revenue_engine import get_case_evidence, get_revenue_case
from revenue_engine.cases import build_revenue_case

ROOT = Path(__file__).resolve().parent.parent


class SecondaryCaseTests(unittest.TestCase):
    def test_patel_client_overbilling(self):
        case = get_revenue_case("CASE-002")
        self.assertEqual(case["expected_annual_fee"], 6400)
        self.assertEqual(case["actual_annual_fee"], 8000)
        self.assertEqual(case["annual_difference"], 1600)
        self.assertEqual(case["impact_direction"], "potential_overbilling")

    def test_chen_marginal_breakpoint(self):
        case = get_revenue_case("CASE-003")
        self.assertEqual(case["calculation_method"], "marginal")
        self.assertEqual(case["expected_annual_fee"], 17500)
        self.assertEqual(case["actual_annual_fee"], 20000)
        self.assertEqual(case["annual_difference"], 2500)
        self.assertEqual(case["expected_rate"], 0.00875)
        self.assertEqual(case["impact_direction"], "potential_overbilling")

    def test_ramirez_asset_exclusion(self):
        case = get_revenue_case("CASE-004")
        self.assertEqual(case["expected_annual_fee"], 6000)
        self.assertEqual(case["actual_annual_fee"], 8000)
        self.assertEqual(case["annual_difference"], 2000)
        self.assertEqual(case["impact_direction"], "potential_overbilling")

    def test_evidence_matches_case_ids_and_is_json(self):
        for case_id in ["CASE-002", "CASE-003", "CASE-004"]:
            with self.subTest(case_id=case_id):
                case = get_revenue_case(case_id)
                evidence = get_case_evidence(case_id)
                self.assertEqual(case["evidence_ids"], [e["evidence_id"] for e in evidence])
                self.assertEqual(len(evidence), 2)
                json.dumps(case)
                json.dumps(evidence)

    def test_ramirez_without_explicit_exclusion_has_no_discrepancy(self):
        definition = json.loads((ROOT / "data/demo/cases/CASE-004.json").read_text())
        evidence = deepcopy(get_case_evidence("CASE-004"))
        evidence[0]["content"]["excluded_assets"] = 0
        self.assertEqual(build_revenue_case(definition, evidence)["annual_difference"], 0)

    def test_marginal_case_rejects_flat_agreement(self):
        definition = json.loads((ROOT / "data/demo/cases/CASE-003.json").read_text())
        evidence = deepcopy(get_case_evidence("CASE-003"))
        evidence[0]["content"]["pricing_method"] = "flat"
        with self.assertRaises(ValueError):
            build_revenue_case(definition, evidence)


if __name__ == "__main__":
    unittest.main()
