from __future__ import annotations

from uuid import uuid4

import pytest

from app.platform.events.publisher import EventPublisher
from app.platform.events.worker import OutboxEventWorker
from app.platform.repository.db import db_available, db_url
from app.platform.tenant import service as tenant_service
from app.platform.uow import UnitOfWork


def _require_real_postgres() -> None:
    if not db_available() or not db_url():
        pytest.skip("DATABASE_URL is not configured for real PostgreSQL integration test")


def test_tenant_service_create_tenant_publishes_outbox_event() -> None:
    suffix = uuid4().hex[:8]
    tenant = tenant_service.create_tenant(f"evt-{suffix}", f"Tenant {suffix}", actor="pytest")
    tenant_id = int(tenant["tenant_id"])

    with UnitOfWork() as uow:
        events = uow.outbox_event_repository.list_for_tenant(tenant_id, conn=uow.conn)

    matching = [item for item in events if str(item["event_type"]) == "tenant.created"]
    assert matching
    assert int(matching[0]["tenant_id"]) == tenant_id
    assert str(matching[0]["aggregate_type"]) == "tenant"
    assert int(matching[0]["payload_json"]["tenant_id"]) == tenant_id


@pytest.mark.integration
def test_outbox_event_rolls_back_with_business_transaction() -> None:
    _require_real_postgres()

    suffix = uuid4().hex[:8]
    tenant_id: int | None = None

    with pytest.raises(RuntimeError, match="forced rollback"):
        with UnitOfWork() as uow:
            tenant = uow.tenant_repository.create_tenant(f"outbox-rb-{suffix}", f"Rollback {suffix}", conn=uow.conn)
            tenant_id = int(tenant["tenant_id"])
            EventPublisher(uow=uow).publish_event(
                tenant_id=tenant_id,
                event_type="tenant.created",
                aggregate_type="tenant",
                aggregate_id=tenant_id,
                payload_json={"tenant_id": tenant_id, "slug": tenant["slug"]},
            )
            raise RuntimeError("forced rollback")

    assert tenant_id is not None
    with UnitOfWork() as uow:
        tenants = uow.tenant_repository.list_tenant_profiles(conn=uow.conn)
        events = uow.outbox_event_repository.list_for_tenant(tenant_id, conn=uow.conn)

    assert all(int(item["tenant_id"]) != tenant_id for item in tenants)
    assert events == []


def test_outbox_worker_processes_pending_events() -> None:
    suffix = uuid4().hex[:8]
    tenant = tenant_service.create_tenant(f"wrk-{suffix}", f"Worker {suffix}", actor="pytest")
    tenant_id = int(tenant["tenant_id"])

    worker = OutboxEventWorker(retry_delay_seconds=0.0)
    result = worker.run_once()

    assert result["processed"] >= 1
    assert result["succeeded"] >= 1

    with UnitOfWork() as uow:
        events = uow.outbox_event_repository.list_for_tenant(tenant_id, conn=uow.conn)
        notifications = uow.notification_repository.list_for_tenant(tenant_id, conn=uow.conn)

    matching_events = [item for item in events if str(item["event_type"]) == "tenant.created"]
    matching_notifications = [
        item
        for item in notifications
        if str(item["payload"]["event_type"]) == "tenant.created"
    ]
    assert matching_events
    assert str(matching_events[0]["status"]) == "processed"
    assert matching_notifications
    assert int(matching_notifications[0]["tenant_id"]) == tenant_id


def test_outbox_worker_retries_failed_handler() -> None:
    class FlakyHandler:
        name = "flaky"

        def __init__(self) -> None:
            self.calls = 0

        def handle(self, event, *, uow):
            _ = (event, uow)
            self.calls += 1
            if self.calls == 1:
                raise RuntimeError("temporary handler failure")
            return {"status": "processed"}

    suffix = uuid4().hex[:8]
    tenant = tenant_service.create_tenant(f"retry-{suffix}", f"Retry {suffix}", actor="pytest")
    tenant_id = int(tenant["tenant_id"])

    OutboxEventWorker(retry_delay_seconds=0.0).run_once()

    with UnitOfWork() as uow:
        EventPublisher(uow=uow).publish_event(
            tenant_id=tenant_id,
            event_type="student.created",
            aggregate_type="student_profile",
            aggregate_id="1001",
            payload_json={"student_profile_id": 1001},
        )

    handler = FlakyHandler()
    worker = OutboxEventWorker(handlers=[handler], retry_delay_seconds=0.0, max_retry_count=3)

    first = worker.run_once()
    assert first["retried"] == 1

    second = worker.run_once()
    assert second["succeeded"] == 1

    with UnitOfWork() as uow:
        events = uow.outbox_event_repository.list_for_tenant(tenant_id, conn=uow.conn)

    matching = [
        item
        for item in events
        if str(item["event_type"]) == "student.created" and str(item["aggregate_id"]) == "1001"
    ]
    assert matching
    assert str(matching[0]["status"]) == "processed"
    assert int(matching[0]["retry_count"]) == 1


def test_outbox_repository_preserves_tenant_isolation() -> None:
    first = tenant_service.create_tenant(f"iso-a-{uuid4().hex[:8]}", "Isolation A", actor="pytest")
    second = tenant_service.create_tenant(f"iso-b-{uuid4().hex[:8]}", "Isolation B", actor="pytest")
    first_tenant_id = int(first["tenant_id"])
    second_tenant_id = int(second["tenant_id"])

    OutboxEventWorker(retry_delay_seconds=0.0).run_once()

    with UnitOfWork() as uow:
        EventPublisher(uow=uow).publish_event(
            tenant_id=first_tenant_id,
            event_type="tenant.created",
            aggregate_type="tenant",
            aggregate_id=str(first_tenant_id),
            payload_json={"tenant_id": first_tenant_id},
        )
        EventPublisher(uow=uow).publish_event(
            tenant_id=second_tenant_id,
            event_type="tenant.created",
            aggregate_type="tenant",
            aggregate_id=str(second_tenant_id),
            payload_json={"tenant_id": second_tenant_id},
        )

    with UnitOfWork() as uow:
        tenant_101 = uow.outbox_event_repository.list_for_tenant(first_tenant_id, conn=uow.conn)
        tenant_202 = uow.outbox_event_repository.list_for_tenant(second_tenant_id, conn=uow.conn)

    assert tenant_101
    assert tenant_202
    assert all(int(item["tenant_id"]) == first_tenant_id for item in tenant_101)
    assert all(int(item["tenant_id"]) == second_tenant_id for item in tenant_202)