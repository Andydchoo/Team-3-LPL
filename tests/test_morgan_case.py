"""Engine + offline Morgan acceptance checks."""

from __future__ import annotations

import unittest

from investigation.morgan import evaluate_morgan
from revenue_engine import get_case_evidence, get_revenue_case


class MorganEngineTests(unittest.TestCase):
    def test_get_revenue_case_is_review_dependent(self):
        case = get_revenue_case("CASE-005")
        self.assertEqual(case["household"], "Morgan Household")
        self.assertEqual(case["calculation_method"], "review_dependent")
        self.assertEqual(case["impact_direction"], "review_dependent")
        self.assertIsNone(case["expected_annual_fee"])
        self.assertIsNone(case["actual_annual_fee"])
        self.assertIsNone(case["annual_difference"])
        self.assertEqual(case["expected_rate"], 0.01)
        self.assertEqual(case["actual_rate"], 0.0075)
        self.assertEqual(case["status"], "requires_review")

    def test_get_case_evidence_includes_discussion_note(self):
        evidence = get_case_evidence("CASE-005")
        ids = [item["evidence_id"] for item in evidence]
        self.assertEqual(
            ids,
            ["morgan_agreement", "morgan_billing", "morgan_internal_note"],
        )
        note = evidence[2]["content"]
        self.assertIn("discussed extending preferred pricing", note["note"])
        self.assertEqual(note["authorization_status"], "discussion_only")
        self.assertFalse(note["finalized"])


class MorganCheckTests(unittest.TestCase):
    def _base(self, **overrides):
        result = {
            "case_id": "CASE-005",
            "investigation_status": "conflicting_evidence",
            "likely_cause": "Billing rate conflicts with agreement; discussion not finalized",
            "summary": (
                "Agreement is 1.00% while billing is 0.75%. An internal note says "
                "preferred pricing was discussed but authorization is not finalized."
            ),
            "evidence_strength": "medium",
            "evidence_used": [
                {"evidence_id": "morgan_agreement", "finding": "Agreement 1.00%"},
                {
                    "evidence_id": "morgan_internal_note",
                    "finding": "Discussion only; not authorized",
                },
            ],
            "uncertainties": ["No finalized authorization for preferred pricing."],
            "recommended_action": "Route to authorized human review before changing rates.",
            "requires_human_review": True,
        }
        result.update(overrides)
        return result

    def test_passes_expected_morgan_shape(self):
        self.assertEqual(evaluate_morgan(self._base()), [])

    def test_rejects_supported_explanation(self):
        failures = evaluate_morgan(
            self._base(investigation_status="supported_explanation")
        )
        self.assertTrue(failures)

    def test_rejects_confident_rate_change(self):
        failures = evaluate_morgan(
            self._base(
                recommended_action="The rate should be raised to 1.00% immediately."
            )
        )
        self.assertTrue(any("confidently" in item for item in failures))


if __name__ == "__main__":
    unittest.main()
