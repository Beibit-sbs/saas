"""A-023.4 minimal validation for finance/procurement/assets foundation artifacts."""

from __future__ import annotations

import importlib

import pytest

from app.modules.contracts_legal_repository import service as contracts_service
from app.modules.procurement_approval_workflow import service as procurement_service


@pytest.mark.parametrize(
    "module_name",
    [
        "app.modules.alumni_relations_ops",
        "app.modules.donations_fundraising",
        "app.modules.contracts_legal_repository.service",
        "app.modules.procurement_approval_workflow.service",
    ],
)
def test_a0234_modules_are_importable(module_name: str) -> None:
    importlib.import_module(module_name)


def test_a0234_l2_services_expose_state_and_safety_contracts() -> None:
    assert isinstance(contracts_service.CONTRACT_STATES, frozenset)
    assert {"DRAFT", "UNDER_REVIEW", "PENDING_SIGNATURE", "SIGNED", "ARCHIVED"}.issubset(
        contracts_service.CONTRACT_STATES
    )
    assert isinstance(contracts_service.SAFETY_GUARDS, frozenset)
    assert "NO_AUTOMATIC_CONTRACT_SIGNING" in contracts_service.SAFETY_GUARDS

    assert isinstance(procurement_service.WORKFLOW_STATES, frozenset)
    assert {"REQUESTED", "UNDER_REVIEW", "APPROVED", "REJECTED", "PO_READY"}.issubset(
        procurement_service.WORKFLOW_STATES
    )
    assert isinstance(procurement_service.SAFETY_GUARDS, frozenset)
    assert "NO_AUTOMATIC_PROCUREMENT_APPROVAL" in procurement_service.SAFETY_GUARDS


@pytest.mark.parametrize("tenant_id", [0, -1])
def test_a0234_l2_services_reject_non_positive_tenant(tenant_id: int) -> None:
    with pytest.raises(ValueError, match="tenant_id must be a positive integer"):
        contracts_service.list_contracts(tenant_id)

    with pytest.raises(ValueError, match="tenant_id must be a positive integer"):
        procurement_service.list_requests(tenant_id)