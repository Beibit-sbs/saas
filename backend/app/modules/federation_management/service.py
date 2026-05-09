"""A-023.3 — Federation Management service skeleton (L2).

Tracks tenant-scoped identity provider metadata and mapping policies only.
"""
from __future__ import annotations

from app.modules.university_core.tenant_entity_api import (
    create_entity_for_tenant,
    list_entities_for_tenant,
)


FEDERATION_STATES: frozenset[str] = frozenset({"DRAFT", "ACTIVE", "RETIRED"})


def _validate_tenant(tenant_id: int) -> None:
    if not tenant_id or tenant_id <= 0:
        raise ValueError("tenant_id must be a positive integer")


def register_identity_provider(
    tenant_id: int,
    *,
    provider_name: str,
    protocol: str,
    metadata_url: str,
) -> dict:
    """Register identity provider metadata in DRAFT state."""
    _validate_tenant(tenant_id)
    if not provider_name:
        raise ValueError("provider_name is required")
    if not protocol:
        raise ValueError("protocol is required")
    if not metadata_url:
        raise ValueError("metadata_url is required")

    row = create_entity_for_tenant(
        tenant_id,
        "federation_identity_providers",
        {
            "provider_name": provider_name,
            "protocol": protocol,
            "metadata_url": metadata_url,
            "status": "DRAFT",
            "tenant_id": tenant_id,
        },
    )
    return {"provider_id": row["id"], "status": "DRAFT"}


def set_provider_status(
    tenant_id: int,
    *,
    provider_id: str,
    status: str,
) -> dict:
    """Set provider status with explicit operator intent only."""
    _validate_tenant(tenant_id)
    if status not in FEDERATION_STATES:
        raise ValueError(f"status must be one of {sorted(FEDERATION_STATES)}")

    for row in list_entities_for_tenant(tenant_id, "federation_identity_providers"):
        if row.get("id") == provider_id:
            row["status"] = status
            return {"provider_id": provider_id, "status": status}

    raise ValueError(f"Provider {provider_id!r} not found for tenant {tenant_id}")


def list_identity_providers(
    tenant_id: int,
    *,
    status: str | None = None,
) -> list[dict]:
    """List tenant-scoped identity providers with optional status filter."""
    _validate_tenant(tenant_id)
    rows = list_entities_for_tenant(tenant_id, "federation_identity_providers")
    if status:
        rows = [row for row in rows if row.get("status") == status]
    return rows
