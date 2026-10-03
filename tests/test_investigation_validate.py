"""Unit tests for Investigation JSON parsing/validation (no AWS calls)."""

from __future__ import annotations

import unittest

from investigation.validate import (
    extract_json_object,
    investigation_error,
    validate_investigation,
)


class ValidateInvestigationTests(unittest.TestCase):
    def test_extract_json_from_fenced_text(self):
        text = 'Here:\n```json\n{"case_id": "CASE-001", "ok": true}\n```\n'
        self.assertEqual(
            extract_json_object(text),
            {"case_id": "CASE-001", "ok": True},
        )

    def test_validate_happy_path(self):
        raw = {
            "case_id": "CASE-001",
            "investigation_status": "supported_explanation",
            "likely_cause": "Expired temporary pricing exception",
            "summary": "Billing still uses 0.75% after exception end.",
            "evidence_strength": "high",
            "evidence_used": [
                {
                    "evidence_id": "anderson_exception",
                    "finding": "Exception ended 2025-12-31",
                }
            ],
            "uncertainties": [],
            "recommended_action": "Send to advisor for authorized human review.",
            "requires_human_review": False,
        }
        result = validate_investigation(
            raw,
            case_id="CASE-001",
            allowed_evidence_ids={"anderson_exception", "anderson_agreement"},
        )
        self.assertTrue(result["requires_human_review"])
        self.assertEqual(result["investigation_status"], "supported_explanation")

    def test_rejects_unknown_evidence_id(self):
        raw = {
            "case_id": "CASE-001",
            "investigation_status": "supported_explanation",
            "likely_cause": "x",
            "summary": "summary",
            "evidence_strength": "medium",
            "evidence_used": [{"evidence_id": "nope", "finding": "x"}],
            "uncertainties": [],
            "recommended_action": "review",
            "requires_human_review": True,
        }
        with self.assertRaises(ValueError):
            validate_investigation(
                raw,
                case_id="CASE-001",
                allowed_evidence_ids={"anderson_exception"},
            )

    def test_investigation_error_shape(self):
        err = investigation_error("CASE-001", "boom")
        self.assertEqual(err["investigation_status"], "investigation_error")
        self.assertIs(err["requires_human_review"], True)


if __name__ == "__main__":
    unittest.main()
