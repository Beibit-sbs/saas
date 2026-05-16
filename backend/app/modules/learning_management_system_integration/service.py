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


def get_learning_management_system_provider_readiness_foundation(tenant_id: int) -> dict:
    """Return deterministic A-029.3 provider readiness foundation (NON_LIVE_READINESS)."""
    tenant_id = validate_tenant_id(tenant_id)

    required_capabilities = [
        "course mapping boundary",
        "user provisioning boundary",
        "grade import and export boundary",
        "attendance data boundary",
        "content publication boundary",
        "audit trail mapping",
    ]
    required_evidence = [
        "lms_provider_contract_document",
        "course_mapping_policy",
        "grade_sync_boundary_policy",
        "user_provisioning_approval",
        "content_publication_boundary_policy",
    ]

    return {
        "tenant_id": tenant_id,
        "module": MODULE_NAME,
        "uce_id": ORIGINAL_UCE_ID,
        "provider_type": "LMS",
        "provider_key": "LMS_KZ",
        "provider_label": "Kazakhstan LMS readiness profile",
        "country_profile": "KZ",
        "future_gcc_placeholder": "SA_LMS_PROVIDER",
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
        "readiness_summary": "LMS provider profile readiness only; no live LMS sync or course management.",
        "capability_matrix": {
            "required_capabilities": list(required_capabilities),
        },
        "required_evidence": list(required_evidence),
        "missing_configuration_evidence": [
            "provider connectivity approval record",
            "security sign-off for production LMS API credentials",
        ],
        "data_categories": [
            "course_references",
            "user_references",
            "grade_references",
            "attendance_references",
            "content_references",
        ],
        "pii_risk_level": "HIGH",
        "legal_basis_required": True,
        "security_review_required": True,
        "owner_role": "integration_governance_lead",
        "approval_required_before_live": True,
        "security_requirements": [
            "tenant isolation enforced",
            "no LMS API credentials in foundation mode",
            "grade and attendance data protection enforced",
            "audit trail required before live transition",
        ],
        "legal_requirements": [
            "education data governance approval",
            "data processing legal basis documentation",
        ],
        "audit_requirements": [
            "immutable readiness history",
            "human approval evidence before live enablement",
        ],
        "rollback_requirements": [
            "disable LMS mode toggle",
            "revert to non-live profile-only state",
        ],
        "audit_required": True,
        "rollback_required_before_live": True,
        "allowed_actions": [
            "VIEW_LMS_READINESS_PROFILE",
            "VALIDATE_READINESS_EVIDENCE_GAPS",
            "PREPARE_HUMAN_REVIEW_PACKET",
        ],
        "forbidden_actions": [
            "no LMS API call",
            "no course or user sync",
            "no grade import or export",
            "no attendance sync",
            "no content publish",
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


def evaluate_learning_management_system_provider_readiness_l3(tenant_id: int) -> dict:
    """Return deterministic A-029.5 L3 provider readiness logic without live integration."""
    tenant_id = validate_tenant_id(tenant_id)
    l2_profile = get_learning_management_system_provider_readiness_foundation(tenant_id)

    blocker_details = [
        {"severity": "HIGH_BLOCKER", "category": "CAPABILITY_MAPPING", "blocker": "missing course/user mapping"},
        {"severity": "HIGH_BLOCKER", "category": "CAPABILITY_MAPPING", "blocker": "missing grade import/export policy"},
        {"severity": "CRITICAL_BLOCKER", "category": "ROLLBACK_PLAN", "blocker": "missing attendance sync boundary"},
        {"severity": "HIGH_BLOCKER", "category": "OWNER_APPROVAL", "blocker": "missing content publication boundary"},
        {"severity": "CRITICAL_BLOCKER", "category": "SECURITY_REVIEW", "blocker": "no LMS sync/publish/import/export allowed in this phase"},
    ]
    warning_details = [{"severity": "MEDIUM_WARNING", "category": "MONITORING_PLAN", "warning": "optional content taxonomy evidence gaps"}]
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
        "readiness_status_reason": "Live LMS interactions remain prohibited and LMS governance evidence is incomplete.",
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
            "Complete LMS mapping, policy, and attendance/content boundary evidence.",
            "Maintain all LMS sync and publication actions blocked in non-live mode.",
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


def get_learning_management_system_provider_l4_visibility_summary(tenant_id: int) -> dict:
    """Return deterministic A-029.7 L4 read-only provider visibility summary."""
    tenant_id = validate_tenant_id(tenant_id)
    l3_profile = evaluate_learning_management_system_provider_readiness_l3(tenant_id)
    blockers = list(l3_profile.get("go_live_blockers", []))
    missing_evidence = list(l3_profile.get("missing_evidence_by_category", []))
    forbidden_actions = list(dict.fromkeys(list(l3_profile.get("forbidden_actions", [])) + [
        "no LMS roster sync",
        "no grade passback",
        "no assignment push",
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
        "visibility_summary": "LMS readiness visibility over roster/course mapping and grade passback boundary conditions.",
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
            "A-029.4-RUNTIME",
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
