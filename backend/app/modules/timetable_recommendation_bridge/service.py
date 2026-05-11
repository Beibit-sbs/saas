"""
Timetable Recommendation Bridge Service Contract

L2 deterministic service contract for recommendation envelope.
No AI provider calls, no automatic recommendations, no autonomous execution.
"""

from typing import Dict, Any

# ============================================================================
# Constants
# ============================================================================

RECOMMENDATION_SOURCE = {
    "SIMULATION_ANALYSIS": "Analysis derived from simulation module",
    "HISTORICAL_PATTERNS": "Patterns extracted from historical data",
    "PENDING": "Recommendation not yet available",
}

BRIDGE_MODE = "DETERMINISTIC_ENVELOPE_ONLY"
NO_AI_PROVIDER_CALLS = True

# ============================================================================
# Safety Flags
# ============================================================================

SAFETY_FLAGS = {
    "no_api_claim": True,
    "no_frontend_claim": True,
    "no_brain_claim": True,
    "no_ai_provider_calls": True,
    "no_autonomous_recommendation_execution": True,
    "no_autonomous_execution": True,
    "no_kpi_lineage_claim": True,
    "no_e2e_claim": True,
    "target_level": "L3",
}


# ============================================================================
# Tenant Validation (Critical)
# ============================================================================

def validate_bridge_tenant(tenant_id: Any) -> bool:
    """
    Validate tenant_id for bridge access.
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

def create_recommendation_envelope(tenant_id: Any, simulation_result: Any = None) -> Dict[str, Any]:
    """
    Create deterministic recommendation envelope based on simulation result.
    Envelope only — no autonomous recommendations or AI calls.

    Args:
        tenant_id: Tenant identifier for scoping
        simulation_result: Optional simulation result to derive from

    Returns:
        Dictionary with recommendation envelope
    """
    if not validate_bridge_tenant(tenant_id):
        return {
            "tenant_id": None,
            "module": "timetable_recommendation_bridge",
            "readiness_status": "TENANT_VALIDATION_FAILED",
            "error": "Invalid tenant_id",
        }

    return {
        "tenant_id": tenant_id,
        "module": "timetable_recommendation_bridge",
        "recommendation_status": "ENVELOPE_READY",
        "evidence_level": "L2",
        "target_level": "L2",
        "bridge_mode": BRIDGE_MODE,
        "source": "SIMULATION_ANALYSIS" if simulation_result else "PENDING",
        "recommendation_fields": {
            "tenant_id": tenant_id,
            "source": str,
            "confidence": float,  # type hint only, no values filled
            "applicable_to_proposal_id": int,
        },
        "safety_flags": SAFETY_FLAGS,
        "note": "Bridge provides envelope only, no autonomous execution",
    }


def get_bridge_readiness_contract(tenant_id: Any) -> Dict[str, Any]:
    """
    Return bridge L2 readiness contract.

    Args:
        tenant_id: Tenant identifier for scoping

    Returns:
        Dictionary with bridge readiness status
    """
    if not validate_bridge_tenant(tenant_id):
        return {
            "tenant_id": None,
            "module": "timetable_recommendation_bridge",
            "readiness_status": "TENANT_VALIDATION_FAILED",
            "error": "Invalid tenant_id",
        }

    return {
        "tenant_id": tenant_id,
        "module": "timetable_recommendation_bridge",
        "readiness_status": "L2_CONTRACT_READY",
        "evidence_level": "L2",
        "target_level": "L2",
        "bridge_mode": BRIDGE_MODE,
        "ai_provider_calls": NO_AI_PROVIDER_CALLS,
        "valid_sources": list(RECOMMENDATION_SOURCE.keys()),
        "safety_flags": SAFETY_FLAGS,
        "contract_type": "deterministic_envelope_bridge",
    }


def evaluate_recommendation_bridge(tenant_id: Any, simulation_result: Any) -> Dict[str, Any]:
    """Deterministically classify recommendation bridge readiness at L3."""
    if not validate_bridge_tenant(tenant_id):
        return {
            "tenant_id": None,
            "module": "timetable_recommendation_bridge",
            "maturity_level": "L3",
            "bridge_status": "TENANT_VALIDATION_FAILED",
            "classification": "RECOMMENDATION_NOT_READY",
            "BRIDGE_MODE": BRIDGE_MODE,
            "safety_flags": SAFETY_FLAGS,
        }

    result = simulation_result if isinstance(simulation_result, dict) else {}
    simulation_status = str(result.get("readiness_status") or result.get("simulation_status") or result.get("classification") or "").upper()
    policy_review_required = bool(result.get("policy_review_required") or result.get("requires_policy_review"))
    missing_inputs = [field for field in ["proposal_id", "simulation_type"] if result.get(field) in (None, "")]

    if missing_inputs:
        classification = "RECOMMENDATION_BLOCKED_BY_INCOMPLETE_SIMULATION"
        next_step = "COMPLETE_SIMULATION_INPUTS"
    elif policy_review_required or simulation_status in {"CONFLICT_DETECTED", "SIMULATION_REQUIRES_POLICY_REVIEW"}:
        classification = "RECOMMENDATION_REQUIRES_POLICY_REVIEW"
        next_step = "POLICY_REVIEW"
    elif simulation_status in {"READY_FOR_APPROVAL", "SIMULATION_RESULT_READY_FOR_APPROVAL", "READY"}:
        classification = "RECOMMENDATION_READY_FOR_HUMAN_REVIEW"
        next_step = "SUBMIT_FOR_HUMAN_REVIEW"
    else:
        classification = "RECOMMENDATION_NOT_READY"
        next_step = "COLLECT_ADDITIONAL_EVIDENCE"

    recommendation_envelope = {
        "tenant_id": tenant_id,
        "module": "timetable_recommendation_bridge",
        "bridge_mode": BRIDGE_MODE,
        "recommendation_source": "SIMULATION_ANALYSIS" if result else "PENDING",
        "simulation_status": simulation_status or "UNKNOWN",
        "next_recommended_step": next_step,
    }

    return {
        "tenant_id": tenant_id,
        "module": "timetable_recommendation_bridge",
        "maturity_level": "L3",
        "bridge_status": "EVALUATED",
        "classification": classification,
        "BRIDGE_MODE": BRIDGE_MODE,
        "recommendation_envelope": recommendation_envelope,
        "allowed_actions": ["PREVIEW", "REVIEW", "REQUEST_MORE_INFO"],
        "forbidden_actions": ["AUTO_RECOMMEND", "AUTO_APPLY", "AI_PROVIDER_CALL"],
        "next_recommended_step": next_step,
        "safety_flags": SAFETY_FLAGS,
    }
