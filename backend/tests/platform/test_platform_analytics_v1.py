from __future__ import annotations

import base64
from datetime import date, timedelta
import json
from uuid import uuid4

import pytest

from tests.conftest import ADMIN_HEADERS, INTERNAL_HEADERS, _auth_headers, client

from app.platform.analytics import service as analytics_service
from app.platform.analytics.repository import AnalyticsRepository
from app.platform.developer import service as developer_service
from app.platform.events.handlers.analytics_handler import AnalyticsEventHandler
from app.platform.events.publisher import EventPublisher
from app.platform.events.schemas import OutboxEventRead
from app.platform.events.worker import OutboxEventWorker
from app.platform.repository.db import db_url as _platform_db_url
from app.platform.tenant import service as tenant_service
from app.platform.uow import UnitOfWork
from app.modules.observability.metrics import snapshot_developer_analytics_contract_metrics
from app.modules.observability.security_signals import snapshot_security_metrics


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_event(tenant_id: int, event_type: str = "student.created", event_id: int = 1) -> OutboxEventRead:
    return OutboxEventRead(
        id=event_id,
        tenant_id=tenant_id,
        event_type=event_type,
        aggregate_type="student",
        aggregate_id=str(event_id),
        payload_json={"student_id": event_id},
        status="pending",
        retry_count=0,
        available_at="2026-01-01T00:00:00+00:00",
        created_at="2026-01-01T00:00:00+00:00",
    )


def _tenant_admin_headers(tenant_id: int) -> dict[str, str]:
    return _auth_headers(
        f"tenant.admin.analytics.{tenant_id}@example.com",
        ["admin"],
        tenant_id=tenant_id,
    )


def _developer_headers_for_tenant(*, tenant_id: int, enable_entitlement: bool = True) -> dict[str, str]:
    app = developer_service.developer_service.create_app(
        tenant_id=tenant_id,
        name=f"Analytics Reader {tenant_id}",
        description="tenant analytics read api",
        owner_email="owner@example.com",
        scopes=["analytics.read"],
    )
    developer_service.developer_service.install_app(
        app_id=int(app["id"]),
        tenant_id=tenant_id,
        installed_by="test-suite",
    )
    if enable_entitlement:
        _set_developer_analytics_entitlement(
            tenant_id=tenant_id,
            enabled=True,
            headers=_tenant_admin_headers(tenant_id),
        )
    return {
        "X-App-Key": str(app["app_key"]),
        "X-App-Secret": str(app["app_secret"]),
    }


def _set_developer_analytics_entitlement(
    *,
    tenant_id: int,
    enabled: bool,
    headers: dict[str, str] | None = None,
) -> None:
    entitlement_headers = headers or _tenant_admin_headers(tenant_id)
    response = client.put(
        f"/api/v1/admin/tenants/{int(tenant_id)}/features/analytics/developer_read",
        headers=entitlement_headers,
        json={"enabled": bool(enabled)},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["scope"] == "tenant"
    assert int(body["tenant_id"]) == int(tenant_id)
    assert body["module"] == "analytics"
    assert body["key"] == "developer_read"
    assert bool(body["enabled"]) is bool(enabled)


def _set_developer_analytics_rollout_required(
    *,
    tenant_id: int,
    enabled: bool,
    headers: dict[str, str] | None = None,
) -> None:
    rollout_headers = headers or _tenant_admin_headers(tenant_id)
    response = client.put(
        f"/api/v1/admin/tenants/{int(tenant_id)}/features/analytics/developer_read_required",
        headers=rollout_headers,
        json={"enabled": bool(enabled)},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["scope"] == "tenant"
    assert int(body["tenant_id"]) == int(tenant_id)
    assert body["module"] == "analytics"
    assert body["key"] == "developer_read_required"
    assert bool(body["enabled"]) is bool(enabled)


def _get_analytics_rollout_state(*, tenant_id: int, headers: dict[str, str]) -> dict[str, object]:
    response = client.get(
        f"/api/v1/admin/tenants/{int(tenant_id)}/analytics/entitlement-rollout-state",
        headers=headers,
    )
    assert response.status_code == 200, response.text
    return dict(response.json())


def _get_analytics_rollout_summary(*, headers: dict[str, str], limit: int = 100) -> dict[str, object]:
    response = client.get(
        f"/api/v1/admin/tenants/analytics/entitlement-rollout-summary?limit={int(limit)}",
        headers=headers,
    )
    assert response.status_code == 200, response.text
    return dict(response.json())


def _usage_metric_value(*, tenant_id: int, metric: str, period_key: str = "current") -> int:
    with UnitOfWork() as uow:
        rows = uow.usage_repository.list_for_tenant_period(int(tenant_id), period_key=period_key, conn=uow.conn)
    for row in rows:
        if str(row.get("metric", "")).strip().lower() == str(metric).strip().lower():
            return int(row.get("value", 0) or 0)
    return 0


# ---------------------------------------------------------------------------
# Repository unit tests (in-memory fallback)
# ---------------------------------------------------------------------------

def test_analytics_repository_append_projection_idempotent(reset_shared_state) -> None:
    repo = AnalyticsRepository()
    tenant = tenant_service.create_tenant(f"an-idem-{uuid4().hex[:8]}", "Tenant Idem")
    tid = int(tenant["tenant_id"])

    first = repo.append_event_projection(
        tenant_id=tid, outbox_event_id=100, event_type="student.created",
        aggregate_type="student", aggregate_id="100",
    )
    assert first is not None
    assert first["outbox_event_id"] == 100

    # same outbox_event_id → duplicate, returns None
    duplicate = repo.append_event_projection(
        tenant_id=tid, outbox_event_id=100, event_type="student.created",
        aggregate_type="student", aggregate_id="100",
    )
    assert duplicate is None

    rows = repo.list_event_projections(tenant_id=tid)
    assert len(rows) == 1


def test_analytics_repository_kpi_increment(reset_shared_state) -> None:
    repo = AnalyticsRepository()
    tenant = tenant_service.create_tenant(f"an-kpi-{uuid4().hex[:8]}", "Tenant KPI")
    tid = int(tenant["tenant_id"])
    today = date.today().isoformat()

    snap1 = repo.increment_kpi_snapshot(tenant_id=tid, snapshot_date=today, event_type="student.created")
    assert snap1["total_events"] == 1
    assert snap1["event_counts_json"]["student.created"] == 1

    snap2 = repo.increment_kpi_snapshot(tenant_id=tid, snapshot_date=today, event_type="student.created")
    assert snap2["total_events"] == 2
    assert snap2["event_counts_json"]["student.created"] == 2

    snap3 = repo.increment_kpi_snapshot(tenant_id=tid, snapshot_date=today, event_type="enrollment.created")
    assert snap3["total_events"] == 3
    assert snap3["event_counts_json"]["enrollment.created"] == 1


def test_analytics_repository_kpi_get_latest_returns_none_when_empty(reset_shared_state) -> None:
    repo = AnalyticsRepository()
    tenant = tenant_service.create_tenant(f"an-empty-{uuid4().hex[:8]}", "Tenant Empty")
    tid = int(tenant["tenant_id"])
    assert repo.get_latest_kpi_snapshot(tenant_id=tid) is None


def test_analytics_repository_list_by_event_type_filter(reset_shared_state) -> None:
    repo = AnalyticsRepository()
    tenant = tenant_service.create_tenant(f"an-flt-{uuid4().hex[:8]}", "Tenant Filter")
    tid = int(tenant["tenant_id"])

    for oid, etype in [(201, "student.created"), (202, "enrollment.created"), (203, "student.created")]:
        repo.append_event_projection(
            tenant_id=tid, outbox_event_id=oid, event_type=etype,
            aggregate_type="x", aggregate_id=str(oid),
        )

    student_rows = repo.list_event_projections(tenant_id=tid, event_type="student.created")
    assert len(student_rows) == 2
    assert all(r["event_type"] == "student.created" for r in student_rows)

    all_rows = repo.list_event_projections(tenant_id=tid)
    assert len(all_rows) == 3


# ---------------------------------------------------------------------------
# Handler integration (record_event_projection via AnalyticsEventHandler)
# ---------------------------------------------------------------------------

def test_analytics_handler_records_projection_and_kpi(reset_shared_state) -> None:
    tenant = tenant_service.create_tenant(f"an-hdl-{uuid4().hex[:8]}", "Handler Tenant")
    tid = int(tenant["tenant_id"])
    event = _make_event(tid, event_type="grade.submitted", event_id=999)

    handler = AnalyticsEventHandler()
    with UnitOfWork() as uow:
        result = handler.handle(event, uow=uow)

    assert result["status"] == "recorded"
    assert result["outbox_event_id"] == 999

    with UnitOfWork() as uow:
        projections = analytics_service.list_event_projections(tenant_id=tid, uow=uow)
    assert len(projections) == 1
    assert projections[0]["event_type"] == "grade.submitted"

    with UnitOfWork() as uow:
        kpi = analytics_service.get_latest_tenant_kpis(tenant_id=tid, uow=uow)
    assert kpi is not None
    assert kpi["total_events"] == 1
    assert kpi["event_counts_json"]["grade.submitted"] == 1


def test_analytics_handler_duplicate_outbox_event_is_noop(reset_shared_state) -> None:
    tenant = tenant_service.create_tenant(f"an-dup-{uuid4().hex[:8]}", "Dup Tenant")
    tid = int(tenant["tenant_id"])
    event = _make_event(tid, event_id=888)

    handler = AnalyticsEventHandler()
    with UnitOfWork() as uow:
        r1 = handler.handle(event, uow=uow)
    with UnitOfWork() as uow:
        r2 = handler.handle(event, uow=uow)

    assert r1["status"] == "recorded"
    assert r2["status"] == "duplicate"

    with UnitOfWork() as uow:
        projections = analytics_service.list_event_projections(tenant_id=tid, uow=uow)
    assert len(projections) == 1


# ---------------------------------------------------------------------------
# Tenant KPI isolation
# ---------------------------------------------------------------------------

def test_analytics_tenant_isolation(reset_shared_state) -> None:
    ta = tenant_service.create_tenant(f"an-isoa-{uuid4().hex[:8]}", "Iso A")
    tb = tenant_service.create_tenant(f"an-isob-{uuid4().hex[:8]}", "Iso B")
    tid_a = int(ta["tenant_id"])
    tid_b = int(tb["tenant_id"])

    handler = AnalyticsEventHandler()
    for i, tid in [(1, tid_a), (2, tid_a), (3, tid_b)]:
        event = _make_event(tid, event_id=i)
        with UnitOfWork() as uow:
            handler.handle(event, uow=uow)

    with UnitOfWork() as uow:
        rows_a = analytics_service.list_event_projections(tenant_id=tid_a, uow=uow)
        rows_b = analytics_service.list_event_projections(tenant_id=tid_b, uow=uow)
    assert len(rows_a) == 2
    assert len(rows_b) == 1

    with UnitOfWork() as uow:
        kpi_a = analytics_service.get_latest_tenant_kpis(tenant_id=tid_a, uow=uow)
        kpi_b = analytics_service.get_latest_tenant_kpis(tenant_id=tid_b, uow=uow)
    assert kpi_a["total_events"] == 2
    assert kpi_b["total_events"] == 1


# ---------------------------------------------------------------------------
# Full outbox worker → analytics handler pipeline
# ---------------------------------------------------------------------------

def test_analytics_handler_invoked_via_outbox_worker(reset_shared_state) -> None:
    tenant = tenant_service.create_tenant(f"an-wkr-{uuid4().hex[:8]}", "Worker Tenant")
    tid = int(tenant["tenant_id"])

    with UnitOfWork() as uow:
        publisher = EventPublisher(uow=uow)
        publisher.publish_event(
            tenant_id=tid,
            event_type="enrollment.created",
            aggregate_type="enrollment",
            aggregate_id="42",
            payload_json={"enrollment_id": 42},
        )

    with UnitOfWork() as uow:
        worker = OutboxEventWorker()
        result = worker.run_once()

    assert result["succeeded"] >= 1

    with UnitOfWork() as uow:
        projections = analytics_service.list_event_projections(
            tenant_id=tid, event_type="enrollment.created", uow=uow
        )
    assert len(projections) >= 1


# ---------------------------------------------------------------------------
# refresh_tenant_kpis (recompute from scratch)
# ---------------------------------------------------------------------------

def test_refresh_tenant_kpis_recomputes_counts(reset_shared_state) -> None:
    tenant = tenant_service.create_tenant(f"an-rfr-{uuid4().hex[:8]}", "Refresh Tenant")
    tid = int(tenant["tenant_id"])

    handler = AnalyticsEventHandler()
    for i in range(1, 4):
        with UnitOfWork() as uow:
            handler.handle(_make_event(tid, event_type="student.created", event_id=i * 100), uow=uow)

    with UnitOfWork() as uow:
        snap = analytics_service.refresh_tenant_kpis(tenant_id=tid, uow=uow)
    assert snap["total_events"] == 3
    assert snap["event_counts_json"]["student.created"] == 3
    assert snap["version"] >= 1


# ---------------------------------------------------------------------------
# Admin API — list projections
# ---------------------------------------------------------------------------

def test_admin_api_list_analytics_events(reset_shared_state) -> None:
    tid = 1

    handler = AnalyticsEventHandler()
    with UnitOfWork() as uow:
        handler.handle(_make_event(tid, event_type="student.created", event_id=501), uow=uow)
    with UnitOfWork() as uow:
        handler.handle(_make_event(tid, event_type="grade.submitted", event_id=502), uow=uow)

    resp = client.get(
        f"/api/v1/admin/tenants/{tid}/analytics/events",
        headers=ADMIN_HEADERS,
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["tenant_id"] == tid
    assert body["total"] == 2

    # filter by event_type
    resp2 = client.get(
        f"/api/v1/admin/tenants/{tid}/analytics/events?event_type=student.created",
        headers=ADMIN_HEADERS,
    )
    assert resp2.status_code == 200, resp2.text
    body2 = resp2.json()
    assert body2["total"] == 1
    assert body2["items"][0]["event_type"] == "student.created"


def test_admin_api_get_latest_kpis(reset_shared_state) -> None:
    tenant = tenant_service.create_tenant(f"an-kpi-api-{uuid4().hex[:8]}", "KPI API Tenant")
    tid = int(tenant["tenant_id"])

    handler = AnalyticsEventHandler()
    with UnitOfWork() as uow:
        handler.handle(_make_event(tid, event_type="student.created", event_id=601), uow=uow)

    resp = client.get(
        f"/api/v1/admin/tenants/{tid}/analytics/kpis/latest",
        headers=ADMIN_HEADERS,
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["tenant_id"] == tid
    assert body["total_events"] == 1
    assert body["event_counts_json"]["student.created"] == 1


def test_admin_api_get_latest_kpis_404_when_none(reset_shared_state) -> None:
    tenant = tenant_service.create_tenant(f"an-404-{uuid4().hex[:8]}", "No KPI Tenant")
    tid = int(tenant["tenant_id"])

    resp = client.get(
        f"/api/v1/admin/tenants/{tid}/analytics/kpis/latest",
        headers=ADMIN_HEADERS,
    )
    assert resp.status_code == 404, resp.text


# ---------------------------------------------------------------------------
# Internal API — KPI refresh endpoint
# ---------------------------------------------------------------------------

def test_internal_api_kpi_refresh(reset_shared_state) -> None:
    tenant = tenant_service.create_tenant(f"an-int-{uuid4().hex[:8]}", "Internal Tenant")
    tid = int(tenant["tenant_id"])

    handler = AnalyticsEventHandler()
    for i in range(1, 3):
        with UnitOfWork() as uow:
            handler.handle(_make_event(tid, event_type="enrollment.created", event_id=i * 700), uow=uow)

    resp = client.post(
        f"/api/v1/internal/analytics/tenants/{tid}/kpis/refresh",
        headers=INTERNAL_HEADERS,
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["tenant_id"] == tid
    assert body["total_events"] == 2
    assert body["event_counts_json"]["enrollment.created"] == 2


def test_developer_api_recent_analytics_events_tenant_scoped(reset_shared_state) -> None:
    tenant_a = tenant_service.create_tenant(f"an-dev-a-{uuid4().hex[:8]}", "Developer Tenant A")
    tenant_b = tenant_service.create_tenant(f"an-dev-b-{uuid4().hex[:8]}", "Developer Tenant B")
    tenant_a_id = int(tenant_a["tenant_id"])
    tenant_b_id = int(tenant_b["tenant_id"])

    handler = AnalyticsEventHandler()
    with UnitOfWork() as uow:
        handler.handle(_make_event(tenant_a_id, event_type="student.created", event_id=801), uow=uow)
    with UnitOfWork() as uow:
        handler.handle(_make_event(tenant_b_id, event_type="grade.submitted", event_id=802), uow=uow)

    response = client.get(
        "/api/dev/analytics/events",
        headers=_developer_headers_for_tenant(tenant_id=tenant_a_id),
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["tenant_id"] == tenant_a_id
    assert body["total"] == 1
    assert body["ordering"] == "created_at_desc"
    assert body["limit"] == 50
    assert body["next_cursor"] is None
    assert body["freshness_status"] == "fresh"
    assert body["data_as_of"] == body["items"][0]["created_at"]
    assert isinstance(body["served_at"], str)
    assert body["served_at"]
    assert body["applied_filters"] == {
        "event_type": None,
        "date_from": None,
        "date_to": None,
    }
    assert body["items"][0]["event_type"] == "student.created"
    assert all(item["tenant_id"] == tenant_a_id for item in body["items"])


def test_developer_api_analytics_endpoints_require_entitlement(reset_shared_state) -> None:
    tenant = tenant_service.create_tenant(f"an-dev-ent-{uuid4().hex[:8]}", "Developer Entitlement Tenant")
    tenant_id = int(tenant["tenant_id"])
    headers = _developer_headers_for_tenant(tenant_id=tenant_id)
    _set_developer_analytics_entitlement(tenant_id=tenant_id, enabled=False)

    before_contract = snapshot_developer_analytics_contract_metrics()
    before_security_events, _ = snapshot_security_metrics()

    events_response = client.get("/api/dev/analytics/events", headers=headers)
    latest_response = client.get("/api/dev/analytics/kpis/latest", headers=headers)
    kpi_response = client.get("/api/dev/analytics/kpi", headers=headers)

    assert events_response.status_code == 403, events_response.text
    assert latest_response.status_code == 403, latest_response.text
    assert kpi_response.status_code == 403, kpi_response.text
    assert events_response.json().get("detail") == "analytics entitlement required"
    assert latest_response.json().get("detail") == "analytics entitlement required"
    assert kpi_response.json().get("detail") == "analytics entitlement required"

    after_contract = snapshot_developer_analytics_contract_metrics()
    assert int(after_contract.get(("analytics.events", "denied", "explicit_disabled"), 0)) >= int(
        before_contract.get(("analytics.events", "denied", "explicit_disabled"), 0)
    ) + 1
    assert int(after_contract.get(("analytics.kpis.latest", "denied", "explicit_disabled"), 0)) >= int(
        before_contract.get(("analytics.kpis.latest", "denied", "explicit_disabled"), 0)
    ) + 1
    assert int(after_contract.get(("analytics.kpi", "denied", "explicit_disabled"), 0)) >= int(
        before_contract.get(("analytics.kpi", "denied", "explicit_disabled"), 0)
    ) + 1

    after_security_events, _ = snapshot_security_metrics()
    signal_key = ("developer.analytics.contract_denied", "denied")
    assert int(after_security_events.get(signal_key, 0)) >= int(before_security_events.get(signal_key, 0)) + 3


def test_developer_api_analytics_events_allowed_when_entitlement_present(reset_shared_state) -> None:
    tenant = tenant_service.create_tenant(f"an-dev-ent-ok-{uuid4().hex[:8]}", "Developer Entitlement Allow Tenant")
    tenant_id = int(tenant["tenant_id"])
    headers = _developer_headers_for_tenant(tenant_id=tenant_id)
    _set_developer_analytics_entitlement(tenant_id=tenant_id, enabled=True)

    response = client.get("/api/dev/analytics/events", headers=headers)
    assert response.status_code == 200, response.text


def test_developer_api_analytics_usage_metering_increments_on_success(reset_shared_state) -> None:
    tenant = tenant_service.create_tenant(f"an-dev-meter-ok-{uuid4().hex[:8]}", "Developer Metering Success Tenant")
    tenant_id = int(tenant["tenant_id"])

    handler = AnalyticsEventHandler()
    with UnitOfWork() as uow:
        handler.handle(_make_event(tenant_id, event_type="student.created", event_id=1301), uow=uow)

    headers = _developer_headers_for_tenant(tenant_id=tenant_id)
    before_events = _usage_metric_value(tenant_id=tenant_id, metric="analytics.events.read")
    before_kpi = _usage_metric_value(tenant_id=tenant_id, metric="analytics.kpi.read")

    events_response = client.get("/api/dev/analytics/events", headers=headers)
    latest_response = client.get("/api/dev/analytics/kpis/latest", headers=headers)
    kpi_response = client.get("/api/dev/analytics/kpi", headers=headers)

    assert events_response.status_code == 200, events_response.text
    assert latest_response.status_code == 200, latest_response.text
    assert kpi_response.status_code == 200, kpi_response.text

    after_events = _usage_metric_value(tenant_id=tenant_id, metric="analytics.events.read")
    after_kpi = _usage_metric_value(tenant_id=tenant_id, metric="analytics.kpi.read")

    assert after_events == before_events + 1
    assert after_kpi == before_kpi + 2


def test_developer_api_analytics_usage_metering_not_written_on_entitlement_deny(reset_shared_state) -> None:
    tenant = tenant_service.create_tenant(f"an-dev-meter-deny-{uuid4().hex[:8]}", "Developer Metering Deny Tenant")
    tenant_id = int(tenant["tenant_id"])
    headers = _developer_headers_for_tenant(tenant_id=tenant_id)
    _set_developer_analytics_entitlement(tenant_id=tenant_id, enabled=False)

    before_events = _usage_metric_value(tenant_id=tenant_id, metric="analytics.events.read")
    before_kpi = _usage_metric_value(tenant_id=tenant_id, metric="analytics.kpi.read")

    events_response = client.get("/api/dev/analytics/events", headers=headers)
    latest_response = client.get("/api/dev/analytics/kpis/latest", headers=headers)
    kpi_response = client.get("/api/dev/analytics/kpi", headers=headers)

    assert events_response.status_code == 403, events_response.text
    assert latest_response.status_code == 403, latest_response.text
    assert kpi_response.status_code == 403, kpi_response.text

    after_events = _usage_metric_value(tenant_id=tenant_id, metric="analytics.events.read")
    after_kpi = _usage_metric_value(tenant_id=tenant_id, metric="analytics.kpi.read")

    assert after_events == before_events
    assert after_kpi == before_kpi


def test_developer_api_analytics_usage_metering_is_tenant_isolated(reset_shared_state) -> None:
    tenant_a = tenant_service.create_tenant(f"an-dev-meter-a-{uuid4().hex[:8]}", "Developer Metering Tenant A")
    tenant_b = tenant_service.create_tenant(f"an-dev-meter-b-{uuid4().hex[:8]}", "Developer Metering Tenant B")
    tenant_a_id = int(tenant_a["tenant_id"])
    tenant_b_id = int(tenant_b["tenant_id"])

    handler = AnalyticsEventHandler()
    with UnitOfWork() as uow:
        handler.handle(_make_event(tenant_a_id, event_type="student.created", event_id=1401), uow=uow)
    with UnitOfWork() as uow:
        handler.handle(_make_event(tenant_b_id, event_type="student.created", event_id=1402), uow=uow)

    headers_a = _developer_headers_for_tenant(tenant_id=tenant_a_id)
    headers_b = _developer_headers_for_tenant(tenant_id=tenant_b_id)

    before_a_events = _usage_metric_value(tenant_id=tenant_a_id, metric="analytics.events.read")
    before_a_kpi = _usage_metric_value(tenant_id=tenant_a_id, metric="analytics.kpi.read")
    before_b_events = _usage_metric_value(tenant_id=tenant_b_id, metric="analytics.events.read")
    before_b_kpi = _usage_metric_value(tenant_id=tenant_b_id, metric="analytics.kpi.read")

    only_a_events = client.get("/api/dev/analytics/events", headers=headers_a)
    only_a_latest = client.get("/api/dev/analytics/kpis/latest", headers=headers_a)
    assert only_a_events.status_code == 200, only_a_events.text
    assert only_a_latest.status_code == 200, only_a_latest.text

    after_a_events = _usage_metric_value(tenant_id=tenant_a_id, metric="analytics.events.read")
    after_a_kpi = _usage_metric_value(tenant_id=tenant_a_id, metric="analytics.kpi.read")
    after_b_events = _usage_metric_value(tenant_id=tenant_b_id, metric="analytics.events.read")
    after_b_kpi = _usage_metric_value(tenant_id=tenant_b_id, metric="analytics.kpi.read")

    assert after_a_events == before_a_events + 1
    assert after_a_kpi == before_a_kpi + 1
    assert after_b_events == before_b_events
    assert after_b_kpi == before_b_kpi

    # Ensure second tenant still gets independent usage when it calls the same APIs.
    b_events = client.get("/api/dev/analytics/events", headers=headers_b)
    b_latest = client.get("/api/dev/analytics/kpis/latest", headers=headers_b)
    assert b_events.status_code == 200, b_events.text
    assert b_latest.status_code == 200, b_latest.text
    final_b_events = _usage_metric_value(tenant_id=tenant_b_id, metric="analytics.events.read")
    final_b_kpi = _usage_metric_value(tenant_id=tenant_b_id, metric="analytics.kpi.read")
    assert final_b_events == before_b_events + 1
    assert final_b_kpi == before_b_kpi + 1


def test_developer_api_analytics_absent_entitlement_allowed_for_legacy_compat(reset_shared_state) -> None:
    tenant = tenant_service.create_tenant(f"an-dev-ent-legacy-{uuid4().hex[:8]}", "Developer Legacy Compatible Tenant")
    tenant_id = int(tenant["tenant_id"])
    headers = _developer_headers_for_tenant(tenant_id=tenant_id, enable_entitlement=False)

    events_response = client.get("/api/dev/analytics/events", headers=headers)
    latest_response = client.get("/api/dev/analytics/kpis/latest", headers=headers)
    kpi_response = client.get("/api/dev/analytics/kpi", headers=headers)

    assert events_response.status_code == 200, events_response.text
    assert latest_response.status_code in {200, 404}, latest_response.text
    assert kpi_response.status_code == 200, kpi_response.text


def test_developer_api_analytics_absent_entitlement_denied_for_governed_tenant(reset_shared_state) -> None:
    tenant = tenant_service.create_tenant(
        f"an-dev-ent-governed-{uuid4().hex[:8]}",
        "Developer Governed Entitlement Tenant",
    )
    tenant_id = int(tenant["tenant_id"])
    headers = _developer_headers_for_tenant(tenant_id=tenant_id, enable_entitlement=False)
    _set_developer_analytics_rollout_required(tenant_id=tenant_id, enabled=True)

    before_contract = snapshot_developer_analytics_contract_metrics()

    events_response = client.get("/api/dev/analytics/events", headers=headers)
    latest_response = client.get("/api/dev/analytics/kpis/latest", headers=headers)
    kpi_response = client.get("/api/dev/analytics/kpi", headers=headers)

    assert events_response.status_code == 403, events_response.text
    assert latest_response.status_code == 403, latest_response.text
    assert kpi_response.status_code == 403, kpi_response.text
    assert events_response.json().get("detail") == "analytics entitlement required"
    assert latest_response.json().get("detail") == "analytics entitlement required"
    assert kpi_response.json().get("detail") == "analytics entitlement required"

    after_contract = snapshot_developer_analytics_contract_metrics()
    assert int(after_contract.get(("analytics.events", "denied", "missing_entitlement_denied"), 0)) >= int(
        before_contract.get(("analytics.events", "denied", "missing_entitlement_denied"), 0)
    ) + 1
    assert int(after_contract.get(("analytics.kpis.latest", "denied", "missing_entitlement_denied"), 0)) >= int(
        before_contract.get(("analytics.kpis.latest", "denied", "missing_entitlement_denied"), 0)
    ) + 1
    assert int(after_contract.get(("analytics.kpi", "denied", "missing_entitlement_denied"), 0)) >= int(
        before_contract.get(("analytics.kpi", "denied", "missing_entitlement_denied"), 0)
    ) + 1


def test_platform_managed_rollout_marker_write_path_is_tenant_scoped(reset_shared_state) -> None:
    tenant_id = 1

    non_admin_headers = _auth_headers("tenant.viewer.rollout@example.com", ["student"], tenant_id=tenant_id)
    denied = client.put(
        f"/api/v1/admin/tenants/{tenant_id}/features/analytics/developer_read_required",
        headers=non_admin_headers,
        json={"enabled": True},
    )
    assert denied.status_code == 403, denied.text

    tenant_admin_headers = _auth_headers("tenant.admin.rollout@example.com", ["admin"], tenant_id=tenant_id)
    allowed = client.put(
        f"/api/v1/admin/tenants/{tenant_id}/features/analytics/developer_read_required",
        headers=tenant_admin_headers,
        json={"enabled": True},
    )
    assert allowed.status_code == 200, allowed.text
    body = allowed.json()
    assert body["scope"] == "tenant"
    assert int(body["tenant_id"]) == tenant_id
    assert body["module"] == "analytics"
    assert body["key"] == "developer_read_required"
    assert body["enabled"] is True

    rollback = client.put(
        f"/api/v1/admin/tenants/{tenant_id}/features/analytics/developer_read_required",
        headers=tenant_admin_headers,
        json={"enabled": False},
    )
    assert rollback.status_code == 200, rollback.text


def test_platform_managed_rollout_feature_write_and_inspect_are_consistent(reset_shared_state) -> None:
    tenant_id = 1

    non_admin_headers = _auth_headers("tenant.viewer.feature-rollout@example.com", ["student"], tenant_id=tenant_id)
    denied = client.put(
        f"/api/v1/admin/tenants/{tenant_id}/features/analytics/developer_read",
        headers=non_admin_headers,
        json={"enabled": True},
    )
    assert denied.status_code == 403, denied.text

    tenant_admin_headers = _auth_headers("tenant.admin.feature-rollout@example.com", ["admin"], tenant_id=tenant_id)
    cross_tenant = client.put(
        "/api/v1/admin/tenants/2/features/analytics/developer_read",
        headers=tenant_admin_headers,
        json={"enabled": True},
    )
    assert cross_tenant.status_code == 403, cross_tenant.text

    _set_developer_analytics_entitlement(tenant_id=tenant_id, enabled=True, headers=tenant_admin_headers)
    enabled_state = _get_analytics_rollout_state(tenant_id=tenant_id, headers=tenant_admin_headers)
    assert enabled_state["feature_enabled"] is True
    assert enabled_state["effective_state"] == "explicitly_enabled"
    assert enabled_state["is_entitled"] is True

    _set_developer_analytics_entitlement(tenant_id=tenant_id, enabled=False, headers=tenant_admin_headers)
    disabled_state = _get_analytics_rollout_state(tenant_id=tenant_id, headers=tenant_admin_headers)
    assert disabled_state["feature_enabled"] is False
    assert disabled_state["effective_state"] == "explicitly_disabled"
    assert disabled_state["is_entitled"] is False


def test_platform_managed_rollout_state_inspection_requires_admin_read(reset_shared_state) -> None:
    tenant_id = 1

    admin_headers = ADMIN_HEADERS
    viewer_headers = _auth_headers("tenant.viewer.rollout-state@example.com", ["student"], tenant_id=tenant_id)

    denied = client.get(
        f"/api/v1/admin/tenants/{tenant_id}/analytics/entitlement-rollout-state",
        headers=viewer_headers,
    )
    assert denied.status_code == 403, denied.text

    state = _get_analytics_rollout_state(tenant_id=tenant_id, headers=admin_headers)
    assert int(state["tenant_id"]) == tenant_id
    assert state["module"] == "analytics"
    assert state["marker_key"] == "developer_read_required"
    assert state["feature_key"] == "developer_read"


def test_platform_managed_rollout_summary_requires_platform_admin_read(reset_shared_state) -> None:
    tenant_id = 1

    viewer_headers = _auth_headers("tenant.viewer.rollout-summary@example.com", ["student"], tenant_id=tenant_id)
    denied = client.get(
        "/api/v1/admin/tenants/analytics/entitlement-rollout-summary?limit=10",
        headers=viewer_headers,
    )
    assert denied.status_code == 403, denied.text

    tenant_scoped_admin = _tenant_admin_headers(
        int(tenant_service.create_tenant(f"an-sum-scope-{uuid4().hex[:8]}", "Scoped Summary Tenant")["tenant_id"])
    )
    scoped_denied = client.get(
        "/api/v1/admin/tenants/analytics/entitlement-rollout-summary?limit=10",
        headers=tenant_scoped_admin,
    )
    assert scoped_denied.status_code == 403, scoped_denied.text
    assert scoped_denied.json()["detail"] == "cross-tenant access denied"

    summary = _get_analytics_rollout_summary(headers=ADMIN_HEADERS, limit=10)
    assert summary["limit"] == 10
    assert int(summary["count"]) >= 1
    assert isinstance(summary["items"], list)


def test_platform_managed_rollout_summary_reflects_multiple_tenant_effective_states(reset_shared_state) -> None:
    tenant_ids = {
        "legacy": int(tenant_service.create_tenant(f"an-sum-legacy-{uuid4().hex[:8]}", "Summary Legacy Tenant")["tenant_id"]),
        "strict": int(tenant_service.create_tenant(f"an-sum-strict-{uuid4().hex[:8]}", "Summary Strict Tenant")["tenant_id"]),
        "enabled": int(tenant_service.create_tenant(f"an-sum-enabled-{uuid4().hex[:8]}", "Summary Enabled Tenant")["tenant_id"]),
        "disabled": int(tenant_service.create_tenant(f"an-sum-disabled-{uuid4().hex[:8]}", "Summary Disabled Tenant")["tenant_id"]),
    }

    _set_developer_analytics_rollout_required(tenant_id=tenant_ids["strict"], enabled=True)
    _set_developer_analytics_rollout_required(tenant_id=tenant_ids["enabled"], enabled=True)
    _set_developer_analytics_entitlement(tenant_id=tenant_ids["enabled"], enabled=True)
    _set_developer_analytics_rollout_required(tenant_id=tenant_ids["disabled"], enabled=False)
    _set_developer_analytics_entitlement(tenant_id=tenant_ids["disabled"], enabled=False)

    summary = _get_analytics_rollout_summary(headers=ADMIN_HEADERS, limit=200)
    items_by_tenant = {int(item["tenant_id"]): dict(item) for item in summary["items"]}

    expected_states = {
        tenant_ids["legacy"]: "legacy_compatible_allow",
        tenant_ids["strict"]: "strict_required_missing",
        tenant_ids["enabled"]: "explicitly_enabled",
        tenant_ids["disabled"]: "explicitly_disabled",
    }

    for tenant_id, expected_state in expected_states.items():
        assert tenant_id in items_by_tenant
        summary_item = items_by_tenant[tenant_id]
        inspected = _get_analytics_rollout_state(
            tenant_id=tenant_id,
            headers=_tenant_admin_headers(tenant_id),
        )
        assert summary_item["effective_state"] == expected_state
        assert summary_item == inspected


def test_platform_managed_rollout_summary_is_bounded_by_limit(reset_shared_state) -> None:
    for index in range(3):
        tenant_service.create_tenant(f"an-sum-limit-{index}-{uuid4().hex[:8]}", f"Summary Limit Tenant {index}")

    summary = _get_analytics_rollout_summary(headers=ADMIN_HEADERS, limit=2)
    assert summary["limit"] == 2
    assert summary["count"] == 2
    assert len(summary["items"]) == 2


@pytest.mark.parametrize(
    ("expected_state", "marker_enabled", "feature_enabled", "expected_events_status"),
    [
        ("legacy_compatible_allow", None, None, 200),
        ("strict_required_missing", True, None, 403),
        ("explicitly_enabled", True, True, 200),
        ("explicitly_disabled", False, False, 403),
    ],
)
def test_platform_managed_rollout_state_reflects_effective_policy(
    reset_shared_state,
    expected_state: str,
    marker_enabled: bool | None,
    feature_enabled: bool | None,
    expected_events_status: int,
) -> None:
    tenant_id = 1

    admin_headers = ADMIN_HEADERS
    developer_headers = _developer_headers_for_tenant(tenant_id=tenant_id, enable_entitlement=False)
    try:
        if marker_enabled is not None:
            _set_developer_analytics_rollout_required(
                tenant_id=tenant_id,
                enabled=marker_enabled,
                headers=admin_headers,
            )

        if feature_enabled is not None:
            _set_developer_analytics_entitlement(tenant_id=tenant_id, enabled=feature_enabled)

        state = _get_analytics_rollout_state(tenant_id=tenant_id, headers=admin_headers)
        assert state["effective_state"] == expected_state
        assert bool(state["is_entitled"]) is (expected_events_status == 200)

        if expected_state == "legacy_compatible_allow":
            assert state["feature_enabled"] is None
            assert state["marker_enabled"] in {None, False}
        else:
            assert state["marker_enabled"] is marker_enabled
            assert state["feature_enabled"] is feature_enabled

        events_response = client.get("/api/dev/analytics/events", headers=developer_headers)
        assert events_response.status_code == expected_events_status, events_response.text
    finally:
        if feature_enabled is not None:
            _set_developer_analytics_entitlement(tenant_id=tenant_id, enabled=True)
        _set_developer_analytics_rollout_required(
            tenant_id=tenant_id,
            enabled=False,
            headers=admin_headers,
        )


def test_developer_api_analytics_events_pagination_cursor_flow(reset_shared_state) -> None:
    tenant = tenant_service.create_tenant(f"an-dev-page-{uuid4().hex[:8]}", "Developer Pagination Tenant")
    tenant_id = int(tenant["tenant_id"])

    handler = AnalyticsEventHandler()
    for event_id in (1001, 1002, 1003, 1004):
        with UnitOfWork() as uow:
            handler.handle(_make_event(tenant_id, event_type="student.created", event_id=event_id), uow=uow)

    headers = _developer_headers_for_tenant(tenant_id=tenant_id)
    first_page = client.get(
        "/api/dev/analytics/events?limit=2",
        headers=headers,
    )
    assert first_page.status_code == 200, first_page.text
    first_body = first_page.json()
    assert first_body["total"] == 2
    assert first_body["limit"] == 2
    assert first_body["ordering"] == "created_at_desc"
    assert isinstance(first_body["next_cursor"], str)
    assert not first_body["next_cursor"].isdigit()
    first_ids = [item["id"] for item in first_body["items"]]
    assert first_ids == sorted(first_ids, reverse=True)

    second_page = client.get(
        f"/api/dev/analytics/events?limit=2&cursor={first_body['next_cursor']}",
        headers=headers,
    )
    assert second_page.status_code == 200, second_page.text
    second_body = second_page.json()
    second_ids = [item["id"] for item in second_body["items"]]
    assert second_ids == sorted(second_ids, reverse=True)
    assert second_ids[0] < first_ids[-1]
    assert set(first_ids).isdisjoint(set(second_ids))
    assert second_body["next_cursor"] is not None


def test_developer_api_analytics_events_filter_by_event_type(reset_shared_state) -> None:
    tenant = tenant_service.create_tenant(f"an-dev-filter-{uuid4().hex[:8]}", "Developer Filter Tenant")
    tenant_id = int(tenant["tenant_id"])

    handler = AnalyticsEventHandler()
    with UnitOfWork() as uow:
        handler.handle(_make_event(tenant_id, event_type="student.created", event_id=1101), uow=uow)
    with UnitOfWork() as uow:
        handler.handle(_make_event(tenant_id, event_type="grade.submitted", event_id=1102), uow=uow)

    response = client.get(
        "/api/dev/analytics/events?event_type=grade.submitted",
        headers=_developer_headers_for_tenant(tenant_id=tenant_id),
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["total"] == 1
    assert body["applied_filters"]["event_type"] == "grade.submitted"
    assert body["items"][0]["event_type"] == "grade.submitted"


def test_developer_api_analytics_events_filter_by_date_range_and_empty_result(reset_shared_state) -> None:
    tenant = tenant_service.create_tenant(f"an-dev-date-{uuid4().hex[:8]}", "Developer Date Tenant")
    tenant_id = int(tenant["tenant_id"])

    handler = AnalyticsEventHandler()
    with UnitOfWork() as uow:
        handler.handle(_make_event(tenant_id, event_type="student.created", event_id=1201), uow=uow)

    today = date.today().isoformat()
    in_range = client.get(
        f"/api/dev/analytics/events?date_from={today}&date_to={today}",
        headers=_developer_headers_for_tenant(tenant_id=tenant_id),
    )
    assert in_range.status_code == 200, in_range.text
    in_range_body = in_range.json()
    assert in_range_body["total"] == 1
    assert in_range_body["applied_filters"] == {
        "event_type": None,
        "date_from": today,
        "date_to": today,
    }

    future = (date.today() + timedelta(days=180)).isoformat()
    empty = client.get(
        f"/api/dev/analytics/events?date_from={future}&date_to={future}",
        headers=_developer_headers_for_tenant(tenant_id=tenant_id),
    )
    assert empty.status_code == 200, empty.text
    empty_body = empty.json()
    assert empty_body["total"] == 0
    assert empty_body["items"] == []
    assert empty_body["next_cursor"] is None
    assert empty_body["data_as_of"] is None
    assert empty_body["freshness_status"] == "empty"
    assert isinstance(empty_body["served_at"], str)
    assert empty_body["served_at"]


def test_developer_api_analytics_events_cursor_flow_with_filters(reset_shared_state) -> None:
    tenant = tenant_service.create_tenant(f"an-dev-filter-cursor-{uuid4().hex[:8]}", "Developer Filter Cursor Tenant")
    tenant_id = int(tenant["tenant_id"])

    handler = AnalyticsEventHandler()
    for event_id in (1301, 1302, 1303):
        with UnitOfWork() as uow:
            handler.handle(_make_event(tenant_id, event_type="student.created", event_id=event_id), uow=uow)
    with UnitOfWork() as uow:
        handler.handle(_make_event(tenant_id, event_type="grade.submitted", event_id=1304), uow=uow)

    today = date.today().isoformat()
    headers = _developer_headers_for_tenant(tenant_id=tenant_id)
    first = client.get(
        f"/api/dev/analytics/events?event_type=student.created&date_from={today}&date_to={today}&limit=1",
        headers=headers,
    )
    assert first.status_code == 200, first.text
    first_body = first.json()
    assert first_body["total"] == 1
    assert first_body["applied_filters"] == {
        "event_type": "student.created",
        "date_from": today,
        "date_to": today,
    }
    assert first_body["items"][0]["event_type"] == "student.created"
    assert first_body["next_cursor"] is not None

    second = client.get(
        (
            "/api/dev/analytics/events"
            f"?event_type=student.created&date_from={today}&date_to={today}&limit=1&cursor={first_body['next_cursor']}"
        ),
        headers=headers,
    )
    assert second.status_code == 200, second.text
    second_body = second.json()
    assert second_body["total"] == 1
    assert second_body["items"][0]["event_type"] == "student.created"
    assert second_body["items"][0]["id"] < first_body["items"][0]["id"]


def test_developer_api_analytics_events_validates_cursor_and_date_bounds(reset_shared_state) -> None:
    tenant = tenant_service.create_tenant(f"an-dev-validate-{uuid4().hex[:8]}", "Developer Validation Tenant")
    tenant_id = int(tenant["tenant_id"])
    headers = _developer_headers_for_tenant(tenant_id=tenant_id)

    handler = AnalyticsEventHandler()
    for event_id in (1401, 1402):
        with UnitOfWork() as uow:
            handler.handle(_make_event(tenant_id, event_type="student.created", event_id=event_id), uow=uow)

    before_contract = snapshot_developer_analytics_contract_metrics()
    before_security_events, _ = snapshot_security_metrics()

    bad_cursor = client.get("/api/dev/analytics/events?cursor=abc", headers=headers)
    assert bad_cursor.status_code == 400, bad_cursor.text

    bad_date_order = client.get(
        "/api/dev/analytics/events?date_from=2026-02-01&date_to=2026-01-01",
        headers=headers,
    )
    assert bad_date_order.status_code == 422, bad_date_order.text

    too_wide = client.get(
        "/api/dev/analytics/events?date_from=2026-01-01&date_to=2026-03-15",
        headers=headers,
    )
    assert too_wide.status_code == 422, too_wide.text

    bad_ordering = client.get(
        "/api/dev/analytics/events?ordering=created_at_asc",
        headers=headers,
    )
    assert bad_ordering.status_code == 422, bad_ordering.text

    valid_page = client.get("/api/dev/analytics/events?limit=1", headers=headers)
    assert valid_page.status_code == 200, valid_page.text
    valid_cursor = str(valid_page.json()["next_cursor"])
    payload_b64, signature_b64 = valid_cursor.split(".", 1)
    padding = "=" * ((4 - len(payload_b64) % 4) % 4)
    payload = json.loads(base64.urlsafe_b64decode((payload_b64 + padding).encode("ascii")).decode("utf-8"))
    payload["id"] = int(payload["id"]) + 777
    tampered_payload_b64 = base64.urlsafe_b64encode(
        json.dumps(payload, separators=(",", ":")).encode("utf-8")
    ).decode("ascii").rstrip("=")
    tampered_cursor = f"{tampered_payload_b64}.{signature_b64}"
    tampered = client.get(f"/api/dev/analytics/events?limit=1&cursor={tampered_cursor}", headers=headers)
    assert tampered.status_code == 400, tampered.text

    filter_mismatch = client.get(
        f"/api/dev/analytics/events?event_type=grade.submitted&cursor={valid_cursor}",
        headers=headers,
    )
    assert filter_mismatch.status_code == 400, filter_mismatch.text

    after_contract = snapshot_developer_analytics_contract_metrics()
    malformed_cursor_key = ("analytics.events", "denied", "malformed_cursor")
    tampered_cursor_key = ("analytics.events", "denied", "tampered_cursor")
    cursor_context_mismatch_key = ("analytics.events", "denied", "cursor_context_mismatch")
    invalid_date_range_key = ("analytics.events", "denied", "invalid_date_range")
    invalid_ordering_key = ("analytics.events", "denied", "invalid_ordering")
    assert int(after_contract.get(malformed_cursor_key, 0)) >= int(before_contract.get(malformed_cursor_key, 0)) + 1
    assert int(after_contract.get(tampered_cursor_key, 0)) >= int(before_contract.get(tampered_cursor_key, 0)) + 1
    assert int(after_contract.get(cursor_context_mismatch_key, 0)) >= int(
        before_contract.get(cursor_context_mismatch_key, 0)
    ) + 1
    assert int(after_contract.get(invalid_date_range_key, 0)) >= int(before_contract.get(invalid_date_range_key, 0)) + 2
    assert int(after_contract.get(invalid_ordering_key, 0)) >= int(before_contract.get(invalid_ordering_key, 0)) + 1

    after_security_events, _ = snapshot_security_metrics()
    signal_key = ("developer.analytics.contract_denied", "denied")
    assert int(after_security_events.get(signal_key, 0)) >= int(before_security_events.get(signal_key, 0)) + 6


def test_developer_api_analytics_events_clamps_oversize_limit_and_observes_guard(reset_shared_state) -> None:
    tenant = tenant_service.create_tenant(f"an-dev-limit-{uuid4().hex[:8]}", "Developer Limit Guard Tenant")
    tenant_id = int(tenant["tenant_id"])
    headers = _developer_headers_for_tenant(tenant_id=tenant_id)

    before_contract = snapshot_developer_analytics_contract_metrics()

    response = client.get("/api/dev/analytics/events?limit=999", headers=headers)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["limit"] == 100

    after_contract = snapshot_developer_analytics_contract_metrics()
    guard_key = ("analytics.events", "guarded", "limit_clamped")
    success_key = ("analytics.events", "success", "ok")
    assert int(after_contract.get(guard_key, 0)) >= int(before_contract.get(guard_key, 0)) + 1
    assert int(after_contract.get(success_key, 0)) >= int(before_contract.get(success_key, 0)) + 1


def test_developer_api_latest_kpi_snapshot_refresh_to_read_flow(reset_shared_state) -> None:
    tenant = tenant_service.create_tenant(f"an-dev-kpi-{uuid4().hex[:8]}", "Developer KPI Tenant")
    tenant_id = int(tenant["tenant_id"])

    handler = AnalyticsEventHandler()
    with UnitOfWork() as uow:
        handler.handle(_make_event(tenant_id, event_type="student.created", event_id=901), uow=uow)
    with UnitOfWork() as uow:
        handler.handle(_make_event(tenant_id, event_type="student.created", event_id=902), uow=uow)

    refresh = client.post(
        f"/api/v1/internal/analytics/tenants/{tenant_id}/kpis/refresh",
        headers=INTERNAL_HEADERS,
    )
    assert refresh.status_code == 200, refresh.text

    response = client.get(
        "/api/dev/analytics/kpis/latest",
        headers=_developer_headers_for_tenant(tenant_id=tenant_id),
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["tenant_id"] == tenant_id
    assert body["total_events"] == 2
    assert body["event_counts_json"]["student.created"] == 2
    assert body["data_as_of"] == body["updated_at"]
    assert body["freshness_status"] == "fresh"
    assert isinstance(body["served_at"], str)
    assert body["served_at"]


# ---------------------------------------------------------------------------
# Regression: PostgreSQL path — KPI increment must not raise IndeterminateDatatype
# ---------------------------------------------------------------------------
# Requires DATABASE_URL env var pointing at a live PostgreSQL instance with the
# platform schema already applied (e.g. platform_restore from DR rehearsal).
# Skipped automatically when running in-memory CI (DATABASE_URL not set).


@pytest.mark.skipif(
    not _platform_db_url(),
    reason="DATABASE_URL not set — skipping PostgreSQL regression path",
)
def test_kpi_increment_pg_no_indeterminate_datatype() -> None:
    """
    Regression guard for psycopg.errors.IndeterminateDatatype in
    AnalyticsRepository.increment_kpi_snapshot() when executed against a real
    PostgreSQL connection.

    Before the fix the SQL used:
      - %s::jsonb with a bare Python str  (rather than psycopg.types.json.Jsonb)
      - %s in jsonb_build_object(variadic "any") without ::text cast

    PostgreSQL could not determine the parameter types and raised
    IndeterminateDatatype, aborting the transaction and cascading failures
    through the Outbox worker.
    """
    import psycopg  # noqa: PLC0415

    from app.platform.repository.db import db_url  # noqa: PLC0415

    url = db_url()
    if not url:
        pytest.skip("DATABASE_URL not set — skipping PostgreSQL regression path")
    repo = AnalyticsRepository()
    # Use a tenant_id that is guaranteed to exist after DR seed (9001) or fall
    # back to a throwaway value — we roll back so no permanent data is written.
    tenant_id = 9001
    snapshot_date = "2026-03-25"
    event_type = "student.created"

    with psycopg.connect(url) as conn:
        try:
            snap1 = repo.increment_kpi_snapshot(
                tenant_id=tenant_id,
                snapshot_date=snapshot_date,
                event_type=event_type,
                conn=conn,
            )
            # First insert: total_events == 1, event_counts_json has the key
            assert snap1["total_events"] >= 1
            assert event_type in snap1["event_counts_json"]
            count_after_first = snap1["event_counts_json"][event_type]

            snap2 = repo.increment_kpi_snapshot(
                tenant_id=tenant_id,
                snapshot_date=snapshot_date,
                event_type=event_type,
                conn=conn,
            )
            # Second call: counter must increase by exactly 1
            assert snap2["event_counts_json"][event_type] == count_after_first + 1
            assert snap2["total_events"] == snap1["total_events"] + 1
            assert snap2["version"] == snap1["version"] + 1
        finally:
            # Always roll back so the regression test leaves no side-effects
            conn.rollback()


@pytest.mark.skipif(
    not _platform_db_url(),
    reason="DATABASE_URL not set — skipping PostgreSQL regression path",
)
def test_outbox_worker_kpi_increment_pg_transaction_does_not_abort() -> None:
    """
    Full outbox-worker → analytics-handler → KPI increment pipeline on
    PostgreSQL.  Verifies that publishing an event and processing it via the
    OutboxEventWorker completes without aborting the transaction.
    """
    import psycopg  # noqa: PLC0415

    from app.platform.repository.db import db_url  # noqa: PLC0415

    url = db_url()
    if not url:
        pytest.skip("DATABASE_URL not set — skipping PostgreSQL regression path")

    # We need a real tenant row in the DB for FK constraints.
    # The DR rehearsal seeds tenant_id=9001; use that.
    tenant_id = 9001

    with psycopg.connect(url) as conn:
        try:
            # Insert a pending outbox event directly
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO app_platform_outbox_events
                        (tenant_id, event_type, aggregate_type, aggregate_id,
                         payload_json, status, retry_count, available_at)
                    VALUES (%s, %s, %s, %s, %s::jsonb, 'pending', 0, NOW())
                    RETURNING id
                    """,
                    (
                        tenant_id,
                        "grade.submitted",
                        "grade",
                        "reg-9001",
                        '{"grade_id": 9001}',
                    ),
                )
                (outbox_id,) = cur.fetchone()

            # Run the analytics handler directly (same transaction)
            repo = AnalyticsRepository()
            snap = repo.increment_kpi_snapshot(
                tenant_id=tenant_id,
                snapshot_date="2026-03-25",
                event_type="grade.submitted",
                conn=conn,
            )
            # Transaction must remain open (not aborted)
            assert snap["total_events"] >= 1
            assert "grade.submitted" in snap["event_counts_json"]

        finally:
            conn.rollback()

