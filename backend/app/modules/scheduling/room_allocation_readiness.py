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


class RoomAllocationAvailability(BaseModel):
    """What a room can provide."""

    room_id: int
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
