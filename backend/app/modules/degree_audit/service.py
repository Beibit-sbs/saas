"""Degree_Audit L2 Foundation Service Contract (UCE-092)."""

from . import MODULE_NAME, TARGET_LEVEL, CONTRACT_VERSION, FOUNDATION_STATUS

CANONICAL_UCE_ID = "UCE-092"


def validate_tenant_id(tenant_id: int) -> int:
    """Fail-closed tenant validation."""
    if not tenant_id or tenant_id <= 0:
        raise ValueError(f"invalid_tenant_id: {tenant_id}")
    return tenant_id


def get_degree_audit_foundation_contract(tenant_id: int, payload: dict | None = None) -> dict:
    """L2 foundation contract for degree_audit. No provider calls, no autonomy, deterministic only."""
    validate_tenant_id(tenant_id)
    
    return {
        "tenant_id": tenant_id,
        "module": MODULE_NAME,
        "uce_id": CANONICAL_UCE_ID,
        "maturity_level": TARGET_LEVEL,
        "expansion_layer": "university_completeness",
        "contract_status": "FOUNDATION_READY",
        "service_contract_ready": True,
        "tenant_scoped": True,
        "deterministic": True,
        
        "lifecycle_statuses": [
            "AUDIT_REQUESTED",
            "REQUIREMENT_CHECK",
            "EXCEPTION_REVIEW",
            "READY_FOR_MANUAL_APPROVAL",
            "CLOSED"
        ],
        
        "allowed_actions": [
            "REVIEW_DEGREE_REQUIREMENTS",
            "REQUEST_TRANSCRIPT_EVIDENCE",
            "MARK_READY_FOR_REGISTRAR_REVIEW"
        ],
        
        "forbidden_actions": [
            "NO_AUTO_GRADUATE_STUDENT",
            "NO_AUTO_OVERRIDE_REQUIREMENT",
            "NO_AUTO_CHANGE_TRANSCRIPT"
        ],
        
        "required_evidence": [
            "transcript",
            "curriculum_requirements",
            "exception_approval"
        ],
        
        "next_maturity_gap": "L3 deterministic logic: degree requirement validation and progress rules",
        
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
