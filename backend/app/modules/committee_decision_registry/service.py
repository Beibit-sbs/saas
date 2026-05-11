"""Committee Decision Registry Foundation Service Contract - A-027.2 L2."""

MODULE_NAME = "committee_decision_registry"
UCE_ID = "UCE-090"
TARGET_LEVEL = "L2"
EXPANSION_LAYER = "university_completeness"


def get_committee_decision_registry_foundation_contract(tenant_id: int, payload: dict | None = None) -> dict:
    """
    Return L2 foundation contract for committee decision registry.
    
    Tenant validation:
    - None/0/-1 rejected
    - positive int accepted
    
    Records formal committee decisions. No autonomous recording, deterministic only.
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
            "MEETING_REVIEW",
            "DECISION_RECORDED",
            "SIGNATURE_PENDING",
            "ARCHIVED",
        ],
        "allowed_actions": [
            "RECORD_DECISION",
            "DOCUMENT_MEETING_OUTCOMES",
            "PREPARE_MINUTES",
            "REQUEST_SIGNATURES",
            "ARCHIVE_DECISION",
        ],
        "forbidden_actions": [
            "AUTO_RECORD_DECISION",
            "AUTO_APPROVE_MINUTES",
            "AUTO_SIGN_PROTOCOL",
            "AUTO_PUBLISH_DECISION",
        ],
        "required_evidence": [
            "decision_id",
            "committee_id",
            "meeting_date",
        ],
        "next_maturity_gap": "L3 deterministic logic: decision lineage tracking, escalation workflows, evidence audit",
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
