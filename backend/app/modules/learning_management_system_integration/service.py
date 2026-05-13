"""Deterministic L2 integration contract for learning_management_system_integration (A-027.5)."""

from __future__ import annotations

MODULE_NAME = "learning_management_system_integration"
ORIGINAL_UCE_ID = "UCE-106"
ORIGINAL_CANDIDATE_NAME = "lms_integration"
TARGET_LEVEL = "L2"
CONTRACT_VERSION = "A-027.5"
INTEGRATION_STATUS = "CONTRACT_READY"
COUNTRY_ADAPTER_READY = True
LIVE_PROVIDER_CALLS_ALLOWED = False
DEFAULT_COUNTRY_CODE = "KZ"
DEFAULT_PROVIDER_PROFILE = "LMS_KZ"
PROVIDER_PROFILES = ["LMS_KZ"]
FUTURE_PROVIDER_PROFILE_PLACEHOLDERS = ["SA_LMS_PROVIDER"]
SUPPORTED_COUNTRY_CODES = ["KZ"]
FUTURE_SUPPORTED_COUNTRY_CODES = ["SA", "AE", "QA", "OM", "BH", "KW"]
INTEGRATION_TYPE = "learning_management_system"
DATA_EXCHANGE_DIRECTION = "bidirectional_contract_only"
ALLOWED_ACTIONS = ["DESCRIBE_LMS_CONTRACT","VALIDATE_LMS_CONFIGURATION_EVIDENCE","MARK_READY_FOR_MANUAL_PROVIDER_REVIEW"]
FORBIDDEN_ACTIONS = ["LIVE_LMS_CALL","AUTO_SYNC_GRADES","AUTO_CREATE_COURSE","HARD_CODE_LMS_PROVIDER"]
REQUIRED_CONFIGURATION_EVIDENCE = ["lms_provider_contract","course_mapping_policy","grade_sync_boundary_policy"]
EXPECTED_FAILURE_MODES = ["lms_provider_unavailable","course_mapping_missing","grade_boundary_not_approved"]

CREDENTIAL_BOUNDARY = {
    "credentials_required_for_contract": False,
    "credential_material_allowed": False,
    "credential_values_exposed": False,
    "production_credential_usage": False,
}

PROVIDER_BOUNDARY = {
    "live_provider_call_allowed": False,
    "provider_io_allowed": False,
    "provider_data_access_allowed": False,
    "provider_success_claim_allowed": False,
}

SAFETY_FLAGS = {
    "no_api_claim": True,
    "no_frontend_claim": True,
    "no_live_integration_claim": True,
    "no_provider_call": True,
    "no_credential_use": True,
    "no_secret_storage": True,
    "no_fake_success": True,
    "no_external_side_effects": True,
    "no_kpi_claim": True,
    "no_brain_claim": True,
    "no_autonomous_execution": True,
    "no_country_hardcode_in_core": True,
    "country_adapter_ready": True,
    "no_l3_claim": True,
    "no_l4_claim": True,
    "no_l5_claim": True,
    "no_l6_claim": True,
}


def validate_tenant_id(tenant_id: int) -> int:
    """Fail-closed tenant validation for deterministic contract generation."""
    if tenant_id is None:
        raise ValueError("tenant_id is required")
    if not isinstance(tenant_id, int):
        raise TypeError("tenant_id must be an int")
    if tenant_id <= 0:
        raise ValueError("tenant_id must be a positive integer")
    return tenant_id


def get_learning_management_system_integration_integration_contract(tenant_id: int, payload: dict | None = None) -> dict:
    """Return deterministic L2 country-adapter integration contract metadata."""
    tenant_id = validate_tenant_id(tenant_id)
    _ = payload

    return {
        "tenant_id": tenant_id,
        "module": MODULE_NAME,
        "original_uce_id": ORIGINAL_UCE_ID,
        "original_candidate_name": ORIGINAL_CANDIDATE_NAME,
        "maturity_level": TARGET_LEVEL,
        "expansion_layer": "university_completeness",
        "integration_type": INTEGRATION_TYPE,
        "contract_status": INTEGRATION_STATUS,
        "country_adapter_ready": COUNTRY_ADAPTER_READY,
        "provider_profiles": list(PROVIDER_PROFILES),
        "default_country_code": DEFAULT_COUNTRY_CODE,
        "default_provider_profile": DEFAULT_PROVIDER_PROFILE,
        "future_provider_profile_placeholders": list(FUTURE_PROVIDER_PROFILE_PLACEHOLDERS),
        "supported_country_codes": list(SUPPORTED_COUNTRY_CODES),
        "future_supported_country_codes": list(FUTURE_SUPPORTED_COUNTRY_CODES),
        "live_provider_call_allowed": LIVE_PROVIDER_CALLS_ALLOWED,
        "credentials_required_for_contract": CREDENTIAL_BOUNDARY["credentials_required_for_contract"],
        "credential_boundary": dict(CREDENTIAL_BOUNDARY),
        "provider_boundary": dict(PROVIDER_BOUNDARY),
        "allowed_actions": list(ALLOWED_ACTIONS),
        "forbidden_actions": list(FORBIDDEN_ACTIONS),
        "required_configuration_evidence": list(REQUIRED_CONFIGURATION_EVIDENCE),
        "expected_failure_modes": list(EXPECTED_FAILURE_MODES),
        "data_exchange_direction": DATA_EXCHANGE_DIRECTION,
        "tenant_scoped": True,
        "deterministic": True,
        "next_maturity_gap": "L3 deterministic integration readiness logic required",
        "safety_flags": dict(SAFETY_FLAGS),
    }


def classify_learning_management_system_integration_readiness(tenant_id: int, evidence: dict | None = None) -> dict:
    """Deterministic L3 readiness classifier without live provider execution."""
    tenant_id = validate_tenant_id(tenant_id)
    required_evidence = [
        "lms_provider_contract",
        "course_mapping_policy",
        "grade_sync_boundary_policy",
    ]
    evidence = evidence or {}
    present_evidence = [key for key in required_evidence if key in evidence]
    missing_evidence = [key for key in required_evidence if key not in evidence]
    present_count = len(present_evidence)

    if present_count == len(required_evidence):
        readiness_status = "READY_FOR_REVIEW"
        risk_band = "LOW"
        recommended_next_step = "READY_FOR_HUMAN_REVIEW"
    elif present_count == 2:
        readiness_status = "PARTIAL_EVIDENCE"
        risk_band = "MEDIUM"
        recommended_next_step = "REQUEST_MISSING_EVIDENCE"
    elif present_count == 1:
        readiness_status = "INCOMPLETE_EVIDENCE"
        risk_band = "HIGH"
        recommended_next_step = "REQUEST_MISSING_EVIDENCE"
    else:
        readiness_status = "BLOCKED_MISSING_EVIDENCE"
        risk_band = "BLOCKED"
        recommended_next_step = "BLOCK_UNTIL_REQUIRED_EVIDENCE_PRESENT"

    return {
        "tenant_id": tenant_id,
        "module": MODULE_NAME,
        "original_uce_id": ORIGINAL_UCE_ID,
        "maturity_level": "L3",
        "expansion_layer": "university_completeness",
        "deterministic_logic_ready": True,
        "readiness_status": readiness_status,
        "risk_band": risk_band,
        "evidence_completeness": (present_count * 100) // len(required_evidence),
        "required_evidence": required_evidence,
        "present_evidence": present_evidence,
        "missing_evidence": missing_evidence,
        "recommended_next_step": recommended_next_step,
        "human_review_required": True,
        "allowed_actions": [
            "REVIEW_READINESS_CLASSIFICATION",
            "REQUEST_MISSING_EVIDENCE",
            "PREPARE_HUMAN_REVIEW",
        ],
        "forbidden_actions": list(FORBIDDEN_ACTIONS),
        "l2_contract_preserved": True,
        "l3_boundary": "integration_readiness_only_no_live_provider_execution",
        "next_maturity_gap": "L4 operational visibility/API surface required",
        "country_adapter_ready": COUNTRY_ADAPTER_READY,
        "default_country_code": DEFAULT_COUNTRY_CODE,
        "default_provider_profile": DEFAULT_PROVIDER_PROFILE,
        "future_provider_profile_placeholders": list(FUTURE_PROVIDER_PROFILE_PLACEHOLDERS),
        "live_provider_call_allowed": LIVE_PROVIDER_CALLS_ALLOWED,
        "credentials_required_for_contract": CREDENTIAL_BOUNDARY["credentials_required_for_contract"],
        "safety_flags": {
            "no_api_claim": True,
            "no_frontend_claim": True,
            "no_provider_call": True,
            "no_live_integration_call": True,
            "no_credential_use": True,
            "no_secret_storage": True,
            "no_kpi_value_claim": True,
            "no_fake_dashboard": True,
            "no_policy_enforcement": True,
            "no_report_submission": True,
            "no_document_signature": True,
            "no_brain_execution": True,
            "no_autonomous_execution": True,
            "no_external_side_effects": True,
            "no_db_mutation": True,
            "no_l4_claim": True,
            "no_l5_claim": True,
            "no_l6_claim": True,
        },
    }
