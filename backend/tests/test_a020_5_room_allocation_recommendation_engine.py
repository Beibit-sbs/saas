"""A-020.5 — Room Allocation Recommendation Engine tests.

Deterministic ranking-only recommendation that explains why candidates are preferred.
No assignment, no reservation, no mutation.
"""
from __future__ import annotations

import pytest

from app.modules.brain_core.classifiers.risk_classifier import RiskClassifier
from app.modules.brain_core.reasoning.rules_engine import RulesEngine
from app.modules.brain_core.registry import DecisionRegistry, SignalRegistry
from app.modules.scheduling.room_allocation_readiness import (
    CapacityRiskLevel,
    ConflictSeverity,
    ConflictType,
    RoomAllocationSchedule,
    RoomAllocationRecommendationStatus,
    RoomAllocationRequirement,
    RoomCapability,
    SchedulingConflictEvidence,
    build_capacity_matching_result,
    build_room_allocation_recommendation_result,
    build_scheduling_conflict_result,
    detect_room_requirement_conflicts,
    room_allocation_readiness_from_event_payload,
)
from app.platform.event_ingestion.types import VALID_EVENT_TYPES
from app.platform.events.registry import EXACT_EVENT_REGISTRY
from app.platform.kpi import service as kpi_service


TENANT = 1


def _req(**kwargs) -> RoomAllocationRequirement:
    data = {
        "section_id": 2001,
        "course_id": 301,
        "group_id": 701,
        "teacher_id": "T-7",
        "students_count": 36,
        "max_capacity": 45,
        "required_room_type": "computer_lab",
        "required_computers": 20,
        "equipment_required": ["projector", "whiteboard"],
        "restrictions_required": ["exam_enabled"],
    }
    data.update(kwargs)
    return RoomAllocationRequirement(**data)


def _cap(room_id: str, **kwargs) -> RoomCapability:
    data = {
        "tenant_id": TENANT,
        "room_id": room_id,
        "room_code": room_id,
        "room_name": room_id,
        "room_type": "computer_lab",
        "capacity": 48,
        "computers_count": 24,
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
    data.update(kwargs)
    return RoomCapability(**data)


def _conflict(room_id: str, severity: ConflictSeverity = ConflictSeverity.MEDIUM) -> SchedulingConflictEvidence:
    return SchedulingConflictEvidence(
        tenant_id=TENANT,
        conflict_type=ConflictType.ROOM_TIME_CONFLICT,
        severity=severity,
        section_id=2001,
        course_id=301,
        room_id=room_id,
        reason="test-conflict",
        evidence={"source": "test"},
        source_entity_type="section",
        source_entity_id=2001,
    )


def test_01_ranks_better_capacity_match_higher():
    req = _req(students_count=40)
    candidates = [
        _cap("R-OK", capacity=44),
        _cap("R-TIGHT", capacity=40),
        _cap("R-SHORT", capacity=20),
    ]
    result = build_room_allocation_recommendation_result(TENANT, req, candidates)
    assert result.candidates[0].room_id in {"R-OK", "R-TIGHT"}
    assert result.candidates[-1].room_id == "R-SHORT"


def test_02_returns_no_viable_candidate_when_everything_unavailable():
    req = _req()
    candidates = [
        _cap("R1", maintenance_status="maintenance"),
        _cap("R2", availability_status="unavailable"),
    ]
    result = build_room_allocation_recommendation_result(TENANT, req, candidates)
    assert result.recommendation_status == RoomAllocationRecommendationStatus.NO_VIABLE_CANDIDATE
    assert result.has_viable_candidate is False
    assert result.best_candidate_id is None


def test_03_candidate_tenant_mismatch_rejected():
    with pytest.raises(ValueError):
        build_room_allocation_recommendation_result(TENANT, _req(), [_cap("R1", tenant_id=999)])


def test_04_conflict_tenant_mismatch_rejected():
    bad_conflict = _conflict("R1")
    bad_conflict.tenant_id = 999
    with pytest.raises(ValueError):
        build_room_allocation_recommendation_result(
            TENANT,
            _req(),
            [_cap("R1")],
            conflicts_by_room_id={"R1": [bad_conflict]},
        )


def test_05_deterministic_tie_breaker_uses_room_id_asc():
    req = _req(students_count=30)
    a = _cap("R-A", capacity=40)
    b = _cap("R-B", capacity=40)
    result = build_room_allocation_recommendation_result(TENANT, req, [b, a])
    assert [c.room_id for c in result.candidates[:2]] == ["R-A", "R-B"]


def test_06_conflict_penalty_lowers_score():
    req = _req()
    base = build_room_allocation_recommendation_result(TENANT, req, [_cap("R1")])
    penalized = build_room_allocation_recommendation_result(
        TENANT,
        req,
        [_cap("R1")],
        conflicts_by_room_id={"R1": [_conflict("R1")]},
    )
    assert penalized.candidates[0].recommendation_score < base.candidates[0].recommendation_score


def test_07_equipment_gap_lowers_score():
    req = _req(equipment_required=["projector", "smartboard"])
    best = build_room_allocation_recommendation_result(
        TENANT,
        req,
        [_cap("R1", equipment_available=["projector", "smartboard", "whiteboard"])],
    )
    degraded = build_room_allocation_recommendation_result(
        TENANT,
        req,
        [_cap("R1", equipment_available=["projector"])],
    )
    assert degraded.candidates[0].recommendation_score < best.candidates[0].recommendation_score


def test_08_computer_gap_lowers_score():
    req = _req(required_computers=30)
    best = build_room_allocation_recommendation_result(TENANT, req, [_cap("R1", computers_count=40)])
    degraded = build_room_allocation_recommendation_result(TENANT, req, [_cap("R1", computers_count=10)])
    assert degraded.candidates[0].recommendation_score < best.candidates[0].recommendation_score


def test_09_capacity_shortage_moves_to_review_required_candidate_status():
    req = _req(students_count=60)
    result = build_room_allocation_recommendation_result(TENANT, req, [_cap("R1", capacity=20)])
    assert result.candidates[0].recommendation_status == RoomAllocationRecommendationStatus.REVIEW_REQUIRED
    assert result.candidates[0].required_human_review is True


def test_10_output_contains_no_assignment_fields():
    result = build_room_allocation_recommendation_result(TENANT, _req(), [_cap("R1")])
    payload = result.model_dump()
    assert "assigned_room_id" not in payload
    assert "reservation_id" not in payload
    assert "auto_apply" not in payload


def test_11_output_contains_ranked_candidates_and_best_candidate():
    result = build_room_allocation_recommendation_result(TENANT, _req(), [_cap("R2"), _cap("R1")])
    assert len(result.candidates) == 2
    assert result.best_candidate_id is not None
    assert result.best_candidate_score is not None


def test_12_no_candidate_input_yields_no_viable_candidate():
    result = build_room_allocation_recommendation_result(TENANT, _req(), [])
    assert result.recommendation_status == RoomAllocationRecommendationStatus.NO_VIABLE_CANDIDATE
    assert result.required_human_review is True


def test_13_recommendation_is_deterministic_for_same_input():
    req = _req()
    candidates = [_cap("R1"), _cap("R2", capacity=46)]
    first = build_room_allocation_recommendation_result(TENANT, req, candidates)
    second = build_room_allocation_recommendation_result(TENANT, req, candidates)
    assert first.model_dump() == second.model_dump()


def test_14_source_entity_fields_present():
    result = build_room_allocation_recommendation_result(TENANT, _req(section_id=999), [_cap("R1")])
    assert result.source_entity_type == "section"
    assert result.source_entity_id == 999


def test_15_no_schedule_mutation_when_conflicts_detected():
    req = _req()
    cap = _cap("R1")
    bookings = [{"room_id": "R1", "day_of_week": "monday", "time_slot_id": 2, "section_id": 888, "booking_type": "booking"}]
    before = [dict(x) for x in bookings]
    schedule = RoomAllocationSchedule(day_of_week="monday", time_slot_id=2)
    conflicts = detect_room_requirement_conflicts(
        TENANT,
        req,
        capability=cap,
        schedule=schedule,
        existing_bookings=bookings,
    )
    _ = build_room_allocation_recommendation_result(TENANT, req, [cap], conflicts_by_room_id={"R1": conflicts})
    assert bookings == before


def test_16_reasons_and_warnings_populated():
    req = _req(required_computers=40)
    result = build_room_allocation_recommendation_result(TENANT, req, [_cap("R1", computers_count=10)])
    candidate = result.candidates[0]
    assert any(x.startswith("match_status=") for x in candidate.reasons)
    assert "computers_shortage" in candidate.warnings


def test_17_ranking_prefers_lower_risk_at_same_score_band():
    req = _req(students_count=45)
    low = _cap("R-LOW", capacity=48)
    high = _cap("R-HIGH", capacity=46)
    result = build_room_allocation_recommendation_result(
        TENANT,
        req,
        [high, low],
        conflicts_by_room_id={"R-HIGH": [_conflict("R-HIGH", severity=ConflictSeverity.HIGH)]},
    )
    assert result.candidates[0].room_id == "R-LOW"


def test_18_a0201_readiness_still_operational():
    readiness = room_allocation_readiness_from_event_payload(
        TENANT,
        {
            "section_id": 1,
            "course_id": 2,
            "enrolled_count": 10,
            "max_capacity": 25,
            "room_id": "R-1",
            "room_capacity": 30,
        },
    )
    assert readiness.tenant_id == TENANT
    assert readiness.requirement.section_id == 1


def test_19_a0204_capacity_matching_still_operational():
    result = build_capacity_matching_result(TENANT, _req(), capability=_cap("R1"))
    assert result.risk_level in {
        CapacityRiskLevel.LOW,
        CapacityRiskLevel.MEDIUM,
        CapacityRiskLevel.HIGH,
        CapacityRiskLevel.CRITICAL,
    }


def test_20_a0203_conflict_detection_contract_still_operational():
    result = build_scheduling_conflict_result(TENANT, _req(), capability=_cap("R1"))
    assert result.conflict_count == 0


def test_21_brain_registry_classifier_rules_for_recommendation_signal():
    assert SignalRegistry.signals["scheduling.room_allocation.recommendation_generated"]["scenario"] == "room_allocation_recommendation"
    assert "room_allocation_recommendation" in DecisionRegistry.decisions
    cls = RiskClassifier().classify(
        {
            "event_type": "scheduling.room_allocation.recommendation_generated",
            "payload": {"recommendation_status": "recommended", "required_human_review": False},
        },
        {},
    )
    decision = RulesEngine().evaluate(cls, {})
    assert "review_room_allocation_recommendations" in decision["recommended_actions"]


def test_22_kpi_and_event_lineage_recommendation_path_exists():
    assert "scheduling.room_allocation.recommendation_generated" in VALID_EVENT_TYPES
    assert "scheduling.room_allocation.recommendation_generated" in EXACT_EVENT_REGISTRY
    assert "scheduling.room_allocation.recommendation_generated" in kpi_service.EVENT_DERIVED_METRIC_LINEAGE[
        "room_allocation_recommendations_generated_count"
    ]


def test_23_high_risk_event_classifies_to_recommendation_high_path():
    cls = RiskClassifier().classify(
        {
            "event_type": "scheduling.room_allocation.recommendation_generated",
            "payload": {
                "recommendation_status": "review_required",
                "required_human_review": True,
            },
        },
        {},
    )
    assert cls["reasoning_path"] == "room_allocation_recommendation_high"


def test_24_review_required_rule_requires_approval():
    decision = RulesEngine().evaluate(
        {
            "reasoning_path": "room_allocation_recommendation_high",
            "severity": "high",
            "urgency": "high",
        },
        {},
    )
    assert decision["requires_approval"] is True
    assert "request_room_allocation_human_review" in decision["recommended_actions"]
