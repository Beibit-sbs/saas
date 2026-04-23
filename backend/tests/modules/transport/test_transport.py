"""Phase VI-VI2: Transport module tests."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.modules.transport import service as transport_service
from tests.conftest import ADMIN_HEADERS, client as test_client


def test_list_transport_routes_empty(monkeypatch) -> None:
    monkeypatch.setattr(transport_service, "list_entities_for_tenant", lambda name, tid: [])
    assert transport_service.list_transport_routes(tenant_id=1) == []


def test_list_transport_routes_filter_by_status(monkeypatch) -> None:
    rows = [
        {"id": 1, "route_code": "R-1", "route_name": "Campus Loop", "status": "active", "tenant_id": 1},
        {"id": 2, "route_code": "R-2", "route_name": "City Express", "status": "disrupted", "tenant_id": 1},
    ]
    monkeypatch.setattr(transport_service, "list_entities_for_tenant", lambda name, tid: rows)
    result = transport_service.list_transport_routes(tenant_id=1, status="active")
    assert len(result) == 1
    assert result[0]["route_code"] == "R-1"


def test_create_transport_route_disrupted_fires_signal(monkeypatch) -> None:
    created = {
        "id": 5,
        "route_code": "R-5",
        "route_name": "South Gate",
        "status": "cancelled",
        "vehicle_type": "bus",
        "departure_time": "08:00",
        "arrival_time": "08:30",
        "capacity": 40,
        "assigned_driver": None,
        "tenant_id": 1,
    }
    monkeypatch.setattr(transport_service, "create_entity_for_tenant", lambda name, payload, tid: created)

    with patch("app.modules.transport.service.EventPublisher") as mock_pub_cls:
        publisher = MagicMock()
        mock_pub_cls.return_value = publisher
        record = transport_service.create_transport_route(
            {"route_code": "R-5", "route_name": "South Gate", "status": "cancelled"},
            tenant_id=1,
        )

    assert record["id"] == 5
    publisher.publish_event.assert_called_once()
    call_kwargs = publisher.publish_event.call_args.kwargs
    assert call_kwargs["event_type"] == "campus.transport.disruption_detected"
    assert call_kwargs["payload_json"]["route_status"] == "cancelled"


def test_create_transport_route_active_no_signal(monkeypatch) -> None:
    created = {
        "id": 6, "route_code": "R-6", "route_name": "North Gate", "status": "active", "tenant_id": 1,
    }
    monkeypatch.setattr(transport_service, "create_entity_for_tenant", lambda name, payload, tid: created)

    with patch("app.modules.transport.service.EventPublisher") as mock_pub_cls:
        publisher = MagicMock()
        mock_pub_cls.return_value = publisher
        transport_service.create_transport_route(
            {"route_code": "R-6", "route_name": "North Gate", "status": "active"},
            tenant_id=1,
        )

    publisher.publish_event.assert_not_called()


def test_get_transport_brain_context_high_risk(monkeypatch) -> None:
    routes = [
        {"id": 1, "route_code": "R-1", "route_name": "A", "status": "active", "tenant_id": 1},
        {"id": 2, "route_code": "R-2", "route_name": "B", "status": "cancelled", "tenant_id": 1},
    ]
    bookings = [{"id": 1, "route_code": "R-1", "student_id": "STU-1", "booking_status": "confirmed", "tenant_id": 1}]

    def mock_list(name, tid):
        if name == "transport_routes":
            return routes
        return bookings

    monkeypatch.setattr(transport_service, "list_entities_for_tenant", mock_list)
    ctx = transport_service.get_transport_brain_context(tenant_id=1)
    assert ctx["risk_level"] == "high"
    assert ctx["cancelled_routes"] == 1
    assert ctx["total_bookings"] == 1


def test_http_list_transport_routes_empty() -> None:
    response = test_client.get("/api/admin/transport/routes", headers=ADMIN_HEADERS)
    assert response.status_code == 200
    assert response.json()["records"] == []


def test_http_create_transport_route() -> None:
    payload = {
        "route_code": "R-HTTP-1",
        "route_name": "HTTP Test Route",
        "status": "active",
        "vehicle_type": "minibus",
        "capacity": 20,
    }
    response = test_client.post("/api/admin/transport/routes", json=payload, headers=ADMIN_HEADERS)
    assert response.status_code == 201
    data = response.json()["record"]
    assert data["route_code"] == "R-HTTP-1"
    assert data["status"] == "active"


def test_http_get_transport_brain_context() -> None:
    response = test_client.get("/api/admin/transport/brain-context", headers=ADMIN_HEADERS)
    assert response.status_code == 200
    ctx = response.json()
    assert ctx["module"] == "transport"
    assert "risk_level" in ctx
