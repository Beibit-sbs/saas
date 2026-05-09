"""A-020.7 — Room Allocation Cross-Feature E2E.

Validation/evidence-only suite proving integrated flow across:
- requirement/readiness
- room capability
- capacity matching brain
- conflict detection
- recommendation ranking
- KPI pipeline

Non-destructive guarantees:
- no room assignment
- no reservation
- no timetable mutation
- no room booking mutation
- no auto-apply
- no fake optimization output
"""

from __future__ import annotations

from uuid import uuid4

import pytest

from app.modules.tenants import service as module_tenant_service
from app.platform.event_ingestion import service as event_ingestion_service
from app.platform.kpi import service as kpi_service
from app.platform.uow import UnitOfWork
from app.modules.scheduling.room_allocation_readiness import (
    CapacityRiskLevel,
    ConflictType,
    RoomAllocationRecommendationStatus,
    RoomAllocationRequirement,
    RoomAllocationSchedule,
    RoomCapability,
    build_capacity_matching_result,
    build_room_allocation_recommendation_result,
    detect_room_requirement_conflicts,
)


def _create_tenant(prefix: str) -> int:
    tenant = module_tenant_service.create_tenant(
        {
            "slug": f"{prefix}-{uuid4().hex[:8]}",
            "name": f"{prefix} Tenant",
        }
    )
    return int(tenant["id"])


def _requirement(**overrides: object) -> RoomAllocationRequirement:
    payload: dict[str, object] = {
        "section_id": 7101,
        "course_id": 7201,
        "group_id": 7301,
        "teacher_id": "prof-room-01",
        "students_count": 38,
        "max_capacity": 45,
        "required_room_type": "computer_lab",
        "required_computers": 20,
        "equipment_required": ["projector", "whiteboard"],
        "restrictions_required": ["exam_enabled"],
    }
    payload.update(overrides)
    return RoomAllocationRequirement(**payload)


def _capability(tenant_id: int, room_id: str, **overrides: object) -> RoomCapability:
    payload: dict[str, object] = {
        "tenant_id": tenant_id,
        "room_id": room_id,
        "room_code": room_id,
        "room_name": room_id,
        "room_type": "computer_lab",
        "capacity": 44,
        "computers_count": 28,
        "equipment_available": ["projector", "whiteboard", "audio"],
        "supported_lesson_types": ["lecture", "lab"],
        "restrictions": ["exam_enabled"],
        "availability_status": "available",
        "booking_status": "released",
        "maintenance_status": "ok",
        "is_active": True,
        "source_entity_type": "campus_room",
        "source_entity_id": f"entity-{room_id}",
    }
    payload.update(overrides)
    return RoomCapability(**payload)


def _emit(tenant_id: int, event_type: str, event_id: int) -> None:
    event_ingestion_service.record_event(
        tenant_id=tenant_id,
        event_type=event_type,
        payload={"id": event_id, "source": "test-a0207"},
    )


def test_requirement_capability_capacity_match_to_recommendation_contract() -> None:
    tenant_id = _create_tenant("a0207-flow1")
    requirement = _requirement()
    candidate_a = _capability(tenant_id, "LAB-01", capacity=50, computers_count=32)
    candidate_b = _capability(tenant_id, "LAB-02", capacity=38, computers_count=20)

    before_a = candidate_a.model_dump()
    before_b = candidate_b.model_dump()

    recommendation = build_room_allocation_recommendation_result(
        tenant_id,
        requirement,
        [candidate_b, candidate_a],
    )

    assert recommendation.has_viable_candidate is True
    assert recommendation.best_candidate_id == "LAB-02"
    assert recommendation.candidates[0].capacity_match.match_score >= recommendation.candidates[1].capacity_match.match_score

    best_match = recommendation.candidates[0].capacity_match
    assert 0 <= best_match.match_score <= 100
    assert best_match.risk_level in {
        CapacityRiskLevel.LOW,
        CapacityRiskLevel.MEDIUM,
        CapacityRiskLevel.HIGH,
        CapacityRiskLevel.CRITICAL,
    }

    payload = recommendation.model_dump()
    assert "assigned_room_id" not in payload
    assert "reservation_id" not in payload
    assert "auto_apply" not in payload

    assert candidate_a.model_dump() == before_a
    assert candidate_b.model_dump() == before_b


def test_conflict_evidence_reduces_room_recommendation_without_mutation() -> None:
    tenant_id = _create_tenant("a0207-flow2")
    requirement = _requirement()
    room = _capability(tenant_id, "LAB-CONFLICT")
    schedule = RoomAllocationSchedule(day_of_week="monday", time_slot_id=2)

    existing_bookings = [
        {
            "room_id": "LAB-CONFLICT",
            "day_of_week": "monday",
            "time_slot_id": 2,
            "section_id": 8888,
            "booking_type": "booking",
        }
    ]
    before_bookings = [dict(item) for item in existing_bookings]

    without_conflict = build_room_allocation_recommendation_result(
        tenant_id,
        requirement,
        [room],
    )

    conflicts = detect_room_requirement_conflicts(
        tenant_id,
        requirement,
        capability=room,
        schedule=schedule,
        existing_bookings=existing_bookings,
    )
    assert any(item.conflict_type in {ConflictType.ROOM_TIME_CONFLICT, ConflictType.BOOKING_CONFLICT} for item in conflicts)

    with_conflict = build_room_allocation_recommendation_result(
        tenant_id,
        requirement,
        [room],
        conflicts_by_room_id={"LAB-CONFLICT": conflicts},
    )

    assert with_conflict.candidates[0].recommendation_score < without_conflict.candidates[0].recommendation_score
    assert existing_bookings == before_bookings


def test_no_viable_candidate_requires_human_review() -> None:
    tenant_id = _create_tenant("a0207-flow3")
    requirement = _requirement()
    unavailable_rooms = [
        _capability(tenant_id, "LAB-MAINT", maintenance_status="maintenance"),
        _capability(tenant_id, "LAB-OFF", availability_status="unavailable"),
    ]

    recommendation = build_room_allocation_recommendation_result(
        tenant_id,
        requirement,
        unavailable_rooms,
    )

    assert recommendation.recommendation_status == RoomAllocationRecommendationStatus.NO_VIABLE_CANDIDATE
    assert recommendation.has_viable_candidate is False
    assert recommendation.required_human_review is True
    assert recommendation.best_candidate_id is None


def test_room_allocation_kpi_pipeline_contract(reset_shared_state) -> None:
    tenant_id = _create_tenant("a0207-flow4")

    _emit(tenant_id, "scheduling.room_allocation.recommendation_generated", 100)
    _emit(tenant_id, "scheduling.room_allocation.recommendation_generated", 101)
    _emit(tenant_id, "scheduling.room_allocation.review_required", 102)
    _emit(tenant_id, "scheduling.room_allocation.no_viable_candidate", 103)
    _emit(tenant_id, "scheduling.room_allocation.candidate_ranked", 104)
    _emit(tenant_id, "scheduling.capacity_mismatch.detected", 105)

    with UnitOfWork() as uow:
        rows = kpi_service.refresh_tenant_metrics(tenant_id=tenant_id, uow=uow)

    values = {str(item["metric_key"]): int(item["metric_value"]) for item in rows}
    assert values["room_allocation_recommendations_count"] == 2
    assert values["room_allocation_review_required_count"] == 1
    assert values["room_allocation_no_viable_candidate_count"] == 1
    assert values["room_allocation_candidate_evaluated_count"] == 1
    assert values["room_capacity_mismatch_count"] == 1


def test_cross_tenant_candidate_rejected_and_no_leakage(reset_shared_state) -> None:
    tenant_a = _create_tenant("a0207-flow5-a")
    tenant_b = _create_tenant("a0207-flow5-b")
    requirement = _requirement()

    candidate_b = _capability(tenant_b, "LAB-B")
    with pytest.raises(ValueError, match="tenant_id mismatch"):
        build_room_allocation_recommendation_result(tenant_a, requirement, [candidate_b])

    _emit(tenant_b, "scheduling.room_allocation.recommendation_generated", 210)
    _emit(tenant_b, "scheduling.room_allocation.review_required", 211)

    with UnitOfWork() as uow:
        tenant_a_rows = kpi_service.refresh_tenant_metrics(tenant_id=tenant_a, uow=uow)

    tenant_a_values = {str(item["metric_key"]): int(item["metric_value"]) for item in tenant_a_rows}
    assert tenant_a_values["room_allocation_recommendations_count"] == 0
    assert tenant_a_values["room_allocation_review_required_count"] == 0


def test_non_destructive_room_allocation_contract() -> None:
    tenant_id = _create_tenant("a0207-flow6")
    requirement = _requirement()
    capability = _capability(tenant_id, "LAB-NON-DESTRUCT")

    capacity_result = build_capacity_matching_result(
        tenant_id,
        requirement,
        capability=capability,
    )

    recommendation = build_room_allocation_recommendation_result(
        tenant_id,
        requirement,
        [capability],
    )

    capacity_payload = capacity_result.model_dump()
    recommendation_payload = recommendation.model_dump()

    assert "assigned_room_id" not in capacity_payload
    assert "assigned_room_id" not in recommendation_payload
    assert "reservation_id" not in capacity_payload
    assert "reservation_id" not in recommendation_payload
    assert "booking_override" not in recommendation_payload
    assert "auto_apply" not in recommendation_payload

    combined_text = str(capacity_payload).lower() + " " + str(recommendation_payload).lower()
    assert "fake optimization" not in combined_text

    for action in capacity_result.decision.recommended_actions:
        lowered = action.lower()
        assert "assign" not in lowered
        assert "reserve" not in lowered
        assert "override" not in lowered
        assert "auto" not in lowered
