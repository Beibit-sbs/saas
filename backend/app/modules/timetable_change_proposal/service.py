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
    "no_kpi_lineage_claim": True,
    "no_e2e_claim": True,
    "target_level": "L3",
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


def evaluate_timetable_change_proposal(tenant_id: Any, proposal: Any) -> Dict[str, Any]:
    """Deterministically classify timetable change proposal readiness at L3."""
    if not validate_proposal_tenant(tenant_id):
        return {
            "tenant_id": None,
            "module": "timetable_change_proposal",
            "maturity_level": "L3",
            "evaluation_status": "TENANT_VALIDATION_FAILED",
            "classification": "REJECTED_INVALID_PAYLOAD",
            "missing_fields": ["tenant_id"],
            "next_required_evidence": ["VALID_TENANT"],
            "safety_flags": SAFETY_FLAGS,
        }

    if not isinstance(proposal, dict):
        return {
            "tenant_id": tenant_id,
            "module": "timetable_change_proposal",
            "maturity_level": "L3",
            "evaluation_status": "INVALID_PAYLOAD",
            "classification": "REJECTED_INVALID_PAYLOAD",
            "missing_fields": ["proposal"],
            "next_required_evidence": ["DICT_PAYLOAD"],
            "safety_flags": SAFETY_FLAGS,
        }

    required_fields = ["proposal_type", "description", "reason", "impact"]
    missing_fields = [field for field in required_fields if not proposal.get(field)]
    classification = "READY_FOR_REVIEW"
    next_required_evidence = ["REVIEW_CONTEXT"]

    if missing_fields:
        classification = "INCOMPLETE_PROPOSAL"
        next_required_evidence = missing_fields[:]
    else:
        affected_fields = [field for field in ["affected_course", "affected_room", "affected_instructor"] if proposal.get(field) is not None]
        requested_change_type = str(proposal.get("requested_change_type") or proposal.get("proposal_type") or "").upper()
        policy_review_required = bool(proposal.get("policy_review_required") or proposal.get("policy_flag"))
        if policy_review_required:
            classification = "POLICY_REVIEW_REQUIRED"
            next_required_evidence = ["POLICY_REVIEW_CLEARANCE"]
        elif requested_change_type in {"SIMULATION", "SIMULATE", "HIGH_RISK"} or proposal.get("requires_simulation") is True:
            classification = "READY_FOR_SIMULATION"
            next_required_evidence = ["SIMULATION_REQUEST"]
        else:
            classification = "READY_FOR_REVIEW"
            next_required_evidence = affected_fields or ["REVIEW_CONTEXT"]

    return {
        "tenant_id": tenant_id,
        "module": "timetable_change_proposal",
        "maturity_level": "L3",
        "evaluation_status": "EVALUATED",
        "classification": classification,
        "proposal_type": proposal.get("proposal_type") if isinstance(proposal, dict) else None,
        "missing_fields": missing_fields,
        "next_required_evidence": next_required_evidence,
        "allowed_actions": ["SUBMIT", "REVIEW", "REQUEST_MORE_INFO", "REQUEST_SIMULATION", "REJECT"],
        "forbidden_actions": ["AUTO_APPLY", "AUTO_OPTIMIZE", "AUTONOMOUS_MUTATION"],
        "safety_flags": SAFETY_FLAGS,
    }


def get_timetable_proposal_visibility_summary(tenant_id: Any) -> Dict[str, Any]:
    """Build deterministic read-only L4 visibility summary for proposal operations."""
    if not validate_proposal_tenant(tenant_id):
        return {
            "tenant_id": None,
            "module": "timetable_change_proposal",
            "visibility_level": "L4",
            "operational_status": "TENANT_VALIDATION_FAILED",
            "classification": "REJECTED_INVALID_PAYLOAD",
            "allowed_actions": ["SUBMIT", "REVIEW", "REQUEST_MORE_INFO"],
            "forbidden_actions": ["AUTO_APPLY", "AUTO_OPTIMIZE", "AUTONOMOUS_MUTATION"],
            "safety_flags": SAFETY_FLAGS,
            "evidence_notes": ["tenant validation failed"],
            "no_autonomous_execution": True,
            "readonly": True,
            "tenant_scoped": True,
        }

    evaluated = evaluate_timetable_change_proposal(int(tenant_id), {})
    return {
        "tenant_id": int(tenant_id),
        "module": "timetable_change_proposal",
        "visibility_level": "L4",
        "operational_status": str(evaluated.get("evaluation_status") or "EVALUATED"),
        "classification": str(evaluated.get("classification") or "READY_FOR_REVIEW"),
        "allowed_actions": list(evaluated.get("allowed_actions") or []),
        "forbidden_actions": list(evaluated.get("forbidden_actions") or []),
        "safety_flags": SAFETY_FLAGS,
        "evidence_notes": [
            "deterministic L3 proposal evaluator surfaced via read-only L4 visibility",
            "no mutation or apply path exposed",
        ],
        "no_autonomous_execution": True,
        "readonly": True,
        "tenant_scoped": True,
    }
