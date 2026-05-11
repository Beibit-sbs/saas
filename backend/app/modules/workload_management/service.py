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
    "no_kpi_lineage_claim": True,
    "no_e2e_claim": True,
    "target_level": "L3",
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


def evaluate_workload_plan(tenant_id: Any, workload_payload: Any) -> Dict[str, Any]:
    """Deterministically classify workload planning at L3."""
    if not validate_workload_tenant(tenant_id):
        return {
            "tenant_id": None,
            "module": "workload_management",
            "maturity_level": "L3",
            "evaluation_status": "TENANT_VALIDATION_FAILED",
            "classification": "WORKLOAD_INPUT_INCOMPLETE",
            "risk_level": "LOW",
            "next_required_evidence": ["VALID_TENANT"],
            "safety_flags": SAFETY_FLAGS,
        }

    payload = workload_payload if isinstance(workload_payload, dict) else {}
    required_fields = ["workload_type", "units"]
    missing_fields = [field for field in required_fields if payload.get(field) in (None, "")]
    overload_risk = bool(payload.get("overload_risk") or payload.get("capacity_exceeded"))
    policy_review_required = bool(payload.get("policy_review_required") or payload.get("policy_flag"))
    has_assignment_context = bool(payload.get("assignment_context") or payload.get("assignment_plan"))

    if missing_fields:
        classification = "WORKLOAD_INPUT_INCOMPLETE"
        risk_level = "LOW"
        next_required_evidence = missing_fields[:]
    elif policy_review_required:
        classification = "POLICY_REVIEW_REQUIRED"
        risk_level = "HIGH"
        next_required_evidence = ["POLICY_REVIEW_CLEARANCE"]
    elif overload_risk:
        classification = "OVERLOAD_RISK_REVIEW_REQUIRED"
        risk_level = "HIGH"
        next_required_evidence = ["CAPACITY_REVIEW"]
    elif has_assignment_context:
        classification = "READY_FOR_ASSIGNMENT_PLANNING"
        risk_level = "MEDIUM"
        next_required_evidence = ["ASSIGNMENT_PLAN_REVIEW"]
    else:
        classification = "READY_FOR_HUMAN_REVIEW"
        risk_level = "MEDIUM"
        next_required_evidence = ["HUMAN_REVIEW_CONTEXT"]

    return {
        "tenant_id": tenant_id,
        "module": "workload_management",
        "maturity_level": "L3",
        "evaluation_status": "EVALUATED",
        "classification": classification,
        "risk_level": risk_level,
        "allowed_actions": ["ASSESS", "CLASSIFY", "REVIEW"],
        "forbidden_actions": ["AUTO_ASSIGN", "AUTO_OVERRIDE_CONSTRAINTS", "AUTO_MUTATE_PAYROLL", "AUTO_DISTRIBUTE_WORKLOAD"],
        "next_required_evidence": next_required_evidence,
        "safety_flags": SAFETY_FLAGS,
    }


def get_workload_visibility_summary(tenant_id: Any) -> Dict[str, Any]:
    """Build deterministic read-only L4 visibility summary for workload operations."""
    if not validate_workload_tenant(tenant_id):
        return {
            "tenant_id": None,
            "module": "workload_management",
            "visibility_level": "L4",
            "operational_status": "TENANT_VALIDATION_FAILED",
            "classification": "WORKLOAD_INPUT_INCOMPLETE",
            "allowed_actions": ["ASSESS", "CLASSIFY", "REVIEW"],
            "forbidden_actions": [
                "AUTO_ASSIGN",
                "AUTO_OVERRIDE_CONSTRAINTS",
                "AUTO_MUTATE_PAYROLL",
                "AUTO_DISTRIBUTE_WORKLOAD",
            ],
            "safety_flags": SAFETY_FLAGS,
            "evidence_notes": ["tenant validation failed"],
            "no_autonomous_execution": True,
            "readonly": True,
            "tenant_scoped": True,
        }

    evaluated = evaluate_workload_plan(int(tenant_id), {"workload_type": "teaching", "units": 1})
    return {
        "tenant_id": int(tenant_id),
        "module": "workload_management",
        "visibility_level": "L4",
        "operational_status": str(evaluated.get("evaluation_status") or "EVALUATED"),
        "classification": str(evaluated.get("classification") or "READY_FOR_HUMAN_REVIEW"),
        "allowed_actions": list(evaluated.get("allowed_actions") or []),
        "forbidden_actions": list(evaluated.get("forbidden_actions") or []),
        "safety_flags": SAFETY_FLAGS,
        "evidence_notes": [
            "deterministic workload classifier surfaced via read-only L4 visibility",
            "no payroll or assignment mutation exposed",
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


def get_workload_l5_readiness(
    tenant_id: Any, evidence_context: Dict[str, Any] | None = None
) -> Dict[str, Any]:
    """Deterministic L5-readiness evidence/governance contract for workload_management.

    Returns evidence lineage, governance mapping, KPI-readiness boundary, and Brain
    candidate boundary. No assignment automation, no payroll mutation, no L6 claim.
    """
    if not validate_workload_tenant(tenant_id):
        raise ValueError(
            f"tenant_id must be a positive integer; got {tenant_id!r}"
        )

    tid = int(tenant_id)

    return {
        "tenant_id": tid,
        "module": "workload_management",
        "readiness_level": "L5_READY",
        # Evidence lineage
        "evidence_lineage_status": "EVIDENCED_FROM_L4_VISIBILITY_SURFACE",
        "evidence_sources": [
            "workload_visibility_summary",
            "workload_risk_classification",
            "assignment_boundary",
        ],
        "evidence_completeness": "PARTIAL_UNTIL_INDEXED",
        # Governance mapping
        "governance_mapping_status": "GOVERNANCE_BOUNDARY_MAPPED",
        "governance_category": "WORKLOAD_GOVERNANCE",
        "human_review_owner": "workload_planning_reviewer",
        "escalation_boundary": "high_risk_workload_or_policy_conflict",
        "allowed_governance_actions": [
            "REVIEW_WORKLOAD_EVIDENCE",
            "REQUEST_CAPACITY_REVIEW",
            "MARK_FOR_MANUAL_ASSIGNMENT_PLANNING",
        ],
        "forbidden_autonomous_actions": [
            "AUTO_ASSIGN",
            "AUTO_OVERRIDE_CONSTRAINTS",
            "AUTO_MUTATE_PAYROLL",
        ],
        # KPI readiness
        "kpi_readiness_status": "WORKLOAD_EVIDENCE_READY_FOR_GOVERNANCE_MAPPING",
        # Brain boundary
        "brain_readiness_boundary": "BRAIN_CANDIDATE_ONLY_NO_EXECUTION",
        # Human review
        "human_review_required": True,
        # Confidence
        "confidence_status": "MEDIUM",
        "rationale_notes": (
            "Workload evidence lineage established from A-026.5 L4 visibility surface. "
            "Governance mapping complete. No fake workload KPI values. "
            "Brain boundary: candidate envelope only, execution forbidden."
        ),
        # Audit
        "audit_evidence_notes": [
            f"tenant_id={tid} scoped workload evidence contract",
            "source: A-026.5-RUNTIME workload readiness visibility",
            "no cross-tenant workload aggregation",
            "no payroll or assignment mutation",
        ],
        # Safety flags
        "safety_flags": L5_SAFETY_FLAGS,
        "no_autonomous_execution": True,
        "no_l6_claim": True,
        "tenant_scoped": True,
    }
