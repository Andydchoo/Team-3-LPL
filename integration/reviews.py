"""Persist human workflow decisions in the existing private evidence bucket."""

import json
from datetime import datetime, timezone
from uuid import uuid4

from revenue_engine import get_revenue_case

from .aws_config import AWSSettings, create_client, create_session
from .s3_evidence import assert_private_bucket
from .service_boundary import IntegrationUnavailable, require_live_case

DECISIONS = {"send_for_review", "investigate_further", "dismiss"}


def validate_review_request(case_id: str, decision: str) -> None:
    require_live_case(case_id)
    if decision not in DECISIONS:
        raise IntegrationUnavailable("Choose Send for Review, Investigate Further or Dismiss.")
    get_revenue_case(case_id)


class S3ReviewStore:
    def __init__(self, s3, bucket: str, account_id: str):
        self.s3 = s3
        self.bucket = bucket
        self.account_id = account_id

    def record_review(self, case_id: str, decision: str) -> dict:
        validate_review_request(case_id, decision)
        assert_private_bucket(self.s3, self.bucket, self.account_id)
        record = {
            "review_id": f"REV-{uuid4().hex.upper()}",
            "case_id": case_id,
            "decision": decision,
            "actor": "human",
            "recorded_at": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        }
        self.s3.put_object(
            Bucket=self.bucket,
            Key=f"reviews/{case_id}/{record['review_id']}.json",
            ExpectedBucketOwner=self.account_id,
            Body=json.dumps(record, indent=2).encode("utf-8"),
            ContentType="application/json",
            ServerSideEncryption="AES256",
            IfNoneMatch="*",
        )
        # Confirmation is returned only after S3 acknowledges the entire write.
        return record


def record_review(case_id: str, decision: str) -> dict:
    validate_review_request(case_id, decision)
    settings = AWSSettings.from_environment()
    if not settings.bucket:
        raise IntegrationUnavailable("Set REVENUE_S3_BUCKET to the private evidence bucket.")
    session = create_session(settings)
    account_id = create_client(session, "sts").get_caller_identity()["Account"]
    s3 = create_client(session, "s3")
    return S3ReviewStore(s3, settings.bucket, account_id).record_review(case_id, decision)
