from __future__ import annotations

from typing import Any


def fetch_faculty_context(*, tenant_id: int, subject: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    """Return faculty context slice for Brain Core decisions."""
    return {
        "faculty_id": subject.get("faculty_id") or payload.get("faculty_id"),
        "workload_ratio": payload.get("workload_ratio"),
        "tenant_id": tenant_id,
    }
