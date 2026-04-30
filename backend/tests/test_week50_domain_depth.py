"""W50 depth tests — equipment_booking: booking cap + overdue alerts."""
from __future__ import annotations

import pytest


def test_equipment_booking_status_cap_dict_structure():
    from app.modules.equipment_booking.service import _EQUIPMENT_BOOKING_STATUS_MAX_ACTIVE

    assert isinstance(_EQUIPMENT_BOOKING_STATUS_MAX_ACTIVE, dict)
    assert _EQUIPMENT_BOOKING_STATUS_MAX_ACTIVE["pending"] == 100
    assert _EQUIPMENT_BOOKING_STATUS_MAX_ACTIVE["confirmed"] == 200
    assert _EQUIPMENT_BOOKING_STATUS_MAX_ACTIVE["active"] == 150
    assert _EQUIPMENT_BOOKING_STATUS_MAX_ACTIVE["overdue"] == 50
    assert all(isinstance(v, int) and v > 0 for v in _EQUIPMENT_BOOKING_STATUS_MAX_ACTIVE.values())


def test_active_booking_statuses_and_overdue_risk_statuses():
    from app.modules.equipment_booking.service import (
        _ACTIVE_BOOKING_STATUSES,
        _OVERDUE_BOOKING_RISK_STATUSES,
    )

    assert isinstance(_ACTIVE_BOOKING_STATUSES, frozenset)
    assert "pending" in _ACTIVE_BOOKING_STATUSES
    assert "confirmed" in _ACTIVE_BOOKING_STATUSES
    assert "active" in _ACTIVE_BOOKING_STATUSES
    assert "overdue" not in _ACTIVE_BOOKING_STATUSES

    assert isinstance(_OVERDUE_BOOKING_RISK_STATUSES, frozenset)
    assert "overdue" in _OVERDUE_BOOKING_RISK_STATUSES


def test_create_equipment_booking_raises_when_cap_reached(monkeypatch):
    """ValueError raised when active booking count >= cap for the requested status."""
    from app.modules.equipment_booking import service as svc
    monkeypatch.setattr(svc, "_check_requester_enrollment_for_booking", lambda *a, **kw: None)

    # Equipment exists check passes
    monkeypatch.setattr(
        svc,
        "list_entities_for_tenant",
        lambda entity_type, tid: (
            [{"equipment_code": "LAB-001"}]
            if entity_type == "equipment_items"
            else [
                {"booking_status": "confirmed"}
                for _ in range(200)  # confirmed cap = 200
            ]
        ),
    )

    payload = {
        "equipment_code": "LAB-001",
        "requester_id": "student-42",
        "start_time": "2026-05-01T09:00",
        "end_time": "2026-05-01T11:00",
        "booking_status": "confirmed",
    }

    with pytest.raises(ValueError, match="active cap reached"):
        svc.create_equipment_booking(payload, tenant_id=7)


def test_ensure_overdue_booking_alert_record_is_idempotent(monkeypatch):
    """No duplicate alert created when one already exists."""
    from app.modules.equipment_booking import service as svc

    created: list[dict] = []

    def fake_list(entity_type, tid):
        if entity_type == "equipment_booking_overdue_alerts":
            return [
                {
                    "integration_source": "equipment_booking_overdue_queue",
                    "source_entity_id": "77",
                }
            ]
        return []

    def fake_create(entity_type, payload, tid):
        created.append(payload)
        return {**payload, "id": 1}

    monkeypatch.setattr(svc, "list_entities_for_tenant", fake_list)
    monkeypatch.setattr(svc, "create_entity_for_tenant", fake_create)

    svc._ensure_overdue_booking_alert_record(booking_id=77, tenant_id=7)

    assert len(created) == 0, "Alert must not be duplicated"
