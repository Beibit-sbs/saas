"""A-023.1.B1 minimal validation for L2 foundation service artifacts.

These checks are intentionally narrow: importability, exposed FSM contracts,
and tenant guard behavior only.
"""

from __future__ import annotations

import pytest

from app.modules.accreditation_compliance import service as accreditation_service
from app.modules.research_grants import service as grants_service


def test_a0231_services_import_and_expose_fsm_sets() -> None:
    assert isinstance(grants_service.GRANT_STATES, frozenset)
    assert "DRAFT" in grants_service.GRANT_STATES
    assert "CLOSED" in grants_service.GRANT_STATES

    assert isinstance(accreditation_service.CYCLE_STATES, frozenset)
    assert "PLANNED" in accreditation_service.CYCLE_STATES
    assert "ACCREDITED" in accreditation_service.CYCLE_STATES


@pytest.mark.parametrize("tenant_id", [0, -1])
def test_a0231_services_reject_non_positive_tenant_ids(tenant_id: int) -> None:
    with pytest.raises(ValueError, match="tenant_id must be a positive integer"):
        grants_service.list_grants(tenant_id)

    with pytest.raises(ValueError, match="tenant_id must be a positive integer"):
        accreditation_service.list_bodies(tenant_id)