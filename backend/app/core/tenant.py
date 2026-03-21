"""Tenant context dependency for FastAPI.

Resolves tenant context from X-Tenant-ID when explicitly provided.
Otherwise, authenticated requests inherit tenant_id from access-token claims.
Unauthenticated requests fall back to the default tenant id=1.
"""
from __future__ import annotations

from fastapi import Header, HTTPException, Request

from app.modules.auth.token_service import AccessTokenClaims, TokenValidationError, parse_access_token_from_request
from app.modules.observability.security_signals import record_security_signal
from app.modules.rbac.service import is_platform_admin
from app.modules.tenants.service import get_tenant


_DEFAULT_TENANT_ID = 1


def _resolve_authenticated_claims(request: Request, authorization: str | None) -> AccessTokenClaims | None:
    try:
        return parse_access_token_from_request(request, authorization)
    except TokenValidationError:
        return None


async def get_current_tenant(
    request: Request,
    authorization: str | None = Header(default=None),
    x_tenant_id: int | None = Header(default=None, alias="X-Tenant-ID"),
) -> dict[str, object]:
    """Resolve the current tenant from the X-Tenant-ID header.

    * Explicit header wins for platform-global/test callers.
    * Authenticated local/ldap sessions inherit tenant_id from token claims.
    * Missing tenant context → default tenant (id=1).
    * Tenant not found → 404.
    * Tenant status != 'active' → 403.
    """
    claims = _resolve_authenticated_claims(request, authorization)
    authenticated_tenant_id = int(claims.tenant_id) if claims is not None else None
    if x_tenant_id is not None:
        if (
            authenticated_tenant_id is not None
            and x_tenant_id != authenticated_tenant_id
        ):
            claim_roles = {r.strip() for r in getattr(claims, "roles", []) if str(r).strip()}
            actor = str(getattr(claims, "user_id", ""))
            # Cross-tenant override is reserved for platform authority only,
            # independent of authentication source.
            if "superadmin" not in claim_roles and not is_platform_admin(actor):
                record_security_signal(
                    signal="tenant.override.denied",
                    outcome="denied",
                    actor=actor,
                    client_ip=request.client.host if request.client else "unknown",
                    path=request.url.path,
                    tenant_id=authenticated_tenant_id,
                )
                raise HTTPException(status_code=403, detail="cross-tenant override forbidden")
        tenant_id = x_tenant_id
    elif authenticated_tenant_id is not None:
        tenant_id = authenticated_tenant_id
    else:
        tenant_id = _DEFAULT_TENANT_ID
    tenant = get_tenant(tenant_id)
    if tenant is None:
        raise HTTPException(status_code=404, detail=f"Tenant {tenant_id} not found")
    if tenant.get("status") != "active":
        raise HTTPException(status_code=403, detail=f"Tenant {tenant_id} is not active")
    return tenant
