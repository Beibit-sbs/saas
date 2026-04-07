"""Targeted tests for the platform event ingestion layer v1.

Tests:
  1. record_event via repository directly
  2. analytics.event.read fires on GET /api/analytics/kpis
  3. analytics.kpi.read fires on GET /api/analytics/kpis/trends
  4. analytics.kpi.read fires on GET /api/analytics/kpis/insights
  5. analytics.kpi.read fires on GET /api/analytics/kpis/recommendations
  6. billing.usage.recorded fires on increment_usage
  7. tenant isolation — tenant A events do not appear for tenant B
  8. event payload contains expected keys
  9. event not recorded on unknown type (silently dropped)
 10. billing increment_usage still returns correct result when event recorded
"""
from __future__ import annotations

from uuid import uuid4

from tests.conftest import _auth_headers, client

from app.platform.billing import service as billing_service
from app.platform.event_ingestion import service as event_ingestion_service
from app.platform.event_ingestion.types import (
    ANALYTICS_EVENT_READ,
    ANALYTICS_KPI_READ,
    BILLING_USAGE_RECORDED,
)
from app.platform.uow import UnitOfWork
from app.modules.tenants import service as module_tenant_service


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _create_tenant(prefix: str) -> int:
    slug = f"{prefix}-{uuid4().hex[:8]}"
    tenant = module_tenant_service.create_tenant({"slug": slug, "name": f"{prefix} Tenant"})
    return int(tenant["id"])


def _tenant_user_headers(*, tenant_id: int) -> dict[str, str]:
    return _auth_headers(
        f"evtbus.viewer.{tenant_id}@example.com",
        ["student"],
        tenant_id=tenant_id,
    )


def _list_events(tenant_id: int, *, event_type: str | None = None) -> list[dict]:
    with UnitOfWork() as uow:
        return uow.platform_event_repository.list_for_tenant(
            tenant_id,
            event_type=event_type,
            conn=uow.conn,
        )


# ---------------------------------------------------------------------------
# 1. Direct repository record
# ---------------------------------------------------------------------------

def test_event_repository_records_and_retrieves(reset_shared_state) -> None:
    tenant_id = _create_tenant("evtrepo")
    with UnitOfWork() as uow:
        evt = uow.platform_event_repository.record(
            tenant_id=tenant_id,
            event_type=ANALYTICS_KPI_READ,
            payload_json={"test": True},
            conn=uow.conn,
        )

    assert int(evt["id"]) > 0
    assert int(evt["tenant_id"]) == tenant_id
    assert str(evt["event_type"]) == ANALYTICS_KPI_READ
    assert dict(evt["payload_json"]) == {"test": True}

    rows = _list_events(tenant_id)
    assert len(rows) == 1
    assert str(rows[0]["event_type"]) == ANALYTICS_KPI_READ


# ---------------------------------------------------------------------------
# 2. analytics.event.read fires on GET /api/analytics/kpis
# ---------------------------------------------------------------------------

def test_analytics_kpis_endpoint_records_event_read(reset_shared_state) -> None:
    tenant_id = _create_tenant("evtkpis")
    headers = _tenant_user_headers(tenant_id=tenant_id)

    before = _list_events(tenant_id, event_type=ANALYTICS_EVENT_READ)
    assert len(before) == 0

    resp = client.get("/api/analytics/kpis", headers=headers)
    assert resp.status_code == 200

    after = _list_events(tenant_id, event_type=ANALYTICS_EVENT_READ)
    assert len(after) == 1
    assert str(after[0]["payload_json"].get("endpoint")) == "kpis"


# ---------------------------------------------------------------------------
# 3. analytics.kpi.read fires on GET /api/analytics/kpis/trends
# ---------------------------------------------------------------------------

def test_analytics_trends_endpoint_records_kpi_read(reset_shared_state) -> None:
    tenant_id = _create_tenant("evttrends")
    headers = _tenant_user_headers(tenant_id=tenant_id)

    resp = client.get("/api/analytics/kpis/trends?window_days=7", headers=headers)
    assert resp.status_code == 200

    events = _list_events(tenant_id, event_type=ANALYTICS_KPI_READ)
    assert len(events) == 1
    assert str(events[0]["payload_json"].get("endpoint")) == "kpis/trends"
    assert int(events[0]["payload_json"].get("window_days")) == 7


# ---------------------------------------------------------------------------
# 4. analytics.kpi.read fires on GET /api/analytics/kpis/insights
# ---------------------------------------------------------------------------

def test_analytics_insights_endpoint_records_kpi_read(reset_shared_state) -> None:
    tenant_id = _create_tenant("evtinsights")
    headers = _tenant_user_headers(tenant_id=tenant_id)

    resp = client.get("/api/analytics/kpis/insights?window_days=30", headers=headers)
    assert resp.status_code == 200

    events = _list_events(tenant_id, event_type=ANALYTICS_KPI_READ)
    assert len(events) == 1
    assert str(events[0]["payload_json"].get("endpoint")) == "kpis/insights"


# ---------------------------------------------------------------------------
# 5. analytics.kpi.read fires on GET /api/analytics/kpis/recommendations
# ---------------------------------------------------------------------------

def test_analytics_recommendations_endpoint_records_kpi_read(reset_shared_state) -> None:
    tenant_id = _create_tenant("evtrec")
    headers = _tenant_user_headers(tenant_id=tenant_id)

    resp = client.get("/api/analytics/kpis/recommendations?window_days=90", headers=headers)
    assert resp.status_code == 200

    events = _list_events(tenant_id, event_type=ANALYTICS_KPI_READ)
    assert len(events) == 1
    assert int(events[0]["payload_json"].get("window_days")) == 90


# ---------------------------------------------------------------------------
# 6. billing.usage.recorded fires on increment_usage
# ---------------------------------------------------------------------------

def test_billing_increment_usage_records_platform_event(reset_shared_state) -> None:
    tenant_id = _create_tenant("evtusage")

    billing_service.increment_usage(tenant_id, "analytics.events.read", 3)

    events = _list_events(tenant_id, event_type=BILLING_USAGE_RECORDED)
    assert len(events) == 1
    payload = events[0]["payload_json"]
    assert str(payload["metric"]) == "analytics.events.read"
    assert int(payload["value"]) == 3
    assert str(payload["period_key"]) == "current"


# ---------------------------------------------------------------------------
# 7. Tenant isolation
# ---------------------------------------------------------------------------

def test_event_ingestion_tenant_isolation(reset_shared_state) -> None:
    tenant_a = _create_tenant("evtiso-a")
    tenant_b = _create_tenant("evtiso-b")

    billing_service.increment_usage(tenant_a, "analytics.kpi.read", 1)
    billing_service.increment_usage(tenant_b, "analytics.kpi.read", 5)

    # Extra event for tenant_a via analytics endpoint
    headers_a = _tenant_user_headers(tenant_id=tenant_a)
    client.get("/api/analytics/kpis", headers=headers_a)

    events_a = _list_events(tenant_a)
    events_b = _list_events(tenant_b)

    # tenant_a: 1 billing event + 1 analytics.event.read
    assert len(events_a) == 2
    assert all(int(e["tenant_id"]) == tenant_a for e in events_a)

    # tenant_b: only 1 billing event
    assert len(events_b) == 1
    assert all(int(e["tenant_id"]) == tenant_b for e in events_b)


# ---------------------------------------------------------------------------
# 8. Event payload contains expected keys
# ---------------------------------------------------------------------------

def test_event_record_has_all_required_fields(reset_shared_state) -> None:
    tenant_id = _create_tenant("evtfields")
    result = event_ingestion_service.record_event(
        tenant_id,
        ANALYTICS_KPI_READ,
        {"endpoint": "test"},
    )

    assert result is not None
    assert "id" in result
    assert "tenant_id" in result
    assert "event_type" in result
    assert "payload_json" in result
    assert "created_at" in result
    assert int(result["tenant_id"]) == tenant_id
    assert str(result["event_type"]) == ANALYTICS_KPI_READ


# ---------------------------------------------------------------------------
# 9. Unknown event type is silently dropped
# ---------------------------------------------------------------------------

def test_record_event_silently_drops_unknown_type(reset_shared_state) -> None:
    tenant_id = _create_tenant("evtunk")

    result = event_ingestion_service.record_event(
        tenant_id,
        "totally.unknown.event.type.xyz",
        {"x": 1},
    )

    assert result is None
    rows = _list_events(tenant_id)
    assert len(rows) == 0


# ---------------------------------------------------------------------------
# 10. increment_usage still returns correct result when event recorded
# ---------------------------------------------------------------------------

def test_billing_increment_usage_return_value_unchanged(reset_shared_state) -> None:
    tenant_id = _create_tenant("evtret")

    result = billing_service.increment_usage(tenant_id, "analytics.kpi.read", 7)

    assert result is not None
    assert int(result["tenant_id"]) == tenant_id


# ===========================================================================
# Event projection / read layer v1 — GET /api/analytics/events
#                                   GET /api/analytics/events/summary
# ===========================================================================

# ---------------------------------------------------------------------------
# 11. Tenant reads own recent events via HTTP
# ---------------------------------------------------------------------------

def test_get_events_endpoint_returns_own_events(reset_shared_state) -> None:
    tenant_id = _create_tenant("evtread-own")
    headers = _tenant_user_headers(tenant_id=tenant_id)

    client.get("/api/analytics/kpis", headers=headers)
    client.get("/api/analytics/kpis/trends?window_days=7", headers=headers)

    resp = client.get("/api/analytics/events", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["tenant_id"] == tenant_id
    assert body["count"] == 2
    assert len(body["items"]) == 2
    for item in body["items"]:
        assert "id" in item
        assert "event_type" in item
        assert "created_at" in item
        assert "payload" in item


# ---------------------------------------------------------------------------
# 12. Event list is newest-first
# ---------------------------------------------------------------------------

def test_get_events_endpoint_newest_first(reset_shared_state) -> None:
    tenant_id = _create_tenant("evtread-order")
    headers = _tenant_user_headers(tenant_id=tenant_id)

    client.get("/api/analytics/kpis", headers=headers)
    client.get("/api/analytics/kpis/trends?window_days=7", headers=headers)

    resp = client.get("/api/analytics/events", headers=headers)
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert len(items) == 2
    # Newest-first: IDs must be non-ascending
    assert int(items[0]["id"]) >= int(items[1]["id"])


# ---------------------------------------------------------------------------
# 13. Limit parameter is honored
# ---------------------------------------------------------------------------

def test_get_events_endpoint_limit_bounded(reset_shared_state) -> None:
    tenant_id = _create_tenant("evtlimit")
    headers = _tenant_user_headers(tenant_id=tenant_id)

    client.get("/api/analytics/kpis", headers=headers)
    client.get("/api/analytics/kpis/trends", headers=headers)
    client.get("/api/analytics/kpis/insights", headers=headers)

    resp = client.get("/api/analytics/events?limit=2", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["items"]) == 2
    assert body["count"] == 2


# ---------------------------------------------------------------------------
# 14. Tenant cannot read another tenant's events
# ---------------------------------------------------------------------------

def test_get_events_endpoint_tenant_isolation(reset_shared_state) -> None:
    tenant_a = _create_tenant("evtiso-read-a")
    tenant_b = _create_tenant("evtiso-read-b")
    headers_a = _tenant_user_headers(tenant_id=tenant_a)
    headers_b = _tenant_user_headers(tenant_id=tenant_b)

    # Tenant A fires two events
    client.get("/api/analytics/kpis", headers=headers_a)
    client.get("/api/analytics/kpis", headers=headers_a)

    # Tenant B should see zero events
    resp_b = client.get("/api/analytics/events", headers=headers_b)
    assert resp_b.status_code == 200
    body_b = resp_b.json()
    assert body_b["tenant_id"] == tenant_b
    assert body_b["count"] == 0
    assert body_b["items"] == []


# ---------------------------------------------------------------------------
# 15. Summary projection matches recorded events
# ---------------------------------------------------------------------------

def test_get_events_summary_matches_recorded(reset_shared_state) -> None:
    tenant_id = _create_tenant("evtsum")
    headers = _tenant_user_headers(tenant_id=tenant_id)

    client.get("/api/analytics/kpis", headers=headers)           # analytics.event.read ×1
    client.get("/api/analytics/kpis/trends", headers=headers)    # analytics.kpi.read ×1
    client.get("/api/analytics/kpis/insights", headers=headers)  # analytics.kpi.read ×1
    billing_service.increment_usage(tenant_id, "analytics.events.read", 1)  # billing.usage.recorded ×1

    resp = client.get("/api/analytics/events/summary", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["tenant_id"] == tenant_id
    counts = body["counts_by_type"]
    assert int(counts.get(ANALYTICS_EVENT_READ, 0)) == 1
    assert int(counts.get(ANALYTICS_KPI_READ, 0)) == 2
    assert int(counts.get(BILLING_USAGE_RECORDED, 0)) == 1
    assert int(body["total"]) == 4


# ---------------------------------------------------------------------------
# 16. Empty state returns predictable structure
# ---------------------------------------------------------------------------

def test_get_events_empty_state(reset_shared_state) -> None:
    tenant_id = _create_tenant("evtempty")
    headers = _tenant_user_headers(tenant_id=tenant_id)

    resp_list = client.get("/api/analytics/events", headers=headers)
    assert resp_list.status_code == 200
    body_list = resp_list.json()
    assert body_list["tenant_id"] == tenant_id
    assert body_list["items"] == []
    assert body_list["count"] == 0

    resp_sum = client.get("/api/analytics/events/summary", headers=headers)
    assert resp_sum.status_code == 200
    body_sum = resp_sum.json()
    assert body_sum["tenant_id"] == tenant_id
    assert body_sum["counts_by_type"] == {}
    assert body_sum["total"] == 0
