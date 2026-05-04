"""Scheduling context source for Brain Core decisions.

A-013.3: Provides tenant-scoped scheduling/enrollment context derived from
the incoming signal payload.  No direct DB access — follows the payload-based
pattern of context_sources/academic.py to keep the context builder synchronous
and import-safe.
"""
from __future__ import annotations

from typing import Any


def fetch_scheduling_context(
    *,
    tenant_id: int,
    subject: dict[str, Any],
    payload: dict[str, Any],
) -> dict[str, Any]:
    """Return scheduling context slice for Brain Core decisions.

    Fields sourced from signal subject/payload:
    - section_id, course_id, term_id
    - faculty_id / instructor_id (aliased)
    - room_id
    - enrolled_count, max_capacity → fill_rate (auto-computed if not present)
    - conflict_type, conflicting_section_id
    - prerequisite_violations
    - risk_type

    The caller is responsible for passing the signal's authoritative tenant_id;
    payload-level tenant fields are intentionally ignored to prevent cross-tenant
    injection.
    """
    section_id = subject.get("section_id") or payload.get("section_id")
    course_id = subject.get("course_id") or payload.get("course_id")
    term_id = subject.get("term_id") or payload.get("term_id")
    faculty_id = (
        payload.get("faculty_id")
        or payload.get("instructor_id")
        or subject.get("faculty_id")
    )
    room_id = payload.get("room_id") or subject.get("room_id")

    enrolled_count = payload.get("enrolled_count")
    max_capacity = payload.get("max_capacity")

    # Auto-compute fill_rate from counts, but honour an explicit value if present.
    computed_fill_rate: float | None = None
    if enrolled_count is not None and max_capacity:
        try:
            computed_fill_rate = round(float(enrolled_count) / float(max_capacity), 3)
        except (ZeroDivisionError, TypeError, ValueError):
            computed_fill_rate = None

    fill_rate = (
        payload.get("fill_rate")
        if payload.get("fill_rate") is not None
        else computed_fill_rate
    )

    return {
        "section_id": section_id,
        "course_id": course_id,
        "term_id": term_id,
        "faculty_id": faculty_id,
        "room_id": room_id,
        "enrolled_count": enrolled_count,
        "max_capacity": max_capacity,
        "fill_rate": fill_rate,
        "conflict_type": payload.get("conflict_type"),
        "conflicting_section_id": payload.get("conflicting_section_id"),
        "prerequisite_violations": int(payload.get("prerequisite_violations") or 0),
        "risk_type": payload.get("risk_type"),
        "tenant_id": tenant_id,
    }
