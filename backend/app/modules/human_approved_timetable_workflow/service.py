"""
Human-Approved Timetable Workflow Service Contract

L2 deterministic service contract for workflow state management.
All state transitions require explicit human approval.
No automatic application permitted.
"""

from typing import Dict, Any, Tuple

# ============================================================================
# FSM/Status Constants
# ============================================================================

WORKFLOW_STATUS = {
    "DRAFT": "Initial proposal state, awaiting initial review",
    "PENDING_HUMAN_REVIEW": "Awaiting human decision on workflow approval",
    "HUMAN_APPROVED": "Approved by human reviewer, ready for manual application",
    "HUMAN_REJECTED": "Rejected by human reviewer during evaluation",
    "CANCELLED": "Workflow cancelled by initiator or admin",
}

FORBIDDEN_ACTIONS = [
    "AUTO_APPLY",
    "AUTO_OPTIMIZE",
    "AUTONOMOUS_ROLLBACK",
    "AUTO_RESCHEDULE",
]

# Critical safety flag: all transitions require human intervention
HUMAN_APPROVAL_REQUIRED = True

# ============================================================================
# Safety Flags
# ============================================================================

SAFETY_FLAGS = {
    "no_api_claim": True,
    "no_frontend_claim": True,
    "no_brain_claim": True,
    "no_kpi_lineage_claim": True,
    "no_autonomous_execution": True,
    "no_e2e_claim": True,
    "target_level": "L2",
}


# ============================================================================
# Tenant Validation (Critical)
# ============================================================================

def validate_workflow_tenant(tenant_id: Any) -> bool:
    """
    Validate tenant_id for workflow access.
    Fail-closed: reject None, non-positive, non-integer.

    Args:
        tenant_id: Claimed tenant identifier

    Returns:
        bool: True if valid, False if invalid

    Raises:
        None: Returns bool deterministically
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

def get_workflow_status_contract(tenant_id: Any) -> Dict[str, Any]:
    """
    Return deterministic workflow status contract for L2 readiness.

    Args:
        tenant_id: Tenant identifier for scoping

    Returns:
        Dictionary with workflow L2 contract
    """
    if not validate_workflow_tenant(tenant_id):
        return {
            "tenant_id": None,
            "module": "human_approved_timetable_workflow",
            "readiness_status": "TENANT_VALIDATION_FAILED",
            "evidence_level": "L0",
            "target_level": "L2",
            "error": "Invalid tenant_id",
        }

    return {
        "tenant_id": tenant_id,
        "module": "human_approved_timetable_workflow",
        "readiness_status": "L2_CONTRACT_READY",
        "evidence_level": "L2",
        "target_level": "L2",
        "human_approval_required": HUMAN_APPROVAL_REQUIRED,
        "valid_statuses": list(WORKFLOW_STATUS.keys()),
        "forbidden_actions": FORBIDDEN_ACTIONS,
        "safety_flags": SAFETY_FLAGS,
        "workflow_type": "deterministic_human_approval_required",
    }


def get_workflow_state_transition_rules(tenant_id: Any) -> Dict[str, Any]:
    """
    Return deterministic workflow state transition rules.

    Args:
        tenant_id: Tenant identifier for scoping

    Returns:
        Dictionary with allowed transitions
    """
    if not validate_workflow_tenant(tenant_id):
        return {"valid": False, "error": "Invalid tenant_id"}

    return {
        "valid": True,
        "tenant_id": tenant_id,
        "transitions": {
            "DRAFT": ["PENDING_HUMAN_REVIEW", "CANCELLED"],
            "PENDING_HUMAN_REVIEW": ["HUMAN_APPROVED", "HUMAN_REJECTED", "CANCELLED"],
            "HUMAN_APPROVED": ["CANCELLED"],
            "HUMAN_REJECTED": ["DRAFT", "CANCELLED"],
            "CANCELLED": [],
        },
        "rule": "All transitions are deterministic and require human decision points",
    }
