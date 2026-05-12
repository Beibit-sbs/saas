"""
academic_integrity_case_management service.py — L2 Foundation Contract
"""

MODULE_NAME = "academic_integrity_case_management"
UCE_ID = "UCE-078"
TARGET_LEVEL = "L2"
CONTRACT_VERSION = "A-027.4"
FOUNDATION_STATUS = "FOUNDATION_READY"

LIFECYCLE_STATUSES = ["CASE_OPENED", "EVIDENCE_COLLECTION", "COMMITTEE_REVIEW", "DECISION_PENDING", "CLOSED"]
ALLOWED_ACTIONS = ["REVIEW_INTEGRITY_CASE", "REQUEST_EVIDENCE", "MARK_READY_FOR_HUMAN_DECISION"]
FORBIDDEN_ACTIONS = ["AUTO_ACCUSATION", "AUTO_PENALTY", "AUTO_CHANGE_GRADE"]
REQUIRED_EVIDENCE = ["case_record", "evidence_bundle", "committee_record"]

SAFETY_FLAGS = {
    "no_api_claim": True, "no_frontend_claim": True, "no_live_integration_claim": True,
    "no_provider_call": True, "no_kpi_claim": True, "no_brain_claim": True,
    "no_autonomous_execution": True, "no_external_side_effects": True,
    "no_l3_claim": True, "no_l4_claim": True, "no_l5_claim": True, "no_l6_claim": True,
}

def validate_tenant_id(tenant_id):
    if tenant_id is None:
        raise ValueError("tenant_id cannot be None")
    if not isinstance(tenant_id, int):
        raise TypeError(f"tenant_id must be int, got {type(tenant_id)}")
    if tenant_id <= 0:
        raise ValueError(f"tenant_id must be positive, got {tenant_id}")
    return tenant_id

def get_academic_integrity_case_management_foundation_contract(tenant_id, payload=None):
    tenant_id = validate_tenant_id(tenant_id)
    return {
        "tenant_id": tenant_id,
        "module": MODULE_NAME,
        "uce_id": UCE_ID,
        "maturity_level": TARGET_LEVEL,
        "expansion_layer": "university_completeness",
        "contract_status": "FOUNDATION_READY",
        "service_contract_ready": True,
        "tenant_scoped": True,
        "deterministic": True,
        "lifecycle_statuses": LIFECYCLE_STATUSES,
        "allowed_actions": ALLOWED_ACTIONS,
        "forbidden_actions": FORBIDDEN_ACTIONS,
        "required_evidence": REQUIRED_EVIDENCE,
        "next_maturity_gap": "L3 deterministic logic required",
        "sensitive_boundary": {
            "no_automatic_academic_misconduct_decision": True,
            "no_penalty_automation": True,
            "no_automatic_grade_change": True,
        },
        "safety_flags": SAFETY_FLAGS,
    }
