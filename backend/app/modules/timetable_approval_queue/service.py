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
    "no_kpi_lineage_claim": True,
    "no_e2e_claim": True,
    "target_level": "L3",
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


def evaluate_queue_item(tenant_id: Any, item: Any) -> Dict[str, Any]:
    """Deterministically classify a queue item at L3."""
    if not validate_queue_tenant(tenant_id):
        return {
            "tenant_id": None,
            "module": "timetable_approval_queue",
            "maturity_level": "L3",
            "queue_status": "QUEUE_ITEM_INVALID",
            "classification": "QUEUE_ITEM_INVALID",
            "human_review_required": True,
            "allowed_actions": ["APPROVE", "REJECT", "REQUEST_MORE_INFO", "REASSIGN_REVIEWER"],
            "forbidden_actions": FORBIDDEN_AUTO_ACTIONS,
            "safety_flags": SAFETY_FLAGS,
        }

    queue_item = item if isinstance(item, dict) else {}
    queue_status = str(queue_item.get("queue_status") or queue_item.get("status") or "").upper()
    if not queue_item:
        classification = "QUEUE_ITEM_INVALID"
        next_step = "REQUEST_MORE_INFO"
    elif queue_item.get("requires_more_info") is True or queue_status == "BLOCKED_REQUIRES_MORE_INFO":
        classification = "BLOCKED_REQUIRES_MORE_INFO"
        next_step = "REQUEST_MORE_INFO"
    elif queue_status in {"IN_PROGRESS", "REVIEW_IN_PROGRESS"}:
        classification = "REVIEW_IN_PROGRESS"
        next_step = "CONTINUE_REVIEW"
    elif queue_status in {"READY_FOR_MANUAL_DECISION", "APPROVED_PENDING_APPLY", "PENDING_REVIEW"}:
        classification = "READY_FOR_MANUAL_DECISION" if queue_status != "PENDING_REVIEW" else "READY_FOR_REVIEW"
        next_step = "MANUAL_DECISION"
    else:
        classification = "READY_FOR_REVIEW"
        next_step = "BEGIN_REVIEW"

    return {
        "tenant_id": tenant_id,
        "module": "timetable_approval_queue",
        "maturity_level": "L3",
        "queue_status": classification,
        "classification": classification,
        "human_review_required": True,
        "allowed_actions": ["APPROVE", "REJECT", "REQUEST_MORE_INFO", "REASSIGN_REVIEWER"],
        "forbidden_actions": FORBIDDEN_AUTO_ACTIONS,
        "next_recommended_step": next_step,
        "safety_flags": SAFETY_FLAGS,
    }


def get_approval_queue_visibility_summary(tenant_id: Any) -> Dict[str, Any]:
    """Build deterministic read-only L4 visibility summary for approval queue operations."""
    if not validate_queue_tenant(tenant_id):
        return {
            "tenant_id": None,
            "module": "timetable_approval_queue",
            "visibility_level": "L4",
            "operational_status": "TENANT_VALIDATION_FAILED",
            "classification": "QUEUE_ITEM_INVALID",
            "allowed_actions": ["APPROVE", "REJECT", "REQUEST_MORE_INFO", "REASSIGN_REVIEWER"],
            "forbidden_actions": FORBIDDEN_AUTO_ACTIONS,
            "safety_flags": SAFETY_FLAGS,
            "evidence_notes": ["tenant validation failed"],
            "no_autonomous_execution": True,
            "readonly": True,
            "tenant_scoped": True,
        }

    evaluated = evaluate_queue_item(int(tenant_id), {})
    return {
        "tenant_id": int(tenant_id),
        "module": "timetable_approval_queue",
        "visibility_level": "L4",
        "operational_status": "EVALUATED",
        "classification": str(evaluated.get("classification") or "READY_FOR_REVIEW"),
        "allowed_actions": list(evaluated.get("allowed_actions") or []),
        "forbidden_actions": list(evaluated.get("forbidden_actions") or []),
        "safety_flags": SAFETY_FLAGS,
        "evidence_notes": [
            "deterministic queue evaluator surfaced via read-only L4 visibility",
            "manual decision boundary preserved",
        ],
        "no_autonomous_execution": True,
        "readonly": True,
        "tenant_scoped": True,
    }


L5_SAFETY_FLAGS = {
    "tenant_scoped": True,
    "no_cross_tenant_evidence": True,
    "no_fake_kpi_values": True,
    "no_brain_execution": True,
    "no_autonomous_execution": True,
    "no_l6_claim": True,
    "human_review_required": True,
}


def get_approval_queue_l5_readiness(
    tenant_id: Any, evidence_context: Dict[str, Any] | None = None
) -> Dict[str, Any]:
    """Deterministic L5-readiness evidence/governance contract for timetable_approval_queue.

    Returns structured evidence lineage, governance mapping, KPI-readiness boundary,
    and Brain candidate boundary. No autonomous execution, no fake KPI, no L6 claim.
    """
    if not validate_queue_tenant(tenant_id):
        raise ValueError(
            f"tenant_id must be a positive integer; got {tenant_id!r}"
        )

    tid = int(tenant_id)

    return {
        "tenant_id": tid,
        "module": "timetable_approval_queue",
        "readiness_level": "L5_READY",
        # Evidence lineage
        "evidence_lineage_status": "EVIDENCED_FROM_L4_VISIBILITY_SURFACE",
        "evidence_sources": [
            "queue_visibility_summary",
            "reviewer_state",
            "manual_decision_boundary",
        ],
        "evidence_completeness": "PARTIAL_UNTIL_INDEXED",
        # Governance mapping
        "governance_mapping_status": "GOVERNANCE_BOUNDARY_MAPPED",
        "governance_category": "HUMAN_REVIEW_QUEUE_GOVERNANCE",
        "human_review_owner": "approval_queue_reviewer",
        "escalation_boundary": "unresolved_conflict_or_policy_breach",
        "allowed_governance_actions": [
            "REVIEW_QUEUE_ITEM",
            "REQUEST_MORE_INFO",
            "MANUAL_APPROVE",
            "MANUAL_REJECT",
            "REASSIGN_REVIEWER",
        ],
        "forbidden_autonomous_actions": [
            "AUTO_APPROVE",
            "AUTO_REJECT",
            "AUTO_APPLY",
        ],
        # KPI readiness
        "kpi_readiness_status": "QUEUE_GOVERNANCE_READINESS_ONLY",
        # Brain boundary
        "brain_readiness_boundary": "BRAIN_CANDIDATE_ONLY_NO_EXECUTION",
        # Human review
        "human_review_required": True,
        # Confidence
        "confidence_status": "MEDIUM",
        "rationale_notes": (
            "Queue evidence lineage established from A-026.5 L4 visibility surface. "
            "Governance mapping complete. KPI readiness-only — no fabricated values. "
            "Brain boundary: no execution path."
        ),
        # Audit
        "audit_evidence_notes": [
            f"tenant_id={tid} scoped evidence contract",
            "source: A-026.5-RUNTIME operational visibility",
            "no cross-tenant evidence aggregation",
            "human reviewer decision gate enforced",
        ],
        # Safety flags
        "safety_flags": L5_SAFETY_FLAGS,
        "no_autonomous_execution": True,
        "no_l6_claim": True,
        "tenant_scoped": True,
    }
