"""Phase VI-VI2: Dining service."""
from __future__ import annotations

from app.platform.events.publisher import EventPublisher
from app.modules.university_core.tenant_entity_service import (
    create_entity_for_tenant,
    list_entities_for_tenant,
)


def list_dining_menus(
    tenant_id: int,
    meal_type: str | None = None,
    status: str | None = None,
) -> list[dict[str, object]]:
    rows = list_entities_for_tenant("dining_menus", tenant_id)
    meal_filter = str(meal_type or "").strip().lower()
    status_filter = str(status or "").strip().lower()
    result: list[dict[str, object]] = []
    for row in rows:
        if meal_filter and str(row.get("meal_type") or "").strip().lower() != meal_filter:
            continue
        if status_filter and str(row.get("status") or "").strip().lower() != status_filter:
            continue
        result.append(row)
    return result


def create_dining_menu(payload: dict[str, object], tenant_id: int) -> dict[str, object]:
    record = create_entity_for_tenant("dining_menus", payload, tenant_id)
    available_capacity = record.get("available_capacity")
    if isinstance(available_capacity, int) and available_capacity <= 0:
        record_id = str(record.get("id") or "unknown")
        EventPublisher().publish_event(
            tenant_id=tenant_id,
            event_type="campus.dining.capacity_exceeded",
            aggregate_type="dining_menu",
            aggregate_id=record_id,
            payload_json={
                "menu_code": record.get("menu_code"),
                "facility_code": record.get("facility_code"),
                "meal_type": record.get("meal_type"),
                "capacity": record.get("capacity"),
                "available_capacity": available_capacity,
                "source_entity_type": "dining_menu",
                "source_entity_id": record_id,
            },
        )
    return record


def list_dining_orders(
    tenant_id: int,
    status: str | None = None,
) -> list[dict[str, object]]:
    rows = list_entities_for_tenant("dining_orders", tenant_id)
    status_filter = str(status or "").strip().lower()
    if not status_filter:
        return rows
    return [
        row for row in rows
        if str(row.get("status") or "").strip().lower() == status_filter
    ]


def create_dining_order(payload: dict[str, object], tenant_id: int) -> dict[str, object]:
    return create_entity_for_tenant("dining_orders", payload, tenant_id)


def get_dining_brain_context(tenant_id: int) -> dict[str, object]:
    menus = list_entities_for_tenant("dining_menus", tenant_id)
    orders = list_entities_for_tenant("dining_orders", tenant_id)

    active_menus = sum(
        1 for m in menus if str(m.get("status") or "").strip().lower() == "active"
    )
    capacity_exceeded_menus = sum(
        1 for m in menus
        if isinstance(m.get("available_capacity"), int) and m["available_capacity"] <= 0
    )

    if capacity_exceeded_menus > 0:
        risk_level = "high"
    elif active_menus == 0 and len(menus) > 0:
        risk_level = "medium"
    else:
        risk_level = "low"

    return {
        "module": "dining",
        "tenant_id": tenant_id,
        "total_menus": len(menus),
        "active_menus": active_menus,
        "capacity_exceeded_menus": capacity_exceeded_menus,
        "total_orders": len(orders),
        "risk_level": risk_level,
    }
