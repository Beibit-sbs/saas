from __future__ import annotations

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


def set_platform_feature(module: str, key: str, enabled: bool) -> dict[str, object]:
    normalized_module = module.strip().lower()
    normalized_key = key.strip().lower()
    with UnitOfWork() as uow:
        row = uow.feature_flag_repository.set_flag(
            scope="platform",
            module=normalized_module,
            key=normalized_key,
            enabled=bool(enabled),
            tenant_id=_PLATFORM_TENANT_ID,
            conn=uow.conn,
        )
    _invalidate_cache(_PLATFORM_TENANT_ID, normalized_module, normalized_key)
    return row


def set_tenant_feature(tenant_id: int, module: str, key: str, enabled: bool) -> dict[str, object]:
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
