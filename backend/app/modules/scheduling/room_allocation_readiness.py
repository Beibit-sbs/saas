"""Room Allocation Readiness Contract — A-020.1.

Lightweight schema for normalizing room allocation readiness evidence
across scheduling, room_booking, Brain Core, KPI and frontend surfaces.

Non-destructive: represents readiness state, never mutations.
Tenant-safe: always requires authoritative tenant_id.
Additive-only: builds on existing signals, no breaking changes.
"""
from __future__ import annotations

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
