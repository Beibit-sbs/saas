"""Partnership_Registry L2 Foundation Service Contract (UCE-022)."""

from . import MODULE_NAME, UCE_ID, TARGET_LEVEL, CONTRACT_VERSION, FOUNDATION_STATUS


def validate_tenant_id(tenant_id: int) -> int:
    """Fail-closed tenant validation."""
    if not tenant_id or tenant_id <= 0:
        raise ValueError(f"invalid_tenant_id: {tenant_id}")
    return tenant_id


def get_partnership_registry_foundation_contract(tenant_id: int, payload: dict | None = None) -> dict:
    """L2 foundation contract for partnership_registry. No provider calls, no autonomy, deterministic only."""
    validate_tenant_id(tenant_id)
    
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
        
        "lifecycle_statuses": [
            "PROPOSED",
            "DUE_DILIGENCE",
            "APPROVED_MANUAL",
            "ACTIVE",
            "SUSPENDED",
            "CLOSED"
        ],
        
        "allowed_actions": [
            "REVIEW_PARTNERSHIP",
            "REQUEST_DUE_DILIGENCE_EVIDENCE",
            "MARK_READY_FOR_MANUAL_APPROVAL"
        ],
        
        "forbidden_actions": [
            "NO_AUTO_APPROVE_PARTNERSHIP",
            "NO_AUTO_SHARE_DATA_WITH_PARTNER",
            "NO_AUTO_TERMINATE_PARTNERSHIP"
        ],
        
        "required_evidence": [
            "partner_profile",
            "risk_review",
            "approval_record"
        ],
        
        "next_maturity_gap": "L3 deterministic logic: partnership lifecycle and risk assessment rules",
        
        "safety_flags": {
            "no_api_claim": True,
            "no_frontend_claim": True,
            "no_live_integration_claim": True,
            "no_provider_call": True,
            "no_kpi_claim": True,
            "no_brain_claim": True,
            "no_autonomous_execution": True,
            "no_external_side_effects": True,
            "no_l3_claim": True,
            "no_l4_claim": True,
            "no_l5_claim": True,
            "no_l6_claim": True
        }
    }


# --- L3 Deterministic Readiness Classifier (A-027.9) ---

A0279_L3_READY = True


def classify_partnership_registry_readiness(tenant_id: int, evidence: dict | None = None) -> dict:
    """Deterministic L3 readiness classifier. No decision execution, no autonomy, no provider calls."""
    validate_tenant_id(tenant_id)
    required_evidence = [
        "partner_identity_present",
        "partner_status_verified",
        "relationship_owner_assigned",
        "compliance_review_required",
        "renewal_review_policy_available",
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
            "PARTNERSHIP_READINESS_CLASSIFICATION",
            "PARTNER_EVIDENCE_CHECK",
            "HUMAN_REVIEW_PREPARATION",
        ],
        "forbidden_actions": [
            "AUTO_CREATE_LEGAL_PARTNERSHIP",
            "AUTO_APPROVE_PARTNER",
            "AUTO_RENEW_PARTNERSHIP",
            "MUTATE_CONTRACT_RECORD",
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
