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


_PLATFORM_DEFAULT_TENANT_ID = 1


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
_flags_by_tenant: Dict[int, Dict[str, FeatureFlag]] = {_PLATFORM_DEFAULT_TENANT_ID: _flags}


def _require_tenant_id(tenant_id: int | None, *, operation: str) -> int:
    if tenant_id is None:
        raise ValueError(f"tenant_id is required for {operation}")
    normalized = int(tenant_id)
    if normalized <= 0:
        raise ValueError("tenant_id must be positive")
    return normalized


def _tenant_store(tenant_id: int) -> Dict[str, FeatureFlag]:
    store = _flags_by_tenant.get(tenant_id)
    if store is not None:
        return store

    seeded: Dict[str, FeatureFlag] = {
        key: FeatureFlag(
            key=item.key,
            description=item.description,
            enabled=item.enabled,
            scope=item.scope,
            updated_at=item.updated_at,
        )
        for key, item in _flags.items()
    }
    _flags_by_tenant[tenant_id] = seeded
    return seeded


def list_flags(tenant_id: int | None = None) -> List[dict[str, object]]:
    store = _tenant_store(_require_tenant_id(tenant_id, operation="list_flags"))
    return [
        {
            "key": item.key,
            "description": item.description,
            "enabled": item.enabled,
            "scope": item.scope,
            "updated_at": item.updated_at,
        }
        for item in store.values()
    ]


def set_flag(
    key: str,
    enabled: bool,
    description: str | None = None,
    scope: str = "global",
    tenant_id: int | None = None,
) -> dict[str, object]:
    store = _tenant_store(_require_tenant_id(tenant_id, operation="set_flag"))
    now = datetime.now(timezone.utc).isoformat()
    existing = store.get(key)

    if existing is None:
        created = FeatureFlag(
            key=key,
            description=(description or key).strip(),
            enabled=enabled,
            scope=scope,
            updated_at=now,
        )
        store[key] = created
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
