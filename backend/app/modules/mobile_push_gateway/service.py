"""L2 foundation service contract for mobile_push_gateway (A-026.7.L1L2)."""

from typing import Any, Mapping

MODULE_NAME = "mobile_push_gateway"
TARGET_LEVEL = "L2"
CONTRACT_VERSION = "A-026.7.L1L2"

CONTRACT_STATUS = "FOUNDATION_CONTRACT_READY"
NEXT_MATURITY_GAP = "deterministic_service_logic_needed"

ALLOWED_ACTIONS = [
    "VALIDATE_TENANT",
    "READ_FOUNDATION_CONTRACT",
    "ASSESS_FOUNDATION_READINESS",
]

FORBIDDEN_ACTIONS = [
    "CREATE_API_ENDPOINT",
    "CREATE_FRONTEND_PAGE",
    "COMPUTE_KPI_VALUE",
    "MAP_BRAIN_SIGNAL",
    "EXECUTE_AUTONOMOUS_ACTION",
    "CALL_EXTERNAL_PROVIDER",
    "MUTATE_DATABASE",
    "PUBLISH_EVENT",
]

REQUIRED_EVIDENCE = [
    "service_contract_defined",
    "tenant_fail_closed_validation",
    "deterministic_contract_output",
    "anti_inflation_safety_flags",
]

SAFETY_FLAGS = {
    "no_api_claim": True,
    "no_frontend_claim": True,
    "no_kpi_claim": True,
    "no_brain_claim": True,
    "no_autonomous_execution": True,
    "no_external_provider_call": True,
    "no_l3_claim": True,
    "no_l4_claim": True,
    "no_l5_claim": True,
    "no_l6_claim": True,
}


def validate_tenant_id(tenant_id: Any) -> int:
    """Fail-closed tenant validator for L2 foundation contracts."""
    if tenant_id is None:
        raise ValueError("tenant_id is required")
    if not isinstance(tenant_id, int):
        raise ValueError("tenant_id must be an integer")
    if tenant_id <= 0:
        raise ValueError("tenant_id must be a positive integer")
    return tenant_id


def get_mobile_push_gateway_foundation_contract(
    tenant_id: int,
    payload: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Return a deterministic L2 foundation service contract for this module."""
    normalized_tenant_id = validate_tenant_id(tenant_id)
    normalized_payload = dict(payload) if isinstance(payload, Mapping) else {}

    return {
        "tenant_id": normalized_tenant_id,
        "module": MODULE_NAME,
        "maturity_level": TARGET_LEVEL,
        "contract_version": CONTRACT_VERSION,
        "contract_status": CONTRACT_STATUS,
        "service_contract_ready": True,
        "tenant_scoped": True,
        "deterministic": True,
        "allowed_actions": list(ALLOWED_ACTIONS),
        "forbidden_actions": list(FORBIDDEN_ACTIONS),
        "required_evidence": list(REQUIRED_EVIDENCE),
        "next_maturity_gap": NEXT_MATURITY_GAP,
        "payload_keys": sorted(normalized_payload.keys()),
        "safety_flags": dict(SAFETY_FLAGS),
    }
