"""W71 — equipment_booking: Block booking creation for unavailable equipment.

Real-world problem: create_equipment_booking() verified equipment existence by
equipment_code but never checked the equipment's status.  A booking could be
confirmed against equipment in 'maintenance', 'broken', or 'retired' status.
Students/researchers would arrive to find equipment unavailable.

Fix: After the existence check, read equipment_record.status and raise ValueError
if the status is not in _BOOKABLE_EQUIPMENT_STATUSES {'available', 'operational'}.
"""
from __future__ import annotations

import pytest

from app.modules.equipment_booking.service import (
    _BOOKABLE_EQUIPMENT_STATUSES,
    create_equipment_booking,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_equipment(code: str, status: str) -> dict:
    return {"id": 1, "equipment_code": code, "name": "Lab Centrifuge", "status": status}


def _make_booking_payload(code: str) -> dict:
    return {
        "equipment_code": code,
        "requester_id": "student-42",
        "booking_status": "pending",
        "start_time": "2026-05-01T09:00:00",
        "end_time": "2026-05-01T11:00:00",
        "integration_source": "lab_system",
        "source_entity_id": "req-99",
    }


# ---------------------------------------------------------------------------
# 1. _BOOKABLE_EQUIPMENT_STATUSES sanity
# ---------------------------------------------------------------------------

def test_w71_bookable_statuses_frozenset():
    """_BOOKABLE_EQUIPMENT_STATUSES must be a frozenset containing 'available' and 'operational'."""
    assert isinstance(_BOOKABLE_EQUIPMENT_STATUSES, frozenset)
    assert "available" in _BOOKABLE_EQUIPMENT_STATUSES
    assert "operational" in _BOOKABLE_EQUIPMENT_STATUSES
    # Must not include maintenance/repair/retired
    assert "maintenance" not in _BOOKABLE_EQUIPMENT_STATUSES
    assert "broken" not in _BOOKABLE_EQUIPMENT_STATUSES
    assert "retired" not in _BOOKABLE_EQUIPMENT_STATUSES


# ---------------------------------------------------------------------------
# 2. Booking blocked when equipment is in maintenance
# ---------------------------------------------------------------------------

def test_w71_booking_blocked_when_equipment_in_maintenance(monkeypatch):
    """create_equipment_booking must raise ValueError if equipment status is 'maintenance'."""
    monkeypatch.setattr("app.modules.equipment_booking.service._check_requester_enrollment_for_booking", lambda *a, **kw: None)
    equipment = _make_equipment("CENT-001", "maintenance")

    def mock_list(entity_name, tenant_id):
        if entity_name == "equipment_items":
            return [equipment]
        return []

    monkeypatch.setattr("app.modules.equipment_booking.service.list_entities_for_tenant", mock_list)

    with pytest.raises(ValueError, match="not available for booking"):
        create_equipment_booking(_make_booking_payload("CENT-001"), tenant_id=1)


# ---------------------------------------------------------------------------
# 3. Booking blocked when equipment is retired
# ---------------------------------------------------------------------------

def test_w71_booking_blocked_when_equipment_retired(monkeypatch):
    """create_equipment_booking must raise ValueError if equipment status is 'retired'."""
    monkeypatch.setattr("app.modules.equipment_booking.service._check_requester_enrollment_for_booking", lambda *a, **kw: None)
    equipment = _make_equipment("CENT-002", "retired")

    def mock_list(entity_name, tenant_id):
        if entity_name == "equipment_items":
            return [equipment]
        return []

    monkeypatch.setattr("app.modules.equipment_booking.service.list_entities_for_tenant", mock_list)

    with pytest.raises(ValueError, match="not available for booking"):
        create_equipment_booking(_make_booking_payload("CENT-002"), tenant_id=1)


# ---------------------------------------------------------------------------
# 4. Booking allowed when equipment is available
# ---------------------------------------------------------------------------

def test_w71_booking_allowed_when_equipment_available(monkeypatch):
    """create_equipment_booking must succeed when equipment status is 'available'."""
    monkeypatch.setattr("app.modules.equipment_booking.service._check_requester_enrollment_for_booking", lambda *a, **kw: None)
    equipment = _make_equipment("CENT-003", "available")
    created_booking = {
        "id": 1,
        "equipment_code": "cent-003",
        "booking_status": "pending",
        "conflict_flag": "false",
        "requester_id": "student-42",
    }

    def mock_list(entity_name, tenant_id):
        if entity_name == "equipment_items":
            return [equipment]
        if entity_name == "equipment_bookings":
            return []
        return []

    def mock_create(entity_name, payload, tenant_id):
        return created_booking

    monkeypatch.setattr("app.modules.equipment_booking.service.list_entities_for_tenant", mock_list)
    monkeypatch.setattr("app.modules.equipment_booking.service.create_entity_for_tenant", mock_create)

    result = create_equipment_booking(_make_booking_payload("CENT-003"), tenant_id=1)
    assert result is not None
    assert result["booking_status"] == "pending"


# ---------------------------------------------------------------------------
# 5. Booking allowed when equipment is operational
# ---------------------------------------------------------------------------

def test_w71_booking_allowed_when_equipment_operational(monkeypatch):
    """create_equipment_booking must succeed when equipment status is 'operational'."""
    monkeypatch.setattr("app.modules.equipment_booking.service._check_requester_enrollment_for_booking", lambda *a, **kw: None)
    equipment = _make_equipment("CENT-004", "operational")
    created_booking = {
        "id": 2,
        "equipment_code": "cent-004",
        "booking_status": "pending",
        "conflict_flag": "false",
    }

    def mock_list(entity_name, tenant_id):
        if entity_name == "equipment_items":
            return [equipment]
        if entity_name == "equipment_bookings":
            return []
        return []

    def mock_create(entity_name, payload, tenant_id):
        return created_booking

    monkeypatch.setattr("app.modules.equipment_booking.service.list_entities_for_tenant", mock_list)
    monkeypatch.setattr("app.modules.equipment_booking.service.create_entity_for_tenant", mock_create)

    result = create_equipment_booking(_make_booking_payload("CENT-004"), tenant_id=1)
    assert result is not None


# ---------------------------------------------------------------------------
# 6. Equipment not found still raises the original error
# ---------------------------------------------------------------------------

def test_w71_equipment_not_found_raises(monkeypatch):
    """create_equipment_booking must raise ValueError('Equipment not found') when code is unknown."""
    monkeypatch.setattr("app.modules.equipment_booking.service._check_requester_enrollment_for_booking", lambda *a, **kw: None)
    def mock_list(entity_name, tenant_id):
        return []

    monkeypatch.setattr("app.modules.equipment_booking.service.list_entities_for_tenant", mock_list)

    with pytest.raises(ValueError, match="Equipment not found"):
        create_equipment_booking(_make_booking_payload("UNKNOWN-001"), tenant_id=1)


# ---------------------------------------------------------------------------
# 7. Conflict path must not emit phantom event before persistence
# ---------------------------------------------------------------------------

def test_w71_conflict_rejected_without_event_publish(monkeypatch):
    """On conflict rejection, service must raise without publishing phantom conflict event."""
    monkeypatch.setattr("app.modules.equipment_booking.service._check_requester_enrollment_for_booking", lambda *a, **kw: None)
    equipment = _make_equipment("CENT-005", "available")
    existing_conflict = {
        "id": 77,
        "equipment_code": "CENT-005",
        "booking_status": "confirmed",
    }
    publish_calls: list[dict] = []

    def mock_list(entity_name, tenant_id):
        if entity_name == "equipment_items":
            return [equipment]
        if entity_name == "equipment_bookings":
            return [existing_conflict]
        return []

    def mock_publish_event(self, **kwargs):
        publish_calls.append(kwargs)

    monkeypatch.setattr("app.modules.equipment_booking.service.list_entities_for_tenant", mock_list)
    monkeypatch.setattr("app.platform.events.publisher.EventPublisher.publish_event", mock_publish_event)

    with pytest.raises(ValueError, match="Booking conflict detected for equipment"):
        create_equipment_booking(_make_booking_payload("CENT-005"), tenant_id=1)

    assert publish_calls == []
