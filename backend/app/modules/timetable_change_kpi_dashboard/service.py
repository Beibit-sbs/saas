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
    "no_kpi_values_computed": True,
    "no_kpi_lineage_claim": True,
    "backend_contract_only": True,
    "target_level": "L2",
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
