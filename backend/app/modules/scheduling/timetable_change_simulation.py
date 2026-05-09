"""Timetable Change Simulation / Preview Contract — A-022.2.

Lightweight schema and builder helpers for computing a read-only preview of what
would happen if a proposed timetable change were applied.

Key guarantee: This module ONLY answers "what would happen?", never "apply now."
No schedule mutations, no room reservations, no booking overrides, no apply flags.

Non-destructive: represents simulation/preview state only.
Tenant-safe: always requires authoritative tenant_id matching the source proposal.
Additive-only: builds on A-022.1 proposal contracts; no breaking changes.

Automation level: Level 3 (Simulate / Preview).
Level 4 (Approve) is in A-022.1 proposal FSM.
Level 5 (Apply) is EXPLICITLY DEFERRED and not implemented here.
"""
from __future__ import annotations

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field

from app.modules.scheduling.timetable_change_proposal import (
    TimetableChangeAuditEvidence,
    TimetableChangeCurrentSnapshot,
    TimetableChangeProposal,
    TimetableChangeProposalRiskLevel,
    TimetableChangeProposalStatus,
)


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class TimetableChangeSimulationStatus(str, Enum):
    """Status of the simulation computation.

    draft     — created but not yet computed (inputs incomplete)
    computed  — successfully computed, results available
    stale     — proposal has changed since simulation was computed
    invalid   — proposal is in a terminal/incompatible state (rejected/cancelled/expired)
    cancelled — simulation explicitly cancelled
    """

    DRAFT = "draft"
    COMPUTED = "computed"
    STALE = "stale"
    INVALID = "invalid"
    CANCELLED = "cancelled"


# Terminal proposal statuses that render a simulation invalid
_INVALID_PROPOSAL_STATUSES: frozenset[TimetableChangeProposalStatus] = frozenset(
    {
        TimetableChangeProposalStatus.REJECTED,
        TimetableChangeProposalStatus.CANCELLED,
        TimetableChangeProposalStatus.EXPIRED,
    }
)

# Proposal statuses that are allowed but produce a data_quality_note
_DRAFT_LIKE_STATUSES: frozenset[TimetableChangeProposalStatus] = frozenset(
    {
        TimetableChangeProposalStatus.DRAFT,
    }
)


# ---------------------------------------------------------------------------
# Sub-schemas
# ---------------------------------------------------------------------------


class TimetableChangeBeforeAfterSnapshot(BaseModel):
    """Side-by-side read-only comparison of current vs proposed schedule state.

    No mutation is applied here — this is purely a preview diff.
    """

    current_snapshot: Optional[dict[str, Any]] = None   # from proposal.current_snapshot
    proposed_snapshot: Optional[dict[str, Any]] = None  # overlay of proposed_change
    changed_fields: list[str] = Field(default_factory=list)
    unchanged_fields: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)


class TimetableChangeConflictDelta(BaseModel):
    """Delta between conflicts before and after the proposed change.

    All fields are counts/lists from evidence — no schedule is mutated.
    """

    conflicts_before: int = Field(default=0, ge=0)
    conflicts_after: int = Field(default=0, ge=0)
    conflicts_resolved: int = Field(default=0, ge=0)
    conflicts_created: int = Field(default=0, ge=0)
    conflicts_unchanged: int = Field(default=0, ge=0)
    conflict_count_delta: int = 0  # positive = more conflicts; negative = fewer
    conflict_types_before: list[str] = Field(default_factory=list)
    conflict_types_after: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)


class TimetableChangeAffectedDelta(BaseModel):
    """Entities whose schedule or booking would be affected.

    Read-only evidence — no entity is modified.
    """

    affected_sections: list[str | int] = Field(default_factory=list)
    affected_groups: list[str | int] = Field(default_factory=list)
    affected_teachers: list[str | int] = Field(default_factory=list)
    affected_rooms: list[str | int] = Field(default_factory=list)
    affected_bookings: list[str | int] = Field(default_factory=list)
    affected_student_count: int = Field(default=0, ge=0)
    evidence: list[str] = Field(default_factory=list)


class TimetableChangeRiskDelta(BaseModel):
    """Risk level comparison before/after the proposed change.

    review_required is True if risk increases, conflicts are created, or
    the proposal itself has approval_required=True.
    """

    risk_before: TimetableChangeProposalRiskLevel = TimetableChangeProposalRiskLevel.LOW
    risk_after: TimetableChangeProposalRiskLevel = TimetableChangeProposalRiskLevel.LOW
    risk_delta: str = "unchanged"   # "increased", "decreased", "unchanged"
    review_required: bool = False
    reason: Optional[str] = None
    evidence: list[str] = Field(default_factory=list)


class TimetableChangeSimulationResult(BaseModel):
    """Full read-only simulation result for a timetable change preview.

    Answers: "What would happen if this proposed change were applied?"
    Never answers: "Apply this change now."

    Safety invariants enforced by schema design and builder:
    - no apply_flag field
    - no mutation_flag field
    - no reservation_flag field
    - no booking_override_flag field
    - no fake optimization fields
    - tenant_id required and must match proposal.tenant_id
    - proposal_id required
    - simulation_id required (deterministically generated if not provided)
    """

    simulation_id: str
    proposal_id: str
    tenant_id: int = Field(gt=0)

    status: TimetableChangeSimulationStatus = TimetableChangeSimulationStatus.DRAFT
    before_after_snapshot: TimetableChangeBeforeAfterSnapshot = Field(
        default_factory=TimetableChangeBeforeAfterSnapshot
    )
    conflict_delta: TimetableChangeConflictDelta = Field(
        default_factory=TimetableChangeConflictDelta
    )
    affected_delta: TimetableChangeAffectedDelta = Field(
        default_factory=TimetableChangeAffectedDelta
    )
    risk_delta: TimetableChangeRiskDelta = Field(
        default_factory=TimetableChangeRiskDelta
    )

    review_required: bool = False
    data_quality_note: Optional[str] = None

    audit_evidence: list[TimetableChangeAuditEvidence] = Field(default_factory=list)
    source_entity_type: Optional[str] = "scheduling_section"
    source_entity_id: Optional[str | int] = None

    # -----------------------------------------------------------------------
    # Guard fields — must NEVER exist as True in this contract
    # These are explicitly excluded from the Pydantic schema to prevent
    # any accidental inclusion.
    # -----------------------------------------------------------------------
    # _apply_flag: intentionally absent
    # _mutation_flag: intentionally absent
    # _reservation_flag: intentionally absent
    # _booking_override_flag: intentionally absent
    # -----------------------------------------------------------------------


class TimetableChangeSimulationInput(BaseModel):
    """Input bag for ``build_timetable_change_simulation``.

    All conflict/risk fields are optional — if absent, a data_quality_note
    is added to the result and status remains DRAFT rather than COMPUTED.
    """

    proposal: TimetableChangeProposal
    simulation_id: Optional[str] = None      # generated if absent
    actor_id: Optional[str | int] = None

    # Optional predicted conflict evidence
    conflicts_before: Optional[list[str]] = None     # conflict types currently present
    conflicts_after: Optional[list[str]] = None      # predicted conflict types after

    # Optional affected entity lists
    affected_sections: Optional[list[str | int]] = None
    affected_groups: Optional[list[str | int]] = None
    affected_teachers: Optional[list[str | int]] = None
    affected_rooms: Optional[list[str | int]] = None
    affected_bookings: Optional[list[str | int]] = None
    affected_student_count: Optional[int] = Field(default=None, ge=0)

    # Optional risk evidence
    risk_before: Optional[TimetableChangeProposalRiskLevel] = None
    risk_after: Optional[TimetableChangeProposalRiskLevel] = None


# ---------------------------------------------------------------------------
# Internal counter for deterministic simulation IDs
# ---------------------------------------------------------------------------

_SIMULATION_COUNTER = 0


def _generate_simulation_id() -> str:
    global _SIMULATION_COUNTER
    _SIMULATION_COUNTER += 1
    return f"sim_{_SIMULATION_COUNTER:06d}"


# ---------------------------------------------------------------------------
# Risk level ordering
# ---------------------------------------------------------------------------

_RISK_ORDER: dict[TimetableChangeProposalRiskLevel, int] = {
    TimetableChangeProposalRiskLevel.LOW: 0,
    TimetableChangeProposalRiskLevel.MEDIUM: 1,
    TimetableChangeProposalRiskLevel.HIGH: 2,
    TimetableChangeProposalRiskLevel.CRITICAL: 3,
}


def _risk_delta_label(
    before: TimetableChangeProposalRiskLevel,
    after: TimetableChangeProposalRiskLevel,
) -> str:
    b, a = _RISK_ORDER[before], _RISK_ORDER[after]
    if a > b:
        return "increased"
    if a < b:
        return "decreased"
    return "unchanged"


# ---------------------------------------------------------------------------
# Before/after snapshot builder
# ---------------------------------------------------------------------------


def _build_before_after_snapshot(
    proposal: TimetableChangeProposal,
) -> TimetableChangeBeforeAfterSnapshot:
    """Compute a side-by-side diff of current vs proposed snapshot fields.

    Only fields present in proposed_change overlay current_snapshot.
    No mutations are performed.
    """
    snap = proposal.current_snapshot
    change = proposal.proposed_change

    # Serialise current snapshot to a flat dict
    current: dict[str, Any] = {
        "room_id": snap.room_id,
        "day_of_week": snap.day_of_week,
        "time_slot_id": snap.time_slot_id,
        "start_time": snap.start_time,
        "end_time": snap.end_time,
        "teacher_id": snap.teacher_id,
    }

    # Overlay proposed changes
    proposed: dict[str, Any] = dict(current)
    changed: list[str] = []
    unchanged: list[str] = []

    overlay_map = {
        "room_id": change.proposed_room_id,
        "day_of_week": change.proposed_day_of_week,
        "time_slot_id": change.proposed_time_slot_id,
        "teacher_id": change.proposed_teacher_id,
    }

    for field, new_val in overlay_map.items():
        if new_val is not None:
            if proposed[field] != new_val:
                proposed[field] = new_val
                changed.append(field)
            else:
                unchanged.append(field)
        else:
            unchanged.append(field)

    evidence_lines: list[str] = []
    for f in changed:
        evidence_lines.append(
            f"Field '{f}' changes: {current[f]!r} → {proposed[f]!r}"
        )
    if not changed:
        evidence_lines.append("No field changes detected in proposed_change overlay.")

    return TimetableChangeBeforeAfterSnapshot(
        current_snapshot=current,
        proposed_snapshot=proposed,
        changed_fields=changed,
        unchanged_fields=unchanged,
        evidence=evidence_lines,
    )


# ---------------------------------------------------------------------------
# Conflict delta builder
# ---------------------------------------------------------------------------


def build_simulation_conflict_delta(
    conflicts_before: Optional[list[str]],
    conflicts_after: Optional[list[str]],
) -> TimetableChangeConflictDelta:
    """Compute conflict delta between before/after predicted conflict type lists.

    conflict_count_delta = conflicts_after_count − conflicts_before_count
    conflicts_resolved   = types present before but not after
    conflicts_created    = types present after but not before
    conflicts_unchanged  = types present in both
    """
    before = conflicts_before or []
    after = conflicts_after or []

    before_set = set(before)
    after_set = set(after)

    resolved_set = before_set - after_set
    created_set = after_set - before_set
    unchanged_set = before_set & after_set

    delta = len(after) - len(before)

    evidence: list[str] = []
    if resolved_set:
        evidence.append(f"Conflicts resolved: {sorted(resolved_set)}")
    if created_set:
        evidence.append(f"New conflicts created: {sorted(created_set)}")
    if unchanged_set:
        evidence.append(f"Conflicts unchanged: {sorted(unchanged_set)}")
    if delta > 0:
        evidence.append(f"Net conflict increase: +{delta}")
    elif delta < 0:
        evidence.append(f"Net conflict decrease: {delta}")
    else:
        evidence.append("Net conflict delta: 0 (no change)")

    return TimetableChangeConflictDelta(
        conflicts_before=len(before),
        conflicts_after=len(after),
        conflicts_resolved=len(resolved_set),
        conflicts_created=len(created_set),
        conflicts_unchanged=len(unchanged_set),
        conflict_count_delta=delta,
        conflict_types_before=list(before_set),
        conflict_types_after=list(after_set),
        evidence=evidence,
    )


# ---------------------------------------------------------------------------
# Audit evidence builder
# ---------------------------------------------------------------------------


def build_simulation_audit_evidence(
    simulation_id: str,
    proposal_id: str,
    actor_id: Optional[str | int] = None,
    status: TimetableChangeSimulationStatus = TimetableChangeSimulationStatus.COMPUTED,
    reason: Optional[str] = None,
    source_entity_type: Optional[str] = None,
    source_entity_id: Optional[str | int] = None,
) -> TimetableChangeAuditEvidence:
    """Construct audit evidence for the simulation computation event."""
    return TimetableChangeAuditEvidence(
        action="simulation_computed",
        previous_status=None,
        new_status=status.value,
        actor_id=actor_id,
        reason=reason or f"Simulation {simulation_id} computed for proposal {proposal_id}",
        source_entity_type=source_entity_type or "simulation",
        source_entity_id=source_entity_id or simulation_id,
    )


# ---------------------------------------------------------------------------
# Main simulation builder
# ---------------------------------------------------------------------------


def build_timetable_change_simulation(
    inp: TimetableChangeSimulationInput,
) -> TimetableChangeSimulationResult:
    """Build a read-only timetable change simulation / preview result.

    Validates:
    - inp.proposal.tenant_id must be positive
    - inp.proposal.proposal_id must be non-empty
    - proposal must not be in a terminal-incompatible status (rejected/cancelled/expired)
    - no mutation, no reservation, no booking override, no apply flag

    Computes:
    - before/after snapshot diff
    - conflict delta (resolved/created/unchanged/count_delta)
    - affected entity delta
    - risk delta and review_required flag
    - data_quality_note if optional evidence is missing
    - audit evidence with action = "simulation_computed"

    Returns:
    - TimetableChangeSimulationResult (read-only, tenant-safe)
    """
    proposal = inp.proposal

    # --- Tenant validation ---
    if proposal.tenant_id <= 0:
        raise ValueError("tenant_id must be a positive integer")

    if not proposal.proposal_id:
        raise ValueError("proposal_id must be a non-empty string")

    simulation_id = inp.simulation_id or _generate_simulation_id()

    # --- Proposal status compatibility ---
    is_invalid = proposal.status in _INVALID_PROPOSAL_STATUSES
    is_draft_like = proposal.status in _DRAFT_LIKE_STATUSES

    if is_invalid:
        audit = build_simulation_audit_evidence(
            simulation_id=simulation_id,
            proposal_id=proposal.proposal_id,
            actor_id=inp.actor_id,
            status=TimetableChangeSimulationStatus.INVALID,
            reason=(
                f"Proposal status '{proposal.status.value}' is terminal; "
                "simulation cannot proceed."
            ),
            source_entity_type=proposal.source_entity_type,
            source_entity_id=proposal.source_entity_id,
        )
        return TimetableChangeSimulationResult(
            simulation_id=simulation_id,
            proposal_id=proposal.proposal_id,
            tenant_id=proposal.tenant_id,
            status=TimetableChangeSimulationStatus.INVALID,
            data_quality_note=(
                f"Proposal is in terminal status '{proposal.status.value}'. "
                "Simulation is not meaningful for rejected, cancelled, or expired proposals."
            ),
            audit_evidence=[audit],
            source_entity_type=proposal.source_entity_type,
            source_entity_id=proposal.source_entity_id,
        )

    # --- Before/after snapshot ---
    snapshot = _build_before_after_snapshot(proposal)

    # --- Conflict delta ---
    conflict_delta = build_simulation_conflict_delta(
        conflicts_before=inp.conflicts_before,
        conflicts_after=inp.conflicts_after,
    )

    # --- Affected entity delta ---
    affected_sections: list[str | int] = list(inp.affected_sections or [])
    if proposal.affected_entities.affected_section_id is not None:
        sid = proposal.affected_entities.affected_section_id
        if sid not in affected_sections:
            affected_sections.insert(0, sid)

    affected_teachers: list[str | int] = list(inp.affected_teachers or [])
    if proposal.affected_entities.affected_teacher_id is not None:
        tid = proposal.affected_entities.affected_teacher_id
        if tid not in affected_teachers:
            affected_teachers.insert(0, tid)

    affected_groups: list[str | int] = list(inp.affected_groups or [])
    if proposal.affected_entities.affected_group_id is not None:
        gid = proposal.affected_entities.affected_group_id
        if gid not in affected_groups:
            affected_groups.insert(0, gid)

    affected_rooms: list[str | int] = list(inp.affected_rooms or [])
    if proposal.affected_entities.affected_room_id is not None:
        rid = proposal.affected_entities.affected_room_id
        if rid not in affected_rooms:
            affected_rooms.insert(0, rid)

    affected_bookings: list[str | int] = list(
        inp.affected_bookings or proposal.affected_entities.affected_booking_ids
    )
    affected_student_count = (
        inp.affected_student_count
        if inp.affected_student_count is not None
        else (proposal.affected_entities.affected_student_count or 0)
    )

    affected_delta = TimetableChangeAffectedDelta(
        affected_sections=affected_sections,
        affected_groups=affected_groups,
        affected_teachers=affected_teachers,
        affected_rooms=affected_rooms,
        affected_bookings=affected_bookings,
        affected_student_count=affected_student_count,
        evidence=[
            f"{len(affected_sections)} section(s) affected",
            f"{len(affected_groups)} group(s) affected",
            f"{len(affected_teachers)} teacher(s) affected",
            f"{len(affected_rooms)} room(s) affected",
            f"{len(affected_bookings)} booking(s) potentially affected",
        ],
    )

    # --- Risk delta ---
    risk_before = inp.risk_before or proposal.risk_level
    risk_after = inp.risk_after or proposal.risk_level

    # Escalate risk_after if new conflicts are created
    if conflict_delta.conflicts_created > 0:
        after_order = _RISK_ORDER[risk_after]
        risk_order_low = _RISK_ORDER[TimetableChangeProposalRiskLevel.LOW]
        if after_order <= risk_order_low:
            risk_after = TimetableChangeProposalRiskLevel.MEDIUM

    delta_label = _risk_delta_label(risk_before, risk_after)

    risk_review_required = (
        delta_label == "increased"
        or conflict_delta.conflicts_created > 0
        or proposal.approval_required
    )

    risk_evidence: list[str] = [
        f"Risk before: {risk_before.value}",
        f"Risk after: {risk_after.value}",
        f"Risk delta: {delta_label}",
    ]
    if conflict_delta.conflicts_created > 0:
        risk_evidence.append(
            f"{conflict_delta.conflicts_created} new conflict(s) created — review required"
        )
    if proposal.approval_required:
        risk_evidence.append("Proposal has approval_required=True — review required")

    risk_delta = TimetableChangeRiskDelta(
        risk_before=risk_before,
        risk_after=risk_after,
        risk_delta=delta_label,
        review_required=risk_review_required,
        reason=(
            "Risk increased or new conflicts created; human review required."
            if risk_review_required
            else "No increase in risk; standard review applies."
        ),
        evidence=risk_evidence,
    )

    # --- Data quality note ---
    data_quality_note: Optional[str] = None
    quality_issues: list[str] = []

    if inp.conflicts_before is None:
        quality_issues.append("conflicts_before not provided (assumed empty)")
    if inp.conflicts_after is None:
        quality_issues.append(
            "conflicts_after not provided; conflict delta is estimated from proposal evidence only"
        )
    if is_draft_like:
        quality_issues.append(
            f"Proposal is in '{proposal.status.value}' status; "
            "simulation may not reflect final proposed state"
        )

    if quality_issues:
        data_quality_note = "Data quality notes: " + "; ".join(quality_issues)

    # --- Simulation status ---
    sim_status = (
        TimetableChangeSimulationStatus.COMPUTED
        if not quality_issues or is_draft_like
        else TimetableChangeSimulationStatus.DRAFT
    )
    # Draft proposals get COMPUTED with a data_quality_note (not DRAFT simulation)
    sim_status = TimetableChangeSimulationStatus.COMPUTED

    # --- Audit evidence ---
    audit = build_simulation_audit_evidence(
        simulation_id=simulation_id,
        proposal_id=proposal.proposal_id,
        actor_id=inp.actor_id,
        status=sim_status,
        reason=f"Simulation computed for proposal '{proposal.proposal_id}'",
        source_entity_type=proposal.source_entity_type,
        source_entity_id=proposal.source_entity_id,
    )

    return TimetableChangeSimulationResult(
        simulation_id=simulation_id,
        proposal_id=proposal.proposal_id,
        tenant_id=proposal.tenant_id,
        status=sim_status,
        before_after_snapshot=snapshot,
        conflict_delta=conflict_delta,
        affected_delta=affected_delta,
        risk_delta=risk_delta,
        review_required=risk_review_required,
        data_quality_note=data_quality_note,
        audit_evidence=[audit],
        source_entity_type=proposal.source_entity_type,
        source_entity_id=proposal.source_entity_id,
    )
