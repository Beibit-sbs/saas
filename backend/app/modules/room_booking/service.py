"""Phase XLII — Room Booking sub-module."""
from __future__ import annotations

from app.modules.university_core.tenant_entity_api import (
    create_entity_for_tenant,
    list_entities_for_tenant,
)
from app.platform.events.publisher import EventPublisher

BOOKING_STATES: frozenset[str] = frozenset({"REQUESTED", "APPROVED", "OCCUPIED", "RELEASED"})

UTILIZATION_THRESHOLD: float = 0.90

_BOOKING_FSM: dict[str, frozenset[str]] = {
    "REQUESTED": frozenset({"APPROVED"}),
    "APPROVED": frozenset({"OCCUPIED"}),
    "OCCUPIED": frozenset({"RELEASED"}),
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


def _get_booking(tenant_id: int, booking_id: str) -> dict:
    rows = list_entities_for_tenant(tenant_id, "room_bookings")
    for r in rows:
        if r.get("id") == booking_id:
            return r
    raise ValueError(f"Booking {booking_id!r} not found")


def _assert_transition(current: str, target: str) -> None:
    allowed = _BOOKING_FSM.get(current, frozenset())
    if target not in allowed:
        raise ValueError(f"Cannot transition booking from {current} to {target}")


# ─── public API ───────────────────────────────────────────────────────────────

def create_room(
    tenant_id: int,
    *,
    name: str,
    capacity: int,
    location: str = "",
) -> dict:
    _validate_tenant(tenant_id)
    if not name:
        raise ValueError("name is required")
    if capacity <= 0:
        raise ValueError("capacity must be > 0")
    row = create_entity_for_tenant(
        tenant_id,
        "campus_rooms",
        {"name": name, "capacity": capacity, "location": location, "tenant_id": tenant_id},
    )
    return {"room_id": row["id"], "name": name, "capacity": capacity}


def request_booking(
    tenant_id: int,
    *,
    room_id: str,
    requester_id: str,
    start_time: str,
    end_time: str,
    purpose: str = "",
) -> dict:
    _validate_tenant(tenant_id)
    if not room_id:
        raise ValueError("room_id is required")
    if not requester_id:
        raise ValueError("requester_id is required")
    if not start_time:
        raise ValueError("start_time is required")
    if not end_time:
        raise ValueError("end_time is required")

    # conflict check: look for APPROVED or OCCUPIED bookings for the same room
    existing = list_entities_for_tenant(tenant_id, "room_bookings")
    conflict = any(
        r.get("room_id") == room_id and r.get("status") in {"APPROVED", "OCCUPIED"}
        and r.get("start_time") == start_time
        for r in existing
    )
    if conflict:
        _fire(tenant_id, "booking.conflict_detected", {"room_id": room_id, "start_time": start_time})
        raise ValueError("Booking conflict detected for this room/time")

    row = create_entity_for_tenant(
        tenant_id,
        "room_bookings",
        {
            "room_id": room_id,
            "requester_id": requester_id,
            "start_time": start_time,
            "end_time": end_time,
            "purpose": purpose,
            "status": "REQUESTED",
            "tenant_id": tenant_id,
        },
    )
    return {"booking_id": row["id"], "room_id": room_id, "status": "REQUESTED"}


def approve_booking(tenant_id: int, *, booking_id: str) -> dict:
    _validate_tenant(tenant_id)
    booking = _get_booking(tenant_id, booking_id)
    _assert_transition(booking["status"], "APPROVED")
    booking["status"] = "APPROVED"
    _fire(tenant_id, "booking.approved", {"booking_id": booking_id})
    return {"booking_id": booking_id, "status": "APPROVED"}


def check_in_room(tenant_id: int, *, booking_id: str) -> dict:
    _validate_tenant(tenant_id)
    booking = _get_booking(tenant_id, booking_id)
    _assert_transition(booking["status"], "OCCUPIED")
    booking["status"] = "OCCUPIED"
    return {"booking_id": booking_id, "status": "OCCUPIED"}


def release_room(tenant_id: int, *, booking_id: str) -> dict:
    _validate_tenant(tenant_id)
    booking = _get_booking(tenant_id, booking_id)
    _assert_transition(booking["status"], "RELEASED")
    booking["status"] = "RELEASED"
    _fire(tenant_id, "room.released", {"booking_id": booking_id, "room_id": booking.get("room_id")})
    return {"booking_id": booking_id, "status": "RELEASED"}


def check_utilization(tenant_id: int, *, room_id: str, total_slots: int, occupied_slots: int) -> dict:
    """Fire resource.overload if utilization > UTILIZATION_THRESHOLD."""
    _validate_tenant(tenant_id)
    if total_slots <= 0:
        raise ValueError("total_slots must be > 0")
    utilization = occupied_slots / total_slots
    overload = utilization > UTILIZATION_THRESHOLD
    if overload:
        _fire(tenant_id, "resource.overload", {"room_id": room_id, "utilization": utilization})
    return {"room_id": room_id, "utilization": utilization, "overload": overload}


def list_rooms(tenant_id: int) -> list[dict]:
    _validate_tenant(tenant_id)
    return list_entities_for_tenant(tenant_id, "campus_rooms")


def list_bookings(
    tenant_id: int,
    *,
    room_id: str | None = None,
    status: str | None = None,
    requester_id: str | None = None,
) -> list[dict]:
    _validate_tenant(tenant_id)
    rows = list_entities_for_tenant(tenant_id, "room_bookings")
    if room_id:
        rows = [r for r in rows if r.get("room_id") == room_id]
    if status:
        rows = [r for r in rows if r.get("status") == status]
    if requester_id:
        rows = [r for r in rows if r.get("requester_id") == requester_id]
    return rows
