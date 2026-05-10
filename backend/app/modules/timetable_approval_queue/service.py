"""
Timetable Approval Queue Service Contract

L2 deterministic service contract for human review queue management.
No automatic decisions, no auto-apply, queue status tracking only.
"""

from typing import Dict, Any

# ============================================================================
# FSM/Status Constants
# ============================================================================

QUEUE_STATUS = {
    "PENDING_REVIEW": "Awaiting human reviewer attention",
    "IN_PROGRESS": "Reviewer is actively examining item",
    "APPROVED_PENDING_APPLY": "Approved by reviewer, awaiting apply command",
    "REJECTED": "Rejected by reviewer during evaluation",
    "APPLIED": "Changes have been applied successfully",
}

ALLOWED_ACTIONS = [
    "APPROVE",
    "REJECT",
    "REQUEST_MORE_INFO",
    "REASSIGN_REVIEWER",
    "VIEW_DETAILS",
]

FORBIDDEN_AUTO_ACTIONS = [
    "AUTO_APPROVE",
    "AUTO_APPLY",
    "AUTO_REJECT",
    "AUTO_ESCALATE",
]

# ============================================================================
# Safety Flags
# ============================================================================

SAFETY_FLAGS = {
    "no_api_claim": True,
    "no_frontend_claim": True,
    "no_brain_claim": True,
    "no_automatic_decision": True,
    "no_autonomous_execution": True,
    "target_level": "L2",
}


# ============================================================================
# Tenant Validation (Critical)
# ============================================================================

def validate_queue_tenant(tenant_id: Any) -> bool:
    """
    Validate tenant_id for queue access.
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

def enqueue_for_review(tenant_id: Any, item: Any) -> Dict[str, Any]:
    """
    Enqueue item for human review.

    Args:
        tenant_id: Tenant identifier for scoping
        item: Item to enqueue (dict with item_id, type, etc.)

    Returns:
        Dictionary with queue assignment
    """
    if not validate_queue_tenant(tenant_id):
        return {"valid": False, "error": "Invalid tenant_id"}

    if not isinstance(item, dict):
        return {"valid": False, "error": "Item must be dictionary"}

    return {
        "valid": True,
        "tenant_id": tenant_id,
        "queue_id": f"q_{tenant_id}_{item.get('item_id', 'unknown')}",
        "queue_status": "PENDING_REVIEW",
        "assigned_reviewer": None,  # Will be assigned by human coordination
        "item_type": item.get("type", "unknown"),
    }


def get_queue_status_contract(tenant_id: Any) -> Dict[str, Any]:
    """
    Return queue status contract for L2 readiness.

    Args:
        tenant_id: Tenant identifier for scoping

    Returns:
        Dictionary with queue status contract
    """
    if not validate_queue_tenant(tenant_id):
        return {
            "tenant_id": None,
            "module": "timetable_approval_queue",
            "readiness_status": "TENANT_VALIDATION_FAILED",
            "error": "Invalid tenant_id",
        }

    return {
        "tenant_id": tenant_id,
        "module": "timetable_approval_queue",
        "readiness_status": "L2_CONTRACT_READY",
        "evidence_level": "L2",
        "target_level": "L2",
        "valid_statuses": list(QUEUE_STATUS.keys()),
        "allowed_actions": ALLOWED_ACTIONS,
        "forbidden_auto_actions": FORBIDDEN_AUTO_ACTIONS,
        "safety_flags": SAFETY_FLAGS,
        "contract_type": "deterministic_human_review_queue",
    }


def get_queue_item_details(tenant_id: Any, queue_id: Any) -> Dict[str, Any]:
    """
    Return queue item details with tenant scoping.

    Args:
        tenant_id: Tenant identifier for scoping
        queue_id: Queue item identifier

    Returns:
        Dictionary with queue item details
    """
    if not validate_queue_tenant(tenant_id):
        return {"error": "Invalid tenant_id"}

    return {
        "valid": True,
        "tenant_id": tenant_id,
        "queue_id": queue_id,
        "queue_status": "PENDING_REVIEW",
        "allowed_actions": ALLOWED_ACTIONS,
        "forbidden_actions": FORBIDDEN_AUTO_ACTIONS,
    }
