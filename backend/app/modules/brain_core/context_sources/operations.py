from __future__ import annotations

from typing import Any

from app.modules.operations.service import get_operations_health_snapshot


def fetch_operations_context(*, tenant_id: int, subject: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    """Return operations context slice for Brain Core decisions."""
    return {
        "source_entity_id": payload.get("source_entity_id"),
        "criticality": payload.get("criticality"),
        "facility_code": payload.get("facility_code"),
        "room_code": payload.get("room_code"),
        "health_snapshot": get_operations_health_snapshot(tenant_id).model_dump(),
        "tenant_id": tenant_id,
    }
