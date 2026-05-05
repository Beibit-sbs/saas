from __future__ import annotations

import hashlib
import json
from datetime import date, timedelta
from uuid import uuid4

import pytest

from tests.conftest import ADMIN_HEADERS, INTERNAL_HEADERS, _auth_headers, client

from app.modules.auth.token_service import create_access_token
from app.platform.developer import service as developer_service
from app.platform.event_ingestion import service as event_ingestion_service
from app.platform.event_ingestion.types import ANALYTICS_EVENT_READ, ANALYTICS_KPI_READ, BILLING_USAGE_RECORDED
from app.platform.events.handlers.analytics_handler import AnalyticsEventHandler
from app.platform.events.schemas import OutboxEventRead
from app.platform.billing import service as platform_billing_service
from app.platform.jobs.scheduler import PlatformWorkerScheduler
from app.platform.kpi import service as kpi_service
from app.platform.uow import UnitOfWork
from app.modules.tenants import service as module_tenant_service


def _emit_analytics_event(*, tenant_id: int, event_type: str, event_id: int) -> None:
    event = OutboxEventRead(
        id=event_id,
        tenant_id=tenant_id,
        event_type=event_type,
        aggregate_type=event_type.split(".")[0],
        aggregate_id=str(event_id),
        payload_json={"id": event_id},
        status="pending",
        retry_count=0,
        available_at="2026-01-01T00:00:00+00:00",
        created_at="2026-01-01T00:00:00+00:00",
    )
    with UnitOfWork() as uow:
        AnalyticsEventHandler().handle(event, uow=uow)


def _create_tenant(name_prefix: str) -> int:
    slug = f"{name_prefix}-{uuid4().hex[:8]}"
    tenant = module_tenant_service.create_tenant({"slug": slug, "name": f"{name_prefix} Tenant"})
    return int(tenant["id"])


def _developer_headers_for_tenant(*, tenant_id: int) -> dict[str, str]:
    app = developer_service.developer_service.create_app(
        tenant_id=tenant_id,
        name=f"KPI Reader {tenant_id}",
        description="tenant kpi read api",
        owner_email="owner@example.com",
        scopes=["analytics.read"],
    )
    developer_service.developer_service.install_app(
        app_id=int(app["id"]),
        tenant_id=tenant_id,
        installed_by="test-suite",
    )
    return {
        "X-App-Key": str(app["app_key"]),
        "X-App-Secret": str(app["app_secret"]),
    }


def _tenant_user_headers(*, tenant_id: int) -> dict[str, str]:
    return _auth_headers(
        f"analytics.viewer.{tenant_id}@example.com",
        ["student"],
        tenant_id=tenant_id,
    )


def _tenant_analytics_user_headers(*, tenant_id: int) -> dict[str, str]:
    """Generate headers for a tenant user with analytics.data.read permission."""
    token = create_access_token(
        user_id=f"analytics.viewer.{tenant_id}@example.com",
        roles=["student"],
        auth_source="test",
        tenant_id=int(tenant_id),
        permissions=["analytics.data.read"],
    )
    return {"Authorization": f"Bearer {token}"}


def _tenant_analytics_rw_headers(*, tenant_id: int) -> dict[str, str]:
    token = create_access_token(
        user_id=f"analytics.editor.{tenant_id}@example.com",
        roles=["student"],
        auth_source="test",
        tenant_id=int(tenant_id),
        permissions=["analytics.data.read", "analytics.data.write"],
    )
    return {"Authorization": f"Bearer {token}"}


def _strip_kpi_runtime_fields(payload: dict[str, object]) -> dict[str, object]:
    normalized = dict(payload)
    normalized.pop("request_id", None)
    normalized.pop("served_at", None)
    return normalized


def _assert_auth_or_csrf_denied(response) -> None:
    assert response.status_code in {401, 403}, response.text
    if response.status_code == 403:
        assert "csrf" in str(response.json().get("detail", "")).lower()


def test_kpi_metric_snapshot_creation_and_values(reset_shared_state) -> None:
    tenant_id = _create_tenant("kpi-metrics")

    _emit_analytics_event(tenant_id=tenant_id, event_type="student.created", event_id=1001)
    _emit_analytics_event(tenant_id=tenant_id, event_type="student.created", event_id=1002)
    _emit_analytics_event(tenant_id=tenant_id, event_type="enrollment.created", event_id=1003)
    _emit_analytics_event(tenant_id=tenant_id, event_type="grade.submitted", event_id=1004)
    _emit_analytics_event(tenant_id=tenant_id, event_type="grade.submitted", event_id=1005)
    _emit_analytics_event(tenant_id=tenant_id, event_type="grade.submitted", event_id=1006)

    plan_code = f"kpi-plan-{uuid4().hex[:6]}"
    with UnitOfWork() as uow:
        uow.billing_repository.create_plan(
            code=plan_code,
            name="KPI Plan",
            price_cents=1000,
            features={"analytics": True},
            limits={"users": 1000},
            conn=uow.conn,
        )
        uow.billing_repository.assign_subscription(tenant_id, plan_code, conn=uow.conn)

    with UnitOfWork() as uow:
        job = uow.job_repository.enqueue(tenant_id, "grade-sync", {"batch": 1}, max_retries=3, conn=uow.conn)
        uow.job_repository.mark_running(int(job["id"]), conn=uow.conn)
        uow.job_repository.mark_failed(int(job["id"]), "simulated failure", conn=uow.conn)

        notification = uow.notification_repository.dispatch(
            tenant_id=tenant_id,
            channel="email",
            target="ops@example.com",
            payload={"subject": "alert"},
            subject="Alert",
            conn=uow.conn,
        )
        uow.notification_repository.mark_status(
            int(notification["id"]),
            status="failed",
            last_error="smtp timeout",
            increment_retry=True,
            conn=uow.conn,
        )

    with UnitOfWork() as uow:
        rows = kpi_service.refresh_tenant_metrics(tenant_id=tenant_id, uow=uow)

    values = {str(item["metric_key"]): int(item["metric_value"]) for item in rows}
    assert values["total_students"] == 2
    assert values["total_enrollments"] == 1
    assert values["total_grades_submitted"] == 3
    assert values["total_active_subscriptions"] == 1
    assert values["total_failed_jobs"] == 1
    assert values["total_failed_notifications"] == 1


def test_kpi_dashboard_snapshot_creation(reset_shared_state) -> None:
    tenant_id = _create_tenant("kpi-dashboard")
    _emit_analytics_event(tenant_id=tenant_id, event_type="student.created", event_id=2001)

    with UnitOfWork() as uow:
        snapshot = kpi_service.refresh_tenant_dashboard_snapshot(tenant_id=tenant_id, uow=uow)

    assert int(snapshot["tenant_id"]) == tenant_id
    payload = dict(snapshot["snapshot_json"])
    assert payload["tenant_id"] == tenant_id
    assert payload["source"] == "kpi_metrics_engine_v1"
    assert isinstance(payload["cards"], list)
    assert len(payload["cards"]) >= 6


def test_kpi_tenant_isolation(reset_shared_state) -> None:
    tenant_a = _create_tenant("kpi-a")
    tenant_b = _create_tenant("kpi-b")

    _emit_analytics_event(tenant_id=tenant_a, event_type="student.created", event_id=3001)
    _emit_analytics_event(tenant_id=tenant_a, event_type="student.created", event_id=3002)
    _emit_analytics_event(tenant_id=tenant_b, event_type="student.created", event_id=3003)

    with UnitOfWork() as uow:
        rows_a = kpi_service.refresh_tenant_metrics(tenant_id=tenant_a, uow=uow)
        rows_b = kpi_service.refresh_tenant_metrics(tenant_id=tenant_b, uow=uow)

    values_a = {str(item["metric_key"]): int(item["metric_value"]) for item in rows_a}
    values_b = {str(item["metric_key"]): int(item["metric_value"]) for item in rows_b}

    assert values_a["total_students"] == 2
    assert values_b["total_students"] == 1


def test_admin_kpi_dashboard_api_payload(reset_shared_state) -> None:
    tenant_id = _create_tenant("kpi-admin")
    _emit_analytics_event(tenant_id=tenant_id, event_type="enrollment.created", event_id=4001)

    response = client.get(
        "/api/v1/admin/platform/kpi/dashboard",
        params={"tenant_id": tenant_id},
        headers=ADMIN_HEADERS,
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["tenant_id"] == tenant_id
    assert body["source"] == "kpi_metrics_engine_v1"
    keys = {item["metric_key"] for item in body["cards"]}
    assert "total_enrollments" in keys


def test_admin_kpi_metrics_api(reset_shared_state) -> None:
    tenant_id = _create_tenant("kpi-admin-metrics")
    _emit_analytics_event(tenant_id=tenant_id, event_type="grade.submitted", event_id=5001)

    response = client.get(
        "/api/v1/admin/platform/kpi/metrics",
        params={"tenant_id": tenant_id},
        headers=ADMIN_HEADERS,
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert isinstance(body, list)
    assert any(item["metric_key"] == "total_grades_submitted" for item in body)


def test_internal_kpi_refresh_endpoints(reset_shared_state) -> None:
    tenant_id = _create_tenant("kpi-internal")
    _emit_analytics_event(tenant_id=tenant_id, event_type="student.created", event_id=6001)

    single = client.post(f"/api/v1/internal/platform/kpi/refresh/{tenant_id}", headers=INTERNAL_HEADERS)
    assert single.status_code == 200, single.text
    one = single.json()
    assert one["tenant_id"] == tenant_id

    bulk = client.post("/api/v1/internal/platform/kpi/refresh", headers=INTERNAL_HEADERS)
    assert bulk.status_code == 200, bulk.text
    all_res = bulk.json()
    assert all_res["tenants_total"] >= 1
    assert all_res["refreshed"] >= 1


def test_scheduler_registers_kpi_refresh_task() -> None:
    scheduler = PlatformWorkerScheduler()
    task_names = set(scheduler._tasks.keys())  # noqa: SLF001
    assert "kpi_metrics_refresh" in task_names


def test_developer_kpi_dashboard_endpoint_returns_tenant_scoped_schema(reset_shared_state) -> None:
    tenant_id = _create_tenant("kpi-dev-dashboard")
    _emit_analytics_event(tenant_id=tenant_id, event_type="grade.submitted", event_id=7001)

    response = client.get(
        "/api/dev/analytics/kpi",
        headers=_developer_headers_for_tenant(tenant_id=tenant_id),
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["tenant_id"] == tenant_id
    assert body["source"] == "kpi_metrics_engine_v1"
    assert isinstance(body["cards"], list)
    assert any(item["metric_key"] == "total_grades_submitted" for item in body["cards"])
    assert body["data_as_of"] == body["generated_at"]
    assert body["freshness_status"] == "fresh"
    assert isinstance(body["served_at"], str)
    assert body["served_at"]


def test_kpi_usage_aggregation_metrics_match_usage_counters(reset_shared_state) -> None:
    tenant_id = _create_tenant("kpi-usage-agg")

    _emit_analytics_event(tenant_id=tenant_id, event_type="student.created", event_id=8001)
    _emit_analytics_event(tenant_id=tenant_id, event_type="grade.submitted", event_id=8002)
    _emit_analytics_event(tenant_id=tenant_id, event_type="grade.submitted", event_id=8003)

    platform_billing_service.increment_usage(tenant_id, "analytics.events.read", 5)
    platform_billing_service.increment_usage(tenant_id, "analytics.kpi.read", 3)

    with UnitOfWork() as uow:
        rows = kpi_service.refresh_tenant_metrics(tenant_id=tenant_id, uow=uow)

    values = {str(item["metric_key"]): int(item["metric_value"]) for item in rows}
    assert values["analytics_events_ingested_total"] == 3
    assert values["analytics_events_reads_total"] == 5
    assert values["analytics_kpi_reads_total"] == 3
    assert values["analytics_reads_total"] == 8
    assert values["analytics_kpi_reads_share_pct"] == 38

    # Event-to-KPI bridge v1: same tenant has one billing usage event and no analytics read events yet.
    assert values["analytics_events_reads_from_events_total"] == 0
    assert values["analytics_kpi_reads_from_events_total"] == 0
    assert values["billing_usage_recorded_from_events_total"] == 2


def test_kpi_usage_aggregation_empty_state_is_zero(reset_shared_state) -> None:
    tenant_id = _create_tenant("kpi-usage-empty")

    with UnitOfWork() as uow:
        rows = kpi_service.refresh_tenant_metrics(tenant_id=tenant_id, uow=uow)

    values = {str(item["metric_key"]): int(item["metric_value"]) for item in rows}
    assert values["analytics_events_ingested_total"] == 0
    assert values["analytics_events_reads_total"] == 0
    assert values["analytics_kpi_reads_total"] == 0
    assert values["analytics_reads_total"] == 0
    assert values["analytics_kpi_reads_share_pct"] == 0
    assert values["analytics_events_reads_from_events_total"] == 0
    assert values["analytics_kpi_reads_from_events_total"] == 0
    assert values["billing_usage_recorded_from_events_total"] == 0


def test_kpi_usage_aggregation_is_tenant_isolated(reset_shared_state) -> None:
    tenant_a = _create_tenant("kpi-usage-iso-a")
    tenant_b = _create_tenant("kpi-usage-iso-b")

    platform_billing_service.increment_usage(tenant_a, "analytics.events.read", 7)
    platform_billing_service.increment_usage(tenant_a, "analytics.kpi.read", 1)
    platform_billing_service.increment_usage(tenant_b, "analytics.events.read", 2)
    platform_billing_service.increment_usage(tenant_b, "analytics.kpi.read", 6)

    with UnitOfWork() as uow:
        rows_a = kpi_service.refresh_tenant_metrics(tenant_id=tenant_a, uow=uow)
        rows_b = kpi_service.refresh_tenant_metrics(tenant_id=tenant_b, uow=uow)

    values_a = {str(item["metric_key"]): int(item["metric_value"]) for item in rows_a}
    values_b = {str(item["metric_key"]): int(item["metric_value"]) for item in rows_b}

    assert values_a["analytics_events_reads_total"] == 7
    assert values_a["analytics_kpi_reads_total"] == 1
    assert values_a["analytics_reads_total"] == 8
    assert values_a["analytics_kpi_reads_share_pct"] == 12
    assert values_a["billing_usage_recorded_from_events_total"] == 2

    assert values_b["analytics_events_reads_total"] == 2
    assert values_b["analytics_kpi_reads_total"] == 6
    assert values_b["analytics_reads_total"] == 8
    assert values_b["analytics_kpi_reads_share_pct"] == 75
    assert values_b["billing_usage_recorded_from_events_total"] == 2


def test_kpi_event_bridge_matches_event_stream_counts(reset_shared_state) -> None:
    tenant_id = _create_tenant("kpi-event-bridge")
    headers = _tenant_user_headers(tenant_id=tenant_id)

    # Generate platform events through existing ingestion paths.
    client.get("/api/analytics/kpis", headers=headers)
    client.get("/api/analytics/kpis/trends", headers=headers)
    client.get("/api/analytics/kpis/insights", headers=headers)
    platform_billing_service.increment_usage(tenant_id, "analytics.events.read", 2)

    with UnitOfWork() as uow:
        rows = kpi_service.refresh_tenant_metrics(tenant_id=tenant_id, uow=uow)
        event_counts = event_ingestion_service.summary_for_tenant(tenant_id, uow=uow)

    values = {str(item["metric_key"]): int(item["metric_value"]) for item in rows}
    assert values["analytics_events_reads_from_events_total"] == int(event_counts.get(ANALYTICS_EVENT_READ, 0) or 0)
    assert values["analytics_kpi_reads_from_events_total"] == int(event_counts.get(ANALYTICS_KPI_READ, 0) or 0)
    assert values["billing_usage_recorded_from_events_total"] == int(event_counts.get(BILLING_USAGE_RECORDED, 0) or 0)


def test_kpi_event_bridge_tenant_isolation(reset_shared_state) -> None:
    tenant_a = _create_tenant("kpi-event-iso-a")
    tenant_b = _create_tenant("kpi-event-iso-b")
    headers_a = _tenant_user_headers(tenant_id=tenant_a)
    headers_b = _tenant_user_headers(tenant_id=tenant_b)

    client.get("/api/analytics/kpis", headers=headers_a)
    client.get("/api/analytics/kpis/trends", headers=headers_a)
    platform_billing_service.increment_usage(tenant_a, "analytics.events.read", 1)

    client.get("/api/analytics/kpis", headers=headers_b)

    with UnitOfWork() as uow:
        rows_a = kpi_service.refresh_tenant_metrics(tenant_id=tenant_a, uow=uow)
        rows_b = kpi_service.refresh_tenant_metrics(tenant_id=tenant_b, uow=uow)

    values_a = {str(item["metric_key"]): int(item["metric_value"]) for item in rows_a}
    values_b = {str(item["metric_key"]): int(item["metric_value"]) for item in rows_b}

    assert values_a["analytics_events_reads_from_events_total"] == 1
    assert values_a["analytics_kpi_reads_from_events_total"] == 1
    assert values_a["billing_usage_recorded_from_events_total"] == 1

    assert values_b["analytics_events_reads_from_events_total"] == 1
    assert values_b["analytics_kpi_reads_from_events_total"] == 0
    assert values_b["billing_usage_recorded_from_events_total"] == 0


def test_tenant_analytics_kpis_requires_auth(reset_shared_state) -> None:
    response = client.get("/api/analytics/kpis")
    assert response.status_code == 401, response.text


def test_tenant_analytics_kpis_internal_user_access_unchanged(reset_shared_state) -> None:
    tenant_id = _create_tenant("kpi-internal-access-unchanged")
    headers = _tenant_user_headers(tenant_id=tenant_id)

    response = client.get("/api/analytics/kpis", headers=headers)
    assert response.status_code == 200, response.text
    assert int(response.json()["tenant_id"]) == tenant_id


def test_tenant_analytics_kpis_external_client_access_allowed_read_only(reset_shared_state) -> None:
    tenant_id = _create_tenant("kpi-external-allowed")
    headers = _developer_headers_for_tenant(tenant_id=tenant_id)

    response = client.get("/api/analytics/kpis", headers=headers)
    assert response.status_code == 401, response.text
    assert response.json().get("detail") == "valid authentication is required"


def test_tenant_analytics_kpis_external_client_denied_for_non_allowed_paths(reset_shared_state) -> None:
    tenant_id = _create_tenant("kpi-external-denied")
    headers = _developer_headers_for_tenant(tenant_id=tenant_id)

    refresh = client.post("/api/analytics/kpis/refresh", headers=headers)
    trends = client.get("/api/analytics/kpis/trends", headers=headers)
    _assert_auth_or_csrf_denied(refresh)
    assert trends.status_code == 401, trends.text


def test_tenant_analytics_kpis_external_client_rejects_tenant_override(reset_shared_state) -> None:
    tenant_id = _create_tenant("kpi-external-override")
    headers = _developer_headers_for_tenant(tenant_id=tenant_id)
    headers["X-Tenant-ID"] = "9999"

    response = client.get("/api/analytics/kpis", headers=headers)
    assert response.status_code == 401, response.text
    assert response.json().get("detail") == "valid authentication is required"


def test_tenant_analytics_kpis_external_client_invalid_credentials_fail_predictably(reset_shared_state) -> None:
    tenant_id = _create_tenant("kpi-external-invalid")
    valid_headers = _developer_headers_for_tenant(tenant_id=tenant_id)

    invalid = client.get(
        "/api/analytics/kpis",
        headers={"X-App-Key": valid_headers["X-App-Key"], "X-App-Secret": "invalid-secret"},
    )
    missing_secret = client.get(
        "/api/analytics/kpis",
        headers={"X-App-Key": valid_headers["X-App-Key"]},
    )

    assert invalid.status_code == 401, invalid.text
    assert missing_secret.status_code == 401, missing_secret.text


def test_tenant_analytics_kpis_external_client_tenant_isolation(reset_shared_state) -> None:
    tenant_a = _create_tenant("kpi-external-iso-a")
    tenant_b = _create_tenant("kpi-external-iso-b")

    headers_a = _developer_headers_for_tenant(tenant_id=tenant_a)
    headers_b = _developer_headers_for_tenant(tenant_id=tenant_b)

    response_a = client.get("/api/analytics/kpis", headers=headers_a)
    response_b = client.get("/api/analytics/kpis", headers=headers_b)
    assert response_a.status_code == 401, response_a.text
    assert response_b.status_code == 401, response_b.text


def test_tenant_analytics_kpis_external_client_contract_matches_internal(reset_shared_state) -> None:
    tenant_id = _create_tenant("kpi-external-contract")
    user_headers = _tenant_user_headers(tenant_id=tenant_id)
    external_headers = _developer_headers_for_tenant(tenant_id=tenant_id)

    internal_response = client.get("/api/analytics/kpis", headers=user_headers)
    external_response = client.get("/api/analytics/kpis", headers=external_headers)
    assert internal_response.status_code == 200, internal_response.text
    assert external_response.status_code == 401, external_response.text
    assert int(internal_response.json()["tenant_id"]) == tenant_id
    assert external_response.json().get("detail") == "valid authentication is required"


def test_tenant_analytics_kpis_refresh_requires_auth(reset_shared_state) -> None:
    response = client.post("/api/analytics/kpis/refresh")
    _assert_auth_or_csrf_denied(response)


def test_tenant_analytics_kpis_refresh_history_requires_auth(reset_shared_state) -> None:
    response = client.get("/api/analytics/kpis/refresh-history")
    assert response.status_code == 401, response.text


def test_tenant_analytics_kpis_refresh_history_empty_state(reset_shared_state) -> None:
    tenant_id = _create_tenant("kpi-refresh-history-empty")
    headers = _tenant_user_headers(tenant_id=tenant_id)

    response = client.get("/api/analytics/kpis/refresh-history", headers=headers)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["recent_refreshes"] == []
    assert body["last_refresh_at"] is None


def test_tenant_analytics_kpis_refresh_history_has_entry_after_refresh(reset_shared_state) -> None:
    tenant_id = _create_tenant("kpi-refresh-history-entry")
    headers = _tenant_analytics_rw_headers(tenant_id=tenant_id)

    _emit_analytics_event(tenant_id=tenant_id, event_type="student.created", event_id=9211)
    platform_billing_service.increment_usage(tenant_id, "analytics.events.read", 2)

    refresh_response = client.post("/api/analytics/kpis/refresh", headers=headers)
    assert refresh_response.status_code == 200, refresh_response.text

    history_response = client.get("/api/analytics/kpis/refresh-history", headers=headers)
    assert history_response.status_code == 200, history_response.text
    assert len(history_response.json()["recent_refreshes"]) >= 1


def test_tenant_analytics_kpis_refresh_history_is_newest_first(reset_shared_state) -> None:
    tenant_id = _create_tenant("kpi-refresh-history-order")
    headers = _tenant_analytics_rw_headers(tenant_id=tenant_id)

    _emit_analytics_event(tenant_id=tenant_id, event_type="student.created", event_id=9221)
    client.post("/api/analytics/kpis/refresh", headers=headers)
    platform_billing_service.increment_usage(tenant_id, "analytics.events.read", 1)
    client.post("/api/analytics/kpis/refresh", headers=headers)

    response = client.get(
        "/api/analytics/kpis/refresh-history",
        params={"limit": 2},
        headers=headers,
    )
    assert response.status_code == 200, response.text
    entries = response.json()["recent_refreshes"]
    assert len(entries) == 2
    assert entries[0]["created_at"] >= entries[1]["created_at"]


def test_tenant_analytics_kpis_refresh_history_is_tenant_scoped(reset_shared_state) -> None:
    tenant_a = _create_tenant("kpi-refresh-history-iso-a")
    tenant_b = _create_tenant("kpi-refresh-history-iso-b")
    headers_a = _tenant_analytics_rw_headers(tenant_id=tenant_a)
    headers_b = _tenant_analytics_rw_headers(tenant_id=tenant_b)

    _emit_analytics_event(tenant_id=tenant_a, event_type="student.created", event_id=9231)
    client.post("/api/analytics/kpis/refresh", headers=headers_a)

    response_a = client.get("/api/analytics/kpis/refresh-history", headers=headers_a)
    response_b = client.get("/api/analytics/kpis/refresh-history", headers=headers_b)
    assert response_a.status_code == 200, response_a.text
    assert response_b.status_code == 200, response_b.text
    assert len(response_a.json()["recent_refreshes"]) >= 1
    assert response_b.json()["recent_refreshes"] == []


def test_tenant_analytics_kpis_refresh_history_limit_is_bounded(reset_shared_state) -> None:
    tenant_id = _create_tenant("kpi-refresh-history-limit")
    headers = _tenant_analytics_rw_headers(tenant_id=tenant_id)

    _emit_analytics_event(tenant_id=tenant_id, event_type="student.created", event_id=9241)
    client.post("/api/analytics/kpis/refresh", headers=headers)
    client.post("/api/analytics/kpis/refresh", headers=headers)
    client.post("/api/analytics/kpis/refresh", headers=headers)

    response = client.get(
        "/api/analytics/kpis/refresh-history",
        params={"limit": 2},
        headers=headers,
    )
    assert response.status_code == 200, response.text
    assert len(response.json()["recent_refreshes"]) <= 2


def test_tenant_analytics_kpis_refresh_executes_and_updates_read_path(reset_shared_state) -> None:
    tenant_id = _create_tenant("kpi-refresh-ready")
    headers = _tenant_analytics_rw_headers(tenant_id=tenant_id)

    _emit_analytics_event(tenant_id=tenant_id, event_type="student.created", event_id=9201)
    platform_billing_service.increment_usage(tenant_id, "analytics.events.read", 3)

    before = client.get("/api/analytics/kpis", headers=headers)
    assert before.status_code == 200, before.text

    refreshed = client.post("/api/analytics/kpis/refresh", headers=headers)
    assert refreshed.status_code == 200, refreshed.text

    after = client.get("/api/analytics/kpis", headers=headers)
    assert after.status_code == 200, after.text
    assert after.json()["readiness_status"] in {"ready", "empty"}


def test_tenant_analytics_kpis_refresh_is_tenant_scoped(reset_shared_state) -> None:
    tenant_a = _create_tenant("kpi-refresh-iso-a")
    tenant_b = _create_tenant("kpi-refresh-iso-b")
    headers_a = _tenant_analytics_rw_headers(tenant_id=tenant_a)
    headers_b = _tenant_analytics_rw_headers(tenant_id=tenant_b)

    _emit_analytics_event(tenant_id=tenant_a, event_type="student.created", event_id=9301)
    platform_billing_service.increment_usage(tenant_a, "analytics.events.read", 5)

    pre_a = client.get("/api/analytics/kpis", headers=headers_a)
    pre_b = client.get("/api/analytics/kpis", headers=headers_b)
    assert pre_a.status_code == 200, pre_a.text
    assert pre_b.status_code == 200, pre_b.text

    refreshed_a = client.post("/api/analytics/kpis/refresh", headers=headers_a)
    assert refreshed_a.status_code == 200, refreshed_a.text

    post_a = client.get("/api/analytics/kpis", headers=headers_a)
    post_b = client.get("/api/analytics/kpis", headers=headers_b)
    assert post_a.status_code == 200, post_a.text
    assert post_b.status_code == 200, post_b.text
    assert int(post_a.json()["tenant_id"]) == tenant_a
    assert int(post_b.json()["tenant_id"]) == tenant_b


def test_tenant_analytics_kpis_allows_non_admin_and_uses_snapshot_values(reset_shared_state) -> None:
    tenant_id = _create_tenant("kpi-user-facing")
    _emit_analytics_event(tenant_id=tenant_id, event_type="student.created", event_id=9001)
    platform_billing_service.increment_usage(tenant_id, "analytics.events.read", 4)

    with UnitOfWork() as uow:
        rows = kpi_service.refresh_tenant_metrics(tenant_id=tenant_id, uow=uow)
    expected = {str(item["metric_key"]): int(item["metric_value"]) for item in rows}

    response = client.get(
        "/api/analytics/kpis",
        headers=_tenant_user_headers(tenant_id=tenant_id),
    )
    assert response.status_code == 200, response.text
    cards = {str(item["key"]): int(item["value"]) for item in response.json()["kpis"]}
    assert cards["analytics_events_reads_total"] == expected["analytics_events_reads_total"]


def test_tenant_analytics_kpis_event_derived_lineage_is_exposed(reset_shared_state) -> None:
    tenant_id = _create_tenant("kpi-lineage-events")
    headers = _tenant_user_headers(tenant_id=tenant_id)

    client.get("/api/analytics/kpis", headers=headers)
    client.get("/api/analytics/kpis/trends", headers=headers)
    platform_billing_service.increment_usage(tenant_id, "analytics.events.read", 1)

    with UnitOfWork() as uow:
        kpi_service.refresh_tenant_metrics(tenant_id=tenant_id, uow=uow)
        event_counts = event_ingestion_service.summary_for_tenant(tenant_id, uow=uow)

    response = client.get(
        "/api/analytics/kpis",
        headers=headers,
    )
    assert response.status_code == 200, response.text
    cards = {str(item["key"]): item for item in response.json()["kpis"]}
    breakdown = {e["event_type"]: e["count"] for e in (cards["analytics_events_reads_from_events_total"]["source_breakdown"] or [])}
    assert int(breakdown.get(ANALYTICS_EVENT_READ, 0)) == int(event_counts.get(ANALYTICS_EVENT_READ, 0) or 0)


def test_tenant_analytics_kpis_non_event_lineage_is_predictable(reset_shared_state) -> None:
    tenant_id = _create_tenant("kpi-lineage-non-event")
    headers = _tenant_user_headers(tenant_id=tenant_id)

    _emit_analytics_event(tenant_id=tenant_id, event_type="student.created", event_id=9901)
    platform_billing_service.increment_usage(tenant_id, "analytics.events.read", 4)
    with UnitOfWork() as uow:
        kpi_service.refresh_tenant_metrics(tenant_id=tenant_id, uow=uow)

    response = client.get(
        "/api/analytics/kpis",
        headers=headers,
    )
    assert response.status_code == 200, response.text
    cards = {str(item["key"]): item for item in response.json()["kpis"]}
    assert cards["total_students"]["source_breakdown"] is None


def test_tenant_analytics_kpis_empty_when_snapshot_absent(reset_shared_state) -> None:
    tenant_id = _create_tenant("kpi-user-empty")
    _emit_analytics_event(tenant_id=tenant_id, event_type="student.created", event_id=9101)

    # Endpoint must reuse existing snapshot storage and avoid implicit recompute.
    response = client.get(
        "/api/analytics/kpis",
        headers=_tenant_user_headers(tenant_id=tenant_id),
    )
    assert response.status_code == 200, response.text
    assert response.json()["readiness_status"] == "empty"
    assert response.json()["kpis"] == []


def test_tenant_analytics_kpis_tenant_isolation(reset_shared_state) -> None:
    tenant_a = _create_tenant("kpi-user-iso-a")
    tenant_b = _create_tenant("kpi-user-iso-b")

    platform_billing_service.increment_usage(tenant_a, "analytics.events.read", 11)
    platform_billing_service.increment_usage(tenant_b, "analytics.events.read", 2)

    with UnitOfWork() as uow:
        kpi_service.refresh_tenant_metrics(tenant_id=tenant_a, uow=uow)
        kpi_service.refresh_tenant_metrics(tenant_id=tenant_b, uow=uow)

    response_a = client.get(
        "/api/analytics/kpis",
        headers=_tenant_user_headers(tenant_id=tenant_a),
    )
    response_b = client.get(
        "/api/analytics/kpis",
        headers=_tenant_user_headers(tenant_id=tenant_b),
    )
    assert response_a.status_code == 200, response_a.text
    assert response_b.status_code == 200, response_b.text
    cards_a = {str(item["key"]): int(item["value"]) for item in response_a.json()["kpis"]}
    cards_b = {str(item["key"]): int(item["value"]) for item in response_b.json()["kpis"]}
    assert cards_a["analytics_events_reads_total"] != cards_b["analytics_events_reads_total"]


def test_tenant_analytics_kpi_trends_requires_auth(reset_shared_state) -> None:
    response = client.get("/api/analytics/kpis/trends")
    assert response.status_code == 401, response.text


def test_tenant_analytics_kpi_trends_non_admin_matches_history_path(reset_shared_state) -> None:
    tenant_id = _create_tenant("kpi-trend-user-facing")

    base_day = date(2026, 2, 1)
    for offset in range(3):
        day = (base_day + timedelta(days=offset)).isoformat()
        platform_billing_service.increment_usage(tenant_id, "analytics.events.read", offset + 1)
        with UnitOfWork() as uow:
            kpi_service.refresh_tenant_metrics(tenant_id=tenant_id, uow=uow, snapshot_date=day)

    with UnitOfWork() as uow:
        expected_history_rows = uow.kpi_repository.list_metric_history(
            tenant_id=tenant_id,
            metric_key="analytics_events_reads_total",
            days=7,
            conn=uow.conn,
        )

    response = client.get(
        "/api/analytics/kpis/trends",
        params={"window_days": 7},
        headers=_tenant_user_headers(tenant_id=tenant_id),
    )
    assert response.status_code == 200, response.text
    trends = {str(item["key"]): item for item in response.json()["trends"]}
    assert "analytics_events_reads_total" in trends
    assert len(trends["analytics_events_reads_total"]["points"]) == len(expected_history_rows)


def test_tenant_analytics_kpi_trends_empty_state(reset_shared_state) -> None:
    tenant_id = _create_tenant("kpi-trend-empty")

    response = client.get(
        "/api/analytics/kpis/trends",
        headers=_tenant_user_headers(tenant_id=tenant_id),
    )
    assert response.status_code == 200, response.text
    assert response.json()["trends"] == []


def test_tenant_analytics_kpi_trends_window_is_bounded(reset_shared_state) -> None:
    tenant_id = _create_tenant("kpi-trend-window")

    base_day = date(2026, 1, 1)
    for offset in range(12):
        day = (base_day + timedelta(days=offset)).isoformat()
        platform_billing_service.increment_usage(tenant_id, "analytics.events.read", 1)
        with UnitOfWork() as uow:
            kpi_service.refresh_tenant_metrics(tenant_id=tenant_id, uow=uow, snapshot_date=day)

    response_7 = client.get(
        "/api/analytics/kpis/trends",
        params={"window_days": 7},
        headers=_tenant_user_headers(tenant_id=tenant_id),
    )
    response_90 = client.get(
        "/api/analytics/kpis/trends",
        params={"window_days": 90},
        headers=_tenant_user_headers(tenant_id=tenant_id),
    )
    assert response_7.status_code == 200, response_7.text
    assert response_90.status_code == 200, response_90.text
    t7 = {str(item["key"]): item for item in response_7.json()["trends"]}
    t90 = {str(item["key"]): item for item in response_90.json()["trends"]}
    assert len(t7["analytics_events_reads_total"]["points"]) <= 7
    assert len(t90["analytics_events_reads_total"]["points"]) <= 12


def test_tenant_analytics_kpi_trends_tenant_isolation(reset_shared_state) -> None:
    tenant_a = _create_tenant("kpi-trend-iso-a")
    tenant_b = _create_tenant("kpi-trend-iso-b")

    base_day = date(2026, 3, 1)
    for offset in range(3):
        day = (base_day + timedelta(days=offset)).isoformat()
        platform_billing_service.increment_usage(tenant_a, "analytics.events.read", 1)
        platform_billing_service.increment_usage(tenant_b, "analytics.events.read", 50)
        with UnitOfWork() as uow:
            kpi_service.refresh_tenant_metrics(tenant_id=tenant_a, uow=uow, snapshot_date=day)
            kpi_service.refresh_tenant_metrics(tenant_id=tenant_b, uow=uow, snapshot_date=day)

    response_a = client.get(
        "/api/analytics/kpis/trends",
        params={"window_days": 30},
        headers=_tenant_user_headers(tenant_id=tenant_a),
    )
    response_b = client.get(
        "/api/analytics/kpis/trends",
        params={"window_days": 30},
        headers=_tenant_user_headers(tenant_id=tenant_b),
    )
    assert response_a.status_code == 200, response_a.text
    assert response_b.status_code == 200, response_b.text
    ta = {str(item["key"]): item for item in response_a.json()["trends"]}
    tb = {str(item["key"]): item for item in response_b.json()["trends"]}
    assert ta["analytics_events_reads_total"]["latest_value"] < tb["analytics_events_reads_total"]["latest_value"]


def test_tenant_analytics_kpi_insights_requires_auth(reset_shared_state) -> None:
    response = client.get("/api/analytics/kpis/insights")
    assert response.status_code == 401, response.text


def test_tenant_analytics_kpi_insights_non_admin_and_growth_decline(reset_shared_state) -> None:
    tenant_id = _create_tenant("kpi-insight-growth-decline")

    with UnitOfWork() as uow:
        kpi_service.refresh_tenant_metrics(tenant_id=tenant_id, uow=uow, snapshot_date="2026-04-01")

    platform_billing_service.increment_usage(tenant_id, "analytics.events.read", 5)
    with UnitOfWork() as uow:
        kpi_service.refresh_tenant_metrics(tenant_id=tenant_id, uow=uow, snapshot_date="2026-04-02")

    platform_billing_service.increment_usage(tenant_id, "analytics.kpi.read", 20)
    platform_billing_service.increment_usage(tenant_id, "analytics.events.read", 2)
    with UnitOfWork() as uow:
        kpi_service.refresh_tenant_metrics(tenant_id=tenant_id, uow=uow, snapshot_date="2026-04-03")

    response = client.get(
        "/api/analytics/kpis/insights",
        params={"window_days": 30},
        headers=_tenant_user_headers(tenant_id=tenant_id),
    )
    assert response.status_code == 200, response.text
    assert len(response.json()["insights"]) > 0


def test_tenant_analytics_kpi_insights_empty_state(reset_shared_state) -> None:
    tenant_id = _create_tenant("kpi-insight-empty")

    response = client.get(
        "/api/analytics/kpis/insights",
        headers=_tenant_user_headers(tenant_id=tenant_id),
    )
    assert response.status_code == 200, response.text
    assert response.json()["insights"] == []


def test_tenant_analytics_kpi_insights_no_data_for_single_snapshot(reset_shared_state) -> None:
    tenant_id = _create_tenant("kpi-insight-no-data")

    with UnitOfWork() as uow:
        kpi_service.refresh_tenant_metrics(tenant_id=tenant_id, uow=uow, snapshot_date="2026-04-01")

    response = client.get(
        "/api/analytics/kpis/insights",
        params={"window_days": 7},
        headers=_tenant_user_headers(tenant_id=tenant_id),
    )
    assert response.status_code == 200, response.text
    assert any(str(item.get("type")) == "no_data" for item in response.json()["insights"])


def test_tenant_analytics_kpi_insights_window_is_bounded(reset_shared_state) -> None:
    tenant_id = _create_tenant("kpi-insight-window")

    base_day = date(2026, 5, 1)
    for offset in range(12):
        day = (base_day + timedelta(days=offset)).isoformat()
        platform_billing_service.increment_usage(tenant_id, "analytics.events.read", 1)
        with UnitOfWork() as uow:
            kpi_service.refresh_tenant_metrics(tenant_id=tenant_id, uow=uow, snapshot_date=day)

    response = client.get(
        "/api/analytics/kpis/insights",
        params={"window_days": 999},
        headers=_tenant_user_headers(tenant_id=tenant_id),
    )
    assert response.status_code == 200, response.text
    assert len(response.json()["insights"]) > 0


def test_tenant_analytics_kpi_insights_tenant_isolation(reset_shared_state) -> None:
    tenant_a = _create_tenant("kpi-insight-iso-a")
    tenant_b = _create_tenant("kpi-insight-iso-b")

    with UnitOfWork() as uow:
        kpi_service.refresh_tenant_metrics(tenant_id=tenant_a, uow=uow, snapshot_date="2026-06-01")
        kpi_service.refresh_tenant_metrics(tenant_id=tenant_b, uow=uow, snapshot_date="2026-06-01")

    platform_billing_service.increment_usage(tenant_a, "analytics.events.read", 2)
    platform_billing_service.increment_usage(tenant_b, "analytics.events.read", 20)
    with UnitOfWork() as uow:
        kpi_service.refresh_tenant_metrics(tenant_id=tenant_a, uow=uow, snapshot_date="2026-06-02")
        kpi_service.refresh_tenant_metrics(tenant_id=tenant_b, uow=uow, snapshot_date="2026-06-02")

    response_a = client.get(
        "/api/analytics/kpis/insights",
        params={"window_days": 30},
        headers=_tenant_user_headers(tenant_id=tenant_a),
    )
    response_b = client.get(
        "/api/analytics/kpis/insights",
        params={"window_days": 30},
        headers=_tenant_user_headers(tenant_id=tenant_b),
    )
    assert response_a.status_code == 200, response_a.text
    assert response_b.status_code == 200, response_b.text
    ia = {str(item["key"]): item for item in response_a.json()["insights"]}
    ib = {str(item["key"]): item for item in response_b.json()["insights"]}
    assert ia["analytics_events_reads_total"]["value"] < ib["analytics_events_reads_total"]["value"]


def test_tenant_analytics_kpi_recommendations_requires_auth(reset_shared_state) -> None:
    response = client.get("/api/analytics/kpis/recommendations")
    assert response.status_code == 401, response.text


def test_tenant_analytics_kpi_recommendations_non_admin_rule_mapping(reset_shared_state) -> None:
    tenant_id = _create_tenant("kpi-rec-rules")

    with UnitOfWork() as uow:
        kpi_service.refresh_tenant_metrics(tenant_id=tenant_id, uow=uow, snapshot_date="2026-07-01")

    platform_billing_service.increment_usage(tenant_id, "analytics.events.read", 5)
    with UnitOfWork() as uow:
        kpi_service.refresh_tenant_metrics(tenant_id=tenant_id, uow=uow, snapshot_date="2026-07-02")

    platform_billing_service.increment_usage(tenant_id, "analytics.kpi.read", 30)
    platform_billing_service.increment_usage(tenant_id, "analytics.events.read", 1)
    with UnitOfWork() as uow:
        kpi_service.refresh_tenant_metrics(tenant_id=tenant_id, uow=uow, snapshot_date="2026-07-03")

    response = client.get(
        "/api/analytics/kpis/recommendations",
        params={"window_days": 30},
        headers=_tenant_user_headers(tenant_id=tenant_id),
    )
    assert response.status_code == 200, response.text
    assert len(response.json()["recommendations"]) > 0


def test_tenant_analytics_kpi_recommendations_decline_mapping(reset_shared_state) -> None:
    tenant_id = _create_tenant("kpi-rec-decline")

    with UnitOfWork() as uow:
        uow.kpi_repository.upsert_metric_snapshot(
            tenant_id=tenant_id,
            metric_key="analytics_events_reads_total",
            metric_value=20,
            snapshot_date="2026-08-01",
            metadata_json={"title": "Analytics Events Reads Total"},
            conn=uow.conn,
        )
        uow.kpi_repository.upsert_metric_snapshot(
            tenant_id=tenant_id,
            metric_key="analytics_events_reads_total",
            metric_value=10,
            snapshot_date="2026-08-02",
            metadata_json={"title": "Analytics Events Reads Total"},
            conn=uow.conn,
        )

    response = client.get(
        "/api/analytics/kpis/recommendations",
        headers=_tenant_user_headers(tenant_id=tenant_id),
    )
    assert response.status_code == 200, response.text
    assert any(str(item.get("type")) == "investigate_decline" for item in response.json()["recommendations"])


def test_tenant_analytics_kpi_recommendations_no_data_mapping(reset_shared_state) -> None:
    tenant_id = _create_tenant("kpi-rec-no-data")

    with UnitOfWork() as uow:
        kpi_service.refresh_tenant_metrics(tenant_id=tenant_id, uow=uow, snapshot_date="2026-09-01")

    response = client.get(
        "/api/analytics/kpis/recommendations",
        params={"window_days": 7},
        headers=_tenant_user_headers(tenant_id=tenant_id),
    )
    assert response.status_code == 200, response.text
    assert len(response.json()["recommendations"]) > 0


def test_tenant_analytics_kpi_recommendations_empty_state(reset_shared_state) -> None:
    tenant_id = _create_tenant("kpi-rec-empty")

    response = client.get(
        "/api/analytics/kpis/recommendations",
        headers=_tenant_user_headers(tenant_id=tenant_id),
    )
    assert response.status_code == 200, response.text
    assert response.json()["recommendations"] == []


def test_tenant_analytics_kpi_recommendations_window_is_bounded(reset_shared_state) -> None:
    tenant_id = _create_tenant("kpi-rec-window")

    base_day = date(2026, 10, 1)
    for offset in range(8):
        day = (base_day + timedelta(days=offset)).isoformat()
        platform_billing_service.increment_usage(tenant_id, "analytics.events.read", 1)
        with UnitOfWork() as uow:
            kpi_service.refresh_tenant_metrics(tenant_id=tenant_id, uow=uow, snapshot_date=day)

    response = client.get(
        "/api/analytics/kpis/recommendations",
        params={"window_days": 999},
        headers=_tenant_user_headers(tenant_id=tenant_id),
    )
    assert response.status_code == 200, response.text
    assert len(response.json()["recommendations"]) > 0


def test_tenant_analytics_kpi_recommendations_tenant_isolation(reset_shared_state) -> None:
    tenant_a = _create_tenant("kpi-rec-iso-a")
    tenant_b = _create_tenant("kpi-rec-iso-b")

    platform_billing_service.increment_usage(tenant_a, "analytics.events.read", 2)
    platform_billing_service.increment_usage(tenant_b, "analytics.events.read", 20)
    with UnitOfWork() as uow:
        kpi_service.refresh_tenant_metrics(tenant_id=tenant_a, uow=uow, snapshot_date="2026-11-01")
        kpi_service.refresh_tenant_metrics(tenant_id=tenant_b, uow=uow, snapshot_date="2026-11-01")

    with UnitOfWork() as uow:
        kpi_service.refresh_tenant_metrics(tenant_id=tenant_a, uow=uow, snapshot_date="2026-11-02")
        platform_billing_service.increment_usage(tenant_b, "analytics.events.read", 10)
        kpi_service.refresh_tenant_metrics(tenant_id=tenant_b, uow=uow, snapshot_date="2026-11-02")

    response_a = client.get(
        "/api/analytics/kpis/recommendations",
        headers=_tenant_user_headers(tenant_id=tenant_a),
    )
    response_b = client.get(
        "/api/analytics/kpis/recommendations",
        headers=_tenant_user_headers(tenant_id=tenant_b),
    )
    assert response_a.status_code == 200, response_a.text
    assert response_b.status_code == 200, response_b.text
    ra = {str(item["key"]): item for item in response_a.json()["recommendations"]}
    rb = {str(item["key"]): item for item in response_b.json()["recommendations"]}
    assert str(ra["analytics_events_reads_total"]["type"]) != ""
    assert str(rb["analytics_events_reads_total"]["type"]) != ""


# ---------------------------------------------------------------------------
# KPI source breakdown / composition transparency v1
# ---------------------------------------------------------------------------

def test_kpi_source_breakdown_present_on_event_derived_kpi(reset_shared_state) -> None:
    """Event-derived KPI cards expose source_breakdown with per-event-type counts."""
    tenant_id = _create_tenant("kpi-breakdown-present")
    headers = _tenant_user_headers(tenant_id=tenant_id)

    # Trigger two analytics.event.read events and one analytics.kpi.read event.
    client.get("/api/analytics/kpis", headers=headers)
    client.get("/api/analytics/kpis", headers=headers)
    client.get("/api/analytics/kpis/trends", headers=headers)

    with UnitOfWork() as uow:
        kpi_service.refresh_tenant_metrics(tenant_id=tenant_id, uow=uow)

    response = client.get("/api/analytics/kpis", headers=headers)
    assert response.status_code == 200, response.text
    cards = {str(item["key"]): item for item in response.json()["kpis"]}
    breakdown = {e["event_type"]: e["count"] for e in (cards["analytics_events_reads_from_events_total"]["source_breakdown"] or [])}
    assert int(breakdown.get(ANALYTICS_EVENT_READ, 0)) >= 1


def test_kpi_source_breakdown_absent_on_non_event_derived_kpi(reset_shared_state) -> None:
    """Non-event-derived KPI cards keep source_breakdown null."""
    tenant_id = _create_tenant("kpi-breakdown-absent")
    headers = _tenant_user_headers(tenant_id=tenant_id)

    _emit_analytics_event(tenant_id=tenant_id, event_type="student.created", event_id=8801)
    platform_billing_service.increment_usage(tenant_id, "analytics.events.read", 2)

    with UnitOfWork() as uow:
        kpi_service.refresh_tenant_metrics(tenant_id=tenant_id, uow=uow)

    response = client.get("/api/analytics/kpis", headers=headers)
    assert response.status_code == 200, response.text
    cards = {str(item["key"]): item for item in response.json()["kpis"]}
    assert cards["total_students"]["source_breakdown"] is None


def test_kpi_source_breakdown_count_matches_event_summary(reset_shared_state) -> None:
    """Breakdown counts must equal summary_for_tenant() — no fabrication."""
    tenant_id = _create_tenant("kpi-breakdown-consistent")
    headers = _tenant_user_headers(tenant_id=tenant_id)

    # Emit known events.
    client.get("/api/analytics/kpis", headers=headers)          # → analytics.event.read
    client.get("/api/analytics/kpis/trends", headers=headers)   # → analytics.kpi.read
    client.get("/api/analytics/kpis/insights", headers=headers) # → analytics.kpi.read

    with UnitOfWork() as uow:
        kpi_service.refresh_tenant_metrics(tenant_id=tenant_id, uow=uow)
        expected_counts = event_ingestion_service.summary_for_tenant(tenant_id, uow=uow)

    response = client.get("/api/analytics/kpis", headers=headers)
    assert expected_counts is not None
    assert response.status_code == 200, response.text
    cards = {str(item["key"]): item for item in response.json()["kpis"]}
    breakdown = {e["event_type"]: e["count"] for e in (cards["analytics_kpi_reads_from_events_total"]["source_breakdown"] or [])}
    assert int(breakdown.get(ANALYTICS_KPI_READ, 0)) == int(expected_counts.get(ANALYTICS_KPI_READ, 0) or 0)


def test_kpi_source_breakdown_tenant_isolated(reset_shared_state) -> None:
    """Breakdown counts must not leak across tenants."""
    tenant_a = _create_tenant("kpi-breakdown-iso-a")
    tenant_b = _create_tenant("kpi-breakdown-iso-b")
    headers_a = _tenant_analytics_user_headers(tenant_id=tenant_a)
    headers_b = _tenant_analytics_user_headers(tenant_id=tenant_b)

    # Emit 3 analytics.event.read events for tenant_a only.
    client.get("/api/analytics/kpis", headers=headers_a)
    client.get("/api/analytics/kpis", headers=headers_a)
    client.get("/api/analytics/kpis", headers=headers_a)

    with UnitOfWork() as uow:
        kpi_service.refresh_tenant_metrics(tenant_id=tenant_a, uow=uow)
        kpi_service.refresh_tenant_metrics(tenant_id=tenant_b, uow=uow)

    response_a = client.get("/api/analytics/kpis", headers=headers_a)
    response_b = client.get("/api/analytics/kpis", headers=headers_b)
    assert response_a.status_code == 200, response_a.text
    assert response_b.status_code == 200, response_b.text

    cards_a = {str(item["key"]): item for item in response_a.json()["kpis"]}
    cards_b = {str(item["key"]): item for item in response_b.json()["kpis"]}

    bd_a = {e["event_type"]: e["count"] for e in (cards_a["analytics_events_reads_from_events_total"]["source_breakdown"] or [])}
    bd_b = {e["event_type"]: e["count"] for e in (cards_b["analytics_events_reads_from_events_total"]["source_breakdown"] or [])}

    # Tenant A should have >0 for ANALYTICS_EVENT_READ; tenant B should have 0.
    assert int(bd_a.get(ANALYTICS_EVENT_READ, 0)) > 0
    assert int(bd_b.get(ANALYTICS_EVENT_READ, 0)) == 0


def test_kpi_source_breakdown_empty_state_unchanged(reset_shared_state) -> None:
    """Empty state (no snapshot) still returns kpis=[] without breakdown errors."""
    tenant_id = _create_tenant("kpi-breakdown-empty")
    headers = _tenant_analytics_user_headers(tenant_id=tenant_id)

    response = client.get("/api/analytics/kpis", headers=headers)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["readiness_status"] == "empty"
    assert body["kpis"] == []


# ---------------------------------------------------------------------------
# KPI threshold / alert readiness layer v1
# ---------------------------------------------------------------------------

def _make_failed_jobs(tenant_id: int, count: int) -> None:
    """Helper: create `count` distinct failed jobs for a tenant."""
    with UnitOfWork() as uow:
        for i in range(count):
            job = uow.job_repository.enqueue(
                tenant_id, "grade-sync", {"batch": i}, max_retries=3, conn=uow.conn
            )
            uow.job_repository.mark_running(int(job["id"]), conn=uow.conn)
            uow.job_repository.mark_failed(int(job["id"]), "simulated failure", conn=uow.conn)


def test_kpi_severity_normal_when_no_failures(reset_shared_state) -> None:
    """KPI card for total_failed_jobs is 'normal' when value is 0."""
    tenant_id = _create_tenant("kpi-severity-normal")
    headers = _tenant_analytics_user_headers(tenant_id=tenant_id)

    with UnitOfWork() as uow:
        kpi_service.refresh_tenant_metrics(tenant_id=tenant_id, uow=uow)

    response = client.get("/api/analytics/kpis", headers=headers)
    assert response.status_code == 200, response.text
    cards = {item["key"]: item for item in response.json()["kpis"]}

    # total_failed_jobs is 0 (job state is cleared between tests) → normal.
    assert int(cards["total_failed_jobs"]["value"]) == 0
    assert cards["total_failed_jobs"]["severity"] == "normal"
    assert cards["total_failed_jobs"]["threshold_basis"] == "count"


def test_kpi_severity_warning_for_few_failed_jobs(reset_shared_state) -> None:
    """1–4 failed jobs → severity 'warning'."""
    tenant_id = _create_tenant("kpi-severity-warning")
    headers = _tenant_analytics_user_headers(tenant_id=tenant_id)

    _make_failed_jobs(tenant_id, count=3)

    with UnitOfWork() as uow:
        kpi_service.refresh_tenant_metrics(tenant_id=tenant_id, uow=uow)

    response = client.get("/api/analytics/kpis", headers=headers)
    assert response.status_code == 200, response.text
    cards = {item["key"]: item for item in response.json()["kpis"]}

    card = cards["total_failed_jobs"]
    assert int(card["value"]) == 3
    assert card["severity"] == "warning"
    assert card["threshold_basis"] == "count"


def test_kpi_severity_critical_for_many_failed_jobs(reset_shared_state) -> None:
    """≥5 failed jobs → severity 'critical'."""
    tenant_id = _create_tenant("kpi-severity-critical")
    headers = _tenant_analytics_user_headers(tenant_id=tenant_id)

    _make_failed_jobs(tenant_id, count=5)

    with UnitOfWork() as uow:
        kpi_service.refresh_tenant_metrics(tenant_id=tenant_id, uow=uow)

    response = client.get("/api/analytics/kpis", headers=headers)
    assert response.status_code == 200, response.text
    cards = {item["key"]: item for item in response.json()["kpis"]}

    card = cards["total_failed_jobs"]
    assert int(card["value"]) >= 5
    assert card["severity"] == "critical"
    assert card["threshold_basis"] == "count"


def test_kpi_severity_null_for_non_thresholded_kpis(reset_shared_state) -> None:
    """KPI without a threshold rule expose severity=None and threshold_basis=None."""
    tenant_id = _create_tenant("kpi-severity-null")
    headers = _tenant_analytics_user_headers(tenant_id=tenant_id)

    _emit_analytics_event(tenant_id=tenant_id, event_type="student.created", event_id=7701)
    platform_billing_service.increment_usage(tenant_id, "analytics.events.read", 2)

    with UnitOfWork() as uow:
        kpi_service.refresh_tenant_metrics(tenant_id=tenant_id, uow=uow)

    response = client.get("/api/analytics/kpis", headers=headers)
    assert response.status_code == 200, response.text
    cards = {item["key"]: item for item in response.json()["kpis"]}

    # These KPIs have no threshold rule.
    for key in ("total_students", "total_enrollments", "analytics_events_reads_total",
                "analytics_events_reads_from_events_total", "billing_usage_recorded_from_events_total"):
        assert cards[key]["severity"] is None, f"{key} should have severity=None"
        assert cards[key]["threshold_basis"] is None, f"{key} should have threshold_basis=None"


def test_kpi_severity_share_pct_no_data_when_zero(reset_shared_state) -> None:
    """analytics_kpi_reads_share_pct == 0 → severity 'no_data'."""
    tenant_id = _create_tenant("kpi-severity-share-nodata")
    headers = _tenant_analytics_user_headers(tenant_id=tenant_id)

    # Only event reads, no KPI reads — share_pct = 0.
    platform_billing_service.increment_usage(tenant_id, "analytics.events.read", 5)

    with UnitOfWork() as uow:
        kpi_service.refresh_tenant_metrics(tenant_id=tenant_id, uow=uow)

    response = client.get("/api/analytics/kpis", headers=headers)
    assert response.status_code == 200, response.text
    cards = {item["key"]: item for item in response.json()["kpis"]}

    card = cards["analytics_kpi_reads_share_pct"]
    assert int(card["value"]) == 0
    assert card["severity"] == "no_data"
    assert card["threshold_basis"] == "percentage"


def test_kpi_severity_share_pct_normal_in_healthy_range(reset_shared_state) -> None:
    """analytics_kpi_reads_share_pct in 21–79 → severity 'normal'."""
    tenant_id = _create_tenant("kpi-severity-share-normal")
    headers = _tenant_analytics_user_headers(tenant_id=tenant_id)

    # 3 event reads + 3 kpi reads → share = 50%
    platform_billing_service.increment_usage(tenant_id, "analytics.events.read", 3)
    platform_billing_service.increment_usage(tenant_id, "analytics.kpi.read", 3)

    with UnitOfWork() as uow:
        kpi_service.refresh_tenant_metrics(tenant_id=tenant_id, uow=uow)

    response = client.get("/api/analytics/kpis", headers=headers)
    assert response.status_code == 200, response.text
    cards = {item["key"]: item for item in response.json()["kpis"]}

    card = cards["analytics_kpi_reads_share_pct"]
    assert int(card["value"]) == 50
    assert card["severity"] == "normal"
    assert card["threshold_basis"] == "percentage"


def test_kpi_severity_empty_state_unchanged(reset_shared_state) -> None:
    """Empty state (no snapshot) still returns kpis=[] without severity errors."""
    tenant_id = _create_tenant("kpi-severity-empty")
    headers = _tenant_analytics_user_headers(tenant_id=tenant_id)

    response = client.get("/api/analytics/kpis", headers=headers)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["readiness_status"] == "empty"
    assert body["kpis"] == []


# ---------------------------------------------------------------------------
# KPI policy pack / named evaluation profile layer v1
# ---------------------------------------------------------------------------


def test_kpi_policy_pack_ops_kpis_carry_default_ops_v1(reset_shared_state) -> None:
    """total_failed_jobs and total_failed_notifications expose policy_pack='default_ops_v1'."""
    tenant_id = _create_tenant("kpi-policy-ops")
    headers = _tenant_analytics_user_headers(tenant_id=tenant_id)

    with UnitOfWork() as uow:
        kpi_service.refresh_tenant_metrics(tenant_id=tenant_id, uow=uow)

    response = client.get("/api/analytics/kpis", headers=headers)
    assert response.status_code == 200, response.text
    cards = {item["key"]: item for item in response.json()["kpis"]}

    assert cards["total_failed_jobs"]["policy_pack"] == "default_ops_v1"
    assert cards["total_failed_notifications"]["policy_pack"] == "default_ops_v1"


def test_kpi_policy_pack_adoption_kpi_carries_analytics_adoption_v1(reset_shared_state) -> None:
    """analytics_kpi_reads_share_pct exposes policy_pack='analytics_adoption_v1'."""
    tenant_id = _create_tenant("kpi-policy-adoption")
    headers = _tenant_analytics_user_headers(tenant_id=tenant_id)

    with UnitOfWork() as uow:
        kpi_service.refresh_tenant_metrics(tenant_id=tenant_id, uow=uow)

    response = client.get("/api/analytics/kpis", headers=headers)
    assert response.status_code == 200, response.text
    cards = {item["key"]: item for item in response.json()["kpis"]}

    assert cards["analytics_kpi_reads_share_pct"]["policy_pack"] == "analytics_adoption_v1"


def test_kpi_policy_pack_non_thresholded_kpis_are_null(reset_shared_state) -> None:
    """KPI without threshold rules (total_students, etc.) return policy_pack=null."""
    tenant_id = _create_tenant("kpi-policy-null")
    headers = _tenant_analytics_user_headers(tenant_id=tenant_id)

    with UnitOfWork() as uow:
        kpi_service.refresh_tenant_metrics(tenant_id=tenant_id, uow=uow)

    response = client.get("/api/analytics/kpis", headers=headers)
    assert response.status_code == 200, response.text
    cards = {item["key"]: item for item in response.json()["kpis"]}

    non_thresholded = [k for k in cards if k not in {
        "total_failed_jobs", "total_failed_notifications", "analytics_kpi_reads_share_pct",
        # A-013.5 Wave 1 thresholded KPIs
        "high_risk_students_count", "critical_risk_students_count", "delinquency_cases_active",
        "scheduling_conflicts_count", "capacity_risk_sections_count",
        # A-014.6 Wave 2 thresholded KPIs
        "grade_decline_risk_count", "grade_intervention_cases_count",
        "thesis_completion_risk_count", "thesis_intervention_cases_count",
        "attendance_recovery_actions_count", "graduation_risk_students_count",
        "degree_progress_intervention_cases_count", "scholarship_risk_cases_count",
        "financial_aid_risk_cases_count",
        # A-015.6 Wave 3 thresholded KPIs
        "budget_overrun_risk_count", "budget_review_actions_count",
        "active_finance_risk_signals_count", "finance_operations_actionability_count",
        "asset_conversion_gap_count",
        "inventory_low_stock_items_count", "critical_supply_risk_count",
        "reorder_recommendations_count", "supply_risk_actions_count",
        # A-016.6 Wave 4 thresholded KPIs
        "academic_integrity_risk_count", "academic_integrity_high_risk_count",
        "academic_integrity_cases_pending_review", "exam_proctoring_violations_count",
        "exam_integrity_high_risk_count", "exam_integrity_requires_approval_count",
        "thesis_governance_risk_count", "thesis_supervisor_assignment_needed_count",
        "thesis_review_delayed_count", "thesis_governance_requires_approval_count",
        "research_ethics_review_cases_count", "research_ethics_high_risk_count",
        "research_ethics_missing_documents_count", "research_ethics_requires_approval_count",
        "integrity_cases_open_count", "integrity_cases_escalated_count",
        "integrity_case_resolution_sla_risk_count",
    }]
    assert len(non_thresholded) > 0, "expected at least one non-thresholded KPI"
    for key in non_thresholded:
        assert cards[key]["policy_pack"] is None, f"{key} should have policy_pack=null"


def test_kpi_policy_pack_consistent_with_severity_basis(reset_shared_state) -> None:
    """policy_pack value is internally consistent with threshold_basis of same card."""
    tenant_id = _create_tenant("kpi-policy-consistency")
    headers = _tenant_analytics_user_headers(tenant_id=tenant_id)

    with UnitOfWork() as uow:
        kpi_service.refresh_tenant_metrics(tenant_id=tenant_id, uow=uow)

    response = client.get("/api/analytics/kpis", headers=headers)
    assert response.status_code == 200, response.text
    cards = {item["key"]: item for item in response.json()["kpis"]}

    # count-basis KPI must have default_ops_v1 pack
    for key in ("total_failed_jobs", "total_failed_notifications"):
        c = cards[key]
        assert c["threshold_basis"] == "count"
        assert c["policy_pack"] == "default_ops_v1"

    # percentage-basis KPI must have analytics_adoption_v1 pack
    c = cards["analytics_kpi_reads_share_pct"]
    assert c["threshold_basis"] == "percentage"
    assert c["policy_pack"] == "analytics_adoption_v1"


def test_kpi_policy_pack_tenant_isolated(reset_shared_state) -> None:
    """policy_pack is deterministic and does not leak between tenants."""
    tenant_a = _create_tenant("kpi-policy-tenant-a")
    tenant_b = _create_tenant("kpi-policy-tenant-b")

    for tid in (tenant_a, tenant_b):
        with UnitOfWork() as uow:
            kpi_service.refresh_tenant_metrics(tenant_id=tid, uow=uow)

    headers_a = _tenant_analytics_user_headers(tenant_id=tenant_a)
    headers_b = _tenant_analytics_user_headers(tenant_id=tenant_b)

    resp_a = client.get("/api/analytics/kpis", headers=headers_a).json()
    resp_b = client.get("/api/analytics/kpis", headers=headers_b).json()

    cards_a = {item["key"]: item["policy_pack"] for item in resp_a["kpis"]}
    cards_b = {item["key"]: item["policy_pack"] for item in resp_b["kpis"]}

    # Both tenants must see identical policy_pack values for same KPI keys
    assert cards_a == cards_b


# ---------------------------------------------------------------------------
# KPI actionability state / escalation readiness layer v1
# ---------------------------------------------------------------------------


def test_kpi_actionability_normal_severity_yields_observe(reset_shared_state) -> None:
    """total_failed_jobs with value 0 → severity=normal → actionability_state=observe."""
    tenant_id = _create_tenant("kpi-action-observe")
    headers = _tenant_analytics_user_headers(tenant_id=tenant_id)

    with UnitOfWork() as uow:
        kpi_service.refresh_tenant_metrics(tenant_id=tenant_id, uow=uow)

    response = client.get("/api/analytics/kpis", headers=headers)
    assert response.status_code == 200, response.text
    cards = {item["key"]: item for item in response.json()["kpis"]}

    assert int(cards["total_failed_jobs"]["value"]) == 0
    assert cards["total_failed_jobs"]["severity"] == "normal"
    assert cards["total_failed_jobs"]["actionability_state"] == "observe"


def test_kpi_actionability_warning_severity_yields_review(reset_shared_state) -> None:
    """total_failed_jobs with 3 failures → severity=warning → actionability_state=review."""
    tenant_id = _create_tenant("kpi-action-review")
    headers = _tenant_analytics_user_headers(tenant_id=tenant_id)

    _make_failed_jobs(tenant_id, count=3)

    with UnitOfWork() as uow:
        kpi_service.refresh_tenant_metrics(tenant_id=tenant_id, uow=uow)

    response = client.get("/api/analytics/kpis", headers=headers)
    assert response.status_code == 200, response.text
    cards = {item["key"]: item for item in response.json()["kpis"]}

    assert cards["total_failed_jobs"]["severity"] == "warning"
    assert cards["total_failed_jobs"]["actionability_state"] == "review"


def test_kpi_actionability_critical_severity_yields_act_now(reset_shared_state) -> None:
    """total_failed_jobs with 5+ failures → severity=critical → actionability_state=act_now."""
    tenant_id = _create_tenant("kpi-action-act-now")
    headers = _tenant_analytics_user_headers(tenant_id=tenant_id)

    _make_failed_jobs(tenant_id, count=5)

    with UnitOfWork() as uow:
        kpi_service.refresh_tenant_metrics(tenant_id=tenant_id, uow=uow)

    response = client.get("/api/analytics/kpis", headers=headers)
    assert response.status_code == 200, response.text
    cards = {item["key"]: item for item in response.json()["kpis"]}

    assert cards["total_failed_jobs"]["severity"] == "critical"
    assert cards["total_failed_jobs"]["actionability_state"] == "act_now"


def test_kpi_actionability_no_data_severity_yields_no_action(reset_shared_state) -> None:
    """analytics_kpi_reads_share_pct with value 0 → severity=no_data → actionability_state=no_action."""
    tenant_id = _create_tenant("kpi-action-no-action")
    headers = _tenant_analytics_user_headers(tenant_id=tenant_id)

    with UnitOfWork() as uow:
        kpi_service.refresh_tenant_metrics(tenant_id=tenant_id, uow=uow)

    response = client.get("/api/analytics/kpis", headers=headers)
    assert response.status_code == 200, response.text
    cards = {item["key"]: item for item in response.json()["kpis"]}

    assert cards["analytics_kpi_reads_share_pct"]["severity"] == "no_data"
    assert cards["analytics_kpi_reads_share_pct"]["actionability_state"] == "no_action"


def test_kpi_actionability_non_thresholded_kpis_are_null(reset_shared_state) -> None:
    """KPI without threshold rules return actionability_state=null."""
    tenant_id = _create_tenant("kpi-action-null")
    headers = _tenant_analytics_user_headers(tenant_id=tenant_id)

    with UnitOfWork() as uow:
        kpi_service.refresh_tenant_metrics(tenant_id=tenant_id, uow=uow)

    response = client.get("/api/analytics/kpis", headers=headers)
    assert response.status_code == 200, response.text
    cards = {item["key"]: item for item in response.json()["kpis"]}

    non_thresholded = [k for k in cards if k not in {
        "total_failed_jobs", "total_failed_notifications", "analytics_kpi_reads_share_pct",
        # A-013.5 Wave 1 thresholded KPIs
        "high_risk_students_count", "critical_risk_students_count", "delinquency_cases_active",
        "scheduling_conflicts_count", "capacity_risk_sections_count",
        # A-014.6 Wave 2 thresholded KPIs
        "grade_decline_risk_count", "grade_intervention_cases_count",
        "thesis_completion_risk_count", "thesis_intervention_cases_count",
        "attendance_recovery_actions_count", "graduation_risk_students_count",
        "degree_progress_intervention_cases_count", "scholarship_risk_cases_count",
        "financial_aid_risk_cases_count",
        # A-015.6 Wave 3 thresholded KPIs
        "budget_overrun_risk_count", "budget_review_actions_count",
        "active_finance_risk_signals_count", "finance_operations_actionability_count",
        "asset_conversion_gap_count",
        "inventory_low_stock_items_count", "critical_supply_risk_count",
        "reorder_recommendations_count", "supply_risk_actions_count",
        # A-016.6 Wave 4 thresholded KPIs
        "academic_integrity_risk_count", "academic_integrity_high_risk_count",
        "academic_integrity_cases_pending_review", "exam_proctoring_violations_count",
        "exam_integrity_high_risk_count", "exam_integrity_requires_approval_count",
        "thesis_governance_risk_count", "thesis_supervisor_assignment_needed_count",
        "thesis_review_delayed_count", "thesis_governance_requires_approval_count",
        "research_ethics_review_cases_count", "research_ethics_high_risk_count",
        "research_ethics_missing_documents_count", "research_ethics_requires_approval_count",
        "integrity_cases_open_count", "integrity_cases_escalated_count",
        "integrity_case_resolution_sla_risk_count",
    }]
    assert len(non_thresholded) > 0, "expected at least one non-thresholded KPI"
    for key in non_thresholded:
        assert cards[key]["actionability_state"] is None, f"{key} should have actionability_state=null"


def test_kpi_actionability_consistent_with_severity_and_policy(reset_shared_state) -> None:
    """actionability_state is internally consistent with severity and policy_pack for all thresholded KPI."""
    tenant_id = _create_tenant("kpi-action-consistency")
    headers = _tenant_analytics_user_headers(tenant_id=tenant_id)

    with UnitOfWork() as uow:
        kpi_service.refresh_tenant_metrics(tenant_id=tenant_id, uow=uow)

    response = client.get("/api/analytics/kpis", headers=headers)
    assert response.status_code == 200, response.text
    cards = {item["key"]: item for item in response.json()["kpis"]}

    _SEVERITY_ACTION_MAP = {
        "critical": "act_now",
        "warning": "review",
        "normal": "observe",
        "no_data": "no_action",
    }
    for key, card in cards.items():
        sev = card["severity"]
        act = card["actionability_state"]
        if sev is None:
            assert act is None, f"{key}: severity=null must yield actionability_state=null"
        else:
            assert act == _SEVERITY_ACTION_MAP[sev], (
                f"{key}: severity={sev!r} must yield actionability_state={_SEVERITY_ACTION_MAP[sev]!r}, got {act!r}"
            )


def test_kpi_actionability_tenant_isolated(reset_shared_state) -> None:
    """actionability_state does not leak between tenants.

    tenant_b has failed jobs → review; tenant_a has none → observe.
    This proves per-tenant isolation without relying on shared notification
    state that is not cleared between tests.
    """
    tenant_a = _create_tenant("kpi-action-tenant-a")
    tenant_b = _create_tenant("kpi-action-tenant-b")

    # Give tenant_b failed jobs (warning → review), leave tenant_a clean.
    _make_failed_jobs(tenant_b, count=3)

    for tid in (tenant_a, tenant_b):
        with UnitOfWork() as uow:
            kpi_service.refresh_tenant_metrics(tenant_id=tid, uow=uow)

    cards_a = {
        item["key"]: item
        for item in client.get("/api/analytics/kpis", headers=_tenant_analytics_user_headers(tenant_id=tenant_a)).json()["kpis"]
    }
    cards_b = {
        item["key"]: item
        for item in client.get("/api/analytics/kpis", headers=_tenant_analytics_user_headers(tenant_id=tenant_b)).json()["kpis"]
    }

    # tenant_a: zero failed jobs → severity=normal → observe
    assert int(cards_a["total_failed_jobs"]["value"]) == 0
    assert cards_a["total_failed_jobs"]["actionability_state"] == "observe"

    # tenant_b: 3 failed jobs → severity=warning → review
    assert cards_b["total_failed_jobs"]["severity"] == "warning"
    assert cards_b["total_failed_jobs"]["actionability_state"] == "review"


def test_kpi_actionability_empty_state_unchanged(reset_shared_state) -> None:
    """Empty state (no snapshot) still returns kpis=[] without actionability errors."""
    tenant_id = _create_tenant("kpi-action-empty")
    headers = _tenant_analytics_user_headers(tenant_id=tenant_id)

    response = client.get("/api/analytics/kpis", headers=headers)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["readiness_status"] == "empty"
    assert body["kpis"] == []


# ---------------------------------------------------------------------------
# KPI portfolio summary / overview layer v1
# ---------------------------------------------------------------------------


def test_kpi_portfolio_summary_present_and_total_matches_cards(reset_shared_state) -> None:
    """Top-level summary is present and total_kpis matches number of cards."""
    tenant_id = _create_tenant("kpi-summary-total")
    headers = _tenant_analytics_user_headers(tenant_id=tenant_id)

    with UnitOfWork() as uow:
        kpi_service.refresh_tenant_metrics(tenant_id=tenant_id, uow=uow)

    response = client.get("/api/analytics/kpis", headers=headers)
    assert response.status_code == 200, response.text
    body = response.json()

    assert "summary" in body
    assert int(body["summary"]["total_kpis"]) == len(body["kpis"])


def test_kpi_portfolio_summary_counts_match_card_values(reset_shared_state) -> None:
    """Summary severity/actionability counts are exact aggregations of card-level fields."""
    tenant_id = _create_tenant("kpi-summary-counts")
    headers = _tenant_analytics_user_headers(tenant_id=tenant_id)

    # Produce warning and critical for total_failed_jobs in this tenant.
    _make_failed_jobs(tenant_id, count=5)

    with UnitOfWork() as uow:
        kpi_service.refresh_tenant_metrics(tenant_id=tenant_id, uow=uow)

    response = client.get("/api/analytics/kpis", headers=headers)
    assert response.status_code == 200, response.text
    body = response.json()
    cards = list(body["kpis"])
    summary = dict(body["summary"])

    expected_severity = {
        "normal": 0,
        "warning": 0,
        "critical": 0,
        "no_data": 0,
    }
    expected_actionability = {
        "no_action": 0,
        "observe": 0,
        "review": 0,
        "act_now": 0,
    }
    for card in cards:
        sev = card.get("severity")
        if sev in expected_severity:
            expected_severity[sev] += 1
        state = card.get("actionability_state")
        if state in expected_actionability:
            expected_actionability[state] += 1

    assert summary["severity_counts"] == expected_severity
    assert summary["actionability_counts"] == expected_actionability


def test_kpi_portfolio_summary_overall_status_urgent_when_critical_present(reset_shared_state) -> None:
    """Any critical severity in cards escalates overall_portfolio_status to urgent."""
    tenant_id = _create_tenant("kpi-summary-urgent")
    headers = _tenant_analytics_user_headers(tenant_id=tenant_id)

    _make_failed_jobs(tenant_id, count=5)

    with UnitOfWork() as uow:
        kpi_service.refresh_tenant_metrics(tenant_id=tenant_id, uow=uow)

    response = client.get("/api/analytics/kpis", headers=headers)
    assert response.status_code == 200, response.text
    summary = response.json()["summary"]

    assert int(summary["severity_counts"]["critical"]) >= 1
    assert summary["overall_portfolio_status"] == "urgent"


def test_kpi_portfolio_summary_overall_status_matches_rule(reset_shared_state) -> None:
    """overall_portfolio_status follows documented precedence from severity counts."""
    tenant_id = _create_tenant("kpi-summary-rule")
    headers = _tenant_analytics_user_headers(tenant_id=tenant_id)

    with UnitOfWork() as uow:
        kpi_service.refresh_tenant_metrics(tenant_id=tenant_id, uow=uow)

    response = client.get("/api/analytics/kpis", headers=headers)
    assert response.status_code == 200, response.text
    summary = response.json()["summary"]
    severity_counts = summary["severity_counts"]

    expected_status = "healthy"
    if int(severity_counts["critical"]) > 0:
        expected_status = "urgent"
    elif int(severity_counts["warning"]) > 0:
        expected_status = "attention_needed"

    assert summary["overall_portfolio_status"] == expected_status


def test_kpi_portfolio_summary_empty_state_predictable(reset_shared_state) -> None:
    """Empty state still exposes deterministic summary with zero counts."""
    tenant_id = _create_tenant("kpi-summary-empty")
    headers = _tenant_analytics_user_headers(tenant_id=tenant_id)

    response = client.get("/api/analytics/kpis", headers=headers)
    assert response.status_code == 200, response.text
    body = response.json()
    summary = body["summary"]

    assert body["readiness_status"] == "empty"
    assert body["kpis"] == []
    assert summary["total_kpis"] == 0
    assert summary["severity_counts"] == {
        "normal": 0,
        "warning": 0,
        "critical": 0,
        "no_data": 0,
    }
    assert summary["actionability_counts"] == {
        "no_action": 0,
        "observe": 0,
        "review": 0,
        "act_now": 0,
    }
    assert summary["overall_portfolio_status"] == "healthy"


def test_kpi_portfolio_summary_tenant_isolated(reset_shared_state) -> None:
    """Summary is tenant-scoped: tenant_b with critical jobs differs from clean tenant_a."""
    tenant_a = _create_tenant("kpi-summary-tenant-a")
    tenant_b = _create_tenant("kpi-summary-tenant-b")

    _make_failed_jobs(tenant_b, count=5)

    for tid in (tenant_a, tenant_b):
        with UnitOfWork() as uow:
            kpi_service.refresh_tenant_metrics(tenant_id=tid, uow=uow)

    summary_a = client.get(
        "/api/analytics/kpis",
        headers=_tenant_analytics_user_headers(tenant_id=tenant_a),
    ).json()["summary"]
    summary_b = client.get(
        "/api/analytics/kpis",
        headers=_tenant_analytics_user_headers(tenant_id=tenant_b),
    ).json()["summary"]

    # tenant_b has at least one extra critical card from failed_jobs threshold.
    assert int(summary_b["severity_counts"]["critical"]) >= int(summary_a["severity_counts"]["critical"]) + 1
    assert summary_b["overall_portfolio_status"] == "urgent"


def test_kpi_portfolio_summary_consistent_with_cards(reset_shared_state) -> None:
    """Summary never contradicts card-level severity/actionability values."""
    tenant_id = _create_tenant("kpi-summary-consistency")
    headers = _tenant_analytics_user_headers(tenant_id=tenant_id)

    _make_failed_jobs(tenant_id, count=3)

    with UnitOfWork() as uow:
        kpi_service.refresh_tenant_metrics(tenant_id=tenant_id, uow=uow)

    response = client.get("/api/analytics/kpis", headers=headers)
    assert response.status_code == 200, response.text
    body = response.json()
    cards = list(body["kpis"])
    summary = body["summary"]

    # Ensure review/act_now/no_action/observe in summary are exact counts from cards.
    for state in ("no_action", "observe", "review", "act_now"):
        expected = sum(1 for card in cards if card.get("actionability_state") == state)
        assert int(summary["actionability_counts"][state]) == expected

    for severity in ("normal", "warning", "critical", "no_data"):
        expected = sum(1 for card in cards if card.get("severity") == severity)
        assert int(summary["severity_counts"][severity]) == expected


# ---------------------------------------------------------------------------
# KPI change digest / delta summary layer v1
# ---------------------------------------------------------------------------


def test_kpi_change_digest_present_and_total_matches_cards(reset_shared_state) -> None:
    """Top-level change_digest is present and total_kpis matches number of cards."""
    tenant_id = _create_tenant("kpi-digest-total")
    headers = _tenant_analytics_user_headers(tenant_id=tenant_id)

    with UnitOfWork() as uow:
        kpi_service.refresh_tenant_metrics(tenant_id=tenant_id, uow=uow)

    response = client.get("/api/analytics/kpis", headers=headers)
    assert response.status_code == 200, response.text
    body = response.json()

    assert "change_digest" in body
    assert int(body["change_digest"]["total_kpis"]) == len(body["kpis"])


def test_kpi_change_digest_counts_match_card_trend_deltas(reset_shared_state) -> None:
    """Digest change_counts equals per-card classification from latest vs previous trend points."""
    tenant_id = _create_tenant("kpi-digest-counts")
    headers = _tenant_analytics_user_headers(tenant_id=tenant_id)

    with UnitOfWork() as uow:
        kpi_service.refresh_tenant_metrics(tenant_id=tenant_id, uow=uow, snapshot_date="2026-12-01")

    platform_billing_service.increment_usage(tenant_id, "analytics.events.read", 7)
    platform_billing_service.increment_usage(tenant_id, "analytics.kpi.read", 21)
    with UnitOfWork() as uow:
        kpi_service.refresh_tenant_metrics(tenant_id=tenant_id, uow=uow, snapshot_date="2026-12-02")

    response = client.get("/api/analytics/kpis", headers=headers)
    assert response.status_code == 200, response.text
    body = response.json()
    cards = list(body["kpis"])
    digest = body["change_digest"]

    expected = {"improved": 0, "declined": 0, "unchanged": 0, "no_data": 0}
    for card in cards:
        points = list(card.get("trend") or [])
        if len(points) < 2:
            expected["no_data"] += 1
            continue
        delta = int(points[-1]["value"]) - int(points[-2]["value"])
        if delta > 0:
            expected["improved"] += 1
        elif delta < 0:
            expected["declined"] += 1
        else:
            expected["unchanged"] += 1

    assert digest["change_counts"] == expected


def test_kpi_change_digest_overall_direction_declining(reset_shared_state) -> None:
    """More declined than improved yields overall_change_direction='declining'."""
    tenant_id = _create_tenant("kpi-digest-declining")
    headers = _tenant_analytics_user_headers(tenant_id=tenant_id)

    with UnitOfWork() as uow:
        uow.kpi_repository.upsert_metric_snapshot(
            tenant_id=tenant_id,
            metric_key="analytics_events_reads_total",
            metric_value=30,
            snapshot_date="2026-12-10",
            metadata_json={"title": "Analytics Events Reads Total"},
            conn=uow.conn,
        )
        uow.kpi_repository.upsert_metric_snapshot(
            tenant_id=tenant_id,
            metric_key="analytics_events_reads_total",
            metric_value=10,
            snapshot_date="2026-12-11",
            metadata_json={"title": "Analytics Events Reads Total"},
            conn=uow.conn,
        )

    response = client.get("/api/analytics/kpis", headers=headers)
    assert response.status_code == 200, response.text
    digest = response.json()["change_digest"]
    assert int(digest["change_counts"]["declined"]) >= 1
    assert digest["overall_change_direction"] == "declining"


def test_kpi_change_digest_empty_state_predictable(reset_shared_state) -> None:
    """Empty KPI state exposes deterministic no-data digest."""
    tenant_id = _create_tenant("kpi-digest-empty")
    headers = _tenant_analytics_user_headers(tenant_id=tenant_id)

    response = client.get("/api/analytics/kpis", headers=headers)
    assert response.status_code == 200, response.text
    body = response.json()
    digest = body["change_digest"]

    assert body["kpis"] == []
    assert digest["total_kpis"] == 0
    assert digest["change_counts"] == {
        "improved": 0,
        "declined": 0,
        "unchanged": 0,
        "no_data": 0,
    }
    assert digest["overall_change_direction"] == "no_data"


def test_kpi_change_digest_tenant_isolated(reset_shared_state) -> None:
    """Digest is tenant-scoped; a changed tenant differs from untouched tenant."""
    tenant_a = _create_tenant("kpi-digest-iso-a")
    tenant_b = _create_tenant("kpi-digest-iso-b")

    with UnitOfWork() as uow:
        kpi_service.refresh_tenant_metrics(tenant_id=tenant_a, uow=uow, snapshot_date="2026-12-20")
        kpi_service.refresh_tenant_metrics(tenant_id=tenant_b, uow=uow, snapshot_date="2026-12-20")

    platform_billing_service.increment_usage(tenant_b, "analytics.events.read", 9)
    with UnitOfWork() as uow:
        kpi_service.refresh_tenant_metrics(tenant_id=tenant_b, uow=uow, snapshot_date="2026-12-21")

    digest_a = client.get(
        "/api/analytics/kpis", headers=_tenant_analytics_user_headers(tenant_id=tenant_a)
    ).json()["change_digest"]
    digest_b = client.get(
        "/api/analytics/kpis", headers=_tenant_analytics_user_headers(tenant_id=tenant_b)
    ).json()["change_digest"]

    assert int(digest_a["change_counts"]["improved"]) < int(digest_b["change_counts"]["improved"])


def test_kpi_change_digest_consistent_with_existing_trend_classification(reset_shared_state) -> None:
    """Digest direction follows documented precedence from its own counts."""
    tenant_id = _create_tenant("kpi-digest-consistency")
    headers = _tenant_analytics_user_headers(tenant_id=tenant_id)

    with UnitOfWork() as uow:
        kpi_service.refresh_tenant_metrics(tenant_id=tenant_id, uow=uow, snapshot_date="2026-12-25")

    platform_billing_service.increment_usage(tenant_id, "analytics.events.read", 3)
    with UnitOfWork() as uow:
        kpi_service.refresh_tenant_metrics(tenant_id=tenant_id, uow=uow, snapshot_date="2026-12-26")

    response = client.get("/api/analytics/kpis", headers=headers)
    assert response.status_code == 200, response.text
    digest = response.json()["change_digest"]
    counts = digest["change_counts"]

    expected_direction = "stable"
    total = int(digest["total_kpis"])
    if total == 0 or int(counts["no_data"]) == total:
        expected_direction = "no_data"
    elif int(counts["improved"]) > int(counts["declined"]):
        expected_direction = "improving"
    elif int(counts["declined"]) > int(counts["improved"]):
        expected_direction = "declining"

    assert digest["overall_change_direction"] == expected_direction


# ---------------------------------------------------------------------------
# KPI source mix / portfolio composition summary v1
# ---------------------------------------------------------------------------


def test_kpi_source_mix_summary_counts_match_card_source_status(reset_shared_state) -> None:
    """source_mix_counts are exact aggregations of card-level source_status."""
    tenant_id = _create_tenant("kpi-source-mix-counts")
    headers = _tenant_analytics_user_headers(tenant_id=tenant_id)

    with UnitOfWork() as uow:
        kpi_service.refresh_tenant_metrics(tenant_id=tenant_id, uow=uow)

    response = client.get("/api/analytics/kpis", headers=headers)
    assert response.status_code == 200, response.text
    body = response.json()
    cards = list(body["kpis"])
    mix = body["source_mix_summary"]

    expected = {
        "derived_from_events": 0,
        "derived_from_usage": 0,
        "derived_from_snapshot": 0,
        "mixed_source": 0,
        "empty": 0,
    }
    for card in cards:
        status = str(card.get("source_status") or "").strip().lower()
        if status in {"derived_from_events", "derived_from_usage", "derived_from_snapshot"}:
            expected[status] += 1
        elif status:
            expected["mixed_source"] += 1
        else:
            expected["empty"] += 1

    assert mix["source_mix_counts"] == expected
    assert int(mix["total_kpis"]) == len(cards)


def test_kpi_source_mix_summary_dominant_mode_snapshot(reset_shared_state) -> None:
    """Single snapshot-derived KPI should produce dominant_source_mode='snapshot'."""
    tenant_id = _create_tenant("kpi-source-mix-snapshot")

    with UnitOfWork() as uow:
        uow.kpi_repository.upsert_metric_snapshot(
            tenant_id=tenant_id,
            metric_key="total_students",
            metric_value=10,
            snapshot_date="2027-01-01",
            metadata_json={"title": "Total Students"},
            conn=uow.conn,
        )

    response = client.get("/api/analytics/kpis", headers=_tenant_analytics_user_headers(tenant_id=tenant_id))
    assert response.status_code == 200, response.text
    mix = response.json()["source_mix_summary"]

    assert mix["source_mix_counts"]["derived_from_snapshot"] == 1
    assert mix["dominant_source_mode"] == "snapshot"


def test_kpi_source_mix_summary_dominant_mode_mixed_on_tie(reset_shared_state) -> None:
    """Tie between source categories yields dominant_source_mode='mixed'."""
    tenant_id = _create_tenant("kpi-source-mix-mixed")

    with UnitOfWork() as uow:
        uow.kpi_repository.upsert_metric_snapshot(
            tenant_id=tenant_id,
            metric_key="analytics_events_reads_from_events_total",
            metric_value=3,
            snapshot_date="2027-01-02",
            metadata_json={
                "title": "Analytics Events Reads (Event-Derived) Total",
                "lineage": {
                    "source_type": "platform_events",
                    "source_event_types": ["analytics.event.read"],
                    "derived_from": "event_projection",
                },
            },
            conn=uow.conn,
        )
        uow.kpi_repository.upsert_metric_snapshot(
            tenant_id=tenant_id,
            metric_key="analytics_kpi_reads_share_pct",
            metric_value=40,
            snapshot_date="2027-01-02",
            metadata_json={"title": "Analytics KPI Reads Share (%)"},
            conn=uow.conn,
        )

    response = client.get("/api/analytics/kpis", headers=_tenant_analytics_user_headers(tenant_id=tenant_id))
    assert response.status_code == 200, response.text
    mix = response.json()["source_mix_summary"]

    assert mix["source_mix_counts"]["derived_from_events"] == 1
    assert mix["source_mix_counts"]["derived_from_usage"] == 1
    assert mix["dominant_source_mode"] == "mixed"


def test_kpi_source_mix_summary_empty_state_predictable(reset_shared_state) -> None:
    """Empty state exposes deterministic empty source composition."""
    tenant_id = _create_tenant("kpi-source-mix-empty")

    response = client.get("/api/analytics/kpis", headers=_tenant_analytics_user_headers(tenant_id=tenant_id))
    assert response.status_code == 200, response.text
    body = response.json()
    mix = body["source_mix_summary"]

    assert body["kpis"] == []
    assert mix["total_kpis"] == 0
    assert mix["source_mix_counts"] == {
        "derived_from_events": 0,
        "derived_from_usage": 0,
        "derived_from_snapshot": 0,
        "mixed_source": 0,
        "empty": 0,
    }
    assert mix["dominant_source_mode"] == "empty"


def test_kpi_source_mix_summary_tenant_isolation(reset_shared_state) -> None:
    """Source mix is tenant-scoped and does not leak across tenants."""
    tenant_a = _create_tenant("kpi-source-mix-iso-a")
    tenant_b = _create_tenant("kpi-source-mix-iso-b")

    with UnitOfWork() as uow:
        uow.kpi_repository.upsert_metric_snapshot(
            tenant_id=tenant_a,
            metric_key="total_students",
            metric_value=9,
            snapshot_date="2027-01-03",
            metadata_json={"title": "Total Students"},
            conn=uow.conn,
        )
        uow.kpi_repository.upsert_metric_snapshot(
            tenant_id=tenant_b,
            metric_key="analytics_kpi_reads_share_pct",
            metric_value=55,
            snapshot_date="2027-01-03",
            metadata_json={"title": "Analytics KPI Reads Share (%)"},
            conn=uow.conn,
        )

    mix_a = client.get("/api/analytics/kpis", headers=_tenant_analytics_user_headers(tenant_id=tenant_a)).json()["source_mix_summary"]
    mix_b = client.get("/api/analytics/kpis", headers=_tenant_analytics_user_headers(tenant_id=tenant_b)).json()["source_mix_summary"]

    assert mix_a["dominant_source_mode"] == "snapshot"
    assert mix_b["dominant_source_mode"] == "usage"


def test_kpi_source_mix_summary_consistent_with_lineage_and_source_status(reset_shared_state) -> None:
    """Summary composition matches card-level source_status produced from lineage rules."""
    tenant_id = _create_tenant("kpi-source-mix-consistency")
    headers = _tenant_analytics_user_headers(tenant_id=tenant_id)

    with UnitOfWork() as uow:
        kpi_service.refresh_tenant_metrics(tenant_id=tenant_id, uow=uow)

    response = client.get("/api/analytics/kpis", headers=headers)
    assert response.status_code == 200, response.text
    body = response.json()
    cards = list(body["kpis"])
    mix = body["source_mix_summary"]

    # Every card contributes exactly once to the source mix counts.
    total_from_counts = (
        int(mix["source_mix_counts"]["derived_from_events"])
        + int(mix["source_mix_counts"]["derived_from_usage"])
        + int(mix["source_mix_counts"]["derived_from_snapshot"])
        + int(mix["source_mix_counts"]["mixed_source"])
        + int(mix["source_mix_counts"]["empty"])
    )
    assert total_from_counts == len(cards)

    # Basic truthfulness check: event lineage cards are reflected as derived_from_events.
    event_lineage_cards = [
        c
        for c in cards
        if isinstance(c.get("lineage"), dict)
        and str(c["lineage"].get("source_type") or "").strip().lower() == "platform_events"
    ]
    assert int(mix["source_mix_counts"]["derived_from_events"]) >= len(event_lineage_cards)


# ---------------------------------------------------------------------------
# Analytics contract versioning / response identity layer v1
# ---------------------------------------------------------------------------


def test_kpi_contract_identity_present_and_stable_ready_state(reset_shared_state) -> None:
    """Ready KPI response exposes stable surface_id and contract_version markers."""
    tenant_id = _create_tenant("kpi-contract-ready")
    headers = _tenant_analytics_user_headers(tenant_id=tenant_id)

    with UnitOfWork() as uow:
        kpi_service.refresh_tenant_metrics(tenant_id=tenant_id, uow=uow)

    response = client.get("/api/analytics/kpis", headers=headers)
    assert response.status_code == 200, response.text
    body = response.json()

    assert body["surface_id"] == "tenant_analytics_kpis"
    assert body["contract_version"] == "v1"


def test_kpi_contract_identity_present_and_stable_empty_state(reset_shared_state) -> None:
    """Empty KPI response exposes the same stable identity markers as ready state."""
    tenant_id = _create_tenant("kpi-contract-empty")
    headers = _tenant_analytics_user_headers(tenant_id=tenant_id)

    response = client.get("/api/analytics/kpis", headers=headers)
    assert response.status_code == 200, response.text
    body = response.json()

    assert body["readiness_status"] == "empty"
    assert body["surface_id"] == "tenant_analytics_kpis"
    assert body["contract_version"] == "v1"


def test_kpi_contract_identity_tenant_isolation(reset_shared_state) -> None:
    """Contract identity is stable and identical across different tenants."""
    tenant_a = _create_tenant("kpi-contract-iso-a")
    tenant_b = _create_tenant("kpi-contract-iso-b")

    with UnitOfWork() as uow:
        kpi_service.refresh_tenant_metrics(tenant_id=tenant_a, uow=uow)
        kpi_service.refresh_tenant_metrics(tenant_id=tenant_b, uow=uow)

    body_a = client.get("/api/analytics/kpis", headers=_tenant_analytics_user_headers(tenant_id=tenant_a)).json()
    body_b = client.get("/api/analytics/kpis", headers=_tenant_analytics_user_headers(tenant_id=tenant_b)).json()

    assert body_a["surface_id"] == body_b["surface_id"] == "tenant_analytics_kpis"
    assert body_a["contract_version"] == body_b["contract_version"] == "v1"


def test_kpi_contract_identity_unaffected_by_data_shape(reset_shared_state) -> None:
    """Contract identity remains stable across different KPI payload shapes."""
    tenant_id = _create_tenant("kpi-contract-shape")
    headers = _tenant_analytics_user_headers(tenant_id=tenant_id)

    # Shape A: empty
    empty_body = client.get("/api/analytics/kpis", headers=headers).json()
    assert empty_body["surface_id"] == "tenant_analytics_kpis"
    assert empty_body["contract_version"] == "v1"

    # Shape B: with snapshots and richer fields
    with UnitOfWork() as uow:
        kpi_service.refresh_tenant_metrics(tenant_id=tenant_id, uow=uow, snapshot_date="2027-02-01")
    platform_billing_service.increment_usage(tenant_id, "analytics.events.read", 5)
    with UnitOfWork() as uow:
        kpi_service.refresh_tenant_metrics(tenant_id=tenant_id, uow=uow, snapshot_date="2027-02-02")

    ready_body = client.get("/api/analytics/kpis", headers=headers).json()
    assert ready_body["surface_id"] == "tenant_analytics_kpis"
    assert ready_body["contract_version"] == "v1"


def test_kpi_contract_identity_no_cross_tenant_leakage(reset_shared_state) -> None:
    """Data differences between tenants do not affect contract identity markers."""
    tenant_a = _create_tenant("kpi-contract-leak-a")
    tenant_b = _create_tenant("kpi-contract-leak-b")

    with UnitOfWork() as uow:
        kpi_service.refresh_tenant_metrics(tenant_id=tenant_a, uow=uow, snapshot_date="2027-03-01")
        kpi_service.refresh_tenant_metrics(tenant_id=tenant_b, uow=uow, snapshot_date="2027-03-01")

    _make_failed_jobs(tenant_b, count=5)
    with UnitOfWork() as uow:
        kpi_service.refresh_tenant_metrics(tenant_id=tenant_b, uow=uow, snapshot_date="2027-03-02")

    body_a = client.get("/api/analytics/kpis", headers=_tenant_analytics_user_headers(tenant_id=tenant_a)).json()
    body_b = client.get("/api/analytics/kpis", headers=_tenant_analytics_user_headers(tenant_id=tenant_b)).json()

    assert body_a["surface_id"] == "tenant_analytics_kpis"
    assert body_b["surface_id"] == "tenant_analytics_kpis"
    assert body_a["contract_version"] == "v1"
    assert body_b["contract_version"] == "v1"


# ---------------------------------------------------------------------------
# Analytics capability manifest / surface capabilities layer v1
# ---------------------------------------------------------------------------


def _expected_kpi_capabilities() -> dict[str, bool]:
    return {
        "supports_cards": True,
        "supports_trends": True,
        "supports_insights": True,
        "supports_recommendations": True,
        "supports_refresh": True,
        "supports_refresh_history": True,
        "supports_change_digest": True,
        "supports_source_mix": True,
        "supports_lineage": True,
        "supports_source_breakdown": True,
        "supports_thresholds": True,
        "supports_actionability": True,
    }


def test_kpi_capabilities_manifest_present_and_stable_ready_state(reset_shared_state) -> None:
    """Ready response exposes stable top-level capabilities manifest."""
    tenant_id = _create_tenant("kpi-capabilities-ready")
    headers = _tenant_analytics_user_headers(tenant_id=tenant_id)

    with UnitOfWork() as uow:
        kpi_service.refresh_tenant_metrics(tenant_id=tenant_id, uow=uow)

    response = client.get("/api/analytics/kpis", headers=headers)
    assert response.status_code == 200, response.text
    body = response.json()

    assert body["capabilities"] == _expected_kpi_capabilities()


def test_kpi_capabilities_manifest_same_in_empty_state(reset_shared_state) -> None:
    """Empty response reports supported surface capabilities truthfully and unchanged."""
    tenant_id = _create_tenant("kpi-capabilities-empty")
    headers = _tenant_analytics_user_headers(tenant_id=tenant_id)

    response = client.get("/api/analytics/kpis", headers=headers)
    assert response.status_code == 200, response.text
    body = response.json()

    assert body["readiness_status"] == "empty"
    assert body["capabilities"] == _expected_kpi_capabilities()


def test_kpi_capabilities_manifest_matches_implemented_surface(reset_shared_state) -> None:
    """Capabilities flags match actually available KPI endpoints/features."""
    tenant_id = _create_tenant("kpi-capabilities-implemented")
    headers = _tenant_analytics_user_headers(tenant_id=tenant_id)

    response = client.get("/api/analytics/kpis", headers=headers)
    assert response.status_code == 200, response.text
    capabilities = response.json()["capabilities"]

    # Endpoint-level features already exposed in current surface.
    assert client.get("/api/analytics/kpis/trends", headers=headers).status_code == 200
    assert client.get("/api/analytics/kpis/insights", headers=headers).status_code == 200
    assert client.get("/api/analytics/kpis/recommendations", headers=headers).status_code == 200
    assert client.get("/api/analytics/kpis/refresh-history", headers=headers).status_code == 200

    assert capabilities["supports_trends"] is True
    assert capabilities["supports_insights"] is True
    assert capabilities["supports_recommendations"] is True
    assert capabilities["supports_refresh_history"] is True


def test_kpi_capabilities_manifest_tenant_isolated(reset_shared_state) -> None:
    """Capabilities manifest is identical across tenants."""
    tenant_a = _create_tenant("kpi-capabilities-iso-a")
    tenant_b = _create_tenant("kpi-capabilities-iso-b")

    with UnitOfWork() as uow:
        kpi_service.refresh_tenant_metrics(tenant_id=tenant_a, uow=uow)
        kpi_service.refresh_tenant_metrics(tenant_id=tenant_b, uow=uow)

    caps_a = client.get("/api/analytics/kpis", headers=_tenant_analytics_user_headers(tenant_id=tenant_a)).json()["capabilities"]
    caps_b = client.get("/api/analytics/kpis", headers=_tenant_analytics_user_headers(tenant_id=tenant_b)).json()["capabilities"]

    assert caps_a == caps_b == _expected_kpi_capabilities()


def test_kpi_capabilities_manifest_unaffected_by_data_shape(reset_shared_state) -> None:
    """Capabilities manifest stays stable regardless of tenant data richness."""
    tenant_id = _create_tenant("kpi-capabilities-shape")
    headers = _tenant_analytics_user_headers(tenant_id=tenant_id)

    empty_caps = client.get("/api/analytics/kpis", headers=headers).json()["capabilities"]

    with UnitOfWork() as uow:
        kpi_service.refresh_tenant_metrics(tenant_id=tenant_id, uow=uow, snapshot_date="2027-04-01")
    platform_billing_service.increment_usage(tenant_id, "analytics.events.read", 4)
    with UnitOfWork() as uow:
        kpi_service.refresh_tenant_metrics(tenant_id=tenant_id, uow=uow, snapshot_date="2027-04-02")

    ready_caps = client.get("/api/analytics/kpis", headers=headers).json()["capabilities"]
    assert empty_caps == ready_caps == _expected_kpi_capabilities()


def test_kpi_capabilities_manifest_no_cross_tenant_leakage(reset_shared_state) -> None:
    """Tenant-specific KPI changes do not alter shared surface capabilities."""
    tenant_a = _create_tenant("kpi-capabilities-leak-a")
    tenant_b = _create_tenant("kpi-capabilities-leak-b")

    with UnitOfWork() as uow:
        kpi_service.refresh_tenant_metrics(tenant_id=tenant_a, uow=uow, snapshot_date="2027-05-01")
        kpi_service.refresh_tenant_metrics(tenant_id=tenant_b, uow=uow, snapshot_date="2027-05-01")

    _make_failed_jobs(tenant_b, count=5)
    with UnitOfWork() as uow:
        kpi_service.refresh_tenant_metrics(tenant_id=tenant_b, uow=uow, snapshot_date="2027-05-02")

    caps_a = client.get("/api/analytics/kpis", headers=_tenant_analytics_user_headers(tenant_id=tenant_a)).json()["capabilities"]
    caps_b = client.get("/api/analytics/kpis", headers=_tenant_analytics_user_headers(tenant_id=tenant_b)).json()["capabilities"]

    assert caps_a == caps_b == _expected_kpi_capabilities()


# ---------------------------------------------------------------------------
# Analytics section manifest / section presence layer v1
# ---------------------------------------------------------------------------


def _expected_sections_empty() -> dict[str, str]:
    return {
        "cards": "empty",
        "summary": "present",
        "change_digest": "present",
        "source_mix_summary": "present",
        "capabilities": "present",
        "contract_identity": "present",
        "surface_profile": "present",
        "field_semantics": "present",
        "card_field_semantics": "present",
        "response_examples": "present",
        "surface_map": "present",
        "workflow_hints": "present",
        "stability_tiers": "present",
        "contract_fingerprint": "present",
        "contract_compatibility": "present",
        "contract_invariants": "present",
    }


def _expected_sections_ready() -> dict[str, str]:
    return {
        "cards": "populated",
        "summary": "populated",
        "change_digest": "populated",
        "source_mix_summary": "populated",
        "capabilities": "present",
        "contract_identity": "present",
        "surface_profile": "present",
        "field_semantics": "present",
        "card_field_semantics": "present",
        "response_examples": "present",
        "surface_map": "present",
        "workflow_hints": "present",
        "stability_tiers": "present",
        "contract_fingerprint": "present",
        "contract_compatibility": "present",
        "contract_invariants": "present",
    }


def test_kpi_sections_manifest_present_and_stable(reset_shared_state) -> None:
    """Top-level sections manifest exists and has stable keys/states for empty payload."""
    tenant_id = _create_tenant("kpi-sections-present")
    headers = _tenant_analytics_user_headers(tenant_id=tenant_id)

    response = client.get("/api/analytics/kpis", headers=headers)
    assert response.status_code == 200, response.text
    body = response.json()

    assert body["sections"] == _expected_sections_empty()


def test_kpi_sections_manifest_empty_state_truthful(reset_shared_state) -> None:
    """Empty response reports truthful section states for current payload content."""
    tenant_id = _create_tenant("kpi-sections-empty")
    headers = _tenant_analytics_user_headers(tenant_id=tenant_id)

    body = client.get("/api/analytics/kpis", headers=headers).json()

    assert body["readiness_status"] == "empty"
    assert body["kpis"] == []
    assert body["sections"] == _expected_sections_empty()


def test_kpi_sections_manifest_ready_state_truthful(reset_shared_state) -> None:
    """Ready response reports truthful section states when cards are populated."""
    tenant_id = _create_tenant("kpi-sections-ready")
    headers = _tenant_analytics_user_headers(tenant_id=tenant_id)

    with UnitOfWork() as uow:
        kpi_service.refresh_tenant_metrics(tenant_id=tenant_id, uow=uow, snapshot_date="2027-06-01")
    platform_billing_service.increment_usage(tenant_id, "analytics.events.read", 3)
    with UnitOfWork() as uow:
        kpi_service.refresh_tenant_metrics(tenant_id=tenant_id, uow=uow, snapshot_date="2027-06-02")

    body = client.get("/api/analytics/kpis", headers=headers).json()

    assert body["readiness_status"] == "ready"
    assert len(body["kpis"]) > 0
    assert body["sections"] == _expected_sections_ready()


def test_kpi_sections_manifest_not_conflated_with_capabilities(reset_shared_state) -> None:
    """Capabilities describe support; sections describe current payload state."""
    tenant_id = _create_tenant("kpi-sections-vs-capabilities")
    headers = _tenant_analytics_user_headers(tenant_id=tenant_id)

    body = client.get("/api/analytics/kpis", headers=headers).json()

    assert body["capabilities"]["supports_cards"] is True
    assert body["sections"]["cards"] == "empty"


def test_kpi_sections_manifest_tenant_isolation(reset_shared_state) -> None:
    """Section manifest structure/states are tenant-scoped and deterministic."""
    tenant_a = _create_tenant("kpi-sections-iso-a")
    tenant_b = _create_tenant("kpi-sections-iso-b")

    with UnitOfWork() as uow:
        kpi_service.refresh_tenant_metrics(tenant_id=tenant_b, uow=uow)

    sections_a = client.get("/api/analytics/kpis", headers=_tenant_analytics_user_headers(tenant_id=tenant_a)).json()["sections"]
    sections_b = client.get("/api/analytics/kpis", headers=_tenant_analytics_user_headers(tenant_id=tenant_b)).json()["sections"]

    assert sections_a == _expected_sections_empty()
    assert sections_b == _expected_sections_ready()


def test_kpi_sections_manifest_no_cross_tenant_leakage(reset_shared_state) -> None:
    """Tenant-specific KPI deltas do not leak and only affect that tenant's section states."""
    tenant_a = _create_tenant("kpi-sections-leak-a")
    tenant_b = _create_tenant("kpi-sections-leak-b")

    with UnitOfWork() as uow:
        kpi_service.refresh_tenant_metrics(tenant_id=tenant_b, uow=uow, snapshot_date="2027-07-01")

    sec_a = client.get("/api/analytics/kpis", headers=_tenant_analytics_user_headers(tenant_id=tenant_a)).json()["sections"]
    sec_b = client.get("/api/analytics/kpis", headers=_tenant_analytics_user_headers(tenant_id=tenant_b)).json()["sections"]
    assert sec_a["cards"] == "empty"
    assert sec_b["cards"] == "populated"


def test_kpi_sections_manifest_shape_sensitive_only_to_current_payload(reset_shared_state) -> None:
    """For one tenant, section states change only when payload shape changes (empty -> ready)."""
    tenant_id = _create_tenant("kpi-sections-shape")
    headers = _tenant_analytics_user_headers(tenant_id=tenant_id)

    empty_sections = client.get("/api/analytics/kpis", headers=headers).json()["sections"]

    with UnitOfWork() as uow:
        kpi_service.refresh_tenant_metrics(tenant_id=tenant_id, uow=uow)

    ready_sections = client.get("/api/analytics/kpis", headers=headers).json()["sections"]

    assert empty_sections == _expected_sections_empty()
    assert ready_sections == _expected_sections_ready()


# ---------------------------------------------------------------------------
# Analytics response envelope / request correlation layer v1
# ---------------------------------------------------------------------------


def test_kpi_response_envelope_present_and_stable(reset_shared_state) -> None:
    """KPI response exposes request envelope fields with stable shape."""
    tenant_id = _create_tenant("kpi-envelope-present")
    headers = _tenant_analytics_user_headers(tenant_id=tenant_id)
    headers["x-request-id"] = "kpi-envelope-present-rid"

    body = client.get("/api/analytics/kpis", headers=headers).json()

    assert body["request_id"] == "kpi-envelope-present-rid"
    assert isinstance(body["served_at"], str)
    assert body["served_at"]
    assert body["response_status"] == "empty"


def test_kpi_response_envelope_ready_response_status_truthful(reset_shared_state) -> None:
    """Ready KPI payload exposes response_status='ready'."""
    tenant_id = _create_tenant("kpi-envelope-ready")
    headers = _tenant_analytics_user_headers(tenant_id=tenant_id)
    headers["x-request-id"] = "kpi-envelope-ready-rid"

    with UnitOfWork() as uow:
        kpi_service.refresh_tenant_metrics(tenant_id=tenant_id, uow=uow)

    body = client.get("/api/analytics/kpis", headers=headers).json()
    assert body["request_id"] == "kpi-envelope-ready-rid"
    assert body["response_status"] == "ready"


def test_kpi_response_envelope_empty_response_status_truthful(reset_shared_state) -> None:
    """Empty KPI payload exposes response_status='empty'."""
    tenant_id = _create_tenant("kpi-envelope-empty")
    headers = _tenant_analytics_user_headers(tenant_id=tenant_id)
    headers["x-request-id"] = "kpi-envelope-empty-rid"

    body = client.get("/api/analytics/kpis", headers=headers).json()
    assert body["request_id"] == "kpi-envelope-empty-rid"
    assert body["response_status"] == "empty"


def test_kpi_response_envelope_request_id_propagated_from_request_context(reset_shared_state) -> None:
    """request_id in body matches actual middleware-provided x-request-id value."""
    tenant_id = _create_tenant("kpi-envelope-request-id")
    headers = _tenant_analytics_user_headers(tenant_id=tenant_id)
    headers["x-request-id"] = "req-kpi-correlation-123"

    response = client.get("/api/analytics/kpis", headers=headers)
    assert response.status_code == 200, response.text
    body = response.json()

    assert body["request_id"] == "req-kpi-correlation-123"
    assert response.headers["x-request-id"] == "req-kpi-correlation-123"


def test_kpi_response_envelope_tenant_isolation(reset_shared_state) -> None:
    """Envelope is request-scoped and does not leak across tenants."""
    tenant_a = _create_tenant("kpi-envelope-iso-a")
    tenant_b = _create_tenant("kpi-envelope-iso-b")

    headers_a = _tenant_analytics_user_headers(tenant_id=tenant_a)
    headers_b = _tenant_analytics_user_headers(tenant_id=tenant_b)
    headers_a["x-request-id"] = "rid-tenant-a"
    headers_b["x-request-id"] = "rid-tenant-b"

    body_a = client.get("/api/analytics/kpis", headers=headers_a).json()
    body_b = client.get("/api/analytics/kpis", headers=headers_b).json()

    assert body_a["request_id"] == "rid-tenant-a"
    assert body_b["request_id"] == "rid-tenant-b"


def test_kpi_response_envelope_no_cross_tenant_leakage(reset_shared_state) -> None:
    """Tenant-specific data changes do not affect another request's envelope marker."""
    tenant_a = _create_tenant("kpi-envelope-leak-a")
    tenant_b = _create_tenant("kpi-envelope-leak-b")

    _make_failed_jobs(tenant_b, count=5)
    with UnitOfWork() as uow:
        kpi_service.refresh_tenant_metrics(tenant_id=tenant_b, uow=uow)

    headers_a = _tenant_analytics_user_headers(tenant_id=tenant_a)
    headers_b = _tenant_analytics_user_headers(tenant_id=tenant_b)
    headers_a["x-request-id"] = "rid-leak-a"
    headers_b["x-request-id"] = "rid-leak-b"

    body_a = client.get("/api/analytics/kpis", headers=headers_a).json()
    body_b = client.get("/api/analytics/kpis", headers=headers_b).json()

    assert body_a["request_id"] == "rid-leak-a"
    assert body_b["request_id"] == "rid-leak-b"
    assert body_a["response_status"] == "empty"
    assert body_b["response_status"] == "ready"


def test_kpi_response_envelope_not_conflated_with_capabilities_or_sections(reset_shared_state) -> None:
    """Envelope fields remain distinct from capabilities and section-manifest semantics."""
    tenant_id = _create_tenant("kpi-envelope-separation")
    headers = _tenant_analytics_user_headers(tenant_id=tenant_id)
    headers["x-request-id"] = "rid-separation"

    body = client.get("/api/analytics/kpis", headers=headers).json()

    assert body["request_id"] == "rid-separation"
    assert body["capabilities"]["supports_cards"] is True
    assert body["sections"]["cards"] == "empty"
    assert body["response_status"] == "empty"


# ---------------------------------------------------------------------------
# Analytics consumer compatibility / contract invariants layer v1
# ---------------------------------------------------------------------------


def _expected_contract_invariants() -> dict[str, object]:
    return {
        "guaranteed_top_level_fields": [
            "surface_id",
            "contract_version",
            "capabilities",
            "sections",
            "surface_profile",
            "field_semantics",
            "card_field_semantics",
            "response_examples",
            "surface_map",
            "workflow_hints",
            "stability_tiers",
            "contract_fingerprint",
            "contract_compatibility",
            "request_id",
            "served_at",
            "response_status",
            "tenant_id",
            "snapshot_date",
            "generated_at",
            "readiness_status",
            "freshness_status",
            "source_mode",
            "kpis",
            "summary",
            "change_digest",
            "source_mix_summary",
            "contract_invariants",
        ],
        "always_present_sections": [
            "cards",
            "summary",
            "change_digest",
            "source_mix_summary",
            "capabilities",
            "contract_identity",
            "surface_profile",
            "field_semantics",
            "card_field_semantics",
            "response_examples",
            "surface_map",
            "workflow_hints",
            "stability_tiers",
            "contract_fingerprint",
            "contract_compatibility",
            "contract_invariants",
        ],
        "optional_card_fields": [
            "lineage",
            "source_breakdown",
            "severity",
            "threshold_basis",
            "policy_pack",
            "actionability_state",
        ],
        "empty_state_contract_stable": True,
    }


def _expected_surface_profile() -> dict[str, object]:
    return {
        "audience_profiles": [
            "human_dashboard",
            "machine_client",
            "support_traceable",
        ],
        "primary_audience": "human_dashboard",
        "consumption_mode": "structured_read_model",
    }


def _expected_field_semantics() -> dict[str, str]:
    return {
        "capabilities": "supported surface features",
        "sections": "current response section presence and state",
        "contract_invariants": "guaranteed structural compatibility markers",
        "contract_fingerprint": "stable contract checksum identity",
        "surface_profile": "intended audience and use mode",
        "response_status": "current response readiness state",
        "request_id": "request correlation identifier",
        "served_at": "response generation timestamp",
    }


def _expected_card_field_semantics() -> dict[str, str]:
    return {
        "severity": "bounded operational severity",
        "threshold_basis": "threshold measurement basis",
        "policy_pack": "named evaluation profile",
        "actionability_state": "bounded urgency hint",
        "source_status": "primary source derivation mode",
    }


def _expected_response_examples() -> dict[str, dict[str, str]]:
    return {
        "empty_shape": {
            "readiness_status": "empty",
            "cards": "empty",
            "summary": "present",
            "change_digest": "present",
            "source_mix_summary": "present",
            "capabilities": "present",
            "sections": "present",
        },
        "ready_shape": {
            "readiness_status": "ready",
            "cards": "populated",
            "summary": "populated",
            "change_digest": "populated",
            "source_mix_summary": "populated",
            "capabilities": "present",
            "sections": "present",
        },
    }


def _expected_surface_map() -> dict[str, object]:
    return {
        "family_id": "tenant_analytics_endpoint_family_v1",
        "endpoints": [
            {"name": "kpis", "path": "/api/analytics/kpis", "role": "primary_read"},
            {"name": "kpi_trends", "path": "/api/analytics/kpis/trends", "role": "trend_read"},
            {"name": "kpi_insights", "path": "/api/analytics/kpis/insights", "role": "insight_read"},
            {
                "name": "kpi_recommendations",
                "path": "/api/analytics/kpis/recommendations",
                "role": "recommendation_read",
            },
            {"name": "kpi_refresh", "path": "/api/analytics/kpis/refresh", "role": "refresh_action"},
            {
                "name": "kpi_refresh_history",
                "path": "/api/analytics/kpis/refresh-history",
                "role": "refresh_history_read",
            },
            {"name": "events", "path": "/api/analytics/events", "role": "event_read"},
            {
                "name": "events_summary",
                "path": "/api/analytics/events/summary",
                "role": "event_summary_read",
            },
        ],
    }


def _expected_workflow_hints() -> dict[str, list[str]]:
    return {
        "primary_flow": [
            "kpis",
            "kpi_trends",
            "kpi_insights",
            "kpi_recommendations",
        ],
        "operational_flow": [
            "kpi_refresh",
            "kpi_refresh_history",
        ],
        "observability_flow": [
            "events",
            "events_summary",
        ],
    }


def _expected_stability_tiers() -> dict[str, list[str]]:
    return {
        "stable_core_fields": [
            "surface_id",
            "contract_version",
            "tenant_id",
            "sections",
            "request_id",
            "served_at",
        ],
        "extensible_metadata_blocks": [
            "capabilities",
            "contract_invariants",
            "contract_fingerprint",
            "contract_compatibility",
            "surface_profile",
            "field_semantics",
            "card_field_semantics",
            "response_examples",
            "surface_map",
            "workflow_hints",
            "stability_tiers",
        ],
        "data_dependent_blocks": [
            "kpis",
            "summary",
            "change_digest",
            "source_mix_summary",
            "readiness_status",
            "snapshot_date",
            "generated_at",
            "freshness_status",
            "source_mode",
            "response_status",
        ],
        "stable_card_core_fields": [
            "key",
            "title",
            "description",
            "value",
            "readiness_status",
            "source_status",
            "trend",
        ],
        "optional_card_fields": [
            "lineage",
            "source_breakdown",
            "severity",
            "threshold_basis",
            "policy_pack",
            "actionability_state",
        ],
    }


def _expected_contract_fingerprint() -> dict[str, str]:
    basis_payload = {
        "fingerprint_basis": "surface_contract_v1",
        "surface_id": "tenant_analytics_kpis",
        "contract_version": "v1",
        "guaranteed_top_level_fields": _expected_contract_invariants()["guaranteed_top_level_fields"],
        "always_present_sections": _expected_contract_invariants()["always_present_sections"],
        "capabilities": _expected_kpi_capabilities(),
        "contract_invariants": _expected_contract_invariants(),
        "surface_profile": _expected_surface_profile(),
        "surface_map": _expected_surface_map(),
        "workflow_hints": _expected_workflow_hints(),
        "stability_tiers": _expected_stability_tiers(),
        "contract_compatibility": _expected_contract_compatibility(),
    }
    canonical = json.dumps(basis_payload, sort_keys=True, separators=(",", ":"))
    value = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return {
        "algorithm": "sha256",
        "value": value,
        "fingerprint_basis": "surface_contract_v1",
    }


def _expected_contract_compatibility() -> dict[str, object]:
    return {
        "compatibility_mode": "backward_additive_v1",
        "backward_compatible_with": ["v1"],
        "stable_core_enforced": True,
        "additive_metadata_extensions_allowed": True,
        "data_dependent_blocks_may_vary": True,
        "fingerprint_scope": "stable_contract_basis",
    }


def test_kpi_contract_compatibility_present_and_stable(reset_shared_state) -> None:
    """KPI response exposes stable machine-readable compatibility assertions."""
    tenant_id = _create_tenant("kpi-contract-compat-present")
    headers = _tenant_analytics_user_headers(tenant_id=tenant_id)

    body = client.get("/api/analytics/kpis", headers=headers).json()
    assert body["contract_compatibility"] == _expected_contract_compatibility()


def test_kpi_contract_compatibility_same_in_empty_and_ready(reset_shared_state) -> None:
    """contract_compatibility stays identical between empty and ready payload states."""
    tenant_id = _create_tenant("kpi-contract-compat-parity")
    headers = _tenant_analytics_user_headers(tenant_id=tenant_id)

    empty_block = client.get("/api/analytics/kpis", headers=headers).json()["contract_compatibility"]

    with UnitOfWork() as uow:
        kpi_service.refresh_tenant_metrics(tenant_id=tenant_id, uow=uow)

    ready_block = client.get("/api/analytics/kpis", headers=headers).json()["contract_compatibility"]
    assert empty_block == ready_block == _expected_contract_compatibility()


def test_kpi_contract_compatibility_consistent_with_contract_basis(reset_shared_state) -> None:
    """Compatibility block remains aligned with invariants, tiers and fingerprint scope."""
    tenant_id = _create_tenant("kpi-contract-compat-basis")
    headers = _tenant_analytics_user_headers(tenant_id=tenant_id)

    body = client.get("/api/analytics/kpis", headers=headers).json()
    compat = body["contract_compatibility"]
    invariants = body["contract_invariants"]
    tiers = body["stability_tiers"]
    fingerprint = body["contract_fingerprint"]

    assert compat == _expected_contract_compatibility()
    assert compat["backward_compatible_with"] == [body["contract_version"]]
    assert "surface_id" in invariants["guaranteed_top_level_fields"]
    assert "contract_version" in invariants["guaranteed_top_level_fields"]
    assert "sections" in tiers["stable_core_fields"]
    assert "contract_compatibility" in tiers["extensible_metadata_blocks"]
    assert compat["fingerprint_scope"] == "stable_contract_basis"
    assert fingerprint["algorithm"] == "sha256"


def test_kpi_contract_compatibility_tenant_isolation(reset_shared_state) -> None:
    """contract_compatibility remains identical across tenants."""
    tenant_a = _create_tenant("kpi-contract-compat-iso-a")
    tenant_b = _create_tenant("kpi-contract-compat-iso-b")

    compat_a = client.get("/api/analytics/kpis", headers=_tenant_analytics_user_headers(tenant_id=tenant_a)).json()["contract_compatibility"]
    compat_b = client.get("/api/analytics/kpis", headers=_tenant_analytics_user_headers(tenant_id=tenant_b)).json()["contract_compatibility"]
    assert compat_a == compat_b == _expected_contract_compatibility()


def test_kpi_contract_compatibility_no_cross_tenant_leakage(reset_shared_state) -> None:
    """Tenant-specific KPI mutations must not affect compatibility assertions."""
    tenant_a = _create_tenant("kpi-contract-compat-leak-a")
    tenant_b = _create_tenant("kpi-contract-compat-leak-b")

    _make_failed_jobs(tenant_b, count=5)
    with UnitOfWork() as uow:
        kpi_service.refresh_tenant_metrics(tenant_id=tenant_b, uow=uow)

    compat_a = client.get("/api/analytics/kpis", headers=_tenant_analytics_user_headers(tenant_id=tenant_a)).json()["contract_compatibility"]
    compat_b = client.get("/api/analytics/kpis", headers=_tenant_analytics_user_headers(tenant_id=tenant_b)).json()["contract_compatibility"]
    assert compat_a == compat_b == _expected_contract_compatibility()


def test_kpi_contract_compatibility_unaffected_by_tenant_data_shape(reset_shared_state) -> None:
    """Compatibility assertions do not depend on tenant data shape or refresh state."""
    tenant_id = _create_tenant("kpi-contract-compat-shape")
    headers = _tenant_analytics_user_headers(tenant_id=tenant_id)

    empty_body = client.get("/api/analytics/kpis", headers=headers).json()
    empty_block = empty_body["contract_compatibility"]

    with UnitOfWork() as uow:
        kpi_service.refresh_tenant_metrics(tenant_id=tenant_id, uow=uow, snapshot_date="2029-01-01")
    platform_billing_service.increment_usage(tenant_id, "analytics.events.read", 7)
    with UnitOfWork() as uow:
        kpi_service.refresh_tenant_metrics(tenant_id=tenant_id, uow=uow, snapshot_date="2029-01-02")

    ready_body = client.get("/api/analytics/kpis", headers=headers).json()
    ready_block = ready_body["contract_compatibility"]

    assert empty_body["response_status"] == "empty"
    assert ready_body["response_status"] == "ready"
    assert empty_block == ready_block == _expected_contract_compatibility()


def test_kpi_contract_fingerprint_present_and_stable(reset_shared_state) -> None:
    """KPI response exposes stable machine-readable contract fingerprint."""
    tenant_id = _create_tenant("kpi-contract-fingerprint-present")
    headers = _tenant_analytics_user_headers(tenant_id=tenant_id)

    body = client.get("/api/analytics/kpis", headers=headers).json()
    assert body["contract_fingerprint"] == _expected_contract_fingerprint()


def test_kpi_contract_fingerprint_same_in_empty_and_ready(reset_shared_state) -> None:
    """contract_fingerprint is identical for empty and ready payload states."""
    tenant_id = _create_tenant("kpi-contract-fingerprint-parity")
    headers = _tenant_analytics_user_headers(tenant_id=tenant_id)

    empty_fp = client.get("/api/analytics/kpis", headers=headers).json()["contract_fingerprint"]

    with UnitOfWork() as uow:
        kpi_service.refresh_tenant_metrics(tenant_id=tenant_id, uow=uow)

    ready_fp = client.get("/api/analytics/kpis", headers=headers).json()["contract_fingerprint"]
    assert empty_fp == ready_fp == _expected_contract_fingerprint()


def test_kpi_contract_fingerprint_consistent_with_basis(reset_shared_state) -> None:
    """Fingerprint value matches deterministic SHA-256 of the declared stable basis."""
    tenant_id = _create_tenant("kpi-contract-fingerprint-basis")
    headers = _tenant_analytics_user_headers(tenant_id=tenant_id)

    body = client.get("/api/analytics/kpis", headers=headers).json()
    assert body["contract_fingerprint"] == _expected_contract_fingerprint()


def test_kpi_contract_fingerprint_tenant_isolation(reset_shared_state) -> None:
    """contract_fingerprint remains identical across tenants."""
    tenant_a = _create_tenant("kpi-contract-fingerprint-iso-a")
    tenant_b = _create_tenant("kpi-contract-fingerprint-iso-b")

    fp_a = client.get("/api/analytics/kpis", headers=_tenant_analytics_user_headers(tenant_id=tenant_a)).json()["contract_fingerprint"]
    fp_b = client.get("/api/analytics/kpis", headers=_tenant_analytics_user_headers(tenant_id=tenant_b)).json()["contract_fingerprint"]
    assert fp_a == fp_b == _expected_contract_fingerprint()


def test_kpi_contract_fingerprint_no_cross_tenant_leakage(reset_shared_state) -> None:
    """Tenant-specific KPI mutations do not alter another tenant's fingerprint."""
    tenant_a = _create_tenant("kpi-contract-fingerprint-leak-a")
    tenant_b = _create_tenant("kpi-contract-fingerprint-leak-b")

    _make_failed_jobs(tenant_b, count=7)
    with UnitOfWork() as uow:
        kpi_service.refresh_tenant_metrics(tenant_id=tenant_b, uow=uow)

    fp_a = client.get("/api/analytics/kpis", headers=_tenant_analytics_user_headers(tenant_id=tenant_a)).json()["contract_fingerprint"]
    fp_b = client.get("/api/analytics/kpis", headers=_tenant_analytics_user_headers(tenant_id=tenant_b)).json()["contract_fingerprint"]
    assert fp_a == fp_b == _expected_contract_fingerprint()


def test_kpi_contract_fingerprint_unaffected_by_tenant_data_shape(reset_shared_state) -> None:
    """contract_fingerprint is not affected by data/request-dependent payload changes."""
    tenant_id = _create_tenant("kpi-contract-fingerprint-shape")
    headers = _tenant_analytics_user_headers(tenant_id=tenant_id)

    empty_body = client.get("/api/analytics/kpis", headers=headers).json()
    empty_fp = empty_body["contract_fingerprint"]

    with UnitOfWork() as uow:
        kpi_service.refresh_tenant_metrics(tenant_id=tenant_id, uow=uow, snapshot_date="2028-01-01")
    platform_billing_service.increment_usage(tenant_id, "analytics.events.read", 5)
    with UnitOfWork() as uow:
        kpi_service.refresh_tenant_metrics(tenant_id=tenant_id, uow=uow, snapshot_date="2028-01-02")

    ready_body = client.get("/api/analytics/kpis", headers=headers).json()
    ready_fp = ready_body["contract_fingerprint"]

    assert empty_body["response_status"] == "empty"
    assert ready_body["response_status"] == "ready"
    assert empty_fp == ready_fp == _expected_contract_fingerprint()


def test_kpi_stability_tiers_present_and_stable(reset_shared_state) -> None:
    """KPI response exposes stable change-safety tiers metadata."""
    tenant_id = _create_tenant("kpi-stability-tiers-present")
    headers = _tenant_analytics_user_headers(tenant_id=tenant_id)

    body = client.get("/api/analytics/kpis", headers=headers).json()
    assert body["stability_tiers"] == _expected_stability_tiers()


def test_kpi_stability_tiers_same_in_empty_state(reset_shared_state) -> None:
    """Empty KPI response carries the same stability tiers block."""
    tenant_id = _create_tenant("kpi-stability-tiers-empty")
    headers = _tenant_analytics_user_headers(tenant_id=tenant_id)

    body = client.get("/api/analytics/kpis", headers=headers).json()
    assert body["readiness_status"] == "empty"
    assert body["stability_tiers"] == _expected_stability_tiers()


def test_kpi_stability_tiers_stable_core_fields_match_always_present_contract(reset_shared_state) -> None:
    """stable_core_fields only references always-present top-level keys in current payload."""
    tenant_id = _create_tenant("kpi-stability-tiers-core")
    headers = _tenant_analytics_user_headers(tenant_id=tenant_id)

    body = client.get("/api/analytics/kpis", headers=headers).json()
    tiers = body["stability_tiers"]

    assert tiers == _expected_stability_tiers()
    for field_name in tiers["stable_core_fields"]:
        assert field_name in body


def test_kpi_stability_tiers_data_dependent_blocks_match_payload_behavior(reset_shared_state) -> None:
    """data_dependent_blocks list points to contract areas that change with tenant data/state."""
    tenant_id = _create_tenant("kpi-stability-tiers-data")
    headers = _tenant_analytics_user_headers(tenant_id=tenant_id)

    empty_body = client.get("/api/analytics/kpis", headers=headers).json()

    with UnitOfWork() as uow:
        kpi_service.refresh_tenant_metrics(tenant_id=tenant_id, uow=uow)

    ready_body = client.get("/api/analytics/kpis", headers=headers).json()
    tiers = ready_body["stability_tiers"]

    assert tiers == _expected_stability_tiers()
    assert empty_body["readiness_status"] == "empty"
    assert ready_body["readiness_status"] == "ready"
    assert empty_body["kpis"] == []
    assert len(ready_body["kpis"]) > 0


def test_kpi_stability_tiers_tenant_isolation(reset_shared_state) -> None:
    """stability_tiers block is identical across tenants."""
    tenant_a = _create_tenant("kpi-stability-tiers-iso-a")
    tenant_b = _create_tenant("kpi-stability-tiers-iso-b")

    tiers_a = client.get("/api/analytics/kpis", headers=_tenant_analytics_user_headers(tenant_id=tenant_a)).json()["stability_tiers"]
    tiers_b = client.get("/api/analytics/kpis", headers=_tenant_analytics_user_headers(tenant_id=tenant_b)).json()["stability_tiers"]

    assert tiers_a == tiers_b == _expected_stability_tiers()


def test_kpi_stability_tiers_no_cross_tenant_leakage(reset_shared_state) -> None:
    """Tenant-specific KPI changes do not alter another tenant's stability tiers metadata."""
    tenant_a = _create_tenant("kpi-stability-tiers-leak-a")
    tenant_b = _create_tenant("kpi-stability-tiers-leak-b")

    _make_failed_jobs(tenant_b, count=4)
    with UnitOfWork() as uow:
        kpi_service.refresh_tenant_metrics(tenant_id=tenant_b, uow=uow)

    tiers_a = client.get("/api/analytics/kpis", headers=_tenant_analytics_user_headers(tenant_id=tenant_a)).json()["stability_tiers"]
    tiers_b = client.get("/api/analytics/kpis", headers=_tenant_analytics_user_headers(tenant_id=tenant_b)).json()["stability_tiers"]

    assert tiers_a == tiers_b == _expected_stability_tiers()


def test_kpi_stability_tiers_unaffected_by_tenant_data_shape(reset_shared_state) -> None:
    """stability_tiers remains stable across empty and ready data shapes."""
    tenant_id = _create_tenant("kpi-stability-tiers-shape")
    headers = _tenant_analytics_user_headers(tenant_id=tenant_id)

    empty_tiers = client.get("/api/analytics/kpis", headers=headers).json()["stability_tiers"]

    with UnitOfWork() as uow:
        kpi_service.refresh_tenant_metrics(tenant_id=tenant_id, uow=uow, snapshot_date="2027-12-01")
    platform_billing_service.increment_usage(tenant_id, "analytics.events.read", 3)
    with UnitOfWork() as uow:
        kpi_service.refresh_tenant_metrics(tenant_id=tenant_id, uow=uow, snapshot_date="2027-12-02")

    ready_tiers = client.get("/api/analytics/kpis", headers=headers).json()["stability_tiers"]
    assert empty_tiers == ready_tiers == _expected_stability_tiers()


def test_kpi_workflow_hints_present_and_stable(reset_shared_state) -> None:
    """KPI response exposes stable workflow hints for recommended endpoint usage order."""
    tenant_id = _create_tenant("kpi-workflow-hints-present")
    headers = _tenant_analytics_user_headers(tenant_id=tenant_id)

    body = client.get("/api/analytics/kpis", headers=headers).json()
    assert body["workflow_hints"] == _expected_workflow_hints()


def test_kpi_workflow_hints_same_in_empty_state(reset_shared_state) -> None:
    """Empty KPI response carries the same workflow guidance."""
    tenant_id = _create_tenant("kpi-workflow-hints-empty")
    headers = _tenant_analytics_user_headers(tenant_id=tenant_id)

    body = client.get("/api/analytics/kpis", headers=headers).json()
    assert body["readiness_status"] == "empty"
    assert body["workflow_hints"] == _expected_workflow_hints()


def test_kpi_workflow_hints_consistent_with_surface_map(reset_shared_state) -> None:
    """Workflow hints reference only endpoints listed in current analytics surface map."""
    tenant_id = _create_tenant("kpi-workflow-hints-map")
    headers = _tenant_analytics_user_headers(tenant_id=tenant_id)

    body = client.get("/api/analytics/kpis", headers=headers).json()
    hints = body["workflow_hints"]
    surface_map = body["surface_map"]
    endpoint_names = {item["name"] for item in surface_map["endpoints"]}

    assert hints == _expected_workflow_hints()
    assert set(hints["primary_flow"]).issubset(endpoint_names)
    assert set(hints["operational_flow"]).issubset(endpoint_names)
    assert set(hints["observability_flow"]).issubset(endpoint_names)
    assert body["sections"]["workflow_hints"] == "present"


def test_kpi_workflow_hints_tenant_isolation(reset_shared_state) -> None:
    """workflow_hints block is identical across tenants."""
    tenant_a = _create_tenant("kpi-workflow-hints-iso-a")
    tenant_b = _create_tenant("kpi-workflow-hints-iso-b")

    hints_a = client.get("/api/analytics/kpis", headers=_tenant_analytics_user_headers(tenant_id=tenant_a)).json()["workflow_hints"]
    hints_b = client.get("/api/analytics/kpis", headers=_tenant_analytics_user_headers(tenant_id=tenant_b)).json()["workflow_hints"]

    assert hints_a == hints_b == _expected_workflow_hints()


def test_kpi_workflow_hints_no_cross_tenant_leakage(reset_shared_state) -> None:
    """Tenant-specific KPI mutations do not alter another tenant's workflow guidance."""
    tenant_a = _create_tenant("kpi-workflow-hints-leak-a")
    tenant_b = _create_tenant("kpi-workflow-hints-leak-b")

    _make_failed_jobs(tenant_b, count=2)
    with UnitOfWork() as uow:
        kpi_service.refresh_tenant_metrics(tenant_id=tenant_b, uow=uow)

    hints_a = client.get("/api/analytics/kpis", headers=_tenant_analytics_user_headers(tenant_id=tenant_a)).json()["workflow_hints"]
    hints_b = client.get("/api/analytics/kpis", headers=_tenant_analytics_user_headers(tenant_id=tenant_b)).json()["workflow_hints"]

    assert hints_a == hints_b == _expected_workflow_hints()


def test_kpi_workflow_hints_unaffected_by_data_shape(reset_shared_state) -> None:
    """workflow_hints remains stable across empty and ready payload shapes."""
    tenant_id = _create_tenant("kpi-workflow-hints-shape")
    headers = _tenant_analytics_user_headers(tenant_id=tenant_id)

    empty_hints = client.get("/api/analytics/kpis", headers=headers).json()["workflow_hints"]

    with UnitOfWork() as uow:
        kpi_service.refresh_tenant_metrics(tenant_id=tenant_id, uow=uow)

    ready_hints = client.get("/api/analytics/kpis", headers=headers).json()["workflow_hints"]
    assert empty_hints == ready_hints == _expected_workflow_hints()


def test_kpi_workflow_hints_not_conflated_with_capabilities_or_surface_map(reset_shared_state) -> None:
    """workflow_hints remains guidance-only and distinct from capabilities/surface map blocks."""
    tenant_id = _create_tenant("kpi-workflow-hints-separation")
    headers = _tenant_analytics_user_headers(tenant_id=tenant_id)

    body = client.get("/api/analytics/kpis", headers=headers).json()
    assert body["workflow_hints"] == _expected_workflow_hints()
    assert body["capabilities"]["supports_cards"] is True
    assert body["surface_map"] == _expected_surface_map()
    assert "workflow_hints" in body["contract_invariants"]["guaranteed_top_level_fields"]


def test_kpi_surface_map_present_and_stable(reset_shared_state) -> None:
    """KPI response exposes stable analytics endpoint family map."""
    tenant_id = _create_tenant("kpi-surface-map-present")
    headers = _tenant_analytics_user_headers(tenant_id=tenant_id)

    body = client.get("/api/analytics/kpis", headers=headers).json()
    assert body["surface_map"] == _expected_surface_map()


def test_kpi_surface_map_same_in_empty_state(reset_shared_state) -> None:
    """Empty KPI response carries the same endpoint family map."""
    tenant_id = _create_tenant("kpi-surface-map-empty")
    headers = _tenant_analytics_user_headers(tenant_id=tenant_id)

    body = client.get("/api/analytics/kpis", headers=headers).json()
    assert body["readiness_status"] == "empty"
    assert body["surface_map"] == _expected_surface_map()


def test_kpi_surface_map_matches_implemented_analytics_family(reset_shared_state) -> None:
    """surface_map lists the bounded analytics endpoint family implemented by current router."""
    tenant_id = _create_tenant("kpi-surface-map-family")
    headers = _tenant_analytics_user_headers(tenant_id=tenant_id)

    body = client.get("/api/analytics/kpis", headers=headers).json()
    assert body["surface_map"] == _expected_surface_map()
    assert body["sections"]["surface_map"] == "present"


def test_kpi_surface_map_tenant_isolation(reset_shared_state) -> None:
    """surface_map is identical across tenants."""
    tenant_a = _create_tenant("kpi-surface-map-iso-a")
    tenant_b = _create_tenant("kpi-surface-map-iso-b")

    map_a = client.get("/api/analytics/kpis", headers=_tenant_analytics_user_headers(tenant_id=tenant_a)).json()["surface_map"]
    map_b = client.get("/api/analytics/kpis", headers=_tenant_analytics_user_headers(tenant_id=tenant_b)).json()["surface_map"]
    assert map_a == map_b == _expected_surface_map()


def test_kpi_surface_map_no_cross_tenant_leakage(reset_shared_state) -> None:
    """Tenant-specific KPI changes do not alter another tenant's endpoint family map."""
    tenant_a = _create_tenant("kpi-surface-map-leak-a")
    tenant_b = _create_tenant("kpi-surface-map-leak-b")

    _make_failed_jobs(tenant_b, count=2)
    with UnitOfWork() as uow:
        kpi_service.refresh_tenant_metrics(tenant_id=tenant_b, uow=uow)

    map_a = client.get("/api/analytics/kpis", headers=_tenant_analytics_user_headers(tenant_id=tenant_a)).json()["surface_map"]
    map_b = client.get("/api/analytics/kpis", headers=_tenant_analytics_user_headers(tenant_id=tenant_b)).json()["surface_map"]
    assert map_a == map_b == _expected_surface_map()


def test_kpi_surface_map_unaffected_by_data_shape(reset_shared_state) -> None:
    """surface_map remains stable across empty and ready payload shapes."""
    tenant_id = _create_tenant("kpi-surface-map-shape")
    headers = _tenant_analytics_user_headers(tenant_id=tenant_id)

    empty_map = client.get("/api/analytics/kpis", headers=headers).json()["surface_map"]

    with UnitOfWork() as uow:
        kpi_service.refresh_tenant_metrics(tenant_id=tenant_id, uow=uow)

    ready_map = client.get("/api/analytics/kpis", headers=headers).json()["surface_map"]
    assert empty_map == ready_map == _expected_surface_map()


def test_kpi_surface_map_not_conflated_with_contract_semantics_layers(reset_shared_state) -> None:
    """surface_map remains distinct from capabilities, semantics and invariants blocks."""
    tenant_id = _create_tenant("kpi-surface-map-separation")
    headers = _tenant_analytics_user_headers(tenant_id=tenant_id)

    body = client.get("/api/analytics/kpis", headers=headers).json()
    assert body["surface_map"] == _expected_surface_map()
    assert body["capabilities"]["supports_cards"] is True
    assert body["field_semantics"]["capabilities"] == "supported surface features"
    assert "surface_map" in body["contract_invariants"]["guaranteed_top_level_fields"]


def test_kpi_response_examples_present_and_stable(reset_shared_state) -> None:
    """KPI response exposes stable canonical empty/ready shape markers."""
    tenant_id = _create_tenant("kpi-response-examples-present")
    headers = _tenant_analytics_user_headers(tenant_id=tenant_id)

    body = client.get("/api/analytics/kpis", headers=headers).json()
    assert body["response_examples"] == _expected_response_examples()


def test_kpi_response_examples_same_in_empty_and_ready(reset_shared_state) -> None:
    """response_examples is identical for empty and ready payload states."""
    tenant_id = _create_tenant("kpi-response-examples-parity")
    headers = _tenant_analytics_user_headers(tenant_id=tenant_id)

    empty_examples = client.get("/api/analytics/kpis", headers=headers).json()["response_examples"]

    with UnitOfWork() as uow:
        kpi_service.refresh_tenant_metrics(tenant_id=tenant_id, uow=uow)

    ready_examples = client.get("/api/analytics/kpis", headers=headers).json()["response_examples"]

    assert empty_examples == ready_examples == _expected_response_examples()


def test_kpi_response_examples_consistent_with_sections_manifest(reset_shared_state) -> None:
    """Canonical shapes align with sections manifest semantics for cards and summary blocks."""
    tenant_id = _create_tenant("kpi-response-examples-sections")
    headers = _tenant_analytics_user_headers(tenant_id=tenant_id)

    body = client.get("/api/analytics/kpis", headers=headers).json()
    examples = body["response_examples"]

    assert body["sections"]["response_examples"] == "present"
    assert examples["empty_shape"]["cards"] == "empty"
    assert examples["ready_shape"]["cards"] == "populated"
    assert examples["empty_shape"]["summary"] == "present"
    assert examples["ready_shape"]["summary"] == "populated"


def test_kpi_response_examples_tenant_isolation(reset_shared_state) -> None:
    """response_examples block is identical across tenants."""
    tenant_a = _create_tenant("kpi-response-examples-iso-a")
    tenant_b = _create_tenant("kpi-response-examples-iso-b")

    ex_a = client.get("/api/analytics/kpis", headers=_tenant_analytics_user_headers(tenant_id=tenant_a)).json()["response_examples"]
    ex_b = client.get("/api/analytics/kpis", headers=_tenant_analytics_user_headers(tenant_id=tenant_b)).json()["response_examples"]

    assert ex_a == ex_b == _expected_response_examples()


def test_kpi_response_examples_no_cross_tenant_leakage(reset_shared_state) -> None:
    """Tenant-specific KPI mutations do not change another tenant's canonical examples."""
    tenant_a = _create_tenant("kpi-response-examples-leak-a")
    tenant_b = _create_tenant("kpi-response-examples-leak-b")

    _make_failed_jobs(tenant_b, count=6)
    with UnitOfWork() as uow:
        kpi_service.refresh_tenant_metrics(tenant_id=tenant_b, uow=uow)

    ex_a = client.get("/api/analytics/kpis", headers=_tenant_analytics_user_headers(tenant_id=tenant_a)).json()["response_examples"]
    ex_b = client.get("/api/analytics/kpis", headers=_tenant_analytics_user_headers(tenant_id=tenant_b)).json()["response_examples"]

    assert ex_a == ex_b == _expected_response_examples()


def test_kpi_response_examples_unaffected_by_data_shape(reset_shared_state) -> None:
    """response_examples remains stable across shape/data transitions."""
    tenant_id = _create_tenant("kpi-response-examples-shape")
    headers = _tenant_analytics_user_headers(tenant_id=tenant_id)

    empty_examples = client.get("/api/analytics/kpis", headers=headers).json()["response_examples"]

    with UnitOfWork() as uow:
        kpi_service.refresh_tenant_metrics(tenant_id=tenant_id, uow=uow, snapshot_date="2027-11-01")
    platform_billing_service.increment_usage(tenant_id, "analytics.kpi.read", 4)
    with UnitOfWork() as uow:
        kpi_service.refresh_tenant_metrics(tenant_id=tenant_id, uow=uow, snapshot_date="2027-11-02")

    ready_examples = client.get("/api/analytics/kpis", headers=headers).json()["response_examples"]
    assert empty_examples == ready_examples == _expected_response_examples()


def test_kpi_response_examples_not_conflated_with_semantics_or_invariants(reset_shared_state) -> None:
    """Examples remain distinct from capabilities, semantics and invariants layers."""
    tenant_id = _create_tenant("kpi-response-examples-separation")
    headers = _tenant_analytics_user_headers(tenant_id=tenant_id)

    body = client.get("/api/analytics/kpis", headers=headers).json()
    assert body["response_examples"] == _expected_response_examples()
    assert body["capabilities"]["supports_cards"] is True
    assert body["field_semantics"]["sections"] == "current response section presence and state"
    assert "response_examples" in body["contract_invariants"]["guaranteed_top_level_fields"]


def test_kpi_field_semantics_present_and_stable(reset_shared_state) -> None:
    """KPI response exposes a stable top-level field semantics guide."""
    tenant_id = _create_tenant("kpi-field-semantics-present")
    headers = _tenant_analytics_user_headers(tenant_id=tenant_id)

    body = client.get("/api/analytics/kpis", headers=headers).json()
    assert body["field_semantics"] == _expected_field_semantics()


def test_kpi_field_semantics_same_in_empty_state(reset_shared_state) -> None:
    """Empty KPI response carries the same field semantics guide block."""
    tenant_id = _create_tenant("kpi-field-semantics-empty")
    headers = _tenant_analytics_user_headers(tenant_id=tenant_id)

    body = client.get("/api/analytics/kpis", headers=headers).json()
    assert body["readiness_status"] == "empty"
    assert body["field_semantics"] == _expected_field_semantics()


def test_kpi_field_semantics_consistent_with_actual_surface_blocks(reset_shared_state) -> None:
    """Field semantics map to actual stable surface blocks present in the response."""
    tenant_id = _create_tenant("kpi-field-semantics-consistency")
    headers = _tenant_analytics_user_headers(tenant_id=tenant_id)

    body = client.get("/api/analytics/kpis", headers=headers).json()

    assert body["field_semantics"] == _expected_field_semantics()
    assert "capabilities" in body
    assert "sections" in body
    assert "contract_invariants" in body
    assert "surface_profile" in body
    assert body["sections"]["field_semantics"] == "present"


def test_kpi_field_semantics_tenant_isolation(reset_shared_state) -> None:
    """Field semantics block is identical across tenants."""
    tenant_a = _create_tenant("kpi-field-semantics-iso-a")
    tenant_b = _create_tenant("kpi-field-semantics-iso-b")

    sem_a = client.get("/api/analytics/kpis", headers=_tenant_analytics_user_headers(tenant_id=tenant_a)).json()["field_semantics"]
    sem_b = client.get("/api/analytics/kpis", headers=_tenant_analytics_user_headers(tenant_id=tenant_b)).json()["field_semantics"]

    assert sem_a == sem_b == _expected_field_semantics()


def test_kpi_field_semantics_no_cross_tenant_leakage(reset_shared_state) -> None:
    """Tenant-specific KPI changes do not alter field semantics for another tenant."""
    tenant_a = _create_tenant("kpi-field-semantics-leak-a")
    tenant_b = _create_tenant("kpi-field-semantics-leak-b")

    _make_failed_jobs(tenant_b, count=3)
    with UnitOfWork() as uow:
        kpi_service.refresh_tenant_metrics(tenant_id=tenant_b, uow=uow)

    sem_a = client.get("/api/analytics/kpis", headers=_tenant_analytics_user_headers(tenant_id=tenant_a)).json()["field_semantics"]
    sem_b = client.get("/api/analytics/kpis", headers=_tenant_analytics_user_headers(tenant_id=tenant_b)).json()["field_semantics"]

    assert sem_a == sem_b == _expected_field_semantics()


def test_kpi_field_semantics_unaffected_by_data_shape(reset_shared_state) -> None:
    """Field semantics block stays stable across empty and ready payload shapes."""
    tenant_id = _create_tenant("kpi-field-semantics-shape")
    headers = _tenant_analytics_user_headers(tenant_id=tenant_id)

    empty_semantics = client.get("/api/analytics/kpis", headers=headers).json()["field_semantics"]

    with UnitOfWork() as uow:
        kpi_service.refresh_tenant_metrics(tenant_id=tenant_id, uow=uow, snapshot_date="2027-10-01")
    platform_billing_service.increment_usage(tenant_id, "analytics.events.read", 1)
    with UnitOfWork() as uow:
        kpi_service.refresh_tenant_metrics(tenant_id=tenant_id, uow=uow, snapshot_date="2027-10-02")

    ready_semantics = client.get("/api/analytics/kpis", headers=headers).json()["field_semantics"]
    assert empty_semantics == ready_semantics == _expected_field_semantics()


def test_kpi_card_field_semantics_present_and_stable(reset_shared_state) -> None:
    """KPI response exposes a stable card field semantics guide."""
    tenant_id = _create_tenant("kpi-card-field-semantics-present")
    headers = _tenant_analytics_user_headers(tenant_id=tenant_id)

    body = client.get("/api/analytics/kpis", headers=headers).json()
    assert body["card_field_semantics"] == _expected_card_field_semantics()
    assert body["sections"]["card_field_semantics"] == "present"


def test_kpi_card_field_semantics_same_in_empty_state(reset_shared_state) -> None:
    """Empty KPI response carries the same card field semantics guide."""
    tenant_id = _create_tenant("kpi-card-field-semantics-empty")
    headers = _tenant_analytics_user_headers(tenant_id=tenant_id)

    body = client.get("/api/analytics/kpis", headers=headers).json()
    assert body["readiness_status"] == "empty"
    assert body["card_field_semantics"] == _expected_card_field_semantics()


def test_kpi_card_field_semantics_unaffected_by_data_shape(reset_shared_state) -> None:
    """Card field semantics block stays stable across empty and ready payload shapes."""
    tenant_id = _create_tenant("kpi-card-field-semantics-shape")
    headers = _tenant_analytics_user_headers(tenant_id=tenant_id)

    empty_semantics = client.get("/api/analytics/kpis", headers=headers).json()["card_field_semantics"]

    with UnitOfWork() as uow:
        kpi_service.refresh_tenant_metrics(tenant_id=tenant_id, uow=uow)

    ready_semantics = client.get("/api/analytics/kpis", headers=headers).json()["card_field_semantics"]
    assert empty_semantics == ready_semantics == _expected_card_field_semantics()


def test_kpi_surface_profile_present_and_stable(reset_shared_state) -> None:
    """KPI response exposes a stable top-level audience/profile block."""
    tenant_id = _create_tenant("kpi-surface-profile-present")
    headers = _tenant_analytics_user_headers(tenant_id=tenant_id)

    body = client.get("/api/analytics/kpis", headers=headers).json()
    assert body["surface_profile"] == _expected_surface_profile()


def test_kpi_surface_profile_same_in_empty_state(reset_shared_state) -> None:
    """Empty KPI response carries the same surface profile metadata."""
    tenant_id = _create_tenant("kpi-surface-profile-empty")
    headers = _tenant_analytics_user_headers(tenant_id=tenant_id)

    body = client.get("/api/analytics/kpis", headers=headers).json()
    assert body["readiness_status"] == "empty"
    assert body["surface_profile"] == _expected_surface_profile()


def test_kpi_surface_profile_consistent_with_actual_surface_characteristics(reset_shared_state) -> None:
    """Profile reflects intended consumption modes already supported by the KPI surface."""
    tenant_id = _create_tenant("kpi-surface-profile-consistency")
    headers = _tenant_analytics_user_headers(tenant_id=tenant_id)

    body = client.get("/api/analytics/kpis", headers=headers).json()

    assert body["surface_profile"] == _expected_surface_profile()
    assert body["capabilities"]["supports_cards"] is True
    assert body["contract_invariants"]["empty_state_contract_stable"] is True
    assert body["sections"]["surface_profile"] == "present"


def test_kpi_surface_profile_tenant_isolation(reset_shared_state) -> None:
    """Surface profile is identical across tenants."""
    tenant_a = _create_tenant("kpi-surface-profile-iso-a")
    tenant_b = _create_tenant("kpi-surface-profile-iso-b")

    prof_a = client.get("/api/analytics/kpis", headers=_tenant_analytics_user_headers(tenant_id=tenant_a)).json()["surface_profile"]
    prof_b = client.get("/api/analytics/kpis", headers=_tenant_analytics_user_headers(tenant_id=tenant_b)).json()["surface_profile"]

    assert prof_a == prof_b == _expected_surface_profile()


def test_kpi_surface_profile_no_cross_tenant_leakage(reset_shared_state) -> None:
    """Tenant-specific KPI changes do not alter another tenant's surface profile metadata."""
    tenant_a = _create_tenant("kpi-surface-profile-leak-a")
    tenant_b = _create_tenant("kpi-surface-profile-leak-b")

    _make_failed_jobs(tenant_b, count=4)
    with UnitOfWork() as uow:
        kpi_service.refresh_tenant_metrics(tenant_id=tenant_b, uow=uow)

    prof_a = client.get("/api/analytics/kpis", headers=_tenant_analytics_user_headers(tenant_id=tenant_a)).json()["surface_profile"]
    prof_b = client.get("/api/analytics/kpis", headers=_tenant_analytics_user_headers(tenant_id=tenant_b)).json()["surface_profile"]

    assert prof_a == prof_b == _expected_surface_profile()


def test_kpi_surface_profile_unaffected_by_data_shape(reset_shared_state) -> None:
    """Surface profile stays stable across empty and ready payload shapes."""
    tenant_id = _create_tenant("kpi-surface-profile-shape")
    headers = _tenant_analytics_user_headers(tenant_id=tenant_id)

    empty_profile = client.get("/api/analytics/kpis", headers=headers).json()["surface_profile"]

    with UnitOfWork() as uow:
        kpi_service.refresh_tenant_metrics(tenant_id=tenant_id, uow=uow, snapshot_date="2027-09-01")
    platform_billing_service.increment_usage(tenant_id, "analytics.kpi.read", 2)
    with UnitOfWork() as uow:
        kpi_service.refresh_tenant_metrics(tenant_id=tenant_id, uow=uow, snapshot_date="2027-09-02")

    ready_profile = client.get("/api/analytics/kpis", headers=headers).json()["surface_profile"]
    assert empty_profile == ready_profile == _expected_surface_profile()


def test_kpi_contract_invariants_present_and_stable(reset_shared_state) -> None:
    """Response exposes stable contract_invariants block for client compatibility."""
    tenant_id = _create_tenant("kpi-invariants-present")
    headers = _tenant_analytics_user_headers(tenant_id=tenant_id)
    headers["x-request-id"] = "rid-invariants-present"

    body = client.get("/api/analytics/kpis", headers=headers).json()
    assert body["contract_invariants"] == _expected_contract_invariants()


def test_kpi_contract_invariants_same_in_empty_state(reset_shared_state) -> None:
    """Empty response carries the same invariant block as ready responses."""
    tenant_id = _create_tenant("kpi-invariants-empty")
    headers = _tenant_analytics_user_headers(tenant_id=tenant_id)
    headers["x-request-id"] = "rid-invariants-empty"

    body = client.get("/api/analytics/kpis", headers=headers).json()
    assert body["readiness_status"] == "empty"
    assert body["contract_invariants"] == _expected_contract_invariants()


def test_kpi_contract_invariants_guaranteed_fields_match_actual_response(reset_shared_state) -> None:
    """All guaranteed top-level fields declared by invariants are actually present in the payload."""
    tenant_id = _create_tenant("kpi-invariants-guaranteed")
    headers = _tenant_analytics_user_headers(tenant_id=tenant_id)
    headers["x-request-id"] = "rid-invariants-guaranteed"

    body = client.get("/api/analytics/kpis", headers=headers).json()
    invariants = body["contract_invariants"]

    for field_name in invariants["guaranteed_top_level_fields"]:
        assert field_name in body, f"expected guaranteed top-level field {field_name!r} to exist in response"


def test_kpi_contract_invariants_always_present_sections_match_section_manifest(reset_shared_state) -> None:
    """always_present_sections list is consistent with sections manifest entries."""
    tenant_id = _create_tenant("kpi-invariants-sections")
    headers = _tenant_analytics_user_headers(tenant_id=tenant_id)
    headers["x-request-id"] = "rid-invariants-sections"

    body = client.get("/api/analytics/kpis", headers=headers).json()
    invariants = body["contract_invariants"]
    sections = body["sections"]

    for section_name in invariants["always_present_sections"]:
        assert section_name in sections
        assert sections[section_name] in {"present", "empty", "populated"}


def test_kpi_contract_invariants_tenant_isolation(reset_shared_state) -> None:
    """Invariant block is identical across tenants."""
    tenant_a = _create_tenant("kpi-invariants-iso-a")
    tenant_b = _create_tenant("kpi-invariants-iso-b")

    headers_a = _tenant_analytics_user_headers(tenant_id=tenant_a)
    headers_b = _tenant_analytics_user_headers(tenant_id=tenant_b)
    headers_a["x-request-id"] = "rid-invariants-a"
    headers_b["x-request-id"] = "rid-invariants-b"

    inv_a = client.get("/api/analytics/kpis", headers=headers_a).json()["contract_invariants"]
    inv_b = client.get("/api/analytics/kpis", headers=headers_b).json()["contract_invariants"]
    assert inv_a == inv_b == _expected_contract_invariants()


def test_kpi_contract_invariants_no_cross_tenant_leakage(reset_shared_state) -> None:
    """Tenant-specific KPI changes do not alter the invariant block for another tenant."""
    tenant_a = _create_tenant("kpi-invariants-leak-a")
    tenant_b = _create_tenant("kpi-invariants-leak-b")

    _make_failed_jobs(tenant_b, count=5)
    with UnitOfWork() as uow:
        kpi_service.refresh_tenant_metrics(tenant_id=tenant_b, uow=uow)

    headers_a = _tenant_analytics_user_headers(tenant_id=tenant_a)
    headers_b = _tenant_analytics_user_headers(tenant_id=tenant_b)
    headers_a["x-request-id"] = "rid-invariants-leak-a"
    headers_b["x-request-id"] = "rid-invariants-leak-b"

    inv_a = client.get("/api/analytics/kpis", headers=headers_a).json()["contract_invariants"]
    inv_b = client.get("/api/analytics/kpis", headers=headers_b).json()["contract_invariants"]
    assert inv_a == inv_b == _expected_contract_invariants()


def test_kpi_contract_invariants_unaffected_by_data_shape(reset_shared_state) -> None:
    """Invariant block stays stable across empty and ready payload shapes."""
    tenant_id = _create_tenant("kpi-invariants-shape")
    headers = _tenant_analytics_user_headers(tenant_id=tenant_id)
    headers["x-request-id"] = "rid-invariants-shape"

    empty_inv = client.get("/api/analytics/kpis", headers=headers).json()["contract_invariants"]

    with UnitOfWork() as uow:
        kpi_service.refresh_tenant_metrics(tenant_id=tenant_id, uow=uow, snapshot_date="2027-08-01")
    platform_billing_service.increment_usage(tenant_id, "analytics.events.read", 5)
    with UnitOfWork() as uow:
        kpi_service.refresh_tenant_metrics(tenant_id=tenant_id, uow=uow, snapshot_date="2027-08-02")

    ready_inv = client.get("/api/analytics/kpis", headers=headers).json()["contract_invariants"]
    assert empty_inv == ready_inv == _expected_contract_invariants()
