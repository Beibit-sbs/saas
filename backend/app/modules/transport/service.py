"""Phase VI-VI2: Transport service."""
from __future__ import annotations

from app.platform.events.publisher import EventPublisher
from app.modules.university_core.tenant_entity_service import (
    create_entity_for_tenant,
    list_entities_for_tenant,
)
from app.core.module_helpers.service_validation import DomainValidationError

_DISRUPTED_STATUSES = {"disrupted", "cancelled", "suspended"}

# ---------------------------------------------------------------------------
# W105: Transport booking route status guard
# A booking may only be created for a route that exists AND has a bookable
# status. Booking a cancelled/disrupted/non-existent route generates confirmed
# reservations for ghost journeys, corrupts transport KPIs, and misleads students.
# ---------------------------------------------------------------------------
_BOOKABLE_ROUTE_STATUSES: frozenset[str] = frozenset({"active", "scheduled"})


def _check_route_is_bookable(
    *,
    tenant_id: int,
    route_code: str,
) -> None:
    """W105: Cross-entity guard — transport_bookings × transport_routes.

    A transport booking may only be created for a route with status 'active'
    or 'scheduled'. Booking a disrupted, cancelled, or non-existent route:
      - Confirms a journey that will not operate
      - Misleads students expecting transport that won't arrive
      - Corrupts Brain Core transport utilisation analytics
      - Creates booking KPIs for ghost routes

    FAIL-CLOSED: if route lookup fails (any exception), the booking is BLOCKED.
    """
    try:
        all_routes = list_entities_for_tenant("transport_routes", tenant_id)
    except Exception as exc:
        raise DomainValidationError(
            f"Transport booking blocked for route_code='{route_code}': "
            f"route lookup failed — {exc}. Cannot verify route status."
        ) from exc

    matching = [
        row for row in all_routes
        if str(row.get("route_code") or "").strip().lower() == str(route_code).strip().lower()
    ]

    if not matching:
        raise DomainValidationError(
            f"Transport booking blocked for route_code='{route_code}': "
            "route not found. Only existing routes can accept bookings."
        )

    route = matching[0]
    route_status = str(route.get("status") or "").strip().lower()
    if route_status not in _BOOKABLE_ROUTE_STATUSES:
        raise DomainValidationError(
            f"Transport booking blocked for route_code='{route_code}': "
            f"route status is '{route_status}' — not bookable. "
            f"Only routes with status {sorted(_BOOKABLE_ROUTE_STATUSES)} accept bookings."
        )

_VEHICLE_TYPE_MAX_ACTIVE_ROUTES: dict[str, int] = {
    "bus": 10,
    "shuttle": 8,
    "van": 5,
    "minibus": 6,
}
_ACTIVE_ROUTE_STATUSES = frozenset({"active", "scheduled"})


def _ensure_transport_disruption_record(
    route: dict[str, object], tenant_id: int
) -> None:
    route_id = str(route.get("id") or "").strip()
    if not route_id:
        return

    for row in list_entities_for_tenant("transport_disruption_records", tenant_id):
        if (
            str(row.get("integration_source") or "").strip() == "transport_disruption"
            and str(row.get("source_entity_id") or "").strip() == route_id
        ):
            return

    create_entity_for_tenant(
        "transport_disruption_records",
        {
            "route_id": route_id,
            "route_code": str(route.get("route_code") or "").strip(),
            "vehicle_type": str(route.get("vehicle_type") or "").strip(),
            "disruption_status": str(route.get("status") or "").strip(),
            "severity": "high",
            "record_status": "open",
            "integration_source": "transport_disruption",
            "source_entity_id": route_id,
        },
        tenant_id,
    )


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
    vehicle_type = str(payload.get("vehicle_type") or "").strip().lower()
    status = str(payload.get("status") or "").strip().lower()
    cap = _VEHICLE_TYPE_MAX_ACTIVE_ROUTES.get(vehicle_type)
    if cap is not None and status in _ACTIVE_ROUTE_STATUSES:
        active_count = sum(
            1
            for row in list_entities_for_tenant("transport_routes", tenant_id)
            if (
                str(row.get("vehicle_type") or "").strip().lower() == vehicle_type
                and str(row.get("status") or "").strip().lower() in _ACTIVE_ROUTE_STATUSES
            )
        )
        if active_count >= cap:
            raise ValueError(
                f"Transport route cap exceeded: vehicle_type '{vehicle_type}' already has "
                f"{active_count} active routes (max {cap})"
            )

    record = create_entity_for_tenant("transport_routes", payload, tenant_id)
    route_status = str(record.get("status") or "").strip().lower()
    if route_status in _DISRUPTED_STATUSES:
        _ensure_transport_disruption_record(record, tenant_id)
        record_id = str(record.get("id") or "unknown")  # noqa: used below
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
    # W105: Route status guard — booking requires an active/scheduled route
    route_code = str(payload.get("route_code") or "").strip()
    _check_route_is_bookable(tenant_id=tenant_id, route_code=route_code)
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
