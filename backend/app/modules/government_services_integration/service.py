"""Deterministic L2 integration contract for government_services_integration (A-027.5)."""

from __future__ import annotations

MODULE_NAME = "government_services_integration"
ORIGINAL_UCE_ID = "UCE-030"
ORIGINAL_CANDIDATE_NAME = "egov_integration"
TARGET_LEVEL = "L2"
CONTRACT_VERSION = "A-027.5"
INTEGRATION_STATUS = "CONTRACT_READY"
COUNTRY_ADAPTER_READY = True
LIVE_PROVIDER_CALLS_ALLOWED = False
DEFAULT_COUNTRY_CODE = "KZ"
DEFAULT_PROVIDER_PROFILE = "EGOV_KZ"
PROVIDER_PROFILES = ["EGOV_KZ"]
FUTURE_PROVIDER_PROFILE_PLACEHOLDERS = ["SA_GOVERNMENT_SERVICES_PROVIDER"]
SUPPORTED_COUNTRY_CODES = ["KZ"]
FUTURE_SUPPORTED_COUNTRY_CODES = ["SA", "AE", "QA", "OM", "BH", "KW"]
INTEGRATION_TYPE = "government_services"
DATA_EXCHANGE_DIRECTION = "external_verification_contract_only"
ALLOWED_ACTIONS = ["DESCRIBE_GOVERNMENT_SERVICES_CONTRACT","VALIDATE_GOVERNMENT_CONFIGURATION_EVIDENCE","MARK_READY_FOR_MANUAL_PROVIDER_REVIEW"]
FORBIDDEN_ACTIONS = ["LIVE_EGOV_CALL","AUTO_SUBMIT_GOVERNMENT_FORM","AUTO_VERIFY_CITIZEN_DATA","HARD_CODE_EGOV_AS_CORE"]
REQUIRED_CONFIGURATION_EVIDENCE = ["government_provider_contract","consent_policy","verification_scope_policy"]
EXPECTED_FAILURE_MODES = ["government_provider_unavailable","consent_missing","verification_scope_not_approved"]

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


def get_government_services_integration_integration_contract(tenant_id: int, payload: dict | None = None) -> dict:
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


def get_government_services_provider_readiness_foundation(tenant_id: int) -> dict:
    """Return deterministic A-029.2 provider readiness foundation (NON_LIVE_READINESS)."""
    tenant_id = validate_tenant_id(tenant_id)

    required_capabilities = [
        "citizen identity reference boundary",
        "document request mapping",
        "status polling contract",
        "consent requirement mapping",
        "legal basis mapping",
    ]
    optional_capabilities = [
        "document taxonomy normalization",
        "government channel fallback mapping",
    ]
    required_evidence = [
        "government_provider_contract",
        "consent_policy",
        "verification_scope_policy",
        "legal_basis_register",
        "human_review_approval_flow",
    ]

    return {
        "tenant_id": tenant_id,
        "module": MODULE_NAME,
        "uce_id": ORIGINAL_UCE_ID,
        "provider_type": "GOVERNMENT_SERVICES",
        "provider_key": "EGOV_KZ",
        "provider_label": "eGov Kazakhstan government services readiness profile",
        "country_profile": "KZ",
        "future_gcc_placeholder": "SA_GOVERNMENT_SERVICES_PROVIDER",
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
        "readiness_summary": "Government services provider profile readiness only; no live government interactions.",
        "capability_matrix": {
            "required_capabilities": list(required_capabilities),
            "optional_capabilities": list(optional_capabilities),
        },
        "required_evidence": list(required_evidence),
        "missing_configuration_evidence": [
            "government connectivity authorization",
            "regulatory submission approval",
        ],
        "data_categories": [
            "citizen_identity_references",
            "public_service_requests",
            "document_status_references",
        ],
        "pii_risk_level": "HIGH",
        "legal_basis_required": True,
        "security_review_required": True,
        "owner_role": "public_services_integration_governance_lead",
        "approval_required_before_live": True,
        "security_requirements": [
            "tenant isolation and data minimization",
            "no credential handling in foundation mode",
            "no external channel access before approval",
        ],
        "legal_requirements": [
            "regulatory legal basis approval",
            "consent handling policy validation",
        ],
        "audit_requirements": [
            "immutable readiness evidence trail",
            "approval traceability for government boundaries",
        ],
        "rollback_requirements": [
            "disable external interaction capability toggle",
            "restore profile-only non-live state",
        ],
        "audit_required": True,
        "rollback_required_before_live": True,
        "allowed_actions": [
            "VIEW_PROVIDER_READINESS_PROFILE",
            "VALIDATE_READINESS_EVIDENCE_GAPS",
            "PREPARE_HUMAN_REVIEW_PACKET",
        ],
        "forbidden_actions": [
            "no eGov calls",
            "no citizen/student data query",
            "no document status claim",
            "no external submission",
            "no credential validation",
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


def evaluate_government_services_provider_readiness_l3(tenant_id: int) -> dict:
    """Return deterministic A-029.5 L3 provider readiness logic without live integration."""
    tenant_id = validate_tenant_id(tenant_id)
    l2_profile = get_government_services_provider_readiness_foundation(tenant_id)

    blocker_details = [
        {"severity": "CRITICAL_BLOCKER", "category": "LEGAL_BASIS", "blocker": "missing eGov legal basis"},
        {"severity": "HIGH_BLOCKER", "category": "DATA_PROTECTION", "blocker": "missing consent/data access boundary"},
        {"severity": "HIGH_BLOCKER", "category": "CAPABILITY_MAPPING", "blocker": "missing public service request mapping"},
        {"severity": "CRITICAL_BLOCKER", "category": "EXTERNAL_CONTRACT", "blocker": "missing external approval"},
        {"severity": "CRITICAL_BLOCKER", "category": "SECURITY_REVIEW", "blocker": "no eGov query/submission allowed in this phase"},
    ]
    warning_details = [{"severity": "MEDIUM_WARNING", "category": "MONITORING_PLAN", "warning": "optional SLA monitoring gaps"}]
    missing_evidence_by_category = sorted({entry["category"] for entry in blocker_details})

    return {
        "tenant_id": tenant_id,
        "module": MODULE_NAME,
        "uce_id": ORIGINAL_UCE_ID,
        "provider_type": l2_profile["provider_type"],
        "provider_key": l2_profile["provider_key"],
        "readiness_level": "L3_PROVIDER_READINESS_DETERMINISTIC_LOGIC",
        "maturity_target": "L3",
        "integration_mode": "NON_LIVE_READINESS",
        "provider_profile_level": "L2_PROVIDER_READINESS_FOUNDATION",
        "deterministic_logic_version": "A-029.5",
        "readiness_status": "BLOCKED_LIVE_CALLS_NOT_ALLOWED",
        "readiness_status_reason": "Live eGov interactions are prohibited in this phase and governance evidence is incomplete.",
        "blocker_count": len(blocker_details),
        "warning_count": len(warning_details),
        "missing_evidence_count": len(missing_evidence_by_category),
        "security_completeness_status": "INCOMPLETE",
        "legal_completeness_status": "INCOMPLETE",
        "audit_completeness_status": "INCOMPLETE",
        "rollback_completeness_status": "INCOMPLETE",
        "capability_coverage_status": "PARTIAL",
        "go_live_blockers": [entry["blocker"] for entry in blocker_details],
        "blocker_details": blocker_details,
        "warning_details": warning_details,
        "missing_evidence_by_category": missing_evidence_by_category,
        "readiness_recommendations": [
            "Complete legal, consent, and request mapping evidence.",
            "Keep all external interactions blocked until future live-approved lane.",
        ],
        "allowed_next_steps": [
            "RUN_GOVERNANCE_REVIEW",
            "COLLECT_MISSING_EVIDENCE",
            "PREPARE_MANUAL_APPROVAL_PACKET",
        ],
        "forbidden_actions": list(l2_profile.get("forbidden_actions", [])),
        "tenant_scoped": True,
        "read_only": True,
        "no_mutation": True,
        "no_provider_call": True,
        "no_credentials": True,
        "no_external_submission": True,
        "no_provider_connected_claim": True,
        "no_sync_claim": True,
        "no_l4_claim": True,
        "no_l5_claim": True,
        "no_l6_claim": True,
    }


def get_government_services_provider_l4_visibility_summary(tenant_id: int) -> dict:
    """Return deterministic A-029.7 L4 read-only provider visibility summary."""
    tenant_id = validate_tenant_id(tenant_id)
    l3_profile = evaluate_government_services_provider_readiness_l3(tenant_id)
    blockers = list(l3_profile.get("go_live_blockers", []))
    missing_evidence = list(l3_profile.get("missing_evidence_by_category", []))
    forbidden_actions = list(dict.fromkeys(list(l3_profile.get("forbidden_actions", [])) + [
        "no eGov query/submission",
        "no public service request execution",
    ]))

    return {
        "tenant_id": tenant_id,
        "module": MODULE_NAME,
        "uce_id": l3_profile["uce_id"],
        "provider_type": l3_profile["provider_type"],
        "provider_key": l3_profile["provider_key"],
        "readiness_level": "L4_PROVIDER_READONLY_VISIBILITY",
        "maturity_target": "L4",
        "visibility_source_level": "L3_PROVIDER_READINESS_DETERMINISTIC_LOGIC",
        "integration_mode": "NON_LIVE_READINESS",
        "provider_profile_level": "L2_PROVIDER_READINESS_FOUNDATION",
        "deterministic_logic_version": "A-029.5",
        "visibility_version": "A-029.7",
        "provider_connected": False,
        "live_calls_enabled": False,
        "credentials_configured": False,
        "external_submission_enabled": False,
        "sync_enabled": False,
        "readiness_status": l3_profile["readiness_status"],
        "readiness_status_reason": l3_profile["readiness_status_reason"],
        "blocker_count": l3_profile["blocker_count"],
        "warning_count": l3_profile["warning_count"],
        "missing_evidence_count": l3_profile["missing_evidence_count"],
        "visibility_summary": "Government services readiness visibility over consent/legal basis and document request/status boundaries.",
        "go_live_blocker_summary": "; ".join(blockers) if blockers else "No go-live blockers recorded.",
        "missing_evidence_summary": ", ".join(missing_evidence) if missing_evidence else "No missing evidence categories recorded.",
        "security_legal_audit_rollback_summary": (
            f"security={l3_profile.get('security_completeness_status')}; "
            f"legal={l3_profile.get('legal_completeness_status')}; "
            f"audit={l3_profile.get('audit_completeness_status')}; "
            f"rollback={l3_profile.get('rollback_completeness_status')}"
        ),
        "allowed_next_steps": list(l3_profile.get("allowed_next_steps", [])),
        "forbidden_actions": forbidden_actions,
        "evidence_refs": [
            "A-029.2-RUNTIME",
            "A-029.5-RUNTIME",
            "A-029.7-RUNTIME",
        ],
        "go_live_blockers": blockers,
        "blocker_details": list(l3_profile.get("blocker_details", [])),
        "warning_details": list(l3_profile.get("warning_details", [])),
        "missing_evidence_by_category": missing_evidence,
        "tenant_scoped": True,
        "read_only": True,
        "no_mutation": True,
        "no_provider_call": True,
        "no_credentials": True,
        "no_external_submission": True,
        "no_provider_connected_claim": True,
        "no_sync_claim": True,
        "no_l5_claim": True,
        "no_l6_claim": True,
    }
