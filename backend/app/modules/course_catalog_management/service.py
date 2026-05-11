"""Course_Catalog_Management L2 Foundation Service Contract (UCE-076)."""

from . import MODULE_NAME, UCE_ID, TARGET_LEVEL, CONTRACT_VERSION, FOUNDATION_STATUS


def validate_tenant_id(tenant_id: int) -> int:
    """Fail-closed tenant validation."""
    if not tenant_id or tenant_id <= 0:
        raise ValueError(f"invalid_tenant_id: {tenant_id}")
    return tenant_id


def get_course_catalog_management_foundation_contract(tenant_id: int, payload: dict | None = None) -> dict:
    """L2 foundation contract for course_catalog_management. No provider calls, no autonomy, deterministic only."""
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
            "COURSE_DRAFT",
            "DEPARTMENT_REVIEW",
            "QUALITY_REVIEW",
            "APPROVED_MANUAL",
            "ARCHIVED"
        ],
        
        "allowed_actions": [
            "REVIEW_COURSE_CATALOG_ENTRY",
            "REQUEST_SYLLABUS_EVIDENCE",
            "MARK_READY_FOR_PUBLICATION_REVIEW"
        ],
        
        "forbidden_actions": [
            "NO_AUTO_PUBLISH_COURSE",
            "NO_AUTO_DELETE_COURSE",
            "NO_AUTO_CHANGE_CREDIT_VALUE"
        ],
        
        "required_evidence": [
            "course_description",
            "syllabus_reference",
            "department_approval"
        ],
        
        "next_maturity_gap": "L3 deterministic logic: course catalog versioning and publication rules",
        
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
