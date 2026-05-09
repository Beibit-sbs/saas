"""A-020.4 — Capacity Matching Brain tests.

Deterministic, evidence-only matching for room capability vs section requirement.
Non-destructive: no assignment/ranking/reservation/mutation.
"""
from __future__ import annotations

import pytest

from app.modules.brain_core.classifiers.risk_classifier import RiskClassifier
from app.modules.brain_core.reasoning.rules_engine import RulesEngine
from app.modules.brain_core.registry import DecisionRegistry, SignalRegistry
from app.modules.scheduling.room_allocation_readiness import (
    CapacityMatchStatus,
    CapacityMismatchReason,
    CapacityRiskLevel,
    ConflictSeverity,
    ConflictType,
    RoomAllocationRequirement,
    RoomAllocationSchedule,
    RoomCapability,
    SchedulingConflictEvidence,
    assess_room_capability_against_requirement,
    build_capacity_matching_result,
    build_scheduling_conflict_result,
    detect_room_requirement_conflicts,
)
from app.platform.event_ingestion.types import VALID_EVENT_TYPES
from app.platform.events.registry import EXACT_EVENT_REGISTRY
from app.platform.kpi import service as kpi_service


TENANT = 1


def _req(**kwargs) -> RoomAllocationRequirement:
    data = {
        "section_id": 101,
        "course_id": 202,
        "group_id": 303,
        "teacher_id": "T-1",
        "students_count": 30,
        "max_capacity": 40,
        "required_room_type": "computer_lab",
        "required_computers": 20,
        "equipment_required": ["projector", "whiteboard"],
        "restrictions_required": ["exam_enabled"],
    }
    data.update(kwargs)
    return RoomAllocationRequirement(**data)


def _cap(**kwargs) -> RoomCapability:
    data = {
        "tenant_id": TENANT,
        "room_id": "LAB-9",
        "room_code": "LAB-9",
        "room_name": "Lab 9",
        "room_type": "computer_lab",
        "capacity": 45,
        "computers_count": 25,
        "equipment_available": ["projector", "whiteboard", "audio"],
        "supported_lesson_types": ["lecture", "lab"],
        "restrictions": ["exam_enabled"],
        "availability_status": "available",
        "booking_status": "released",
        "maintenance_status": "ok",
        "is_active": True,
        "source_entity_type": "campus_room",
        "source_entity_id": "room-9",
    }
    data.update(kwargs)
    return RoomCapability(**data)


def _conflict(conflict_type: ConflictType, severity: ConflictSeverity) -> SchedulingConflictEvidence:
    return SchedulingConflictEvidence(
        tenant_id=TENANT,
        conflict_type=conflict_type,
        severity=severity,
        section_id=101,
        course_id=202,
        room_id="LAB-9",
        reason="test-conflict",
        evidence={"src": "test"},
        source_entity_type="section",
        source_entity_id=101,
    )


def test_01_excellent_match_produces_high_score_and_low_risk():
    result = build_capacity_matching_result(TENANT, _req(), capability=_cap())
    assert result.match_status == CapacityMatchStatus.EXCELLENT_MATCH
    assert result.match_score >= 90
    assert result.risk_level == CapacityRiskLevel.LOW
    assert result.required_human_review is False


def test_02_good_match_produces_acceptable_score_and_low_risk():
    result = build_capacity_matching_result(TENANT, _req(), capability=_cap(room_type=None))
    assert result.match_status == CapacityMatchStatus.GOOD_MATCH
    assert 75 <= result.match_score <= 89
    assert result.risk_level == CapacityRiskLevel.LOW


def test_03_partial_match_produces_reasons_and_medium_risk():
    result = build_capacity_matching_result(
        TENANT,
        _req(required_computers=20),
        capability=_cap(capacity=None, computers_count=None),
    )
    assert result.match_status == CapacityMatchStatus.PARTIAL_MATCH
    assert result.risk_level == CapacityRiskLevel.MEDIUM
    assert CapacityMismatchReason.CAPACITY_UNKNOWN in result.mismatch_reasons
    assert CapacityMismatchReason.COMPUTERS_UNKNOWN in result.mismatch_reasons


def test_04_insufficient_capacity_produces_high_or_critical_and_review_required():
    result = build_capacity_matching_result(TENANT, _req(students_count=60), capability=_cap(capacity=20))
    assert CapacityMismatchReason.CAPACITY_SHORTAGE in result.mismatch_reasons
    assert result.risk_level in {CapacityRiskLevel.HIGH, CapacityRiskLevel.CRITICAL}
    assert result.required_human_review is True


def test_05_computer_shortage_produces_mismatch_reason():
    result = build_capacity_matching_result(TENANT, _req(required_computers=30), capability=_cap(computers_count=10))
    assert CapacityMismatchReason.COMPUTERS_SHORTAGE in result.mismatch_reasons


def test_06_equipment_mismatch_exposes_missing_equipment_payload():
    result = build_capacity_matching_result(
        TENANT,
        _req(equipment_required=["projector", "smartboard"]),
        capability=_cap(equipment_available=["projector"]),
    )
    assert CapacityMismatchReason.EQUIPMENT_MISMATCH in result.mismatch_reasons
    cap_match = result.evidence.get("capability_match") or {}
    assert "smartboard" in (cap_match.get("missing_equipment") or [])


def test_07_room_type_mismatch_produces_mismatch_reason():
    result = build_capacity_matching_result(
        TENANT,
        _req(required_room_type="lecture_hall"),
        capability=_cap(room_type="computer_lab"),
    )
    assert CapacityMismatchReason.ROOM_TYPE_MISMATCH in result.mismatch_reasons


def test_08_unavailable_or_maintenance_room_produces_unavailable_status():
    result = build_capacity_matching_result(
        TENANT,
        _req(),
        capability=_cap(maintenance_status="maintenance"),
    )
    assert result.match_status == CapacityMatchStatus.UNAVAILABLE
    assert result.risk_level in {CapacityRiskLevel.HIGH, CapacityRiskLevel.CRITICAL}


def test_09_conflict_evidence_reduces_score():
    base = build_capacity_matching_result(TENANT, _req(), capability=_cap())
    with_conflict = build_capacity_matching_result(
        TENANT,
        _req(),
        capability=_cap(),
        conflicts=[_conflict(ConflictType.GROUP_TIME_CONFLICT, ConflictSeverity.MEDIUM)],
    )
    assert with_conflict.match_score < base.match_score
    assert CapacityMismatchReason.CONFLICT_PENALTY_APPLIED in with_conflict.mismatch_reasons


def test_10_missing_optional_fields_do_not_crash():
    req = RoomAllocationRequirement(section_id=1, course_id=2, students_count=10, max_capacity=20)
    result = build_capacity_matching_result(TENANT, req, capability=_cap())
    assert 0 <= result.match_score <= 100


def test_11_missing_tenant_id_fails_closed():
    with pytest.raises(ValueError):
        build_capacity_matching_result(0, _req(), capability=_cap())


def test_12_tenant_mismatch_between_requirement_and_capability_rejected():
    with pytest.raises(ValueError):
        build_capacity_matching_result(TENANT, _req(), capability=_cap(tenant_id=999))


def test_13_high_or_critical_requires_human_review():
    result = build_capacity_matching_result(
        TENANT,
        _req(students_count=120),
        capability=_cap(capacity=10),
        conflicts=[_conflict(ConflictType.BOOKING_CONFLICT, ConflictSeverity.CRITICAL)],
    )
    assert result.risk_level == CapacityRiskLevel.CRITICAL
    assert result.required_human_review is True
    assert result.decision.requires_approval is True


def test_14_low_risk_has_no_destructive_actions():
    result = build_capacity_matching_result(TENANT, _req(), capability=_cap())
    assert result.risk_level == CapacityRiskLevel.LOW
    assert all("assign" not in a for a in result.decision.recommended_actions)
    assert all("reserve" not in a for a in result.decision.recommended_actions)
    assert all("reschedule" not in a for a in result.decision.recommended_actions)


def test_15_brain_registry_classifier_rules_path_exists_via_existing_capacity_scenario():
    assert SignalRegistry.signals["scheduling.capacity_mismatch.detected"]["scenario"] == "enrollment_capacity_risk"
    assert "enrollment_capacity_risk" in DecisionRegistry.decisions
    assert "scheduling.capacity_mismatch.detected" in DecisionRegistry.decisions["enrollment_capacity_risk"]["allowed_event_types"]

    cls = RiskClassifier().classify(
        {"event_type": "scheduling.capacity_mismatch.detected", "payload": {"required_capacity": 50, "room_capacity": 30}},
        {},
    )
    assert cls["reasoning_path"] == "enrollment_capacity_risk_high"
    decision = RulesEngine().evaluate(cls, {})
    assert "create_enrollment_capacity_task" in decision["recommended_actions"]


def test_16_kpi_and_event_lineage_for_capacity_path_exists():
    assert "scheduling.capacity_mismatch.detected" in VALID_EVENT_TYPES
    assert "scheduling.capacity_mismatch.detected" in EXACT_EVENT_REGISTRY
    assert "scheduling.capacity_mismatch.detected" in kpi_service.EVENT_DERIVED_METRIC_LINEAGE["capacity_risk_sections_count"]


def test_17_no_schedule_mutation_occurs():
    req = _req()
    cap = _cap()
    before = req.model_dump(), cap.model_dump()
    _ = build_capacity_matching_result(TENANT, req, capability=cap)
    after = req.model_dump(), cap.model_dump()
    assert before == after


def test_18_no_room_booking_mutation_occurs_when_conflicts_are_passed_in():
    req = _req()
    cap = _cap()
    bookings = [{"room_id": "LAB-9", "day_of_week": "monday", "time_slot_id": 1, "section_id": 999, "booking_type": "booking"}]
    schedule = RoomAllocationSchedule(day_of_week="monday", time_slot_id=1)
    conflicts = detect_room_requirement_conflicts(
        TENANT,
        req,
        capability=cap,
        schedule=schedule,
        existing_bookings=bookings,
    )
    before_bookings = [dict(x) for x in bookings]
    _ = build_capacity_matching_result(TENANT, req, capability=cap, conflicts=conflicts)
    assert bookings == before_bookings


def test_19_no_recommendation_ranking_produced():
    result = build_capacity_matching_result(TENANT, _req(), capability=_cap())
    payload = result.model_dump()
    assert "ranking" not in payload
    assert "candidate_rooms" not in payload


def test_20_no_room_assignment_or_reservation_output_produced():
    result = build_capacity_matching_result(TENANT, _req(), capability=_cap())
    payload = result.model_dump()
    assert "assigned_room_id" not in payload
    assert "reservation_id" not in payload
    assert "auto_apply" not in payload


def test_21_no_fake_optimization_result_fields():
    result = build_capacity_matching_result(TENANT, _req(), capability=_cap())
    payload = result.model_dump()
    assert "optimization_score" not in payload
    assert "model_confidence" not in payload


def test_22_a0201_readiness_contract_still_operational():
    from app.modules.scheduling.room_allocation_readiness import room_allocation_readiness_from_event_payload

    readiness = room_allocation_readiness_from_event_payload(
        1,
        {"section_id": 1, "course_id": 2, "enrolled_count": 10, "max_capacity": 20, "room_id": "R1", "room_capacity": 25},
    )
    assert readiness.tenant_id == 1
    assert readiness.requirement.section_id == 1


def test_23_a0202_capability_contract_still_operational():
    req = _req()
    cap = _cap()
    match = assess_room_capability_against_requirement(cap, req, authoritative_tenant_id=TENANT)
    assert match.capacity_ok is True


def test_24_a0203_conflict_contract_still_operational():
    result = build_scheduling_conflict_result(TENANT, _req(), capability=_cap())
    assert result.conflict_count == 0


def test_25_unknown_status_when_capability_missing():
    result = build_capacity_matching_result(TENANT, _req(), capability=None)
    assert result.match_status == CapacityMatchStatus.UNKNOWN
    assert result.required_human_review is True


def test_26_decision_contains_review_only_actions():
    result = build_capacity_matching_result(
        TENANT,
        _req(students_count=90),
        capability=_cap(capacity=20),
    )
    actions = set(result.decision.recommended_actions)
    assert "review_room_match" in actions
    assert "inspect_room_capability_evidence" in actions
    assert "request_room_change_review" in actions
