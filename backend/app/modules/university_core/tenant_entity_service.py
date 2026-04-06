"""Tenant-aware facade for shared university entity CRUD helpers."""

from app.modules.university_core.tenant_entity_api import (
    create_entity_for_tenant,
    delete_entity_for_tenant,
    list_entities_for_tenant,
    update_entity_for_tenant,
)

__all__ = [
    "list_entities_for_tenant",
    "create_entity_for_tenant",
    "update_entity_for_tenant",
    "delete_entity_for_tenant",
]
