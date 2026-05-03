"""Phase VII-VII2: Equipment booking service."""
from __future__ import annotations

from app.core.module_helpers.service_validation import DomainValidationError
from app.modules.university_core.tenant_entity_service import (
    create_entity_for_tenant,
    list_entities_for_tenant,
    update_entity_for_tenant,
)
from app.platform.events.publisher import EventPublisher

_EQUIPMENT_BOOKING_STATUS_MAX_ACTIVE: dict[str, int] = {
    "pending": 100,
    "confirmed": 200,
    "active": 150,
    "cancelled": 500,
    "completed": 1000,
    "overdue": 50,
}
_ACTIVE_BOOKING_STATUSES = frozenset({"pending", "confirmed", "active"})
_OVERDUE_BOOKING_RISK_STATUSES = frozenset({"overdue"})
_ALLOWED_BOOKING_STATUS_TRANSITIONS: dict[str, frozenset[str]] = {
    "pending": frozenset({"confirmed", "cancelled"}),
    "confirmed": frozenset({"active", "cancelled", "overdue"}),
    "active": frozenset({"completed", "cancelled", "overdue"}),
    "overdue": frozenset({"completed", "cancelled"}),
    "completed": frozenset(),
    "cancelled": frozenset(),
}

# W71: equipment must be in one of these statuses to accept new bookings
_BOOKABLE_EQUIPMENT_STATUSES: frozenset[str] = frozenset({"available", "operational"})

# W119: requester must have an active enrollment to place a booking
_ACTIVE_ENROLLMENT_STATUSES: frozenset[str] = frozenset({"active", "enrolled"})


def _check_requester_enrollment_for_booking(
    *,
    tenant_id: int,
    requester_id: str,
) -> None:
    """Fail-closed guard: requester must have an active enrollment in this tenant.

    Dangerous action: creating an equipment booking that consumes shared lab inventory.
    Real-world constraint: only currently enrolled students/researchers may book equipment.
    External entity: enrollments (student_enrollments).
    Validates BEFORE create_entity_for_tenant().
    Bad outcome prevented: ghost bookings by withdrawn/expelled users block available inventory.
    """
    try:
        enrollments = list_entities_for_tenant("student_enrollments", tenant_id)
    except Exception as exc:
        raise DomainValidationError(
            f"Cannot verify requester enrollment: enrollment lookup failed ({exc})"
        ) from exc

    normalized_id = str(requester_id).strip().lower()
    active_enrollment = next(
        (
            row for row in enrollments
            if str(row.get("student_id") or "").strip().lower() == normalized_id
            and str(row.get("status") or "").strip().lower() in _ACTIVE_ENROLLMENT_STATUSES
        ),
        None,
    )
    if active_enrollment is None:
        raise DomainValidationError(
            f"Requester '{requester_id}' has no active enrollment in this tenant. "
            "Equipment bookings may only be placed by currently enrolled students or researchers."
        )


def list_equipment(
    tenant_id: int,
    category: str | None = None,
    status: str | None = None,
) -> list[dict[str, object]]:
    rows = list_entities_for_tenant("equipment_items", tenant_id)
    cat_filter = str(category or "").strip().lower()
    status_filter = str(status or "").strip().lower()

    result: list[dict[str, object]] = []
    for row in rows:
        if cat_filter and str(row.get("category") or "").strip().lower() != cat_filter:
            continue
        if status_filter and str(row.get("status") or "").strip().lower() != status_filter:
            continue
        result.append(row)
    return result


def create_equipment(payload: dict[str, object], tenant_id: int) -> dict[str, object]:
    return create_entity_for_tenant("equipment_items", payload, tenant_id)


def list_equipment_bookings(
    tenant_id: int,
    booking_status: str | None = None,
    equipment_code: str | None = None,
) -> list[dict[str, object]]:
    rows = list_entities_for_tenant("equipment_bookings", tenant_id)
    status_filter = str(booking_status or "").strip().lower()
    code_filter = str(equipment_code or "").strip().lower()

    result: list[dict[str, object]] = []
    for row in rows:
        if status_filter and str(row.get("booking_status") or "").strip().lower() != status_filter:
            continue
        if code_filter and str(row.get("equipment_code") or "").strip().lower() != code_filter:
            continue
        result.append(row)
    return result


def create_equipment_booking(payload: dict[str, object], tenant_id: int) -> dict[str, object]:
    """Create booking, detect conflicts, and block unsafe bookings."""
    requester_id = str(payload.get("requester_id") or "").strip()
    if not requester_id:
        raise DomainValidationError("requester_id is required for booking")

    # W119: fail-closed guard — requester must have active enrollment BEFORE any persist
    _check_requester_enrollment_for_booking(tenant_id=tenant_id, requester_id=requester_id)

    equipment_items = list_entities_for_tenant("equipment_items", tenant_id)
    new_code = str(payload.get("equipment_code") or "").strip().lower()
    equipment_record = next(
        (row for row in equipment_items
         if str(row.get("equipment_code") or "").strip().lower() == new_code),
        None,
    )
    if equipment_record is None:
        raise ValueError("Equipment not found")

    # W71: block booking if equipment is not in a bookable status
    equipment_status = str(equipment_record.get("status") or "").strip().lower()
    if equipment_status and equipment_status not in _BOOKABLE_EQUIPMENT_STATUSES:
        raise ValueError(
            f"Equipment '{new_code}' is not available for booking "
            f"(current status: '{equipment_status}'). "
            "Only equipment with status 'available' or 'operational' can be booked."
        )

    booking_status_val = str(payload.get("booking_status") or "pending").strip().lower()
    all_bookings = list_entities_for_tenant("equipment_bookings", tenant_id)
    active_booking_count = sum(
        1 for r in all_bookings
        if str(r.get("booking_status") or "").strip().lower() in _ACTIVE_BOOKING_STATUSES
    )
    booking_cap = _EQUIPMENT_BOOKING_STATUS_MAX_ACTIVE.get(booking_status_val, 100)
    if active_booking_count >= booking_cap:
        raise ValueError("equipment_booking active cap reached")

    # Check for conflict: any existing active booking for the same equipment_code
    existing = all_bookings
    has_conflict = any(
        str(row.get("equipment_code") or "").strip().lower() == new_code
        and str(row.get("booking_status") or "").strip().lower() in {"confirmed", "active", "pending"}
        for row in existing
    )

    enriched_payload = dict(payload)
    enriched_payload["conflict_flag"] = "true" if has_conflict else "false"

    if has_conflict:
        raise ValueError("Booking conflict detected for equipment")

    record = create_entity_for_tenant("equipment_bookings", enriched_payload, tenant_id)

    # XXXIV.8: fire booking.created event (fire-and-forget)
    try:
        EventPublisher().publish_event(
            "equipment_booking.booking.created",
            {"tenant_id": tenant_id, "booking_id": str(record.get("id", "")),
             "equipment_code": new_code, "requester_id": requester_id},
        )
    except Exception:  # noqa: BLE001
        pass

    # XXXIV.8: persist action log (fire-and-forget)
    try:
        create_entity_for_tenant(
            "equipment_booking_action_logs",
            {
                "booking_id": str(record.get("id", "")),
                "action_type": "booking_created",
                "requester_id": requester_id,
                "equipment_code": new_code,
                "tenant_id": tenant_id,
            },
            tenant_id,
        )
    except Exception:  # noqa: BLE001
        pass

    return record


def update_equipment_booking_status(booking_id: int, status: str, tenant_id: int) -> dict[str, object]:
    """Update booking status with strict lifecycle transition guard."""
    bookings = list_entities_for_tenant("equipment_bookings", tenant_id)
    existing_record = next((r for r in bookings if int(r.get("id") or 0) == booking_id), None)
    if existing_record is None:
        raise ValueError(f"Equipment booking '{booking_id}' not found")

    current_status = str(existing_record.get("booking_status") or "").strip().lower()
    next_status = status.strip().lower()

    allowed_next = _ALLOWED_BOOKING_STATUS_TRANSITIONS.get(current_status)
    if allowed_next is None:
        raise ValueError(f"Unsupported current booking status '{current_status}'")

    if next_status not in _ALLOWED_BOOKING_STATUS_TRANSITIONS:
        raise ValueError(f"Unsupported target booking status '{next_status}'")

    if next_status != current_status and next_status not in allowed_next:
        raise ValueError(
            f"Invalid equipment booking status transition '{current_status}' -> '{next_status}'"
        )

    record = update_entity_for_tenant("equipment_bookings", booking_id, {"booking_status": next_status}, tenant_id)
    if next_status in _OVERDUE_BOOKING_RISK_STATUSES:
        _ensure_overdue_booking_alert_record(booking_id, tenant_id)

    # XXXIV.8: fire lifecycle events (fire-and-forget)
    _fire_booking_lifecycle_event(record, next_status, tenant_id)

    return record


def _fire_booking_lifecycle_event(
    record: dict[str, object],
    new_status: str,
    tenant_id: int,
) -> None:
    """XXXIV.8: fire confirmed/cancelled/completed/overdue event fire-and-forget."""
    _STATUS_EVENT_MAP = {
        "confirmed": "equipment_booking.booking.confirmed",
        "cancelled": "equipment_booking.booking.cancelled",
        "completed": "equipment_booking.booking.returned",
        "overdue": "equipment_booking.booking.overdue",
    }
    event_type = _STATUS_EVENT_MAP.get(new_status)
    if not event_type:
        return
    try:
        EventPublisher().publish_event(
            event_type,
            {"tenant_id": tenant_id, "booking_id": str(record.get("id", "")),
             "status": new_status},
        )
    except Exception:  # noqa: BLE001
        pass


def _ensure_overdue_booking_alert_record(booking_id: int, tenant_id: int) -> None:
    existing = list_entities_for_tenant("equipment_booking_overdue_alerts", tenant_id)
    already = any(
        r.get("integration_source") == "equipment_booking_overdue_queue"
        and str(r.get("source_entity_id") or "") == str(booking_id)
        for r in existing
    )
    if already:
        return
    alert_payload: dict[str, object] = {
        "booking_id": booking_id,
        "alert_status": "open",
        "integration_source": "equipment_booking_overdue_queue",
        "source_entity_id": str(booking_id),
        "tenant_id": tenant_id,
    }
    create_entity_for_tenant("equipment_booking_overdue_alerts", alert_payload, tenant_id)


def get_equipment_booking_brain_context(tenant_id: int) -> dict[str, object]:
    equipment = list_entities_for_tenant("equipment_items", tenant_id)
    bookings = list_entities_for_tenant("equipment_bookings", tenant_id)

    total_eq = len(equipment)
    available = sum(
        1 for row in equipment if str(row.get("status") or "").strip().lower() == "available"
    )
    total_bookings = len(bookings)
    active_bookings = sum(
        1
        for row in bookings
        if str(row.get("booking_status") or "").strip().lower() in {"confirmed", "active"}
    )
    conflict_bookings = sum(
        1 for row in bookings if bool(row.get("conflict_flag"))
    )

    utilization_rate = round(active_bookings / total_eq, 3) if total_eq > 0 else 0.0

    if conflict_bookings > 0 or utilization_rate >= 0.9:
        availability_status = "constrained"
    elif utilization_rate >= 0.6:
        availability_status = "busy"
    else:
        availability_status = "available"

    return {
        "module": "equipment_booking",
        "tenant_id": tenant_id,
        "total_equipment": total_eq,
        "available_equipment": available,
        "total_bookings": total_bookings,
        "active_bookings": active_bookings,
        "conflict_bookings": conflict_bookings,
        "utilization_rate": utilization_rate,
        "availability_status": availability_status,
    }
