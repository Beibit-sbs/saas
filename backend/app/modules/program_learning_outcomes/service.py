"""Program Learning Outcomes Foundation Service Contract - A-027.2 L2."""

MODULE_NAME = "program_learning_outcomes"
UCE_ID = "UCE-071"
TARGET_LEVEL = "L2"
EXPANSION_LAYER = "university_completeness"


def get_program_learning_outcomes_foundation_contract(tenant_id: int, payload: dict | None = None) -> dict:
    """
    Return L2 foundation contract for program learning outcomes.
    
    Tenant validation:
    - None/0/-1 rejected
    - positive int accepted
    
    Program-level outcomes catalog. No enforcement, deterministic only.
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
            "ALIGNMENT_REVIEW",
            "QUALITY_REVIEW",
            "APPROVED_MANUAL",
        ],
        "allowed_actions": [
            "CREATE_PLO",
            "DEFINE_LEARNING_DOMAIN",
            "SUBMIT_FOR_ALIGNMENT_REVIEW",
            "SUBMIT_FOR_QUALITY_REVIEW",
            "APPROVE_PLO",
        ],
        "forbidden_actions": [
            "AUTO_APPROVE_OUTCOME",
            "AUTO_CHANGE_ACCREDITATION_MAPPING",
            "AUTO_DELETE_OUTCOME",
            "AUTO_LINK_COURSES",
        ],
        "required_evidence": [
            "outcome_id",
            "program_id",
            "outcome_domain",
        ],
        "next_maturity_gap": "L3 deterministic logic: course mapping validation, assessment strategy routing",
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
