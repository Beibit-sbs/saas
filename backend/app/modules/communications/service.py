"""Phase VIII-1: Communications service."""
from __future__ import annotations

from app.modules.university_core.tenant_entity_service import (
    create_entity_for_tenant,
    list_entities_for_tenant,
)


def list_messages(
    tenant_id: int,
    message_type: str | None = None,
    status: str | None = None,
) -> list[dict[str, object]]:
    rows = list_entities_for_tenant("communication_messages", tenant_id)
    type_filter = str(message_type or "").strip().lower()
    status_filter = str(status or "").strip().lower()

    result: list[dict[str, object]] = []
    for row in rows:
        if type_filter and str(row.get("message_type") or "").strip().lower() != type_filter:
            continue
        if status_filter and str(row.get("status") or "").strip().lower() != status_filter:
            continue
        result.append(row)
    return result


def create_message(payload: dict[str, object], tenant_id: int) -> dict[str, object]:
    return create_entity_for_tenant("communication_messages", payload, tenant_id)


def get_communications_brain_context(tenant_id: int) -> dict[str, object]:
    messages = list_entities_for_tenant("communication_messages", tenant_id)

    total_messages = len(messages)
    sent_messages = sum(
        1 for r in messages if str(r.get("status") or "").strip().lower() in {"sent", "delivered"}
    )

    total_recipients = sum(int(r.get("recipients_count") or 0) for r in messages)
    total_delivered = sum(int(r.get("delivered_count") or 0) for r in messages)
    total_opened = sum(int(r.get("opened_count") or 0) for r in messages)

    delivery_rate = round(total_delivered / total_recipients, 4) if total_recipients > 0 else 0.0
    open_rate = round(total_opened / total_delivered, 4) if total_delivered > 0 else 0.0

    if delivery_rate < 0.5:
        delivery_health = "poor"
    elif delivery_rate < 0.8:
        delivery_health = "fair"
    else:
        delivery_health = "good"

    return {
        "module": "communications",
        "tenant_id": tenant_id,
        "total_messages": total_messages,
        "sent_messages": sent_messages,
        "delivery_rate": delivery_rate,
        "open_rate": open_rate,
        "delivery_health": delivery_health,
    }
