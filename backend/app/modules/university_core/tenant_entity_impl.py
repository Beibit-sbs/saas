"""Tenant-aware implementation layer for university entity CRUD.

This module hosts the concrete tenant-scoped behavior extracted from
`university_core.service` during C-007 phased decomposition.
"""

from app.modules.university_core import service as university_service


def list_entities_for_tenant_impl(entity_name: str, tenant_id: int) -> list[dict[str, object]]:
    """List entities filtered by tenant_id."""
    if entity_name not in university_service.ENTITY_CONFIGS:
        raise ValueError("unknown entity")

    if university_service._use_database():
        try:
            return university_service._list_entities_for_tenant_db(entity_name, tenant_id)
        except Exception as exc:
            if not university_service._should_fallback_to_memory(exc):
                raise

    return university_service._list_entities_for_tenant_memory(entity_name, tenant_id)


def create_entity_for_tenant_impl(
    entity_name: str,
    payload: dict[str, object],
    tenant_id: int,
) -> dict[str, object]:
    """Create entity with tenant_id forced from context (ignores incoming tenant_id)."""
    if entity_name not in university_service.ENTITY_CONFIGS:
        raise ValueError("unknown entity")

    payload_with_tenant: dict[str, object] = {**payload, "tenant_id": str(tenant_id)}
    normalized = university_service._normalize_payload(entity_name, payload_with_tenant)

    if university_service._use_database():
        try:
            return university_service._create_entity_db(entity_name, normalized)
        except Exception as exc:
            if not university_service._should_fallback_to_memory(exc):
                raise

    with university_service._state_lock:
        university_service._validate_foreign_keys_memory(entity_name, normalized)
        university_service._state.counters[entity_name] += 1
        item_id = university_service._state.counters[entity_name]
        row: dict[str, object] = {"id": item_id, **normalized}
        if entity_name == "students":
            row["created_at"] = university_service._now_iso()
        university_service._state.data[entity_name][item_id] = row
        return dict(row)


def update_entity_for_tenant_impl(
    entity_name: str,
    item_id: int,
    payload: dict[str, object],
    tenant_id: int,
) -> dict[str, object]:
    """Update entity, enforcing tenant ownership."""
    if entity_name not in university_service.ENTITY_CONFIGS:
        raise ValueError("unknown entity")

    payload_with_tenant: dict[str, object] = {**payload, "tenant_id": str(tenant_id)}
    normalized = university_service._normalize_payload(entity_name, payload_with_tenant)

    if university_service._use_database():
        try:
            return university_service._update_entity_for_tenant_db(entity_name, item_id, normalized, tenant_id)
        except Exception as exc:
            if not university_service._should_fallback_to_memory(exc):
                raise

    return university_service._update_entity_for_tenant_memory(entity_name, item_id, normalized, tenant_id)


def delete_entity_for_tenant_impl(
    entity_name: str,
    item_id: int,
    tenant_id: int,
) -> dict[str, object]:
    """Delete entity, enforcing tenant ownership."""
    if entity_name not in university_service.ENTITY_CONFIGS:
        raise ValueError("unknown entity")

    if university_service._use_database():
        try:
            return university_service._delete_entity_for_tenant_db(entity_name, item_id, tenant_id)
        except Exception as exc:
            if not university_service._should_fallback_to_memory(exc):
                raise

    return university_service._delete_entity_for_tenant_memory(entity_name, item_id, tenant_id)


__all__ = [
    "list_entities_for_tenant_impl",
    "create_entity_for_tenant_impl",
    "update_entity_for_tenant_impl",
    "delete_entity_for_tenant_impl",
]
