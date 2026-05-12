"""
disability_support_services service.py — L2 Foundation Contract

Deterministic foundation contract for disability support request governance.
Tenant fail-closed validation.
No autonomy, no provider calls, no KPI, no Brain, no L3+ claims.
"""

# Constants
MODULE_NAME = "disability_support_services"
UCE_ID = "UCE-081"
TARGET_LEVEL = "L2"
CONTRACT_VERSION = "A-027.4"
FOUNDATION_STATUS = "FOUNDATION_READY"

# Lifecycle statuses
LIFECYCLE_STATUSES = [
    "REQUESTED",
    "DOCUMENTATION_REVIEW",
    "ACCOMMODATION_REVIEW",
    "APPROVED_MANUAL",
    "CLOSED",
]

# Allowed actions (deterministic constants only)
ALLOWED_ACTIONS = [
    "REVIEW_SUPPORT_REQUEST",
    "REQUEST_DOCUMENTATION",
    "MARK_READY_FOR_ACCOMMODATION_REVIEW",
]

# Forbidden actions (deterministic constraints only)
FORBIDDEN_ACTIONS = [
    "AUTO_APPROVE_ACCOMMODATION",
    "AUTO_DENY_SUPPORT",
    "AUTO_DISCLOSE_DISABILITY_DATA",
]

# Required evidence
REQUIRED_EVIDENCE = [
    "support_request",
    "consent_record",
    "documentation_evidence",
]

# Safety flags
SAFETY_FLAGS = {
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
}


def validate_tenant_id(tenant_id):
    """Fail-closed tenant validation."""
    if tenant_id is None:
        raise ValueError("tenant_id cannot be None")
    if not isinstance(tenant_id, int):
        raise TypeError(f"tenant_id must be int, got {type(tenant_id)}")
    if tenant_id <= 0:
        raise ValueError(f"tenant_id must be positive, got {tenant_id}")
    return tenant_id


def get_disability_support_services_foundation_contract(tenant_id, payload=None):
    """
    Generate deterministic L2 foundation contract for disability support services.
    
    Args:
        tenant_id: Integer tenant identifier
        payload: Optional dict (unused at L2)
    
    Returns:
        dict: Deterministic foundation contract
    """
    tenant_id = validate_tenant_id(tenant_id)
    
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
        "lifecycle_statuses": LIFECYCLE_STATUSES,
        "allowed_actions": ALLOWED_ACTIONS,
        "forbidden_actions": FORBIDDEN_ACTIONS,
        "required_evidence": REQUIRED_EVIDENCE,
        "next_maturity_gap": "L3 deterministic logic required",
        "sensitive_boundary": {
            "no_medical_diagnosis": True,
            "no_automatic_accommodation_decision": True,
            "no_disclosure_of_sensitive_data": True,
        },
        "safety_flags": SAFETY_FLAGS,
    }
