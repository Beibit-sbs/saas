"""XCVIII - Equipment Booking Service Hardening (canonical 10-step hooks).

Verifies:
1. create_equipment_booking uses canonical EventPublisher constructor and records metric.
2. update_equipment_booking_status uses canonical EventPublisher constructor and records metric.
3. create_equipment_booking survives outcome hook failure and still records metric.
4. update_equipment_booking_status rejects invalid transition (guard fail-closed).
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

from app.modules.equipment_booking import service as svc

MODULE = "app.modules.equipment_booking.service"


def _booking(*, booking_status: str = "pending") -> dict[str, object]:
    return {
        "id": 11,
        "equipment_code": "LAB-001",
        "requester_id": "STU-001",
        "booking_status": booking_status,
        "conflict_flag": False,
    }


def _equipment() -> list[dict[str, object]]:
    return [{"id": 99, "equipment_code": "LAB-001", "status": "available"}]


def _active_enrollment() -> list[dict[str, object]]:
    return [{"student_id": "STU-001", "status": "active"}]


def test_create_equipment_booking_uses_canonical_event_publisher_and_metric() -> None:
    metrics: list[tuple[int, str, int]] = []

    def _capture_metric(tenant_id: int, metric: str, value: int = 1) -> None:
        metrics.append((tenant_id, metric, value))

    def _list(entity: str, tenant_id: int) -> list[dict[str, object]]:
        if entity == "student_enrollments":
            return _active_enrollment()
        if entity == "equipment_items":
            return _equipment()
        if entity == "equipment_bookings":
            return []
        return []

    with (
        patch(f"{MODULE}.list_entities_for_tenant", side_effect=_list),
        patch(f"{MODULE}.create_entity_for_tenant", return_value=_booking()),
        patch(f"{MODULE}.EventPublisher") as mock_ep,
        patch(f"{MODULE}._metric", side_effect=_capture_metric),
        patch(f"{MODULE}.log_admin_action"),
        patch("app.modules.brain_core.service.brain_core_service"),
    ):
        result = svc.create_equipment_booking(
            {
                "equipment_code": "LAB-001",
                "requester_id": "STU-001",
                "booking_status": "pending",
            },
            tenant_id=1,
            actor="admin@test.com",
        )

    assert int(result["id"]) == 11
    mock_ep.assert_called_once_with()
    mock_ep.return_value.publish_event.assert_called_once()
    assert (1, "equipment_bookings_created", 1) in metrics


def test_update_equipment_booking_status_uses_canonical_event_publisher_and_metric() -> None:
    metrics: list[tuple[int, str, int]] = []

    def _capture_metric(tenant_id: int, metric: str, value: int = 1) -> None:
        metrics.append((tenant_id, metric, value))

    with (
        patch(f"{MODULE}.list_entities_for_tenant", return_value=[_booking(booking_status="pending")]),
        patch(f"{MODULE}.update_entity_for_tenant", return_value=_booking(booking_status="confirmed")),
        patch(f"{MODULE}.EventPublisher") as mock_ep,
        patch(f"{MODULE}._metric", side_effect=_capture_metric),
        patch(f"{MODULE}.log_admin_action"),
        patch("app.modules.brain_core.service.brain_core_service"),
    ):
        result = svc.update_equipment_booking_status(
            booking_id=11,
            status="confirmed",
            tenant_id=1,
            actor="admin@test.com",
        )

    assert str(result["booking_status"]).lower() == "confirmed"
    mock_ep.assert_called_once_with()
    mock_ep.return_value.publish_event.assert_called_once()
    assert (1, "equipment_booking_status_updates", 1) in metrics


def test_create_equipment_booking_survives_outcome_failure_and_records_metric() -> None:
    metrics: list[tuple[int, str, int]] = []

    def _capture_metric(tenant_id: int, metric: str, value: int = 1) -> None:
        metrics.append((tenant_id, metric, value))

    def _list(entity: str, tenant_id: int) -> list[dict[str, object]]:
        if entity == "student_enrollments":
            return _active_enrollment()
        if entity == "equipment_items":
            return _equipment()
        if entity == "equipment_bookings":
            return []
        return []

    with (
        patch(f"{MODULE}.list_entities_for_tenant", side_effect=_list),
        patch(f"{MODULE}.create_entity_for_tenant", return_value=_booking()),
        patch(f"{MODULE}.EventPublisher") as mock_ep,
        patch(f"{MODULE}._metric", side_effect=_capture_metric),
        patch(f"{MODULE}.log_admin_action"),
        patch("app.modules.brain_core.service.brain_core_service") as mock_brain,
    ):
        mock_brain.record_dispatch_outcome.side_effect = RuntimeError("brain down")
        result = svc.create_equipment_booking(
            {
                "equipment_code": "LAB-001",
                "requester_id": "STU-001",
                "booking_status": "pending",
            },
            tenant_id=1,
            actor="admin@test.com",
        )

    assert int(result["id"]) == 11
    mock_ep.assert_called_once_with()
    mock_ep.return_value.publish_event.assert_called_once()
    assert (1, "equipment_bookings_created", 1) in metrics


def test_update_equipment_booking_status_rejects_invalid_transition_fail_closed() -> None:
    with patch(f"{MODULE}.list_entities_for_tenant", return_value=[_booking(booking_status="pending")]):
        with pytest.raises(ValueError, match="Invalid equipment booking status transition"):
            svc.update_equipment_booking_status(
                booking_id=11,
                status="completed",
                tenant_id=1,
                actor="admin@test.com",
            )
