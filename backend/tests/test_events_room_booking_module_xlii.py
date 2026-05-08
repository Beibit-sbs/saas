"""Tests for Phase XLII — Events Management + Room Booking."""
from __future__ import annotations

from unittest.mock import patch

import pytest

from app.modules.events_management.service import (
    EVENT_STATES,
    cancel_event,
    complete_event,
    create_event,
    list_events,
    list_registrations,
    open_registration,
    publish_event,
    register_participant,
    start_event,
)
from app.modules.room_booking.service import (
    BOOKING_STATES,
    UTILIZATION_THRESHOLD,
    approve_booking,
    check_in_room,
    check_utilization,
    create_room,
    list_bookings,
    list_rooms,
    release_room,
    request_booking,
)

TENANT = 1

# ─── helpers ──────────────────────────────────────────────────────────────────

def _ev(id_="e1", status="DRAFT", capacity=50, registered_count=0):
    return {"id": id_, "status": status, "capacity": capacity,
            "registered_count": registered_count, "category_id": "cat1", "tenant_id": TENANT}


def _booking(id_="b1", room_id="r1", status="REQUESTED"):
    return {"id": id_, "room_id": room_id, "status": status, "tenant_id": TENANT}


# ─── constants ────────────────────────────────────────────────────────────────

def test_event_states():
    assert EVENT_STATES == {"DRAFT", "PUBLISHED", "REGISTRATION_OPEN", "IN_PROGRESS", "COMPLETED", "CANCELLED"}


def test_booking_states():
    assert BOOKING_STATES == {"REQUESTED", "APPROVED", "OCCUPIED", "RELEASED"}


def test_utilization_threshold():
    assert UTILIZATION_THRESHOLD == 0.90


# ─── create_event ─────────────────────────────────────────────────────────────

def test_create_event_success():
    with patch("app.modules.events_management.service.create_entity_for_tenant",
               return_value={"id": "e1"}):
        result = create_event(TENANT, title="Tech Talk", category_id="cat1",
                              organizer_id="org1",
                              capacity=100, start_time="2026-06-01T10:00",
                              end_time="2026-06-01T12:00")
    assert result["event_id"] == "e1"
    assert result["status"] == "DRAFT"


def test_create_event_missing_title():
    with pytest.raises(ValueError, match="title"):
        create_event(TENANT, title="", category_id="cat1", organizer_id="org1", capacity=50,
                     start_time="2026-06-01T10:00", end_time="2026-06-01T12:00")


def test_create_event_zero_capacity():
    with pytest.raises(ValueError, match="capacity"):
        create_event(TENANT, title="Talk", category_id="cat1", organizer_id="org1", capacity=0,
                     start_time="2026-06-01T10:00", end_time="2026-06-01T12:00")


def test_create_event_invalid_tenant():
    with pytest.raises(ValueError, match="tenant_id"):
        create_event(0, title="Talk", category_id="cat1", organizer_id="org1", capacity=50,
                     start_time="2026-06-01T10:00", end_time="2026-06-01T12:00")


# ─── publish_event ────────────────────────────────────────────────────────────

def test_publish_event_fires_event():
    ev = _ev(status="DRAFT")
    with (
        patch("app.modules.events_management.service.list_entities_for_tenant", return_value=[ev]),
        patch("app.modules.events_management.service.EventPublisher") as mock_pub,
    ):
        result = publish_event(TENANT, event_id="e1")
    assert result["status"] == "PUBLISHED"
    call_kwargs = mock_pub.return_value.publish_event.call_args[1]
    assert call_kwargs["event_type"] == "event.published"


def test_publish_event_wrong_status():
    ev = _ev(status="IN_PROGRESS")
    with patch("app.modules.events_management.service.list_entities_for_tenant", return_value=[ev]):
        with pytest.raises(ValueError, match="Cannot transition"):
            publish_event(TENANT, event_id="e1")


# ─── open_registration ────────────────────────────────────────────────────────

def test_open_registration_success():
    ev = _ev(status="PUBLISHED")
    with patch("app.modules.events_management.service.list_entities_for_tenant", return_value=[ev]):
        result = open_registration(TENANT, event_id="e1")
    assert result["status"] == "REGISTRATION_OPEN"


# ─── register_participant ─────────────────────────────────────────────────────

def test_register_participant_success():
    ev = _ev(status="REGISTRATION_OPEN", capacity=50, registered_count=0)
    with (
        patch("app.modules.events_management.service.list_entities_for_tenant", return_value=[ev]),
        patch("app.modules.events_management.service.create_entity_for_tenant",
              return_value={"id": "reg1"}),
    ):
        result = register_participant(TENANT, event_id="e1", student_id="st1")
    assert result["registration_id"] == "reg1"
    assert result["registration_full"] is False


def test_register_participant_fires_full_event():
    ev = _ev(status="REGISTRATION_OPEN", capacity=1, registered_count=0)
    with (
        patch("app.modules.events_management.service.list_entities_for_tenant", return_value=[ev]),
        patch("app.modules.events_management.service.create_entity_for_tenant",
              return_value={"id": "reg1"}),
        patch("app.modules.events_management.service.EventPublisher") as mock_pub,
    ):
        result = register_participant(TENANT, event_id="e1", student_id="st1")
    assert result["registration_full"] is True
    call_kwargs = mock_pub.return_value.publish_event.call_args[1]
    assert call_kwargs["event_type"] == "event.registration_full"


def test_register_participant_wrong_status():
    ev = _ev(status="DRAFT")
    with patch("app.modules.events_management.service.list_entities_for_tenant", return_value=[ev]):
        with pytest.raises(ValueError, match="not open"):
            register_participant(TENANT, event_id="e1", student_id="st1")


# ─── start/complete/cancel ────────────────────────────────────────────────────

def test_start_event_fires_event():
    ev = _ev(status="REGISTRATION_OPEN")
    with (
        patch("app.modules.events_management.service.list_entities_for_tenant", return_value=[ev]),
        patch("app.modules.events_management.service.EventPublisher") as mock_pub,
    ):
        result = start_event(TENANT, event_id="e1")
    assert result["status"] == "IN_PROGRESS"
    call_kwargs = mock_pub.return_value.publish_event.call_args[1]
    assert call_kwargs["event_type"] == "event.started"


def test_complete_event_success():
    ev = _ev(status="IN_PROGRESS")
    with patch("app.modules.events_management.service.list_entities_for_tenant", return_value=[ev]):
        result = complete_event(TENANT, event_id="e1")
    assert result["status"] == "COMPLETED"


def test_cancel_event_success():
    ev = _ev(status="PUBLISHED")
    with patch("app.modules.events_management.service.list_entities_for_tenant", return_value=[ev]):
        result = cancel_event(TENANT, event_id="e1")
    assert result["status"] == "CANCELLED"


def test_cancel_event_terminal_raises():
    ev = _ev(status="COMPLETED")
    with patch("app.modules.events_management.service.list_entities_for_tenant", return_value=[ev]):
        with pytest.raises(ValueError, match="terminal"):
            cancel_event(TENANT, event_id="e1")


# ─── list events/registrations ────────────────────────────────────────────────

def test_list_events_unfiltered():
    events = [_ev("e1", "DRAFT"), _ev("e2", "PUBLISHED")]
    with patch("app.modules.events_management.service.list_entities_for_tenant", return_value=events):
        result = list_events(TENANT)
    assert len(result) == 2


def test_list_registrations_by_student():
    regs = [{"id": "r1", "student_id": "st1"}, {"id": "r2", "student_id": "st2"}]
    with patch("app.modules.events_management.service.list_entities_for_tenant", return_value=regs):
        result = list_registrations(TENANT, student_id="st1")
    assert len(result) == 1


# ─── room_booking ─────────────────────────────────────────────────────────────

def test_create_room_success():
    with patch("app.modules.room_booking.service.create_entity_for_tenant",
               return_value={"id": "r1"}):
        result = create_room(TENANT, name="Room 101", capacity=30)
    assert result["room_id"] == "r1"
    assert result["capacity"] == 30


def test_create_room_missing_name():
    with pytest.raises(ValueError, match="name"):
        create_room(TENANT, name="", capacity=10)


def test_request_booking_success():
    with (
        patch("app.modules.room_booking.service.list_entities_for_tenant", return_value=[]),
        patch("app.modules.room_booking.service.create_entity_for_tenant",
              return_value={"id": "b1"}),
    ):
        result = request_booking(TENANT, room_id="r1", requester_id="u1",
                                 start_time="2026-06-01T09:00", end_time="2026-06-01T10:00")
    assert result["booking_id"] == "b1"
    assert result["status"] == "REQUESTED"


def test_request_booking_conflict_raises():
    existing = [_booking(id_="b0", room_id="r1", status="APPROVED") | {"start_time": "2026-06-01T09:00"}]
    with (
        patch("app.modules.room_booking.service.list_entities_for_tenant", return_value=existing),
        patch("app.modules.room_booking.service.EventPublisher"),
    ):
        with pytest.raises(ValueError, match="conflict"):
            request_booking(TENANT, room_id="r1", requester_id="u1",
                            start_time="2026-06-01T09:00", end_time="2026-06-01T10:00")


def test_approve_booking_fires_event():
    booking = _booking(status="REQUESTED")
    with (
        patch("app.modules.room_booking.service.list_entities_for_tenant", return_value=[booking]),
        patch("app.modules.room_booking.service.EventPublisher") as mock_pub,
    ):
        result = approve_booking(TENANT, booking_id="b1")
    assert result["status"] == "APPROVED"
    call_kwargs = mock_pub.return_value.publish_event.call_args[1]
    assert call_kwargs["event_type"] == "booking.approved"


def test_check_in_room_success():
    booking = _booking(status="APPROVED")
    with patch("app.modules.room_booking.service.list_entities_for_tenant", return_value=[booking]):
        result = check_in_room(TENANT, booking_id="b1")
    assert result["status"] == "OCCUPIED"


def test_release_room_fires_event():
    booking = _booking(status="OCCUPIED")
    with (
        patch("app.modules.room_booking.service.list_entities_for_tenant", return_value=[booking]),
        patch("app.modules.room_booking.service.EventPublisher") as mock_pub,
    ):
        result = release_room(TENANT, booking_id="b1")
    assert result["status"] == "RELEASED"
    call_kwargs = mock_pub.return_value.publish_event.call_args[1]
    assert call_kwargs["event_type"] == "room.released"


def test_check_utilization_overload_fires_event():
    with patch("app.modules.room_booking.service.EventPublisher") as mock_pub:
        result = check_utilization(TENANT, room_id="r1", total_slots=10, occupied_slots=10)
    assert result["overload"] is True
    call_kwargs = mock_pub.return_value.publish_event.call_args[1]
    assert call_kwargs["event_type"] == "resource.overload"


def test_check_utilization_no_event_when_ok():
    with patch("app.modules.room_booking.service.EventPublisher") as mock_pub:
        result = check_utilization(TENANT, room_id="r1", total_slots=10, occupied_slots=5)
    assert result["overload"] is False
    mock_pub.return_value.publish_event.assert_not_called()


def test_list_rooms():
    rooms = [{"id": "r1", "name": "101"}, {"id": "r2", "name": "102"}]
    with patch("app.modules.room_booking.service.list_entities_for_tenant", return_value=rooms):
        result = list_rooms(TENANT)
    assert len(result) == 2


def test_list_bookings_by_room():
    bookings = [_booking("b1", "r1"), _booking("b2", "r2")]
    with patch("app.modules.room_booking.service.list_entities_for_tenant", return_value=bookings):
        result = list_bookings(TENANT, room_id="r1")
    assert len(result) == 1
