from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, List


@dataclass
class FeatureFlag:
    key: str
    description: str
    enabled: bool
    scope: str
    updated_at: str


# Scaffold-only in-memory store.
# This module is intentionally not wired into runtime until rollout phase.
_flags: Dict[str, FeatureFlag] = {
    "admin.local_users.tab": FeatureFlag(
        key="admin.local_users.tab",
        description="Show local users tab in admin panel",
        enabled=True,
        scope="global",
        updated_at=datetime.now(timezone.utc).isoformat(),
    )
}


def list_flags() -> List[dict[str, object]]:
    return [
        {
            "key": item.key,
            "description": item.description,
            "enabled": item.enabled,
            "scope": item.scope,
            "updated_at": item.updated_at,
        }
        for item in _flags.values()
    ]


def set_flag(key: str, enabled: bool, description: str | None = None, scope: str = "global") -> dict[str, object]:
    now = datetime.now(timezone.utc).isoformat()
    existing = _flags.get(key)

    if existing is None:
        created = FeatureFlag(
            key=key,
            description=(description or key).strip(),
            enabled=enabled,
            scope=scope,
            updated_at=now,
        )
        _flags[key] = created
        existing = created
    else:
        existing.enabled = enabled
        existing.scope = scope
        existing.updated_at = now
        if description is not None and description.strip():
            existing.description = description.strip()

    return {
        "key": existing.key,
        "description": existing.description,
        "enabled": existing.enabled,
        "scope": existing.scope,
        "updated_at": existing.updated_at,
    }
