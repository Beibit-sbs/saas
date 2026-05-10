"""
Timetable Change Simulation Service Contract

L2 deterministic service contract for simulation request/response.
No real timetable mutation, no optimization solving, no conflict resolution.
"""

from typing import Dict, Any, Tuple

# ============================================================================
# FSM/Status Constants
# ============================================================================

SIMULATION_STATUS = {
    "PENDING": "Awaiting simulation execution",
    "SIMULATED": "Simulation completed successfully",
    "CONFLICT_DETECTED": "Simulation detected conflicts",
    "READY_FOR_APPROVAL": "No conflicts detected, ready for review",
    "SIMULATION_FAILED": "Simulation process encountered error",
}

FORBIDDEN_MUTATIONS = [
    "APPLY_TIMETABLE",
    "COMMIT_CHANGES",
    "AUTO_RESOLVE_CONFLICTS",
    "MODIFY_ACTUAL_SCHEDULE",
]

# ============================================================================
# Safety Flags
# ============================================================================

SAFETY_FLAGS = {
    "no_api_claim": True,
    "no_frontend_claim": True,
    "no_brain_claim": True,
    "no_real_mutation": True,
    "no_optimization_solver": True,
    "no_autonomous_execution": True,
    "target_level": "L2",
}


# ============================================================================
# Tenant Validation (Critical)
# ============================================================================

def validate_simulation_tenant(tenant_id: Any) -> bool:
    """
    Validate tenant_id for simulation access.
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

def validate_simulation_request(tenant_id: Any, request: Any) -> Tuple[bool, Dict[str, Any]]:
    """
    Validate simulation request deterministically.

    Args:
        tenant_id: Tenant identifier for scoping
        request: Simulation request to validate

    Returns:
        Tuple of (is_valid: bool, validation_result: Dict)
    """
    if not validate_simulation_tenant(tenant_id):
        return (False, {"error": "Invalid tenant_id"})

    if not isinstance(request, dict):
        return (False, {"error": "Request must be dictionary"})

    required_fields = ["proposal_id", "simulation_type"]
    missing_fields = [f for f in required_fields if f not in request]

    if missing_fields:
        return (False, {"error": "Missing required fields", "missing": missing_fields})

    return (True, {
        "valid": True,
        "tenant_id": tenant_id,
        "proposal_id": request.get("proposal_id"),
        "simulation_type": request.get("simulation_type"),
        "validation_status": "REQUEST_VALID",
    })


def get_simulation_readiness_response(tenant_id: Any) -> Dict[str, Any]:
    """
    Return simulation readiness contract for L2 assessment.

    Args:
        tenant_id: Tenant identifier for scoping

    Returns:
        Dictionary with simulation readiness status
    """
    if not validate_simulation_tenant(tenant_id):
        return {
            "tenant_id": None,
            "module": "timetable_change_simulation",
            "readiness_status": "TENANT_VALIDATION_FAILED",
            "error": "Invalid tenant_id",
        }

    return {
        "tenant_id": tenant_id,
        "module": "timetable_change_simulation",
        "readiness_status": "L2_CONTRACT_READY",
        "evidence_level": "L2",
        "target_level": "L2",
        "valid_statuses": list(SIMULATION_STATUS.keys()),
        "forbidden_mutations": FORBIDDEN_MUTATIONS,
        "safety_flags": SAFETY_FLAGS,
        "contract_type": "deterministic_readonly_simulation",
        "note": "Simulation returns status but does not mutate actual timetable",
    }


def get_simulation_output_contract(tenant_id: Any, simulation_status: str = "PENDING") -> Dict[str, Any]:
    """
    Return deterministic simulation output contract.

    Args:
        tenant_id: Tenant identifier for scoping
        simulation_status: Current simulation status

    Returns:
        Dictionary with simulation output fields
    """
    if not validate_simulation_tenant(tenant_id):
        return {"error": "Invalid tenant_id"}

    return {
        "tenant_id": tenant_id,
        "module": "timetable_change_simulation",
        "simulation_status": simulation_status,
        "conflicts_detected": simulation_status == "CONFLICT_DETECTED",
        "ready_for_approval": simulation_status == "READY_FOR_APPROVAL",
        "actual_schedule_modified": False,
        "safety_flags": SAFETY_FLAGS,
    }
