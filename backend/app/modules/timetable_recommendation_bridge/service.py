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
    "target_level": "L2",
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
