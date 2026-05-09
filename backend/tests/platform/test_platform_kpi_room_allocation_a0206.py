from __future__ import annotations

from uuid import uuid4

from app.modules.tenants import service as module_tenant_service
from app.platform.event_ingestion import service as event_ingestion_service
from app.platform.event_ingestion.types import VALID_EVENT_TYPES
from app.platform.events.registry import EXACT_EVENT_REGISTRY
from app.platform.kpi import service as kpi_service
from app.platform.uow import UnitOfWork


A0206_METRICS = {
    "room_allocation_recommendations_count",
    "room_allocation_review_required_count",
    "room_allocation_no_viable_candidate_count",
    "room_allocation_candidate_evaluated_count",
    "room_capacity_mismatch_count",
    "room_equipment_mismatch_count",
    "room_computer_shortage_count",
    "room_type_mismatch_count",
    "scheduling_conflicts_count",
    "room_conflict_count",
    "capacity_risk_sections_count",
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
            payload={"id": base_id + idx, "source": "test-a0206"},
        )


def test_a0206_metric_titles_exist() -> None:
    for metric in A0206_METRICS:
        assert metric in kpi_service.METRIC_TITLES
        assert isinstance(kpi_service.METRIC_TITLES[metric], str)
        assert kpi_service.METRIC_TITLES[metric].strip()


def test_a0206_metric_lineage_exists() -> None:
    for metric in A0206_METRICS:
        assert metric in kpi_service.EVENT_DERIVED_METRIC_LINEAGE
        lineage = kpi_service.EVENT_DERIVED_METRIC_LINEAGE[metric]
        assert isinstance(lineage, list)
        assert len(lineage) > 0


def test_a0206_recommendation_metric_maps_to_recommendation_generated() -> None:
    lineage = kpi_service.EVENT_DERIVED_METRIC_LINEAGE["room_allocation_recommendations_count"]
    assert "scheduling.room_allocation.recommendation_generated" in lineage


def test_a0206_review_required_metric_maps_to_review_required() -> None:
    lineage = kpi_service.EVENT_DERIVED_METRIC_LINEAGE["room_allocation_review_required_count"]
    assert "scheduling.room_allocation.review_required" in lineage


def test_a0206_no_viable_metric_maps_to_no_viable_candidate() -> None:
    lineage = kpi_service.EVENT_DERIVED_METRIC_LINEAGE["room_allocation_no_viable_candidate_count"]
    assert "scheduling.room_allocation.no_viable_candidate" in lineage


def test_a0206_candidate_evaluated_metric_maps_to_candidate_ranked() -> None:
    lineage = kpi_service.EVENT_DERIVED_METRIC_LINEAGE["room_allocation_candidate_evaluated_count"]
    assert "scheduling.room_allocation.candidate_ranked" in lineage


def test_a0206_events_registered_for_ingestion_and_exact_registry() -> None:
    required_events = {
        "scheduling.room_allocation.recommendation_generated",
        "scheduling.room_allocation.review_required",
        "scheduling.room_allocation.no_viable_candidate",
        "scheduling.room_allocation.candidate_ranked",
        "scheduling.equipment_mismatch.detected",
        "scheduling.room_type_mismatch.detected",
        "scheduling.computer_shortage.detected",
        "scheduling.capacity_mismatch.detected",
    }
    for event_type in required_events:
        assert event_type in VALID_EVENT_TYPES
        assert event_type in EXACT_EVENT_REGISTRY


def test_a0206_refresh_metrics_counts_are_deterministic(reset_shared_state) -> None:
    tenant_id = _create_tenant("kpi-a0206")

    _emit_many(tenant_id=tenant_id, event_type="scheduling.room_allocation.recommendation_generated", count=2, base_id=1_000)
    _emit_many(tenant_id=tenant_id, event_type="scheduling.room_allocation.review_required", count=3, base_id=2_000)
    _emit_many(tenant_id=tenant_id, event_type="scheduling.room_allocation.no_viable_candidate", count=1, base_id=3_000)
    _emit_many(tenant_id=tenant_id, event_type="scheduling.room_allocation.candidate_ranked", count=5, base_id=4_000)
    _emit_many(tenant_id=tenant_id, event_type="scheduling.capacity_mismatch.detected", count=4, base_id=5_000)
    _emit_many(tenant_id=tenant_id, event_type="scheduling.equipment_mismatch.detected", count=6, base_id=6_000)
    _emit_many(tenant_id=tenant_id, event_type="scheduling.computer_shortage.detected", count=7, base_id=7_000)
    _emit_many(tenant_id=tenant_id, event_type="scheduling.room_type_mismatch.detected", count=8, base_id=8_000)
    _emit_many(tenant_id=tenant_id, event_type="scheduling.section.conflict_detected", count=2, base_id=9_000)
    _emit_many(tenant_id=tenant_id, event_type="scheduling.room_conflict.detected", count=1, base_id=10_000)
    _emit_many(tenant_id=tenant_id, event_type="scheduling.room_allocation.required", count=4, base_id=11_000)
    _emit_many(tenant_id=tenant_id, event_type="enrollment.capacity_risk.detected", count=3, base_id=12_000)

    with UnitOfWork() as uow:
        rows = kpi_service.refresh_tenant_metrics(tenant_id=tenant_id, uow=uow)

    values = {str(item["metric_key"]): int(item["metric_value"]) for item in rows}

    assert values["room_allocation_recommendations_count"] == 2
    assert values["room_allocation_review_required_count"] == 3
    assert values["room_allocation_no_viable_candidate_count"] == 1
    assert values["room_allocation_candidate_evaluated_count"] == 5
    assert values["room_capacity_mismatch_count"] == 4
    assert values["room_equipment_mismatch_count"] == 6
    assert values["room_computer_shortage_count"] == 7
    assert values["room_type_mismatch_count"] == 8
    assert values["scheduling_conflicts_count"] == 2
    assert values["room_conflict_count"] == 5
    assert values["capacity_risk_sections_count"] == 3


def test_a0206_missing_event_counts_default_to_zero(reset_shared_state) -> None:
    tenant_id = _create_tenant("kpi-a0206-empty")

    with UnitOfWork() as uow:
        rows = kpi_service.refresh_tenant_metrics(tenant_id=tenant_id, uow=uow)

    values = {str(item["metric_key"]): int(item["metric_value"]) for item in rows}
    for metric in A0206_METRICS:
        assert metric in values
        assert values[metric] == 0


def test_a0206_no_duplicate_metric_names() -> None:
    keys = list(kpi_service.METRIC_TITLES.keys())
    assert len(keys) == len(set(keys))


def test_a0206_threshold_policy_consistency_for_added_metrics() -> None:
    # A-020.6 metrics are informational/event-count visibility KPIs by default.
    for metric in A0206_METRICS:
        if metric in kpi_service.KPI_SEVERITY_RULES:
            rule = kpi_service.KPI_SEVERITY_RULES[metric]
            assert rule.get("basis") in {"count", "percentage"}


def test_a0205_event_kpi_wiring_remains_backward_compatible() -> None:
    assert "room_allocation_recommendations_generated_count" in kpi_service.EVENT_DERIVED_METRIC_LINEAGE
    assert "scheduling.room_allocation.recommendation_generated" in kpi_service.EVENT_DERIVED_METRIC_LINEAGE[
        "room_allocation_recommendations_generated_count"
    ]
