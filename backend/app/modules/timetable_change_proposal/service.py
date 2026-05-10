"""
Timetable Change Proposal Service Contract

L2 deterministic service contract for proposal submission and validation.
No scheduling conflict detection, optimization, or automatic approval.
"""

from typing import Dict, Any, Tuple

# ============================================================================
# FSM/Status Constants
# ============================================================================

PROPOSAL_STATUS = {
    "SUBMITTED": "Initial proposal submission",
    "UNDER_REVIEW": "Being evaluated by system",
    "READY_FOR_SIMULATION": "Approved for simulation testing",
    "REJECTED": "Rejected during review phase",
    "APPLIED": "Change has been applied successfully",
}

# ============================================================================
# Safety Flags
# ============================================================================

SAFETY_FLAGS = {
    "no_api_claim": True,
    "no_frontend_claim": True,
    "no_brain_claim": True,
    "no_scheduling_conflict_solving": True,
    "no_autonomous_execution": True,
    "target_level": "L2",
}


# ============================================================================
# Tenant Validation (Critical)
# ============================================================================

def validate_proposal_tenant(tenant_id: Any) -> bool:
    """
    Validate tenant_id for proposal access.
    Fail-closed: reject None, non-positive, non-integer.

    Args:
        tenant_id: Claimed tenant identifier

    Returns:
        bool: True if valid, False if invalid
    """
    if tenant_id is None:
        return False
    if not isinstance(tenant_id, int):
        return False
    if tenant_id <= 0:
        return False
    return True


# ============================================================================
# Service Contracts
# ============================================================================

def validate_proposal_payload(tenant_id: Any, payload: Any) -> Tuple[bool, Dict[str, Any]]:
    """
    Validate proposal payload deterministically.
    Shallow validation: check structure, not scheduling feasibility.

    Args:
        tenant_id: Tenant identifier for scoping
        payload: Proposed payload to validate

    Returns:
        Tuple of (is_valid: bool, validation_result: Dict)
    """
    if not validate_proposal_tenant(tenant_id):
        return (False, {"error": "Invalid tenant_id"})

    if not isinstance(payload, dict):
        return (False, {"error": "Payload must be dictionary"})

    required_fields = ["proposal_type", "description"]
    missing_fields = [f for f in required_fields if f not in payload]

    if missing_fields:
        return (False, {"error": "Missing required fields", "missing": missing_fields})

    return (True, {
        "valid": True,
        "tenant_id": tenant_id,
        "proposal_type": payload.get("proposal_type"),
        "validation_status": "SHALLOW_CHECK_PASS",
        "note": "No scheduling conflict detection in L2 contract",
    })


def get_proposal_schema(tenant_id: Any) -> Dict[str, Any]:
    """
    Return deterministic proposal schema for L2 contract.

    Args:
        tenant_id: Tenant identifier for scoping

    Returns:
        Dictionary with expected proposal structure
    """
    if not validate_proposal_tenant(tenant_id):
        return {"valid": False, "error": "Invalid tenant_id"}

    return {
        "valid": True,
        "tenant_id": tenant_id,
        "schema": {
            "proposal_type": "string",
            "description": "string",
            "reason": "optional string",
            "affected_entities": "optional list",
        },
        "status_values": list(PROPOSAL_STATUS.keys()),
        "safety_flags": SAFETY_FLAGS,
    }


def get_proposal_readiness_contract(tenant_id: Any) -> Dict[str, Any]:
    """
    Return proposal L2 readiness contract.

    Args:
        tenant_id: Tenant identifier for scoping

    Returns:
        Dictionary with readiness status
    """
    if not validate_proposal_tenant(tenant_id):
        return {
            "tenant_id": None,
            "module": "timetable_change_proposal",
            "readiness_status": "TENANT_VALIDATION_FAILED",
            "error": "Invalid tenant_id",
        }

    return {
        "tenant_id": tenant_id,
        "module": "timetable_change_proposal",
        "readiness_status": "L2_CONTRACT_READY",
        "evidence_level": "L2",
        "target_level": "L2",
        "valid_statuses": list(PROPOSAL_STATUS.keys()),
        "safety_flags": SAFETY_FLAGS,
        "contract_type": "deterministic_shallow_validation",
    }
