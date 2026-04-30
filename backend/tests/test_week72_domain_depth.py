"""W72 — equipment_booking transition-guard hardening.

Root fix: strict lifecycle transition guard in update_equipment_booking_status()
with explicit missing-record handling before persist.
"""
from __future__ import annotations

import pytest

from app.modules.equipment_booking.service import (
    _ALLOWED_BOOKING_STATUS_TRANSITIONS,
    update_equipment_booking_status,
)


@pytest.mark.parametrize(
    "current_status,next_status",
    [
        ("pending", "confirmed"),
        ("confirmed", "active"),
        ("active", "completed"),
        ("confirmed", "overdue"),
        ("overdue", "completed"),
    ],
)
def test_w72_valid_transition_succeeds(monkeypatch, current_status: str, next_status: str):
    bookings = [{"id": 10, "booking_status": current_status}]

    def mock_list(entity_name, tenant_id):
        if entity_name == "equipment_bookings":
            return bookings
        if entity_name == "equipment_booking_overdue_alerts":
            return []
        return []

    def mock_update(entity_name, booking_id, payload, tenant_id):
        assert entity_name == "equipment_bookings"
        assert booking_id == 10
        assert payload["booking_status"] == next_status
        return {"id": booking_id, "booking_status": next_status}

    monkeypatch.setattr("app.modules.equipment_booking.service.list_entities_for_tenant", mock_list)
    monkeypatch.setattr("app.modules.equipment_booking.service.update_entity_for_tenant", mock_update)

    result = update_equipment_booking_status(booking_id=10, status=next_status, tenant_id=1)
    assert result["booking_status"] == next_status


def test_w72_invalid_transition_blocked(monkeypatch):
    """completed -> active must be blocked by transition guard."""
    bookings = [{"id": 11, "booking_status": "completed"}]

    def mock_list(entity_name, tenant_id):
        return bookings

    monkeypatch.setattr("app.modules.equipment_booking.service.list_entities_for_tenant", mock_list)

    with pytest.raises(ValueError, match="Invalid equipment booking status transition"):
        update_equipment_booking_status(booking_id=11, status="active", tenant_id=1)


def test_w72_missing_booking_blocked_explicitly(monkeypatch):
    """Missing booking must raise explicit not-found domain error."""

    def mock_list(entity_name, tenant_id):
        return []

    monkeypatch.setattr("app.modules.equipment_booking.service.list_entities_for_tenant", mock_list)

    with pytest.raises(ValueError, match="not found"):
        update_equipment_booking_status(booking_id=404, status="confirmed", tenant_id=1)


def test_w72_unknown_target_status_blocked(monkeypatch):
    bookings = [{"id": 12, "booking_status": "pending"}]

    def mock_list(entity_name, tenant_id):
        return bookings

    monkeypatch.setattr("app.modules.equipment_booking.service.list_entities_for_tenant", mock_list)

    with pytest.raises(ValueError, match="Unsupported target booking status"):
        update_equipment_booking_status(booking_id=12, status="migrated", tenant_id=1)


def test_w72_transition_map_terminals():
    """Terminal statuses must not allow reopening transitions."""
    assert _ALLOWED_BOOKING_STATUS_TRANSITIONS["completed"] == frozenset()
    assert _ALLOWED_BOOKING_STATUS_TRANSITIONS["cancelled"] == frozenset()
