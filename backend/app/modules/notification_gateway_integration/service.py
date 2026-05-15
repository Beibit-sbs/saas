"""Deterministic L2 integration contract for notification_gateway_integration (A-027.5)."""

from __future__ import annotations

MODULE_NAME = "notification_gateway_integration"
ORIGINAL_UCE_ID = "UCE-028"
ORIGINAL_CANDIDATE_NAME = "sms_gateway_integration"
TARGET_LEVEL = "L2"
CONTRACT_VERSION = "A-027.5"
INTEGRATION_STATUS = "CONTRACT_READY"
COUNTRY_ADAPTER_READY = True
LIVE_PROVIDER_CALLS_ALLOWED = False
DEFAULT_COUNTRY_CODE = "KZ"
DEFAULT_PROVIDER_PROFILE = "SMS_GATEWAY_KZ"
PROVIDER_PROFILES = ["SMS_GATEWAY_KZ"]
FUTURE_PROVIDER_PROFILE_PLACEHOLDERS = ["SA_SMS_PROVIDER"]
SUPPORTED_COUNTRY_CODES = ["KZ"]
FUTURE_SUPPORTED_COUNTRY_CODES = ["SA", "AE", "QA", "OM", "BH", "KW"]
INTEGRATION_TYPE = "notification_gateway"
DATA_EXCHANGE_DIRECTION = "outbound_notification_contract_only"
ALLOWED_ACTIONS = ["DESCRIBE_NOTIFICATION_GATEWAY_CONTRACT","VALIDATE_NOTIFICATION_CONFIGURATION_EVIDENCE","MARK_READY_FOR_MANUAL_PROVIDER_REVIEW"]
FORBIDDEN_ACTIONS = ["LIVE_SMS_SEND","AUTO_SEND_SMS","STORE_PROVIDER_SECRET","HARD_CODE_SMS_PROVIDER"]
REQUIRED_CONFIGURATION_EVIDENCE = ["sms_provider_contract","consent_policy","message_template_policy"]
EXPECTED_FAILURE_MODES = ["sms_provider_unavailable","consent_missing","template_not_approved"]

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


def get_notification_gateway_integration_integration_contract(tenant_id: int, payload: dict | None = None) -> dict:
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


def get_notification_gateway_provider_readiness_foundation(tenant_id: int) -> dict:
    """Return deterministic A-029.3 provider readiness foundation (NON_LIVE_READINESS)."""
    tenant_id = validate_tenant_id(tenant_id)

    required_capabilities = [
        "SMS dispatch boundary",
        "consent mapping",
        "delivery status mapping",
        "retry and backoff boundary",
        "audit trail mapping",
    ]
    required_evidence = [
        "sms_provider_contract_document",
        "consent_and_opt_out_boundary",
        "message_template_approval_policy",
        "delivery_audit_requirements",
        "retry_policy_document",
    ]

    return {
        "tenant_id": tenant_id,
        "module": MODULE_NAME,
        "uce_id": ORIGINAL_UCE_ID,
        "provider_type": "NOTIFICATION_SMS_GATEWAY",
        "provider_key": "SMS_GATEWAY_KZ",
        "provider_label": "Kazakhstan SMS/notification gateway readiness profile",
        "country_profile": "KZ",
        "future_gcc_placeholder": "SA_SMS_PROVIDER",
        "readiness_level": "L2_PROVIDER_READINESS_FOUNDATION",
        "maturity_target": "L2",
        "integration_mode": "NON_LIVE_READINESS",
        "live_calls_enabled": False,
        "credentials_configured": False,
        "credential_reference": None,
        "external_submission_enabled": False,
        "provider_connected": False,
        "provider_status_claim": "NOT_CONNECTED_NON_LIVE_PROFILE_ONLY",
        "sync_enabled": False,
        "readiness_summary": "SMS/notification gateway provider profile readiness only; no live SMS or push dispatch.",
        "capability_matrix": {
            "required_capabilities": list(required_capabilities),
        },
        "required_evidence": list(required_evidence),
        "missing_configuration_evidence": [
            "provider connectivity approval record",
            "security sign-off for production SMS gateway credentials",
        ],
        "data_categories": [
            "phone_references",
            "notification_templates",
            "delivery_references",
            "consent_flags",
        ],
        "pii_risk_level": "MEDIUM",
        "legal_basis_required": True,
        "security_review_required": True,
        "owner_role": "integration_governance_lead",
        "approval_required_before_live": True,
        "security_requirements": [
            "tenant isolation enforced",
            "no SMS gateway credentials in foundation mode",
            "audit trail required before live transition",
        ],
        "legal_requirements": [
            "consent and opt-out compliance documentation",
            "data processing legal basis documentation",
        ],
        "audit_requirements": [
            "immutable readiness history",
            "human approval evidence before live enablement",
        ],
        "rollback_requirements": [
            "disable notification gateway mode toggle",
            "revert to non-live profile-only state",
        ],
        "audit_required": True,
        "rollback_required_before_live": True,
        "allowed_actions": [
            "VIEW_NOTIFICATION_GATEWAY_READINESS_PROFILE",
            "VALIDATE_READINESS_EVIDENCE_GAPS",
            "PREPARE_HUMAN_REVIEW_PACKET",
        ],
        "forbidden_actions": [
            "no SMS gateway call",
            "no push dispatch",
            "no WhatsApp or Telegram send",
            "no delivery status claim",
            "no credential validation",
            "no external submission",
        ],
        "tenant_scoped": True,
        "read_only": True,
        "no_mutation": True,
        "no_provider_call": True,
        "no_credentials": True,
        "no_external_submission": True,
        "no_fake_integration_status": True,
        "no_sync_claim": True,
        "no_l4_claim": True,
        "no_l5_claim": True,
        "no_l6_claim": True,
    }
