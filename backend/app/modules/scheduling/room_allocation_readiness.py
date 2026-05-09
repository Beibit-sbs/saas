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
