"""A-022.3 Room Recommendation -> Timetable Proposal Bridge.

This module converts A-020 room allocation recommendation outputs into
A-022 timetable proposal/simulation-ready contract objects.

Strictly non-destructive:
- no timetable mutation
- no room reservation
- no booking override
- no apply/commit semantics
"""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from app.modules.scheduling.room_allocation_readiness import (
    CapacityMismatchReason,
    CapacityRiskLevel,
    RoomAllocationCandidate,
    RoomAllocationRecommendationResult,
    RoomAllocationRecommendationStatus,
)
from app.modules.scheduling.timetable_change_proposal import (
    TimetableChangeAffectedEntities,
    TimetableChangeCurrentSnapshot,
    TimetableChangeProposal,
    TimetableChangeProposalEvidence,
    TimetableChangeProposalInput,
    TimetableChangeProposalRiskLevel,
    TimetableChangeProposalSourceType,
    TimetableChangeProposedChange,
    TimetableChangeType,
    build_proposal_audit_evidence,
    build_timetable_change_proposal,
)
from app.modules.scheduling.timetable_change_simulation import (
    TimetableChangeSimulationInput,
)


class RoomRecommendationToProposalBridgeInput(BaseModel):
    """Input bag for recommendation-to-proposal bridge."""

    tenant_id: int = Field(gt=0)
    recommendation_result: RoomAllocationRecommendationResult
    current_snapshot: TimetableChangeCurrentSnapshot

    selected_candidate_id: Optional[str | int] = None
    affected_entities: Optional[TimetableChangeAffectedEntities] = None

    created_by: Optional[str | int] = None
    reason: Optional[str] = None

    # Required to allow NOT_RECOMMENDED / unavailable candidates.
    explicit_review_reason: Optional[str] = None

    # Policy switch: when no viable candidate exists, reject by default.
    # If enabled, creates a review-only proposal with no proposed room.
    allow_review_only_no_viable: bool = False

    source_entity_type: Optional[str] = "room_allocation_recommendation"
    source_entity_id: Optional[str | int] = None


class RoomRecommendationToProposalBridgeResult(BaseModel):
    """Bridge output containing proposal + simulation-ready contract input."""

    proposal: TimetableChangeProposal
    simulation_input: TimetableChangeSimulationInput

    selected_candidate_id: Optional[str | int] = None
    selected_candidate_rank: Optional[int] = None

    simulation_ready: bool = True
    data_quality_note: Optional[str] = None
    bridge_evidence: list[str] = Field(default_factory=list)


def _map_capacity_risk_to_proposal_risk(
    level: CapacityRiskLevel,
) -> TimetableChangeProposalRiskLevel:
    mapping: dict[CapacityRiskLevel, TimetableChangeProposalRiskLevel] = {
        CapacityRiskLevel.LOW: TimetableChangeProposalRiskLevel.LOW,
        CapacityRiskLevel.MEDIUM: TimetableChangeProposalRiskLevel.MEDIUM,
        CapacityRiskLevel.HIGH: TimetableChangeProposalRiskLevel.HIGH,
        CapacityRiskLevel.CRITICAL: TimetableChangeProposalRiskLevel.CRITICAL,
    }
    return mapping.get(level, TimetableChangeProposalRiskLevel.MEDIUM)


def _resolve_recommendation_id(
    recommendation_result: RoomAllocationRecommendationResult,
    fallback_source_entity_id: Optional[str | int],
) -> str:
    """Resolve a stable recommendation reference for proposal traceability."""
    source_id = (
        fallback_source_entity_id
        if fallback_source_entity_id is not None
        else recommendation_result.source_entity_id
    )
    if source_id is not None:
        return str(source_id)

    # Deterministic fallback to preserve traceability even if upstream id is absent.
    return (
        f"roomrec:{recommendation_result.section_id}:"
        f"{recommendation_result.best_candidate_id or 'none'}"
    )


def _select_candidate(
    recommendation_result: RoomAllocationRecommendationResult,
    selected_candidate_id: Optional[str | int],
) -> Optional[RoomAllocationCandidate]:
    """Select candidate explicitly or via best_candidate_id when viable."""
    candidates = recommendation_result.candidates
    if selected_candidate_id is not None:
        for candidate in candidates:
            if str(candidate.room_id) == str(selected_candidate_id):
                return candidate
        raise ValueError(
            f"selected_candidate_id '{selected_candidate_id}' not found in recommendation candidates"
        )

    if recommendation_result.has_viable_candidate and recommendation_result.best_candidate_id is not None:
        for candidate in candidates:
            if str(candidate.room_id) == str(recommendation_result.best_candidate_id):
                return candidate
        raise ValueError(
            "has_viable_candidate is true but best_candidate_id was not found in candidates"
        )

    return None


def _build_affected_entities(
    recommendation_result: RoomAllocationRecommendationResult,
    current_snapshot: TimetableChangeCurrentSnapshot,
    selected_candidate: Optional[RoomAllocationCandidate],
    provided: Optional[TimetableChangeAffectedEntities],
) -> TimetableChangeAffectedEntities:
    if provided is not None:
        return provided

    return TimetableChangeAffectedEntities(
        affected_section_id=int(recommendation_result.section_id),
        affected_course_id=int(recommendation_result.course_id),
        affected_group_id=recommendation_result.group_id,
        affected_teacher_id=recommendation_result.teacher_id,
        affected_room_id=(
            selected_candidate.room_id if selected_candidate is not None else current_snapshot.room_id
        ),
        affected_student_count=current_snapshot.students_count,
        affected_booking_ids=[],
        affected_conflict_ids=[],
    )


def build_recommendation_to_proposal_evidence(
    recommendation_result: RoomAllocationRecommendationResult,
    selected_candidate: Optional[RoomAllocationCandidate],
    recommendation_id: str,
    data_quality_note: Optional[str] = None,
) -> TimetableChangeProposalEvidence:
    """Create proposal evidence derived from recommendation and selected candidate."""
    conflict_count = 0
    conflict_types: list[str] = []
    risk_summary = "Derived from room allocation recommendation"
    capacity_ok = True
    equipment_ok = True
    room_type_ok = True

    if selected_candidate is not None:
        conflict_count = len(selected_candidate.conflict_evidence)
        conflict_types = sorted(
            {
                conflict.conflict_type.value
                for conflict in selected_candidate.conflict_evidence
            }
        )
        mismatch_reasons = set(selected_candidate.capacity_match.mismatch_reasons)
        capacity_ok = (
            CapacityMismatchReason.CAPACITY_SHORTAGE not in mismatch_reasons
            and CapacityMismatchReason.CAPACITY_UNKNOWN not in mismatch_reasons
        )
        equipment_ok = CapacityMismatchReason.EQUIPMENT_MISMATCH not in mismatch_reasons
        room_type_ok = (
            CapacityMismatchReason.ROOM_TYPE_MISMATCH not in mismatch_reasons
            and CapacityMismatchReason.ROOM_TYPE_UNKNOWN not in mismatch_reasons
        )
        risk_summary = (
            f"match_score={selected_candidate.capacity_match.match_score}; "
            f"candidate_score={selected_candidate.recommendation_score}; "
            f"risk={selected_candidate.capacity_match.risk_level.value}; "
            f"status={selected_candidate.recommendation_status.value}"
        )

    return TimetableChangeProposalEvidence(
        conflict_count=conflict_count,
        conflict_types=conflict_types,
        capacity_ok=capacity_ok,
        equipment_ok=equipment_ok,
        room_type_ok=room_type_ok,
        risk_summary=risk_summary,
        source_recommendation_id=recommendation_id,
        source_conflict_ids=[c.source_entity_id for c in (selected_candidate.conflict_evidence if selected_candidate is not None else []) if c.source_entity_id is not None],
        data_quality_note=data_quality_note,
    )


def build_proposal_from_room_allocation_recommendation(
    inp: RoomRecommendationToProposalBridgeInput,
) -> RoomRecommendationToProposalBridgeResult:
    """Convert A-020 recommendation result into A-022 proposal + simulation input.

    Fail-closed rules:
    - tenant_id must be positive
    - recommendation tenant must match authoritative tenant
    - selected candidate tenant must match recommendation tenant
    - no viable candidate rejected unless allow_review_only_no_viable=True
    - unavailable/not_recommended candidate requires explicit_review_reason
    """
    if inp.tenant_id <= 0:
        raise ValueError("tenant_id must be a positive integer")

    recommendation = inp.recommendation_result

    if recommendation.tenant_id != inp.tenant_id:
        raise ValueError(
            f"Cross-tenant bridge rejected: recommendation.tenant_id={recommendation.tenant_id}, "
            f"authoritative_tenant_id={inp.tenant_id}"
        )

    recommendation_id = _resolve_recommendation_id(
        recommendation,
        inp.source_entity_id,
    )

    selected_candidate = _select_candidate(
        recommendation,
        inp.selected_candidate_id,
    )

    data_quality_note: Optional[str] = None
    bridge_evidence: list[str] = [
        f"recommendation_status={recommendation.recommendation_status.value}",
        f"has_viable_candidate={recommendation.has_viable_candidate}",
        f"source_recommendation_id={recommendation_id}",
    ]

    if selected_candidate is None and not recommendation.has_viable_candidate:
        if not inp.allow_review_only_no_viable:
            raise ValueError(
                "No viable recommendation candidate available. "
                "Bridge rejected by policy (allow_review_only_no_viable=False)."
            )
        data_quality_note = (
            "No viable candidate from recommendation; review-only proposal created."
        )

    if selected_candidate is not None and selected_candidate.tenant_id != inp.tenant_id:
        raise ValueError(
            f"Cross-tenant candidate rejected: candidate.tenant_id={selected_candidate.tenant_id}, "
            f"authoritative_tenant_id={inp.tenant_id}"
        )

    if selected_candidate is not None:
        if selected_candidate.recommendation_status in {
            RoomAllocationRecommendationStatus.NOT_RECOMMENDED,
            RoomAllocationRecommendationStatus.NO_VIABLE_CANDIDATE,
        } and not inp.explicit_review_reason:
            raise ValueError(
                "Selected candidate is not recommended/no-viable and requires explicit_review_reason."
            )

        if selected_candidate.capacity_match.match_status.value in {"unavailable", "not_suitable"} and not inp.explicit_review_reason:
            raise ValueError(
                "Selected candidate is unavailable/not suitable and requires explicit_review_reason."
            )

    affected_entities = _build_affected_entities(
        recommendation,
        inp.current_snapshot,
        selected_candidate,
        inp.affected_entities,
    )

    proposed_room_id = selected_candidate.room_id if selected_candidate is not None else None

    if proposed_room_id is not None and str(proposed_room_id) != str(inp.current_snapshot.room_id):
        change_type = TimetableChangeType.ROOM_CHANGE
        bridge_evidence.append(
            f"room_change={inp.current_snapshot.room_id!r}->{proposed_room_id!r}"
        )
    else:
        change_type = TimetableChangeType.UNKNOWN
        if data_quality_note is None:
            data_quality_note = (
                "Selected room is same as current room or no room selected; proposal remains review-only."
            )

    reason_fragments: list[str] = []
    if inp.reason:
        reason_fragments.append(inp.reason)
    else:
        reason_fragments.append("Derived from A-020 room allocation recommendation")

    if inp.explicit_review_reason:
        reason_fragments.append(f"explicit_review_reason={inp.explicit_review_reason}")

    if selected_candidate is not None:
        reason_fragments.append(
            f"candidate_score={selected_candidate.recommendation_score}"
        )
        reason_fragments.append(
            f"match_score={selected_candidate.capacity_match.match_score}"
        )
        reason_fragments.append(
            f"risk={selected_candidate.capacity_match.risk_level.value}"
        )
        mismatch = [reason.value for reason in selected_candidate.capacity_match.mismatch_reasons]
        if mismatch:
            reason_fragments.append(f"mismatch_reasons={','.join(sorted(set(mismatch)))}")

    proposal_risk_level = (
        _map_capacity_risk_to_proposal_risk(selected_candidate.capacity_match.risk_level)
        if selected_candidate is not None
        else TimetableChangeProposalRiskLevel.HIGH
    )

    proposal_evidence = build_recommendation_to_proposal_evidence(
        recommendation,
        selected_candidate,
        recommendation_id,
        data_quality_note=data_quality_note,
    )

    proposal_input = TimetableChangeProposalInput(
        tenant_id=inp.tenant_id,
        source_type=TimetableChangeProposalSourceType.ROOM_ALLOCATION_RECOMMENDATION,
        source_recommendation_id=recommendation_id,
        current_snapshot=inp.current_snapshot,
        proposed_change=TimetableChangeProposedChange(
            change_type=change_type,
            proposed_room_id=proposed_room_id,
            reason="; ".join(reason_fragments),
            evidence=bridge_evidence,
        ),
        affected_entities=affected_entities,
        evidence=proposal_evidence,
        created_by=inp.created_by,
        risk_level=proposal_risk_level,
        source_entity_type=inp.source_entity_type,
        source_entity_id=recommendation_id,
    )

    proposal = build_timetable_change_proposal(proposal_input)

    # Enforce human-review policy for high/critical recommendation-derived proposals.
    if proposal.risk_level in {
        TimetableChangeProposalRiskLevel.HIGH,
        TimetableChangeProposalRiskLevel.CRITICAL,
    } and proposal.approval_required is not True:
        proposal = proposal.model_copy(update={"approval_required": True})

    bridge_audit = build_proposal_audit_evidence(
        action="bridge_from_room_recommendation",
        previous_status=None,
        new_status=proposal.status,
        actor_id=inp.created_by,
        reason="Recommendation->proposal bridge created",
        source_entity_type=inp.source_entity_type,
        source_entity_id=recommendation_id,
    )
    proposal = proposal.model_copy(
        update={"audit_evidence": proposal.audit_evidence + [bridge_audit]}
    )

    room_values: list[str | int] = []
    if proposal.current_snapshot.room_id is not None:
        room_values.append(proposal.current_snapshot.room_id)
    if proposed_room_id is not None and proposed_room_id not in room_values:
        room_values.append(proposed_room_id)

    simulation_input = TimetableChangeSimulationInput(
        proposal=proposal,
        actor_id=inp.created_by,
        affected_sections=[proposal.current_snapshot.section_id],
        affected_groups=(
            [proposal.current_snapshot.group_id]
            if proposal.current_snapshot.group_id is not None
            else []
        ),
        affected_teachers=(
            [proposal.current_snapshot.teacher_id]
            if proposal.current_snapshot.teacher_id is not None
            else []
        ),
        affected_rooms=room_values,
        affected_bookings=proposal.affected_entities.affected_booking_ids,
        affected_student_count=proposal.current_snapshot.students_count,
        risk_before=proposal.risk_level,
        risk_after=proposal.risk_level,
        conflicts_before=proposal.evidence.conflict_types,
        conflicts_after=proposal.evidence.conflict_types,
    )

    return RoomRecommendationToProposalBridgeResult(
        proposal=proposal,
        simulation_input=simulation_input,
        selected_candidate_id=(selected_candidate.room_id if selected_candidate is not None else None),
        selected_candidate_rank=(selected_candidate.recommendation_rank if selected_candidate is not None else None),
        simulation_ready=True,
        data_quality_note=data_quality_note,
        bridge_evidence=bridge_evidence,
    )


# Alias for readability where proposal semantics are primary
build_timetable_proposal_from_room_recommendation = (
    build_proposal_from_room_allocation_recommendation
)
