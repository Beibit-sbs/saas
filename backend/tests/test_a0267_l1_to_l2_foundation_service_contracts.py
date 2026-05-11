"""A-026.7.L1L2 targeted tests for L1->L2 foundation service contracts."""

from __future__ import annotations

import importlib
import inspect
from typing import Any

import pytest

SELECTED_MODULES = [
    "alumni_relations_ops",
    "digital_certificates",
    "donations_fundraising",
    "event_registration_portal",
    "exam_integrity_analytics",
    "internship_marketplace",
    "lab_operations",
    "lms_assessment_center",
    "mobile_push_gateway",
    "parent_engagement",
    "parking_enforcement",
    "parking_permit_ops",
    "publication_registry",
    "records_hub",
    "research_projects",
    "student_success_analytics",
]

EXPECTED_SAFETY_FLAGS = {
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

FORBIDDEN_SOURCE_TOKENS = [
    "APIRouter",
    "@router",
    "@app.get",
    "@app.post",
    "publish_event",
    "brain_signal",
    "execute_brain",
    "send_email",
    "send_sms",
    "push_provider",
    "auto_apply",
    "auto_approve",
    "auto_assign",
    "autonomous_decision",
]


def _load_service(module_name: str):
    return importlib.import_module(f"app.modules.{module_name}.service")


def _foundation_fn_name(module_name: str) -> str:
    return f"get_{module_name}_foundation_contract"


# ============================================================================
# Group 1: Import validation
# ============================================================================

@pytest.mark.parametrize("module_name", SELECTED_MODULES)
def test_a0267_import_validation(module_name: str) -> None:
    service = _load_service(module_name)
    assert service is not None


@pytest.mark.parametrize("module_name", SELECTED_MODULES)
def test_a0267_required_functions_exist_and_callable(module_name: str) -> None:
    service = _load_service(module_name)
    foundation_fn_name = _foundation_fn_name(module_name)
    assert hasattr(service, "validate_tenant_id")
    assert callable(getattr(service, "validate_tenant_id"))
    assert hasattr(service, foundation_fn_name)
    assert callable(getattr(service, foundation_fn_name))


# ============================================================================
# Group 2: Tenant fail-closed validation
# ============================================================================

@pytest.mark.parametrize("module_name", SELECTED_MODULES)
def test_a0267_tenant_none_rejected(module_name: str) -> None:
    service = _load_service(module_name)
    with pytest.raises(ValueError):
        service.validate_tenant_id(None)


@pytest.mark.parametrize("module_name", SELECTED_MODULES)
def test_a0267_tenant_zero_rejected(module_name: str) -> None:
    service = _load_service(module_name)
    with pytest.raises(ValueError):
        service.validate_tenant_id(0)


@pytest.mark.parametrize("module_name", SELECTED_MODULES)
def test_a0267_tenant_negative_rejected(module_name: str) -> None:
    service = _load_service(module_name)
    with pytest.raises(ValueError):
        service.validate_tenant_id(-1)


@pytest.mark.parametrize("module_name", SELECTED_MODULES)
def test_a0267_tenant_positive_accepted(module_name: str) -> None:
    service = _load_service(module_name)
    assert service.validate_tenant_id(1) == 1


# ============================================================================
# Group 3: Contract output validation
# ============================================================================

@pytest.mark.parametrize("module_name", SELECTED_MODULES)
def test_a0267_contract_output_required_fields(module_name: str) -> None:
    service = _load_service(module_name)
    fn = getattr(service, _foundation_fn_name(module_name))
    contract = fn(tenant_id=1, payload={"z": 1, "a": 2})

    assert isinstance(contract, dict)
    assert contract["tenant_id"] == 1
    assert contract["module"] == module_name
    assert contract["maturity_level"] == "L2"
    assert contract["contract_status"] == "FOUNDATION_CONTRACT_READY"
    assert contract["service_contract_ready"] is True
    assert contract["tenant_scoped"] is True
    assert contract["deterministic"] is True
    assert contract["next_maturity_gap"] == "deterministic_service_logic_needed"
    assert contract["payload_keys"] == ["a", "z"]
    assert isinstance(contract["allowed_actions"], list)
    assert isinstance(contract["forbidden_actions"], list)
    assert isinstance(contract["required_evidence"], list)


# ============================================================================
# Group 4: Safety flags validation
# ============================================================================

@pytest.mark.parametrize("module_name", SELECTED_MODULES)
def test_a0267_safety_flags_are_strict(module_name: str) -> None:
    service = _load_service(module_name)
    fn = getattr(service, _foundation_fn_name(module_name))
    contract = fn(tenant_id=1, payload=None)

    assert contract["safety_flags"] == EXPECTED_SAFETY_FLAGS


# ============================================================================
# Group 5: Determinism validation
# ============================================================================

@pytest.mark.parametrize("module_name", SELECTED_MODULES)
def test_a0267_determinism_same_input_same_output(module_name: str) -> None:
    service = _load_service(module_name)
    fn = getattr(service, _foundation_fn_name(module_name))
    payload: dict[str, Any] = {"k2": "v2", "k1": "v1"}

    first = fn(tenant_id=7, payload=payload)
    second = fn(tenant_id=7, payload=payload)

    assert first == second


# ============================================================================
# Group 6: Anti-inflation validation
# ============================================================================

@pytest.mark.parametrize("module_name", SELECTED_MODULES)
def test_a0267_no_endpoint_or_provider_tokens_in_service_source(module_name: str) -> None:
    service = _load_service(module_name)
    source = inspect.getsource(service)

    for token in FORBIDDEN_SOURCE_TOKENS:
        assert token not in source


@pytest.mark.parametrize("module_name", SELECTED_MODULES)
def test_a0267_contract_enforces_no_l3_plus_claims(module_name: str) -> None:
    service = _load_service(module_name)
    fn = getattr(service, _foundation_fn_name(module_name))
    contract = fn(tenant_id=1, payload={})

    flags = contract["safety_flags"]
    assert flags["no_l3_claim"] is True
    assert flags["no_l4_claim"] is True
    assert flags["no_l5_claim"] is True
    assert flags["no_l6_claim"] is True
    assert "CREATE_API_ENDPOINT" in contract["forbidden_actions"]
    assert "CREATE_FRONTEND_PAGE" in contract["forbidden_actions"]
    assert "COMPUTE_KPI_VALUE" in contract["forbidden_actions"]
    assert "MAP_BRAIN_SIGNAL" in contract["forbidden_actions"]
    assert "EXECUTE_AUTONOMOUS_ACTION" in contract["forbidden_actions"]
    assert "CALL_EXTERNAL_PROVIDER" in contract["forbidden_actions"]
