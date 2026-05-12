"""Deterministic L2 integration contract for hr_payroll_integration (A-027.5)."""

from __future__ import annotations

MODULE_NAME = "hr_payroll_integration"
ORIGINAL_UCE_ID = "UCE-113"
ORIGINAL_CANDIDATE_NAME = "hr_payroll_system_integration"
TARGET_LEVEL = "L2"
CONTRACT_VERSION = "A-027.5"
INTEGRATION_STATUS = "CONTRACT_READY"
COUNTRY_ADAPTER_READY = True
LIVE_PROVIDER_CALLS_ALLOWED = False
DEFAULT_COUNTRY_CODE = "KZ"
DEFAULT_PROVIDER_PROFILE = "HR_PAYROLL_KZ"
PROVIDER_PROFILES = ["HR_PAYROLL_KZ"]
FUTURE_PROVIDER_PROFILE_PLACEHOLDERS = ["SA_HR_PAYROLL_PROVIDER"]
SUPPORTED_COUNTRY_CODES = ["KZ"]
FUTURE_SUPPORTED_COUNTRY_CODES = ["SA", "AE", "QA", "OM", "BH", "KW"]
INTEGRATION_TYPE = "hr_payroll"
DATA_EXCHANGE_DIRECTION = "hr_payroll_contract_only"
ALLOWED_ACTIONS = ["DESCRIBE_HR_PAYROLL_CONTRACT","VALIDATE_HR_PAYROLL_CONFIGURATION_EVIDENCE","MARK_READY_FOR_MANUAL_PROVIDER_REVIEW"]
FORBIDDEN_ACTIONS = ["LIVE_PAYROLL_CALL","AUTO_SYNC_SALARY","AUTO_CHANGE_EMPLOYEE_PAYROLL","HARD_CODE_PAYROLL_PROVIDER"]
REQUIRED_CONFIGURATION_EVIDENCE = ["payroll_provider_contract","employee_mapping_policy","salary_boundary_policy"]
EXPECTED_FAILURE_MODES = ["payroll_provider_unavailable","employee_mapping_missing","salary_boundary_not_approved"]

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


def get_hr_payroll_integration_integration_contract(tenant_id: int, payload: dict | None = None) -> dict:
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
