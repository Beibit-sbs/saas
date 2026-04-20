from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.modules.billing import router as billing_router


def _build_client() -> TestClient:
    app = FastAPI()
    app.include_router(billing_router.router)
    app.dependency_overrides[billing_router.get_actor] = lambda: "admin@example.com"
    return TestClient(app)


def _record(record_id: int = 7, status: str = "grace_period") -> dict[str, object]:
    return {
        "id": record_id,
        "tenant_id": 1,
        "invoice_id": "inv-001",
        "status": status,
        "opened_at": "2026-04-20T00:00:00+00:00",
        "last_reminder_at": None,
        "reminder_count": 0,
        "escalated_at": None,
        "resolved_at": None,
        "resolution": None,
        "notes": None,
        "amount_cents": 12500,
        "events": [
            {
                "event_type": "opened",
                "metadata": {"status": status},
                "created_at": "2026-04-20T00:00:00+00:00",
            }
        ],
    }


def test_get_dunning_policy_returns_default_contract(monkeypatch) -> None:
    client = _build_client()
    monkeypatch.setattr(
        billing_router,
        "get_dunning_policy",
        lambda tenant_id: {
            "grace_period_days": 7,
            "overdue_period_days": 30,
            "suspension_period_days": 30,
            "auto_cancel_after_days": 90,
            "reminder_schedule": [1, 3, 7, 14, 30],
            "require_approval_for_reactivation": True,
        },
    )

    response = client.get("/api/admin/billing/tenants/1/delinquency/policy")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["grace_period_days"] == 7
    assert body["reminder_schedule"] == [1, 3, 7, 14, 30]


def test_put_dunning_policy_updates_contract(monkeypatch) -> None:
    client = _build_client()

    monkeypatch.setattr(
        billing_router,
        "update_dunning_policy",
        lambda tenant_id, payload, actor: payload,
    )

    response = client.put(
        "/api/admin/billing/tenants/1/delinquency/policy",
        json={
            "grace_period_days": 5,
            "overdue_period_days": 20,
            "suspension_period_days": 15,
            "auto_cancel_after_days": 60,
            "reminder_schedule": [1, 2, 5],
            "require_approval_for_reactivation": False,
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["grace_period_days"] == 5
    assert body["require_approval_for_reactivation"] is False


def test_list_delinquency_records_returns_items(monkeypatch) -> None:
    client = _build_client()
    monkeypatch.setattr(
        billing_router,
        "list_delinquency_records",
        lambda tenant_id, status=None: [_record(7, "overdue")],
    )

    response = client.get("/api/admin/billing/tenants/1/delinquency?status=overdue")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["status"] == "overdue"


def test_get_delinquency_record_returns_detail(monkeypatch) -> None:
    client = _build_client()
    monkeypatch.setattr(billing_router, "get_delinquency_record", lambda tenant_id, record_id: _record(record_id))

    response = client.get("/api/admin/billing/tenants/1/delinquency/7")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["id"] == 7
    assert body["events"][0]["event_type"] == "opened"


def test_escalate_delinquency_record_advances_status(monkeypatch) -> None:
    client = _build_client()
    monkeypatch.setattr(
        billing_router,
        "escalate_delinquency_record",
        lambda tenant_id, record_id, actor, notes=None: _record(record_id, "overdue"),
    )

    response = client.post(
        "/api/admin/billing/tenants/1/delinquency/7/escalate",
        json={"notes": "manual escalation"},
    )
    assert response.status_code == 200, response.text
    assert response.json()["status"] == "overdue"


def test_resolve_delinquency_record_sets_resolution(monkeypatch) -> None:
    client = _build_client()

    def _resolve(tenant_id, record_id, resolution, actor, notes=None):
        record = _record(record_id, "collections")
        record["resolution"] = resolution
        record["resolved_at"] = "2026-04-21T00:00:00+00:00"
        return record

    monkeypatch.setattr(billing_router, "resolve_delinquency_record", _resolve)

    response = client.post(
        "/api/admin/billing/tenants/1/delinquency/7/resolve",
        json={"resolution": "paid", "notes": "invoice settled"},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["resolution"] == "paid"
    assert body["resolved_at"] is not None


def test_send_reminder_increments_counter(monkeypatch) -> None:
    client = _build_client()

    def _reminder(tenant_id, record_id, actor, notes=None):
        record = _record(record_id, "overdue")
        record["reminder_count"] = 2
        record["last_reminder_at"] = "2026-04-20T12:00:00+00:00"
        return record

    monkeypatch.setattr(billing_router, "send_delinquency_reminder", _reminder)

    response = client.post(
        "/api/admin/billing/tenants/1/delinquency/7/reminder",
        json={"notes": "second reminder"},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["reminder_count"] == 2
    assert body["last_reminder_at"] is not None


def test_dashboard_returns_summary(monkeypatch) -> None:
    client = _build_client()
    monkeypatch.setattr(
        billing_router,
        "get_delinquency_dashboard",
        lambda tenant_id: {
            "total": 3,
            "open_total": 2,
            "total_overdue_cents": 42000,
            "by_status": {"grace_period": 1, "overdue": 1, "collections": 1},
        },
    )

    response = client.get("/api/admin/billing/tenants/1/delinquency/dashboard")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["total"] == 3
    assert body["open_total"] == 2
    assert body["total_overdue_cents"] == 42000
