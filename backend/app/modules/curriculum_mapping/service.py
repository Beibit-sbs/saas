"""Curriculum Mapping Foundation Service Contract - A-027.2 L2."""

MODULE_NAME = "curriculum_mapping"
UCE_ID = "UCE-014"
TARGET_LEVEL = "L2"
EXPANSION_LAYER = "university_completeness"


def get_curriculum_mapping_foundation_contract(tenant_id: int, payload: dict | None = None) -> dict:
    """
    Return L2 foundation contract for curriculum mapping.
    
    Tenant validation:
    - None/0/-1 rejected
    - positive int accepted
    
    Maps courses to learning outcomes. No enforcement, deterministic only.
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
            "DRAFT_MAPPING",
            "REVIEW_REQUIRED",
            "APPROVED_MANUAL",
            "ARCHIVED",
        ],
        "allowed_actions": [
            "CREATE_CURRICULUM_MAP",
            "LINK_COURSE_TO_OUTCOME",
            "SUBMIT_FOR_REVIEW",
            "APPROVE_MAPPING",
            "ARCHIVE_MAPPING",
        ],
        "forbidden_actions": [
            "AUTO_APPROVE_CURRICULUM",
            "AUTO_CHANGE_PROGRAM",
            "AUTO_DELETE_MAPPING",
            "AUTO_LINK_COURSES",
        ],
        "required_evidence": [
            "mapping_id",
            "program_id",
            "course_ids",
        ],
        "next_maturity_gap": "L3 deterministic logic: outcome alignment validation, curriculum compliance checking",
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
