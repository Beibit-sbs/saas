"""XXXIV.8 — equipment_booking: 10-step loop event hardening tests."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.core.module_helpers.service_validation import DomainValidationError
from app.modules.equipment_booking import service as svc

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_ACTIVE_ENROLLMENT = [{"student_id": "STU-001", "status": "active"}]
_EQUIPMENT = [{"equipment_code": "LAB-001", "status": "available", "id": 10}]

_BOOKING_PAYLOAD: dict[str, object] = {
    "requester_id": "STU-001",
    "equipment_code": "LAB-001",
    "booking_status": "pending",
}


# ---------------------------------------------------------------------------
# 1. create_equipment_booking fires booking.created event
# ---------------------------------------------------------------------------

def test_create_equipment_booking_publishes_booking_created() -> None:
    store: list[dict] = []

    def _create(entity_type: str, payload: dict, tenant_id: int) -> dict:
        record = {**payload, "id": 1}
        store.append(record)
        return record

    def _list(entity_type: str, tenant_id: int) -> list[dict]:
        if entity_type == "student_enrollments":
            return _ACTIVE_ENROLLMENT
        if entity_type == "equipment_items":
            return _EQUIPMENT
        return []

    with (
        patch("app.modules.equipment_booking.service.create_entity_for_tenant", side_effect=_create),
        patch("app.modules.equipment_booking.service.list_entities_for_tenant", side_effect=_list),
        patch("app.modules.equipment_booking.service.EventPublisher") as mock_cls,
    ):
        mock_pub = MagicMock()
        mock_cls.return_value = mock_pub

        result = svc.create_equipment_booking(_BOOKING_PAYLOAD.copy(), tenant_id=1)

    assert result["id"] == 1
    event_types = [c.kwargs.get("event_type") for c in mock_pub.publish_event.call_args_list]
    assert "equipment_booking.booking.created" in event_types


# ---------------------------------------------------------------------------
# 2. create_equipment_booking creates action log entity
# ---------------------------------------------------------------------------

def test_create_equipment_booking_creates_action_log() -> None:
    created_entities: list[str] = []

    def _create(entity_type: str, payload: dict, tenant_id: int) -> dict:
        created_entities.append(entity_type)
        return {**payload, "id": 2}

    def _list(entity_type: str, tenant_id: int) -> list[dict]:
        if entity_type == "student_enrollments":
            return _ACTIVE_ENROLLMENT
        if entity_type == "equipment_items":
            return _EQUIPMENT
        return []

    with (
        patch("app.modules.equipment_booking.service.create_entity_for_tenant", side_effect=_create),
        patch("app.modules.equipment_booking.service.list_entities_for_tenant", side_effect=_list),
        patch("app.modules.equipment_booking.service.EventPublisher"),
    ):
        svc.create_equipment_booking(_BOOKING_PAYLOAD.copy(), tenant_id=1)

    assert "equipment_booking_action_logs" in created_entities


# ---------------------------------------------------------------------------
# 3. Guard blocks requester with no active enrollment
# ---------------------------------------------------------------------------

def test_create_equipment_booking_guard_blocks_no_enrollment() -> None:
    inactive = [{"student_id": "STU-001", "status": "withdrawn"}]

    def _list(entity_type: str, tenant_id: int) -> list[dict]:
        if entity_type == "student_enrollments":
            return inactive
        return []

    with (
        patch("app.modules.equipment_booking.service.list_entities_for_tenant", side_effect=_list),
        patch("app.modules.equipment_booking.service.create_entity_for_tenant"),
        patch("app.modules.equipment_booking.service.EventPublisher"),
    ):
        with pytest.raises(DomainValidationError):
            svc.create_equipment_booking(_BOOKING_PAYLOAD.copy(), tenant_id=1)


# ---------------------------------------------------------------------------
# 4. update_equipment_booking_status confirmed → fires booking.confirmed
# ---------------------------------------------------------------------------

def test_update_equipment_booking_status_confirmed_fires_confirmed_event() -> None:
    existing = {"id": 5, "booking_status": "pending", "equipment_code": "LAB-001"}

    def _list(entity_type: str, tenant_id: int) -> list[dict]:
        if entity_type == "equipment_bookings":
            return [existing]
        return []

    def _update(entity_type: str, entity_id: int, payload: dict, tenant_id: int) -> dict:
        return {**existing, **payload, "id": entity_id}

    with (
        patch("app.modules.equipment_booking.service.list_entities_for_tenant", side_effect=_list),
        patch("app.modules.equipment_booking.service.update_entity_for_tenant", side_effect=_update),
        patch("app.modules.equipment_booking.service.EventPublisher") as mock_cls,
    ):
        mock_pub = MagicMock()
        mock_cls.return_value = mock_pub

        svc.update_equipment_booking_status(5, "confirmed", tenant_id=1)

    event_types = [c.kwargs.get("event_type") for c in mock_pub.publish_event.call_args_list]
    assert "equipment_booking.booking.confirmed" in event_types


# ---------------------------------------------------------------------------
# 5. update_equipment_booking_status cancelled → fires booking.cancelled
# ---------------------------------------------------------------------------

def test_update_equipment_booking_status_cancelled_fires_cancelled_event() -> None:
    existing = {"id": 6, "booking_status": "confirmed", "equipment_code": "LAB-002"}

    def _list(entity_type: str, tenant_id: int) -> list[dict]:
        if entity_type == "equipment_bookings":
            return [existing]
        return []

    def _update(entity_type: str, entity_id: int, payload: dict, tenant_id: int) -> dict:
        return {**existing, **payload, "id": entity_id}

    with (
        patch("app.modules.equipment_booking.service.list_entities_for_tenant", side_effect=_list),
        patch("app.modules.equipment_booking.service.update_entity_for_tenant", side_effect=_update),
        patch("app.modules.equipment_booking.service.EventPublisher") as mock_cls,
    ):
        mock_pub = MagicMock()
        mock_cls.return_value = mock_pub

        svc.update_equipment_booking_status(6, "cancelled", tenant_id=1)

    event_types = [c.kwargs.get("event_type") for c in mock_pub.publish_event.call_args_list]
    assert "equipment_booking.booking.cancelled" in event_types


# ---------------------------------------------------------------------------
# 6. completed transition → fires booking.returned
# ---------------------------------------------------------------------------

def test_update_equipment_booking_status_completed_fires_returned_event() -> None:
    existing = {"id": 7, "booking_status": "active", "equipment_code": "LAB-003"}

    def _list(entity_type: str, tenant_id: int) -> list[dict]:
        if entity_type == "equipment_bookings":
            return [existing]
        return []

    def _update(entity_type: str, entity_id: int, payload: dict, tenant_id: int) -> dict:
        return {**existing, **payload, "id": entity_id}

    with (
        patch("app.modules.equipment_booking.service.list_entities_for_tenant", side_effect=_list),
        patch("app.modules.equipment_booking.service.update_entity_for_tenant", side_effect=_update),
        patch("app.modules.equipment_booking.service.EventPublisher") as mock_cls,
    ):
        mock_pub = MagicMock()
        mock_cls.return_value = mock_pub

        svc.update_equipment_booking_status(7, "completed", tenant_id=1)

    event_types = [c.kwargs.get("event_type") for c in mock_pub.publish_event.call_args_list]
    assert "equipment_booking.booking.returned" in event_types


# ---------------------------------------------------------------------------
# 7. overdue transition → fires booking.overdue
# ---------------------------------------------------------------------------

def test_update_equipment_booking_status_overdue_fires_overdue_event() -> None:
    existing = {"id": 8, "booking_status": "confirmed", "equipment_code": "LAB-004"}

    def _list(entity_type: str, tenant_id: int) -> list[dict]:
        if entity_type == "equipment_bookings":
            return [existing]
        if entity_type == "equipment_booking_overdue_alerts":
            return []
        return []

    def _create(entity_type: str, payload: dict, tenant_id: int) -> dict:
        return {**payload, "id": 99}

    def _update(entity_type: str, entity_id: int, payload: dict, tenant_id: int) -> dict:
        return {**existing, **payload, "id": entity_id}

    with (
        patch("app.modules.equipment_booking.service.list_entities_for_tenant", side_effect=_list),
        patch("app.modules.equipment_booking.service.create_entity_for_tenant", side_effect=_create),
        patch("app.modules.equipment_booking.service.update_entity_for_tenant", side_effect=_update),
        patch("app.modules.equipment_booking.service.EventPublisher") as mock_cls,
    ):
        mock_pub = MagicMock()
        mock_cls.return_value = mock_pub

        svc.update_equipment_booking_status(8, "overdue", tenant_id=1)

    event_types = [c.kwargs.get("event_type") for c in mock_pub.publish_event.call_args_list]
    assert "equipment_booking.booking.overdue" in event_types


# ---------------------------------------------------------------------------
# 8. EventPublisher failure does not block booking creation
# ---------------------------------------------------------------------------

def test_create_equipment_booking_survives_event_publisher_failure() -> None:
    def _create(entity_type: str, payload: dict, tenant_id: int) -> dict:
        return {**payload, "id": 99}

    def _list(entity_type: str, tenant_id: int) -> list[dict]:
        if entity_type == "student_enrollments":
            return _ACTIVE_ENROLLMENT
        if entity_type == "equipment_items":
            return _EQUIPMENT
        return []

    with (
        patch("app.modules.equipment_booking.service.create_entity_for_tenant", side_effect=_create),
        patch("app.modules.equipment_booking.service.list_entities_for_tenant", side_effect=_list),
        patch("app.modules.equipment_booking.service.EventPublisher") as mock_cls,
    ):
        mock_pub = MagicMock()
        mock_pub.publish_event.side_effect = RuntimeError("broker down")
        mock_cls.return_value = mock_pub

        result = svc.create_equipment_booking(_BOOKING_PAYLOAD.copy(), tenant_id=1)

    assert result["id"] == 99
