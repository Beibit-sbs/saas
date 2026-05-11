"""Performance_Appraisal L2 Foundation Service Contract (UCE-005)."""

from . import MODULE_NAME, UCE_ID, TARGET_LEVEL, CONTRACT_VERSION, FOUNDATION_STATUS


def validate_tenant_id(tenant_id: int) -> int:
    """Fail-closed tenant validation."""
    if not tenant_id or tenant_id <= 0:
        raise ValueError(f"invalid_tenant_id: {tenant_id}")
    return tenant_id


def get_performance_appraisal_foundation_contract(tenant_id: int, payload: dict | None = None) -> dict:
    """L2 foundation contract for performance_appraisal. No provider calls, no autonomy, deterministic only."""
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
            "APPRAISAL_DRAFT",
            "MANAGER_REVIEW",
            "HR_REVIEW",
            "EMPLOYEE_ACKNOWLEDGEMENT",
            "CLOSED"
        ],
        
        "allowed_actions": [
            "REVIEW_APPRAISAL",
            "REQUEST_PERFORMANCE_EVIDENCE",
            "MARK_READY_FOR_HR_REVIEW"
        ],
        
        "forbidden_actions": [
            "NO_AUTO_SCORE_EMPLOYEE",
            "NO_AUTO_CHANGE_SALARY",
            "NO_AUTO_DISCIPLINARY_ACTION"
        ],
        
        "required_evidence": [
            "appraisal_form",
            "performance_evidence",
            "review_record"
        ],
        
        "next_maturity_gap": "L3 deterministic logic: performance scoring and validation rules",
        
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
