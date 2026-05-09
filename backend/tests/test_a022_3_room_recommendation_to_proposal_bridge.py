"""A-022.3 Room Recommendation -> Proposal Bridge contract tests."""
from __future__ import annotations

import pytest

from app.modules.scheduling.room_allocation_readiness import (
    CapacityRiskLevel,
    RoomAllocationRecommendationStatus,
    RoomAllocationRequirement,
    RoomCapability,
    build_room_allocation_recommendation_result,
)
from app.modules.scheduling.timetable_change_proposal import (
    TimetableChangeCurrentSnapshot,
    TimetableChangeProposal,
    TimetableChangeProposalSourceType,
    TimetableChangeProposalStatus,
    transition_timetable_change_proposal,
)
from app.modules.scheduling.timetable_change_simulation import (
    TimetableChangeSimulationStatus,
    build_timetable_change_simulation,
)
from app.modules.scheduling.timetable_recommendation_bridge import (
    RoomRecommendationToProposalBridgeInput,
    build_proposal_from_room_allocation_recommendation,
)


def _requirement(**overrides: object) -> RoomAllocationRequirement:
    payload: dict[str, object] = {
        "section_id": 5001,
        "course_id": 7001,
        "group_id": 9001,
        "teacher_id": "teacher-1",
        "students_count": 40,
        "max_capacity": 50,
        "required_room_type": "computer_lab",
        "required_computers": 20,
        "equipment_required": ["projector"],
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
        "capacity": 45,
        "computers_count": 25,
        "equipment_available": ["projector", "whiteboard"],
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


def _snapshot(room_id: str = "ROOM-A") -> TimetableChangeCurrentSnapshot:
    return TimetableChangeCurrentSnapshot(
        section_id=5001,
        course_id=7001,
        group_id=9001,
        teacher_id="teacher-1",
        room_id=room_id,
        day_of_week="monday",
        time_slot_id=2,
        start_time="09:00:00",
        end_time="10:30:00",
        room_capacity=40,
        students_count=38,
        source_entity_type="section",
        source_entity_id=5001,
    )


def _recommendation(
    tenant_id: int = 1,
    viable: bool = True,
    best_room_id: str = "ROOM-B",
    include_second: bool = True,
) -> object:
    req = _requirement()
    candidates = [_capability(tenant_id, best_room_id)]
    if include_second:
        candidates.append(_capability(tenant_id, "ROOM-C", capacity=42, computers_count=21))

    recommendation = build_room_allocation_recommendation_result(
        tenant_id=tenant_id,
        requirement=req,
        candidates=candidates,
    )

    if not viable:
        recommendation = recommendation.model_copy(
            update={
                "has_viable_candidate": False,
                "best_candidate_id": None,
                "recommendation_status": RoomAllocationRecommendationStatus.NO_VIABLE_CANDIDATE,
            }
        )

    return recommendation


def _bridge_input(
    tenant_id: int = 1,
    recommendation=None,
    **overrides: object,
) -> RoomRecommendationToProposalBridgeInput:
    rec = recommendation or _recommendation(tenant_id=tenant_id)
    payload = {
        "tenant_id": tenant_id,
        "recommendation_result": rec,
        "current_snapshot": _snapshot(),
        "created_by": "actor-1",
        "reason": "Bridge from recommendation",
        "source_entity_id": "rec-001",
    }
    payload.update(overrides)
    return RoomRecommendationToProposalBridgeInput(**payload)


# 1

def test_bridge_requires_positive_tenant_id() -> None:
    rec = _recommendation(tenant_id=1)
    inp = _bridge_input(tenant_id=1, recommendation=rec)
    inp = inp.model_copy(update={"tenant_id": 0})
    with pytest.raises(ValueError, match="tenant_id"):
        build_proposal_from_room_allocation_recommendation(inp)


# 2

def test_recommendation_tenant_must_match_authoritative_tenant() -> None:
    rec = _recommendation(tenant_id=2)
    inp = _bridge_input(tenant_id=1, recommendation=rec)
    with pytest.raises(ValueError, match="Cross-tenant bridge rejected"):
        build_proposal_from_room_allocation_recommendation(inp)


# 3

def test_selected_candidate_tenant_must_match_recommendation_tenant() -> None:
    rec = _recommendation(tenant_id=1)
    bad_candidate = rec.candidates[0].model_copy(update={"tenant_id": 9})
    rec = rec.model_copy(update={"candidates": [bad_candidate]})
    inp = _bridge_input(tenant_id=1, recommendation=rec, selected_candidate_id=bad_candidate.room_id)
    with pytest.raises(ValueError, match="Cross-tenant candidate rejected"):
        build_proposal_from_room_allocation_recommendation(inp)


# 4

def test_selected_candidate_id_can_be_explicit() -> None:
    rec = _recommendation(tenant_id=1, best_room_id="ROOM-B", include_second=True)
    inp = _bridge_input(tenant_id=1, recommendation=rec, selected_candidate_id="ROOM-C")
    result = build_proposal_from_room_allocation_recommendation(inp)
    assert str(result.selected_candidate_id) == "ROOM-C"


# 5

def test_missing_selected_candidate_uses_best_candidate_when_viable() -> None:
    rec = _recommendation(tenant_id=1, best_room_id="ROOM-B")
    inp = _bridge_input(tenant_id=1, recommendation=rec)
    result = build_proposal_from_room_allocation_recommendation(inp)
    assert str(result.selected_candidate_id) == str(rec.best_candidate_id)


# 6

def test_no_viable_candidate_rejected_by_default_policy() -> None:
    rec = _recommendation(tenant_id=1, viable=False)
    inp = _bridge_input(tenant_id=1, recommendation=rec)
    with pytest.raises(ValueError, match="No viable recommendation candidate"):
        build_proposal_from_room_allocation_recommendation(inp)


# 7

def test_no_viable_candidate_can_create_review_only_proposal_when_allowed() -> None:
    rec = _recommendation(tenant_id=1, viable=False)
    inp = _bridge_input(
        tenant_id=1,
        recommendation=rec,
        allow_review_only_no_viable=True,
        explicit_review_reason="No viable candidate, create review-only proposal",
    )
    result = build_proposal_from_room_allocation_recommendation(inp)
    assert isinstance(result.proposal, TimetableChangeProposal)
    assert result.proposal.proposed_change.proposed_room_id is None
    assert result.data_quality_note is not None


# 8

def test_not_recommended_candidate_rejected_without_explicit_review_reason() -> None:
    rec = _recommendation(tenant_id=1)
    candidate = rec.candidates[0].model_copy(
        update={"recommendation_status": RoomAllocationRecommendationStatus.NOT_RECOMMENDED}
    )
    rec = rec.model_copy(update={"candidates": [candidate], "best_candidate_id": candidate.room_id})
    inp = _bridge_input(tenant_id=1, recommendation=rec)
    with pytest.raises(ValueError, match="requires explicit_review_reason"):
        build_proposal_from_room_allocation_recommendation(inp)


# 9

def test_bridge_creates_timetable_change_proposal() -> None:
    result = build_proposal_from_room_allocation_recommendation(_bridge_input())
    assert isinstance(result.proposal, TimetableChangeProposal)


# 10

def test_proposal_source_type_is_recommendation() -> None:
    result = build_proposal_from_room_allocation_recommendation(_bridge_input())
    assert result.proposal.source_type == TimetableChangeProposalSourceType.ROOM_ALLOCATION_RECOMMENDATION


# 11

def test_proposal_preserves_source_recommendation_id() -> None:
    result = build_proposal_from_room_allocation_recommendation(_bridge_input(source_entity_id="rec-xyz"))
    assert str(result.proposal.source_recommendation_id) == "rec-xyz"


# 12

def test_proposal_proposed_change_includes_selected_room_id() -> None:
    result = build_proposal_from_room_allocation_recommendation(_bridge_input())
    assert str(result.proposal.proposed_change.proposed_room_id) == str(result.selected_candidate_id)


# 13

def test_proposal_affected_entities_include_section_group_teacher_room() -> None:
    result = build_proposal_from_room_allocation_recommendation(_bridge_input())
    aff = result.proposal.affected_entities
    assert aff.affected_section_id == 5001
    assert aff.affected_group_id == 9001
    assert str(aff.affected_teacher_id) == "teacher-1"
    assert aff.affected_room_id is not None


# 14

def test_high_or_critical_risk_forces_approval_required_true() -> None:
    rec = _recommendation(tenant_id=1)
    high = rec.candidates[0].model_copy(
        update={"capacity_match": rec.candidates[0].capacity_match.model_copy(update={"risk_level": CapacityRiskLevel.HIGH})}
    )
    rec = rec.model_copy(update={"candidates": [high], "best_candidate_id": high.room_id})
    result = build_proposal_from_room_allocation_recommendation(
        _bridge_input(tenant_id=1, recommendation=rec)
    )
    assert result.proposal.approval_required is True


# 15

def test_proposal_audit_evidence_includes_bridge_action() -> None:
    result = build_proposal_from_room_allocation_recommendation(_bridge_input())
    actions = [entry.action for entry in result.proposal.audit_evidence]
    assert "bridge_from_room_recommendation" in actions


# 16

def test_proposal_can_be_passed_to_simulation_helper() -> None:
    bridge_result = build_proposal_from_room_allocation_recommendation(_bridge_input())
    sim_result = build_timetable_change_simulation(bridge_result.simulation_input)
    assert sim_result.status == TimetableChangeSimulationStatus.COMPUTED


# 17

def test_simulation_preview_shows_before_after_room_change() -> None:
    bridge_result = build_proposal_from_room_allocation_recommendation(_bridge_input())
    sim_result = build_timetable_change_simulation(bridge_result.simulation_input)
    assert "room_id" in sim_result.before_after_snapshot.changed_fields


# 18

def test_simulation_does_not_mutate_proposal_status() -> None:
    bridge_result = build_proposal_from_room_allocation_recommendation(_bridge_input())
    original_status = bridge_result.proposal.status
    _ = build_timetable_change_simulation(bridge_result.simulation_input)
    assert bridge_result.proposal.status == original_status


# 19

def test_no_schedule_mutation_output_exists() -> None:
    bridge_result = build_proposal_from_room_allocation_recommendation(_bridge_input())
    payload = bridge_result.proposal.model_dump()
    forbidden = {"mutate", "mutation", "apply_schedule", "update_schedule"}
    for key in payload:
        assert key not in forbidden


# 20

def test_no_room_reservation_output_exists() -> None:
    bridge_result = build_proposal_from_room_allocation_recommendation(_bridge_input())
    payload = bridge_result.proposal.model_dump()
    forbidden = {"reserve_room", "reservation", "room_reservation_flag"}
    for key in payload:
        assert key not in forbidden


# 21

def test_no_booking_override_output_exists() -> None:
    bridge_result = build_proposal_from_room_allocation_recommendation(_bridge_input())
    payload = bridge_result.proposal.model_dump()
    forbidden = {"booking_override", "override_booking", "force_booking"}
    for key in payload:
        assert key not in forbidden


# 22

def test_no_apply_or_commit_field_exists() -> None:
    bridge_result = build_proposal_from_room_allocation_recommendation(_bridge_input())
    payload = bridge_result.proposal.model_dump()
    forbidden = {"apply", "apply_flag", "commit", "auto_apply", "execute"}
    for key in payload:
        assert key not in forbidden


# 23

def test_no_fake_optimization_result_exists() -> None:
    bridge_result = build_proposal_from_room_allocation_recommendation(_bridge_input())
    payload = bridge_result.proposal.model_dump()
    forbidden = {
        "optimization_result",
        "optimized_score",
        "ai_recommendation",
        "auto_optimized",
    }
    for key in payload:
        assert key not in forbidden


# 24

def test_cross_tenant_bridge_rejected() -> None:
    rec = _recommendation(tenant_id=8)
    with pytest.raises(ValueError):
        build_proposal_from_room_allocation_recommendation(
            _bridge_input(tenant_id=1, recommendation=rec)
        )


# 25

def test_a020_recommendation_contract_still_green() -> None:
    rec = _recommendation(tenant_id=1)
    assert rec.has_viable_candidate is True
    assert rec.best_candidate_id is not None


# 26

def test_a022_1_proposal_fsm_contract_still_green() -> None:
    bridge_result = build_proposal_from_room_allocation_recommendation(_bridge_input())
    prop = bridge_result.proposal
    assert prop.status == TimetableChangeProposalStatus.DRAFT
    moved = transition_timetable_change_proposal(
        prop,
        TimetableChangeProposalStatus.PENDING_REVIEW,
        actor_id="actor-2",
        requesting_tenant_id=1,
    )
    assert moved.status == TimetableChangeProposalStatus.PENDING_REVIEW


# 27

def test_a022_2_simulation_contract_still_green() -> None:
    bridge_result = build_proposal_from_room_allocation_recommendation(_bridge_input())
    sim = build_timetable_change_simulation(bridge_result.simulation_input)
    assert sim.proposal_id == bridge_result.proposal.proposal_id
    assert sim.review_required is True


def test_unavailable_candidate_allowed_with_explicit_review_reason() -> None:
    rec = _recommendation(tenant_id=1)
    candidate = rec.candidates[0].model_copy(
        update={
            "capacity_match": rec.candidates[0].capacity_match.model_copy(
                update={"match_status": rec.candidates[0].capacity_match.match_status.UNAVAILABLE}
            ),
            "recommendation_status": RoomAllocationRecommendationStatus.REVIEW_REQUIRED,
        }
    )
    rec = rec.model_copy(update={"candidates": [candidate], "best_candidate_id": candidate.room_id})
    result = build_proposal_from_room_allocation_recommendation(
        _bridge_input(
            tenant_id=1,
            recommendation=rec,
            explicit_review_reason="Candidate unavailable but manual override review requested",
        )
    )
    assert result.proposal is not None


def test_selected_candidate_id_not_found_is_rejected() -> None:
    rec = _recommendation(tenant_id=1)
    with pytest.raises(ValueError, match="selected_candidate_id"):
        build_proposal_from_room_allocation_recommendation(
            _bridge_input(tenant_id=1, recommendation=rec, selected_candidate_id="ROOM-UNKNOWN")
        )
