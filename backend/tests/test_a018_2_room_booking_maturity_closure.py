"""A-018.2 — Room booking maturity closure tests."""
from __future__ import annotations

from unittest.mock import patch

import pytest

from app.modules.brain_core.classifiers.risk_classifier import RiskClassifier
from app.modules.brain_core.registry import DecisionRegistry, SignalRegistry
from app.modules.room_booking import router as room_booking_router
from app.modules.room_booking.service import assess_room_allocation, request_booking
from app.platform.event_ingestion.types import VALID_EVENT_TYPES
from app.platform.events.registry import EXACT_EVENT_REGISTRY
from app.platform.kpi import service as kpi_service


def test_room_booking_router_contract_registered() -> None:
    assert room_booking_router.router.prefix == "/api/admin/room-booking"


def test_room_booking_events_registered_in_platform_contracts() -> None:
    expected = {
        "booking.approved",
        "booking.conflict_detected",
        "room.released",
        "resource.overload",
    }
    for event_type in expected:
        assert event_type in VALID_EVENT_TYPES
        assert event_type in EXACT_EVENT_REGISTRY


def test_signal_registry_reuses_existing_section_conflict_scenario_for_room_booking_events() -> None:
    assert SignalRegistry.signals["booking.conflict_detected"]["scenario"] == "section_conflict"
    assert SignalRegistry.signals["resource.overload"]["scenario"] == "section_conflict"
    assert "booking.conflict_detected" in DecisionRegistry.decisions["section_conflict"]["allowed_event_types"]
    assert "resource.overload" in DecisionRegistry.decisions["section_conflict"]["allowed_event_types"]


def test_risk_classifier_maps_booking_conflict_to_high_section_conflict() -> None:
    classifier = RiskClassifier()
    result = classifier.classify(
        {
            "event_type": "booking.conflict_detected",
            "payload": {"room_id": "R-10", "start_time": "2026-05-10T10:00:00", "conflict_type": "room_conflict"},
        },
        {},
    )

    assert result["reasoning_path"] == "section_conflict_high"
    assert result["severity"] == "high"


def test_risk_classifier_maps_resource_overload_to_medium_or_high_section_conflict() -> None:
    classifier = RiskClassifier()

    high = classifier.classify(
        {
            "event_type": "resource.overload",
            "payload": {"room_id": "R-10", "utilization": 1.0},
        },
        {},
    )
    medium = classifier.classify(
        {
            "event_type": "resource.overload",
            "payload": {"room_id": "R-10", "utilization": 0.95},
        },
        {},
    )

    assert high["reasoning_path"] == "section_conflict_high"
    assert medium["reasoning_path"] == "section_conflict_medium"


def test_request_booking_conflict_emits_legacy_and_scheduling_namespace_events() -> None:
    existing = [
        {
            "id": "b-1",
            "room_id": "r-1",
            "status": "APPROVED",
            "start_time": "2026-06-01T09:00",
            "tenant_id": 5,
        }
    ]
    with (
        patch("app.modules.room_booking.service.list_entities_for_tenant", return_value=existing),
        patch("app.modules.room_booking.service.EventPublisher") as mock_pub,
    ):
        with pytest.raises(ValueError, match="conflict"):
            request_booking(
                5,
                room_id="r-1",
                requester_id="u-1",
                start_time="2026-06-01T09:00",
                end_time="2026-06-01T10:00",
            )

    emitted_types = [call.kwargs["event_type"] for call in mock_pub.return_value.publish_event.call_args_list]
    assert "booking.conflict_detected" in emitted_types
    assert "scheduling.room_conflict.detected" in emitted_types


def test_assess_room_allocation_emits_scheduling_readiness_signals() -> None:
    rooms = [{"id": "r-2", "capacity": 30, "tenant_id": 8}]

    with (
        patch("app.modules.room_booking.service.list_entities_for_tenant", return_value=rooms),
        patch("app.modules.room_booking.service.EventPublisher") as mock_pub,
    ):
        result = assess_room_allocation(8, room_id="r-2", required_capacity=45)

    assert result["room_allocation_required"] is True
    emitted_types = [call.kwargs["event_type"] for call in mock_pub.return_value.publish_event.call_args_list]
    assert emitted_types.count("scheduling.room_allocation.required") == 1
    assert emitted_types.count("scheduling.capacity_mismatch.detected") == 1


def test_room_booking_kpi_lineage_compatibility_is_additive() -> None:
    assert "booking.conflict_detected" in kpi_service.EVENT_DERIVED_METRIC_LINEAGE["scheduling_conflicts_count"]
    assert "resource.overload" in kpi_service.EVENT_DERIVED_METRIC_LINEAGE["capacity_risk_sections_count"]
