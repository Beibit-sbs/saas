"""Phase XLII — Events Management sub-module."""
from __future__ import annotations

import datetime

from app.core.module_helpers.audit_helpers import build_audit_action
from app.modules.audit.service import log_admin_action
from app.modules.university_core.tenant_entity_api import (
    create_entity_for_tenant,
    list_entities_for_tenant,
)
from app.modules.usage.service import record_usage_event
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


def _validate_tenant(tenant_id: int) -> None:
    if not tenant_id or tenant_id <= 0:
        raise ValueError("tenant_id must be a positive integer")


def _require_non_empty(value: str, field_name: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"{field_name} is required")
    return text


def _looks_like_table_rows(rows: object, table: str) -> bool:
    if not isinstance(rows, list):
        return False
    if not rows:
        return False
    if not all(isinstance(r, dict) for r in rows):
        return False
    if table == "campus_events":
        return any(("title" in r) or ("status" in r) or ("category_id" in r) for r in rows)
    if table == "event_registrations":
        return any(("event_id" in r) or ("student_id" in r) for r in rows)
    return True


def _list_rows(table: str, tenant_id: int) -> list[dict]:
    rows = list_entities_for_tenant(table, tenant_id)
    if _looks_like_table_rows(rows, table):
        return rows
    try:
        fallback_rows = list_entities_for_tenant(tenant_id, table)  # type: ignore[arg-type]
    except Exception:
        return rows if isinstance(rows, list) else []
    if _looks_like_table_rows(fallback_rows, table):
        return fallback_rows
    return rows if isinstance(rows, list) else []


def _create_row(table: str, payload: dict, tenant_id: int) -> dict:
    try:
        return create_entity_for_tenant(table, payload, tenant_id)
    except TypeError:
        return create_entity_for_tenant(tenant_id, table, payload)  # type: ignore[arg-type]


def _fire(tenant_id: int, event_type: str, payload: dict) -> None:
    try:
        EventPublisher().publish_event(tenant_id=tenant_id, event_type=event_type, payload=payload)
    except Exception:
        pass


def _audit(tenant_id: int, actor: str, action: str, path: str, metadata: dict) -> None:
    try:
        log_admin_action(
            actor=actor,
            action=action,
            path=path,
            client_ip="service",
            entity="events_management",
            metadata=metadata,
            tenant_id=tenant_id,
        )
    except Exception:
        pass


def _metric(tenant_id: int, metric: str, value: int = 1) -> None:
    try:
        record_usage_event(tenant_id=tenant_id, metric=metric, value=value)
    except Exception:
        pass


def _parse_iso_datetime(value: str) -> datetime.datetime:
    normalized = str(value or "").strip().replace("Z", "+00:00")
    return datetime.datetime.fromisoformat(normalized)


def _validate_schedule_window(start_time: str, end_time: str) -> None:
    try:
        start_dt = _parse_iso_datetime(start_time)
        end_dt = _parse_iso_datetime(end_time)
    except Exception as exc:
        raise ValueError("start_time/end_time must be valid ISO-8601 datetime values") from exc
    if start_dt >= end_dt:
        raise ValueError("start_time must be earlier than end_time")


def _get_event(tenant_id: int, event_id: str) -> dict:
    rows = _list_rows("campus_events", tenant_id)
    for r in rows:
        if r.get("id") == event_id:
            return r
    raise ValueError(f"Event {event_id!r} not found")


def _assert_transition(current: str, target: str, entity: str = "Event") -> None:
    allowed = _APP_FSM.get(current, frozenset())
    if target not in allowed:
        raise ValueError(f"Cannot transition {entity} from {current} to {target}")


def create_event(
    tenant_id: int,
    *,
    title: str,
    category_id: str,
    organizer_id: str,
    capacity: int,
    start_time: str,
    end_time: str,
    actor: str = "system",
) -> dict:
    _validate_tenant(tenant_id)
    title = _require_non_empty(title, "title")
    category_id = _require_non_empty(category_id, "category_id")
    organizer_id = _require_non_empty(organizer_id, "organizer_id")
    if capacity <= 0:
        raise ValueError("capacity must be > 0")
    start_time = _require_non_empty(start_time, "start_time")
    end_time = _require_non_empty(end_time, "end_time")
    _validate_schedule_window(start_time, end_time)

    row = _create_row(
        "campus_events",
        {
            "title": title,
            "category_id": category_id,
            "organizer_id": organizer_id,
            "capacity": capacity,
            "start_time": start_time,
            "end_time": end_time,
            "status": "DRAFT",
            "registered_count": 0,
            "tenant_id": tenant_id,
        },
        tenant_id,
    )
    event_id = str(row.get("id") or "")
    _fire(
        tenant_id,
        "event.created",
        {
            "event_id": event_id,
            "title": title,
            "category_id": category_id,
            "organizer_id": organizer_id,
            "capacity": capacity,
        },
    )
    _audit(
        tenant_id,
        actor,
        build_audit_action("events_management", "event", "create"),
        f"/internal/events-management/events/{event_id}/create",
        {"event_id": event_id, "category_id": category_id, "organizer_id": organizer_id},
    )
    _metric(tenant_id, "events_created", 1)
    return {"event_id": row["id"], "status": "DRAFT", "capacity": capacity}


def publish_event(tenant_id: int, *, event_id: str, actor: str = "system") -> dict:
    _validate_tenant(tenant_id)
    event_id = _require_non_empty(event_id, "event_id")
    ev = _get_event(tenant_id, event_id)
    _assert_transition(ev["status"], "PUBLISHED")
    ev["status"] = "PUBLISHED"
    _fire(tenant_id, "event.published", {"event_id": event_id})
    _audit(
        tenant_id,
        actor,
        build_audit_action("events_management", "event", "publish"),
        f"/internal/events-management/events/{event_id}/publish",
        {"event_id": event_id},
    )
    _metric(tenant_id, "events_published", 1)
    return {"event_id": event_id, "status": "PUBLISHED"}


def open_registration(tenant_id: int, *, event_id: str, actor: str = "system") -> dict:
    _validate_tenant(tenant_id)
    event_id = _require_non_empty(event_id, "event_id")
    ev = _get_event(tenant_id, event_id)
    _assert_transition(ev["status"], "REGISTRATION_OPEN")
    ev["status"] = "REGISTRATION_OPEN"
    _fire(tenant_id, "event.registration_opened", {"event_id": event_id})
    _audit(
        tenant_id,
        actor,
        build_audit_action("events_management", "event", "open_registration"),
        f"/internal/events-management/events/{event_id}/open-registration",
        {"event_id": event_id},
    )
    _metric(tenant_id, "events_registration_opened", 1)
    return {"event_id": event_id, "status": "REGISTRATION_OPEN"}


def register_participant(tenant_id: int, *, event_id: str, student_id: str, actor: str = "system") -> dict:
    _validate_tenant(tenant_id)
    event_id = _require_non_empty(event_id, "event_id")
    student_id = _require_non_empty(student_id, "student_id")
    ev = _get_event(tenant_id, event_id)
    if ev["status"] != "REGISTRATION_OPEN":
        raise ValueError(f"Event is not open for registration (status={ev['status']})")

    registrations = _list_rows("event_registrations", tenant_id)
    already_registered = any(
        r.get("event_id") == event_id and r.get("student_id") == student_id
        for r in registrations
    )
    if already_registered:
        raise ValueError("student_id is already registered for this event")

    try:
        capacity = int(ev.get("capacity", 0))
        registered = int(ev.get("registered_count", 0))
    except (TypeError, ValueError) as exc:
        raise ValueError("event capacity/registered_count must be numeric") from exc

    if registered >= capacity:
        raise ValueError("Event capacity reached")

    row = _create_row(
        "event_registrations",
        {
            "event_id": event_id,
            "student_id": student_id,
            "registered_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "tenant_id": tenant_id,
        },
        tenant_id,
    )
    ev["registered_count"] = registered + 1
    full = ev["registered_count"] >= capacity
    if full:
        _fire(tenant_id, "event.registration_full", {"event_id": event_id, "capacity": capacity})
        _metric(tenant_id, "events_registration_full", 1)
    _audit(
        tenant_id,
        actor,
        build_audit_action("events_management", "registration", "register"),
        f"/internal/events-management/events/{event_id}/registrations",
        {"event_id": event_id, "student_id": student_id, "registration_id": row.get("id")},
    )
    _metric(tenant_id, "event_registrations_created", 1)
    return {"registration_id": row["id"], "event_id": event_id, "student_id": student_id, "registration_full": full}


def start_event(tenant_id: int, *, event_id: str, actor: str = "system") -> dict:
    _validate_tenant(tenant_id)
    event_id = _require_non_empty(event_id, "event_id")
    ev = _get_event(tenant_id, event_id)
    _assert_transition(ev["status"], "IN_PROGRESS")
    ev["status"] = "IN_PROGRESS"
    _fire(tenant_id, "event.started", {"event_id": event_id})
    _audit(
        tenant_id,
        actor,
        build_audit_action("events_management", "event", "start"),
        f"/internal/events-management/events/{event_id}/start",
        {"event_id": event_id},
    )
    _metric(tenant_id, "events_started", 1)
    return {"event_id": event_id, "status": "IN_PROGRESS"}


def complete_event(tenant_id: int, *, event_id: str, actor: str = "system") -> dict:
    _validate_tenant(tenant_id)
    event_id = _require_non_empty(event_id, "event_id")
    ev = _get_event(tenant_id, event_id)
    _assert_transition(ev["status"], "COMPLETED")
    ev["status"] = "COMPLETED"
    _fire(tenant_id, "event.completed", {"event_id": event_id})
    _audit(
        tenant_id,
        actor,
        build_audit_action("events_management", "event", "complete"),
        f"/internal/events-management/events/{event_id}/complete",
        {"event_id": event_id},
    )
    _metric(tenant_id, "events_completed", 1)
    return {"event_id": event_id, "status": "COMPLETED"}


def cancel_event(tenant_id: int, *, event_id: str, actor: str = "system") -> dict:
    _validate_tenant(tenant_id)
    event_id = _require_non_empty(event_id, "event_id")
    ev = _get_event(tenant_id, event_id)
    if ev["status"] in _TERMINAL_STATES:
        raise ValueError(f"Cannot cancel event in terminal state {ev['status']}")
    _assert_transition(ev["status"], "CANCELLED")
    ev["status"] = "CANCELLED"
    _fire(tenant_id, "event.cancelled", {"event_id": event_id})
    _audit(
        tenant_id,
        actor,
        build_audit_action("events_management", "event", "cancel"),
        f"/internal/events-management/events/{event_id}/cancel",
        {"event_id": event_id},
    )
    _metric(tenant_id, "events_cancelled", 1)
    return {"event_id": event_id, "status": "CANCELLED"}


def list_events(tenant_id: int, *, status: str | None = None, category_id: str | None = None) -> list[dict]:
    _validate_tenant(tenant_id)
    rows = _list_rows("campus_events", tenant_id)
    if status:
        rows = [r for r in rows if r.get("status") == status]
    if category_id:
        rows = [r for r in rows if r.get("category_id") == category_id]
    return rows


def list_registrations(tenant_id: int, *, event_id: str | None = None, student_id: str | None = None) -> list[dict]:
    _validate_tenant(tenant_id)
    rows = _list_rows("event_registrations", tenant_id)
    if event_id:
        rows = [r for r in rows if r.get("event_id") == event_id]
    if student_id:
        rows = [r for r in rows if r.get("student_id") == student_id]
    return rows
