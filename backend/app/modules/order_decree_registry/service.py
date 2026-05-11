"""Order Decree Registry Foundation Service Contract - A-027.2 L2."""

MODULE_NAME = "order_decree_registry"
UCE_ID = "UCE-011"
TARGET_LEVEL = "L2"
EXPANSION_LAYER = "university_completeness"


def get_order_decree_registry_foundation_contract(tenant_id: int, payload: dict | None = None) -> dict:
    """
    Return L2 foundation contract for order/decree registry.
    
    Tenant validation:
    - None/0/-1 rejected
    - positive int accepted
    
    No provider calls, no live governance, deterministic only.
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
            "LEGAL_REVIEW",
            "SIGNATURE_PENDING",
            "REGISTERED",
            "ARCHIVED",
        ],
        "allowed_actions": [
            "CREATE_DECREE",
            "SUBMIT_FOR_LEGAL_REVIEW",
            "REQUEST_SIGNATURES",
            "RECORD_REGISTRATION",
            "ARCHIVE_DECREE",
        ],
        "forbidden_actions": [
            "AUTO_ISSUE_ORDER",
            "AUTO_REGISTER_DECREE",
            "AUTO_SIGN_ORDER",
            "AUTO_PUBLISH_DECREE",
        ],
        "required_evidence": [
            "decree_id",
            "decree_type",
            "issuing_authority",
        ],
        "next_maturity_gap": "L3 deterministic logic: decree validation, compliance checks, archival policies",
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
