"""International Office Foundation Service Contract - A-027.2 L2."""

MODULE_NAME = "international_office"
UCE_ID = "UCE-019"
TARGET_LEVEL = "L2"
EXPANSION_LAYER = "university_completeness"


def get_international_office_foundation_contract(tenant_id: int, payload: dict | None = None) -> dict:
    """
    Return L2 foundation contract for international office.
    
    Tenant validation:
    - None/0/-1 rejected
    - positive int accepted
    
    Manages international student operations. No visa authority, deterministic only.
    """
    
    # Tenant fail-closed validation
    if not tenant_id or tenant_id <= 0:
        raise ValueError(f"invalid_tenant_id: {tenant_id}")
    
    return {
        "tenant_id": tenant_id,
        "module": MODULE_NAME,
        "uce_id": UCE_ID,
        "maturity_level": "L2",
        "expansion_layer": EXPANSION_LAYER,
        "contract_status": "FOUNDATION_READY",
        "service_contract_ready": True,
        "tenant_scoped": True,
        "deterministic": True,
        "lifecycle_statuses": [
            "REQUESTED",
            "DOCUMENT_REVIEW",
            "PARTNER_REVIEW",
            "APPROVED_MANUAL",
            "CLOSED",
        ],
        "allowed_actions": [
            "CREATE_MOBILITY_REQUEST",
            "SUBMIT_DOCUMENTS",
            "NOTIFY_PARTNER",
            "APPROVE_MOBILITY",
            "CLOSE_REQUEST",
        ],
        "forbidden_actions": [
            "AUTO_APPROVE_MOBILITY",
            "AUTO_ISSUE_VISA_DECISION",
            "AUTO_CONFIRM_PARTNERSHIP",
            "AUTO_GRANT_VISA",
        ],
        "required_evidence": [
            "request_id",
            "student_profile",
            "destination_country",
        ],
        "next_maturity_gap": "L3 deterministic logic: visa requirement validation, partner agreement workflow",
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
            "no_l6_claim": True,
        },
    }
