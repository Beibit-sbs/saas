"""Phase VII-VII2: Equipment booking service."""
from __future__ import annotations

from app.platform.events.publisher import EventPublisher
from app.modules.university_core.tenant_entity_service import (
    create_entity_for_tenant,
    list_entities_for_tenant,
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
    """Create booking, detect conflicts, emit signal if conflict found."""
    # Check for conflict: any existing active booking for the same equipment_code
    existing = list_entities_for_tenant("equipment_bookings", tenant_id)
    new_code = str(payload.get("equipment_code") or "").strip().lower()
    has_conflict = any(
        str(row.get("equipment_code") or "").strip().lower() == new_code
        and str(row.get("booking_status") or "").strip().lower() in {"confirmed", "active", "pending"}
        for row in existing
    )

    enriched_payload = dict(payload)
    enriched_payload["conflict_flag"] = has_conflict

    record = create_entity_for_tenant("equipment_bookings", enriched_payload, tenant_id)

    if has_conflict:
        record_id = str(record.get("id") or "unknown")
        EventPublisher().publish_event(
            tenant_id=tenant_id,
            event_type="research.equipment.booking_conflict_detected",
            aggregate_type="equipment_booking",
            aggregate_id=record_id,
            payload_json={
                "equipment_code": record.get("equipment_code"),
                "requester_id": record.get("requester_id"),
                "start_time": record.get("start_time"),
                "end_time": record.get("end_time"),
                "integration_source": record.get("integration_source"),
                "source_entity_type": "equipment_booking",
                "source_entity_id": record_id,
            },
        )

    return record


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
