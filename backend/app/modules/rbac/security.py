import logging
import time
from typing import Annotated

from fastapi import Header, HTTPException, Request

from app.core.config import allow_legacy_header_auth, allow_rbac_dev_fallback
from app.core.dependency_logging import log_dependency_unavailable
from app.modules.audit.service import log_admin_action
from app.modules.auth.token_service import (
    AccessTokenClaims,
    TokenValidationError,
    parse_access_token_from_request,
)
from app.modules.observability.perf_profile import perf_segment
from app.modules.observability.security_signals import record_security_signal
from app.modules.rbac.service import (
    get_user_roles_for_tenant,
    get_user_roles_for_tenant_db_source,
    is_platform_admin,
    resolve_permissions,
    resolve_permissions_for_tenant,
    resolve_permissions_for_tenant_db_source,
)
from app.modules.tenants.service import get_tenant
from app.platform.tenant import service as platform_tenant_service

_logger = logging.getLogger(__name__)


def _get_effective_tenant(tenant_id: int) -> dict[str, object] | None:
    tenant = get_tenant(int(tenant_id))
    if tenant is not None:
        return tenant
    try:
        profile = platform_tenant_service.get_tenant_profile(int(tenant_id))
    except Exception as exc:
        _logger.warning(
            "tenant_lookup_failed: returning None (fail-closed downstream)",
            extra={"tenant_id": tenant_id, "error": str(exc)},
        )
        return None
    return {
        "id": int(profile.get("tenant_id", tenant_id)),
        "slug": str(profile.get("slug", "")),
        "name": str(profile.get("name", "")),
        "status": str(profile.get("status", "active")),
    }


def _resolve_tenant_id(request: Request, claims: AccessTokenClaims, x_tenant_id: int | None) -> int:
    if claims.tenant_id <= 0:
        raise HTTPException(status_code=403, detail="invalid tenant context in token")

    if x_tenant_id is not None:
        if int(x_tenant_id) <= 0:
            raise HTTPException(status_code=400, detail="invalid tenant header")
        if x_tenant_id != claims.tenant_id:
            normalized_roles = {r.strip() for r in claims.roles if r.strip()}
            can_cross_tenant_override = "superadmin" in normalized_roles or is_platform_admin(claims.user_id)
            # Keep RBAC administration fail-closed: platform admins must not mutate
            # or inspect another tenant's RBAC state via header override.
            if request.url.path.startswith("/api/admin/rbac"):
                can_cross_tenant_override = False
            if can_cross_tenant_override:
                tenant_id = int(x_tenant_id)
            else:
                record_security_signal(
                    signal="tenant.override.denied",
                    outcome="denied",
                    actor=claims.user_id,
                    client_ip=request.client.host if request.client else "unknown",
                    path=request.url.path,
                    tenant_id=claims.tenant_id,
                )
                log_admin_action(
                    actor=claims.user_id,
                    tenant_id=claims.tenant_id,
                    action="security.cross_tenant.denied",
                    path=str(request.url.path),
                    client_ip=request.client.host if request.client else "unknown",
                    correlation_id=getattr(request.state, "request_id", None),
                    entity="security",
                    result="denied",
                    metadata={"header_tenant_id": int(x_tenant_id), "token_tenant_id": int(claims.tenant_id)},
                )
                raise HTTPException(status_code=403, detail="cross-tenant override forbidden")
        else:
            tenant_id = int(claims.tenant_id)
    else:
        tenant_id = claims.tenant_id
    tenant = _get_effective_tenant(int(tenant_id))
    if tenant is None:
        raise HTTPException(status_code=404, detail=f"Tenant {tenant_id} not found")
    if tenant.get("status") != "active":
        raise HTTPException(status_code=403, detail=f"Tenant {tenant_id} is not active")
    return int(tenant_id)


def resolve_current_user_claims(
    request: Request,
    authorization: str | None,
) -> AccessTokenClaims:
    with perf_segment("auth.resolve_claims"):
        try:
            claims = parse_access_token_from_request(request, authorization)
        except TokenValidationError as exc:
            raise HTTPException(status_code=401, detail=str(exc)) from exc

        if claims is None:
            raise HTTPException(status_code=401, detail="valid authentication is required")

        request.state.auth_claims = claims
        return claims


async def get_actor(
    request: Request,
    authorization: Annotated[str | None, Header()] = None,
    x_admin_user: Annotated[str | None, Header()] = None,
) -> str:
    claims = resolve_current_user_claims(request, authorization)
    if x_admin_user and x_admin_user != claims.user_id:
        raise HTTPException(status_code=401, detail="header actor mismatch with token")

    if allow_legacy_header_auth() and x_admin_user:
        return x_admin_user

    return claims.user_id


async def require_permission(
    request: Request,
    permission: str,
    authorization: Annotated[str | None, Header()] = None,
    x_user_roles: Annotated[str | None, Header()] = None,
    x_admin_user: Annotated[str | None, Header()] = None,
    x_tenant_id: Annotated[int | None, Header(alias="X-Tenant-ID")] = None,
) -> None:
    with perf_segment("rbac.require_permission"):
        started = time.perf_counter()
        fallback_allowed = allow_rbac_dev_fallback()
        claims = getattr(request.state, "auth_claims", None)
        if claims is None:
            claims = resolve_current_user_claims(request, authorization)

        tenant_id = _resolve_tenant_id(request, claims, x_tenant_id)
        if claims.token_type == "service":
            granted_scopes = {item.strip() for item in getattr(claims, "permissions", []) if item.strip()}
            if permission not in granted_scopes:
                log_admin_action(
                    actor=claims.user_id,
                    tenant_id=tenant_id,
                    action="security.access.denied",
                    path=str(request.url.path),
                    client_ip=request.client.host if request.client else "unknown",
                    correlation_id=getattr(request.state, "request_id", None),
                    entity="security",
                    result="denied",
                    metadata={"permission": permission, "token_type": "service"},
                )
                raise HTTPException(status_code=403, detail=f"missing permission: {permission}")
            return

        # Prefer signed token scopes for same-tenant user requests to keep RBAC
        # checks available even during temporary DB pressure.
        if int(tenant_id) == int(claims.tenant_id):
            granted_scopes = {item.strip() for item in getattr(claims, "permissions", []) if item.strip()}
            if granted_scopes:
                if permission not in granted_scopes:
                    log_admin_action(
                        actor=claims.user_id,
                        tenant_id=tenant_id,
                        action="security.access.denied",
                        path=str(request.url.path),
                        client_ip=request.client.host if request.client else "unknown",
                        correlation_id=getattr(request.state, "request_id", None),
                        entity="security",
                        result="denied",
                        metadata={"permission": permission, "token_type": claims.token_type},
                    )
                    raise HTTPException(status_code=403, detail=f"missing permission: {permission}")
                return

        db_source = True
        claims_fallback_used = False
        try:
            role_values = get_user_roles_for_tenant_db_source(claims.user_id, tenant_id)
        except Exception as exc:
            if not fallback_allowed:
                log_dependency_unavailable(
                    request,
                    dependency="rbac.roles",
                    reason=str(exc),
                    started_at=started,
                )
                raise HTTPException(status_code=503, detail="rbac database unavailable") from exc
            db_source = False
            role_values = get_user_roles_for_tenant(claims.user_id, tenant_id)
            if not role_values:
                role_values = [r.strip() for r in claims.roles if r.strip()]
                claims_fallback_used = True

        # Legacy headers are ignored in operational mode and never treated as source
        # of truth. In compatibility mode they can only narrow access, never escalate.
        if allow_legacy_header_auth() and x_admin_user and x_admin_user != claims.user_id:
            raise HTTPException(status_code=401, detail="header actor mismatch with token")
        if allow_legacy_header_auth() and x_user_roles:
            requested = {r.strip() for r in x_user_roles.split(",") if r.strip()}
            if requested:
                role_values = [r for r in role_values if r in requested]

        if "superadmin" in role_values or is_platform_admin(claims.user_id):
            return

        if db_source:
            try:
                granted = resolve_permissions_for_tenant_db_source(role_values, tenant_id)
            except Exception as exc:
                if not fallback_allowed:
                    log_dependency_unavailable(
                        request,
                        dependency="rbac.permissions",
                        reason=str(exc),
                        started_at=started,
                    )
                    raise HTTPException(status_code=503, detail="rbac database unavailable") from exc
                granted = resolve_permissions(role_values) if claims_fallback_used else resolve_permissions_for_tenant(role_values, tenant_id)
        else:
            granted = resolve_permissions(role_values) if claims_fallback_used else resolve_permissions_for_tenant(role_values, tenant_id)

        if permission not in granted:
            log_admin_action(
                actor=claims.user_id,
                tenant_id=tenant_id,
                action="security.access.denied",
                path=str(request.url.path),
                client_ip=request.client.host if request.client else "unknown",
                correlation_id=getattr(request.state, "request_id", None),
                entity="security",
                result="denied",
                metadata={"permission": permission, "token_type": claims.token_type},
            )
            raise HTTPException(status_code=403, detail=f"missing permission: {permission}")


def permission_dependency(permission: str):
    async def dependency(
        request: Request,
        authorization: Annotated[str | None, Header()] = None,
        x_user_roles: Annotated[str | None, Header()] = None,
        x_admin_user: Annotated[str | None, Header()] = None,
        x_tenant_id: Annotated[int | None, Header(alias="X-Tenant-ID")] = None,
    ) -> None:
        await require_permission(
            request,
            permission,
            authorization,
            x_user_roles,
            x_admin_user,
            x_tenant_id,
        )

    return dependency
