from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.modules.auth.token_service import create_access_token
from app.modules.billing import router as billing_router


def _build_client() -> TestClient:
    app = FastAPI()
    app.include_router(billing_router.router)
    app.dependency_overrides[billing_router.get_actor] = lambda: "admin@example.com"
    return TestClient(app)


def _headers(
    *,
    tenant_id: int = 1,
    permissions: list[str] | None = None,
) -> dict[str, str]:
    granted = permissions or [
        "billing.admin.read",
        "billing.admin.write",
        "billing.admin.manage",
        "platform.admin.read",
        "platform.admin.write",
    ]
    token = create_access_token(
        user_id="admin@example.com",
        roles=["admin"],
        auth_source="test",
        tenant_id=tenant_id,
        permissions=granted,
    )
    return {"Authorization": f"Bearer {token}"}


def _subscription(tenant_id: int = 1, plan_code: str = "pro", status: str = "active") -> dict[str, object]:
    return {
        "tenant_id": tenant_id,
        "plan_id": 2,
        "plan_code": plan_code,
        "status": status,
        "started_at": "2026-04-20T00:00:00+00:00",
        "trial_ends_at": None,
        "current_period_start": "2026-04-01T00:00:00+00:00",
        "current_period_end": "2026-05-01T00:00:00+00:00",
        "next_plan_id": None,
        "next_plan_code": None,
        "updated_at": "2026-04-20T00:00:00+00:00",
    }


def _plan(code: str = "pro") -> dict[str, object]:
    return {
        "id": 2,
        "code": code,
        "name": "Pro",
        "price_cents": 9900,
        "features": {"analytics": True},
        "limits": {"api_calls": 1000},
        "active": True,
        "created_at": "2026-04-20T00:00:00+00:00",
    }


def test_get_state_returns_contract_shape(monkeypatch) -> None:
    client = _build_client()

    monkeypatch.setattr(
        billing_router,
        "get_tenant_billing_state",
        lambda tenant_id: {
            "tenant_id": int(tenant_id),
            "plan_code": "pro",
            "plan_id": 2,
            "next_plan_code": None,
            "subscription_status": "active",
            "billing_state": "read_write",
            "period_start": "2026-04-01T00:00:00+00:00",
            "period_end": "2026-05-01T00:00:00+00:00",
            "limits": {"api_calls": 1000},
            "usage": {"api_calls": 12},
            "subscription": _subscription(tenant_id=int(tenant_id)),
        },
    )

    response = client.get("/api/admin/billing/tenants/7/state", headers=_headers())
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["tenant_id"] == 7
    assert body["billing_state"] == "read_write"
    assert body["subscription"]["plan_code"] == "pro"


def test_plan_change_maps_service_error_to_400(monkeypatch) -> None:
    client = _build_client()

    def _raise(*args, **kwargs):
        raise ValueError("effective must be one of: auto, immediate, next_period")

    monkeypatch.setattr(billing_router, "change_subscription_plan", _raise)

    response = client.post(
        "/api/admin/billing/tenants/1/subscription/plan-change",
        headers=_headers(),
        json={"plan_code": "pro", "effective": "invalid"},
    )
    assert response.status_code == 400
    assert "effective must be one of" in response.json()["detail"]


def test_usage_snapshot_passes_since_iso(monkeypatch) -> None:
    client = _build_client()

    captured: dict[str, object] = {}

    def _usage(tenant_id: int, *, since_iso: str | None = None) -> dict[str, int]:
        captured["tenant_id"] = tenant_id
        captured["since_iso"] = since_iso
        return {"api_calls": 15, "ai_usage": 2, "active_users": 1, "storage_mb": 0}

    monkeypatch.setattr(billing_router, "get_usage_snapshot", _usage)

    response = client.get(
        "/api/admin/billing/tenants/3/usage",
        headers=_headers(),
        params={"since_iso": "2026-04-01T00:00:00+00:00"},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["tenant_id"] == 3
    assert body["usage"]["api_calls"] == 15
    assert captured == {"tenant_id": 3, "since_iso": "2026-04-01T00:00:00+00:00"}


def test_transition_endpoint_returns_updated_state(monkeypatch) -> None:
    client = _build_client()

    calls: list[tuple[int, str]] = []

    def _transition(tenant_id: int, status: str, **kwargs):
        calls.append((tenant_id, status))
        return _subscription(tenant_id=tenant_id, status=status)

    monkeypatch.setattr(billing_router, "transition_subscription_status", _transition)
    monkeypatch.setattr(
        billing_router,
        "get_tenant_billing_state",
        lambda tenant_id: {
            "tenant_id": int(tenant_id),
            "plan_code": "pro",
            "plan_id": 2,
            "next_plan_code": None,
            "subscription_status": "suspended",
            "billing_state": "read_only",
            "period_start": "2026-04-01T00:00:00+00:00",
            "period_end": "2026-05-01T00:00:00+00:00",
            "limits": {"api_calls": 1000},
            "usage": {"api_calls": 12},
            "subscription": _subscription(tenant_id=int(tenant_id), status="suspended"),
        },
    )

    response = client.post(
        "/api/admin/billing/tenants/9/subscription/transition",
        headers=_headers(),
        json={"status": "suspended"},
    )
    assert response.status_code == 200, response.text
    assert response.json()["subscription_status"] == "suspended"
    assert calls == [(9, "suspended")]


def test_list_plans_returns_router_contract(monkeypatch) -> None:
    client = _build_client()

    monkeypatch.setattr(
        billing_router.platform_billing_service,
        "list_plans",
        lambda: [_plan("pro"), _plan("enterprise") | {"id": 3, "name": "Enterprise"}],
    )

    response = client.get("/api/admin/billing/plans", headers=_headers())
    assert response.status_code == 200, response.text
    body = response.json()
    assert len(body) == 2
    assert body[0]["code"] == "pro"
    assert body[1]["code"] == "enterprise"


def test_create_plan_returns_idempotent_replay_for_same_payload(monkeypatch) -> None:
    client = _build_client()

    existing = _plan("pro")
    monkeypatch.setattr(billing_router.platform_billing_service, "list_plans", lambda: [existing])

    def _should_not_create(*args, **kwargs):
        raise AssertionError("create_plan must not be called on idempotent replay")

    monkeypatch.setattr(billing_router.platform_billing_service, "create_plan", _should_not_create)

    response = client.post(
        "/api/admin/billing/plans",
        headers=_headers(),
        json={
            "code": "pro",
            "name": "Pro",
            "price_cents": 9900,
            "features": {"analytics": True},
            "limits": {"api_calls": 1000},
        },
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["idempotent_replay"] is True
    assert body["plan"]["code"] == "pro"


def test_assign_subscription_returns_idempotent_replay_when_same_plan(monkeypatch) -> None:
    client = _build_client()

    existing = _subscription(tenant_id=12, plan_code="pro", status="active")
    monkeypatch.setattr(billing_router.platform_billing_service, "get_subscription", lambda tenant_id: existing)

    def _should_not_assign(*args, **kwargs):
        raise AssertionError("assign_plan must not be called on idempotent replay")

    monkeypatch.setattr(billing_router.platform_billing_service, "assign_plan", _should_not_assign)

    response = client.put(
        "/api/admin/billing/tenants/12/subscription",
        headers=_headers(),
        json={"plan_code": "pro"},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["idempotent_replay"] is True
    assert body["subscription"]["tenant_id"] == 12
    assert body["subscription"]["plan_code"] == "pro"


def _usage_counter(tenant_id: int = 1, metric: str = "api_calls", value: int = 5) -> dict[str, object]:
    return {
        "tenant_id": tenant_id,
        "metric": metric,
        "period_key": "2026-04",
        "value": value,
        "updated_at": "2026-04-20T00:00:00+00:00",
    }


def test_usage_increment_calls_platform_service(monkeypatch) -> None:
    client = _build_client()
    called_with: list[tuple] = []

    def _increment(tenant_id: int, metric: str, value: int) -> dict:
        called_with.append((tenant_id, metric, value))
        return _usage_counter(tenant_id=tenant_id, metric=metric, value=value)

    monkeypatch.setattr(billing_router.platform_billing_service, "increment_usage", _increment)

    response = client.post(
        "/api/admin/billing/tenants/5/usage/api_calls",
        headers=_headers(),
        json={"value": 3},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["tenant_id"] == 5
    assert body["metric"] == "api_calls"
    assert body["value"] == 3
    assert called_with == [(5, "api_calls", 3)]


def test_usage_increment_rejects_zero_value(monkeypatch) -> None:
    client = _build_client()

    def _increment(*_args, **_kwargs):  # pragma: no cover
        raise AssertionError("should not reach service")

    monkeypatch.setattr(billing_router.platform_billing_service, "increment_usage", _increment)

    response = client.post(
        "/api/admin/billing/tenants/5/usage/api_calls",
        headers=_headers(),
        json={"value": 0},
    )
    # Pydantic ge=1 constraint → FastAPI returns 422 Unprocessable Entity
    assert response.status_code == 422


def test_patch_plan_updates_active_flag(monkeypatch) -> None:
    client = _build_client()

    updated_plan = _plan("pro") | {"active": False}
    monkeypatch.setattr(
        billing_router.platform_billing_service,
        "update_plan",
        lambda plan_id, *, name, active: updated_plan,
    )

    response = client.patch("/api/admin/billing/plans/2", headers=_headers(), json={"active": False})
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["code"] == "pro"
    assert body["active"] is False


def test_patch_plan_returns_404_when_not_found(monkeypatch) -> None:
    client = _build_client()

    monkeypatch.setattr(
        billing_router.platform_billing_service,
        "update_plan",
        lambda plan_id, *, name, active: None,
    )

    response = client.patch("/api/admin/billing/plans/999", headers=_headers(), json={"active": False})
    assert response.status_code == 404

