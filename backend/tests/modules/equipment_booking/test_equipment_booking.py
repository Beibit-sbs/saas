"""Phase VII-VII2: Equipment booking module tests."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.modules.equipment_booking import service as eq_service
from tests.conftest import ADMIN_HEADERS, client as test_client


def test_list_equipment_empty(monkeypatch) -> None:
    monkeypatch.setattr(eq_service, "list_entities_for_tenant", lambda name, tid: [])
    assert eq_service.list_equipment(tenant_id=1) == []


def test_list_equipment_filter_by_category(monkeypatch) -> None:
    rows = [
        {"id": 1, "equipment_code": "MIC-001", "name": "Microscope", "category": "microscopy", "status": "available", "tenant_id": 1},
        {"id": 2, "equipment_code": "CEN-001", "name": "Centrifuge", "category": "centrifugation", "status": "available", "tenant_id": 1},
    ]
    monkeypatch.setattr(eq_service, "list_entities_for_tenant", lambda name, tid: rows)
    result = eq_service.list_equipment(tenant_id=1, category="microscopy")
    assert len(result) == 1
    assert result[0]["equipment_code"] == "MIC-001"


def test_list_equipment_bookings_filter_by_status(monkeypatch) -> None:
    rows = [
        {"id": 1, "equipment_code": "MIC-001", "requester_id": "USER-1", "start_time": "09:00", "end_time": "11:00", "booking_status": "confirmed", "conflict_flag": False, "tenant_id": 1},
        {"id": 2, "equipment_code": "CEN-001", "requester_id": "USER-2", "start_time": "10:00", "end_time": "12:00", "booking_status": "pending", "conflict_flag": False, "tenant_id": 1},
    ]
    monkeypatch.setattr(eq_service, "list_entities_for_tenant", lambda name, tid: rows)
    result = eq_service.list_equipment_bookings(tenant_id=1, booking_status="confirmed")
    assert len(result) == 1
    assert result[0]["equipment_code"] == "MIC-001"


def test_create_equipment_booking_conflict_fires_signal(monkeypatch) -> None:
    """When another active booking exists for same equipment code, conflict signal fires."""
    existing = [
        {"id": 1, "equipment_code": "MIC-001", "requester_id": "USER-1", "start_time": "09:00", "end_time": "11:00", "booking_status": "confirmed", "conflict_flag": False, "tenant_id": 1},
    ]
    created = {
        "id": 20,
        "equipment_code": "MIC-001",
        "requester_id": "USER-2",
        "start_time": "10:00",
        "end_time": "12:00",
        "booking_status": "pending",
        "conflict_flag": True,
        "purpose": None,
        "integration_source": None,
        "tenant_id": 1,
    }

    def fake_list(name: str, tid: int) -> list:
        if name == "equipment_bookings":
            return existing
        return []

    monkeypatch.setattr(eq_service, "list_entities_for_tenant", fake_list)
    monkeypatch.setattr(eq_service, "create_entity_for_tenant", lambda name, payload, tid: created)

    with patch("app.modules.equipment_booking.service.EventPublisher") as mock_pub_cls:
        publisher = MagicMock()
        mock_pub_cls.return_value = publisher
        record = eq_service.create_equipment_booking(
            {"equipment_code": "MIC-001", "requester_id": "USER-2", "start_time": "10:00", "end_time": "12:00", "booking_status": "pending"},
            tenant_id=1,
        )

    assert record["id"] == 20
    publisher.publish_event.assert_called_once()
    call_kwargs = publisher.publish_event.call_args.kwargs
    assert call_kwargs["event_type"] == "research.equipment.booking_conflict_detected"
    assert call_kwargs["payload_json"]["equipment_code"] == "MIC-001"


def test_create_equipment_booking_no_conflict_no_signal(monkeypatch) -> None:
    """No existing bookings → no conflict → no signal."""
    created = {
        "id": 21,
        "equipment_code": "CEN-001",
        "requester_id": "USER-3",
        "start_time": "14:00",
        "end_time": "16:00",
        "booking_status": "confirmed",
        "conflict_flag": False,
        "purpose": None,
        "integration_source": None,
        "tenant_id": 2,
    }
    monkeypatch.setattr(eq_service, "list_entities_for_tenant", lambda name, tid: [])
    monkeypatch.setattr(eq_service, "create_entity_for_tenant", lambda name, payload, tid: created)

    with patch("app.modules.equipment_booking.service.EventPublisher") as mock_pub_cls:
        publisher = MagicMock()
        mock_pub_cls.return_value = publisher
        record = eq_service.create_equipment_booking(
            {"equipment_code": "CEN-001", "requester_id": "USER-3", "start_time": "14:00", "end_time": "16:00", "booking_status": "confirmed"},
            tenant_id=2,
        )

    publisher.publish_event.assert_not_called()
    assert record["id"] == 21


def test_get_equipment_booking_brain_context_constrained(monkeypatch) -> None:
    equipment = [
        {"id": 1, "equipment_code": "MIC-001", "status": "available", "tenant_id": 3},
        {"id": 2, "equipment_code": "CEN-001", "status": "in_use", "tenant_id": 3},
    ]
    bookings = [
        {"id": 1, "equipment_code": "MIC-001", "booking_status": "confirmed", "conflict_flag": True, "tenant_id": 3},
        {"id": 2, "equipment_code": "MIC-001", "booking_status": "active", "conflict_flag": False, "tenant_id": 3},
    ]

    def fake_list(name: str, tid: int) -> list:
        if name == "equipment_items":
            return equipment
        return bookings

    monkeypatch.setattr(eq_service, "list_entities_for_tenant", fake_list)
    ctx = eq_service.get_equipment_booking_brain_context(tenant_id=3)
    assert ctx["total_equipment"] == 2
    assert ctx["available_equipment"] == 1
    assert ctx["conflict_bookings"] == 1
    assert ctx["availability_status"] == "constrained"


def test_get_equipment_booking_brain_context_empty(monkeypatch) -> None:
    monkeypatch.setattr(eq_service, "list_entities_for_tenant", lambda name, tid: [])
    ctx = eq_service.get_equipment_booking_brain_context(tenant_id=1)
    assert ctx["total_equipment"] == 0
    assert ctx["utilization_rate"] == 0.0
    assert ctx["availability_status"] == "available"


def test_http_list_equipment_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "app.modules.equipment_booking.router.list_equipment",
        lambda tenant_id, category=None, status=None: [],
    )
    resp = test_client.get("/api/admin/equipment-booking/equipment", headers=dict(ADMIN_HEADERS))
    assert resp.status_code == 200
    assert resp.json()["records"] == []


def test_http_create_booking(monkeypatch: pytest.MonkeyPatch) -> None:
    created = {
        "id": 30,
        "equipment_code": "MIC-001",
        "requester_id": "USER-30",
        "start_time": "09:00",
        "end_time": "11:00",
        "booking_status": "pending",
        "conflict_flag": False,
        "purpose": None,
        "integration_source": None,
        "tenant_id": 1,
    }
    monkeypatch.setattr(
        "app.modules.equipment_booking.router.create_equipment_booking",
        lambda payload, tenant_id: created,
    )
    resp = test_client.post(
        "/api/admin/equipment-booking/bookings",
        json={
            "equipment_code": "MIC-001",
            "requester_id": "USER-30",
            "start_time": "09:00",
            "end_time": "11:00",
            "booking_status": "pending",
        },
        headers=dict(ADMIN_HEADERS),
    )
    assert resp.status_code == 201
    assert resp.json()["record"]["id"] == 30


def test_http_brain_context_equipment(monkeypatch: pytest.MonkeyPatch) -> None:
    ctx = {
        "module": "equipment_booking",
        "tenant_id": 1,
        "total_equipment": 10,
        "available_equipment": 4,
        "total_bookings": 20,
        "active_bookings": 6,
        "conflict_bookings": 2,
        "utilization_rate": 0.6,
        "availability_status": "constrained",
    }
    monkeypatch.setattr(
        "app.modules.equipment_booking.router.get_equipment_booking_brain_context",
        lambda tenant_id: ctx,
    )
    resp = test_client.get("/api/admin/equipment-booking/brain-context", headers=dict(ADMIN_HEADERS))
    assert resp.status_code == 200
    body = resp.json()
    assert body["module"] == "equipment_booking"
    assert body["availability_status"] == "constrained"
    assert body["conflict_bookings"] == 2
