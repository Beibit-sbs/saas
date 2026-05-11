"""Course Learning Outcomes Foundation Service Contract - A-027.2 L2."""

MODULE_NAME = "course_learning_outcomes"
UCE_ID = "UCE-072"
TARGET_LEVEL = "L2"
EXPANSION_LAYER = "university_completeness"


def get_course_learning_outcomes_foundation_contract(tenant_id: int, payload: dict | None = None) -> dict:
    """
    Return L2 foundation contract for course learning outcomes.
    
    Tenant validation:
    - None/0/-1 rejected
    - positive int accepted
    
    Course-level outcomes definitions. No enforcement, deterministic only.
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
            "ASSESSMENT_MAPPING_REVIEW",
            "APPROVED_MANUAL",
        ],
        "allowed_actions": [
            "CREATE_CLO",
            "DEFINE_OUTCOME_STATEMENT",
            "LINK_TO_PLO",
            "SUBMIT_FOR_ALIGNMENT_REVIEW",
            "SUBMIT_FOR_ASSESSMENT_MAPPING",
            "APPROVE_CLO",
        ],
        "forbidden_actions": [
            "AUTO_APPROVE_CLO",
            "AUTO_CHANGE_ASSESSMENT_MAPPING",
            "AUTO_DELETE_CLO",
            "AUTO_PUBLISH_CLO",
        ],
        "required_evidence": [
            "clo_id",
            "course_id",
            "outcome_statement",
        ],
        "next_maturity_gap": "L3 deterministic logic: PLO mapping validation, assessment rubric workflow",
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
