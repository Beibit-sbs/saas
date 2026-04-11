from __future__ import annotations

import pytest
from fastapi import HTTPException

from app.modules.billing import service as billing_service


def test_get_tenant_subscription_fails_closed_when_db_only_and_database_unavailable(monkeypatch) -> None:
    monkeypatch.setenv("BILLING_DB_ONLY_MODE", "true")
    monkeypatch.setattr(billing_service, "_use_database", lambda: False)

    with pytest.raises(HTTPException) as exc:
        billing_service.get_tenant_subscription(tenant_id=1)

    assert exc.value.status_code == 503
    assert "DB-only mode" in str(exc.value.detail)


def test_assert_billing_write_allowed_fails_closed_when_db_only_and_database_unavailable(monkeypatch) -> None:
    monkeypatch.setenv("BILLING_DB_ONLY_MODE", "true")
    monkeypatch.setattr(billing_service, "_use_database", lambda: False)

    with pytest.raises(HTTPException) as exc:
        billing_service.assert_billing_write_allowed(tenant_id=1, action="unit-test")

    assert exc.value.status_code == 503
    assert "DB-only mode" in str(exc.value.detail)
