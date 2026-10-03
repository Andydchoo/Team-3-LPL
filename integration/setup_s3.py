"""Explicitly create a private demo bucket, or upload to an existing private one."""

import argparse
import json

from botocore.exceptions import ClientError

from .aws_config import AWSSettings, create_client, create_session, safe_error_message
from .s3_evidence import PUBLIC_ACCESS_BLOCK, S3EvidenceStore


def create_private_bucket(s3, bucket: str, account_id: str):
    try:
        s3.head_bucket(Bucket=bucket, ExpectedBucketOwner=account_id)
    except ClientError as error:
        if error.response["Error"]["Code"] not in {"404", "NoSuchBucket", "NotFound"}:
            raise
    else:
        raise ValueError("The bucket already exists. Omit --create to use a verified private bucket")
    # us-east-1 must omit a LocationConstraint. Never repeat CreateBucket on an
    # existing bucket: in this region that can reset ACLs.
    s3.create_bucket(Bucket=bucket, ObjectOwnership="BucketOwnerEnforced")
    request = {"Bucket": bucket, "ExpectedBucketOwner": account_id}
    s3.put_public_access_block(**request, PublicAccessBlockConfiguration=PUBLIC_ACCESS_BLOCK)
    s3.put_bucket_encryption(**request, ServerSideEncryptionConfiguration={
        "Rules": [{"ApplyServerSideEncryptionByDefault": {"SSEAlgorithm": "AES256"}}],
    })


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile")
    parser.add_argument("--bucket", required=True)
    parser.add_argument("--create", action="store_true", help="Create a new bucket; never alter an existing bucket's privacy configuration")
    args = parser.parse_args()
    try:
        settings = AWSSettings.from_environment(profile=args.profile, bucket=args.bucket)
        session = create_session(settings)
        account_id = create_client(session, "sts").get_caller_identity()["Account"]
        s3 = create_client(session, "s3")
        if args.create:
            create_private_bucket(s3, settings.bucket, account_id)
        store = S3EvidenceStore(s3, settings.bucket, account_id)
        uploaded = store.upload_case_evidence("CASE-001")
        fetched = store.get_case_evidence("CASE-001")
        print(json.dumps({"bucket": settings.bucket, "uploaded": uploaded, "read_back": len(fetched)}, indent=2))
        return 0
    except Exception as error:
        print(json.dumps({"ready": False, "error": safe_error_message(error)}, indent=2))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
