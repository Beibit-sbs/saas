"""A-022.1: Timetable Change Proposal Contract — test suite.

27 required tests covering:
- Schema validation (tenant_id, current_snapshot, proposed_change, affected_entities)
- Default field values (approval_required, status)
- Build helpers from room recommendation source and conflict source
- Manual proposal requirement
- FSM transitions (valid and invalid)
- Cross-tenant / security controls
- Audit evidence tracking
- No schedule mutation / no reservation / no auto-apply contract assertions
- A-020 recommendation compatibility (no mutation)
- Tenant/security regression
"""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.modules.scheduling.timetable_change_proposal import (
    TimetableChangeAffectedEntities,
    TimetableChangeAuditEvidence,
    TimetableChangeCurrentSnapshot,
    TimetableChangeProposal,
    TimetableChangeProposalDecision,
    TimetableChangeProposalInput,
    TimetableChangeProposalRiskLevel,
    TimetableChangeProposalSourceType,
    TimetableChangeProposalStatus,
    TimetableChangeProposedChange,
    TimetableChangeType,
    apply_proposal_decision,
    build_proposal_audit_evidence,
    build_timetable_change_proposal,
    proposal_from_conflict,
    proposal_from_room_recommendation,
    transition_timetable_change_proposal,
)


# ---------------------------------------------------------------------------
# Test-data factories
# ---------------------------------------------------------------------------


def _snapshot(section_id: int = 1, course_id: int = 10, group_id: int = 5) -> TimetableChangeCurrentSnapshot:
    return TimetableChangeCurrentSnapshot(
        section_id=section_id,
        course_id=course_id,
        group_id=group_id,
        teacher_id=42,
        room_id=99,
        day_of_week="monday",
        time_slot_id=1,
        room_capacity=30,
        students_count=25,
        source_entity_type="section",
        source_entity_id=section_id,
    )


def _affected(section_id: int = 1, course_id: int = 10) -> TimetableChangeAffectedEntities:
    return TimetableChangeAffectedEntities(
        affected_section_id=section_id,
        affected_course_id=course_id,
        affected_group_id=5,
        affected_teacher_id=42,
        affected_room_id=99,
        affected_student_count=25,
    )


def _manual_proposal(tenant_id: int = 100) -> TimetableChangeProposal:
    inp = TimetableChangeProposalInput(
        tenant_id=tenant_id,
        source_type=TimetableChangeProposalSourceType.MANUAL,
        current_snapshot=_snapshot(),
        proposed_change=TimetableChangeProposedChange(
            change_type=TimetableChangeType.ROOM_CHANGE,
            proposed_room_id=200,
            reason="Room is too small for the group",
        ),
        affected_entities=_affected(),
        created_by=1,
    )
    return build_timetable_change_proposal(inp)


# ---------------------------------------------------------------------------
# 1. Schema validation — tenant_id required
# ---------------------------------------------------------------------------


def test_01_proposal_requires_tenant_id():
    """Proposal with missing tenant_id must fail validation."""
    with pytest.raises((ValidationError, ValueError)):
        TimetableChangeProposalInput(
            source_type=TimetableChangeProposalSourceType.MANUAL,
            current_snapshot=_snapshot(),
            proposed_change=TimetableChangeProposedChange(
                change_type=TimetableChangeType.ROOM_CHANGE,
                reason="test",
            ),
            affected_entities=_affected(),
            # tenant_id intentionally omitted — should fail
        )


def test_01b_proposal_rejects_zero_tenant_id():
    """Proposal with tenant_id=0 must raise ValueError."""
    with pytest.raises((ValidationError, ValueError)):
        TimetableChangeProposalInput(
            tenant_id=0,
            source_type=TimetableChangeProposalSourceType.MANUAL,
            current_snapshot=_snapshot(),
            proposed_change=TimetableChangeProposedChange(
                change_type=TimetableChangeType.ROOM_CHANGE,
                reason="test",
            ),
            affected_entities=_affected(),
        )


# ---------------------------------------------------------------------------
# 2. Schema validation — current_snapshot required
# ---------------------------------------------------------------------------


def test_02_proposal_requires_current_snapshot():
    """Proposal without current_snapshot must fail validation."""
    with pytest.raises((ValidationError, TypeError)):
        TimetableChangeProposalInput(
            tenant_id=100,
            source_type=TimetableChangeProposalSourceType.MANUAL,
            # current_snapshot intentionally omitted
            proposed_change=TimetableChangeProposedChange(
                change_type=TimetableChangeType.ROOM_CHANGE,
                reason="test",
            ),
            affected_entities=_affected(),
        )


# ---------------------------------------------------------------------------
# 3. Schema validation — proposed_change required
# ---------------------------------------------------------------------------


def test_03_proposal_requires_proposed_change():
    """Proposal without proposed_change must fail validation."""
    with pytest.raises((ValidationError, TypeError)):
        TimetableChangeProposalInput(
            tenant_id=100,
            source_type=TimetableChangeProposalSourceType.MANUAL,
            current_snapshot=_snapshot(),
            # proposed_change intentionally omitted
            affected_entities=_affected(),
        )


# ---------------------------------------------------------------------------
# 4. Schema validation — affected_entities required
# ---------------------------------------------------------------------------


def test_04_proposal_requires_affected_entities():
    """Proposal without affected_entities must fail validation."""
    with pytest.raises((ValidationError, TypeError)):
        TimetableChangeProposalInput(
            tenant_id=100,
            source_type=TimetableChangeProposalSourceType.MANUAL,
            current_snapshot=_snapshot(),
            proposed_change=TimetableChangeProposedChange(
                change_type=TimetableChangeType.ROOM_CHANGE,
                reason="test",
            ),
            # affected_entities intentionally omitted
        )


# ---------------------------------------------------------------------------
# 5. Default: approval_required is True
# ---------------------------------------------------------------------------


def test_05_approval_required_defaults_to_true():
    """approval_required must default to True (no auto-approval pathway)."""
    proposal = _manual_proposal()
    assert proposal.approval_required is True


# ---------------------------------------------------------------------------
# 6. Build from room recommendation source
# ---------------------------------------------------------------------------


def test_06_build_proposal_from_room_recommendation_source():
    """Proposal built from a room recommendation must reference the recommendation."""
    inp = TimetableChangeProposalInput(
        tenant_id=100,
        source_type=TimetableChangeProposalSourceType.ROOM_ALLOCATION_RECOMMENDATION,
        source_recommendation_id="reco_001",
        current_snapshot=_snapshot(),
        proposed_change=TimetableChangeProposedChange(
            change_type=TimetableChangeType.ROOM_CHANGE,
            proposed_room_id=300,
            reason="Better capacity match from A-020 recommendation",
        ),
        affected_entities=_affected(),
        created_by=1,
    )
    proposal = build_timetable_change_proposal(inp)

    assert proposal.source_type == TimetableChangeProposalSourceType.ROOM_ALLOCATION_RECOMMENDATION
    assert proposal.source_recommendation_id == "reco_001"
    assert proposal.tenant_id == 100
    assert proposal.status == TimetableChangeProposalStatus.DRAFT


# ---------------------------------------------------------------------------
# 7. Build from conflict source
# ---------------------------------------------------------------------------


def test_07_build_proposal_from_conflict_source():
    """Proposal built from a conflict must reference the conflict ID."""
    inp = TimetableChangeProposalInput(
        tenant_id=100,
        source_type=TimetableChangeProposalSourceType.CONFLICT_RESOLUTION,
        source_conflict_id="conflict_007",
        current_snapshot=_snapshot(),
        proposed_change=TimetableChangeProposedChange(
            change_type=TimetableChangeType.ROOM_CHANGE,
            reason="Room double-booking conflict",
        ),
        affected_entities=_affected(),
        created_by=2,
    )
    proposal = build_timetable_change_proposal(inp)

    assert proposal.source_type == TimetableChangeProposalSourceType.CONFLICT_RESOLUTION
    assert proposal.source_conflict_id == "conflict_007"
    assert proposal.status == TimetableChangeProposalStatus.DRAFT


# ---------------------------------------------------------------------------
# 8. Manual proposal requires explicit reason
# ---------------------------------------------------------------------------


def test_08_manual_proposal_requires_reason():
    """Manual proposals without a reason must be rejected by the build helper."""
    inp = TimetableChangeProposalInput(
        tenant_id=100,
        source_type=TimetableChangeProposalSourceType.MANUAL,
        current_snapshot=_snapshot(),
        proposed_change=TimetableChangeProposedChange(
            change_type=TimetableChangeType.ROOM_CHANGE,
            reason="",   # empty reason — must fail
        ),
        affected_entities=_affected(),
    )
    with pytest.raises(ValueError, match="[Mm]anual"):
        build_timetable_change_proposal(inp)


# ---------------------------------------------------------------------------
# 9. FSM: draft → pending_review (valid)
# ---------------------------------------------------------------------------


def test_09_draft_to_pending_review_valid():
    """draft → pending_review must succeed."""
    proposal = _manual_proposal()
    updated = transition_timetable_change_proposal(
        proposal,
        TimetableChangeProposalStatus.PENDING_REVIEW,
        actor_id=1,
        reason="Submitting for review",
    )
    assert updated.status == TimetableChangeProposalStatus.PENDING_REVIEW


# ---------------------------------------------------------------------------
# 10. FSM: pending_review → approved (does NOT apply schedule)
# ---------------------------------------------------------------------------


def test_10_pending_review_to_approved_does_not_apply_schedule():
    """approved status must be reachable and must not produce any schedule mutation."""
    proposal = _manual_proposal()
    proposal = transition_timetable_change_proposal(
        proposal, TimetableChangeProposalStatus.PENDING_REVIEW, actor_id=1
    )
    proposal = transition_timetable_change_proposal(
        proposal, TimetableChangeProposalStatus.APPROVED,
        reviewer_id=99,
        reason="Looks good",
    )

    assert proposal.status == TimetableChangeProposalStatus.APPROVED

    # No mutation artefact fields must exist on the returned proposal
    assert not hasattr(proposal, "apply_flag")
    assert not hasattr(proposal, "mutation_flag")
    assert not hasattr(proposal, "schedule_applied")
    assert not hasattr(proposal, "reservation_flag")


# ---------------------------------------------------------------------------
# 11. FSM: pending_review → rejected (does NOT mutate schedule)
# ---------------------------------------------------------------------------


def test_11_pending_review_to_rejected_no_mutation():
    """rejected status must be reachable; no mutation output must exist."""
    proposal = _manual_proposal()
    proposal = transition_timetable_change_proposal(
        proposal, TimetableChangeProposalStatus.PENDING_REVIEW, actor_id=1
    )
    proposal = transition_timetable_change_proposal(
        proposal, TimetableChangeProposalStatus.REJECTED,
        reviewer_id=99,
        reason="Not needed at this time",
    )

    assert proposal.status == TimetableChangeProposalStatus.REJECTED
    assert not hasattr(proposal, "mutation_flag")
    assert not hasattr(proposal, "schedule_applied")


# ---------------------------------------------------------------------------
# 12. FSM: pending_review → revision_requested (does NOT mutate schedule)
# ---------------------------------------------------------------------------


def test_12_pending_review_to_revision_requested_no_mutation():
    """revision_requested status must be reachable; no mutation output."""
    proposal = _manual_proposal()
    proposal = transition_timetable_change_proposal(
        proposal, TimetableChangeProposalStatus.PENDING_REVIEW, actor_id=1
    )
    proposal = transition_timetable_change_proposal(
        proposal, TimetableChangeProposalStatus.REVISION_REQUESTED,
        reviewer_id=99,
        reason="Please provide more context",
    )

    assert proposal.status == TimetableChangeProposalStatus.REVISION_REQUESTED
    assert not hasattr(proposal, "mutation_flag")


# ---------------------------------------------------------------------------
# 13. FSM: revision_requested → pending_review (valid)
# ---------------------------------------------------------------------------


def test_13_revision_requested_to_pending_review_valid():
    """revision_requested → pending_review re-submission must succeed."""
    proposal = _manual_proposal()
    proposal = transition_timetable_change_proposal(
        proposal, TimetableChangeProposalStatus.PENDING_REVIEW, actor_id=1
    )
    proposal = transition_timetable_change_proposal(
        proposal, TimetableChangeProposalStatus.REVISION_REQUESTED,
        reviewer_id=99,
    )
    proposal = transition_timetable_change_proposal(
        proposal, TimetableChangeProposalStatus.PENDING_REVIEW,
        actor_id=1,
        reason="Updated proposal",
    )

    assert proposal.status == TimetableChangeProposalStatus.PENDING_REVIEW


# ---------------------------------------------------------------------------
# 14. FSM: pending_review → cancelled (valid)
# ---------------------------------------------------------------------------


def test_14_pending_review_to_cancelled_valid():
    """pending_review → cancelled must succeed."""
    proposal = _manual_proposal()
    proposal = transition_timetable_change_proposal(
        proposal, TimetableChangeProposalStatus.PENDING_REVIEW, actor_id=1
    )
    proposal = transition_timetable_change_proposal(
        proposal, TimetableChangeProposalStatus.CANCELLED,
        actor_id=1,
        reason="Cancelled by submitter",
    )

    assert proposal.status == TimetableChangeProposalStatus.CANCELLED


# ---------------------------------------------------------------------------
# 15. FSM invalid: approved → rejected must fail
# ---------------------------------------------------------------------------


def test_15_approved_to_rejected_invalid():
    """approved → rejected must raise ValueError (terminal state exit forbidden)."""
    proposal = _manual_proposal()
    proposal = transition_timetable_change_proposal(
        proposal, TimetableChangeProposalStatus.PENDING_REVIEW, actor_id=1
    )
    proposal = transition_timetable_change_proposal(
        proposal, TimetableChangeProposalStatus.APPROVED, reviewer_id=99
    )

    with pytest.raises(ValueError, match="[Ii]nvalid.*[Ff][Ss][Mm]|[Ii]nvalid.*transition"):
        transition_timetable_change_proposal(
            proposal, TimetableChangeProposalStatus.REJECTED, actor_id=1
        )


# ---------------------------------------------------------------------------
# 16. FSM invalid: rejected → approved must fail
# ---------------------------------------------------------------------------


def test_16_rejected_to_approved_invalid():
    """rejected → approved must raise ValueError."""
    proposal = _manual_proposal()
    proposal = transition_timetable_change_proposal(
        proposal, TimetableChangeProposalStatus.PENDING_REVIEW, actor_id=1
    )
    proposal = transition_timetable_change_proposal(
        proposal, TimetableChangeProposalStatus.REJECTED, reviewer_id=99
    )

    with pytest.raises(ValueError):
        transition_timetable_change_proposal(
            proposal, TimetableChangeProposalStatus.APPROVED, actor_id=1
        )


# ---------------------------------------------------------------------------
# 17. FSM invalid: cancelled → approved must fail
# ---------------------------------------------------------------------------


def test_17_cancelled_to_approved_invalid():
    """cancelled → approved must raise ValueError."""
    proposal = _manual_proposal()
    proposal = transition_timetable_change_proposal(
        proposal, TimetableChangeProposalStatus.CANCELLED, actor_id=1
    )

    with pytest.raises(ValueError):
        transition_timetable_change_proposal(
            proposal, TimetableChangeProposalStatus.APPROVED, actor_id=1
        )


# ---------------------------------------------------------------------------
# 18. Cross-tenant transition rejected
# ---------------------------------------------------------------------------


def test_18_cross_tenant_transition_rejected():
    """A transition from a different tenant must be rejected."""
    proposal = _manual_proposal(tenant_id=100)
    proposal = transition_timetable_change_proposal(
        proposal, TimetableChangeProposalStatus.PENDING_REVIEW, actor_id=1
    )

    with pytest.raises(ValueError, match="[Cc]ross.tenant|tenant_id"):
        transition_timetable_change_proposal(
            proposal,
            TimetableChangeProposalStatus.APPROVED,
            actor_id=999,
            requesting_tenant_id=999,   # wrong tenant
        )


# ---------------------------------------------------------------------------
# 19. Missing / invalid tenant_id fails closed
# ---------------------------------------------------------------------------


def test_19_missing_tenant_id_fails_closed():
    """Building a proposal with tenant_id=0 must fail."""
    with pytest.raises((ValidationError, ValueError)):
        inp = TimetableChangeProposalInput(
            tenant_id=0,
            source_type=TimetableChangeProposalSourceType.MANUAL,
            current_snapshot=_snapshot(),
            proposed_change=TimetableChangeProposedChange(
                change_type=TimetableChangeType.ROOM_CHANGE,
                reason="Irrelevant",
            ),
            affected_entities=_affected(),
        )
        build_timetable_change_proposal(inp)


def test_19b_negative_tenant_id_fails_closed():
    """Building a proposal with a negative tenant_id must fail."""
    with pytest.raises((ValidationError, ValueError)):
        TimetableChangeProposalInput(
            tenant_id=-1,
            source_type=TimetableChangeProposalSourceType.MANUAL,
            current_snapshot=_snapshot(),
            proposed_change=TimetableChangeProposedChange(
                change_type=TimetableChangeType.ROOM_CHANGE,
                reason="Irrelevant",
            ),
            affected_entities=_affected(),
        )


# ---------------------------------------------------------------------------
# 20. Audit evidence appended on transition
# ---------------------------------------------------------------------------


def test_20_audit_evidence_appended_on_transition():
    """Each FSM transition must append one audit evidence entry."""
    proposal = _manual_proposal()
    initial_audit_count = len(proposal.audit_evidence)

    proposal = transition_timetable_change_proposal(
        proposal, TimetableChangeProposalStatus.PENDING_REVIEW, actor_id=1
    )
    assert len(proposal.audit_evidence) == initial_audit_count + 1

    proposal = transition_timetable_change_proposal(
        proposal, TimetableChangeProposalStatus.APPROVED, reviewer_id=99
    )
    assert len(proposal.audit_evidence) == initial_audit_count + 2


def test_20b_audit_entry_records_status_change():
    """Audit entries must record previous and new status correctly."""
    proposal = _manual_proposal()
    proposal = transition_timetable_change_proposal(
        proposal, TimetableChangeProposalStatus.PENDING_REVIEW, actor_id=1
    )

    last_entry = proposal.audit_evidence[-1]
    assert last_entry.previous_status == TimetableChangeProposalStatus.DRAFT.value
    assert last_entry.new_status == TimetableChangeProposalStatus.PENDING_REVIEW.value


# ---------------------------------------------------------------------------
# 21. No schedule mutation output exists in the contract
# ---------------------------------------------------------------------------


def test_21_no_schedule_mutation_output():
    """TimetableChangeProposal must not expose any schedule-mutation fields."""
    proposal = _manual_proposal()
    proposal_dict = proposal.model_dump()

    mutation_fields = [
        "apply_flag",
        "mutation_flag",
        "schedule_applied",
        "auto_apply",
        "timetable_applied",
        "booking_created",
        "optimized_schedule",
    ]
    for field in mutation_fields:
        assert field not in proposal_dict, (
            f"Forbidden field '{field}' found in proposal contract output"
        )


# ---------------------------------------------------------------------------
# 22. No room reservation output exists
# ---------------------------------------------------------------------------


def test_22_no_room_reservation_output():
    """TimetableChangeProposal must not expose any room-reservation fields."""
    proposal = _manual_proposal()
    proposal_dict = proposal.model_dump()

    reservation_fields = [
        "reservation_flag",
        "room_reserved",
        "booking_created",
        "room_booking_id",
    ]
    for field in reservation_fields:
        assert field not in proposal_dict, (
            f"Forbidden field '{field}' found in proposal contract output"
        )


# ---------------------------------------------------------------------------
# 23. No booking override output exists
# ---------------------------------------------------------------------------


def test_23_no_booking_override_output():
    """TimetableChangeProposal must not expose booking-override fields."""
    proposal = _manual_proposal()
    proposal_dict = proposal.model_dump()

    override_fields = [
        "booking_override",
        "force_booking",
        "override_conflict",
    ]
    for field in override_fields:
        assert field not in proposal_dict, (
            f"Forbidden field '{field}' found in proposal contract output"
        )


# ---------------------------------------------------------------------------
# 24. No auto-apply field exists
# ---------------------------------------------------------------------------


def test_24_no_auto_apply_field():
    """TimetableChangeProposal must not have any auto-apply field."""
    proposal = _manual_proposal()
    proposal_dict = proposal.model_dump()

    auto_fields = [
        "auto_apply",
        "auto_approve",
        "auto_schedule",
        "auto_commit",
    ]
    for field in auto_fields:
        assert field not in proposal_dict, (
            f"Forbidden field '{field}' found in proposal contract output"
        )

    # Pydantic v2 keeps private attrs as descriptors on the class.
    # We assert the configured default remains False.
    assert TimetableChangeProposal._apply_flag.default is False


# ---------------------------------------------------------------------------
# 25. No fake optimization result exists
# ---------------------------------------------------------------------------


def test_25_no_fake_optimization_result():
    """Proposal must not contain any optimization result or simulation output."""
    proposal = _manual_proposal()
    proposal_dict = proposal.model_dump()

    fake_fields = [
        "optimization_result",
        "simulated_outcome",
        "simulation_output",
        "fake_score",
    ]
    for field in fake_fields:
        assert field not in proposal_dict, (
            f"Forbidden field '{field}' found in proposal contract output"
        )


# ---------------------------------------------------------------------------
# 26. A-020 recommendation output can be referenced without mutation
# ---------------------------------------------------------------------------


class _FakeRecommendationResult:
    """Lightweight stand-in for RoomAllocationRecommendationResult (A-020)."""

    class _Candidate:
        room_id = 301

    recommendation_id = "reco_a020_5"
    ranked_candidates = [_Candidate()]


def test_26_a020_recommendation_referenced_without_mutation():
    """proposal_from_room_recommendation must reference A-020 result without mutating anything."""
    fake_reco = _FakeRecommendationResult()
    proposal = proposal_from_room_recommendation(
        tenant_id=100,
        recommendation_result=fake_reco,
        section_snapshot=_snapshot(),
        affected_entities=_affected(),
        created_by=1,
    )

    # Proposal must reference the recommendation
    assert proposal.source_recommendation_id == "reco_a020_5"
    assert proposal.source_type == TimetableChangeProposalSourceType.ROOM_ALLOCATION_RECOMMENDATION

    # Proposal must NOT be in an applied/mutated state
    assert proposal.status == TimetableChangeProposalStatus.DRAFT
    assert proposal.approval_required is True

    # The fake_reco object must not have been modified
    assert fake_reco.recommendation_id == "reco_a020_5"
    assert fake_reco.ranked_candidates[0].room_id == 301

    # No mutation fields
    proposal_dict = proposal.model_dump()
    assert "apply_flag" not in proposal_dict
    assert "mutation_flag" not in proposal_dict


# ---------------------------------------------------------------------------
# 27. Tenant/security regression remains green
# ---------------------------------------------------------------------------


def test_27_tenant_isolation_enforced():
    """Proposals for different tenants must not be transitional from each other."""
    proposal_tenant_a = _manual_proposal(tenant_id=100)
    proposal_tenant_a = transition_timetable_change_proposal(
        proposal_tenant_a, TimetableChangeProposalStatus.PENDING_REVIEW, actor_id=1
    )

    # Tenant B tries to approve tenant A's proposal
    with pytest.raises(ValueError, match="[Cc]ross.tenant|tenant_id"):
        transition_timetable_change_proposal(
            proposal_tenant_a,
            TimetableChangeProposalStatus.APPROVED,
            actor_id=200,
            requesting_tenant_id=200,  # wrong tenant
        )

    # Tenant A's proposal remains unchanged
    assert proposal_tenant_a.status == TimetableChangeProposalStatus.PENDING_REVIEW


def test_27b_apply_proposal_decision_cross_tenant_rejected():
    """apply_proposal_decision must reject cross-tenant decisions."""
    proposal = _manual_proposal(tenant_id=100)
    proposal = transition_timetable_change_proposal(
        proposal, TimetableChangeProposalStatus.PENDING_REVIEW, actor_id=1
    )

    decision = TimetableChangeProposalDecision(
        proposal_id=proposal.proposal_id,
        tenant_id=999,   # wrong tenant
        reviewer_id=50,
        new_status=TimetableChangeProposalStatus.APPROVED,
    )

    with pytest.raises(ValueError, match="[Cc]ross.tenant|tenant_id"):
        apply_proposal_decision(proposal, decision)


def test_27c_proposal_from_conflict_helper_creates_draft():
    """proposal_from_conflict helper must build a tenant-safe DRAFT proposal."""
    proposal = proposal_from_conflict(
        tenant_id=100,
        conflict_id="conf_999",
        conflict_type="room_double_booking",
        section_snapshot=_snapshot(),
        affected_entities=_affected(),
        reason="Room double-booking requires resolution",
        created_by=1,
    )

    assert proposal.tenant_id == 100
    assert proposal.status == TimetableChangeProposalStatus.DRAFT
    assert proposal.source_type == TimetableChangeProposalSourceType.CONFLICT_RESOLUTION
    assert proposal.source_conflict_id == "conf_999"
    assert proposal.approval_required is True


def test_27d_build_proposal_audit_evidence_helper():
    """build_proposal_audit_evidence must return a well-formed TimetableChangeAuditEvidence."""
    entry = build_proposal_audit_evidence(
        action="submit",
        previous_status=TimetableChangeProposalStatus.DRAFT,
        new_status=TimetableChangeProposalStatus.PENDING_REVIEW,
        actor_id=1,
        reason="Submitted for review",
        source_entity_type="section",
        source_entity_id=42,
    )

    assert isinstance(entry, TimetableChangeAuditEvidence)
    assert entry.action == "submit"
    assert entry.previous_status == TimetableChangeProposalStatus.DRAFT.value
    assert entry.new_status == TimetableChangeProposalStatus.PENDING_REVIEW.value
    assert entry.actor_id == 1
