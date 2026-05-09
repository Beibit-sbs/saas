"""A-022.4 — Human Approval Queue / Decision Contract tests."""
from __future__ import annotations

import pytest

from app.modules.scheduling.room_allocation_readiness import (
    RoomAllocationRequirement,
    RoomCapability,
    build_room_allocation_recommendation_result,
)
from app.modules.scheduling.timetable_approval_queue import (
    TimetableApprovalDecision,
    TimetableApprovalDecisionStatus,
    TimetableApprovalPriority,
    TimetableApprovalQueueInput,
    TimetableApprovalReviewStatus,
    build_timetable_approval_queue_item,
    record_timetable_approval_decision,
)
from app.modules.scheduling.timetable_change_proposal import (
    TimetableChangeAffectedEntities,
    TimetableChangeCurrentSnapshot,
    TimetableChangeProposalRiskLevel,
    TimetableChangeProposalSourceType,
    TimetableChangeProposalStatus,
    TimetableChangeProposedChange,
    TimetableChangeType,
    TimetableChangeProposalInput,
    build_timetable_change_proposal,
    transition_timetable_change_proposal,
)
from app.modules.scheduling.timetable_change_simulation import (
    TimetableChangeSimulationInput,
    build_timetable_change_simulation,
)
from app.modules.scheduling.timetable_recommendation_bridge import (
    RoomRecommendationToProposalBridgeInput,
    build_proposal_from_room_allocation_recommendation,
)


def _snapshot(room_id: str = "ROOM-A") -> TimetableChangeCurrentSnapshot:
    return TimetableChangeCurrentSnapshot(
        section_id=1101,
        course_id=2201,
        group_id=3301,
        teacher_id="teacher-1",
        room_id=room_id,
        day_of_week="monday",
        time_slot_id=2,
        start_time="09:00:00",
        end_time="10:30:00",
        room_capacity=40,
        students_count=36,
        source_entity_type="section",
        source_entity_id=1101,
    )


def _affected() -> TimetableChangeAffectedEntities:
    return TimetableChangeAffectedEntities(
        affected_section_id=1101,
        affected_course_id=2201,
        affected_group_id=3301,
        affected_teacher_id="teacher-1",
        affected_room_id="ROOM-A",
        affected_student_count=36,
    )


def _proposal(
    *,
    tenant_id: int = 1,
    risk: TimetableChangeProposalRiskLevel = TimetableChangeProposalRiskLevel.MEDIUM,
) -> object:
    inp = TimetableChangeProposalInput(
        tenant_id=tenant_id,
        proposal_id="prop_a0224_001",
        source_type=TimetableChangeProposalSourceType.MANUAL,
        current_snapshot=_snapshot(),
        proposed_change=TimetableChangeProposedChange(
            change_type=TimetableChangeType.ROOM_CHANGE,
            proposed_room_id="ROOM-B",
            reason="Human review required for room change",
        ),
        affected_entities=_affected(),
        risk_level=risk,
        created_by="planner-1",
    )
    proposal = build_timetable_change_proposal(inp)
    return transition_timetable_change_proposal(
        proposal,
        TimetableChangeProposalStatus.PENDING_REVIEW,
        actor_id="planner-1",
        requesting_tenant_id=tenant_id,
    )


def _simulation(proposal) -> object:
    sim_inp = TimetableChangeSimulationInput(
        proposal=proposal,
        simulation_id="sim_a0224_001",
        actor_id="planner-1",
        conflicts_before=["room_time_conflict"],
        conflicts_after=[],
        affected_sections=[1101],
        affected_groups=[3301],
        affected_teachers=["teacher-1"],
        affected_rooms=["ROOM-A", "ROOM-B"],
        affected_bookings=["bk-1"],
        affected_student_count=36,
    )
    return build_timetable_change_simulation(sim_inp)


def _queue_item(
    *,
    proposal=None,
    simulation=None,
    authoritative_tenant_id=None,
):
    proposal = proposal or _proposal()
    return build_timetable_approval_queue_item(
        TimetableApprovalQueueInput(
            proposal=proposal,
            simulation=simulation,
            created_by="planner-1",
            assigned_to="reviewer-queue",
            authoritative_tenant_id=authoritative_tenant_id,
        )
    )


def _decision(
    queue_item,
    *,
    status: TimetableApprovalDecisionStatus,
    reviewer_id: str | None = "reviewer-1",
    reviewer_note: str | None = "looks good",
    tenant_id: int | None = None,
) -> TimetableApprovalDecision:
    return TimetableApprovalDecision(
        tenant_id=tenant_id or queue_item.tenant_id,
        queue_item_id=queue_item.queue_item_id,
        proposal_id=queue_item.proposal_id,
        decision_status=status,
        reviewer_id=reviewer_id,
        reviewer_note=reviewer_note,
        decision_reason="decision record",
    )


# 1

def test_queue_item_requires_tenant_id() -> None:
    proposal = _proposal().model_copy(update={"tenant_id": 0})
    with pytest.raises(ValueError, match="tenant_id"):
        _queue_item(proposal=proposal)


# 2

def test_queue_item_requires_proposal_id() -> None:
    proposal = _proposal().model_copy(update={"proposal_id": ""})
    with pytest.raises(ValueError, match="proposal_id"):
        _queue_item(proposal=proposal)


# 3

def test_queue_item_can_reference_simulation_id() -> None:
    proposal = _proposal()
    sim = _simulation(proposal)
    item = _queue_item(proposal=proposal, simulation=sim)
    assert item.simulation_id == "sim_a0224_001"


# 4

def test_queue_item_built_from_timetable_change_proposal() -> None:
    proposal = _proposal()
    item = _queue_item(proposal=proposal)
    assert item.proposal_id == proposal.proposal_id
    assert item.review_status == TimetableApprovalReviewStatus.QUEUED


# 5

def test_queue_item_built_from_proposal_and_simulation() -> None:
    proposal = _proposal()
    sim = _simulation(proposal)
    item = _queue_item(proposal=proposal, simulation=sim)
    assert item.simulation_id == sim.simulation_id
    assert "simulation_id=" in item.evidence_summary


# 6

def test_priority_derived_from_risk_levels() -> None:
    low = _queue_item(proposal=_proposal(risk=TimetableChangeProposalRiskLevel.LOW))
    med = _queue_item(proposal=_proposal(risk=TimetableChangeProposalRiskLevel.MEDIUM))
    high = _queue_item(proposal=_proposal(risk=TimetableChangeProposalRiskLevel.HIGH))
    critical = _queue_item(proposal=_proposal(risk=TimetableChangeProposalRiskLevel.CRITICAL))

    assert low.priority == TimetableApprovalPriority.LOW
    assert med.priority == TimetableApprovalPriority.MEDIUM
    assert high.priority == TimetableApprovalPriority.HIGH
    assert critical.priority == TimetableApprovalPriority.CRITICAL


# 7

def test_review_required_defaults_true() -> None:
    item = _queue_item()
    assert item.review_required is True


# 8

def test_approve_decision_requires_reviewer_id() -> None:
    item = _queue_item()
    decision = _decision(item, status=TimetableApprovalDecisionStatus.APPROVED, reviewer_id=None)
    with pytest.raises(ValueError, match="reviewer_id"):
        record_timetable_approval_decision(queue_item=item, decision=decision)


# 9

def test_reject_decision_requires_reviewer_id_and_note() -> None:
    item = _queue_item()
    decision_missing_id = _decision(
        item,
        status=TimetableApprovalDecisionStatus.REJECTED,
        reviewer_id=None,
        reviewer_note="reason",
    )
    with pytest.raises(ValueError, match="reviewer_id"):
        record_timetable_approval_decision(queue_item=item, decision=decision_missing_id)

    decision_missing_note = _decision(
        item,
        status=TimetableApprovalDecisionStatus.REJECTED,
        reviewer_id="reviewer-1",
        reviewer_note=None,
    )
    with pytest.raises(ValueError, match="reviewer_note"):
        record_timetable_approval_decision(queue_item=item, decision=decision_missing_note)


# 10

def test_revision_requested_requires_reviewer_id_and_note() -> None:
    item = _queue_item()
    decision = _decision(
        item,
        status=TimetableApprovalDecisionStatus.REVISION_REQUESTED,
        reviewer_id="reviewer-1",
        reviewer_note=None,
    )
    with pytest.raises(ValueError, match="reviewer_note"):
        record_timetable_approval_decision(queue_item=item, decision=decision)


# 11

def test_high_or_critical_approval_requires_reviewer_note() -> None:
    for risk in (TimetableChangeProposalRiskLevel.HIGH, TimetableChangeProposalRiskLevel.CRITICAL):
        item = _queue_item(proposal=_proposal(risk=risk))
        decision = _decision(
            item,
            status=TimetableApprovalDecisionStatus.APPROVED,
            reviewer_id="reviewer-1",
            reviewer_note=None,
        )
        with pytest.raises(ValueError, match="high/critical"):
            record_timetable_approval_decision(queue_item=item, decision=decision)


# 12

def test_approved_creates_decision_record_only() -> None:
    item = _queue_item()
    result = record_timetable_approval_decision(
        queue_item=item,
        decision=_decision(item, status=TimetableApprovalDecisionStatus.APPROVED),
    )
    assert result.decision_recorded is True
    assert result.queue_item.review_status == TimetableApprovalReviewStatus.DECISION_RECORDED


# 13

def test_approved_does_not_mutate_schedule() -> None:
    item = _queue_item()
    result = record_timetable_approval_decision(
        queue_item=item,
        decision=_decision(item, status=TimetableApprovalDecisionStatus.APPROVED),
    )
    payload = result.queue_item.model_dump()
    for forbidden in {"schedule_applied", "mutate", "apply_schedule"}:
        assert forbidden not in payload


# 14

def test_approved_does_not_reserve_room() -> None:
    item = _queue_item()
    result = record_timetable_approval_decision(
        queue_item=item,
        decision=_decision(item, status=TimetableApprovalDecisionStatus.APPROVED),
    )
    payload = result.queue_item.model_dump()
    for forbidden in {"reserve_room", "room_reservation", "reservation_flag"}:
        assert forbidden not in payload


# 15

def test_approved_does_not_override_booking() -> None:
    item = _queue_item()
    result = record_timetable_approval_decision(
        queue_item=item,
        decision=_decision(item, status=TimetableApprovalDecisionStatus.APPROVED),
    )
    payload = result.queue_item.model_dump()
    for forbidden in {"booking_override", "override_booking", "force_booking"}:
        assert forbidden not in payload


# 16

def test_approved_does_not_auto_apply() -> None:
    item = _queue_item()
    result = record_timetable_approval_decision(
        queue_item=item,
        decision=_decision(item, status=TimetableApprovalDecisionStatus.APPROVED),
    )
    payload = result.queue_item.model_dump()
    for forbidden in {"auto_apply", "apply", "commit", "execute"}:
        assert forbidden not in payload


# 17

def test_rejected_is_terminal() -> None:
    item = _queue_item()
    result = record_timetable_approval_decision(
        queue_item=item,
        decision=_decision(item, status=TimetableApprovalDecisionStatus.REJECTED, reviewer_note="not valid"),
    )
    assert result.queue_item.review_status == TimetableApprovalReviewStatus.DECISION_RECORDED


# 18

def test_cancelled_is_terminal() -> None:
    item = _queue_item()
    result = record_timetable_approval_decision(
        queue_item=item,
        decision=_decision(item, status=TimetableApprovalDecisionStatus.CANCELLED, reviewer_id=None, reviewer_note=None),
    )
    assert result.queue_item.review_status == TimetableApprovalReviewStatus.CANCELLED


# 19

def test_terminal_queue_item_cannot_be_decided_again() -> None:
    item = _queue_item()
    first = record_timetable_approval_decision(
        queue_item=item,
        decision=_decision(item, status=TimetableApprovalDecisionStatus.APPROVED),
    )
    with pytest.raises(ValueError, match="Terminal queue item"):
        record_timetable_approval_decision(
            queue_item=first.queue_item,
            decision=_decision(first.queue_item, status=TimetableApprovalDecisionStatus.REJECTED, reviewer_note="late reject"),
        )


# 20

def test_cross_tenant_queue_item_rejected() -> None:
    proposal = _proposal(tenant_id=2)
    with pytest.raises(ValueError, match="Cross-tenant queue rejected"):
        _queue_item(proposal=proposal, authoritative_tenant_id=1)


# 21

def test_cross_tenant_decision_rejected() -> None:
    item = _queue_item()
    bad = _decision(item, status=TimetableApprovalDecisionStatus.APPROVED, tenant_id=item.tenant_id + 1)
    with pytest.raises(ValueError, match="Cross-tenant decision"):
        record_timetable_approval_decision(queue_item=item, decision=bad)


# 22

def test_audit_evidence_produced_when_queue_item_created() -> None:
    item = _queue_item()
    actions = [a.action for a in item.audit_evidence]
    assert "approval_queue_item_created" in actions


# 23

def test_audit_evidence_produced_when_decision_recorded() -> None:
    item = _queue_item()
    result = record_timetable_approval_decision(
        queue_item=item,
        decision=_decision(item, status=TimetableApprovalDecisionStatus.APPROVED),
    )
    actions = [a.action for a in result.queue_item.audit_evidence]
    assert "approval_decision_recorded" in actions


# 24

def test_invalid_decision_rejected() -> None:
    item = _queue_item()
    bad = _decision(item, status=TimetableApprovalDecisionStatus.PENDING)
    with pytest.raises(ValueError, match="Invalid decision status"):
        record_timetable_approval_decision(queue_item=item, decision=bad)


# 25

def test_proposal_status_not_mutated_without_explicit_fsm_helper() -> None:
    proposal = _proposal()
    item = _queue_item(proposal=proposal)
    _ = record_timetable_approval_decision(
        queue_item=item,
        decision=_decision(item, status=TimetableApprovalDecisionStatus.APPROVED),
        proposal=proposal,
        apply_proposal_fsm=False,
    )
    assert proposal.status == TimetableChangeProposalStatus.PENDING_REVIEW


# 26

def test_explicit_fsm_helper_can_update_proposal_without_applying_schedule() -> None:
    proposal = _proposal()
    item = _queue_item(proposal=proposal)
    result = record_timetable_approval_decision(
        queue_item=item,
        decision=_decision(item, status=TimetableApprovalDecisionStatus.APPROVED),
        proposal=proposal,
        apply_proposal_fsm=True,
    )
    assert result.proposal is not None
    assert result.proposal.status == TimetableChangeProposalStatus.APPROVED
    payload = result.proposal.model_dump()
    assert "apply_flag" not in payload
    assert "schedule_applied" not in payload


# 27

def test_no_apply_or_commit_field_exists() -> None:
    item = _queue_item()
    payload = item.model_dump()
    for forbidden in {"apply", "apply_flag", "commit", "execute"}:
        assert forbidden not in payload


# 28

def test_no_fake_optimization_result_exists() -> None:
    item = _queue_item()
    payload = item.model_dump()
    for forbidden in {"optimization_result", "optimized_score", "auto_optimized"}:
        assert forbidden not in payload


# 29

def test_a022_1_proposal_contract_remains_green() -> None:
    proposal = _proposal()
    moved = transition_timetable_change_proposal(
        proposal,
        TimetableChangeProposalStatus.APPROVED,
        requesting_tenant_id=proposal.tenant_id,
        reviewer_id="reviewer-1",
        reviewer_note="approved",
    )
    assert moved.status == TimetableChangeProposalStatus.APPROVED


# 30

def test_a022_2_simulation_contract_remains_green() -> None:
    proposal = _proposal()
    sim = _simulation(proposal)
    assert sim.proposal_id == proposal.proposal_id
    assert sim.review_required is True


# 31

def test_a022_3_bridge_contract_remains_green() -> None:
    requirement_payload = RoomAllocationRequirement(
        section_id=5001,
        course_id=7001,
        group_id=9001,
        teacher_id="teacher-1",
        students_count=40,
        max_capacity=50,
        required_room_type="computer_lab",
        required_computers=20,
        equipment_required=["projector"],
        restrictions_required=["exam_enabled"],
    )
    capability_payload = RoomCapability(
        tenant_id=1,
        room_id="ROOM-B",
        room_code="ROOM-B",
        room_name="ROOM-B",
        room_type="computer_lab",
        capacity=45,
        computers_count=25,
        equipment_available=["projector", "whiteboard"],
        supported_lesson_types=["lecture", "lab"],
        restrictions=["exam_enabled"],
        availability_status="available",
        booking_status="released",
        maintenance_status="ok",
        is_active=True,
        source_entity_type="campus_room",
        source_entity_id="entity-ROOM-B",
    )
    rec = build_room_allocation_recommendation_result(
        tenant_id=1,
        requirement=requirement_payload,
        candidates=[capability_payload],
    )
    bridge_result = build_proposal_from_room_allocation_recommendation(
        RoomRecommendationToProposalBridgeInput(
            tenant_id=1,
            recommendation_result=rec,
            current_snapshot=_snapshot(),
            created_by="actor-1",
            reason="Bridge from recommendation",
            source_entity_id="rec-a0224",
        )
    )
    assert bridge_result.proposal.proposal_id


# 32

def test_tenant_security_contract_remains_fail_closed() -> None:
    proposal = _proposal(tenant_id=5)
    item = _queue_item(proposal=proposal)
    bad_decision = _decision(item, status=TimetableApprovalDecisionStatus.APPROVED, tenant_id=7)
    with pytest.raises(ValueError):
        record_timetable_approval_decision(queue_item=item, decision=bad_decision)
