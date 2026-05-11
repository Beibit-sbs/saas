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
