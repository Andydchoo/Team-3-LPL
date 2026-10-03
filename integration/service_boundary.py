"""Explicit service selection and messages safe to show in the demo."""

import os


class IntegrationUnavailable(RuntimeError):
    """A controlled message for the application's integration boundary."""


def backend_mode() -> str:
    mode = os.environ.get("REVENUE_BACKEND", "local").strip().lower()
    if mode not in {"local", "aws"}:
        raise IntegrationUnavailable("Set REVENUE_BACKEND to local or aws.")
    return mode


def require_live_case(case_id: str) -> None:
    if case_id != "CASE-001":
        raise IntegrationUnavailable(
            "AWS integration currently supports Anderson (CASE-001). "
            "Select Anderson or switch to the local demo for the other cases."
        )


def integration_error_message(error: Exception) -> str:
    if isinstance(error, IntegrationUnavailable):
        return str(error)
    # External exceptions can contain SDK request details or model output.
    # Only the SDK's known error types go through the sanitized AWS mapper.
    try:
        from botocore.exceptions import BotoCoreError, ClientError
        from .aws_config import safe_error_message
    except ImportError:
        return "Install requirements-aws.txt before using AWS mode."
    if isinstance(error, (BotoCoreError, ClientError)):
        return safe_error_message(error)
    return "The service could not complete the request. Check configuration and retry."
