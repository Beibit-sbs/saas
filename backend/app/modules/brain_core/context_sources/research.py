from __future__ import annotations

from typing import Any

from app.modules.research.service import get_research_health_snapshot


def fetch_research_context(*, tenant_id: int, subject: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    """Return research-related context slice for Brain Core decisions."""
    health_snapshot = get_research_health_snapshot(tenant_id).model_dump()
    return {
        "tenant_id": tenant_id,
        "research_project_id": payload.get("research_project_id"),
        "lab_id": payload.get("lab_id"),
        "lab_code": payload.get("lab_code"),
        "criticality": payload.get("criticality"),
        "health_snapshot": health_snapshot,
    }
