"""Phase LXXIII — Usage Tracking Router tests (20 tests)."""
from __future__ import annotations

from unittest.mock import patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.modules.usage.router import router

app = FastAPI()
app.include_router(router)
client = TestClient(app)

MODULE = "app.modules.usage.router"


# ─── helpers ──────────────────────────────────────────────────────────────────


def _event(
    id_: int = 1,
    tenant_id: int = 1,
    metric: str = "ai_requests",
    value: int = 5,
    created_at: str = "2026-01-01T00:00:00+00:00",
) -> dict:
    return {
        "id": id_,
        "tenant_id": tenant_id,
        "metric": metric,
        "value": value,
        "created_at": created_at,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# POST /api/usage/events — record_event
# ═══════════════════════════════════════════════════════════════════════════════


def test_record_event_success():
    row = _event()
    with patch(f"{MODULE}.record_usage_event", return_value=row) as mock:
        resp = client.post(
            "/api/usage/events",
            json={"tenant_id": 1, "metric": "ai_requests", "value": 5},
        )
    assert resp.status_code == 201
    body = resp.json()
    assert body["id"] == 1
    assert body["metric"] == "ai_requests"
    assert body["value"] == 5
    mock.assert_called_once_with(tenant_id=1, metric="ai_requests", value=5)


def test_record_event_default_value():
    row = _event(value=1)
    with patch(f"{MODULE}.record_usage_event", return_value=row):
        resp = client.post(
            "/api/usage/events",
            json={"tenant_id": 2, "metric": "logins"},
        )
    assert resp.status_code == 201
    assert resp.json()["value"] == 1


def test_record_event_stores_metric():
    row = _event(metric="storage_mb", value=100)
    with patch(f"{MODULE}.record_usage_event", return_value=row):
        resp = client.post(
            "/api/usage/events",
            json={"tenant_id": 1, "metric": "storage_mb", "value": 100},
        )
    assert resp.status_code == 201
    assert resp.json()["metric"] == "storage_mb"


def test_record_event_missing_tenant_rejected():
    resp = client.post(
        "/api/usage/events",
        json={"metric": "ai_requests", "value": 1},
    )
    assert resp.status_code == 422


def test_record_event_missing_metric_rejected():
    resp = client.post(
        "/api/usage/events",
        json={"tenant_id": 1, "value": 1},
    )
    assert resp.status_code == 422


def test_record_event_zero_tenant_rejected():
    resp = client.post(
        "/api/usage/events",
        json={"tenant_id": 0, "metric": "ai_requests", "value": 1},
    )
    assert resp.status_code == 422


def test_record_event_negative_value_rejected():
    resp = client.post(
        "/api/usage/events",
        json={"tenant_id": 1, "metric": "ai_requests", "value": -1},
    )
    assert resp.status_code == 422


def test_record_event_service_valueerror_returns_400():
    with patch(f"{MODULE}.record_usage_event", side_effect=ValueError("metric is required")):
        resp = client.post(
            "/api/usage/events",
            json={"tenant_id": 1, "metric": "x", "value": 1},
        )
    assert resp.status_code == 400
    assert "metric" in resp.json()["detail"]


# ═══════════════════════════════════════════════════════════════════════════════
# GET /api/usage/events — list_events
# ═══════════════════════════════════════════════════════════════════════════════


def test_list_events_returns_all():
    rows = [_event(id_=1), _event(id_=2, metric="logins", value=1)]
    with patch(f"{MODULE}.list_usage_events", return_value=rows) as mock:
        resp = client.get("/api/usage/events?tenant_id=1")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["events"]) == 2
    mock.assert_called_once_with(tenant_id=1, metric=None, limit=200)


def test_list_events_filters_by_metric():
    rows = [_event()]
    with patch(f"{MODULE}.list_usage_events", return_value=rows) as mock:
        resp = client.get("/api/usage/events?tenant_id=1&metric=ai_requests")
    assert resp.status_code == 200
    mock.assert_called_once_with(tenant_id=1, metric="ai_requests", limit=200)


def test_list_events_respects_limit():
    rows = [_event(id_=i) for i in range(5)]
    with patch(f"{MODULE}.list_usage_events", return_value=rows) as mock:
        resp = client.get("/api/usage/events?tenant_id=1&limit=5")
    assert resp.status_code == 200
    mock.assert_called_once_with(tenant_id=1, metric=None, limit=5)


def test_list_events_missing_tenant_rejected():
    resp = client.get("/api/usage/events")
    assert resp.status_code == 422


def test_list_events_zero_tenant_rejected():
    resp = client.get("/api/usage/events?tenant_id=0")
    assert resp.status_code == 422


def test_list_events_empty_returns_empty_list():
    with patch(f"{MODULE}.list_usage_events", return_value=[]):
        resp = client.get("/api/usage/events?tenant_id=99")
    assert resp.status_code == 200
    assert resp.json()["events"] == []


def test_list_events_limit_too_large_rejected():
    resp = client.get("/api/usage/events?tenant_id=1&limit=9999")
    assert resp.status_code == 422


# ═══════════════════════════════════════════════════════════════════════════════
# GET /api/usage/sum — get_sum
# ═══════════════════════════════════════════════════════════════════════════════


def test_get_sum_success():
    with patch(f"{MODULE}.get_usage_sum", return_value=42) as mock:
        resp = client.get("/api/usage/sum?tenant_id=1&metric=ai_requests")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 42
    assert body["metric"] == "ai_requests"
    assert body["tenant_id"] == 1
    mock.assert_called_once_with(tenant_id=1, metric="ai_requests", since_iso=None)


def test_get_sum_with_since():
    with patch(f"{MODULE}.get_usage_sum", return_value=10) as mock:
        resp = client.get(
            "/api/usage/sum?tenant_id=1&metric=logins&since=2026-01-01T00:00:00Z"
        )
    assert resp.status_code == 200
    assert resp.json()["total"] == 10
    mock.assert_called_once_with(
        tenant_id=1, metric="logins", since_iso="2026-01-01T00:00:00Z"
    )


def test_get_sum_zero_result():
    with patch(f"{MODULE}.get_usage_sum", return_value=0):
        resp = client.get("/api/usage/sum?tenant_id=1&metric=nonexistent")
    assert resp.status_code == 200
    assert resp.json()["total"] == 0


def test_get_sum_missing_tenant_rejected():
    resp = client.get("/api/usage/sum?metric=ai_requests")
    assert resp.status_code == 422


def test_get_sum_missing_metric_rejected():
    resp = client.get("/api/usage/sum?tenant_id=1")
    assert resp.status_code == 422


def test_get_sum_zero_tenant_rejected():
    resp = client.get("/api/usage/sum?tenant_id=0&metric=ai_requests")
    assert resp.status_code == 422
