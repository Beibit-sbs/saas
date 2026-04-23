"""Phase VI-VI2: Transport service."""
from __future__ import annotations

from app.platform.events.publisher import EventPublisher
from app.modules.university_core.tenant_entity_service import (
    create_entity_for_tenant,
    list_entities_for_tenant,
)

_DISRUPTED_STATUSES = {"disrupted", "cancelled", "suspended"}


def list_transport_routes(
    tenant_id: int,
    status: str | None = None,
) -> list[dict[str, object]]:
    rows = list_entities_for_tenant("transport_routes", tenant_id)
    status_filter = str(status or "").strip().lower()
    if not status_filter:
        return rows
    return [
        row for row in rows
        if str(row.get("status") or "").strip().lower() == status_filter
    ]


def create_transport_route(payload: dict[str, object], tenant_id: int) -> dict[str, object]:
    record = create_entity_for_tenant("transport_routes", payload, tenant_id)
    route_status = str(record.get("status") or "").strip().lower()
    if route_status in _DISRUPTED_STATUSES:
        record_id = str(record.get("id") or "unknown")
        EventPublisher().publish_event(
            tenant_id=tenant_id,
            event_type="campus.transport.disruption_detected",
            aggregate_type="transport_route",
            aggregate_id=record_id,
            payload_json={
                "route_code": record.get("route_code"),
                "route_name": record.get("route_name"),
                "route_status": route_status,
                "vehicle_type": record.get("vehicle_type"),
                "source_entity_type": "transport_route",
                "source_entity_id": record_id,
            },
        )
    return record


def list_transport_bookings(
    tenant_id: int,
    booking_status: str | None = None,
) -> list[dict[str, object]]:
    rows = list_entities_for_tenant("transport_bookings", tenant_id)
    status_filter = str(booking_status or "").strip().lower()
    if not status_filter:
        return rows
    return [
        row for row in rows
        if str(row.get("booking_status") or "").strip().lower() == status_filter
    ]


def create_transport_booking(payload: dict[str, object], tenant_id: int) -> dict[str, object]:
    return create_entity_for_tenant("transport_bookings", payload, tenant_id)


def get_transport_brain_context(tenant_id: int) -> dict[str, object]:
    routes = list_entities_for_tenant("transport_routes", tenant_id)
    bookings = list_entities_for_tenant("transport_bookings", tenant_id)

    active_routes = sum(
        1 for r in routes if str(r.get("status") or "").strip().lower() == "active"
    )
    disrupted_routes = sum(
        1 for r in routes if str(r.get("status") or "").strip().lower() == "disrupted"
    )
    cancelled_routes = sum(
        1 for r in routes if str(r.get("status") or "").strip().lower() == "cancelled"
    )

    if cancelled_routes > 0:
        risk_level = "high"
    elif disrupted_routes > 0:
        risk_level = "medium"
    else:
        risk_level = "low"

    return {
        "module": "transport",
        "tenant_id": tenant_id,
        "total_routes": len(routes),
        "active_routes": active_routes,
        "disrupted_routes": disrupted_routes,
        "cancelled_routes": cancelled_routes,
        "total_bookings": len(bookings),
        "risk_level": risk_level,
    }
