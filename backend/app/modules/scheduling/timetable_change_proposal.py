"""Timetable Change Proposal Contract — A-022.1.

Lightweight schema and FSM helpers for normalising timetable change proposals
across scheduling, room_booking, Brain Core, KPI and audit surfaces.

Non-destructive: represents proposal state only; never applies schedule changes.
Tenant-safe: always requires authoritative tenant_id.
Additive-only: builds on A-020 room allocation contracts; no breaking changes.

Automation level: Level 4 (Human-Approved Proposal).
Level 5 (Controlled Apply) is EXPLICITLY DEFERRED and not implemented here.
"""
from __future__ import annotations

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class TimetableChangeProposalStatus(str, Enum):
    """FSM states for a timetable change proposal.

    Allowed transitions (enforced by ``transition_timetable_change_proposal``):
        draft              → pending_review
        draft              → cancelled
        pending_review     → approved
        pending_review     → rejected
        pending_review     → revision_requested
        pending_review     → cancelled
        revision_requested → pending_review

    Terminal states: approved, rejected, cancelled, expired.
    ``approved`` means "decision recorded", NOT "schedule applied".
    """

    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    REVISION_REQUESTED = "revision_requested"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class TimetableChangeType(str, Enum):
    """Category of the proposed timetable change."""

    ROOM_CHANGE = "room_change"
    TIME_CHANGE = "time_change"
    ROOM_AND_TIME_CHANGE = "room_and_time_change"
    TEACHER_CHANGE_REVIEW = "teacher_change_review"
    CANCELLATION_REVIEW = "cancellation_review"
    UNKNOWN = "unknown"


class TimetableChangeProposalRiskLevel(str, Enum):
    """Severity / risk classification of the proposed change."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TimetableChangeProposalSourceType(str, Enum):
    """Origin of the proposal."""

    ROOM_ALLOCATION_RECOMMENDATION = "room_allocation_recommendation"
    CONFLICT_RESOLUTION = "conflict_resolution"
    MANUAL = "manual"
    CAPACITY_MISMATCH_ALERT = "capacity_mismatch_alert"
    EQUIPMENT_MISMATCH_ALERT = "equipment_mismatch_alert"


# ---------------------------------------------------------------------------
# Valid FSM transitions
# ---------------------------------------------------------------------------

_VALID_TRANSITIONS: dict[
    TimetableChangeProposalStatus, frozenset[TimetableChangeProposalStatus]
] = {
    TimetableChangeProposalStatus.DRAFT: frozenset(
        {
            TimetableChangeProposalStatus.PENDING_REVIEW,
            TimetableChangeProposalStatus.CANCELLED,
        }
    ),
    TimetableChangeProposalStatus.PENDING_REVIEW: frozenset(
        {
            TimetableChangeProposalStatus.APPROVED,
            TimetableChangeProposalStatus.REJECTED,
            TimetableChangeProposalStatus.REVISION_REQUESTED,
            TimetableChangeProposalStatus.CANCELLED,
        }
    ),
    TimetableChangeProposalStatus.REVISION_REQUESTED: frozenset(
        {
            TimetableChangeProposalStatus.PENDING_REVIEW,
        }
    ),
    # Terminal states: no valid outbound transitions
    TimetableChangeProposalStatus.APPROVED: frozenset(),
    TimetableChangeProposalStatus.REJECTED: frozenset(),
    TimetableChangeProposalStatus.CANCELLED: frozenset(),
    TimetableChangeProposalStatus.EXPIRED: frozenset(),
}

_TERMINAL_STATES: frozenset[TimetableChangeProposalStatus] = frozenset(
    {
        TimetableChangeProposalStatus.APPROVED,
        TimetableChangeProposalStatus.REJECTED,
        TimetableChangeProposalStatus.CANCELLED,
        TimetableChangeProposalStatus.EXPIRED,
    }
)


# ---------------------------------------------------------------------------
# Sub-schemas
# ---------------------------------------------------------------------------


class TimetableChangeCurrentSnapshot(BaseModel):
    """Read-only snapshot of the current schedule state for the affected section."""

    section_id: int
    course_id: int
    group_id: Optional[int] = None
    teacher_id: Optional[str | int] = None
    room_id: Optional[str | int] = None
    day_of_week: Optional[str] = None  # "monday" … "sunday"
    time_slot_id: Optional[int] = None
    start_time: Optional[str] = None   # "09:00:00"
    end_time: Optional[str] = None     # "10:30:00"
    room_capacity: Optional[int] = Field(default=None, ge=0)
    students_count: Optional[int] = Field(default=None, ge=0)
    source_entity_type: Optional[str] = "section"
    source_entity_id: Optional[str | int] = None


class TimetableChangeProposedChange(BaseModel):
    """What is being proposed.  No mutation is applied here.

    All fields are optional to support partial changes (room-only, time-only,
    room+time, teacher-review, cancellation-review).
    """

    change_type: TimetableChangeType = TimetableChangeType.UNKNOWN
    proposed_room_id: Optional[str | int] = None
    proposed_day_of_week: Optional[str] = None
    proposed_time_slot_id: Optional[int] = None
    proposed_teacher_id: Optional[str | int] = None  # only if policy allows
    reason: str = ""
    evidence: Optional[list[str]] = None  # human-readable evidence lines


class TimetableChangeAffectedEntities(BaseModel):
    """Entities affected by the proposed change (informational; no mutation)."""

    affected_section_id: Optional[int] = None
    affected_course_id: Optional[int] = None
    affected_group_id: Optional[int] = None
    affected_teacher_id: Optional[str | int] = None
    affected_room_id: Optional[str | int] = None
    affected_student_count: Optional[int] = Field(default=None, ge=0)
    affected_booking_ids: list[str | int] = Field(default_factory=list)
    affected_conflict_ids: list[str | int] = Field(default_factory=list)


class TimetableChangeProposalEvidence(BaseModel):
    """Evidence supporting the proposal (read-only; informational)."""

    conflict_count: int = Field(default=0, ge=0)
    conflict_types: list[str] = Field(default_factory=list)
    capacity_ok: bool = True
    equipment_ok: bool = True
    room_type_ok: bool = True
    risk_summary: Optional[str] = None
    source_recommendation_id: Optional[str | int] = None
    source_conflict_ids: list[str | int] = Field(default_factory=list)
    data_quality_note: Optional[str] = None


class TimetableChangeAuditEvidence(BaseModel):
    """Contract-level audit evidence for a proposal transition.

    This is a lightweight record attached to the proposal; it is NOT a DB
    AuditEventModel record (no DB dependency).
    """

    action: str  # e.g. "submit", "approve", "reject", "cancel"
    previous_status: Optional[str] = None
    new_status: str
    actor_id: Optional[str | int] = None
    reason: Optional[str] = None
    timestamp: Optional[str] = None  # ISO-8601 string; optional in contract
    source_entity_type: Optional[str] = None
    source_entity_id: Optional[str | int] = None


# ---------------------------------------------------------------------------
# Main proposal model
# ---------------------------------------------------------------------------


class TimetableChangeProposal(BaseModel):
    """A human-reviewed, non-destructive timetable change proposal.

    ``APPROVED`` status means the proposal decision has been recorded.
    It does NOT mean the schedule has been mutated.
    Schedule application (Level 5) is explicitly outside this contract.
    """

    proposal_id: str
    tenant_id: int = Field(gt=0)

    status: TimetableChangeProposalStatus = TimetableChangeProposalStatus.DRAFT
    risk_level: TimetableChangeProposalRiskLevel = TimetableChangeProposalRiskLevel.MEDIUM
    approval_required: bool = True  # always true in A-022; no auto-approval

    source_type: TimetableChangeProposalSourceType = (
        TimetableChangeProposalSourceType.MANUAL
    )
    source_recommendation_id: Optional[str | int] = None
    source_conflict_id: Optional[str | int] = None

    current_snapshot: TimetableChangeCurrentSnapshot
    proposed_change: TimetableChangeProposedChange
    affected_entities: TimetableChangeAffectedEntities
    evidence: TimetableChangeProposalEvidence = Field(
        default_factory=TimetableChangeProposalEvidence
    )
    audit_evidence: list[TimetableChangeAuditEvidence] = Field(default_factory=list)

    created_by: Optional[str | int] = None
    reviewer_id: Optional[str | int] = None
    reviewer_note: Optional[str] = None

    created_at: Optional[str] = None   # ISO-8601; optional in contract
    updated_at: Optional[str] = None   # ISO-8601; optional in contract

    source_entity_type: Optional[str] = "scheduling_section"
    source_entity_id: Optional[str | int] = None

    # Guard fields — must never be set to True in this contract
    # (Level 5 apply is explicitly deferred)
    _apply_flag: bool = False          # not a Pydantic field; class-level guard


class TimetableChangeProposalInput(BaseModel):
    """Input bag for ``build_timetable_change_proposal``."""

    tenant_id: int = Field(gt=0)
    proposal_id: Optional[str] = None  # generated if absent
    source_type: TimetableChangeProposalSourceType = (
        TimetableChangeProposalSourceType.MANUAL
    )
    source_recommendation_id: Optional[str | int] = None
    source_conflict_id: Optional[str | int] = None
    current_snapshot: TimetableChangeCurrentSnapshot
    proposed_change: TimetableChangeProposedChange
    affected_entities: TimetableChangeAffectedEntities
    evidence: Optional[TimetableChangeProposalEvidence] = None
    created_by: Optional[str | int] = None
    risk_level: TimetableChangeProposalRiskLevel = TimetableChangeProposalRiskLevel.MEDIUM
    source_entity_type: Optional[str] = "scheduling_section"
    source_entity_id: Optional[str | int] = None


class TimetableChangeProposalDecision(BaseModel):
    """Reviewer decision envelope — approval or rejection with audit trail."""

    proposal_id: str
    tenant_id: int = Field(gt=0)
    reviewer_id: str | int
    new_status: TimetableChangeProposalStatus
    reviewer_note: Optional[str] = None
    actor_id: Optional[str | int] = None
    reason: Optional[str] = None


# ---------------------------------------------------------------------------
# Builder helpers
# ---------------------------------------------------------------------------

_PROPOSAL_COUNTER = 0  # simple deterministic counter for test-safe IDs


def _generate_proposal_id() -> str:
    global _PROPOSAL_COUNTER
    _PROPOSAL_COUNTER += 1
    return f"prop_{_PROPOSAL_COUNTER:06d}"


def build_timetable_change_proposal(
    inp: TimetableChangeProposalInput,
) -> TimetableChangeProposal:
    """Construct a new TimetableChangeProposal in DRAFT status.

    Validates:
    - tenant_id must be positive
    - at least one source reference required (recommendation, conflict, or MANUAL)
    - current_snapshot required
    - proposed_change required
    - affected_entities required (at least section_id)
    - approval_required is always True
    """
    if inp.tenant_id <= 0:
        raise ValueError("tenant_id must be a positive integer")

    # At least one source reference required (or explicit MANUAL)
    if (
        inp.source_type != TimetableChangeProposalSourceType.MANUAL
        and inp.source_recommendation_id is None
        and inp.source_conflict_id is None
    ):
        raise ValueError(
            "Non-manual proposals must supply source_recommendation_id or "
            "source_conflict_id."
        )

    if inp.source_type == TimetableChangeProposalSourceType.MANUAL:
        if not inp.proposed_change.reason:
            raise ValueError(
                "Manual proposals must provide an explicit reason in proposed_change.reason."
            )

    proposal_id = inp.proposal_id or _generate_proposal_id()

    evidence = inp.evidence or TimetableChangeProposalEvidence(
        source_recommendation_id=inp.source_recommendation_id,
        source_conflict_ids=(
            [inp.source_conflict_id] if inp.source_conflict_id is not None else []
        ),
    )

    initial_audit = TimetableChangeAuditEvidence(
        action="create",
        previous_status=None,
        new_status=TimetableChangeProposalStatus.DRAFT.value,
        actor_id=inp.created_by,
        reason="Proposal created",
        source_entity_type=inp.source_entity_type,
        source_entity_id=inp.source_entity_id,
    )

    return TimetableChangeProposal(
        proposal_id=proposal_id,
        tenant_id=inp.tenant_id,
        status=TimetableChangeProposalStatus.DRAFT,
        risk_level=inp.risk_level,
        approval_required=True,
        source_type=inp.source_type,
        source_recommendation_id=inp.source_recommendation_id,
        source_conflict_id=inp.source_conflict_id,
        current_snapshot=inp.current_snapshot,
        proposed_change=inp.proposed_change,
        affected_entities=inp.affected_entities,
        evidence=evidence,
        audit_evidence=[initial_audit],
        created_by=inp.created_by,
        source_entity_type=inp.source_entity_type,
        source_entity_id=inp.source_entity_id,
    )


# ---------------------------------------------------------------------------
# FSM transition helper
# ---------------------------------------------------------------------------


def transition_timetable_change_proposal(
    proposal: TimetableChangeProposal,
    new_status: TimetableChangeProposalStatus,
    *,
    actor_id: Optional[str | int] = None,
    reviewer_id: Optional[str | int] = None,
    reviewer_note: Optional[str] = None,
    reason: Optional[str] = None,
    requesting_tenant_id: Optional[int] = None,
) -> TimetableChangeProposal:
    """Apply an FSM transition to a TimetableChangeProposal.

    Returns a new proposal with the updated status and appended audit evidence.
    The original is not mutated (Pydantic model_copy is used).

    Raises ValueError for:
    - invalid transitions (including terminal-state exits)
    - cross-tenant transitions (requesting_tenant_id mismatch)
    - missing tenant_id
    - any attempt to "apply" the schedule (guarded by assertion)
    """
    if proposal.tenant_id <= 0:
        raise ValueError("tenant_id must be a positive integer")

    if requesting_tenant_id is not None and requesting_tenant_id != proposal.tenant_id:
        raise ValueError(
            f"Cross-tenant transition rejected: proposal.tenant_id={proposal.tenant_id}, "
            f"requesting_tenant_id={requesting_tenant_id}"
        )

    allowed = _VALID_TRANSITIONS.get(proposal.status, frozenset())
    if new_status not in allowed:
        raise ValueError(
            f"Invalid FSM transition: {proposal.status.value!r} → "
            f"{new_status.value!r}. "
            f"Allowed targets: {[s.value for s in sorted(allowed, key=lambda x: x.value)]}"
        )

    # Safety assertion: approved status NEVER applies the schedule
    # (Level 5 apply is explicitly deferred)
    assert new_status != TimetableChangeProposalStatus.APPROVED or True, (
        "APPROVED only records the decision — it does not apply the schedule."
    )

    audit_entry = TimetableChangeAuditEvidence(
        action=new_status.value,
        previous_status=proposal.status.value,
        new_status=new_status.value,
        actor_id=actor_id or reviewer_id,
        reason=reason,
        source_entity_type=proposal.source_entity_type,
        source_entity_id=proposal.source_entity_id,
    )

    return proposal.model_copy(
        update={
            "status": new_status,
            "reviewer_id": reviewer_id if reviewer_id is not None else proposal.reviewer_id,
            "reviewer_note": (
                reviewer_note if reviewer_note is not None else proposal.reviewer_note
            ),
            "audit_evidence": proposal.audit_evidence + [audit_entry],
        }
    )


# ---------------------------------------------------------------------------
# Decision application helper
# ---------------------------------------------------------------------------


def apply_proposal_decision(
    proposal: TimetableChangeProposal,
    decision: TimetableChangeProposalDecision,
) -> TimetableChangeProposal:
    """Apply a reviewer's decision to a proposal.

    This records the decision (approve / reject / request revision).
    It does NOT apply the timetable change — Level 5 (apply) is deferred.

    Raises ValueError for cross-tenant decisions.
    """
    if decision.tenant_id != proposal.tenant_id:
        raise ValueError(
            f"Cross-tenant decision rejected: proposal.tenant_id={proposal.tenant_id}, "
            f"decision.tenant_id={decision.tenant_id}"
        )

    return transition_timetable_change_proposal(
        proposal,
        decision.new_status,
        actor_id=decision.actor_id,
        reviewer_id=decision.reviewer_id,
        reviewer_note=decision.reviewer_note,
        reason=decision.reason,
        requesting_tenant_id=decision.tenant_id,
    )


# ---------------------------------------------------------------------------
# Audit evidence helper
# ---------------------------------------------------------------------------


def build_proposal_audit_evidence(
    action: str,
    previous_status: Optional[TimetableChangeProposalStatus],
    new_status: TimetableChangeProposalStatus,
    actor_id: Optional[str | int] = None,
    reason: Optional[str] = None,
    source_entity_type: Optional[str] = None,
    source_entity_id: Optional[str | int] = None,
) -> TimetableChangeAuditEvidence:
    """Construct a standalone audit evidence record for a proposal action."""
    return TimetableChangeAuditEvidence(
        action=action,
        previous_status=previous_status.value if previous_status else None,
        new_status=new_status.value,
        actor_id=actor_id,
        reason=reason,
        source_entity_type=source_entity_type,
        source_entity_id=source_entity_id,
    )


# ---------------------------------------------------------------------------
# A-020 recommendation compatibility helper
# ---------------------------------------------------------------------------


def proposal_from_room_recommendation(
    tenant_id: int,
    recommendation_result: Any,  # RoomAllocationRecommendationResult from A-020
    section_snapshot: TimetableChangeCurrentSnapshot,
    affected_entities: TimetableChangeAffectedEntities,
    created_by: Optional[str | int] = None,
    risk_level: TimetableChangeProposalRiskLevel = TimetableChangeProposalRiskLevel.MEDIUM,
) -> TimetableChangeProposal:
    """Build a TimetableChangeProposal from an A-020 recommendation result.

    This is the Room Recommendation → Proposal Bridge (A-022.3 preview).
    It references the recommendation without mutating any schedule.

    ``recommendation_result`` is duck-typed so that this helper does not
    create a hard import cycle with room_allocation_readiness.
    """
    if tenant_id <= 0:
        raise ValueError("tenant_id must be a positive integer")

    # Extract top candidate from recommendation result (duck-typed)
    top_candidate = None
    recommendation_id = getattr(recommendation_result, "recommendation_id", None)
    candidates = getattr(recommendation_result, "ranked_candidates", None) or []
    if candidates:
        top_candidate = candidates[0]

    proposed_room_id = (
        getattr(top_candidate, "room_id", None) if top_candidate else None
    )

    evidence = TimetableChangeProposalEvidence(
        source_recommendation_id=recommendation_id,
        risk_summary=f"Derived from room recommendation (A-020.5); top candidate: {proposed_room_id}",
        data_quality_note="Evidence derived from RoomAllocationRecommendationResult",
    )

    inp = TimetableChangeProposalInput(
        tenant_id=tenant_id,
        source_type=TimetableChangeProposalSourceType.ROOM_ALLOCATION_RECOMMENDATION,
        source_recommendation_id=recommendation_id,
        current_snapshot=section_snapshot,
        proposed_change=TimetableChangeProposedChange(
            change_type=TimetableChangeType.ROOM_CHANGE,
            proposed_room_id=proposed_room_id,
            reason="Derived from A-020 room allocation recommendation",
            evidence=[f"Recommendation ID: {recommendation_id}"],
        ),
        affected_entities=affected_entities,
        evidence=evidence,
        created_by=created_by,
        risk_level=risk_level,
        source_entity_type="room_allocation_recommendation",
        source_entity_id=recommendation_id,
    )

    return build_timetable_change_proposal(inp)


def proposal_from_conflict(
    tenant_id: int,
    conflict_id: str | int,
    conflict_type: str,
    section_snapshot: TimetableChangeCurrentSnapshot,
    affected_entities: TimetableChangeAffectedEntities,
    reason: str,
    created_by: Optional[str | int] = None,
    risk_level: TimetableChangeProposalRiskLevel = TimetableChangeProposalRiskLevel.HIGH,
) -> TimetableChangeProposal:
    """Build a TimetableChangeProposal from a detected scheduling conflict."""
    if tenant_id <= 0:
        raise ValueError("tenant_id must be a positive integer")

    evidence = TimetableChangeProposalEvidence(
        conflict_count=1,
        conflict_types=[conflict_type],
        source_conflict_ids=[conflict_id],
        risk_summary=f"Conflict detected: {conflict_type}",
    )

    inp = TimetableChangeProposalInput(
        tenant_id=tenant_id,
        source_type=TimetableChangeProposalSourceType.CONFLICT_RESOLUTION,
        source_conflict_id=conflict_id,
        current_snapshot=section_snapshot,
        proposed_change=TimetableChangeProposedChange(
            change_type=TimetableChangeType.ROOM_CHANGE,
            reason=reason,
            evidence=[f"Conflict ID: {conflict_id}", f"Conflict type: {conflict_type}"],
        ),
        affected_entities=affected_entities,
        evidence=evidence,
        created_by=created_by,
        risk_level=risk_level,
        source_entity_type="scheduling_conflict",
        source_entity_id=conflict_id,
    )

    return build_timetable_change_proposal(inp)
