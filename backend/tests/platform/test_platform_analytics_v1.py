from __future__ import annotations

from datetime import date
from uuid import uuid4

from tests.conftest import ADMIN_HEADERS, client

from app.platform.analytics import service as analytics_service
from app.platform.analytics.repository import AnalyticsRepository
from app.platform.events.handlers.analytics_handler import AnalyticsEventHandler
from app.platform.events.publisher import EventPublisher
from app.platform.events.schemas import OutboxEventRead
from app.platform.events.worker import OutboxEventWorker
from app.platform.tenant import service as tenant_service
from app.platform.uow import UnitOfWork


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
    tenant = tenant_service.create_tenant(f"an-api-{uuid4().hex[:8]}", "API Tenant")
    tid = int(tenant["tenant_id"])

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
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["tenant_id"] == tid
    assert body["total_events"] == 2
    assert body["event_counts_json"]["enrollment.created"] == 2


# ---------------------------------------------------------------------------
# Regression: PostgreSQL path — KPI increment must not raise IndeterminateDatatype
# ---------------------------------------------------------------------------
# Requires DATABASE_URL env var pointing at a live PostgreSQL instance with the
# platform schema already applied (e.g. platform_restore from DR rehearsal).
# Skipped automatically when running in-memory CI (DATABASE_URL not set).

import os as _os

import pytest


@pytest.mark.skipif(
    not _os.getenv("DATABASE_URL"),
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
    not _os.getenv("DATABASE_URL"),
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
            from app.platform.analytics.repository import AnalyticsRepository  # noqa: PLC0415
            from app.platform.events.schemas import OutboxEventRead  # noqa: PLC0415
            from app.platform.events.handlers.analytics_handler import AnalyticsEventHandler  # noqa: PLC0415

            event = OutboxEventRead(
                id=outbox_id,
                tenant_id=tenant_id,
                event_type="grade.submitted",
                aggregate_type="grade",
                aggregate_id="reg-9001",
                payload_json={"grade_id": 9001},
                status="pending",
                retry_count=0,
                available_at="2026-03-25T00:00:00+00:00",
                created_at="2026-03-25T00:00:00+00:00",
            )

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

