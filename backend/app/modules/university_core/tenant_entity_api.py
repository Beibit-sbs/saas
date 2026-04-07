"""Public tenant-aware CRUD API for university entities.

This layer stabilizes import boundaries for domain modules during
the phased decomposition of university_core.service (C-007).
"""

from typing import Any

from app.modules.university_core.tenant_entity_impl import (
    create_entity_for_tenant_impl,
    delete_entity_for_tenant_impl,
    list_entities_for_tenant_impl,
    update_entity_for_tenant_impl,
)


def list_entities_for_tenant(entity_name: str, tenant_id: int) -> list[dict[str, object]]:
    return list_entities_for_tenant_impl(entity_name, tenant_id)


def create_entity_for_tenant(
    entity_name: str,
    payload: dict[str, Any],
    tenant_id: int,
) -> dict[str, object]:
    return create_entity_for_tenant_impl(entity_name, payload, tenant_id)


def update_entity_for_tenant(
    entity_name: str,
    item_id: int,
    payload: dict[str, Any],
    tenant_id: int,
) -> dict[str, object]:
    return update_entity_for_tenant_impl(entity_name, item_id, payload, tenant_id)


def delete_entity_for_tenant(
    entity_name: str,
    item_id: int,
    tenant_id: int,
) -> dict[str, object]:
    return delete_entity_for_tenant_impl(entity_name, item_id, tenant_id)


__all__ = [
    "list_entities_for_tenant",
    "create_entity_for_tenant",
    "update_entity_for_tenant",
    "delete_entity_for_tenant",
]
