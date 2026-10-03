"""Offline tests for Anderson acceptance checks (no AWS)."""

from __future__ import annotations

import unittest

from investigation.anderson import evaluate_anderson


def _base(**overrides):
    result = {
        "case_id": "CASE-001",
        "investigation_status": "supported_explanation",
        "likely_cause": "Expired temporary pricing exception",
        "summary": "Billing still reflects the exception after it expired.",
        "evidence_strength": "high",
        "evidence_used": [
            {"evidence_id": "anderson_exception", "finding": "Ended 2025-12-31"}
        ],
        "uncertainties": [],
        "recommended_action": "Send to authorized human review before next billing.",
        "requires_human_review": True,
    }
    result.update(overrides)
    return result


class AndersonCheckTests(unittest.TestCase):
    def test_passes_expected_anderson_shape(self):
        self.assertEqual(evaluate_anderson(_base()), [])

    def test_rejects_investigation_error(self):
        failures = evaluate_anderson(
            _base(investigation_status="investigation_error")
        )
        self.assertTrue(any("investigation_status" in item for item in failures))

    def test_rejects_auto_raise(self):
        failures = evaluate_anderson(
            _base(
                recommended_action="The fee should be raised automatically to 1.00%."
            )
        )
        self.assertTrue(any("automatically" in item for item in failures))

    def test_rejects_missing_exception_narrative(self):
        failures = evaluate_anderson(
            _base(likely_cause="Rate mismatch", summary="Numbers differ.")
        )
        self.assertTrue(any("exception" in item for item in failures))


if __name__ == "__main__":
    unittest.main()
