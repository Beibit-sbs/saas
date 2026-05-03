"""Phase XLII — Events Management sub-module."""
from __future__ import annotations

import datetime

from app.modules.university_core.tenant_entity_api import (
    create_entity_for_tenant,
    list_entities_for_tenant,
)
from app.platform.events.publisher import EventPublisher

EVENT_STATES: frozenset[str] = frozenset(
    {"DRAFT", "PUBLISHED", "REGISTRATION_OPEN", "IN_PROGRESS", "COMPLETED", "CANCELLED"}
)

_TERMINAL_STATES: frozenset[str] = frozenset({"COMPLETED", "CANCELLED"})

_APP_FSM: dict[str, frozenset[str]] = {
    "DRAFT": frozenset({"PUBLISHED", "CANCELLED"}),
    "PUBLISHED": frozenset({"REGISTRATION_OPEN", "CANCELLED"}),
    "REGISTRATION_OPEN": frozenset({"IN_PROGRESS", "CANCELLED"}),
    "IN_PROGRESS": frozenset({"COMPLETED", "CANCELLED"}),
}


# ─── helpers ──────────────────────────────────────────────────────────────────

def _validate_tenant(tenant_id: int) -> None:
    if not tenant_id or tenant_id <= 0:
        raise ValueError("tenant_id must be a positive integer")


def _fire(tenant_id: int, event_type: str, payload: dict) -> None:
    try:
        pub = EventPublisher()
        pub.publish_event(tenant_id=tenant_id, event_type=event_type, payload=payload)
    except Exception:
        pass


def _get_event(tenant_id: int, event_id: str) -> dict:
    rows = list_entities_for_tenant(tenant_id, "campus_events")
    for r in rows:
        if r.get("id") == event_id:
            return r
    raise ValueError(f"Event {event_id!r} not found")


def _assert_transition(current: str, target: str, entity: str = "Event") -> None:
    allowed = _APP_FSM.get(current, frozenset())
    if target not in allowed:
        raise ValueError(f"Cannot transition {entity} from {current} to {target}")


# ─── public API ───────────────────────────────────────────────────────────────

def create_event(
    tenant_id: int,
    *,
    title: str,
    category_id: str,
    capacity: int,
    start_time: str,
    end_time: str,
) -> dict:
    _validate_tenant(tenant_id)
    if not title:
        raise ValueError("title is required")
    if not category_id:
        raise ValueError("category_id is required")
    if capacity <= 0:
        raise ValueError("capacity must be > 0")
    if not start_time:
        raise ValueError("start_time is required")
    if not end_time:
        raise ValueError("end_time is required")

    row = create_entity_for_tenant(
        tenant_id,
        "campus_events",
        {
            "title": title,
            "category_id": category_id,
            "capacity": capacity,
            "start_time": start_time,
            "end_time": end_time,
            "status": "DRAFT",
            "registered_count": 0,
            "tenant_id": tenant_id,
        },
    )
    return {"event_id": row["id"], "status": "DRAFT", "capacity": capacity}


def publish_event(tenant_id: int, *, event_id: str) -> dict:
    _validate_tenant(tenant_id)
    ev = _get_event(tenant_id, event_id)
    _assert_transition(ev["status"], "PUBLISHED")
    ev["status"] = "PUBLISHED"
    _fire(tenant_id, "event.published", {"event_id": event_id})
    return {"event_id": event_id, "status": "PUBLISHED"}


def open_registration(tenant_id: int, *, event_id: str) -> dict:
    _validate_tenant(tenant_id)
    ev = _get_event(tenant_id, event_id)
    _assert_transition(ev["status"], "REGISTRATION_OPEN")
    ev["status"] = "REGISTRATION_OPEN"
    return {"event_id": event_id, "status": "REGISTRATION_OPEN"}


def register_participant(tenant_id: int, *, event_id: str, student_id: str) -> dict:
    _validate_tenant(tenant_id)
    if not student_id:
        raise ValueError("student_id is required")
    ev = _get_event(tenant_id, event_id)
    if ev["status"] != "REGISTRATION_OPEN":
        raise ValueError(f"Event is not open for registration (status={ev['status']})")

    capacity = ev.get("capacity", 0)
    registered = ev.get("registered_count", 0)

    row = create_entity_for_tenant(
        tenant_id,
        "event_registrations",
        {
            "event_id": event_id,
            "student_id": student_id,
            "registered_at": datetime.datetime.utcnow().isoformat(),
            "tenant_id": tenant_id,
        },
    )
    ev["registered_count"] = registered + 1
    full = ev["registered_count"] >= capacity
    if full:
        _fire(tenant_id, "event.registration_full", {"event_id": event_id, "capacity": capacity})
    return {"registration_id": row["id"], "event_id": event_id, "student_id": student_id, "registration_full": full}


def start_event(tenant_id: int, *, event_id: str) -> dict:
    _validate_tenant(tenant_id)
    ev = _get_event(tenant_id, event_id)
    _assert_transition(ev["status"], "IN_PROGRESS")
    ev["status"] = "IN_PROGRESS"
    _fire(tenant_id, "event.started", {"event_id": event_id})
    return {"event_id": event_id, "status": "IN_PROGRESS"}


def complete_event(tenant_id: int, *, event_id: str) -> dict:
    _validate_tenant(tenant_id)
    ev = _get_event(tenant_id, event_id)
    _assert_transition(ev["status"], "COMPLETED")
    ev["status"] = "COMPLETED"
    return {"event_id": event_id, "status": "COMPLETED"}


def cancel_event(tenant_id: int, *, event_id: str) -> dict:
    _validate_tenant(tenant_id)
    ev = _get_event(tenant_id, event_id)
    if ev["status"] in _TERMINAL_STATES:
        raise ValueError(f"Cannot cancel event in terminal state {ev['status']}")
    _assert_transition(ev["status"], "CANCELLED")
    ev["status"] = "CANCELLED"
    return {"event_id": event_id, "status": "CANCELLED"}


def list_events(tenant_id: int, *, status: str | None = None, category_id: str | None = None) -> list[dict]:
    _validate_tenant(tenant_id)
    rows = list_entities_for_tenant(tenant_id, "campus_events")
    if status:
        rows = [r for r in rows if r.get("status") == status]
    if category_id:
        rows = [r for r in rows if r.get("category_id") == category_id]
    return rows


def list_registrations(tenant_id: int, *, event_id: str | None = None, student_id: str | None = None) -> list[dict]:
    _validate_tenant(tenant_id)
    rows = list_entities_for_tenant(tenant_id, "event_registrations")
    if event_id:
        rows = [r for r in rows if r.get("event_id") == event_id]
    if student_id:
        rows = [r for r in rows if r.get("student_id") == student_id]
    return rows
