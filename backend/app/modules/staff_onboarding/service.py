"""Staff Onboarding Foundation Service Contract - A-027.2 L2."""

MODULE_NAME = "staff_onboarding"
UCE_ID = "UCE-002"
TARGET_LEVEL = "L2"
EXPANSION_LAYER = "university_completeness"


def get_staff_onboarding_foundation_contract(tenant_id: int, payload: dict | None = None) -> dict:
    """
    Return L2 foundation contract for staff onboarding.
    
    Tenant validation:
    - None/0/-1 rejected
    - positive int accepted
    
    No provider calls, no autonomy, deterministic only.
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
            "PREBOARDING",
            "DOCUMENT_COLLECTION",
            "ACCESS_REQUEST_REVIEW",
            "ORIENTATION",
            "COMPLETED",
        ],
        "allowed_actions": [
            "CREATE_ONBOARDING_PLAN",
            "ADD_DOCUMENT_REQUIREMENT",
            "SUBMIT_ACCESS_REQUEST",
            "RECORD_ORIENTATION_COMPLETION",
            "COMPLETE_ONBOARDING",
        ],
        "forbidden_actions": [
            "AUTO_GRANT_ACCESS",
            "AUTO_SIGN_CONTRACT",
            "AUTO_COMPLETE_ONBOARDING",
            "AUTO_CREATE_ACCOUNTS",
        ],
        "required_evidence": [
            "onboarding_plan_id",
            "employee_offer_letter",
            "document_checklist",
        ],
        "next_maturity_gap": "L3 deterministic logic: compliance task tracking, document validation workflow",
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
