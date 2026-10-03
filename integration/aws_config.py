"""AWS configuration and bounded clients without embedded credentials."""

import os
import re
from dataclasses import dataclass

import boto3
from botocore.config import Config
from botocore.exceptions import (
    BotoCoreError, ClientError, NoCredentialsError, PartialCredentialsError,
    ProfileNotFound,
)

REGION = "us-east-1"


@dataclass(frozen=True)
class AWSSettings:
    profile: str | None = None
    bucket: str | None = None
    model_id: str | None = None
    region: str = REGION

    def __post_init__(self):
        if self.region != REGION:
            raise ValueError("The hackathon integration requires us-east-1")
        if self.bucket and not re.fullmatch(r"[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]", self.bucket):
            raise ValueError("Use a valid S3 bucket name, not a URL or ARN")

    @classmethod
    def from_environment(cls, *, profile=None, bucket=None, model_id=None):
        for variable in ["AWS_REGION", "AWS_DEFAULT_REGION"]:
            if os.environ.get(variable, REGION) != REGION:
                raise ValueError(f"Set {variable} to {REGION}")
        return cls(
            profile=profile or os.environ.get("AWS_PROFILE") or None,
            bucket=bucket or os.environ.get("REVENUE_S3_BUCKET") or None,
            model_id=model_id or os.environ.get("BEDROCK_MODEL_ID") or None,
        )


def create_session(settings: AWSSettings):
    return boto3.Session(profile_name=settings.profile, region_name=settings.region)


def create_client(session, service: str):
    return session.client(service, region_name=REGION, config=Config(
        connect_timeout=5,
        read_timeout=30,
        retries={"mode": "standard", "total_max_attempts": 2},
    ))


def safe_error_code(error: Exception) -> str | None:
    """Expose only the SDK's short error identifier, never its raw message."""
    if not isinstance(error, ClientError):
        return None
    code = error.response.get("Error", {}).get("Code")
    if isinstance(code, str) and re.fullmatch(r"[A-Za-z0-9_.-]{1,64}", code):
        return code
    return None


def safe_error_message(error: Exception) -> str:
    """UI-safe guidance; never include raw SDK messages or credential values."""
    if isinstance(error, (NoCredentialsError, PartialCredentialsError, ProfileNotFound)):
        return "Configure a valid AWS profile with all three temporary credential values."
    if isinstance(error, ClientError):
        code = error.response.get("Error", {}).get("Code", "AWSServiceError")
        if code in {"ExpiredToken", "ExpiredTokenException"}:
            return "AWS temporary credentials have expired. Get a fresh set of all three values from the event portal and rerun credential setup."
        if code in {"InvalidClientTokenId", "UnrecognizedClientException"}:
            return "AWS rejected the credential set. Re-enter the access key, secret key and session token from the same fresh event session."
        if code in {"AccessDenied", "AccessDeniedException", "403"}:
            return "AWS denied this operation. Check the event role permissions, bucket ownership and model access."
        if code in {"ThrottlingException", "Throttling", "TooManyRequestsException"}:
            return "AWS is throttling requests. Wait at least one second before retrying."
        if code in {"NoSuchKey", "NoSuchBucket", "404"}:
            return "The configured bucket or evidence object was not found. Verify the resource name and upload."
        if code in {"ValidationException", "ResourceNotFoundException"}:
            return "Check the assigned Bedrock model or inference profile ID and its availability in us-east-1."
        return "AWS rejected the request. Check account permissions and resource configuration."
    if isinstance(error, ValueError):
        return str(error)
    if isinstance(error, BotoCoreError):
        return "AWS could not be reached or authenticated. Check connectivity and session credentials."
    return "The integration check failed. Check local configuration and synthetic evidence files."
