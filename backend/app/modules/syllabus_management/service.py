"""Syllabus Management Foundation Service Contract - A-027.2 L2."""

MODULE_NAME = "syllabus_management"
UCE_ID = "UCE-015"
TARGET_LEVEL = "L2"
EXPANSION_LAYER = "university_completeness"


def get_syllabus_management_foundation_contract(tenant_id: int, payload: dict | None = None) -> dict:
    """
    Return L2 foundation contract for syllabus management.
    
    Tenant validation:
    - None/0/-1 rejected
    - positive int accepted
    
    Manages syllabus lifecycle. No publication automation, deterministic only.
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
            "DEPARTMENT_REVIEW",
            "QUALITY_REVIEW",
            "APPROVED_MANUAL",
            "ARCHIVED",
        ],
        "allowed_actions": [
            "CREATE_SYLLABUS",
            "SUBMIT_FOR_DEPARTMENT_REVIEW",
            "SUBMIT_FOR_QUALITY_REVIEW",
            "APPROVE_SYLLABUS",
            "ARCHIVE_SYLLABUS",
        ],
        "forbidden_actions": [
            "AUTO_APPROVE_SYLLABUS",
            "AUTO_PUBLISH_SYLLABUS",
            "AUTO_CHANGE_COURSE_POLICY",
            "AUTO_DELETE_SYLLABUS",
        ],
        "required_evidence": [
            "syllabus_id",
            "course_id",
            "academic_term",
        ],
        "next_maturity_gap": "L3 deterministic logic: policy compliance checking, quality metrics validation",
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
