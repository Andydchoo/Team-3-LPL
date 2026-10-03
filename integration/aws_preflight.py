"""First milestone: real AWS identity, private S3 evidence and one Bedrock response."""

import argparse
import json

from .aws_config import AWSSettings, create_client, create_session, safe_error_code, safe_error_message
from .s3_evidence import S3EvidenceStore, assert_private_bucket


def failed_check(name: str, error: Exception) -> dict:
    result = {"check": name, "status": "failed", "detail": safe_error_message(error)}
    code = safe_error_code(error)
    if code:
        result["error_code"] = code
    return result


def run_preflight(settings: AWSSettings, session=None) -> dict:
    checks = [{"check": "region", "status": "passed", "detail": settings.region}]

    def report():
        return {"ready": all(check["status"] == "passed" for check in checks), "checks": checks}

    try:
        session = session or create_session(settings)
        identity = create_client(session, "sts").get_caller_identity()
        account_id = identity["Account"]
        checks.append({"check": "aws_identity", "status": "passed", "detail": f"Account {account_id}"})
    except Exception as error:
        checks.append(failed_check("aws_identity", error))
        checks.extend({"check": name, "status": "skipped", "detail": "Valid AWS access is required"}
                      for name in ["private_s3", "s3_evidence_read", "bedrock_response"])
        return report()

    if not settings.bucket:
        checks.append({"check": "private_s3", "status": "failed", "detail": "Set REVENUE_S3_BUCKET or pass --bucket"})
        checks.append({"check": "s3_evidence_read", "status": "skipped", "detail": "An assigned private bucket is required"})
    else:
        try:
            s3 = create_client(session, "s3")
            assert_private_bucket(s3, settings.bucket, account_id)
            checks.append({"check": "private_s3", "status": "passed", "detail": settings.bucket})
        except Exception as error:
            checks.append(failed_check("private_s3", error))
            checks.append({"check": "s3_evidence_read", "status": "skipped", "detail": "Verify bucket privacy first"})
        else:
            try:
                records = S3EvidenceStore(s3, settings.bucket, account_id).get_case_evidence("CASE-001")
                checks.append({"check": "s3_evidence_read", "status": "passed", "detail": f"Read {len(records)} Anderson documents"})
            except Exception as error:
                checks.append(failed_check("s3_evidence_read", error))

    if not settings.model_id:
        checks.append({"check": "bedrock_response", "status": "failed", "detail": "Set BEDROCK_MODEL_ID or pass --model-id"})
    else:
        try:
            response = create_client(session, "bedrock-runtime").converse(
                modelId=settings.model_id,
                messages=[{"role": "user", "content": [{"text": "Reply with REVENUE_TWIN_OK. This is a synthetic integration connectivity test."}]}],
                inferenceConfig={"maxTokens": 32},
            )
            blocks = response.get("output", {}).get("message", {}).get("content", [])
            if not any(isinstance(block.get("text"), str) and block["text"].strip() for block in blocks):
                raise ValueError("Bedrock returned no text response; check model support for Converse")
            checks.append({"check": "bedrock_response", "status": "passed", "detail": "Selected model returned text through Converse"})
        except Exception as error:
            checks.append(failed_check("bedrock_response", error))
    return report()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile")
    parser.add_argument("--bucket")
    parser.add_argument("--model-id")
    args = parser.parse_args()
    try:
        settings = AWSSettings.from_environment(profile=args.profile, bucket=args.bucket, model_id=args.model_id)
        result = run_preflight(settings)
    except Exception as error:
        result = {"ready": False, "checks": [failed_check("configuration", error)]}
    print(json.dumps(result, indent=2))
    return 0 if result["ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
