"""Phase VI-VI2: Dining service."""
from __future__ import annotations

from app.platform.events.publisher import EventPublisher
from app.modules.university_core.tenant_entity_service import (
    create_entity_for_tenant,
    list_entities_for_tenant,
)
from app.core.module_helpers.service_validation import DomainValidationError


_MEAL_TYPE_MAX_ACTIVE_MENUS: dict[str, int] = {
    "breakfast": 2,
    "lunch": 3,
    "dinner": 3,
    "late_night": 1,
}
_ACTIVE_MENU_STATUSES = frozenset({"active", "published"})

# ---------------------------------------------------------------------------
# W106: Dining order menu status guard
# An order may only be placed against a menu that exists AND is active/published.
# Orders against closed/archived/draft menus create kitchen requests for
# unavailable items and corrupt Brain Core Dining financial analytics.
# ---------------------------------------------------------------------------
_ORDERABLE_MENU_STATUSES: frozenset[str] = frozenset({"active", "published"})


def _check_menu_is_orderable(
    *,
    tenant_id: int,
    menu_code: str,
) -> None:
    """W106: Cross-entity guard — dining_orders × dining_menus.

    A dining order may only be placed against a menu that exists AND has
    status 'active' or 'published'. Ordering against a closed/archived/draft
    or non-existent menu:
      - Generates kitchen requests for unavailable dishes
      - Creates financial transactions with no corresponding supply
      - Corrupts Brain Core dining revenue and utilisation analytics
      - Leads to unresolved orders and student dissatisfaction

    FAIL-CLOSED: if the menus query fails (any exception), the order is BLOCKED.
    """
    try:
        all_menus = list_entities_for_tenant("dining_menus", tenant_id)
    except Exception as exc:
        raise DomainValidationError(
            f"Dining order blocked for menu_code='{menu_code}': "
            f"menu lookup failed — {exc}. Cannot verify menu availability."
        ) from exc

    matching = [
        row for row in all_menus
        if str(row.get("menu_code") or "").strip().lower() == str(menu_code).strip().lower()
    ]

    if not matching:
        raise DomainValidationError(
            f"Dining order blocked for menu_code='{menu_code}': "
            "menu not found. Orders can only be placed against existing menus."
        )

    menu = matching[0]
    menu_status = str(menu.get("status") or "").strip().lower()
    if menu_status not in _ORDERABLE_MENU_STATUSES:
        raise DomainValidationError(
            f"Dining order blocked for menu_code='{menu_code}': "
            f"menu status is '{menu_status}' — not orderable. "
            f"Only menus with status {sorted(_ORDERABLE_MENU_STATUSES)} accept orders."
        )


# W61: capacity exceeded risk constant
_CAPACITY_EXCEEDED_RISK_STATUSES = frozenset({"capacity_alert"})


def _coerce_capacity_value(value: object) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _ensure_capacity_alert_record(menu: dict[str, object], tenant_id: int) -> None:
    menu_id = str(menu.get("id") or "").strip()
    if not menu_id:
        return

    for row in list_entities_for_tenant("dining_capacity_alert_records", tenant_id):
        if (
            str(row.get("integration_source") or "").strip() == "dining_capacity"
            and str(row.get("source_entity_id") or "").strip() == menu_id
        ):
            return

    create_entity_for_tenant(
        "dining_capacity_alert_records",
        {
            "menu_id": menu_id,
            "menu_code": str(menu.get("menu_code") or "").strip(),
            "facility_code": str(menu.get("facility_code") or "").strip(),
            "meal_type": str(menu.get("meal_type") or "").strip(),
            "alert_level": "high",
            "status": "open",
            "integration_source": "dining_capacity",
            "source_entity_id": menu_id,
        },
        tenant_id,
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
    meal_type = str(payload.get("meal_type") or "").strip().lower()
    status = str(payload.get("status") or "").strip().lower()
    cap = _MEAL_TYPE_MAX_ACTIVE_MENUS.get(meal_type)
    if cap is not None and status in _ACTIVE_MENU_STATUSES:
        active_count = sum(
            1
            for row in list_entities_for_tenant("dining_menus", tenant_id)
            if str(row.get("meal_type") or "").strip().lower() == meal_type
            and str(row.get("status") or "").strip().lower() in _ACTIVE_MENU_STATUSES
        )
        if active_count >= cap:
            raise ValueError(f"meal_type='{meal_type}' active menu cap exceeded; max={cap}")

    record = create_entity_for_tenant("dining_menus", payload, tenant_id)
    available_capacity = _coerce_capacity_value(record.get("available_capacity"))
    if available_capacity is not None and available_capacity <= 0:
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
        _ensure_capacity_alert_record(record, tenant_id)
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
    # W106: Menu status guard — block orders against non-existent / non-orderable menus
    menu_code = str(payload.get("menu_code") or "").strip()
    if menu_code:
        _check_menu_is_orderable(tenant_id=tenant_id, menu_code=menu_code)
    return create_entity_for_tenant("dining_orders", payload, tenant_id)


def get_dining_brain_context(tenant_id: int) -> dict[str, object]:
    menus = list_entities_for_tenant("dining_menus", tenant_id)
    orders = list_entities_for_tenant("dining_orders", tenant_id)

    active_menus = sum(
        1 for m in menus if str(m.get("status") or "").strip().lower() == "active"
    )
    capacity_exceeded_menus = sum(
        1 for m in menus
        if (_coerce_capacity_value(m.get("available_capacity")) or 0) <= 0
        and _coerce_capacity_value(m.get("available_capacity")) is not None
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
