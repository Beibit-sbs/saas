from __future__ import annotations

from typing import Any


def fetch_platform_context(*, tenant_id: int, subject: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    """Return platform-level context slice for Brain Core decisions."""
    return {
        "tenant_id": tenant_id,
        "correlation_id": payload.get("correlation_id"),
        "source_module": payload.get("source_module"),
        "source_entity_type": payload.get("source_entity_type"),
        "source_entity_id": payload.get("source_entity_id"),
    }
