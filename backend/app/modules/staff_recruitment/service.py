"""Staff Recruitment Foundation Service Contract - A-027.2 L2."""

MODULE_NAME = "staff_recruitment"
UCE_ID = "UCE-001"
TARGET_LEVEL = "L2"
EXPANSION_LAYER = "university_completeness"


def get_staff_recruitment_foundation_contract(tenant_id: int, payload: dict | None = None) -> dict:
    """
    Return L2 foundation contract for staff recruitment.
    
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
            "DRAFT",
            "SCREENING",
            "INTERVIEW",
            "OFFER_REVIEW",
            "CLOSED",
        ],
        "allowed_actions": [
            "CREATE_RECRUITMENT_REQUEST",
            "ADD_SCREENING_NOTES",
            "RECORD_INTERVIEW",
            "SUBMIT_OFFER_FOR_REVIEW",
            "CLOSE_RECRUITMENT",
        ],
        "forbidden_actions": [
            "AUTO_HIRE",
            "AUTO_REJECT_CANDIDATE",
            "AUTO_APPROVE_OFFER",
            "AUTO_SEND_OFFER_LETTER",
        ],
        "required_evidence": [
            "recruitment_request_id",
            "candidate_profile",
            "screening_criteria",
        ],
        "next_maturity_gap": "L3 deterministic logic: candidate qualification scoring, screening workflow",
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
