"""
outbound_exchange_management service.py — L2 Foundation Contract
"""

MODULE_NAME = "outbound_exchange_management"
UCE_ID = "UCE-087"
TARGET_LEVEL = "L2"
CONTRACT_VERSION = "A-027.4"
FOUNDATION_STATUS = "FOUNDATION_READY"

LIFECYCLE_STATUSES = ["APPLICATION_SUBMITTED", "ELIGIBILITY_REVIEW", "PARTNER_REVIEW", "APPROVED_MANUAL", "CLOSED"]
ALLOWED_ACTIONS = ["REVIEW_OUTBOUND_EXCHANGE", "REQUEST_ELIGIBILITY_EVIDENCE", "MARK_READY_FOR_PARTNER_REVIEW"]
FORBIDDEN_ACTIONS = ["AUTO_APPROVE_MOBILITY", "AUTO_SUBMIT_TO_PARTNER", "AUTO_CHANGE_ACADEMIC_RECORD"]
REQUIRED_EVIDENCE = ["application_record", "eligibility_evidence", "partner_review"]

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

def get_outbound_exchange_management_foundation_contract(tenant_id, payload=None):
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
            "no_automatic_exchange_approval": True,
            "no_automatic_partner_submission": True,
            "no_automatic_academic_record_changes": True,
        },
        "safety_flags": SAFETY_FLAGS,
    }


# --- L3 Deterministic Readiness Classifier (A-027.9) ---

A0279_L3_READY = True


def classify_outbound_exchange_management_readiness(tenant_id: int, evidence: dict | None = None) -> dict:
    """Deterministic L3 readiness classifier. No decision execution, no autonomy, no provider calls."""
    validate_tenant_id(tenant_id)
    required_evidence = [
        "student_application_present",
        "home_program_approval_required",
        "partner_requirements_available",
        "learning_agreement_draft_present",
        "mobility_risk_review_required",
    ]
    evidence = evidence or {}
    present_evidence = [key for key in required_evidence if key in evidence]
    missing_evidence = [key for key in required_evidence if key not in evidence]
    present_count = len(present_evidence)

    if present_count == len(required_evidence):
        readiness_status = "READY_FOR_REVIEW"
        risk_band = "LOW"
        recommended_next_step = "READY_FOR_HUMAN_REVIEW"
    elif present_count >= 3:
        readiness_status = "PARTIAL_EVIDENCE"
        risk_band = "MEDIUM"
        recommended_next_step = "REQUEST_MISSING_EVIDENCE"
    elif present_count >= 1:
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
        "uce_id": UCE_ID,
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
            "OUTBOUND_EXCHANGE_READINESS_CLASSIFICATION",
            "MISSING_EVIDENCE_IDENTIFICATION",
            "HUMAN_REVIEW_PREPARATION",
        ],
        "forbidden_actions": [
            "AUTO_APPROVE_MOBILITY",
            "AUTO_SEND_NOMINATION",
            "AUTO_COMMIT_STUDENT_TO_PARTNER",
            "MUTATE_STUDENT_RECORD",
            "PROVIDER_CALL",
        ],
        "l2_contract_preserved": True,
        "tenant_scoped": True,
        "l3_boundary": "module_readiness_only_no_decision_execution_or_automation",
        "next_maturity_gap": "L4 operational visibility/API surface required",
        "safety_flags": {
            "no_api_claim": True,
            "no_frontend_claim": True,
            "no_provider_call": True,
            "no_credential_use": True,
            "no_kpi_value_claim": True,
            "no_brain_execution": True,
            "no_autonomous_execution": True,
            "no_external_side_effects": True,
            "no_db_mutation": True,
            "no_decision_execution": True,
            "human_review_required": True,
            "no_l4_claim": True,
            "no_l5_claim": True,
            "no_l6_claim": True,
            "tenant_fail_closed": True,
            "l2_contract_preserved": True,
        },
    }
