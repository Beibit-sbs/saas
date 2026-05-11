"""Document Workflow Foundation Service Contract - A-027.2 L2."""

MODULE_NAME = "document_workflow"
UCE_ID = "UCE-009"
TARGET_LEVEL = "L2"
EXPANSION_LAYER = "university_completeness"


def get_document_workflow_foundation_contract(tenant_id: int, payload: dict | None = None) -> dict:
    """
    Return L2 foundation contract for document workflow.
    
    Tenant validation:
    - None/0/-1 rejected
    - positive int accepted
    
    No provider calls, no e-signature execution, deterministic only.
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
            "ROUTING",
            "APPROVAL_PENDING",
            "SIGNATURE_PENDING",
            "ARCHIVED",
        ],
        "allowed_actions": [
            "CREATE_DOCUMENT",
            "START_ROUTING",
            "SUBMIT_FOR_APPROVAL",
            "REQUEST_SIGNATURE",
            "ARCHIVE_DOCUMENT",
        ],
        "forbidden_actions": [
            "AUTO_SIGN_DOCUMENT",
            "AUTO_APPROVE_DOCUMENT",
            "AUTO_DELETE_DOCUMENT",
            "AUTO_ROUTE_DOCUMENT",
        ],
        "required_evidence": [
            "document_id",
            "document_type",
            "originator",
        ],
        "next_maturity_gap": "L3 deterministic logic: routing rule execution, approval workflow automation",
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
