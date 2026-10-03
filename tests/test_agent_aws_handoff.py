"""Verify the integrated agent uses private storage and paced service calls."""

import json
import os
import unittest
from unittest.mock import Mock, patch

try:
    from investigation import investigate_case
    from investigation.tools import TOOL_HANDLERS, dispatch_tool
    from integration.bedrock_runtime import RequestPacer
except ImportError:
    raise unittest.SkipTest("Install AWS requirements for the integrated agent tests")

from test_service_integration import investigation_fixture
from revenue_engine import get_case_evidence


class AgentAWSHandoffTests(unittest.TestCase):
    def test_live_agent_uses_s3_for_validation_and_both_registered_tools(self):
        result = investigation_fixture()
        fake_client = Mock()
        fake_client.converse.side_effect = [
            {"output": {"message": {"role": "assistant", "content": [
                {"toolUse": {"toolUseId": "case", "name": "get_revenue_case", "input": {"case_id": "CASE-001"}}},
                {"toolUse": {"toolUseId": "evidence", "name": "get_case_evidence", "input": {"case_id": "CASE-001"}}},
            ]}}},
            {"output": {"message": {"role": "assistant", "content": [{"text": json.dumps(result)}]}}},
        ]
        with patch.dict(os.environ, {"REVENUE_BACKEND": "aws"}), \
             patch("integration.case_tools.get_revenue_case", return_value={"case_id": "CASE-001", "annual_difference": 3000}) as case, \
             patch("integration.case_tools.get_case_evidence", return_value=get_case_evidence("CASE-001")) as evidence, \
             patch("investigation.investigate.create_bedrock_client", return_value=fake_client):
            self.assertEqual(investigate_case("CASE-001"), result)
        case.assert_called_once_with("CASE-001")
        self.assertEqual(evidence.call_count, 2)  # Validation plus the model's tool call.
        self.assertEqual(set(TOOL_HANDLERS), {"get_revenue_case", "get_case_evidence"})

    def test_human_review_is_not_an_agent_tool(self):
        result = json.loads(dispatch_tool("record_review", {"case_id": "CASE-001", "decision": "dismiss"}))
        self.assertIn("Unknown tool", result["error"])

    def test_request_pacing_applies_after_success_and_failure(self):
        clock = [10.0]
        starts = []
        def sleep(delay):
            clock[0] += delay
        def request(**kwargs):
            starts.append(clock[0])
            clock[0] += 0.1
            if len(starts) == 2:
                raise RuntimeError("simulated request failure")
            return {"ok": True}
        pacer = RequestPacer()
        with patch("integration.bedrock_runtime.time.monotonic", side_effect=lambda: clock[0]), \
             patch("integration.bedrock_runtime.time.sleep", side_effect=sleep):
            pacer.call(request)
            with self.assertRaises(RuntimeError):
                pacer.call(request)
            pacer.call(request)
        self.assertEqual(starts, [10.0, 11.0, 12.0])
