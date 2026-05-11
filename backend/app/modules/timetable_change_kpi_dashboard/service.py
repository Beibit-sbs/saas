"""
Timetable Change KPI Dashboard Service Contract

L2 backend contract for KPI readiness (no frontend dashboard claims).
Backend-only readiness assessment, no actual KPI values or Brain mapping.
"""

from typing import Dict, Any

# ============================================================================
# Safety Flags
# ============================================================================

SAFETY_FLAGS = {
    "no_api_claim": True,
    "no_frontend_claim": True,
    "no_brain_claim": True,
    "no_autonomous_execution": True,
    "no_kpi_values_computed": True,
    "no_kpi_lineage_claim": True,
    "no_e2e_claim": True,
    "backend_contract_only": True,
    "target_level": "L3",
}


# ============================================================================
# Tenant Validation (Critical)
# ============================================================================

def validate_kpi_dashboard_tenant(tenant_id: Any) -> bool:
    """
    Validate tenant_id for KPI dashboard access.
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

def get_kpi_readiness_contract(tenant_id: Any) -> Dict[str, Any]:
    """
    Return KPI readiness contract (backend only, no frontend/Brain claims).

    Args:
        tenant_id: Tenant identifier for scoping

    Returns:
        Dictionary with KPI readiness status
    """
    if not validate_kpi_dashboard_tenant(tenant_id):
        return {
            "tenant_id": None,
            "module": "timetable_change_kpi_dashboard",
            "readiness_status": "TENANT_VALIDATION_FAILED",
            "error": "Invalid tenant_id",
        }

    return {
        "tenant_id": tenant_id,
        "module": "timetable_change_kpi_dashboard",
        "kpi_readiness_status": "BACKEND_CONTRACT_ONLY",
        "evidence_level": "L2",
        "target_level": "L2",
        "frontend_dashboard_claim": False,
        "kpi_values_available": False,
        "kpi_values_computed": False,
        "brain_mapping_status": "NOT_AVAILABLE",
        "brain_signal_claim": False,
        "safety_flags": SAFETY_FLAGS,
        "contract_type": "backend_kpi_readiness_assessment_only",
        "next_level_readiness": "KPI computation and lineage mapping required for L3+",
    }


def get_kpi_metadata(tenant_id: Any) -> Dict[str, Any]:
    """
    Return KPI metadata for L2 assessment (no actual values).

    Args:
        tenant_id: Tenant identifier for scoping

    Returns:
        Dictionary with KPI metadata
    """
    if not validate_kpi_dashboard_tenant(tenant_id):
        return {"error": "Invalid tenant_id"}

    return {
        "valid": True,
        "tenant_id": tenant_id,
        "module": "timetable_change_kpi_dashboard",
        "kpi_fields": [
            "proposal_count",
            "approval_rate",
            "average_review_time",
            "rejected_proposal_count",
        ],
        "values_available": False,
        "computation_required_for_l3": True,
        "safety_flags": SAFETY_FLAGS,
    }


def classify_kpi_readiness(tenant_id: Any, evidence: Any) -> Dict[str, Any]:
    """Deterministically classify KPI dashboard readiness at L3."""
    if not validate_kpi_dashboard_tenant(tenant_id):
        return {
            "tenant_id": None,
            "module": "timetable_change_kpi_dashboard",
            "maturity_level": "L3",
            "kpi_readiness_status": "KPI_BACKEND_CONTRACT_INCOMPLETE",
            "classification": "KPI_BACKEND_CONTRACT_INCOMPLETE",
            "frontend_claim": False,
            "kpi_values_available": False,
            "brain_mapping_status": "NOT_AVAILABLE",
            "safety_flags": SAFETY_FLAGS,
        }

    evidence_data = evidence if isinstance(evidence, dict) else {}
    backend_contract_ready = bool(evidence_data.get("backend_contract_ready") or evidence_data.get("backend_contract"))
    values_requested = bool(evidence_data.get("values_requested") or evidence_data.get("kpi_values_requested"))
    frontend_claimed = bool(evidence_data.get("frontend_claimed") or evidence_data.get("frontend_requested"))

    if frontend_claimed:
        status = "KPI_FRONTEND_NOT_CLAIMED"
    elif not backend_contract_ready:
        status = "KPI_BACKEND_CONTRACT_INCOMPLETE"
    elif values_requested or evidence_data.get("kpi_values_available") is True:
        status = "KPI_VALUES_NOT_AVAILABLE"
    else:
        status = "KPI_BACKEND_CONTRACT_READY"

    return {
        "tenant_id": tenant_id,
        "module": "timetable_change_kpi_dashboard",
        "maturity_level": "L3",
        "kpi_readiness_status": status,
        "classification": status,
        "frontend_claim": False,
        "frontend_dashboard_claim": False,
        "kpi_values_available": False,
        "kpi_values_computed": False,
        "brain_mapping_status": "NOT_AVAILABLE",
        "brain_signal_claim": False,
        "no_kpi_lineage_claim": True,
        "safety_flags": SAFETY_FLAGS,
        "next_recommended_step": "OPERATIONAL_VISIBILITY_SPECIFICATION",
    }


def get_kpi_dashboard_visibility_summary(tenant_id: Any) -> Dict[str, Any]:
    """Build deterministic read-only L4 visibility summary for KPI readiness."""
    if not validate_kpi_dashboard_tenant(tenant_id):
        return {
            "tenant_id": None,
            "module": "timetable_change_kpi_dashboard",
            "visibility_level": "L4",
            "operational_status": "TENANT_VALIDATION_FAILED",
            "classification": "KPI_BACKEND_CONTRACT_INCOMPLETE",
            "allowed_actions": ["REVIEW_READINESS", "VERIFY_EVIDENCE"],
            "forbidden_actions": ["AUTO_APPLY", "AUTO_APPROVE", "AUTONOMOUS_EXECUTION"],
            "safety_flags": SAFETY_FLAGS,
            "evidence_notes": ["tenant validation failed"],
            "no_autonomous_execution": True,
            "readonly": True,
            "tenant_scoped": True,
        }

    evaluated = classify_kpi_readiness(int(tenant_id), {"backend_contract_ready": True})
    return {
        "tenant_id": int(tenant_id),
        "module": "timetable_change_kpi_dashboard",
        "visibility_level": "L4",
        "operational_status": str(evaluated.get("kpi_readiness_status") or "KPI_BACKEND_CONTRACT_READY"),
        "classification": str(evaluated.get("classification") or "KPI_BACKEND_CONTRACT_READY"),
        "allowed_actions": ["REVIEW_READINESS", "VERIFY_EVIDENCE", "EXPORT_SUMMARY"],
        "forbidden_actions": ["AUTO_APPLY", "AUTO_APPROVE", "AUTONOMOUS_EXECUTION"],
        "safety_flags": SAFETY_FLAGS,
        "evidence_notes": [
            "deterministic backend KPI readiness surfaced via read-only L4 visibility",
            "no KPI values or lineage claims generated",
        ],
        "no_autonomous_execution": True,
        "readonly": True,
        "tenant_scoped": True,
    }
