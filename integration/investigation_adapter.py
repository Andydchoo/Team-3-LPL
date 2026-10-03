"""Validate the AI owner's result at the application integration boundary.

This module does not implement an agent, prompt or model tool loop. The AI
owner supplies investigation.investigate_case and uses integration.case_tools.
"""

import importlib
import json
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

from .case_tools import get_case_evidence
from .service_boundary import (
    IntegrationUnavailable, integration_error_message, require_live_case,
)

SCHEMA_PATH = Path(__file__).resolve().parent.parent / "contracts" / "revenuetwin.schema.json"


def validate_investigation(result, case_id: str, evidence: list[dict]) -> dict:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    investigation_schema = {
        "$schema": schema["$schema"], "$defs": schema["$defs"],
        "$ref": "#/$defs/Investigation",
    }
    validator = Draft202012Validator(investigation_schema, format_checker=FormatChecker())
    if next(validator.iter_errors(result), None) is not None:
        raise IntegrationUnavailable("The investigation response did not match the shared contract. Retry the investigation.")
    if result["case_id"] != case_id:
        raise IntegrationUnavailable("The investigation returned a different case. Retry the investigation.")
    evidence_ids = {item["evidence_id"] for item in evidence}
    used_ids = [item["evidence_id"] for item in result["evidence_used"]]
    if len(set(used_ids)) != len(used_ids) or any(eid not in evidence_ids for eid in used_ids):
        raise IntegrationUnavailable("The investigation cited unverified evidence. Retry the investigation.")
    if result["investigation_status"] == "supported_explanation" and not used_ids:
        raise IntegrationUnavailable("The investigation claimed support without citing evidence. Retry the investigation.")
    return result


def investigation_error(case_id: str, message: str) -> dict:
    return {
        "case_id": case_id,
        "investigation_status": "investigation_error",
        "likely_cause": None,
        "summary": message,
        "evidence_strength": "low",
        "evidence_used": [],
        "uncertainties": ["A live investigation could not be completed."],
        "recommended_action": "Keep the finding in human review and retry the investigation.",
        "requires_human_review": True,
    }


def load_agent():
    try:
        module = importlib.import_module("investigation")
    except ModuleNotFoundError as error:
        if error.name != "investigation":
            raise
        raise IntegrationUnavailable("The AI owner's investigation package is not integrated yet.") from None
    agent = getattr(module, "investigate_case", None)
    if not callable(agent):
        raise IntegrationUnavailable("The AI owner's investigate_case function is not integrated yet.")
    return agent


def investigate_case(case_id: str) -> dict:
    require_live_case(case_id)
    try:
        agent = load_agent()
        evidence = get_case_evidence(case_id)
        result = validate_investigation(agent(case_id), case_id, evidence)
        if result["investigation_status"] == "investigation_error":
            return investigation_error(case_id, "The AI service could not complete the investigation. Retry the investigation.")
        return result
    except Exception as error:
        return investigation_error(case_id, integration_error_message(error))
