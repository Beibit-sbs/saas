"""
Feature flags — thin delegation bridge.

All state is persisted in app_platform_feature_flags via Alembic migrations.
This module provides the legacy flat API (`list_flags`, `is_flag_enabled`,
`set_flag`) used by modules-layer callers; it delegates every operation to
the DB-backed `app.platform.feature_flags.service`.
"""
from __future__ import annotations

from typing import List

from app.platform.feature_flags import service as _platform_service


def _split_composite_key(composite_key: str) -> tuple[str, str]:
    """Split 'module.rest.of.key' into (module, rest.of.key).

    Falls back to ('global', composite_key) for un-dotted keys.
    """
    parts = composite_key.split(".", 1)
    if len(parts) == 2 and parts[0] and parts[1]:
        return parts[0].strip().lower(), parts[1].strip().lower()
    return "global", composite_key.lower()


def _to_legacy_dict(row: dict[str, object]) -> dict[str, object]:
    module = str(row.get("module", ""))
    key = str(row.get("key", ""))
    composite = f"{module}.{key}" if module and module not in ("", "global") else key
    return {
        "key": composite,
        "description": str(row.get("description", "")),
        "enabled": bool(row.get("enabled", False)),
        "scope": str(row.get("scope", "tenant")),
        "updated_at": str(row.get("updated_at", "")),
    }


def list_flags(tenant_id: int | None = None) -> List[dict[str, object]]:
    """Return feature flags for the given tenant in legacy composite-key format."""
    if tenant_id is None:
        raise ValueError("tenant_id is required for list_flags")
    normalized = int(tenant_id)
    if normalized <= 0:
        raise ValueError("tenant_id must be positive")
    try:
        rows = _platform_service.list_tenant_features(normalized)
    except Exception:
        return []
    return [_to_legacy_dict(row) for row in rows]


def is_flag_enabled(
    key: str,
    *,
    tenant_id: int | None = None,
    default: bool = False,
) -> bool:
    """Check if a feature flag is enabled for a tenant.

    Delegates to the DB-backed platform service (no actor bucketing —
    returns enabled state as stored in DB).
    """
    normalized_key = str(key or "").strip()
    if not normalized_key:
        return bool(default)
    if tenant_id is None:
        return bool(default)
    normalized_tenant = int(tenant_id)
    if normalized_tenant <= 0:
        return bool(default)

    module, flag_key = _split_composite_key(normalized_key)
    try:
        rows = _platform_service.list_tenant_features(normalized_tenant)
    except Exception:
        return bool(default)

    for row in rows:
        if (
            str(row.get("module", "")).lower() == module
            and str(row.get("key", "")).lower() == flag_key
        ):
            return bool(row.get("enabled", default))
    return bool(default)


def set_flag(
    key: str,
    enabled: bool,
    description: str | None = None,
    scope: str = "global",
    tenant_id: int | None = None,
) -> dict[str, object]:
    """Upsert a feature flag; delegates to the DB-backed platform service."""
    if tenant_id is None:
        raise ValueError("tenant_id is required for set_flag")
    normalized_tenant = int(tenant_id)
    if normalized_tenant <= 0:
        raise ValueError("tenant_id must be positive")
    module, flag_key = _split_composite_key(str(key).strip())
    row = _platform_service.set_tenant_feature(
        normalized_tenant, module, flag_key, bool(enabled)
    )
    return _to_legacy_dict(row)
