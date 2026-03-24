from __future__ import annotations

from uuid import uuid4

from tests.conftest import ADMIN_HEADERS, client

from app.platform.billing import service as billing_service
from app.platform.events.handlers.analytics_handler import AnalyticsEventHandler
from app.platform.events.schemas import OutboxEventRead
from app.platform.jobs import service as jobs_service
from app.platform.jobs.scheduler import PlatformWorkerScheduler
from app.platform.kpi import service as kpi_service
from app.platform.notifications import service as notifications_service
from app.platform.tenant import service as tenant_service
from app.platform.uow import UnitOfWork


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
    tenant = tenant_service.create_tenant(f"{name_prefix}-{uuid4().hex[:8]}", f"{name_prefix} Tenant")
    return int(tenant["tenant_id"])


def test_kpi_metric_snapshot_creation_and_values(reset_shared_state) -> None:
    tenant_id = _create_tenant("kpi-metrics")

    _emit_analytics_event(tenant_id=tenant_id, event_type="student.created", event_id=1001)
    _emit_analytics_event(tenant_id=tenant_id, event_type="student.created", event_id=1002)
    _emit_analytics_event(tenant_id=tenant_id, event_type="enrollment.created", event_id=1003)
    _emit_analytics_event(tenant_id=tenant_id, event_type="grade.submitted", event_id=1004)
    _emit_analytics_event(tenant_id=tenant_id, event_type="grade.submitted", event_id=1005)
    _emit_analytics_event(tenant_id=tenant_id, event_type="grade.submitted", event_id=1006)

    plan_code = f"kpi-plan-{uuid4().hex[:6]}"
    billing_service.create_plan(plan_code, "KPI Plan", 1000, {"analytics": True}, {"users": 1000})
    billing_service.assign_plan(tenant_id, plan_code)

    job = jobs_service.enqueue_job(tenant_id, "grade-sync", {"batch": 1})
    jobs_service.run_job(int(job["id"]), succeed=False, error="simulated failure")

    notification = notifications_service.dispatch_notification(
        tenant_id=tenant_id,
        channel="email",
        target="ops@example.com",
        payload={"subject": "alert"},
        subject="Alert",
    )
    with UnitOfWork() as uow:
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

    single = client.post(f"/api/v1/internal/platform/kpi/refresh/{tenant_id}")
    assert single.status_code == 200, single.text
    one = single.json()
    assert one["tenant_id"] == tenant_id

    bulk = client.post("/api/v1/internal/platform/kpi/refresh")
    assert bulk.status_code == 200, bulk.text
    all_res = bulk.json()
    assert all_res["tenants_total"] >= 1
    assert all_res["refreshed"] >= 1


def test_scheduler_registers_kpi_refresh_task() -> None:
    scheduler = PlatformWorkerScheduler()
    task_names = set(scheduler._tasks.keys())  # noqa: SLF001
    assert "kpi_metrics_refresh" in task_names
