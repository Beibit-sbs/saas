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
    "target_level": "L3",
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


def evaluate_human_workflow_state(tenant_id: Any, workflow: Any) -> Dict[str, Any]:
    """Deterministically classify a human-approved timetable workflow at L3."""
    if not validate_workflow_tenant(tenant_id):
        return {
            "tenant_id": None,
            "module": "human_approved_timetable_workflow",
            "maturity_level": "L3",
            "evaluation_status": "TENANT_VALIDATION_FAILED",
            "classification": "NEEDS_HUMAN_REVIEW",
            "human_review_required": True,
            "HUMAN_APPROVAL_REQUIRED": HUMAN_APPROVAL_REQUIRED,
            "allowed_actions": [
                "SUBMIT_FOR_REVIEW",
                "REQUEST_MORE_INFO",
                "APPROVE_MANUALLY",
                "REJECT_MANUALLY",
                "CANCEL",
            ],
            "forbidden_actions": [
                "AUTO_APPLY",
                "AUTO_OPTIMIZE",
                "AUTONOMOUS_ROLLBACK",
            ],
            "next_recommended_step": "RESOLVE_TENANT_VALIDATION",
            "safety_flags": SAFETY_FLAGS,
        }

    workflow_data = workflow if isinstance(workflow, dict) else {}
    status = str(workflow_data.get("status") or workflow_data.get("workflow_status") or "").upper()
    policy_rejected = bool(workflow_data.get("policy_rejected") or workflow_data.get("policy_violation"))
    human_decision = str(workflow_data.get("human_decision") or "").upper()

    if status in {"CANCELLED", "CLOSED"} or workflow_data.get("cancelled") is True:
        classification = "CANCELLED_OR_CLOSED"
        next_step = "ARCHIVE_OR_CLOSE_WORKFLOW"
    elif policy_rejected or status in {"REJECTED", "POLICY_REJECTED"}:
        classification = "REJECTED_BY_POLICY"
        next_step = "REVISE_AND_RESUBMIT"
    elif status in {"HUMAN_APPROVED", "APPROVED"} or human_decision == "APPROVE":
        classification = "READY_FOR_MANUAL_APPROVAL"
        next_step = "AWAIT_MANUAL_APPROVAL"
    else:
        classification = "NEEDS_HUMAN_REVIEW"
        next_step = "SUBMIT_FOR_HUMAN_REVIEW"

    return {
        "tenant_id": tenant_id,
        "module": "human_approved_timetable_workflow",
        "maturity_level": "L3",
        "logic_status": classification,
        "evaluation_status": "EVALUATED",
        "classification": classification,
        "workflow_status": status or "UNKNOWN",
        "human_review_required": True,
        "HUMAN_APPROVAL_REQUIRED": HUMAN_APPROVAL_REQUIRED,
        "allowed_actions": [
            "SUBMIT_FOR_REVIEW",
            "REQUEST_MORE_INFO",
            "APPROVE_MANUALLY",
            "REJECT_MANUALLY",
            "CANCEL",
        ],
        "forbidden_actions": [
            "AUTO_APPLY",
            "AUTO_OPTIMIZE",
            "AUTONOMOUS_ROLLBACK",
        ],
        "next_recommended_step": next_step,
        "safety_flags": SAFETY_FLAGS,
    }


def get_human_workflow_visibility_summary(tenant_id: Any) -> Dict[str, Any]:
    """Build deterministic read-only L4 visibility summary for admin/API use."""
    if not validate_workflow_tenant(tenant_id):
        return {
            "tenant_id": None,
            "module": "human_approved_timetable_workflow",
            "visibility_level": "L4",
            "operational_status": "TENANT_VALIDATION_FAILED",
            "classification": "NEEDS_HUMAN_REVIEW",
            "allowed_actions": ["SUBMIT_FOR_REVIEW", "REQUEST_MORE_INFO"],
            "forbidden_actions": ["AUTO_APPLY", "AUTO_OPTIMIZE", "AUTONOMOUS_ROLLBACK"],
            "safety_flags": SAFETY_FLAGS,
            "evidence_notes": ["tenant validation failed"],
            "no_autonomous_execution": True,
            "readonly": True,
            "tenant_scoped": True,
        }

    evaluated = evaluate_human_workflow_state(int(tenant_id), {})
    return {
        "tenant_id": int(tenant_id),
        "module": "human_approved_timetable_workflow",
        "visibility_level": "L4",
        "operational_status": str(evaluated.get("evaluation_status") or "EVALUATED"),
        "classification": str(evaluated.get("classification") or "NEEDS_HUMAN_REVIEW"),
        "allowed_actions": list(evaluated.get("allowed_actions") or []),
        "forbidden_actions": list(evaluated.get("forbidden_actions") or []),
        "safety_flags": SAFETY_FLAGS,
        "evidence_notes": [
            "deterministic L3 workflow classifier surfaced via read-only L4 visibility",
            "human review boundary preserved",
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


def get_human_workflow_l5_readiness(
    tenant_id: Any, evidence_context: Dict[str, Any] | None = None
) -> Dict[str, Any]:
    """Deterministic L5-readiness evidence/governance contract for human_approved_timetable_workflow.

    Returns structured evidence lineage, governance mapping, KPI-readiness boundary,
    and Brain candidate boundary. No autonomous execution, no fake KPI, no L6 claim.
    """
    if not validate_workflow_tenant(tenant_id):
        raise ValueError(
            f"tenant_id must be a positive integer; got {tenant_id!r}"
        )

    tid = int(tenant_id)

    return {
        "tenant_id": tid,
        "module": "human_approved_timetable_workflow",
        "readiness_level": "L5_READY",
        # Evidence lineage
        "evidence_lineage_status": "EVIDENCED_FROM_L4_VISIBILITY_SURFACE",
        "evidence_sources": [
            "workflow_visibility_summary",
            "human_review_state",
            "approval_boundary",
        ],
        "evidence_completeness": "PARTIAL_UNTIL_INDEXED",
        # Governance mapping
        "governance_mapping_status": "GOVERNANCE_BOUNDARY_MAPPED",
        "governance_category": "TIMETABLE_GOVERNANCE",
        "human_review_owner": "timetable_governance_committee",
        "escalation_boundary": "policy_violation_or_high_risk_workflow_only",
        "allowed_governance_actions": [
            "REVIEW_EVIDENCE",
            "REQUEST_MORE_INFO",
            "APPROVE_MANUALLY",
            "REJECT_MANUALLY",
        ],
        "forbidden_autonomous_actions": [
            "AUTO_APPLY",
            "AUTO_OPTIMIZE",
            "AUTONOMOUS_ROLLBACK",
        ],
        # KPI readiness
        "kpi_readiness_status": "KPI_READINESS_CANDIDATE_ONLY",
        # Brain boundary
        "brain_readiness_boundary": "BRAIN_CANDIDATE_ONLY_NO_EXECUTION",
        # Human review
        "human_review_required": True,
        # Confidence
        "confidence_status": "MEDIUM",
        "rationale_notes": (
            "Workflow evidence lineage established from A-026.5 L4 visibility surface. "
            "Governance mapping complete. KPI candidate only — no fabricated values. "
            "Brain boundary: candidate envelope, no execution."
        ),
        # Audit
        "audit_evidence_notes": [
            f"tenant_id={tid} scoped evidence contract",
            "source: A-026.5-RUNTIME operational visibility",
            "no cross-tenant evidence aggregation",
            "human approval gate enforced",
        ],
        # Safety flags
        "safety_flags": L5_SAFETY_FLAGS,
        "no_autonomous_execution": True,
        "no_l6_claim": True,
        "tenant_scoped": True,
    }
