"""Room Allocation Readiness Contract — A-020.1 / A-020.2 / A-020.3.

Lightweight schema for normalizing room allocation readiness evidence
across scheduling, room_booking, Brain Core, KPI and frontend surfaces.

Non-destructive: represents readiness state, never mutations.
Tenant-safe: always requires authoritative tenant_id.
Additive-only: builds on existing signals, no breaking changes.
"""
from __future__ import annotations

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


STANDARD_ROOM_TYPES: frozenset[str] = frozenset(
    {
        "classroom",
        "lecture_hall",
        "computer_lab",
        "laboratory",
        "seminar_room",
        "auditorium",
        "hybrid_room",
        "meeting_room",
    }
)

STANDARD_LESSON_TYPES: frozenset[str] = frozenset(
    {
        "lecture",
        "seminar",
        "lab",
        "practice",
        "exam",
        "event",
    }
)


class RoomAllocationRequirement(BaseModel):
    """What a section/group requires from a room."""

    section_id: int
    course_id: int
    group_id: Optional[int] = None
    teacher_id: Optional[str] = None
    students_count: int = Field(ge=0)
    max_capacity: int = Field(ge=0)
    required_room_type: Optional[str] = None  # "lecture" | "lab" | "seminar" or None
    required_computers: Optional[int] = None  # number of computers needed, None if not required
    equipment_required: Optional[list[str]] = None  # e.g., ["projector", "whiteboard"]
    required_lesson_type: Optional[str] = None
    restrictions_required: Optional[list[str]] = None


class RoomAllocationAvailability(BaseModel):
    """What a room can provide."""

    room_id: str | int
    room_name: Optional[str] = None
    room_capacity: int = Field(ge=0)
    room_type: Optional[str] = None  # "lecture" | "lab" | "seminar" or None
    computers_count: Optional[int] = None
    equipment_available: Optional[list[str]] = None  # e.g., ["projector", "whiteboard"]
    location: Optional[str] = None  # building/floor if available
    is_available: bool = True  # based on booking status


class RoomAllocationSchedule(BaseModel):
    """When the room is needed."""

    day_of_week: Optional[str] = None  # "monday" .. "sunday"
    time_slot_id: Optional[int] = None
    start_time: Optional[str] = None  # "09:00:00"
    end_time: Optional[str] = None  # "10:30:00"
    term_id: Optional[int] = None


class RoomAllocationEvidence(BaseModel):
    """Readiness state — no mutations, evidence only."""

    capacity_mismatch: bool = False  # required > available
    room_conflict: bool = False  # room double-booked or unavailable
    room_allocation_required: bool = False  # room needs to be allocated
    conflict_type: Optional[str] = None  # e.g., "scheduling", "booking", "capacity"
    reason: Optional[str] = None  # human-readable why allocation is needed
    source_entity_type: Optional[str] = None  # "section" | "booking" | "schedule"
    source_entity_id: Optional[str | int] = None  # entity that triggered signal


class RoomCapability(BaseModel):
    """Room inventory/capability contract for A-020.2.

    This contract is evidence-only and does not mutate booking or schedule state.
    Unknown capability values are represented as evidence and do not crash validation.
    """

    tenant_id: int = Field(gt=0)
    room_id: str | int
    room_code: Optional[str] = None
    room_name: Optional[str] = None
    room_type: Optional[str] = None
    capacity: Optional[int] = Field(default=None, ge=0)
    computers_count: Optional[int] = Field(default=None, ge=0)
    equipment_available: list[str] = Field(default_factory=list)
    supported_lesson_types: list[str] = Field(default_factory=list)
    accessibility_features: list[str] = Field(default_factory=list)
    campus: Optional[str] = None
    building: Optional[str] = None
    floor: Optional[str] = None
    availability_status: Optional[str] = None
    booking_status: Optional[str] = None
    maintenance_status: Optional[str] = None
    restrictions: list[str] = Field(default_factory=list)
    is_active: bool = True
    evidence: dict[str, Any] = Field(default_factory=dict)
    source_entity_type: str = "campus_room"
    source_entity_id: str


class RoomCapabilityMatchEvidence(BaseModel):
    """Evidence-only compatibility output: room capability vs room requirement."""

    capacity_ok: bool | None = None
    computers_ok: bool | None = None
    equipment_ok: bool | None = None
    room_type_ok: bool | None = None
    availability_ok: bool | None = None
    restrictions_ok: bool | None = None
    mismatch_reasons: list[str] = Field(default_factory=list)
    missing_equipment: list[str] = Field(default_factory=list)
    equipment_match_score: float | None = None
    room_allocation_required: bool = False


class RoomAllocationReadiness(BaseModel):
    """
    Complete room allocation readiness contract.

    Represents the current state of whether a section/group has adequate
    room allocation. Purely evidential — never causes mutations.

    Non-destructive guarantee:
    - No automatic room reassignment
    - No automatic schedule changes
    - No booking overrides
    - No fake optimization
    """

    # Mandatory context
    tenant_id: int = Field(gt=0, description="Authoritative tenant ID")

    # Requirement, availability, schedule
    requirement: RoomAllocationRequirement
    availability: Optional[RoomAllocationAvailability] = None
    schedule: Optional[RoomAllocationSchedule] = None

    # Evidence
    evidence: RoomAllocationEvidence

    # Metadata
    is_satisfied: bool  # convenience: True if no_mismatch AND no_conflict AND room_adequate
    requires_action: bool  # convenience: True if allocation_required or conflict detected
    priority: str = "normal"  # "low" | "normal" | "high"
    notes: Optional[str] = None  # additional context

    class Config:
        """Pydantic config."""

        from_attributes = True


def _normalize_tokens(values: list[str] | None) -> set[str]:
    if not values:
        return set()
    return {str(value).strip().lower() for value in values if str(value).strip()}


def _room_is_available(capability: RoomCapability) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    if not capability.is_active:
        reasons.append("room_inactive")

    maintenance = str(capability.maintenance_status or "").strip().lower()
    if maintenance in {"maintenance", "out_of_service", "closed"}:
        reasons.append("room_under_maintenance")

    availability = str(capability.availability_status or "").strip().lower()
    if availability in {"unavailable", "occupied", "blocked"}:
        reasons.append("room_unavailable")

    booking = str(capability.booking_status or "").strip().lower()
    if booking in {"reserved", "occupied", "approved"}:
        reasons.append("room_reserved_or_occupied")

    return (len(reasons) == 0, reasons)


def to_room_allocation_availability(
    capability: RoomCapability,
    *,
    authoritative_tenant_id: int | None = None,
) -> RoomAllocationAvailability:
    """Convert RoomCapability to RoomAllocationAvailability without side effects."""
    if authoritative_tenant_id is not None and int(authoritative_tenant_id) != int(capability.tenant_id):
        raise ValueError("authoritative tenant_id mismatch for room capability")

    is_available, _ = _room_is_available(capability)
    location_parts = [part for part in [capability.campus, capability.building, capability.floor] if part]
    location = ", ".join(location_parts) if location_parts else None

    return RoomAllocationAvailability(
        room_id=capability.room_id,
        room_name=capability.room_name or capability.room_code,
        room_capacity=int(capability.capacity or 0),
        room_type=capability.room_type,
        computers_count=capability.computers_count,
        equipment_available=list(capability.equipment_available),
        location=location,
        is_available=is_available,
    )


def assess_room_capability_against_requirement(
    capability: RoomCapability,
    requirement: RoomAllocationRequirement,
    *,
    authoritative_tenant_id: int | None = None,
) -> RoomCapabilityMatchEvidence:
    """Build evidence-only capability matching result.

    This helper does not reserve rooms and does not mutate schedule/booking data.
    """
    if authoritative_tenant_id is not None and int(authoritative_tenant_id) != int(capability.tenant_id):
        raise ValueError("authoritative tenant_id mismatch for room capability")

    mismatch_reasons: list[str] = []

    capacity_ok: bool | None = None
    if capability.capacity is not None and requirement.students_count is not None:
        capacity_ok = int(capability.capacity) >= int(requirement.students_count)
        if not capacity_ok:
            mismatch_reasons.append("capacity_shortage")

    computers_ok: bool | None = None
    if requirement.required_computers is not None:
        if capability.computers_count is None:
            computers_ok = None
            mismatch_reasons.append("computers_count_unknown")
        else:
            computers_ok = int(capability.computers_count) >= int(requirement.required_computers)
            if not computers_ok:
                mismatch_reasons.append("computers_shortage")

    room_type_ok: bool | None = None
    if requirement.required_room_type:
        room_type_ok = str(requirement.required_room_type).strip().lower() == str(capability.room_type or "").strip().lower()
        if not room_type_ok:
            mismatch_reasons.append("room_type_mismatch")

    equipment_required = _normalize_tokens(requirement.equipment_required)
    equipment_available = _normalize_tokens(capability.equipment_available)
    missing_equipment = sorted(list(equipment_required - equipment_available))
    equipment_ok: bool | None = None
    equipment_match_score: float | None = None
    if equipment_required:
        equipment_ok = len(missing_equipment) == 0
        equipment_match_score = round((len(equipment_required) - len(missing_equipment)) / len(equipment_required), 3)
        if not equipment_ok:
            mismatch_reasons.append("equipment_mismatch")

    restrictions_ok: bool | None = None
    required_restrictions = _normalize_tokens(requirement.restrictions_required)
    room_restrictions = _normalize_tokens(capability.restrictions)
    if required_restrictions:
        restrictions_ok = required_restrictions.issubset(room_restrictions)
        if not restrictions_ok:
            mismatch_reasons.append("restrictions_mismatch")

    availability_ok, availability_reasons = _room_is_available(capability)
    mismatch_reasons.extend(availability_reasons)

    room_allocation_required = bool(
        (capacity_ok is False)
        or (computers_ok is False)
        or (equipment_ok is False)
        or (room_type_ok is False)
        or (availability_ok is False)
        or (restrictions_ok is False)
    )

    return RoomCapabilityMatchEvidence(
        capacity_ok=capacity_ok,
        computers_ok=computers_ok,
        equipment_ok=equipment_ok,
        room_type_ok=room_type_ok,
        availability_ok=availability_ok,
        restrictions_ok=restrictions_ok,
        mismatch_reasons=mismatch_reasons,
        missing_equipment=missing_equipment,
        equipment_match_score=equipment_match_score,
        room_allocation_required=room_allocation_required,
    )


def build_room_capability_evidence(
    capability: RoomCapability,
    requirement: RoomAllocationRequirement,
    *,
    authoritative_tenant_id: int | None = None,
) -> dict[str, Any]:
    """Return serializable evidence payload for room capability checks."""
    match = assess_room_capability_against_requirement(
        capability,
        requirement,
        authoritative_tenant_id=authoritative_tenant_id,
    )
    return match.model_dump()


# Convenience helpers for event/context source conversion


def room_allocation_readiness_from_event_payload(
    tenant_id: int,
    payload: dict[str, Any],
) -> RoomAllocationReadiness:
    """
    Convert a scheduling.room_allocation event payload to readiness contract.

    Extracts requirement, availability, evidence from event payload.
    Assumes caller has validated tenant_id.
    """
    if not tenant_id or tenant_id <= 0:
        raise ValueError("tenant_id must be a positive integer")

    # Extract requirement fields
    section_id = payload.get("section_id")
    course_id = payload.get("course_id")
    students_count = payload.get("enrolled_count") or payload.get("students_count", 0)
    max_capacity = payload.get("max_capacity", 0)
    required_capacity = payload.get("required_capacity")

    requirement = RoomAllocationRequirement(
        section_id=section_id,
        course_id=course_id,
        group_id=payload.get("group_id"),
        teacher_id=payload.get("teacher_id") or payload.get("instructor_id"),
        students_count=int(students_count),
        max_capacity=int(max_capacity),
        required_room_type=payload.get("required_room_type"),
        required_computers=payload.get("required_computers"),
        equipment_required=payload.get("equipment_required"),
    )

    # Extract availability fields
    room_id = payload.get("room_id")
    room_capacity = payload.get("room_capacity")
    availability = None
    if room_id:
        availability = RoomAllocationAvailability(
            room_id=room_id,
            room_name=payload.get("room_name"),
            room_capacity=int(room_capacity) if room_capacity else 0,
            room_type=payload.get("room_type"),
            computers_count=payload.get("computers_count"),
            equipment_available=payload.get("equipment_available"),
            location=payload.get("location"),
            is_available=payload.get("is_available", True),
        )

    # Extract schedule
    schedule = RoomAllocationSchedule(
        day_of_week=payload.get("day_of_week"),
        time_slot_id=payload.get("time_slot_id"),
        start_time=payload.get("start_time"),
        end_time=payload.get("end_time"),
        term_id=payload.get("term_id"),
    )

    # Extract evidence
    capacity_mismatch = False
    if required_capacity and room_capacity:
        try:
            capacity_mismatch = int(required_capacity) > int(room_capacity)
        except (TypeError, ValueError):
            capacity_mismatch = False

    evidence = RoomAllocationEvidence(
        capacity_mismatch=capacity_mismatch,
        room_conflict=payload.get("room_conflict", False),
        room_allocation_required=payload.get("room_allocation_required", False),
        conflict_type=payload.get("conflict_type"),
        reason=payload.get("reason"),
        source_entity_type=payload.get("source_entity_type"),
        source_entity_id=payload.get("source_entity_id"),
    )

    # Compute convenience flags
    is_satisfied = (
        not capacity_mismatch
        and not evidence.room_conflict
        and (room_id is not None if required_capacity else True)
    )
    requires_action = evidence.room_allocation_required or evidence.room_conflict

    return RoomAllocationReadiness(
        tenant_id=tenant_id,
        requirement=requirement,
        availability=availability,
        schedule=schedule,
        evidence=evidence,
        is_satisfied=is_satisfied,
        requires_action=requires_action,
        priority=payload.get("priority", "normal"),
        notes=payload.get("notes"),
    )


def room_allocation_readiness_from_scheduling_context(
    context: dict[str, Any],
) -> RoomAllocationReadiness:
    """
    Convert brain_core scheduling context to readiness contract.

    Used when Brain Core fetch_scheduling_context is available.
    Validates tenant_id from context (must be present).
    """
    tenant_id = context.get("tenant_id")
    if not tenant_id or tenant_id <= 0:
        raise ValueError("context must include positive tenant_id")

    # Extract requirement
    requirement = RoomAllocationRequirement(
        section_id=context.get("section_id"),
        course_id=context.get("course_id"),
        group_id=context.get("group_id"),
        teacher_id=context.get("faculty_id") or context.get("instructor_id"),
        students_count=int(context.get("enrolled_count", 0)),
        max_capacity=int(context.get("max_capacity", 0)),
        required_room_type=context.get("required_room_type"),
        required_computers=context.get("required_computers"),
        equipment_required=context.get("equipment_required"),
    )

    # Extract availability
    room_id = context.get("room_id")
    room_capacity = context.get("room_capacity")
    availability = None
    if room_id:
        availability = RoomAllocationAvailability(
            room_id=room_id,
            room_capacity=int(room_capacity) if room_capacity else 0,
            room_type=context.get("room_type"),
        )

    # Extract schedule (minimal in context source)
    schedule = RoomAllocationSchedule(
        term_id=context.get("term_id"),
    )

    # Extract evidence
    evidence = RoomAllocationEvidence(
        room_allocation_required=context.get("room_allocation_required", False),
        conflict_type=context.get("conflict_type"),
        reason=context.get("reason"),
        source_entity_type=context.get("source_entity_type"),
        source_entity_id=context.get("source_entity_id"),
    )

    # Compute convenience flags
    required_capacity = context.get("required_capacity")
    is_satisfied = not evidence.room_allocation_required
    requires_action = evidence.room_allocation_required

    return RoomAllocationReadiness(
        tenant_id=tenant_id,
        requirement=requirement,
        availability=availability,
        schedule=schedule,
        evidence=evidence,
        is_satisfied=is_satisfied,
        requires_action=requires_action,
    )


# ─── A-020.3 Scheduling Conflict Detection Enhancement ────────────────────────


class ConflictType(str, Enum):
    """Enumeration of detectable scheduling conflict types."""

    ROOM_TIME_CONFLICT = "room_time_conflict"
    TEACHER_TIME_CONFLICT = "teacher_time_conflict"
    GROUP_TIME_CONFLICT = "group_time_conflict"
    CAPACITY_MISMATCH = "capacity_mismatch"
    COMPUTER_SHORTAGE = "computer_shortage"
    ROOM_TYPE_MISMATCH = "room_type_mismatch"
    EQUIPMENT_MISMATCH = "equipment_mismatch"
    ROOM_UNAVAILABLE = "room_unavailable"
    BOOKING_CONFLICT = "booking_conflict"
    RESTRICTION_MISMATCH = "restriction_mismatch"


class ConflictSeverity(str, Enum):
    """Impact severity of a detected conflict."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


_CONFLICT_SEVERITY_MAP: dict[ConflictType, ConflictSeverity] = {
    ConflictType.ROOM_TIME_CONFLICT: ConflictSeverity.CRITICAL,
    ConflictType.TEACHER_TIME_CONFLICT: ConflictSeverity.CRITICAL,
    ConflictType.GROUP_TIME_CONFLICT: ConflictSeverity.CRITICAL,
    ConflictType.CAPACITY_MISMATCH: ConflictSeverity.HIGH,
    ConflictType.COMPUTER_SHORTAGE: ConflictSeverity.MEDIUM,
    ConflictType.ROOM_TYPE_MISMATCH: ConflictSeverity.HIGH,
    ConflictType.EQUIPMENT_MISMATCH: ConflictSeverity.MEDIUM,
    ConflictType.ROOM_UNAVAILABLE: ConflictSeverity.HIGH,
    ConflictType.BOOKING_CONFLICT: ConflictSeverity.CRITICAL,
    ConflictType.RESTRICTION_MISMATCH: ConflictSeverity.LOW,
}


class SchedulingConflictEvidence(BaseModel):
    """Evidence record for a single detected scheduling conflict.

    Evidence-only: never mutates schedule, booking, or room state.
    Tenant-safe: tenant_id must be positive.
    """

    tenant_id: int = Field(gt=0)
    conflict_type: ConflictType
    severity: ConflictSeverity
    section_id: Optional[int] = None
    course_id: Optional[int] = None
    group_id: Optional[int] = None
    teacher_id: Optional[str] = None
    room_id: Optional[str | int] = None
    day_of_week: Optional[str] = None
    time_slot: Optional[str | int] = None
    conflicting_entity_type: Optional[str] = None
    conflicting_entity_id: Optional[str | int] = None
    reason: str
    evidence: dict[str, Any] = Field(default_factory=dict)
    source_entity_type: Optional[str] = None
    source_entity_id: Optional[str | int] = None


class SchedulingConflictCheckInput(BaseModel):
    """Input bag for the conflict detection helper.

    All detection is evidence-only — no schedule or booking mutations.
    """

    tenant_id: int = Field(gt=0)
    requirement: RoomAllocationRequirement
    capability: Optional[RoomCapability] = None
    capability_match: Optional[RoomCapabilityMatchEvidence] = None
    schedule: Optional[RoomAllocationSchedule] = None
    # existing bookings: list of dicts with keys: room_id, day_of_week, time_slot_id
    existing_bookings: list[dict[str, Any]] = Field(default_factory=list)
    # teacher schedules: list of dicts with keys: teacher_id, day_of_week, time_slot_id
    teacher_schedules: list[dict[str, Any]] = Field(default_factory=list)
    # group schedules: list of dicts with keys: group_id, day_of_week, time_slot_id
    group_schedules: list[dict[str, Any]] = Field(default_factory=list)


class SchedulingConflictResult(BaseModel):
    """Aggregated result of a scheduling conflict detection run.

    Evidence-only output: no auto-resolution, no ranking, no auto-assignment.
    """

    tenant_id: int = Field(gt=0)
    has_conflicts: bool
    conflict_count: int
    conflicts: list[SchedulingConflictEvidence]
    severity_summary: dict[str, int] = Field(default_factory=dict)


def _make_conflict(
    tenant_id: int,
    conflict_type: ConflictType,
    reason: str,
    *,
    section_id: Optional[int] = None,
    course_id: Optional[int] = None,
    group_id: Optional[int] = None,
    teacher_id: Optional[str] = None,
    room_id: Optional[str | int] = None,
    day_of_week: Optional[str] = None,
    time_slot: Optional[str | int] = None,
    conflicting_entity_type: Optional[str] = None,
    conflicting_entity_id: Optional[str | int] = None,
    evidence: Optional[dict[str, Any]] = None,
    source_entity_type: Optional[str] = None,
    source_entity_id: Optional[str | int] = None,
) -> SchedulingConflictEvidence:
    return SchedulingConflictEvidence(
        tenant_id=tenant_id,
        conflict_type=conflict_type,
        severity=_CONFLICT_SEVERITY_MAP[conflict_type],
        section_id=section_id,
        course_id=course_id,
        group_id=group_id,
        teacher_id=teacher_id,
        room_id=room_id,
        day_of_week=day_of_week,
        time_slot=time_slot,
        conflicting_entity_type=conflicting_entity_type,
        conflicting_entity_id=conflicting_entity_id,
        reason=reason,
        evidence=evidence or {},
        source_entity_type=source_entity_type,
        source_entity_id=source_entity_id,
    )


def detect_room_requirement_conflicts(
    tenant_id: int,
    requirement: RoomAllocationRequirement,
    *,
    capability: Optional[RoomCapability] = None,
    capability_match: Optional[RoomCapabilityMatchEvidence] = None,
    schedule: Optional[RoomAllocationSchedule] = None,
    existing_bookings: Optional[list[dict[str, Any]]] = None,
    teacher_schedules: Optional[list[dict[str, Any]]] = None,
    group_schedules: Optional[list[dict[str, Any]]] = None,
) -> list[SchedulingConflictEvidence]:
    """Detect scheduling conflicts and return evidence-only list.

    Non-destructive guarantee:
    - Never assigns a room.
    - Never reserves a room.
    - Never moves a section.
    - Never changes timetable.
    - Never ranks candidate rooms.
    - Returns evidence records only.

    Cross-tenant safety:
    - tenant_id must match capability.tenant_id when capability provided.
    - tenant_id must be a positive integer.

    Args:
        tenant_id: Authoritative tenant ID (must be positive).
        requirement: Room allocation requirement for the section.
        capability: Optional room capability for capability-based checks.
        capability_match: Pre-computed match evidence; computed if not provided.
        schedule: Optional schedule context for slot-based checks.
        existing_bookings: Bookings to check for room/booking conflicts.
            Each entry: {room_id, day_of_week, time_slot_id}.
        teacher_schedules: Schedule entries to check for teacher conflicts.
            Each entry: {teacher_id, day_of_week, time_slot_id}.
        group_schedules: Schedule entries to check for group conflicts.
            Each entry: {group_id, day_of_week, time_slot_id}.

    Returns:
        List of SchedulingConflictEvidence. Empty list means no conflicts found.
    """
    if not isinstance(tenant_id, int) or tenant_id <= 0:
        raise ValueError("tenant_id must be a positive integer")

    conflicts: list[SchedulingConflictEvidence] = []
    day = schedule.day_of_week if schedule else None
    slot = schedule.time_slot_id if schedule else None

    # ── Capability-based checks (capacity, computers, equipment, type, availability, restrictions) ──
    if capability is not None:
        # Validate tenant boundary
        if int(capability.tenant_id) != int(tenant_id):
            raise ValueError("capability.tenant_id does not match authoritative tenant_id")

        if capability_match is None:
            capability_match = assess_room_capability_against_requirement(
                capability,
                requirement,
                authoritative_tenant_id=tenant_id,
            )

        room_id = capability.room_id
        section_id = requirement.section_id
        course_id = requirement.course_id

        # Capacity mismatch
        if capability_match.capacity_ok is False:
            conflicts.append(_make_conflict(
                tenant_id,
                ConflictType.CAPACITY_MISMATCH,
                reason=f"Room capacity {capability.capacity} < required {requirement.students_count}",
                section_id=section_id,
                course_id=course_id,
                room_id=room_id,
                day_of_week=day,
                time_slot=slot,
                evidence={"room_capacity": capability.capacity, "required": requirement.students_count},
                source_entity_type="room_capability",
                source_entity_id=str(room_id),
            ))

        # Computer shortage
        if capability_match.computers_ok is False:
            conflicts.append(_make_conflict(
                tenant_id,
                ConflictType.COMPUTER_SHORTAGE,
                reason=f"Room computers {capability.computers_count} < required {requirement.required_computers}",
                section_id=section_id,
                course_id=course_id,
                room_id=room_id,
                day_of_week=day,
                time_slot=slot,
                evidence={"room_computers": capability.computers_count, "required": requirement.required_computers},
                source_entity_type="room_capability",
                source_entity_id=str(room_id),
            ))

        # Room type mismatch
        if capability_match.room_type_ok is False:
            conflicts.append(_make_conflict(
                tenant_id,
                ConflictType.ROOM_TYPE_MISMATCH,
                reason=f"Room type '{capability.room_type}' does not match required '{requirement.required_room_type}'",
                section_id=section_id,
                course_id=course_id,
                room_id=room_id,
                day_of_week=day,
                time_slot=slot,
                evidence={"room_type": capability.room_type, "required_type": requirement.required_room_type},
                source_entity_type="room_capability",
                source_entity_id=str(room_id),
            ))

        # Equipment mismatch
        if capability_match.equipment_ok is False:
            conflicts.append(_make_conflict(
                tenant_id,
                ConflictType.EQUIPMENT_MISMATCH,
                reason=f"Missing equipment: {capability_match.missing_equipment}",
                section_id=section_id,
                course_id=course_id,
                room_id=room_id,
                day_of_week=day,
                time_slot=slot,
                evidence={"missing_equipment": capability_match.missing_equipment, "match_score": capability_match.equipment_match_score},
                source_entity_type="room_capability",
                source_entity_id=str(room_id),
            ))

        # Room unavailable / inactive / maintenance
        if capability_match.availability_ok is False:
            unavail_reasons = [r for r in capability_match.mismatch_reasons if r in {
                "room_inactive", "room_under_maintenance", "room_unavailable", "room_reserved_or_occupied"
            }]
            conflicts.append(_make_conflict(
                tenant_id,
                ConflictType.ROOM_UNAVAILABLE,
                reason=f"Room is not available: {unavail_reasons or capability_match.mismatch_reasons}",
                section_id=section_id,
                course_id=course_id,
                room_id=room_id,
                day_of_week=day,
                time_slot=slot,
                evidence={"unavailability_reasons": unavail_reasons, "is_active": capability.is_active,
                          "maintenance_status": capability.maintenance_status, "availability_status": capability.availability_status},
                source_entity_type="room_capability",
                source_entity_id=str(room_id),
            ))

        # Restriction mismatch
        if capability_match.restrictions_ok is False:
            conflicts.append(_make_conflict(
                tenant_id,
                ConflictType.RESTRICTION_MISMATCH,
                reason="Required restrictions not satisfied by this room",
                section_id=section_id,
                course_id=course_id,
                room_id=room_id,
                day_of_week=day,
                time_slot=slot,
                evidence={"required_restrictions": requirement.restrictions_required, "room_restrictions": list(capability.restrictions)},
                source_entity_type="room_capability",
                source_entity_id=str(room_id),
            ))

    # ── Booking-based checks (room_time_conflict / booking_conflict) ──
    if existing_bookings and schedule:
        req_room_id = (capability.room_id if capability else None) or getattr(requirement, "room_id", None)
        for booking in existing_bookings:
            b_room_id = booking.get("room_id")
            b_day = str(booking.get("day_of_week", "")).lower()
            b_slot = booking.get("time_slot_id")
            b_section = booking.get("section_id")
            b_type = booking.get("booking_type", "schedule")

            if b_room_id is None or b_day != str(day or "").lower() or b_slot != slot:
                continue

            if req_room_id is not None and str(b_room_id) == str(req_room_id):
                conflict_type = ConflictType.BOOKING_CONFLICT if b_type == "booking" else ConflictType.ROOM_TIME_CONFLICT
                conflicts.append(_make_conflict(
                    tenant_id,
                    conflict_type,
                    reason=f"Room {b_room_id} already occupied on {day} slot {slot}",
                    section_id=requirement.section_id,
                    course_id=requirement.course_id,
                    room_id=b_room_id,
                    day_of_week=day,
                    time_slot=slot,
                    conflicting_entity_type=b_type,
                    conflicting_entity_id=b_section or b_room_id,
                    evidence={"conflicting_booking": booking},
                    source_entity_type="section",
                    source_entity_id=requirement.section_id,
                ))

    # ── Teacher conflict checks ──
    if teacher_schedules and schedule and requirement.teacher_id:
        for entry in teacher_schedules:
            e_teacher = str(entry.get("teacher_id", ""))
            e_day = str(entry.get("day_of_week", "")).lower()
            e_slot = entry.get("time_slot_id")
            e_section = entry.get("section_id")

            if (e_teacher == str(requirement.teacher_id)
                    and e_day == str(day or "").lower()
                    and e_slot == slot
                    and e_section != requirement.section_id):
                conflicts.append(_make_conflict(
                    tenant_id,
                    ConflictType.TEACHER_TIME_CONFLICT,
                    reason=f"Teacher {requirement.teacher_id} already assigned to section {e_section} on {day} slot {slot}",
                    section_id=requirement.section_id,
                    course_id=requirement.course_id,
                    teacher_id=requirement.teacher_id,
                    day_of_week=day,
                    time_slot=slot,
                    conflicting_entity_type="section",
                    conflicting_entity_id=e_section,
                    evidence={"conflicting_entry": entry},
                    source_entity_type="section",
                    source_entity_id=requirement.section_id,
                ))

    # ── Group / student cohort conflict checks ──
    if group_schedules and schedule and requirement.group_id:
        for entry in group_schedules:
            e_group = entry.get("group_id")
            e_day = str(entry.get("day_of_week", "")).lower()
            e_slot = entry.get("time_slot_id")
            e_section = entry.get("section_id")

            if (e_group is not None
                    and int(e_group) == int(requirement.group_id)
                    and e_day == str(day or "").lower()
                    and e_slot == slot
                    and e_section != requirement.section_id):
                conflicts.append(_make_conflict(
                    tenant_id,
                    ConflictType.GROUP_TIME_CONFLICT,
                    reason=f"Group {requirement.group_id} already scheduled in section {e_section} on {day} slot {slot}",
                    section_id=requirement.section_id,
                    course_id=requirement.course_id,
                    group_id=requirement.group_id,
                    day_of_week=day,
                    time_slot=slot,
                    conflicting_entity_type="section",
                    conflicting_entity_id=e_section,
                    evidence={"conflicting_entry": entry},
                    source_entity_type="section",
                    source_entity_id=requirement.section_id,
                ))

    return conflicts


def build_scheduling_conflict_result(
    tenant_id: int,
    requirement: RoomAllocationRequirement,
    *,
    capability: Optional[RoomCapability] = None,
    capability_match: Optional[RoomCapabilityMatchEvidence] = None,
    schedule: Optional[RoomAllocationSchedule] = None,
    existing_bookings: Optional[list[dict[str, Any]]] = None,
    teacher_schedules: Optional[list[dict[str, Any]]] = None,
    group_schedules: Optional[list[dict[str, Any]]] = None,
) -> SchedulingConflictResult:
    """Build aggregated conflict detection result.

    Evidence-only: no auto-resolution, no ranking, no auto-assignment.
    """
    conflicts = detect_room_requirement_conflicts(
        tenant_id,
        requirement,
        capability=capability,
        capability_match=capability_match,
        schedule=schedule,
        existing_bookings=existing_bookings,
        teacher_schedules=teacher_schedules,
        group_schedules=group_schedules,
    )
    severity_summary: dict[str, int] = {}
    for c in conflicts:
        key = c.severity.value
        severity_summary[key] = severity_summary.get(key, 0) + 1

    return SchedulingConflictResult(
        tenant_id=tenant_id,
        has_conflicts=len(conflicts) > 0,
        conflict_count=len(conflicts),
        conflicts=conflicts,
        severity_summary=severity_summary,
    )


# ─── A-020.4 Capacity Matching Brain ─────────────────────────────────────────


class CapacityMismatchReason(str, Enum):
    """Normalized mismatch reasons for deterministic capacity matching output."""

    CAPACITY_UNKNOWN = "capacity_unknown"
    CAPACITY_SHORTAGE = "capacity_shortage"
    ROOM_TYPE_UNKNOWN = "room_type_unknown"
    ROOM_TYPE_MISMATCH = "room_type_mismatch"
    COMPUTERS_UNKNOWN = "computers_unknown"
    COMPUTERS_SHORTAGE = "computers_shortage"
    EQUIPMENT_MISMATCH = "equipment_mismatch"
    ROOM_UNAVAILABLE = "room_unavailable"
    RESTRICTION_MISMATCH = "restriction_mismatch"
    CONFLICT_PENALTY_APPLIED = "conflict_penalty_applied"
    ROOM_CAPABILITY_MISSING = "room_capability_missing"


class CapacityMatchStatus(str, Enum):
    """Deterministic room-to-requirement matching status."""

    EXCELLENT_MATCH = "excellent_match"
    GOOD_MATCH = "good_match"
    PARTIAL_MATCH = "partial_match"
    POOR_MATCH = "poor_match"
    NOT_SUITABLE = "not_suitable"
    UNAVAILABLE = "unavailable"
    UNKNOWN = "unknown"


class CapacityRiskLevel(str, Enum):
    """Deterministic risk level for capacity matching outcomes."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class CapacityMatchingDecision(BaseModel):
    """Brain-compatible decision envelope for capacity matching evidence."""

    scenario: str = "room_allocation_capacity_matching"
    decision_type: str = "room_allocation_review"
    requires_approval: bool = False
    recommended_actions: list[str] = Field(default_factory=list)


class CapacityMatchEvidence(BaseModel):
    """Evidence contract for deterministic capacity matching (A-020.4)."""

    tenant_id: int = Field(gt=0)
    section_id: Optional[int] = None
    course_id: Optional[int] = None
    group_id: Optional[int] = None
    teacher_id: Optional[str] = None
    room_id: Optional[str | int] = None
    required_capacity: Optional[int] = None
    room_capacity: Optional[int] = None
    required_room_type: Optional[str] = None
    room_type: Optional[str] = None
    required_computers: Optional[int] = None
    computers_count: Optional[int] = None
    equipment_required: list[str] = Field(default_factory=list)
    equipment_available: list[str] = Field(default_factory=list)
    conflict_count: int = 0
    conflict_types: list[str] = Field(default_factory=list)
    match_score: int = Field(ge=0, le=100)
    match_status: CapacityMatchStatus
    risk_level: CapacityRiskLevel
    required_human_review: bool
    mismatch_reasons: list[CapacityMismatchReason] = Field(default_factory=list)
    satisfied_requirements: list[str] = Field(default_factory=list)
    unsatisfied_requirements: list[str] = Field(default_factory=list)
    evidence: dict[str, Any] = Field(default_factory=dict)
    source_entity_type: Optional[str] = None
    source_entity_id: Optional[str | int] = None


class CapacityMatchingInput(BaseModel):
    """Input envelope for deterministic capacity matching."""

    tenant_id: int = Field(gt=0)
    requirement: RoomAllocationRequirement
    capability: Optional[RoomCapability] = None
    capability_match: Optional[RoomCapabilityMatchEvidence] = None
    conflicts: list[SchedulingConflictEvidence] = Field(default_factory=list)


class CapacityMatchingResult(BaseModel):
    """Capacity matching output (evaluation only, no ranking/assignment)."""

    tenant_id: int = Field(gt=0)
    match_score: int = Field(ge=0, le=100)
    match_status: CapacityMatchStatus
    risk_level: CapacityRiskLevel
    mismatch_reasons: list[CapacityMismatchReason] = Field(default_factory=list)
    satisfied_requirements: list[str] = Field(default_factory=list)
    unsatisfied_requirements: list[str] = Field(default_factory=list)
    required_human_review: bool
    evidence: dict[str, Any] = Field(default_factory=dict)
    source_entity_type: Optional[str] = None
    source_entity_id: Optional[str | int] = None
    capacity_match_evidence: CapacityMatchEvidence
    decision: CapacityMatchingDecision


def _clamp_score(value: int) -> int:
    return max(0, min(100, int(value)))


def _derive_match_status(
    score: int,
    *,
    capability: Optional[RoomCapability],
    capability_match: Optional[RoomCapabilityMatchEvidence],
    conflict_types: list[str],
) -> CapacityMatchStatus:
    if capability is None:
        return CapacityMatchStatus.UNKNOWN

    if capability_match is not None and capability_match.availability_ok is False:
        return CapacityMatchStatus.UNAVAILABLE

    if ConflictType.ROOM_UNAVAILABLE.value in conflict_types:
        return CapacityMatchStatus.UNAVAILABLE

    if score >= 90:
        return CapacityMatchStatus.EXCELLENT_MATCH
    if score >= 75:
        return CapacityMatchStatus.GOOD_MATCH
    if score >= 55:
        return CapacityMatchStatus.PARTIAL_MATCH
    if score >= 30:
        return CapacityMatchStatus.POOR_MATCH
    return CapacityMatchStatus.NOT_SUITABLE


def _derive_risk_level(
    status: CapacityMatchStatus,
    conflicts: list[SchedulingConflictEvidence],
    mismatch_reasons: list[CapacityMismatchReason],
) -> CapacityRiskLevel:
    if status in {CapacityMatchStatus.EXCELLENT_MATCH, CapacityMatchStatus.GOOD_MATCH}:
        risk = CapacityRiskLevel.LOW
    elif status == CapacityMatchStatus.PARTIAL_MATCH:
        risk = CapacityRiskLevel.MEDIUM
    elif status in {CapacityMatchStatus.POOR_MATCH, CapacityMatchStatus.UNAVAILABLE, CapacityMatchStatus.UNKNOWN}:
        risk = CapacityRiskLevel.HIGH
    else:
        risk = CapacityRiskLevel.CRITICAL

    severities = {c.severity.value for c in conflicts}
    if ConflictSeverity.CRITICAL.value in severities:
        risk = CapacityRiskLevel.CRITICAL
    elif ConflictSeverity.HIGH.value in severities and risk in {CapacityRiskLevel.LOW, CapacityRiskLevel.MEDIUM}:
        risk = CapacityRiskLevel.HIGH

    if CapacityMismatchReason.CAPACITY_SHORTAGE in mismatch_reasons:
        if status == CapacityMatchStatus.NOT_SUITABLE:
            risk = CapacityRiskLevel.CRITICAL
        elif risk != CapacityRiskLevel.CRITICAL:
            risk = CapacityRiskLevel.HIGH

    return risk


def build_capacity_matching_result(
    tenant_id: int,
    requirement: RoomAllocationRequirement,
    *,
    capability: Optional[RoomCapability] = None,
    capability_match: Optional[RoomCapabilityMatchEvidence] = None,
    conflicts: Optional[list[SchedulingConflictEvidence]] = None,
) -> CapacityMatchingResult:
    """Deterministic A-020.4 capacity matching evaluation.

    Evidence-only output:
    - no recommendation ranking
    - no room assignment/reservation
    - no timetable mutation
    - no booking override
    """
    if not isinstance(tenant_id, int) or tenant_id <= 0:
        raise ValueError("tenant_id must be a positive integer")

    input_conflicts = list(conflicts or [])
    if capability is not None and int(capability.tenant_id) != int(tenant_id):
        raise ValueError("capability.tenant_id does not match authoritative tenant_id")

    if capability is not None and capability_match is None:
        capability_match = assess_room_capability_against_requirement(
            capability,
            requirement,
            authoritative_tenant_id=tenant_id,
        )

    mismatch_reasons: list[CapacityMismatchReason] = []
    satisfied_requirements: list[str] = []
    unsatisfied_requirements: list[str] = []
    score = 0

    conflict_types = [c.conflict_type.value for c in input_conflicts]

    if capability is None:
        mismatch_reasons.append(CapacityMismatchReason.ROOM_CAPABILITY_MISSING)
        unsatisfied_requirements.extend(["capacity", "room_type", "availability"])
    else:
        # 1) Capacity fit (30)
        required_capacity = int(requirement.students_count)
        room_capacity = capability.capacity
        if room_capacity is None:
            score += 10
            mismatch_reasons.append(CapacityMismatchReason.CAPACITY_UNKNOWN)
            unsatisfied_requirements.append("capacity")
        elif int(room_capacity) >= required_capacity:
            score += 30
            satisfied_requirements.append("capacity")
        else:
            mismatch_reasons.append(CapacityMismatchReason.CAPACITY_SHORTAGE)
            unsatisfied_requirements.append("capacity")

        # 2) Room type fit (20)
        required_room_type = str(requirement.required_room_type or "").strip().lower()
        room_type = str(capability.room_type or "").strip().lower()
        if not required_room_type:
            score += 20
            satisfied_requirements.append("room_type")
        elif not room_type:
            score += 8
            mismatch_reasons.append(CapacityMismatchReason.ROOM_TYPE_UNKNOWN)
            unsatisfied_requirements.append("room_type")
        elif required_room_type == room_type:
            score += 20
            satisfied_requirements.append("room_type")
        else:
            mismatch_reasons.append(CapacityMismatchReason.ROOM_TYPE_MISMATCH)
            unsatisfied_requirements.append("room_type")

        # 3) Computer fit (15)
        required_computers = requirement.required_computers
        if required_computers is None or int(required_computers) <= 0:
            score += 15
            satisfied_requirements.append("computers")
        elif capability.computers_count is None:
            score += 5
            mismatch_reasons.append(CapacityMismatchReason.COMPUTERS_UNKNOWN)
            unsatisfied_requirements.append("computers")
        elif int(capability.computers_count) >= int(required_computers):
            score += 15
            satisfied_requirements.append("computers")
        else:
            mismatch_reasons.append(CapacityMismatchReason.COMPUTERS_SHORTAGE)
            unsatisfied_requirements.append("computers")

        # 4) Equipment fit (15)
        required_equipment = _normalize_tokens(requirement.equipment_required)
        available_equipment = _normalize_tokens(capability.equipment_available)
        if not required_equipment:
            score += 15
            satisfied_requirements.append("equipment")
            missing_equipment: list[str] = []
        else:
            missing_equipment = sorted(list(required_equipment - available_equipment))
            matched = max(0, len(required_equipment) - len(missing_equipment))
            score += int(round((matched / len(required_equipment)) * 15))
            if missing_equipment:
                mismatch_reasons.append(CapacityMismatchReason.EQUIPMENT_MISMATCH)
                unsatisfied_requirements.append("equipment")
            else:
                satisfied_requirements.append("equipment")

        # 5) Availability/status fit (10)
        availability_ok = capability_match.availability_ok if capability_match is not None else None
        if availability_ok is True:
            score += 10
            satisfied_requirements.append("availability")
        elif availability_ok is False:
            mismatch_reasons.append(CapacityMismatchReason.ROOM_UNAVAILABLE)
            unsatisfied_requirements.append("availability")
        else:
            score += 4
            unsatisfied_requirements.append("availability")

        # 6) No conflict/restriction issues (10)
        controls_points = 10
        restrictions_ok = capability_match.restrictions_ok if capability_match is not None else None
        if restrictions_ok is False:
            controls_points = 0
            mismatch_reasons.append(CapacityMismatchReason.RESTRICTION_MISMATCH)
            unsatisfied_requirements.append("restrictions")
        elif restrictions_ok is None and requirement.restrictions_required:
            controls_points = 4
            unsatisfied_requirements.append("restrictions")
        else:
            satisfied_requirements.append("restrictions")

        if input_conflicts:
            controls_points = max(0, controls_points - 10)

        score += controls_points

        # Conflict penalties
        severity_penalty = {
            ConflictSeverity.CRITICAL.value: 25,
            ConflictSeverity.HIGH.value: 15,
            ConflictSeverity.MEDIUM.value: 8,
            ConflictSeverity.LOW.value: 4,
        }
        total_penalty = sum(severity_penalty.get(c.severity.value, 0) for c in input_conflicts)
        total_penalty = min(40, total_penalty)
        if total_penalty > 0:
            mismatch_reasons.append(CapacityMismatchReason.CONFLICT_PENALTY_APPLIED)
        score = max(0, score - total_penalty)

    score = _clamp_score(score)
    status = _derive_match_status(
        score,
        capability=capability,
        capability_match=capability_match,
        conflict_types=conflict_types,
    )
    risk_level = _derive_risk_level(status, input_conflicts, mismatch_reasons)

    required_human_review = (
        risk_level in {CapacityRiskLevel.HIGH, CapacityRiskLevel.CRITICAL}
        or status in {
            CapacityMatchStatus.PARTIAL_MATCH,
            CapacityMatchStatus.POOR_MATCH,
            CapacityMatchStatus.NOT_SUITABLE,
            CapacityMatchStatus.UNAVAILABLE,
            CapacityMatchStatus.UNKNOWN,
        }
    )

    reasons = sorted(set(mismatch_reasons), key=lambda r: r.value)
    satisfied_unique = sorted(set(satisfied_requirements))
    unsatisfied_unique = sorted(set(unsatisfied_requirements))

    decision_actions: list[str] = [
        "review_room_match",
        "inspect_room_capability_evidence",
    ]
    if required_human_review:
        decision_actions.extend([
            "request_room_change_review",
            "escalate_to_scheduler",
        ])
    if status in {CapacityMatchStatus.UNAVAILABLE, CapacityMatchStatus.NOT_SUITABLE}:
        decision_actions.append("mark_room_allocation_required")

    decision = CapacityMatchingDecision(
        requires_approval=required_human_review,
        recommended_actions=list(dict.fromkeys(decision_actions)),
    )

    evidence_payload: dict[str, Any] = {
        "weights": {
            "capacity_fit": 30,
            "room_type_fit": 20,
            "computer_fit": 15,
            "equipment_fit": 15,
            "availability_fit": 10,
            "no_conflict_or_restriction_issues": 10,
        },
        "conflict_count": len(input_conflicts),
        "conflict_types": conflict_types,
        "source_contracts": ["A-020.1", "A-020.2", "A-020.3"],
    }

    if capability is not None:
        evidence_payload.update({
            "capability_match": capability_match.model_dump() if capability_match is not None else None,
            "required_capacity": int(requirement.students_count),
            "room_capacity": capability.capacity,
            "required_room_type": requirement.required_room_type,
            "room_type": capability.room_type,
            "required_computers": requirement.required_computers,
            "computers_count": capability.computers_count,
            "equipment_required": list(requirement.equipment_required or []),
            "equipment_available": list(capability.equipment_available),
        })

    capacity_evidence = CapacityMatchEvidence(
        tenant_id=tenant_id,
        section_id=requirement.section_id,
        course_id=requirement.course_id,
        group_id=requirement.group_id,
        teacher_id=requirement.teacher_id,
        room_id=(capability.room_id if capability is not None else None),
        required_capacity=int(requirement.students_count) if requirement.students_count is not None else None,
        room_capacity=(capability.capacity if capability is not None else None),
        required_room_type=requirement.required_room_type,
        room_type=(capability.room_type if capability is not None else None),
        required_computers=requirement.required_computers,
        computers_count=(capability.computers_count if capability is not None else None),
        equipment_required=list(requirement.equipment_required or []),
        equipment_available=(list(capability.equipment_available) if capability is not None else []),
        conflict_count=len(input_conflicts),
        conflict_types=conflict_types,
        match_score=score,
        match_status=status,
        risk_level=risk_level,
        required_human_review=required_human_review,
        mismatch_reasons=reasons,
        satisfied_requirements=satisfied_unique,
        unsatisfied_requirements=unsatisfied_unique,
        evidence=evidence_payload,
        source_entity_type=(capability.source_entity_type if capability is not None else None),
        source_entity_id=(capability.source_entity_id if capability is not None else None),
    )

    return CapacityMatchingResult(
        tenant_id=tenant_id,
        match_score=score,
        match_status=status,
        risk_level=risk_level,
        mismatch_reasons=reasons,
        satisfied_requirements=satisfied_unique,
        unsatisfied_requirements=unsatisfied_unique,
        required_human_review=required_human_review,
        evidence=evidence_payload,
        source_entity_type=capacity_evidence.source_entity_type,
        source_entity_id=capacity_evidence.source_entity_id,
        capacity_match_evidence=capacity_evidence,
        decision=decision,
    )
