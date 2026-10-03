"""Exercise the real frontend without credentials or live service requests."""

import os
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

try:
    from botocore.exceptions import ClientError
    from streamlit.testing.v1 import AppTest
    import jsonschema
except ImportError:
    raise unittest.SkipTest("Install requirements.txt and requirements-aws.txt for frontend integration tests")

from revenue_engine import get_case_evidence, get_revenue_case
from test_service_integration import investigation_fixture

APP = Path(__file__).resolve().parent.parent / "app.py"


def click_label(app, text):
    next(button for button in app.button if text in button.label).click().run()


class StreamlitIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.environment = patch.dict(os.environ, {"REVENUE_BACKEND": "local", "AWS_EC2_METADATA_DISABLED": "true"})
        self.environment.start()
        self.addCleanup(self.environment.stop)

    def case_screen(self):
        app = AppTest.from_file(str(APP), default_timeout=15).run()
        app.button(key="side_CASE-001").click().run()
        self.assertFalse(app.exception)
        return app

    def assert_finding_and_evidence_remain(self, app):
        self.assertFalse(app.exception)
        self.assertEqual(len(app.get("json")), 3)
        rendered = " ".join(item.body for item in app.get("html"))
        self.assertIn("$12,000", rendered)
        self.assertIn("$9,000", rendered)
        self.assertIn("$3,000", rendered)

    def test_local_demo_investigation_and_review_still_work(self):
        app = self.case_screen()
        click_label(app, "Investigate with RevenueTwin")
        click_label(app, "Send for Review")
        self.assertEqual(app.session_state["review"]["actor"], "human")
        self.assertTrue(any("demo session only" in item.value for item in app.caption))
        self.assert_finding_and_evidence_remain(app)

    def test_aws_error_preserves_finding_evidence_and_retry(self):
        result = investigation_fixture()
        error = ClientError({"Error": {"Code": "ThrottlingException", "Message": "never-echo-this"}}, "Converse")
        agent = Mock(side_effect=error)
        with patch.dict(os.environ, {"REVENUE_BACKEND": "aws"}), \
             patch("integration.case_tools.get_revenue_case", return_value=get_revenue_case("CASE-001")), \
             patch("integration.case_tools.get_case_evidence", return_value=get_case_evidence("CASE-001")), \
             patch("integration.investigation_adapter.get_case_evidence", return_value=get_case_evidence("CASE-001")), \
             patch("integration.investigation_adapter.load_agent", return_value=agent):
            app = self.case_screen()
            click_label(app, "Investigate with RevenueTwin")
            self.assertEqual(app.session_state["investigation"]["investigation_status"], "investigation_error")
            self.assertNotIn("never-echo-this", " ".join(item.value for item in app.error))
            self.assert_finding_and_evidence_remain(app)
            click_label(app, "Retry Investigation")
            agent.side_effect = None
            agent.return_value = result
            click_label(app, "Investigate with RevenueTwin")
            self.assertFalse(app.error)
            self.assertEqual(app.session_state["investigation"], result)

    def test_review_write_failure_is_clean_and_can_be_retried(self):
        result = investigation_fixture()
        error = ClientError({"Error": {"Code": "AccessDenied", "Message": "never-echo-this"}}, "PutObject")
        review = {"review_id": "REV-test", "case_id": "CASE-001", "decision": "send_for_review",
                  "actor": "human", "recorded_at": "2026-01-01T12:00:00Z"}
        with patch.dict(os.environ, {"REVENUE_BACKEND": "aws"}), \
             patch("integration.case_tools.get_revenue_case", return_value=get_revenue_case("CASE-001")), \
             patch("integration.case_tools.get_case_evidence", return_value=get_case_evidence("CASE-001")), \
             patch("integration.investigation_adapter.get_case_evidence", return_value=get_case_evidence("CASE-001")), \
             patch("integration.investigation_adapter.load_agent", return_value=Mock(return_value=result)), \
             patch("integration.record_review", side_effect=error) as write:
            app = self.case_screen()
            click_label(app, "Investigate with RevenueTwin")
            click_label(app, "Send for Review")
            self.assertIsNone(app.session_state["review"])
            self.assertIn("not confirmed", app.error[0].value)
            self.assertNotIn("never-echo-this", app.error[0].value)
            self.assert_finding_and_evidence_remain(app)
            write.side_effect = None
            write.return_value = review
            click_label(app, "Send for Review")
            self.assertEqual(app.session_state["review"], review)
            self.assertFalse(app.error)
            self.assertTrue(any("Saved to private S3" in item.value for item in app.caption))

    def test_case_read_failure_has_a_clean_retry_without_mock_fallback(self):
        error = ClientError({"Error": {"Code": "NoSuchKey", "Message": "never-echo-this"}}, "GetObject")
        with patch.dict(os.environ, {"REVENUE_BACKEND": "aws"}), \
             patch("integration.case_tools.get_revenue_case", side_effect=error):
            app = self.case_screen()
            self.assertTrue(app.error)
            self.assertNotIn("never-echo-this", app.error[0].value)
            self.assertTrue(any(button.label == "Retry loading case" for button in app.button))
            self.assertEqual(len(app.get("json")), 0)

    def test_switching_backend_discards_prior_mock_investigation_and_review(self):
        app = self.case_screen()
        click_label(app, "Investigate with RevenueTwin")
        click_label(app, "Send for Review")
        with patch.dict(os.environ, {"REVENUE_BACKEND": "aws"}), \
             patch("integration.case_tools.get_revenue_case", return_value=get_revenue_case("CASE-001")), \
             patch("integration.case_tools.get_case_evidence", return_value=get_case_evidence("CASE-001")):
            app.run()
        self.assertIsNone(app.session_state["investigation"])
        self.assertIsNone(app.session_state["review"])
        self.assertFalse(app.exception)

    def test_model_text_is_rendered_as_text_in_html_cards(self):
        result = investigation_fixture()
        result["summary"] = '<img src="untrusted" onerror="alert(1)">'
        with patch.dict(os.environ, {"REVENUE_BACKEND": "aws"}), \
             patch("integration.case_tools.get_revenue_case", return_value=get_revenue_case("CASE-001")), \
             patch("integration.case_tools.get_case_evidence", return_value=get_case_evidence("CASE-001")), \
             patch("integration.investigation_adapter.get_case_evidence", return_value=get_case_evidence("CASE-001")), \
             patch("integration.investigation_adapter.load_agent", return_value=Mock(return_value=result)):
            app = self.case_screen()
            click_label(app, "Investigate with RevenueTwin")
        rendered = " ".join(item.body for item in app.get("html"))
        self.assertIn("&lt;img", rendered)
        self.assertNotIn('<img src="untrusted"', rendered)
        self.assertFalse(app.exception)
