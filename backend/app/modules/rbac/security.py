from typing import Annotated

from fastapi import Header, HTTPException, Request

from app.core.config import allow_legacy_header_auth, allow_rbac_dev_fallback
from app.modules.auth.token_service import (
    AccessTokenClaims,
    TokenValidationError,
    parse_access_token_from_request,
)
from app.modules.rbac.service import (
    get_user_roles_db_source,
    resolve_permissions,
    resolve_permissions_db_source,
)


def resolve_current_user_claims(
    request: Request,
    authorization: str | None,
) -> AccessTokenClaims:
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
) -> None:
    fallback_allowed = allow_rbac_dev_fallback()
    claims = getattr(request.state, "auth_claims", None)
    if claims is None:
        claims = resolve_current_user_claims(request, authorization)

    db_source = True
    try:
        role_values = get_user_roles_db_source(claims.user_id)
    except Exception as exc:
        if not fallback_allowed:
            raise HTTPException(status_code=503, detail="rbac database unavailable") from exc
        db_source = False
        role_values = [r.strip() for r in claims.roles if r.strip()]

    # Legacy headers are ignored in operational mode and never treated as source
    # of truth. In compatibility mode they can only narrow access, never escalate.
    if allow_legacy_header_auth() and x_admin_user and x_admin_user != claims.user_id:
        raise HTTPException(status_code=401, detail="header actor mismatch with token")
    if allow_legacy_header_auth() and x_user_roles:
        requested = {r.strip() for r in x_user_roles.split(",") if r.strip()}
        if requested:
            role_values = [r for r in role_values if r in requested]

    if "superadmin" in role_values:
        return

    if db_source:
        try:
            granted = resolve_permissions_db_source(role_values)
        except Exception as exc:
            if not fallback_allowed:
                raise HTTPException(status_code=503, detail="rbac database unavailable") from exc
            granted = resolve_permissions(role_values)
    else:
        granted = resolve_permissions(role_values)

    if permission not in granted:
        raise HTTPException(status_code=403, detail=f"missing permission: {permission}")


def permission_dependency(permission: str):
    async def dependency(
        request: Request,
        authorization: Annotated[str | None, Header()] = None,
        x_user_roles: Annotated[str | None, Header()] = None,
        x_admin_user: Annotated[str | None, Header()] = None,
    ) -> None:
        await require_permission(request, permission, authorization, x_user_roles, x_admin_user)

    return dependency
