"""Phase LXXVII — Subscription Management Router tests (21 tests)."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.modules.subscriptions.service import clear_subscriptions_state

client = TestClient(app, raise_server_exceptions=True)
BASE = "/api/billing/subscriptions"


@pytest.fixture(autouse=True)
def _reset():
    clear_subscriptions_state()
    yield
    clear_subscriptions_state()


# ─── helpers ─────────────────────────────────────────────────────────────────


def _create(tenant_id: int = 1, plan_id: int = 10, notes: str | None = None):
    payload: dict = {"tenant_id": tenant_id, "plan_id": plan_id}
    if notes:
        payload["notes"] = notes
    return client.post(BASE, json=payload)


# ─── list ─────────────────────────────────────────────────────────────────────


def test_list_empty():
    r = client.get(BASE)
    assert r.status_code == 200
    assert r.json()["subscriptions"] == []


def test_list_returns_created_subscription():
    _create(tenant_id=1, plan_id=10)
    r = client.get(BASE)
    assert r.status_code == 200
    subs = r.json()["subscriptions"]
    assert len(subs) == 1
    assert subs[0]["tenant_id"] == 1
    assert subs[0]["plan_id"] == 10
    assert subs[0]["status"] == "active"


def test_list_filter_by_tenant_id():
    _create(tenant_id=1, plan_id=10)
    _create(tenant_id=2, plan_id=20)
    r = client.get(BASE, params={"tenant_id": 1})
    subs = r.json()["subscriptions"]
    assert len(subs) == 1
    assert subs[0]["tenant_id"] == 1


def test_list_filter_by_plan_id():
    _create(tenant_id=1, plan_id=10)
    _create(tenant_id=2, plan_id=20)
    r = client.get(BASE, params={"plan_id": 20})
    subs = r.json()["subscriptions"]
    assert len(subs) == 1
    assert subs[0]["plan_id"] == 20


def test_list_filter_by_status():
    _create(tenant_id=1, plan_id=10)
    _create(tenant_id=2, plan_id=20)
    # cancel first
    sub_id = client.get(BASE, params={"tenant_id": 1}).json()["subscriptions"][0]["id"]
    client.post(f"{BASE}/{sub_id}/cancel", json={"reason": "test"})
    r = client.get(BASE, params={"status": "cancelled"})
    subs = r.json()["subscriptions"]
    assert len(subs) == 1
    assert subs[0]["status"] == "cancelled"


# ─── create ───────────────────────────────────────────────────────────────────


def test_create_returns_201():
    r = _create()
    assert r.status_code == 201


def test_create_response_fields():
    r = _create(tenant_id=5, plan_id=99, notes="hello")
    data = r.json()["subscription"]
    assert data["tenant_id"] == 5
    assert data["plan_id"] == 99
    assert data["status"] == "active"
    assert data["notes"] == "hello"
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data


def test_create_duplicate_active_returns_400():
    _create(tenant_id=1, plan_id=10)
    r = _create(tenant_id=1, plan_id=20)  # same tenant, different plan
    assert r.status_code == 400
    assert "active subscription" in r.json()["detail"]


def test_create_different_tenants_ok():
    r1 = _create(tenant_id=1, plan_id=10)
    r2 = _create(tenant_id=2, plan_id=10)
    assert r1.status_code == 201
    assert r2.status_code == 201


# ─── stats ────────────────────────────────────────────────────────────────────


def test_stats_empty():
    r = client.get(f"{BASE}/stats")
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 0
    assert data["active"] == 0


def test_stats_after_create():
    _create(tenant_id=1, plan_id=10)
    _create(tenant_id=2, plan_id=20)
    r = client.get(f"{BASE}/stats")
    data = r.json()
    assert data["total"] == 2
    assert data["active"] == 2
    assert data["cancelled"] == 0


def test_stats_after_cancel():
    _create(tenant_id=1, plan_id=10)
    sub_id = client.get(BASE).json()["subscriptions"][0]["id"]
    client.post(f"{BASE}/{sub_id}/cancel", json={})
    r = client.get(f"{BASE}/stats")
    data = r.json()
    assert data["total"] == 1
    assert data["active"] == 0
    assert data["cancelled"] == 1


# ─── get by id ────────────────────────────────────────────────────────────────


def test_get_by_id_ok():
    r = _create(tenant_id=3, plan_id=30)
    sub_id = r.json()["subscription"]["id"]
    r2 = client.get(f"{BASE}/{sub_id}")
    assert r2.status_code == 200
    assert r2.json()["subscription"]["id"] == sub_id


def test_get_by_id_not_found():
    r = client.get(f"{BASE}/sub_9999")
    assert r.status_code == 404


# ─── cancel ───────────────────────────────────────────────────────────────────


def test_cancel_sets_status_cancelled():
    sub_id = _create().json()["subscription"]["id"]
    r = client.post(f"{BASE}/{sub_id}/cancel", json={"reason": "no longer needed"})
    assert r.status_code == 200
    assert r.json()["subscription"]["status"] == "cancelled"


def test_cancel_not_found():
    r = client.post(f"{BASE}/sub_9999/cancel", json={})
    assert r.status_code == 404


def test_cancel_already_cancelled_returns_400():
    sub_id = _create().json()["subscription"]["id"]
    client.post(f"{BASE}/{sub_id}/cancel", json={})
    r = client.post(f"{BASE}/{sub_id}/cancel", json={})
    assert r.status_code == 400


# ─── upgrade ──────────────────────────────────────────────────────────────────


def test_upgrade_changes_plan():
    sub_id = _create(tenant_id=1, plan_id=10).json()["subscription"]["id"]
    r = client.post(f"{BASE}/{sub_id}/upgrade", json={"new_plan_id": 50})
    assert r.status_code == 200
    assert r.json()["subscription"]["plan_id"] == 50


def test_upgrade_same_plan_returns_400():
    sub_id = _create(tenant_id=1, plan_id=10).json()["subscription"]["id"]
    r = client.post(f"{BASE}/{sub_id}/upgrade", json={"new_plan_id": 10})
    assert r.status_code == 400


def test_upgrade_cancelled_sub_returns_400():
    sub_id = _create().json()["subscription"]["id"]
    client.post(f"{BASE}/{sub_id}/cancel", json={})
    r = client.post(f"{BASE}/{sub_id}/upgrade", json={"new_plan_id": 99})
    assert r.status_code == 400


def test_upgrade_not_found():
    r = client.post(f"{BASE}/sub_9999/upgrade", json={"new_plan_id": 99})
    assert r.status_code == 404
