"""
Workload Management Service Contract

L2 deterministic service contract for workload planning.
No payroll mutation, no schedule mutation, no automatic assignment.
"""

from typing import Dict, Any, Tuple

# ============================================================================
# FSM/Status Constants
# ============================================================================

WORKLOAD_STATUS = {
    "PLANNING": "Initial planning and collection stage",
    "UNDER_REVIEW": "Awaiting approval from management",
    "READY_FOR_ASSIGNMENT": "Approved, ready for staff assignment",
    "ASSIGNED": "Workload assigned to staff members",
    "MONITORED": "Workload being actively monitored",
    "COMPLETED": "Workload cycle complete",
}

FORBIDDEN_AUTO_ACTIONS = [
    "AUTO_ASSIGN",
    "AUTO_OVERRIDE_CONSTRAINTS",
    "AUTO_MUTATE_PAYROLL",
    "AUTO_DISTRIBUTE_WORKLOAD",
]

# ============================================================================
# Safety Flags
# ============================================================================

SAFETY_FLAGS = {
    "no_api_claim": True,
    "no_frontend_claim": True,
    "no_brain_claim": True,
    "no_payroll_mutation": True,
    "no_schedule_mutation": True,
    "no_automatic_assignment": True,
    "no_autonomous_execution": True,
    "target_level": "L2",
}


# ============================================================================
# Tenant Validation (Critical)
# ============================================================================

def validate_workload_tenant(tenant_id: Any) -> bool:
    """
    Validate tenant_id for workload access.
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

def validate_workload_input(tenant_id: Any, payload: Any) -> Tuple[bool, Dict[str, Any]]:
    """
    Validate workload input deterministically.

    Args:
        tenant_id: Tenant identifier for scoping
        payload: Workload payload to validate

    Returns:
        Tuple of (is_valid: bool, validation_result: Dict)
    """
    if not validate_workload_tenant(tenant_id):
        return (False, {"error": "Invalid tenant_id"})

    if not isinstance(payload, dict):
        return (False, {"error": "Payload must be dictionary"})

    required_fields = ["workload_type", "units"]
    missing_fields = [f for f in required_fields if f not in payload]

    if missing_fields:
        return (False, {"error": "Missing required fields", "missing": missing_fields})

    return (True, {
        "valid": True,
        "tenant_id": tenant_id,
        "workload_type": payload.get("workload_type"),
        "units": payload.get("units"),
        "validation_status": "WORKLOAD_INPUT_VALID",
    })


def get_workload_readiness_contract(tenant_id: Any) -> Dict[str, Any]:
    """
    Return workload L2 readiness contract.

    Args:
        tenant_id: Tenant identifier for scoping

    Returns:
        Dictionary with workload readiness status
    """
    if not validate_workload_tenant(tenant_id):
        return {
            "tenant_id": None,
            "module": "workload_management",
            "readiness_status": "TENANT_VALIDATION_FAILED",
            "error": "Invalid tenant_id",
        }

    return {
        "tenant_id": tenant_id,
        "module": "workload_management",
        "readiness_status": "L2_CONTRACT_READY",
        "evidence_level": "L2",
        "target_level": "L2",
        "valid_statuses": list(WORKLOAD_STATUS.keys()),
        "forbidden_auto_actions": FORBIDDEN_AUTO_ACTIONS,
        "safety_flags": SAFETY_FLAGS,
        "contract_type": "deterministic_workload_planning",
        "note": "Planning only, no payroll or schedule mutation in L2",
    }


def get_workload_status_options(tenant_id: Any) -> Dict[str, Any]:
    """
    Return available workload status options.

    Args:
        tenant_id: Tenant identifier for scoping

    Returns:
        Dictionary with status options
    """
    if not validate_workload_tenant(tenant_id):
        return {"error": "Invalid tenant_id"}

    return {
        "valid": True,
        "tenant_id": tenant_id,
        "available_statuses": list(WORKLOAD_STATUS.keys()),
        "allowed_transitions": {
            "PLANNING": ["UNDER_REVIEW", "PLANNING"],
            "UNDER_REVIEW": ["READY_FOR_ASSIGNMENT", "PLANNING"],
            "READY_FOR_ASSIGNMENT": ["ASSIGNED", "UNDER_REVIEW"],
            "ASSIGNED": ["MONITORED"],
            "MONITORED": ["COMPLETED"],
            "COMPLETED": [],
        },
    }
