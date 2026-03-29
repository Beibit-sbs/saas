"""Tenant context dependency for FastAPI (strict fail-closed).

Resolves tenant context from authenticated claims and optional X-Tenant-ID
override for platform-authorized actors only.
No implicit tenant defaults are allowed.
"""
from __future__ import annotations

from fastapi import Header, HTTPException, Request

from app.modules.auth.token_service import AccessTokenClaims, TokenValidationError, parse_access_token_from_request
from app.modules.observability.security_signals import record_security_signal
from app.modules.observability.perf_profile import perf_segment
from app.modules.rbac.service import is_platform_admin
from app.modules.tenants.service import get_tenant


def _resolve_authenticated_claims(request: Request, authorization: str | None) -> AccessTokenClaims | None:
    try:
        return parse_access_token_from_request(request, authorization)
    except TokenValidationError:
        return None


async def get_current_tenant(
    request: Request,
    authorization: str | None = Header(default=None),
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-ID"),
) -> dict[str, object]:
    """Resolve the current tenant from the X-Tenant-ID header.

    * Explicit header wins only for platform-authorized callers.
    * Authenticated local/ldap sessions inherit tenant_id from token claims.
    * Missing tenant context → 401 (fail-closed).
    * Invalid tenant context → 400/403 (fail-closed).
    * Tenant not found → 404.
    * Tenant status != 'active' → 403.
    """
    with perf_segment("tenant.resolve"):
        claims = _resolve_authenticated_claims(request, authorization)
        if claims is None:
            raise HTTPException(status_code=401, detail="valid authentication is required")

        try:
            authenticated_tenant_id = int(claims.tenant_id)
        except (TypeError, ValueError) as exc:
            raise HTTPException(status_code=403, detail="invalid tenant context in token") from exc
        if authenticated_tenant_id <= 0:
            raise HTTPException(status_code=403, detail="invalid tenant context in token")

        parsed_header_tenant_id: int | None = None
        if x_tenant_id is not None:
            try:
                parsed_header_tenant_id = int(str(x_tenant_id).strip())
            except (TypeError, ValueError) as exc:
                raise HTTPException(status_code=400, detail="invalid tenant header") from exc
            if parsed_header_tenant_id <= 0:
                raise HTTPException(status_code=400, detail="invalid tenant header")

        if parsed_header_tenant_id is not None:
            if (
                authenticated_tenant_id is not None
                and parsed_header_tenant_id != authenticated_tenant_id
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
            tenant_id = parsed_header_tenant_id
        elif authenticated_tenant_id is not None:
            tenant_id = authenticated_tenant_id
        else:
            raise HTTPException(status_code=401, detail="tenant context is required")
        tenant = get_tenant(tenant_id)
        if tenant is None:
            raise HTTPException(status_code=404, detail=f"Tenant {tenant_id} not found")
        if tenant.get("status") != "active":
            raise HTTPException(status_code=403, detail=f"Tenant {tenant_id} is not active")
        return tenant
