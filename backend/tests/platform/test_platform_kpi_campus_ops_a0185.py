from __future__ import annotations

from uuid import uuid4

from app.modules.tenants import service as module_tenant_service
from app.platform.event_ingestion import service as event_ingestion_service
from app.platform.kpi import service as kpi_service
from app.platform.uow import UnitOfWork


def _emit_many(*, tenant_id: int, event_type: str, count: int, base_id: int) -> None:
    for index in range(count):
        event_ingestion_service.record_event(
            tenant_id=tenant_id,
            event_type=event_type,
            payload={"id": base_id + index, "source": "test-a0185"},
        )


def _create_tenant(prefix: str) -> int:
    slug = f"{prefix}-{uuid4().hex[:8]}"
    tenant = module_tenant_service.create_tenant({"slug": slug, "name": f"{prefix} Tenant"})
    return int(tenant["id"])


def test_refresh_tenant_metrics_derives_campus_operations_kpis(reset_shared_state) -> None:
    tenant_id = _create_tenant("kpi-campus-ops")

    _emit_many(tenant_id=tenant_id, event_type="scheduling.section.conflict_detected", count=2, base_id=10_000)
    _emit_many(tenant_id=tenant_id, event_type="scheduling.room_conflict.detected", count=3, base_id=11_000)
    _emit_many(tenant_id=tenant_id, event_type="scheduling.room_allocation.required", count=1, base_id=12_000)

    _emit_many(tenant_id=tenant_id, event_type="access.denied", count=5, base_id=13_000)
    _emit_many(tenant_id=tenant_id, event_type="security.anomaly", count=2, base_id=14_000)
    _emit_many(tenant_id=tenant_id, event_type="card.issued", count=7, base_id=15_000)
    _emit_many(tenant_id=tenant_id, event_type="card.reactivated", count=1, base_id=16_000)
    _emit_many(tenant_id=tenant_id, event_type="card.suspended", count=3, base_id=17_000)

    _emit_many(tenant_id=tenant_id, event_type="event.published", count=6, base_id=18_000)
    _emit_many(tenant_id=tenant_id, event_type="event.started", count=4, base_id=19_000)
    _emit_many(tenant_id=tenant_id, event_type="event.completed", count=3, base_id=20_000)
    _emit_many(tenant_id=tenant_id, event_type="event.cancelled", count=1, base_id=21_000)
    _emit_many(tenant_id=tenant_id, event_type="event.registration_full", count=2, base_id=22_000)

    with UnitOfWork() as uow:
        rows = kpi_service.refresh_tenant_metrics(tenant_id=tenant_id, uow=uow)

    values = {str(item["metric_key"]): int(item["metric_value"]) for item in rows}

    assert values["room_conflict_count"] == 4

    assert values["access_denied_count"] == 5
    assert values["unauthorized_attempts_count"] == 7
    assert values["active_access_cards_count"] == 8
    assert values["suspended_access_cards_count"] == 3
    assert values["security_access_anomaly_count"] == 2

    assert values["events_published_count"] == 6
    assert values["events_started_count"] == 4
    assert values["events_completed_count"] == 3
    assert values["events_cancelled_count"] == 1
    assert values["events_registration_full_count"] == 2


def test_campus_operations_metrics_are_marked_as_analytics_sink(reset_shared_state) -> None:
    tenant_id = _create_tenant("kpi-campus-meta")

    _emit_many(tenant_id=tenant_id, event_type="event.published", count=1, base_id=23_000)
    _emit_many(tenant_id=tenant_id, event_type="access.denied", count=1, base_id=24_000)
    _emit_many(tenant_id=tenant_id, event_type="scheduling.room_conflict.detected", count=1, base_id=25_000)

    with UnitOfWork() as uow:
        rows = kpi_service.refresh_tenant_metrics(tenant_id=tenant_id, uow=uow)

    metadata_by_key = {str(item["metric_key"]): dict(item.get("metadata_json") or {}) for item in rows}

    assert metadata_by_key["events_published_count"]["source"] == "analytics_sink_v1"
    assert metadata_by_key["access_denied_count"]["source"] == "analytics_sink_v1"
    assert metadata_by_key["room_conflict_count"]["source"] == "analytics_sink_v1"
