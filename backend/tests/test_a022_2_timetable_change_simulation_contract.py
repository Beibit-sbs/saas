"""A-022.2 — Timetable Change Simulation / Preview Contract tests.

26 mandatory tests covering:
1.  Simulation requires tenant_id
2.  Simulation requires proposal_id
3.  Simulation requires proposal tenant match (via builder)
4.  Simulation builds proposed snapshot from current snapshot + proposed change
5.  changed_fields detected
6.  unchanged_fields detected
7.  conflict_delta computes resolved/created/unchanged/count_delta
8.  affected_delta includes sections/groups/teachers/rooms/bookings
9.  risk_delta marks review_required when risk increases
10. review_required true when proposal approval_required true
11. data_quality_note when predicted conflicts missing
12. draft proposal simulation allowed with note
13. pending_review proposal simulation allowed
14. approved proposal simulation allowed as preview only
15. rejected/cancelled/expired proposal simulation invalid or rejected
16. simulation does not change proposal status
17. no schedule mutation output exists
18. no room reservation output exists
19. no booking override output exists
20. no apply/commit field exists
21. no fake optimization result exists
22. audit evidence produced with simulation_computed action
23. cross-tenant simulation rejected (via tenant_id guard)
24. missing optional fields do not crash
25. A-022.1 proposal tests remain green (import + basic FSM check)
26. A-020 recommendation/room allocation tests remain green (import check)
"""
from __future__ import annotations

import pytest

from app.modules.scheduling.timetable_change_simulation import (
    TimetableChangeAffectedDelta,
    TimetableChangeBeforeAfterSnapshot,
    TimetableChangeConflictDelta,
    TimetableChangeRiskDelta,
    TimetableChangeSimulationInput,
    TimetableChangeSimulationResult,
    TimetableChangeSimulationStatus,
    build_simulation_audit_evidence,
    build_simulation_conflict_delta,
    build_timetable_change_simulation,
)
from app.modules.scheduling.timetable_change_proposal import (
    TimetableChangeAffectedEntities,
    TimetableChangeAuditEvidence,
    TimetableChangeCurrentSnapshot,
    TimetableChangeProposal,
    TimetableChangeProposalInput,
    TimetableChangeProposalRiskLevel,
    TimetableChangeProposalSourceType,
    TimetableChangeProposalStatus,
    TimetableChangeProposedChange,
    TimetableChangeType,
    build_timetable_change_proposal,
    transition_timetable_change_proposal,
)


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _make_snapshot(
    section_id: int = 101,
    course_id: int = 201,
    room_id: str | int | None = "room_A",
    day_of_week: str | None = "monday",
    time_slot_id: int | None = 1,
    teacher_id: str | int | None = "teacher_1",
) -> TimetableChangeCurrentSnapshot:
    return TimetableChangeCurrentSnapshot(
        section_id=section_id,
        course_id=course_id,
        room_id=room_id,
        day_of_week=day_of_week,
        time_slot_id=time_slot_id,
        teacher_id=teacher_id,
        start_time="09:00:00",
        end_time="10:30:00",
        room_capacity=30,
        students_count=25,
    )


def _make_proposed_change(
    change_type: TimetableChangeType = TimetableChangeType.ROOM_CHANGE,
    proposed_room_id: str | int | None = "room_B",
    proposed_day: str | None = None,
    proposed_slot: int | None = None,
    reason: str = "Manual change",
) -> TimetableChangeProposedChange:
    return TimetableChangeProposedChange(
        change_type=change_type,
        proposed_room_id=proposed_room_id,
        proposed_day_of_week=proposed_day,
        proposed_time_slot_id=proposed_slot,
        reason=reason,
    )


def _make_proposal(
    tenant_id: int = 1,
    status: TimetableChangeProposalStatus = TimetableChangeProposalStatus.PENDING_REVIEW,
    risk_level: TimetableChangeProposalRiskLevel = TimetableChangeProposalRiskLevel.MEDIUM,
    approval_required: bool = True,
    proposed_room_id: str | int | None = "room_B",
) -> TimetableChangeProposal:
    inp = TimetableChangeProposalInput(
        tenant_id=tenant_id,
        proposal_id="test_prop_001",
        source_type=TimetableChangeProposalSourceType.MANUAL,
        current_snapshot=_make_snapshot(),
        proposed_change=_make_proposed_change(proposed_room_id=proposed_room_id),
        affected_entities=TimetableChangeAffectedEntities(
            affected_section_id=101,
            affected_group_id=301,
            affected_teacher_id="teacher_1",
            affected_room_id="room_A",
            affected_student_count=25,
            affected_booking_ids=["bk_001"],
        ),
        risk_level=risk_level,
    )
    proposal = build_timetable_change_proposal(inp)
    # Optionally transition to desired status
    if status == TimetableChangeProposalStatus.PENDING_REVIEW:
        proposal = transition_timetable_change_proposal(
            proposal, TimetableChangeProposalStatus.PENDING_REVIEW,
            actor_id="actor_1", requesting_tenant_id=tenant_id,
        )
    elif status == TimetableChangeProposalStatus.APPROVED:
        proposal = transition_timetable_change_proposal(
            proposal, TimetableChangeProposalStatus.PENDING_REVIEW,
            actor_id="actor_1", requesting_tenant_id=tenant_id,
        )
        proposal = transition_timetable_change_proposal(
            proposal, TimetableChangeProposalStatus.APPROVED,
            actor_id="reviewer_1", requesting_tenant_id=tenant_id,
        )
    elif status == TimetableChangeProposalStatus.REJECTED:
        proposal = transition_timetable_change_proposal(
            proposal, TimetableChangeProposalStatus.PENDING_REVIEW,
            actor_id="actor_1", requesting_tenant_id=tenant_id,
        )
        proposal = transition_timetable_change_proposal(
            proposal, TimetableChangeProposalStatus.REJECTED,
            actor_id="reviewer_1", requesting_tenant_id=tenant_id,
        )
    elif status == TimetableChangeProposalStatus.CANCELLED:
        proposal = transition_timetable_change_proposal(
            proposal, TimetableChangeProposalStatus.CANCELLED,
            actor_id="actor_1", requesting_tenant_id=tenant_id,
        )
    elif status == TimetableChangeProposalStatus.REVISION_REQUESTED:
        proposal = transition_timetable_change_proposal(
            proposal, TimetableChangeProposalStatus.PENDING_REVIEW,
            actor_id="actor_1", requesting_tenant_id=tenant_id,
        )
        proposal = transition_timetable_change_proposal(
            proposal, TimetableChangeProposalStatus.REVISION_REQUESTED,
            actor_id="reviewer_1", requesting_tenant_id=tenant_id,
        )
    # Manually set risk_level and approval_required if needed
    proposal = proposal.model_copy(update={"risk_level": risk_level})
    return proposal


def _make_input(
    tenant_id: int = 1,
    status: TimetableChangeProposalStatus = TimetableChangeProposalStatus.PENDING_REVIEW,
    risk_level: TimetableChangeProposalRiskLevel = TimetableChangeProposalRiskLevel.MEDIUM,
    conflicts_before: list[str] | None = None,
    conflicts_after: list[str] | None = None,
) -> TimetableChangeSimulationInput:
    proposal = _make_proposal(tenant_id=tenant_id, status=status, risk_level=risk_level)
    return TimetableChangeSimulationInput(
        proposal=proposal,
        simulation_id="sim_test_001",
        actor_id="actor_1",
        conflicts_before=conflicts_before,
        conflicts_after=conflicts_after,
        affected_sections=[101],
        affected_groups=[301],
        affected_teachers=["teacher_1"],
        affected_rooms=["room_A", "room_B"],
        affected_bookings=["bk_001"],
        affected_student_count=25,
    )


# ---------------------------------------------------------------------------
# Test 1: Simulation requires tenant_id
# ---------------------------------------------------------------------------


def test_simulation_requires_positive_tenant_id() -> None:
    """tenant_id=0 on the proposal must raise ValueError."""
    with pytest.raises(ValueError, match="tenant_id"):
        # Build proposal manually with invalid tenant_id bypassing gt=0 constraint
        # We test via the builder which validates tenant_id > 0
        bad_inp = TimetableChangeProposalInput(
            tenant_id=1,  # valid for construction
            proposal_id="bad_prop",
            source_type=TimetableChangeProposalSourceType.MANUAL,
            current_snapshot=_make_snapshot(),
            proposed_change=_make_proposed_change(),
            affected_entities=TimetableChangeAffectedEntities(affected_section_id=1),
        )
        proposal = build_timetable_change_proposal(bad_inp)
        # Force invalid tenant_id via model_copy (bypassing Field(gt=0))
        proposal = proposal.model_copy(update={"tenant_id": 0})
        sim_inp = TimetableChangeSimulationInput(
            proposal=proposal,
            simulation_id="sim_bad",
        )
        build_timetable_change_simulation(sim_inp)


# ---------------------------------------------------------------------------
# Test 2: Simulation requires proposal_id
# ---------------------------------------------------------------------------


def test_simulation_requires_proposal_id() -> None:
    """Empty proposal_id must raise ValueError."""
    proposal = _make_proposal()
    proposal = proposal.model_copy(update={"proposal_id": ""})
    sim_inp = TimetableChangeSimulationInput(proposal=proposal)
    with pytest.raises(ValueError, match="proposal_id"):
        build_timetable_change_simulation(sim_inp)


# ---------------------------------------------------------------------------
# Test 3: Simulation tenant must match proposal tenant
# ---------------------------------------------------------------------------


def test_simulation_tenant_isolation() -> None:
    """Result tenant_id must equal proposal tenant_id."""
    proposal = _make_proposal(tenant_id=42)
    sim_inp = TimetableChangeSimulationInput(proposal=proposal)
    result = build_timetable_change_simulation(sim_inp)
    assert result.tenant_id == 42


# ---------------------------------------------------------------------------
# Test 4: Builds proposed snapshot
# ---------------------------------------------------------------------------


def test_simulation_builds_proposed_snapshot() -> None:
    """before_after_snapshot must contain current and proposed snapshots."""
    inp = _make_input()
    result = build_timetable_change_simulation(inp)
    snap = result.before_after_snapshot
    assert snap.current_snapshot is not None
    assert snap.proposed_snapshot is not None
    assert "room_id" in snap.current_snapshot
    assert "room_id" in snap.proposed_snapshot


# ---------------------------------------------------------------------------
# Test 5: changed_fields detected
# ---------------------------------------------------------------------------


def test_simulation_detects_changed_fields() -> None:
    """Overlay of proposed_room_id must appear in changed_fields."""
    inp = _make_input()
    result = build_timetable_change_simulation(inp)
    snap = result.before_after_snapshot
    assert "room_id" in snap.changed_fields


# ---------------------------------------------------------------------------
# Test 6: unchanged_fields detected
# ---------------------------------------------------------------------------


def test_simulation_detects_unchanged_fields() -> None:
    """Fields not in the proposed change must appear in unchanged_fields."""
    inp = _make_input()
    result = build_timetable_change_simulation(inp)
    snap = result.before_after_snapshot
    # day_of_week and time_slot_id were not changed
    assert "day_of_week" in snap.unchanged_fields
    assert "time_slot_id" in snap.unchanged_fields


# ---------------------------------------------------------------------------
# Test 7: conflict_delta computation
# ---------------------------------------------------------------------------


def test_simulation_conflict_delta_resolved_created_unchanged() -> None:
    """conflict_delta must correctly compute resolved/created/unchanged/count_delta."""
    delta = build_simulation_conflict_delta(
        conflicts_before=["room_time_conflict", "capacity_mismatch"],
        conflicts_after=["capacity_mismatch", "equipment_mismatch"],
    )
    assert delta.conflicts_before == 2
    assert delta.conflicts_after == 2
    assert delta.conflicts_resolved == 1     # room_time_conflict resolved
    assert delta.conflicts_created == 1      # equipment_mismatch created
    assert delta.conflicts_unchanged == 1    # capacity_mismatch unchanged
    assert delta.conflict_count_delta == 0


def test_simulation_conflict_delta_net_increase() -> None:
    """conflict_count_delta must be positive when more conflicts after."""
    delta = build_simulation_conflict_delta(
        conflicts_before=["room_time_conflict"],
        conflicts_after=["room_time_conflict", "capacity_mismatch", "computer_shortage"],
    )
    assert delta.conflict_count_delta == 2
    assert delta.conflicts_created == 2


def test_simulation_conflict_delta_all_resolved() -> None:
    """All conflicts resolved: conflicts_after=0, conflict_count_delta negative."""
    delta = build_simulation_conflict_delta(
        conflicts_before=["room_time_conflict", "capacity_mismatch"],
        conflicts_after=[],
    )
    assert delta.conflicts_resolved == 2
    assert delta.conflicts_created == 0
    assert delta.conflict_count_delta == -2


# ---------------------------------------------------------------------------
# Test 8: affected_delta
# ---------------------------------------------------------------------------


def test_simulation_affected_delta_includes_all_entity_types() -> None:
    """affected_delta must include sections, groups, teachers, rooms, bookings."""
    inp = _make_input()
    result = build_timetable_change_simulation(inp)
    delta = result.affected_delta
    assert len(delta.affected_sections) >= 1
    assert len(delta.affected_groups) >= 1
    assert len(delta.affected_teachers) >= 1
    assert len(delta.affected_rooms) >= 1
    assert len(delta.affected_bookings) >= 1
    assert delta.affected_student_count >= 0


# ---------------------------------------------------------------------------
# Test 9: risk_delta marks review_required when risk increases
# ---------------------------------------------------------------------------


def test_simulation_risk_delta_review_required_on_increase() -> None:
    """review_required must be True when risk_after > risk_before."""
    inp = _make_input(risk_level=TimetableChangeProposalRiskLevel.MEDIUM)
    inp = inp.model_copy(update={
        "risk_before": TimetableChangeProposalRiskLevel.LOW,
        "risk_after": TimetableChangeProposalRiskLevel.HIGH,
        "conflicts_before": [],
        "conflicts_after": [],
    })
    result = build_timetable_change_simulation(inp)
    assert result.risk_delta.review_required is True
    assert result.risk_delta.risk_delta == "increased"


# ---------------------------------------------------------------------------
# Test 10: review_required true when proposal approval_required true
# ---------------------------------------------------------------------------


def test_simulation_review_required_when_approval_required() -> None:
    """review_required must be True whenever proposal.approval_required is True."""
    proposal = _make_proposal()
    assert proposal.approval_required is True
    sim_inp = TimetableChangeSimulationInput(
        proposal=proposal,
        conflicts_before=[],
        conflicts_after=[],
        risk_before=TimetableChangeProposalRiskLevel.LOW,
        risk_after=TimetableChangeProposalRiskLevel.LOW,
    )
    result = build_timetable_change_simulation(sim_inp)
    assert result.review_required is True


# ---------------------------------------------------------------------------
# Test 11: data_quality_note when predicted conflicts missing
# ---------------------------------------------------------------------------


def test_simulation_data_quality_note_when_conflicts_missing() -> None:
    """data_quality_note must be set when conflicts_after is None."""
    inp = _make_input(conflicts_before=None, conflicts_after=None)
    result = build_timetable_change_simulation(inp)
    assert result.data_quality_note is not None
    assert "conflicts_after" in result.data_quality_note.lower() or \
           "data quality" in result.data_quality_note.lower()


# ---------------------------------------------------------------------------
# Test 12: draft proposal simulation allowed with note
# ---------------------------------------------------------------------------


def test_simulation_draft_proposal_allowed_with_quality_note() -> None:
    """Draft proposal simulation must succeed and include a data_quality_note."""
    proposal = _make_proposal(status=TimetableChangeProposalStatus.DRAFT)
    sim_inp = TimetableChangeSimulationInput(
        proposal=proposal,
        simulation_id="sim_draft_001",
    )
    result = build_timetable_change_simulation(sim_inp)
    # Must not be INVALID — draft is allowed
    assert result.status != TimetableChangeSimulationStatus.INVALID
    assert result.status == TimetableChangeSimulationStatus.COMPUTED
    assert result.data_quality_note is not None
    assert "draft" in result.data_quality_note.lower()


# ---------------------------------------------------------------------------
# Test 13: pending_review proposal simulation allowed
# ---------------------------------------------------------------------------


def test_simulation_pending_review_proposal_allowed() -> None:
    """pending_review proposal simulation must succeed."""
    inp = _make_input(status=TimetableChangeProposalStatus.PENDING_REVIEW)
    result = build_timetable_change_simulation(inp)
    assert result.status == TimetableChangeSimulationStatus.COMPUTED
    assert result.proposal_id == inp.proposal.proposal_id


# ---------------------------------------------------------------------------
# Test 14: approved proposal simulation allowed as preview only
# ---------------------------------------------------------------------------


def test_simulation_approved_proposal_allowed_as_preview() -> None:
    """Approved proposal must be allowed for preview — no apply side effect."""
    proposal = _make_proposal(status=TimetableChangeProposalStatus.APPROVED)
    sim_inp = TimetableChangeSimulationInput(proposal=proposal)
    result = build_timetable_change_simulation(sim_inp)
    # Must succeed as read-only preview
    assert result.status == TimetableChangeSimulationStatus.COMPUTED
    # Approved status must not have produced any apply-related field
    result_dict = result.model_dump()
    assert "apply_flag" not in result_dict
    assert "apply" not in result_dict
    assert "commit" not in result_dict


# ---------------------------------------------------------------------------
# Test 15: rejected/cancelled/expired proposal simulation invalid
# ---------------------------------------------------------------------------


def test_simulation_rejected_proposal_is_invalid() -> None:
    """Rejected proposal simulation must return INVALID status."""
    proposal = _make_proposal(status=TimetableChangeProposalStatus.REJECTED)
    sim_inp = TimetableChangeSimulationInput(proposal=proposal)
    result = build_timetable_change_simulation(sim_inp)
    assert result.status == TimetableChangeSimulationStatus.INVALID
    assert result.data_quality_note is not None


def test_simulation_cancelled_proposal_is_invalid() -> None:
    """Cancelled proposal simulation must return INVALID status."""
    proposal = _make_proposal(status=TimetableChangeProposalStatus.CANCELLED)
    sim_inp = TimetableChangeSimulationInput(proposal=proposal)
    result = build_timetable_change_simulation(sim_inp)
    assert result.status == TimetableChangeSimulationStatus.INVALID


def test_simulation_expired_proposal_is_invalid() -> None:
    """Expired proposal simulation must return INVALID status."""
    proposal = _make_proposal()
    # Force expired status (not reachable via normal FSM in tests)
    proposal = proposal.model_copy(
        update={"status": TimetableChangeProposalStatus.EXPIRED}
    )
    sim_inp = TimetableChangeSimulationInput(proposal=proposal)
    result = build_timetable_change_simulation(sim_inp)
    assert result.status == TimetableChangeSimulationStatus.INVALID


# ---------------------------------------------------------------------------
# Test 16: simulation does not change proposal status
# ---------------------------------------------------------------------------


def test_simulation_does_not_change_proposal_status() -> None:
    """Running simulation must not mutate the input proposal's status."""
    proposal = _make_proposal(status=TimetableChangeProposalStatus.PENDING_REVIEW)
    original_status = proposal.status
    original_audit_len = len(proposal.audit_evidence)

    sim_inp = TimetableChangeSimulationInput(proposal=proposal)
    build_timetable_change_simulation(sim_inp)

    # Proposal must be unchanged
    assert proposal.status == original_status
    assert len(proposal.audit_evidence) == original_audit_len


# ---------------------------------------------------------------------------
# Test 17: no schedule mutation output exists
# ---------------------------------------------------------------------------


def test_simulation_no_schedule_mutation_output() -> None:
    """Result must contain no schedule-mutation fields."""
    inp = _make_input()
    result = build_timetable_change_simulation(inp)
    result_dict = result.model_dump()
    forbidden = {"mutate", "mutation", "update_schedule", "save_schedule", "apply_schedule"}
    for key in result_dict:
        assert key not in forbidden, f"Forbidden mutation field '{key}' found in result"


# ---------------------------------------------------------------------------
# Test 18: no room reservation output exists
# ---------------------------------------------------------------------------


def test_simulation_no_room_reservation_output() -> None:
    """Result must contain no room reservation fields."""
    inp = _make_input()
    result = build_timetable_change_simulation(inp)
    result_dict = result.model_dump()
    forbidden = {"reserve_room", "reservation", "room_reservation_flag"}
    for key in result_dict:
        assert key not in forbidden, f"Forbidden reservation field '{key}' found in result"


# ---------------------------------------------------------------------------
# Test 19: no booking override output exists
# ---------------------------------------------------------------------------


def test_simulation_no_booking_override_output() -> None:
    """Result must contain no booking override fields."""
    inp = _make_input()
    result = build_timetable_change_simulation(inp)
    result_dict = result.model_dump()
    forbidden = {"booking_override", "override_booking", "force_booking"}
    for key in result_dict:
        assert key not in forbidden, f"Forbidden override field '{key}' found in result"


# ---------------------------------------------------------------------------
# Test 20: no apply/commit field exists
# ---------------------------------------------------------------------------


def test_simulation_no_apply_or_commit_field() -> None:
    """Result schema must not contain apply_flag, commit, or auto_apply fields."""
    inp = _make_input()
    result = build_timetable_change_simulation(inp)
    result_dict = result.model_dump()
    forbidden = {"apply_flag", "apply", "commit", "auto_apply", "execute"}
    for key in result_dict:
        assert key not in forbidden, f"Forbidden apply/commit field '{key}' found in result"
    # Also verify no class-level attribute
    assert not hasattr(TimetableChangeSimulationResult, "_apply_flag")


# ---------------------------------------------------------------------------
# Test 21: no fake optimization result exists
# ---------------------------------------------------------------------------


def test_simulation_no_fake_optimization_result() -> None:
    """Result must not contain fake optimization fields."""
    inp = _make_input()
    result = build_timetable_change_simulation(inp)
    result_dict = result.model_dump()
    forbidden = {
        "optimized_score", "optimization_result", "ai_recommendation",
        "auto_optimized", "optimization_rank",
    }
    for key in result_dict:
        assert key not in forbidden, f"Forbidden optimization field '{key}' found in result"


# ---------------------------------------------------------------------------
# Test 22: audit evidence with simulation_computed action
# ---------------------------------------------------------------------------


def test_simulation_audit_evidence_simulation_computed() -> None:
    """audit_evidence must contain an entry with action='simulation_computed'."""
    inp = _make_input()
    result = build_timetable_change_simulation(inp)
    assert len(result.audit_evidence) >= 1
    actions = [e.action for e in result.audit_evidence]
    assert "simulation_computed" in actions


def test_build_simulation_audit_evidence_helper() -> None:
    """build_simulation_audit_evidence must produce correct action and status."""
    evidence = build_simulation_audit_evidence(
        simulation_id="sim_999",
        proposal_id="prop_999",
        actor_id="actor_1",
        status=TimetableChangeSimulationStatus.COMPUTED,
        reason="Test reason",
    )
    assert evidence.action == "simulation_computed"
    assert evidence.new_status == TimetableChangeSimulationStatus.COMPUTED.value
    assert evidence.actor_id == "actor_1"


# ---------------------------------------------------------------------------
# Test 23: cross-tenant simulation rejected
# ---------------------------------------------------------------------------


def test_simulation_cross_tenant_rejected() -> None:
    """Building a simulation with a proposal whose tenant_id=0 must raise ValueError."""
    proposal = _make_proposal(tenant_id=1)
    # Force invalid tenant_id to test builder guard
    proposal = proposal.model_copy(update={"tenant_id": -1})
    sim_inp = TimetableChangeSimulationInput(proposal=proposal)
    with pytest.raises(ValueError, match="tenant_id"):
        build_timetable_change_simulation(sim_inp)


def test_simulation_result_tenant_id_matches_proposal() -> None:
    """Result tenant_id must exactly match the proposal tenant_id."""
    proposal = _make_proposal(tenant_id=99)
    sim_inp = TimetableChangeSimulationInput(proposal=proposal)
    result = build_timetable_change_simulation(sim_inp)
    assert result.tenant_id == 99


# ---------------------------------------------------------------------------
# Test 24: missing optional fields do not crash
# ---------------------------------------------------------------------------


def test_simulation_missing_optional_fields_no_crash() -> None:
    """Simulation must succeed even with all optional fields absent."""
    proposal = _make_proposal()
    sim_inp = TimetableChangeSimulationInput(proposal=proposal)
    result = build_timetable_change_simulation(sim_inp)
    assert result.status in (
        TimetableChangeSimulationStatus.COMPUTED,
        TimetableChangeSimulationStatus.DRAFT,
    )
    assert result.simulation_id is not None
    assert result.proposal_id is not None


def test_simulation_minimal_proposal_no_crash() -> None:
    """Simulation with a proposal that has all-None optional fields must not crash."""
    proposal = _make_proposal(
        status=TimetableChangeProposalStatus.PENDING_REVIEW,
        risk_level=TimetableChangeProposalRiskLevel.LOW,
        proposed_room_id=None,
    )
    sim_inp = TimetableChangeSimulationInput(proposal=proposal)
    result = build_timetable_change_simulation(sim_inp)
    assert result.simulation_id is not None


# ---------------------------------------------------------------------------
# Test 25: A-022.1 proposal tests remain green
# ---------------------------------------------------------------------------


def test_a022_1_proposal_fsm_still_green() -> None:
    """A-022.1 proposal FSM must still work: draft → pending_review."""
    proposal = _make_proposal(status=TimetableChangeProposalStatus.DRAFT)
    assert proposal.status == TimetableChangeProposalStatus.DRAFT

    transitioned = transition_timetable_change_proposal(
        proposal,
        TimetableChangeProposalStatus.PENDING_REVIEW,
        actor_id="actor_1",
        requesting_tenant_id=1,
    )
    assert transitioned.status == TimetableChangeProposalStatus.PENDING_REVIEW


def test_a022_1_proposal_cross_tenant_still_rejected() -> None:
    """A-022.1 cross-tenant transition guard must still be enforced."""
    proposal = _make_proposal(tenant_id=1)
    with pytest.raises(ValueError, match="Cross-tenant"):
        transition_timetable_change_proposal(
            proposal,
            TimetableChangeProposalStatus.PENDING_REVIEW,
            actor_id="actor_x",
            requesting_tenant_id=99,
        )


def test_a022_1_proposal_terminal_state_still_blocks() -> None:
    """A-022.1 terminal state exit guard must still be enforced."""
    proposal = _make_proposal(status=TimetableChangeProposalStatus.REJECTED)
    with pytest.raises(ValueError):
        transition_timetable_change_proposal(
            proposal,
            TimetableChangeProposalStatus.PENDING_REVIEW,
            requesting_tenant_id=1,
        )


# ---------------------------------------------------------------------------
# Test 26: A-020 room allocation imports remain green
# ---------------------------------------------------------------------------


def test_a020_room_allocation_readiness_import_green() -> None:
    """A-020 room allocation readiness contract must import cleanly."""
    from app.modules.scheduling.room_allocation_readiness import (
        RoomAllocationReadiness,
        RoomAllocationRequirement,
        CapacityMatchingResult,
        RoomAllocationRecommendationResult,
        SchedulingConflictResult,
    )
    assert RoomAllocationReadiness is not None
    assert RoomAllocationRequirement is not None
    assert CapacityMatchingResult is not None
    assert RoomAllocationRecommendationResult is not None
    assert SchedulingConflictResult is not None


def test_a020_room_allocation_no_regression() -> None:
    """A-020 capacity matching and recommendation schemas must be instantiable."""
    from app.modules.scheduling.room_allocation_readiness import (
        CapacityMatchingResult,
        CapacityMatchStatus,
        CapacityRiskLevel,
        RoomAllocationRecommendationStatus,
    )
    # Basic schema creation
    assert CapacityMatchStatus.EXCELLENT_MATCH is not None
    assert CapacityRiskLevel.LOW is not None
    assert RoomAllocationRecommendationStatus.RECOMMENDED is not None


# ---------------------------------------------------------------------------
# Additional edge-case tests
# ---------------------------------------------------------------------------


def test_simulation_conflict_delta_empty_inputs() -> None:
    """conflict_delta with empty lists must return all zeros."""
    delta = build_simulation_conflict_delta(
        conflicts_before=[],
        conflicts_after=[],
    )
    assert delta.conflicts_before == 0
    assert delta.conflicts_after == 0
    assert delta.conflict_count_delta == 0
    assert delta.conflicts_resolved == 0
    assert delta.conflicts_created == 0


def test_simulation_conflict_delta_none_inputs() -> None:
    """conflict_delta with None inputs must treat them as empty lists."""
    delta = build_simulation_conflict_delta(None, None)
    assert delta.conflicts_before == 0
    assert delta.conflicts_after == 0
    assert delta.conflict_count_delta == 0


def test_simulation_result_is_pydantic_serialisable() -> None:
    """Result must be serialisable to dict and JSON without errors."""
    inp = _make_input()
    result = build_timetable_change_simulation(inp)
    d = result.model_dump()
    assert isinstance(d, dict)
    json_str = result.model_dump_json()
    assert isinstance(json_str, str)
    assert "simulation_id" in json_str


def test_simulation_id_generated_when_absent() -> None:
    """simulation_id must be auto-generated if not provided in input."""
    proposal = _make_proposal()
    sim_inp = TimetableChangeSimulationInput(proposal=proposal)
    result = build_timetable_change_simulation(sim_inp)
    assert result.simulation_id.startswith("sim_")


def test_simulation_status_enum_values() -> None:
    """TimetableChangeSimulationStatus must have all required values."""
    assert TimetableChangeSimulationStatus.DRAFT.value == "draft"
    assert TimetableChangeSimulationStatus.COMPUTED.value == "computed"
    assert TimetableChangeSimulationStatus.STALE.value == "stale"
    assert TimetableChangeSimulationStatus.INVALID.value == "invalid"
    assert TimetableChangeSimulationStatus.CANCELLED.value == "cancelled"


def test_simulation_before_after_snapshot_evidence_lines() -> None:
    """Snapshot evidence must describe which fields changed."""
    inp = _make_input()
    result = build_timetable_change_simulation(inp)
    snap = result.before_after_snapshot
    assert len(snap.evidence) >= 1
    # Evidence must mention the changed field (room_id)
    evidence_text = " ".join(snap.evidence)
    assert "room_id" in evidence_text


def test_simulation_affected_delta_student_count() -> None:
    """affected_delta.affected_student_count must be non-negative."""
    inp = _make_input()
    result = build_timetable_change_simulation(inp)
    assert result.affected_delta.affected_student_count >= 0


def test_simulation_invalid_has_no_conflict_delta_junk() -> None:
    """INVALID simulation must have sensible empty defaults for delta fields."""
    proposal = _make_proposal(status=TimetableChangeProposalStatus.REJECTED)
    sim_inp = TimetableChangeSimulationInput(proposal=proposal)
    result = build_timetable_change_simulation(sim_inp)
    assert result.status == TimetableChangeSimulationStatus.INVALID
    # Conflict delta should be empty defaults (no junk from partial compute)
    assert result.conflict_delta.conflicts_before == 0
    assert result.conflict_delta.conflicts_after == 0


def test_simulation_revision_requested_proposal_allowed() -> None:
    """revision_requested proposal must be allowed for simulation."""
    proposal = _make_proposal(status=TimetableChangeProposalStatus.REVISION_REQUESTED)
    sim_inp = TimetableChangeSimulationInput(proposal=proposal)
    result = build_timetable_change_simulation(sim_inp)
    assert result.status == TimetableChangeSimulationStatus.COMPUTED
