from __future__ import annotations

from uuid import uuid4

from app.modules.tenants import service as module_tenant_service
from app.platform.event_ingestion import service as event_ingestion_service
from app.platform.event_ingestion.types import VALID_EVENT_TYPES
from app.platform.events.registry import EXACT_EVENT_REGISTRY
from app.platform.kpi import service as kpi_service
from app.platform.uow import UnitOfWork


A0225_METRICS = {
    "timetable_change_proposals_count",
    "timetable_change_pending_review_count",
    "timetable_change_approved_count",
    "timetable_change_rejected_count",
    "timetable_change_revision_requested_count",
    "timetable_simulations_count",
    "timetable_simulations_review_required_count",
    "timetable_simulation_conflicts_created_count",
    "timetable_simulation_conflicts_resolved_count",
    "timetable_approval_queue_count",
    "timetable_approval_pending_count",
    "timetable_approval_approved_count",
    "timetable_approval_rejected_count",
    "timetable_approval_revision_requested_count",
    "timetable_approval_high_risk_count",
}


def _create_tenant(prefix: str) -> int:
    slug = f"{prefix}-{uuid4().hex[:8]}"
    tenant = module_tenant_service.create_tenant({"slug": slug, "name": f"{prefix} Tenant"})
    return int(tenant["id"])


def _emit_many(*, tenant_id: int, event_type: str, count: int, base_id: int) -> None:
    for idx in range(count):
        event_ingestion_service.record_event(
            tenant_id=tenant_id,
            event_type=event_type,
            payload={"id": base_id + idx, "source": "test-a0225"},
        )


def _refresh_values(tenant_id: int) -> dict[str, int]:
    with UnitOfWork() as uow:
        rows = kpi_service.refresh_tenant_metrics(tenant_id=tenant_id, uow=uow)
    return {str(item["metric_key"]): int(item["metric_value"]) for item in rows}


def test_a0225_metric_titles_exist() -> None:
    for metric in A0225_METRICS:
        assert metric in kpi_service.METRIC_TITLES
        assert isinstance(kpi_service.METRIC_TITLES[metric], str)
        assert kpi_service.METRIC_TITLES[metric].strip()


def test_a0225_metric_lineage_exists() -> None:
    for metric in A0225_METRICS:
        assert metric in kpi_service.EVENT_DERIVED_METRIC_LINEAGE
        lineage = kpi_service.EVENT_DERIVED_METRIC_LINEAGE[metric]
        assert isinstance(lineage, list)
        assert len(lineage) > 0


def test_a0225_events_registered_for_ingestion_and_exact_registry() -> None:
    required_events = {
        "scheduling.timetable_proposal.created",
        "scheduling.timetable_proposal.submitted",
        "scheduling.timetable_proposal.approved",
        "scheduling.timetable_proposal.rejected",
        "scheduling.timetable_proposal.revision_requested",
        "scheduling.timetable_simulation.computed",
        "scheduling.timetable_simulation.review_required",
        "scheduling.timetable_simulation.conflicts_created",
        "scheduling.timetable_simulation.conflicts_resolved",
        "scheduling.timetable_approval.queued",
        "scheduling.timetable_approval.in_review",
        "scheduling.timetable_approval.approved",
        "scheduling.timetable_approval.rejected",
        "scheduling.timetable_approval.revision_requested",
        "scheduling.timetable_approval.high_risk",
    }
    for event_type in required_events:
        assert event_type in VALID_EVENT_TYPES
        assert event_type in EXACT_EVENT_REGISTRY


def test_a0225_refresh_metrics_counts_are_deterministic(reset_shared_state) -> None:
    tenant_id = _create_tenant("kpi-a0225")

    _emit_many(tenant_id=tenant_id, event_type="scheduling.timetable_proposal.created", count=6, base_id=1_000)
    _emit_many(tenant_id=tenant_id, event_type="scheduling.timetable_proposal.submitted", count=4, base_id=2_000)
    _emit_many(tenant_id=tenant_id, event_type="scheduling.timetable_proposal.approved", count=2, base_id=3_000)
    _emit_many(tenant_id=tenant_id, event_type="scheduling.timetable_proposal.rejected", count=1, base_id=4_000)
    _emit_many(
        tenant_id=tenant_id,
        event_type="scheduling.timetable_proposal.revision_requested",
        count=3,
        base_id=5_000,
    )

    _emit_many(tenant_id=tenant_id, event_type="scheduling.timetable_simulation.computed", count=5, base_id=6_000)
    _emit_many(
        tenant_id=tenant_id,
        event_type="scheduling.timetable_simulation.review_required",
        count=2,
        base_id=7_000,
    )
    _emit_many(
        tenant_id=tenant_id,
        event_type="scheduling.timetable_simulation.conflicts_created",
        count=7,
        base_id=8_000,
    )
    _emit_many(
        tenant_id=tenant_id,
        event_type="scheduling.timetable_simulation.conflicts_resolved",
        count=4,
        base_id=9_000,
    )

    _emit_many(tenant_id=tenant_id, event_type="scheduling.timetable_approval.queued", count=8, base_id=10_000)
    _emit_many(tenant_id=tenant_id, event_type="scheduling.timetable_approval.in_review", count=3, base_id=11_000)
    _emit_many(tenant_id=tenant_id, event_type="scheduling.timetable_approval.approved", count=2, base_id=12_000)
    _emit_many(tenant_id=tenant_id, event_type="scheduling.timetable_approval.rejected", count=1, base_id=13_000)
    _emit_many(
        tenant_id=tenant_id,
        event_type="scheduling.timetable_approval.revision_requested",
        count=2,
        base_id=14_000,
    )
    _emit_many(tenant_id=tenant_id, event_type="scheduling.timetable_approval.high_risk", count=1, base_id=15_000)

    values = _refresh_values(tenant_id)

    assert values["timetable_change_proposals_count"] == 6
    assert values["timetable_change_pending_review_count"] == 4
    assert values["timetable_change_approved_count"] == 2
    assert values["timetable_change_rejected_count"] == 1
    assert values["timetable_change_revision_requested_count"] == 3
    assert values["timetable_simulations_count"] == 5
    assert values["timetable_simulations_review_required_count"] == 2
    assert values["timetable_simulation_conflicts_created_count"] == 7
    assert values["timetable_simulation_conflicts_resolved_count"] == 4
    assert values["timetable_approval_queue_count"] == 8
    assert values["timetable_approval_pending_count"] == 11
    assert values["timetable_approval_approved_count"] == 2
    assert values["timetable_approval_rejected_count"] == 1
    assert values["timetable_approval_revision_requested_count"] == 2
    assert values["timetable_approval_high_risk_count"] == 1


def test_a0225_missing_event_counts_default_to_zero(reset_shared_state) -> None:
    tenant_id = _create_tenant("kpi-a0225-empty")
    values = _refresh_values(tenant_id)

    for metric in A0225_METRICS:
        assert metric in values
        assert values[metric] == 0


def test_a0225_metrics_are_tenant_scoped(reset_shared_state) -> None:
    tenant_a = _create_tenant("kpi-a0225-a")
    tenant_b = _create_tenant("kpi-a0225-b")

    _emit_many(tenant_id=tenant_a, event_type="scheduling.timetable_proposal.created", count=2, base_id=20_000)
    _emit_many(tenant_id=tenant_a, event_type="scheduling.timetable_approval.approved", count=1, base_id=21_000)

    _emit_many(tenant_id=tenant_b, event_type="scheduling.timetable_proposal.created", count=9, base_id=30_000)
    _emit_many(tenant_id=tenant_b, event_type="scheduling.timetable_approval.approved", count=5, base_id=31_000)

    values_a = _refresh_values(tenant_a)
    values_b = _refresh_values(tenant_b)

    assert values_a["timetable_change_proposals_count"] == 2
    assert values_a["timetable_approval_approved_count"] == 1
    assert values_b["timetable_change_proposals_count"] == 9
    assert values_b["timetable_approval_approved_count"] == 5


def test_a0225_no_duplicate_metric_names() -> None:
    keys = list(kpi_service.METRIC_TITLES.keys())
    assert len(keys) == len(set(keys))
