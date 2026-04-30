from __future__ import annotations

import hashlib
from threading import Lock

from app.platform.uow import UnitOfWork

_cache_lock = Lock()
_flag_cache: dict[tuple[int, str, str], dict[str, object]] = {}
_tenant_list_cache: dict[int, list[dict[str, object]]] = {}

_PLATFORM_TENANT_ID = 1


def _invalidate_cache(tenant_id: int, module: str, key: str) -> None:
    with _cache_lock:
        _flag_cache.pop((tenant_id, module, key), None)
        _tenant_list_cache.pop(int(tenant_id), None)


def clear_feature_flag_cache() -> None:
    with _cache_lock:
        _flag_cache.clear()
        _tenant_list_cache.clear()


def set_platform_feature(module: str, key: str, enabled: bool, rollout_percentage: int = 100) -> dict[str, object]:
    normalized_module = module.strip().lower()
    normalized_key = key.strip().lower()
    with UnitOfWork() as uow:
        row = uow.feature_flag_repository.set_flag(
            scope="platform",
            module=normalized_module,
            key=normalized_key,
            enabled=bool(enabled),
            tenant_id=_PLATFORM_TENANT_ID,
            rollout_percentage=rollout_percentage,
            conn=uow.conn,
        )
    _invalidate_cache(_PLATFORM_TENANT_ID, normalized_module, normalized_key)
    return row


def set_tenant_feature(tenant_id: int, module: str, key: str, enabled: bool, rollout_percentage: int = 100) -> dict[str, object]:
    normalized_tenant_id = int(tenant_id)
    normalized_module = module.strip().lower()
    normalized_key = key.strip().lower()
    with UnitOfWork() as uow:
        row = uow.feature_flag_repository.set_flag(
            scope="tenant",
            module=normalized_module,
            key=normalized_key,
            enabled=bool(enabled),
            tenant_id=normalized_tenant_id,
            rollout_percentage=rollout_percentage,
            conn=uow.conn,
        )
    _invalidate_cache(normalized_tenant_id, normalized_module, normalized_key)
    return row


def list_tenant_features(tenant_id: int) -> list[dict[str, object]]:
    normalized_tenant_id = int(tenant_id)
    with _cache_lock:
        cached = _tenant_list_cache.get(normalized_tenant_id)
        if cached is not None:
            return [dict(item) for item in cached]

    with UnitOfWork() as uow:
        rows = uow.feature_flag_repository.list_tenant_flags(normalized_tenant_id, conn=uow.conn)

    with _cache_lock:
        _tenant_list_cache[normalized_tenant_id] = [dict(item) for item in rows]
        for item in rows:
            cache_tenant_id = int(item["tenant_id"])
            cache_key = (cache_tenant_id, str(item["module"]), str(item["key"]))
            _flag_cache[cache_key] = dict(item)

    return rows


def is_flag_enabled_for_actor(module: str, key: str, actor_id: str, *, tenant_id: int) -> bool:
    """Evaluate a feature flag for a specific actor, respecting rollout_percentage.

    Uses a deterministic hash so the same actor always gets the same result for a given flag.
    """
    normalized_tenant_id = int(tenant_id)
    normalized_module = module.strip().lower()
    normalized_key = key.strip().lower()

    with _cache_lock:
        cached = _flag_cache.get((normalized_tenant_id, normalized_module, normalized_key))

    if cached is None:
        # Populate cache via list
        list_tenant_features(normalized_tenant_id)
        with _cache_lock:
            cached = _flag_cache.get((normalized_tenant_id, normalized_module, normalized_key))

    if cached is None or not cached.get("enabled"):
        return False

    rollout_pct = int(cached.get("rollout_percentage", 100))
    if rollout_pct >= 100:
        return True
    if rollout_pct <= 0:
        return False

    # Hash actor_id + module + key for deterministic bucketing
    digest = hashlib.sha256(f"{actor_id}:{normalized_module}:{normalized_key}".encode()).digest()
    bucket = int.from_bytes(digest[:4], "big") % 100
    return bucket < rollout_pct


def get_tenant_feature(tenant_id: int, module: str, key: str) -> dict[str, object] | None:
    """Return a single feature flag for a tenant, or None if not found."""
    normalized_tenant_id = int(tenant_id)
    normalized_module = module.strip().lower()
    normalized_key = key.strip().lower()
    with UnitOfWork() as uow:
        return uow.feature_flag_repository.get_flag(normalized_tenant_id, normalized_module, normalized_key, conn=uow.conn)


def delete_tenant_feature(tenant_id: int, module: str, key: str) -> bool:
    """Delete a feature flag for a tenant. Returns True if deleted, False if not found."""
    normalized_tenant_id = int(tenant_id)
    normalized_module = module.strip().lower()
    normalized_key = key.strip().lower()
    with UnitOfWork() as uow:
        deleted = uow.feature_flag_repository.delete_flag(normalized_tenant_id, normalized_module, normalized_key, conn=uow.conn)
    if deleted:
        _invalidate_cache(normalized_tenant_id, normalized_module, normalized_key)
    return deleted

