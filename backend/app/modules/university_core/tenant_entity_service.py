"""Tenant-aware facade for shared university entity CRUD helpers.

This module keeps domain services decoupled from the monolithic
`university_core.service` during phased decomposition (C-007).
"""

from app.modules.university_core.service import (
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
