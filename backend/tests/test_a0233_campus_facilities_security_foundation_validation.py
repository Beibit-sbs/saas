"""A-023.3 minimal validation for campus/facilities/security foundation artifacts."""

from __future__ import annotations

import importlib

import pytest

from app.modules.federation_management import service as federation_service
from app.modules.health_services import service as health_service
from app.modules.local_user_management import service as local_user_service
from app.modules.platform_health import service as platform_health_service


@pytest.mark.parametrize(
    "module_name",
    [
        "app.modules.lab_operations",
        "app.modules.records_hub",
        "app.modules.federation_management.service",
        "app.modules.health_services.service",
        "app.modules.local_user_management.service",
        "app.modules.platform_health.service",
    ],
)
def test_a0233_modules_are_importable(module_name: str) -> None:
    importlib.import_module(module_name)


def test_a0233_l2_services_expose_state_contracts() -> None:
    assert isinstance(federation_service.FEDERATION_STATES, frozenset)
    assert {"DRAFT", "ACTIVE", "RETIRED"}.issubset(federation_service.FEDERATION_STATES)

    assert isinstance(health_service.SERVICE_STATES, frozenset)
    assert {"INTAKE", "SCHEDULED", "IN_SERVICE", "COMPLETED", "REFERRED"}.issubset(
        health_service.SERVICE_STATES
    )

    assert isinstance(local_user_service.ACCOUNT_STATES, frozenset)
    assert {"ACTIVE", "SUSPENDED", "ARCHIVED"}.issubset(local_user_service.ACCOUNT_STATES)

    assert isinstance(platform_health_service.HEALTH_STATES, frozenset)
    assert {"HEALTHY", "DEGRADED", "OUTAGE"}.issubset(platform_health_service.HEALTH_STATES)


@pytest.mark.parametrize("tenant_id", [0, -1])
def test_a0233_l2_services_reject_non_positive_tenant(tenant_id: int) -> None:
    with pytest.raises(ValueError, match="tenant_id must be a positive integer"):
        federation_service.list_identity_providers(tenant_id)

    with pytest.raises(ValueError, match="tenant_id must be a positive integer"):
        health_service.list_service_cases(tenant_id)

    with pytest.raises(ValueError, match="tenant_id must be a positive integer"):
        local_user_service.list_local_users(tenant_id)

    with pytest.raises(ValueError, match="tenant_id must be a positive integer"):
        platform_health_service.list_health_signals(tenant_id)