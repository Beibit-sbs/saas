from __future__ import annotations

from fastapi import HTTPException
import pytest

from app.modules.admissions_crm.dependencies import require_admissions_crm_tenant


@pytest.mark.parametrize("tenant_payload", [{"id": 1}, {"id": "2"}, {"id": 9999}])
def test_require_tenant_accepts_valid_values(tenant_payload: dict) -> None:
    assert require_admissions_crm_tenant(tenant_payload) > 0


@pytest.mark.parametrize("tenant_payload", [{"id": None}, {"id": 0}, {"id": -1}, {"id": "abc"}, {}])
def test_require_tenant_rejects_invalid_values(tenant_payload: dict) -> None:
    with pytest.raises(HTTPException):
        require_admissions_crm_tenant(tenant_payload)
