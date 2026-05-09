"""A-023.2 minimal validation for student lifecycle foundation artifacts."""

from __future__ import annotations

import importlib

import pytest

from app.modules.counseling_case_management import service as counseling_service
from app.modules.library_circulation import service as library_service


@pytest.mark.parametrize(
    "module_name",
    [
        "app.modules.event_registration_portal",
        "app.modules.health_services",
        "app.modules.internship_marketplace",
        "app.modules.mobile_push_gateway",
        "app.modules.notification_center",
        "app.modules.parking_enforcement",
        "app.modules.parking_permit_ops",
        "app.modules.parent_engagement",
        "app.modules.counseling_case_management.service",
        "app.modules.library_circulation.service",
    ],
)
def test_a0232_modules_are_importable(module_name: str) -> None:
    importlib.import_module(module_name)


def test_a0232_l2_services_expose_fsm_contracts() -> None:
    assert isinstance(counseling_service.CASE_STATES, frozenset)
    assert {"OPEN", "IN_PROGRESS", "RESOLVED", "CLOSED"}.issubset(counseling_service.CASE_STATES)

    assert isinstance(library_service.LOAN_STATES, frozenset)
    assert {"REQUESTED", "CHECKED_OUT", "RETURNED", "CLOSED"}.issubset(library_service.LOAN_STATES)


@pytest.mark.parametrize("tenant_id", [0, -1])
def test_a0232_l2_services_reject_non_positive_tenant(tenant_id: int) -> None:
    with pytest.raises(ValueError, match="tenant_id must be a positive integer"):
        counseling_service.list_cases(tenant_id)

    with pytest.raises(ValueError, match="tenant_id must be a positive integer"):
        library_service.list_loans(tenant_id)