"""A-011.2 — Billing tenant path validation and override permission tests."""
from __future__ import annotations

from app.modules.auth.token_service import create_access_token
from app.modules.billing import router as billing_router
from tests.conftest import client


def _headers(tenant_id: int, permissions: list[str]) -> dict[str, str]:
    token = create_access_token(
        user_id="owner@example.com",
        roles=["admin"],
        auth_source="test",
        tenant_id=tenant_id,
        permissions=permissions,
    )
    return {"Authorization": f"Bearer {token}"}


def _state_row(tenant_id: int) -> dict[str, object]:
    return {
        "tenant_id": tenant_id,
        "plan_code": "pro",
        "plan_id": 2,
        "next_plan_code": None,
        "subscription_status": "active",
        "billing_state": "read_write",
        "period_start": "2026-04-01T00:00:00+00:00",
        "period_end": "2026-05-01T00:00:00+00:00",
        "limits": {"api_calls": 1000},
        "usage": {"api_calls": 12},
        "subscription": {
            "tenant_id": tenant_id,
            "plan_id": 2,
            "plan_code": "pro",
            "status": "active",
            "started_at": "2026-04-20T00:00:00+00:00",
            "trial_ends_at": None,
            "current_period_start": "2026-04-01T00:00:00+00:00",
            "current_period_end": "2026-05-01T00:00:00+00:00",
            "next_plan_id": None,
            "next_plan_code": None,
            "updated_at": "2026-04-20T00:00:00+00:00",
        },
    }


def test_tenant_user_can_access_own_billing_state(monkeypatch) -> None:
    monkeypatch.setattr(billing_router, "get_tenant_billing_state", lambda tenant_id: _state_row(int(tenant_id)))

    response = client.get(
        "/api/admin/billing/tenants/1/state",
        headers=_headers(tenant_id=1, permissions=["billing.admin.read"]),
    )

    assert response.status_code == 200, response.text
    assert response.json()["tenant_id"] == 1


def test_tenant_user_cross_tenant_state_denied(monkeypatch) -> None:
    monkeypatch.setattr(billing_router, "get_tenant_billing_state", lambda tenant_id: _state_row(int(tenant_id)))

    response = client.get(
        "/api/admin/billing/tenants/2/state",
        headers=_headers(tenant_id=1, permissions=["billing.admin.read"]),
    )

    assert response.status_code == 403, response.text
    assert response.json()["detail"] == "tenant_id_mismatch"


def test_missing_billing_permission_returns_403(monkeypatch) -> None:
    monkeypatch.setattr(billing_router, "get_tenant_billing_state", lambda tenant_id: _state_row(int(tenant_id)))

    response = client.get(
        "/api/admin/billing/tenants/1/state",
        headers=_headers(tenant_id=1, permissions=["admin.dashboard.read"]),
    )

    assert response.status_code == 403, response.text
    assert "missing permission: billing.admin.read" in response.json()["detail"]


def test_platform_override_requires_explicit_permission(monkeypatch) -> None:
    monkeypatch.setattr(billing_router, "get_tenant_billing_state", lambda tenant_id: _state_row(int(tenant_id)))

    response = client.get(
        "/api/admin/billing/tenants/2/state",
        headers=_headers(tenant_id=1, permissions=["billing.admin.read"]),
    )

    assert response.status_code == 403, response.text
    assert response.json()["detail"] == "tenant_id_mismatch"


def test_platform_override_with_explicit_permission_allows_cross_tenant_read(monkeypatch) -> None:
    monkeypatch.setattr(billing_router, "get_tenant_billing_state", lambda tenant_id: _state_row(int(tenant_id)))

    response = client.get(
        "/api/admin/billing/tenants/2/state",
        headers=_headers(tenant_id=1, permissions=["billing.admin.read", "platform.admin.read"]),
    )

    assert response.status_code == 200, response.text
    assert response.json()["tenant_id"] == 2


def test_platform_override_write_requires_platform_admin_write(monkeypatch) -> None:
    monkeypatch.setattr(
        billing_router,
        "transition_subscription_status",
        lambda tenant_id, status, **kwargs: {
            "tenant_id": int(tenant_id),
            "status": status,
        },
    )
    monkeypatch.setattr(billing_router, "get_tenant_billing_state", lambda tenant_id: _state_row(int(tenant_id)))

    denied = client.post(
        "/api/admin/billing/tenants/2/subscription/transition",
        headers=_headers(tenant_id=1, permissions=["billing.admin.write", "platform.admin.read"]),
        json={"status": "suspended"},
    )
    assert denied.status_code == 403, denied.text
    assert denied.json()["detail"] == "tenant_id_mismatch"

    allowed = client.post(
        "/api/admin/billing/tenants/2/subscription/transition",
        headers=_headers(tenant_id=1, permissions=["billing.admin.write", "platform.admin.write"]),
        json={"status": "suspended"},
    )
    assert allowed.status_code == 200, allowed.text


def test_invalid_tenant_id_is_fail_closed_400(monkeypatch) -> None:
    monkeypatch.setattr(billing_router, "get_tenant_billing_state", lambda tenant_id: _state_row(int(tenant_id)))

    response = client.get(
        "/api/admin/billing/tenants/-1/state",
        headers=_headers(tenant_id=1, permissions=["billing.admin.read", "platform.admin.read"]),
    )

    assert response.status_code == 400, response.text
    assert response.json()["detail"] == "invalid tenant_id"
