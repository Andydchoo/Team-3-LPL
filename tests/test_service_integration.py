"""Offline checks of owner handoffs, validation and private review writes."""

import copy
import json
import os
import unittest
from types import SimpleNamespace
from unittest.mock import ANY, Mock, patch

try:
    from botocore.exceptions import ClientError
    from botocore.stub import Stubber
    from jsonschema import Draft202012Validator, FormatChecker
except ImportError:
    raise unittest.SkipTest("Install requirements-aws.txt for service integration tests")

from integration.investigation_adapter import (
    SCHEMA_PATH, investigate_case, validate_investigation,
)
from integration.reviews import S3ReviewStore
from integration.service_boundary import IntegrationUnavailable, backend_mode
from revenue_engine import get_case_evidence, get_revenue_case
from test_aws_integration import ACCOUNT, BUCKET, REQUEST, client, stub_privacy
from ui import services


def investigation_fixture():
    with patch.dict(os.environ, {"REVENUE_BACKEND": "local"}):
        return services.investigate_case("CASE-001")


class ServiceBoundaryTests(unittest.TestCase):
    def test_local_mode_stays_local_even_when_an_agent_exists(self):
        agent = Mock()
        with patch.dict(os.environ, {}, clear=True), patch.dict("sys.modules", {
            "investigation": SimpleNamespace(investigate_case=agent),
        }), patch("integration.case_tools.get_revenue_case") as aws_case:
            self.assertEqual(services.get_revenue_case("CASE-001"), get_revenue_case("CASE-001"))
            self.assertEqual(services.investigate_case("CASE-001")["investigation_status"], "supported_explanation")
            review = services.record_review("CASE-001", "send_for_review")
        self.assertTrue(review["recorded_at"].endswith("Z"))
        agent.assert_not_called()
        aws_case.assert_not_called()

    def test_aws_mode_routes_both_read_tools_to_s3_adapters(self):
        with patch.dict(os.environ, {"REVENUE_BACKEND": "aws"}), \
             patch("integration.case_tools.get_revenue_case", return_value={"marker": "s3-case"}) as case, \
             patch("integration.case_tools.get_case_evidence", return_value=[{"marker": "s3-evidence"}]) as evidence:
            self.assertEqual(services.get_revenue_case("CASE-001"), {"marker": "s3-case"})
            self.assertEqual(services.get_case_evidence("CASE-001"), [{"marker": "s3-evidence"}])
        case.assert_called_once_with("CASE-001")
        evidence.assert_called_once_with("CASE-001")

    def test_aws_mode_never_falls_back_to_mock_cases_or_reviews(self):
        with patch.dict(os.environ, {"REVENUE_BACKEND": "aws"}):
            for function in (services.get_revenue_case, services.get_case_evidence, services.investigate_case):
                with self.assertRaises(IntegrationUnavailable):
                    function("CASE-003")
            with patch("integration.record_review", side_effect=RuntimeError("write failed")):
                with self.assertRaises(RuntimeError):
                    services.record_review("CASE-001", "send_for_review")

    def test_invalid_mode_is_rejected(self):
        with patch.dict(os.environ, {"REVENUE_BACKEND": "typo"}):
            with self.assertRaises(IntegrationUnavailable):
                backend_mode()


class InvestigationHandoffTests(unittest.TestCase):
    def test_valid_result_is_returned_with_verified_evidence_references(self):
        result = investigation_fixture()
        agent = Mock(return_value=result)
        with patch("integration.investigation_adapter.load_agent", return_value=agent), \
             patch("integration.investigation_adapter.get_case_evidence", return_value=get_case_evidence("CASE-001")):
            self.assertEqual(investigate_case("CASE-001"), result)
        agent.assert_called_once_with("CASE-001")

    def test_missing_agent_is_an_error_and_not_a_mock_explanation(self):
        with patch("integration.investigation_adapter.importlib.import_module",
                   side_effect=ModuleNotFoundError(name="investigation")):
            result = investigate_case("CASE-001")
        self.assertEqual(result["investigation_status"], "investigation_error")
        self.assertIn("not integrated", result["summary"])
        self.assertEqual(result["evidence_used"], [])

    def test_s3_failure_prevents_agent_call_and_sanitizes_error(self):
        agent = Mock()
        error = ClientError({"Error": {"Code": "AccessDenied", "Message": "never-echo-this"}}, "GetObject")
        with patch("integration.investigation_adapter.load_agent", return_value=agent), \
             patch("integration.investigation_adapter.get_case_evidence", side_effect=error):
            result = investigate_case("CASE-001")
        self.assertEqual(result["investigation_status"], "investigation_error")
        self.assertNotIn("never-echo-this", json.dumps(result))
        agent.assert_not_called()

    def test_external_exception_text_is_not_exposed(self):
        agent = Mock(side_effect=ValueError("never-echo-this"))
        with patch("integration.investigation_adapter.load_agent", return_value=agent), \
             patch("integration.investigation_adapter.get_case_evidence", return_value=get_case_evidence("CASE-001")):
            result = investigate_case("CASE-001")
        self.assertEqual(result["investigation_status"], "investigation_error")
        self.assertNotIn("never-echo-this", json.dumps(result))

    def test_malformed_wrong_case_and_unverified_evidence_are_rejected(self):
        # Validate context as well as the JSON shape.
        original = investigation_fixture()
        examples = []
        for field, value in (("case_id", "CASE-003"), ("requires_human_review", False),
                             ("investigation_status", "invented"), ("evidence_used", []),
                             ("evidence_used", [{"evidence_id": "invented", "finding": "unverified"}]),
                             ("evidence_used", [original["evidence_used"][0]] * 2)):
            result = copy.deepcopy(original)
            result[field] = value
            examples.append(result)
        examples.extend(["not-json", dict(original, unexpected="never-echo-this")])
        for result in examples:
            with self.subTest(result=result), self.assertRaises(IntegrationUnavailable):
                validate_investigation(result, "CASE-001", get_case_evidence("CASE-001"))

    def test_agent_error_payload_is_replaced_by_a_clean_error(self):
        payload = investigation_fixture()
        payload.update(investigation_status="investigation_error", summary="Traceback: never-echo-this")
        with patch("integration.investigation_adapter.load_agent", return_value=Mock(return_value=payload)), \
             patch("integration.investigation_adapter.get_case_evidence", return_value=get_case_evidence("CASE-001")):
            result = investigate_case("CASE-001")
        self.assertEqual(result["investigation_status"], "investigation_error")
        self.assertNotIn("never-echo-this", json.dumps(result))


class ReviewPersistenceTests(unittest.TestCase):
    def setUp(self):
        self.s3 = client("s3")
        self.store = S3ReviewStore(self.s3, BUCKET, ACCOUNT)

    def test_review_is_scoped_encrypted_and_schema_valid_after_write(self):
        with Stubber(self.s3) as stub:
            stub_privacy(stub)
            stub.add_response("put_object", {}, dict(
                REQUEST, Key="reviews/CASE-001/REV-ABC.json", Body=ANY,
                ContentType="application/json", ServerSideEncryption="AES256", IfNoneMatch="*",
            ))
            with patch("integration.reviews.uuid4", return_value=SimpleNamespace(hex="abc")), \
                 patch.object(self.s3, "put_object", wraps=self.s3.put_object) as write:
                review = self.store.record_review("CASE-001", "send_for_review")
            self.assertEqual(json.loads(write.call_args.kwargs["Body"]), review)
            stub.assert_no_pending_responses()
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        Draft202012Validator({"$defs": schema["$defs"], "$ref": "#/$defs/ReviewRecord"},
                             format_checker=FormatChecker()).validate(review)
        self.assertEqual(review["actor"], "human")

    def test_failed_write_does_not_return_a_review_confirmation(self):
        with Stubber(self.s3) as stub:
            stub_privacy(stub)
            stub.add_client_error("put_object", service_error_code="AccessDenied", expected_params=dict(
                REQUEST, Key=ANY, Body=ANY, ContentType="application/json",
                ServerSideEncryption="AES256", IfNoneMatch="*",
            ))
            with self.assertRaises(ClientError):
                self.store.record_review("CASE-001", "send_for_review")
            stub.assert_no_pending_responses()

    def test_invalid_decision_is_rejected_before_any_aws_request(self):
        with Stubber(self.s3), self.assertRaises(IntegrationUnavailable):
            self.store.record_review("CASE-001", "change_fee")
