"""Tenant context dependency for FastAPI.

Reads the X-Tenant-ID header (falls back to default tenant id=1).
Validates the tenant exists and is active.
Returns tenant dict for use in request handlers.

Tenant filtering in domain modules is NOT enforced here —
this phase only provides the infrastructure.
"""
from __future__ import annotations

from fastapi import Header, HTTPException

from app.modules.tenants.service import get_tenant


_DEFAULT_TENANT_ID = 1


async def get_current_tenant(
    x_tenant_id: int | None = Header(default=None, alias="X-Tenant-ID"),
) -> dict[str, object]:
    """Resolve the current tenant from the X-Tenant-ID header.

    * Missing header → default tenant (id=1).
    * Tenant not found → 404.
    * Tenant status != 'active' → 403.
    """
    tenant_id = x_tenant_id if x_tenant_id is not None else _DEFAULT_TENANT_ID
    tenant = get_tenant(tenant_id)
    if tenant is None:
        raise HTTPException(status_code=404, detail=f"Tenant {tenant_id} not found")
    if tenant.get("status") != "active":
        raise HTTPException(status_code=403, detail=f"Tenant {tenant_id} is not active")
    return tenant
