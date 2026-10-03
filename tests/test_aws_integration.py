import configparser
import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

try:
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError
    from botocore.response import StreamingBody
    from botocore.stub import Stubber
except ImportError:
    raise unittest.SkipTest("Install requirements-aws.txt to run AWS integration tests")

from integration.aws_config import AWSSettings, safe_error_message
from integration.aws_preflight import run_preflight
from integration.case_tools import get_revenue_case as s3_revenue_case
from integration.configure_credentials import save_profile
from integration.s3_evidence import PUBLIC_ACCESS_BLOCK, S3EvidenceStore, assert_private_bucket
from integration.setup_s3 import create_private_bucket
from revenue_engine import get_case_evidence

ACCOUNT = "123456789012"
BUCKET = "revenuetwin-test-evidence"
REQUEST = {"Bucket": BUCKET, "ExpectedBucketOwner": ACCOUNT}


def client(service):
    # Deliberately fake test values; Stubber prevents all network calls.
    return boto3.client(service, region_name="us-east-1", aws_access_key_id="testing",
                        aws_secret_access_key="testing", aws_session_token="testing")


def stub_privacy(stub):
    stub.add_response("get_bucket_location", {}, REQUEST)
    stub.add_response("get_public_access_block", {"PublicAccessBlockConfiguration": PUBLIC_ACCESS_BLOCK}, REQUEST)
    stub.add_response("get_bucket_ownership_controls", {"OwnershipControls": {"Rules": [{"ObjectOwnership": "BucketOwnerEnforced"}]}}, REQUEST)
    stub.add_response("get_bucket_policy_status", {"PolicyStatus": {"IsPublic": False}}, REQUEST)


def stub_evidence(stub, records=None):
    for record in records if records is not None else get_case_evidence("CASE-001"):
        encoded = json.dumps(record).encode()
        stub.add_response("get_object", {"Body": StreamingBody(io.BytesIO(encoded), len(encoded))},
                          dict(REQUEST, Key=record["source_path"]))


class AWSConfigurationTests(unittest.TestCase):
    def test_region_is_enforced(self):
        with self.assertRaises(ValueError):
            AWSSettings(region="us-west-2")
        with patch.dict(os.environ, {"AWS_DEFAULT_REGION": "us-west-2"}, clear=True):
            with self.assertRaises(ValueError):
                AWSSettings.from_environment()

    def test_nonsecret_environment_settings_are_loaded(self):
        with patch.dict(os.environ, {"AWS_DEFAULT_REGION": "us-east-1", "AWS_PROFILE": "event",
                                  "REVENUE_S3_BUCKET": BUCKET, "BEDROCK_MODEL_ID": "assigned-model"}, clear=True):
            settings = AWSSettings.from_environment()
        self.assertEqual(settings.profile, "event")
        self.assertEqual(settings.bucket, BUCKET)
        self.assertEqual(settings.model_id, "assigned-model")

    def test_credential_setup_preserves_unrelated_profiles(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            (folder / "credentials").write_text("[other]\naws_access_key_id = keep\n", encoding="utf-8")
            (folder / "config").write_text("[profile other]\nregion = us-west-2\n", encoding="utf-8")
            save_profile("event", {"aws_access_key_id": "testing", "aws_secret_access_key": "testing",
                                   "aws_session_token": "testing"}, folder)
            parsed = configparser.ConfigParser()
            parsed.read(folder / "credentials")
            self.assertEqual(parsed["other"]["aws_access_key_id"], "keep")
            self.assertEqual(parsed["event"]["aws_session_token"], "testing")
            parsed = configparser.ConfigParser()
            parsed.read(folder / "config")
            self.assertEqual(parsed["profile event"]["region"], "us-east-1")
            self.assertEqual(parsed["profile other"]["region"], "us-west-2")

    def test_partial_temporary_credentials_are_rejected_before_writing(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                save_profile("event", {"aws_access_key_id": "testing"}, Path(directory))
            self.assertFalse((Path(directory) / "credentials").exists())

    def test_service_errors_do_not_echo_raw_messages(self):
        error = ClientError({"Error": {"Code": "AccessDenied", "Message": "secret-value-do-not-echo"}}, "Converse")
        message = safe_error_message(error)
        self.assertNotIn("secret-value", message)
        self.assertIn("permissions", message)


class S3EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.s3 = client("s3")
        self.stub = Stubber(self.s3)
        self.stub.activate()
        self.addCleanup(self.stub.deactivate)
        self.store = S3EvidenceStore(self.s3, BUCKET, ACCOUNT)

    def test_private_bucket_is_verified(self):
        stub_privacy(self.stub)
        assert_private_bucket(self.s3, BUCKET, ACCOUNT)
        self.stub.assert_no_pending_responses()

    def test_public_access_blocks_are_required(self):
        self.stub.add_response("get_bucket_location", {}, REQUEST)
        self.stub.add_response("get_public_access_block", {"PublicAccessBlockConfiguration": dict(PUBLIC_ACCESS_BLOCK, BlockPublicPolicy=False)}, REQUEST)
        with self.assertRaises(ValueError):
            assert_private_bucket(self.s3, BUCKET, ACCOUNT)
        self.stub.assert_no_pending_responses()

    def test_wrong_region_is_rejected(self):
        self.stub.add_response("get_bucket_location", {"LocationConstraint": "us-west-2"}, REQUEST)
        with self.assertRaises(ValueError):
            assert_private_bucket(self.s3, BUCKET, ACCOUNT)

    def test_public_policy_is_rejected_even_with_block_settings(self):
        self.stub.add_response("get_bucket_location", {}, REQUEST)
        self.stub.add_response("get_public_access_block", {"PublicAccessBlockConfiguration": PUBLIC_ACCESS_BLOCK}, REQUEST)
        self.stub.add_response("get_bucket_ownership_controls", {"OwnershipControls": {"Rules": [{"ObjectOwnership": "BucketOwnerEnforced"}]}}, REQUEST)
        self.stub.add_response("get_bucket_policy_status", {"PolicyStatus": {"IsPublic": True}}, REQUEST)
        with self.assertRaises(ValueError):
            assert_private_bucket(self.s3, BUCKET, ACCOUNT)

    def test_private_bucket_without_policy_is_supported(self):
        self.stub.add_response("get_bucket_location", {}, REQUEST)
        self.stub.add_response("get_public_access_block", {"PublicAccessBlockConfiguration": PUBLIC_ACCESS_BLOCK}, REQUEST)
        self.stub.add_response("get_bucket_ownership_controls", {"OwnershipControls": {"Rules": [{"ObjectOwnership": "BucketOwnerEnforced"}]}}, REQUEST)
        self.stub.add_client_error("get_bucket_policy_status", service_error_code="NoSuchBucketPolicy", expected_params=REQUEST)
        assert_private_bucket(self.s3, BUCKET, ACCOUNT)

    def test_read_preserves_shared_evidence_envelopes(self):
        expected = get_case_evidence("CASE-001")
        stub_evidence(self.stub)
        self.assertEqual(self.store.get_case_evidence("CASE-001"), expected)
        self.stub.assert_no_pending_responses()

    def test_wrong_case_evidence_is_rejected(self):
        record = get_case_evidence("CASE-001")[0]
        record["case_id"] = "CASE-002"
        stub_evidence(self.stub, [record])
        with self.assertRaises(ValueError):
            self.store.get_case_evidence("CASE-001")

    def test_unlabeled_synthetic_data_is_rejected(self):
        record = get_case_evidence("CASE-001")[0]
        del record["content"]["synthetic"]
        stub_evidence(self.stub, [record])
        with self.assertRaises(ValueError):
            self.store.get_case_evidence("CASE-001")

    def test_upload_requires_privacy_and_uses_encryption(self):
        stub_privacy(self.stub)
        expected_keys = []
        for record in get_case_evidence("CASE-001"):
            expected_keys.append(record["source_path"])
            self.stub.add_response("put_object", {}, dict(
                REQUEST, Key=record["source_path"],
                Body=json.dumps(record, indent=2, ensure_ascii=False).encode(),
                ContentType="application/json", ServerSideEncryption="AES256",
            ))
        self.assertEqual(self.store.upload_case_evidence("CASE-001"), expected_keys)
        self.stub.assert_no_pending_responses()

    def test_missing_object_errors_are_not_silently_replaced_with_local_data(self):
        self.stub.add_client_error("get_object", service_error_code="NoSuchKey",
                                   expected_params=dict(REQUEST, Key="evidence/anderson/agreement.json"))
        with self.assertRaises(ClientError):
            self.store.get_case_evidence("CASE-001")

    def test_existing_bucket_is_not_recreated(self):
        self.stub.add_response("head_bucket", {}, REQUEST)
        with self.assertRaises(ValueError):
            create_private_bucket(self.s3, BUCKET, ACCOUNT)
        self.stub.assert_no_pending_responses()

    def test_new_bucket_is_created_in_us_east_1_with_private_settings(self):
        self.stub.add_client_error("head_bucket", service_error_code="404", http_status_code=404, expected_params=REQUEST)
        self.stub.add_response("create_bucket", {}, {"Bucket": BUCKET, "ObjectOwnership": "BucketOwnerEnforced"})
        self.stub.add_response("put_public_access_block", {}, dict(REQUEST, PublicAccessBlockConfiguration=PUBLIC_ACCESS_BLOCK))
        self.stub.add_response("put_bucket_encryption", {}, dict(REQUEST, ServerSideEncryptionConfiguration={
            "Rules": [{"ApplyServerSideEncryptionByDefault": {"SSEAlgorithm": "AES256"}}],
        }))
        create_private_bucket(self.s3, BUCKET, ACCOUNT)
        self.stub.assert_no_pending_responses()

    def test_case_adapter_uses_s3_evidence_for_engine_calculations(self):
        evidence = get_case_evidence("CASE-001")
        evidence[0]["content"]["annual_rate"] = 0.0125
        with patch("integration.case_tools.get_case_evidence", return_value=evidence):
            case = s3_revenue_case("CASE-001")
        self.assertEqual(case["expected_annual_fee"], 15000)
        self.assertEqual(case["annual_difference"], 6000)


class PreflightTests(unittest.TestCase):
    def test_expired_and_invalid_sessions_are_distinguished_without_exposing_sdk_messages(self):
        for code, detail in (("ExpiredToken", "have expired"),
                             ("InvalidClientTokenId", "rejected the credential set")):
            with self.subTest(code=code):
                sts = client("sts")
                with Stubber(sts) as stub:
                    stub.add_client_error("get_caller_identity", service_error_code=code,
                                          service_message="secret-value-do-not-echo", expected_params={})
                    with patch("integration.aws_preflight.create_client", return_value=sts) as create:
                        result = run_preflight(AWSSettings(bucket=BUCKET, model_id="assigned-model"), session=object())
                    stub.assert_no_pending_responses()
                self.assertFalse(result["ready"])
                self.assertEqual(result["checks"][1]["error_code"], code)
                self.assertIn(detail, result["checks"][1]["detail"])
                self.assertNotIn("secret-value", json.dumps(result))
                self.assertTrue(all(check["status"] == "skipped" for check in result["checks"][2:]))
                self.assertEqual(create.call_count, 1)

    def test_missing_credentials_block_checks_without_live_calls(self):
        with patch("integration.aws_preflight.create_session", side_effect=NoCredentialsError()):
            result = run_preflight(AWSSettings())
        self.assertFalse(result["ready"])
        self.assertEqual(result["checks"][1]["check"], "aws_identity")
        self.assertEqual(result["checks"][1]["status"], "failed")
        self.assertTrue(all(c["status"] == "skipped" for c in result["checks"][2:]))

    def test_complete_preflight_probes_real_api_shapes_without_network(self):
        sts, s3, bedrock = client("sts"), client("s3"), client("bedrock-runtime")
        settings = AWSSettings(bucket=BUCKET, model_id="assigned-model")
        with Stubber(sts) as sts_stub, Stubber(s3) as s3_stub, Stubber(bedrock) as bedrock_stub:
            sts_stub.add_response("get_caller_identity", {"Account": ACCOUNT, "Arn": f"arn:aws:iam::{ACCOUNT}:user/test", "UserId": "testing"}, {})
            stub_privacy(s3_stub)
            stub_evidence(s3_stub)
            bedrock_stub.add_response("converse", {
                "output": {"message": {"role": "assistant", "content": [{"text": "REVENUE_TWIN_OK"}]}},
                "stopReason": "end_turn", "usage": {"inputTokens": 20, "outputTokens": 5, "totalTokens": 25},
                "metrics": {"latencyMs": 10},
            }, {
                "modelId": "assigned-model",
                "messages": [{"role": "user", "content": [{"text": "Reply with REVENUE_TWIN_OK. This is a synthetic integration connectivity test."}]}],
                "inferenceConfig": {"maxTokens": 32},
            })
            clients = {"sts": sts, "s3": s3, "bedrock-runtime": bedrock}
            with patch("integration.aws_preflight.create_client", side_effect=lambda session, service: clients[service]):
                result = run_preflight(settings, session=object())
            self.assertTrue(result["ready"], result)
            sts_stub.assert_no_pending_responses()
            s3_stub.assert_no_pending_responses()
            bedrock_stub.assert_no_pending_responses()

    def test_unassigned_resources_are_reported_without_guessing_names(self):
        sts = client("sts")
        with Stubber(sts) as stub:
            stub.add_response("get_caller_identity", {"Account": ACCOUNT, "Arn": f"arn:aws:iam::{ACCOUNT}:user/test", "UserId": "testing"}, {})
            with patch("integration.aws_preflight.create_client", return_value=sts):
                result = run_preflight(AWSSettings(), session=object())
        self.assertFalse(result["ready"])
        self.assertEqual(result["checks"][1]["status"], "passed")
        self.assertEqual(result["checks"][-1]["check"], "bedrock_response")
        self.assertEqual(result["checks"][-1]["status"], "failed")


if __name__ == "__main__":
    unittest.main()
