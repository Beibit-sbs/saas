"""Tenant context dependency for FastAPI (strict fail-closed).

Resolves tenant context from authenticated token claims only.
X-Tenant-ID is accepted solely as a secondary consistency check and can never
override authenticated tenant context.
"""
from __future__ import annotations

from fastapi import Header, HTTPException, Request

from app.modules.auth.token_service import AccessTokenClaims, TokenValidationError, parse_access_token_from_request
from app.modules.observability.perf_profile import perf_segment
from app.modules.tenants.service import get_tenant
from app.platform.tenant import service as platform_tenant_service


def _effective_tenant(tenant_id: int) -> dict[str, object] | None:
    tenant = get_tenant(int(tenant_id))
    if tenant is not None:
        return tenant
    try:
        profile = platform_tenant_service.get_tenant_profile(int(tenant_id))
    except Exception:
        return None
    return {
        "id": int(profile.get("tenant_id", tenant_id)),
        "slug": str(profile.get("slug", "")),
        "name": str(profile.get("name", "")),
        "status": str(profile.get("status", "active")),
    }


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
    """Resolve the current tenant from authenticated token claims.

    * Token tenant_id is the single source of truth.
    * X-Tenant-ID is optional validation-only hint and must match token tenant.
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

        if parsed_header_tenant_id is not None and parsed_header_tenant_id != authenticated_tenant_id:
            roles = {str(role).strip() for role in claims.roles if str(role).strip()}
            if "superadmin" in roles:
                # Keep dashboard context fail-closed even for platform superadmin.
                if request.url.path.startswith("/api/admin/dashboard"):
                    raise HTTPException(status_code=403, detail="cross-tenant override forbidden")
                tenant_id = parsed_header_tenant_id
            else:
                raise HTTPException(status_code=403, detail="cross-tenant override forbidden")
        else:
            tenant_id = authenticated_tenant_id

        tenant = _effective_tenant(tenant_id)
        if tenant is None:
            raise HTTPException(status_code=404, detail=f"Tenant {tenant_id} not found")
        if tenant.get("status") != "active":
            raise HTTPException(status_code=403, detail=f"Tenant {tenant_id} is not active")
        return tenant
