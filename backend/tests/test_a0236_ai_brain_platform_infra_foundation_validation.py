"""A-023.6 minimal validation for AI/Brain/Platform/Infra foundation artifacts."""

from __future__ import annotations

import importlib

import pytest

from app.modules.ai_copilot_ops import service as ai_copilot_ops_service
from app.modules.ai_routing_control import service as ai_routing_control_service
from app.modules.developer_portal import service as developer_portal_service


@pytest.mark.parametrize(
    "module_name",
    [
        "app.modules.exam_integrity_analytics",
        "app.modules.ai_copilot_ops.service",
        "app.modules.ai_routing_control.service",
        "app.modules.developer_portal.service",
    ],
)
def test_a0236_modules_are_importable(module_name: str) -> None:
    importlib.import_module(module_name)


def test_a0236_l2_services_expose_state_and_safety_constants() -> None:
    assert isinstance(ai_copilot_ops_service.OPS_STATES, frozenset)
    assert "NO_AUTONOMOUS_EXECUTION" in ai_copilot_ops_service.SAFETY_GUARDS
    assert "NO_EXTERNAL_LLM_PROVIDER_CALLS" in ai_copilot_ops_service.SAFETY_GUARDS

    assert isinstance(ai_routing_control_service.ROUTING_STATES, frozenset)
    assert "NO_AUTONOMOUS_EXECUTION" in ai_routing_control_service.SAFETY_GUARDS
    assert "NO_EXTERNAL_LLM_PROVIDER_CALLS" in ai_routing_control_service.SAFETY_GUARDS

    assert isinstance(developer_portal_service.PORTAL_STATES, frozenset)
    assert "NO_FAKE_OBSERVABILITY_ALERTS" in developer_portal_service.SAFETY_GUARDS
    assert "NO_FAKE_KPI_DASHBOARD_VALUES" in developer_portal_service.SAFETY_GUARDS


@pytest.mark.parametrize("tenant_id", [0, -1])
def test_a0236_l2_services_reject_non_positive_tenant(tenant_id: int) -> None:
    with pytest.raises(ValueError, match="tenant_id must be a positive integer"):
        ai_copilot_ops_service.list_ops_profiles(tenant_id)

    with pytest.raises(ValueError, match="tenant_id must be a positive integer"):
        ai_routing_control_service.list_routing_policies(tenant_id)

    with pytest.raises(ValueError, match="tenant_id must be a positive integer"):
        developer_portal_service.list_portal_channels(tenant_id)