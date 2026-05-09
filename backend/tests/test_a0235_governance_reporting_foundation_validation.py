"""A-023.5 minimal validation for governance/reporting foundation artifacts."""

from __future__ import annotations

import importlib

import pytest

from app.modules.ai_cost_governance import service as ai_cost_governance_service


@pytest.mark.parametrize(
    "module_name",
    [
        "app.modules.publication_registry",
        "app.modules.timetable_approval_queue",
        "app.modules.timetable_change_kpi_dashboard",
        "app.modules.ai_cost_governance.service",
    ],
)
def test_a0235_modules_are_importable(module_name: str) -> None:
    importlib.import_module(module_name)


def test_a0235_l2_service_exposes_state_and_safety_contracts() -> None:
    assert isinstance(ai_cost_governance_service.POLICY_STATES, frozenset)
    assert {"DRAFT", "ACTIVE", "SUSPENDED", "RETIRED"}.issubset(
        ai_cost_governance_service.POLICY_STATES
    )

    assert isinstance(ai_cost_governance_service.SAFETY_GUARDS, frozenset)
    assert "NO_FAKE_MINISTRY_SUBMISSION" in ai_cost_governance_service.SAFETY_GUARDS
    assert "NO_FAKE_COMPLIANCE_SCORE" in ai_cost_governance_service.SAFETY_GUARDS
    assert "NO_SYNTHETIC_KPI_DASHBOARD_VALUES" in ai_cost_governance_service.SAFETY_GUARDS


@pytest.mark.parametrize("tenant_id", [0, -1])
def test_a0235_l2_service_rejects_non_positive_tenant(tenant_id: int) -> None:
    with pytest.raises(ValueError, match="tenant_id must be a positive integer"):
        ai_cost_governance_service.list_policies(tenant_id)