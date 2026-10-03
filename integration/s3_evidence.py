"""Private S3 storage adapter for the existing case/evidence contract."""

import json

from botocore.exceptions import ClientError

from revenue_engine import get_case_evidence as local_case_evidence

from .aws_config import AWSSettings, create_client, create_session

PUBLIC_ACCESS_BLOCK = {
    "BlockPublicAcls": True,
    "IgnorePublicAcls": True,
    "BlockPublicPolicy": True,
    "RestrictPublicBuckets": True,
}
MAX_EVIDENCE_BYTES = 256 * 1024


def assert_private_bucket(s3, bucket: str, account_id: str):
    """Require us-east-1, all public-access blocks, disabled ACLs and no public policy."""
    request = {"Bucket": bucket, "ExpectedBucketOwner": account_id}
    location = s3.get_bucket_location(**request).get("LocationConstraint")
    if location not in {None, "us-east-1"}:
        raise ValueError("The evidence bucket must be in us-east-1")
    actual = s3.get_public_access_block(**request)["PublicAccessBlockConfiguration"]
    if any(actual.get(key) is not True for key in PUBLIC_ACCESS_BLOCK):
        raise ValueError("Enable all four S3 Block Public Access settings before uploading evidence")
    rules = s3.get_bucket_ownership_controls(**request)["OwnershipControls"]["Rules"]
    if not any(rule.get("ObjectOwnership") == "BucketOwnerEnforced" for rule in rules):
        raise ValueError("Use BucketOwnerEnforced ownership so ACLs cannot make objects public")
    try:
        policy = s3.get_bucket_policy_status(**request)
    except ClientError as error:
        if error.response["Error"]["Code"] != "NoSuchBucketPolicy":
            raise
    else:
        if policy["PolicyStatus"].get("IsPublic") is not False:
            raise ValueError("The evidence bucket has a public or unverified policy")


class S3EvidenceStore:
    def __init__(self, s3, bucket: str, account_id: str):
        self.s3 = s3
        self.bucket = bucket
        self.account_id = account_id

    def get_case_evidence(self, case_id: str) -> list[dict]:
        # The engine-owned local mapping supplies object keys, not a caller's path.
        expected_records = local_case_evidence(case_id)
        records = []
        for expected in expected_records:
            response = self.s3.get_object(
                Bucket=self.bucket, Key=expected["source_path"],
                ExpectedBucketOwner=self.account_id,
            )
            body = response["Body"]
            try:
                content = body.read(MAX_EVIDENCE_BYTES + 1)
            finally:
                body.close()
            if len(content) > MAX_EVIDENCE_BYTES:
                raise ValueError("The synthetic evidence document exceeds the demo size limit")
            record = json.loads(content)
            if not isinstance(record, dict):
                raise ValueError("S3 evidence must be a JSON object")
            for field in ["evidence_id", "case_id", "evidence_type", "title", "source_path"]:
                if record.get(field) != expected[field]:
                    raise ValueError("S3 evidence metadata does not match the engine-owned case mapping")
            if not isinstance(record.get("content"), dict) or record["content"].get("synthetic") is not True:
                raise ValueError("Only explicitly synthetic evidence is supported in this demo")
            if record["content"].get("household") != expected["content"].get("household"):
                raise ValueError("S3 evidence belongs to a different household")
            records.append(record)
        return records

    def upload_case_evidence(self, case_id: str) -> list[str]:
        assert_private_bucket(self.s3, self.bucket, self.account_id)
        records = local_case_evidence(case_id)
        # Validate the whole set before the first write.
        if any(record["content"].get("synthetic") is not True for record in records):
            raise ValueError("Only explicitly synthetic evidence can be uploaded")
        keys = []
        for record in records:
            key = record["source_path"]
            self.s3.put_object(
                Bucket=self.bucket, Key=key, ExpectedBucketOwner=self.account_id,
                Body=json.dumps(record, indent=2, ensure_ascii=False).encode("utf-8"),
                ContentType="application/json", ServerSideEncryption="AES256",
            )
            keys.append(key)
        return keys


def get_case_evidence(case_id: str) -> list[dict]:
    """AWS-owner replacement callable with the unchanged one-argument contract."""
    settings = AWSSettings.from_environment()
    if not settings.bucket:
        raise ValueError("Set REVENUE_S3_BUCKET to the private evidence bucket")
    session = create_session(settings)
    account_id = create_client(session, "sts").get_caller_identity()["Account"]
    s3 = create_client(session, "s3")
    assert_private_bucket(s3, settings.bucket, account_id)
    return S3EvidenceStore(s3, settings.bucket, account_id).get_case_evidence(case_id)
