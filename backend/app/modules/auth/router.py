from typing import Annotated
import logging
import secrets

from fastapi import APIRouter, Depends, Header, HTTPException, Request, Response
from pydantic import BaseModel

from app.core.config import (
    allow_legacy_header_auth,
    get_auth_cookie_name,
    get_auth_csrf_cookie_name,
    get_auth_csrf_cookie_same_site,
    get_auth_cookie_same_site,
    get_auth_refresh_cookie_name,
    get_auth_modes,
)
from app.core.errors import DependencyUnavailableError, RevocationStoreUnavailable
from app.core.tenant import get_current_tenant
from app.modules.audit.service import log_admin_action
from app.modules.observability.security_signals import record_security_signal
from app.modules.ldap.service import authenticate_ldap_user
from app.modules.auth.local_users_service import local_user_store
from app.modules.auth.mfa_service import disable_mfa, enable_mfa, initiate_mfa_enrollment, is_mfa_enabled, verify_mfa
from app.modules.auth.preferences_service import get_user_language, set_user_language
from app.modules.auth.session_service import (
    create_session,
    list_sessions_for_user,
    revoke_all_sessions_for_user,
    revoke_session,
)
from app.modules.auth.token_service import (
    create_access_token,
    create_refresh_token,
    parse_access_token_from_cookie,
    parse_refresh_token_from_cookie,
    revoke_token,
    verify_refresh_token,
)
from app.modules.identity.service import (
    consume_oidc_state,
    create_oidc_login_challenge,
    exchange_oidc_code_for_identity,
    get_provider,
)
from app.modules.identity.phase1_service import authenticate_tenant_login
from app.modules.identity.identity_errors import IdentityError
from app.modules.i18n.service import list_languages, normalize_code
from app.modules.observability.metrics import observe_auth_login_attempt
from app.modules.rbac.service import (
    resolve_permissions_for_tenant,
    sync_user_roles_from_trusted_source,
)
from app.modules.rbac.security import resolve_current_user_claims
from app.modules.security.rate_limit import clear_auth_failures, get_auth_lockout_decision, record_auth_failure
from app.modules.tenants.service import get_tenant

router = APIRouter(prefix="/api/auth", tags=["auth"])
identity_logger = logging.getLogger("app.identity.events")


def _require_tenant_id(value: int | str | None, *, operation: str) -> int:
    if value is None:
        raise HTTPException(status_code=400, detail=f"tenant_id is required for {operation}")
    try:
        tenant_id = int(value)
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=f"tenant_id is required for {operation}") from exc
    if tenant_id <= 0:
        raise HTTPException(status_code=400, detail=f"tenant_id is required for {operation}")
    return tenant_id


def _resolve_tenant_for_auth_entrypoint(
    x_tenant_id: Annotated[str | None, Header(alias="X-Tenant-ID")] = None,
) -> dict[str, object]:
    tenant_id = _require_tenant_id(x_tenant_id, operation="auth_entrypoint")
    tenant = get_tenant(tenant_id)
    if tenant is None:
        raise HTTPException(status_code=404, detail=f"Tenant {tenant_id} not found")
    if tenant.get("status") != "active":
        raise HTTPException(status_code=403, detail=f"Tenant {tenant_id} is not active")
    return tenant

class LanguagePreferencePayload(BaseModel):
    language: str


class LdapLoginPayload(BaseModel):
    login: str
    password: str
    mfa_code: str | None = None
    mfa_recovery_code: str | None = None


class ProviderLoginPayload(BaseModel):
    login: str | None = None
    username: str | None = None
    password: str
    provider: str | None = None
    mfa_code: str | None = None
    mfa_recovery_code: str | None = None


class RefreshPayload(BaseModel):
    refresh_token: str | None = None


class MFAEnableConfirmPayload(BaseModel):
    code: str


class MFAVerifyPayload(BaseModel):
    code: str | None = None
    recovery_code: str | None = None


class MFADisablePayload(BaseModel):
    code: str | None = None
    recovery_code: str | None = None


def _log_auth_event(
    *,
    actor: str,
    tenant_id: int,
    auth_source: str,
    action: str,
    request: Request,
    result: str,
    metadata: dict[str, object] | None = None,
) -> None:
    merged_metadata = {"auth_source": auth_source}
    if metadata:
        merged_metadata.update(metadata)
    if action.startswith("auth.login"):
        observe_auth_login_attempt(
            auth_source=auth_source,
            outcome="success" if result.lower() == "success" else str(merged_metadata.get("reason", "failed")),
            tenant_id=tenant_id,
        )
    log_admin_action(
        actor=actor,
        tenant_id=tenant_id,
        action=action,
        path=str(request.url.path),
        client_ip=request.client.host if request.client else "unknown",
        correlation_id=getattr(request.state, "request_id", None),
        entity="identity",
        result=result,
        metadata=merged_metadata,
    )
    if result.lower() == "failed":
        record_security_signal(
            signal=action,
            outcome="failed",
            actor=actor,
            client_ip=request.client.host if request.client else "unknown",
            path=request.url.path,
            tenant_id=tenant_id,
        )
        identity_logger.warning(
            "identity_login_failure",
            extra={
                "path": request.url.path,
                "method": request.method,
                "status_code": 401,
                "error_code": str(merged_metadata.get("reason", "IDENTITY_INVALID_CREDENTIALS")),
            },
        )
    elif action == "auth.login.success":
        identity_logger.info(
            "identity_login_success",
            extra={
                "path": request.url.path,
                "method": request.method,
                "status_code": 200,
            },
        )


def _session_payload(
    *,
    user_id: str,
    display_name: str,
    roles: list[str],
    language: str,
    auth_source: str,
    sync_with_ad: bool,
) -> dict[str, object]:
    return {
        "user_id": user_id,
        "display_name": display_name,
        "roles": roles,
        "language": language,
        "auth_source": auth_source,
        "sync_with_ad": sync_with_ad,
    }


def _token_permissions_for_roles(*, roles: list[str], tenant_id: int) -> list[str]:
    normalized_roles = [str(item).strip() for item in roles if str(item).strip()]
    if not normalized_roles:
        return []
    try:
        return sorted(resolve_permissions_for_tenant(normalized_roles, int(tenant_id)))
    except Exception:
        return []


def _resolve_authoritative_permissions(*, claims, roles: list[str], tenant_id: int) -> list[str]:
    claim_permissions = []
    if claims is not None:
        claim_permissions = sorted(
            {
                str(item).strip()
                for item in getattr(claims, "permissions", [])
                if str(item).strip()
            }
        )
    if claim_permissions:
        return claim_permissions
    return _token_permissions_for_roles(roles=roles, tenant_id=tenant_id)


def _apply_auth_cookie(response: Response, access_token: str, request: Request) -> None:
    same_site = get_auth_cookie_same_site()
    # Honor proxy-forwarded scheme so TLS-terminated deployments still issue secure cookies.
    forwarded_proto = request.headers.get("x-forwarded-proto", "").split(",", 1)[0].strip().lower()
    secure = forwarded_proto == "https" if forwarded_proto else request.url.scheme == "https"
    response.set_cookie(
        key=get_auth_cookie_name(),
        value=access_token,
        httponly=True,
        secure=secure,
        samesite=same_site,
        path="/",
    )


def _apply_refresh_cookie(response: Response, refresh_token: str, request: Request) -> None:
    same_site = get_auth_cookie_same_site()
    forwarded_proto = request.headers.get("x-forwarded-proto", "").split(",", 1)[0].strip().lower()
    secure = forwarded_proto == "https" if forwarded_proto else request.url.scheme == "https"
    response.set_cookie(
        key=get_auth_refresh_cookie_name(),
        value=refresh_token,
        httponly=True,
        secure=secure,
        samesite=same_site,
        path="/api/auth",
    )


def _issue_csrf_token(response: Response, request: Request) -> str:
    token = secrets.token_urlsafe(32)
    same_site = get_auth_csrf_cookie_same_site()
    forwarded_proto = request.headers.get("x-forwarded-proto", "").split(",", 1)[0].strip().lower()
    secure = forwarded_proto == "https" if forwarded_proto else request.url.scheme == "https"
    response.set_cookie(
        key=get_auth_csrf_cookie_name(),
        value=token,
        httponly=False,
        secure=secure,
        samesite=same_site,
        path="/",
    )
    return token


def _resolve_user_id_from_request(
    request: Request,
    authorization: str | None,
    x_user_id: str | None,
) -> str:
    claims = resolve_current_user_claims(request, authorization)
    if claims.token_type == "service":
        record_security_signal(
            signal="service_account.browser_misuse",
            outcome="denied",
            actor=claims.user_id,
            client_ip=request.client.host if request.client else "unknown",
            path=request.url.path,
            tenant_id=claims.tenant_id,
        )
        raise HTTPException(status_code=403, detail="service token cannot access browser user profile")
    if x_user_id and x_user_id != claims.user_id:
        if allow_legacy_header_auth():
            raise HTTPException(status_code=401, detail="header user mismatch with token")
    return claims.user_id


def _enforce_auth_lockout(request: Request, *, tenant_id: int, login_identifier: str | None) -> None:
    decision = get_auth_lockout_decision(request, tenant_id=tenant_id, login_identifier=login_identifier)
    if decision is None:
        return
    record_security_signal(
        signal="auth.login.locked",
        outcome="blocked",
        actor=str(login_identifier or "anonymous"),
        client_ip=request.client.host if request.client else "unknown",
        path=request.url.path,
        tenant_id=tenant_id,
    )
    raise HTTPException(
        status_code=429,
        detail={
            "code": "IDENTITY_RATE_LIMITED",
            "message": f"too many login attempts; retry in {decision.retry_after}s",
        },
        headers={"Retry-After": str(decision.retry_after)},
    )


def _record_auth_failure_lockout(request: Request, *, tenant_id: int, login_identifier: str | None) -> None:
    decision = record_auth_failure(request, tenant_id=tenant_id, login_identifier=login_identifier)
    if decision is None:
        return
    record_security_signal(
        signal="auth.login.backoff",
        outcome="blocked",
        actor=str(login_identifier or "anonymous"),
        client_ip=request.client.host if request.client else "unknown",
        path=request.url.path,
        tenant_id=tenant_id,
    )


@router.get("/modes")
def auth_modes() -> dict[str, dict[str, bool]]:
    return {"modes": get_auth_modes()}


@router.post("/ldap-login")
def ldap_login(
    payload: LdapLoginPayload,
    request: Request,
    response: Response,
    tenant: Annotated[dict, Depends(_resolve_tenant_for_auth_entrypoint)],
) -> dict[str, object]:
    tenant_id = int(tenant["id"])
    normalized_login = str(payload.login or "").strip()
    _enforce_auth_lockout(request, tenant_id=tenant_id, login_identifier=normalized_login)
    try:
        user = authenticate_ldap_user(payload.login, payload.password, tenant_id=tenant_id)
    except ValueError as exc:
        _record_auth_failure_lockout(request, tenant_id=tenant_id, login_identifier=normalized_login)
        _log_auth_event(
            actor=str(payload.login),
            tenant_id=tenant_id,
            auth_source="ldap",
            action="auth.login.failed",
            request=request,
            result="failed",
            metadata={"reason": str(exc)},
        )
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if is_mfa_enabled(user_id=str(user["user_id"]), tenant_id=tenant_id):
        valid_mfa = verify_mfa(
            user_id=str(user["user_id"]),
            tenant_id=tenant_id,
            code=payload.mfa_code,
            recovery_code=payload.mfa_recovery_code,
        )
        if not valid_mfa:
            _record_auth_failure_lockout(request, tenant_id=tenant_id, login_identifier=normalized_login)
            _log_auth_event(
                actor=str(user["user_id"]),
                tenant_id=tenant_id,
                auth_source="ldap",
                action="auth.login.failed",
                request=request,
                result="failed",
                metadata={"reason": "mfa_required_or_invalid"},
            )
            raise HTTPException(status_code=401, detail="mfa required")

    saved_language = get_user_language(str(user["user_id"]))
    session = _session_payload(
        user_id=str(user["user_id"]),
        display_name=str(user["display_name"]),
        roles=list(user["roles"]),
        language=saved_language or str(user["language"]),
        auth_source="ldap",
        sync_with_ad=True,
    )
    trusted_roles = [str(r).strip() for r in user["roles"] if str(r).strip()]
    sync_user_roles_from_trusted_source(str(user["user_id"]), trusted_roles, tenant_id=tenant_id)
    session_row = create_session(
        user_id=str(user["user_id"]),
        tenant_id=tenant_id,
        auth_source="ldap",
        client_ip=request.client.host if request.client else "unknown",
        user_agent=request.headers.get("user-agent", ""),
    )
    access_token = create_access_token(
        user_id=str(user["user_id"]),
        roles=list(user["roles"]),
        auth_source="ldap",
        tenant_id=tenant_id,
        session_id=str(session_row.get("session_id", "")),
        permissions=_token_permissions_for_roles(roles=list(user["roles"]), tenant_id=tenant_id),
    )
    refresh_token = create_refresh_token(
        user_id=str(user["user_id"]),
        roles=list(user["roles"]),
        auth_source="ldap",
        tenant_id=tenant_id,
        session_id=str(session_row.get("session_id", "")),
    )
    _apply_auth_cookie(response, access_token, request)
    _apply_refresh_cookie(response, refresh_token, request)
    clear_auth_failures(request, tenant_id=tenant_id, login_identifier=normalized_login)
    _log_auth_event(
        actor=str(user["user_id"]),
        tenant_id=tenant_id,
        auth_source="ldap",
        action="auth.login.success",
        request=request,
        result="success",
    )
    return {**session, "access_token": access_token, "refresh_token": refresh_token}


@router.post("/login")
def provider_login(
    payload: ProviderLoginPayload,
    request: Request,
    response: Response,
    tenant: Annotated[dict, Depends(_resolve_tenant_for_auth_entrypoint)],
) -> dict[str, object]:
    tenant_id = int(tenant["id"])
    normalized_login = str(payload.login or payload.username or "").strip()
    _enforce_auth_lockout(request, tenant_id=tenant_id, login_identifier=normalized_login)
    try:
        user = authenticate_tenant_login(
            tenant_id=tenant_id,
            login=normalized_login,
            password=payload.password,
            provider_name=payload.provider,
        )
    except DependencyUnavailableError as exc:
        _record_auth_failure_lockout(request, tenant_id=tenant_id, login_identifier=normalized_login)
        _log_auth_event(
            actor=str(normalized_login),
            tenant_id=tenant_id,
            auth_source=str(payload.provider or "identity"),
            action="auth.login.failed",
            request=request,
            result="failed",
            metadata={"reason": "identity_provider_unavailable"},
        )
        raise HTTPException(
            status_code=503,
            detail={
                "code": "IDENTITY_PROVIDER_UNAVAILABLE",
                "message": str(exc),
            },
        ) from exc
    except IdentityError as exc:
        _record_auth_failure_lockout(request, tenant_id=tenant_id, login_identifier=normalized_login)
        status_code = int(exc.http_status)
        response_detail = exc.to_response()
        if response_detail.get("code") in {"IDENTITY_MAPPING_EMPTY", "IDENTITY_MAPPING_INVALID"}:
            identity_logger.warning(
                "identity_mapping_failure",
                extra={
                    "path": request.url.path,
                    "method": request.method,
                    "status_code": status_code,
                    "error_code": response_detail.get("code"),
                },
            )

        _log_auth_event(
            actor=str(normalized_login),
            tenant_id=tenant_id,
            auth_source=str(payload.provider or "identity"),
            action="auth.login.failed",
            request=request,
            result="failed",
            metadata={
                "reason": response_detail.get("code", "IDENTITY_INVALID_CREDENTIALS"),
                "message": response_detail.get("message", "invalid credentials"),
            },
        )
        raise HTTPException(status_code=status_code, detail=response_detail) from exc

    user_id = str(user["user_id"])
    if is_mfa_enabled(user_id=user_id, tenant_id=tenant_id):
        valid_mfa = verify_mfa(
            user_id=user_id,
            tenant_id=tenant_id,
            code=payload.mfa_code,
            recovery_code=payload.mfa_recovery_code,
        )
        if not valid_mfa:
            _record_auth_failure_lockout(request, tenant_id=tenant_id, login_identifier=normalized_login)
            _log_auth_event(
                actor=user_id,
                tenant_id=tenant_id,
                auth_source=str(user.get("auth_source", "identity")),
                action="auth.login.failed",
                request=request,
                result="failed",
                metadata={"reason": "mfa_required_or_invalid"},
            )
            raise HTTPException(status_code=401, detail="mfa required")

    trusted_roles = [str(r).strip() for r in user.get("roles", []) if str(r).strip()]
    sync_user_roles_from_trusted_source(user_id, trusted_roles, tenant_id=tenant_id)
    saved_language = get_user_language(user_id)
    session = _session_payload(
        user_id=user_id,
        display_name=str(user.get("display_name", user_id)),
        roles=trusted_roles,
        language=saved_language or str(user.get("language", "ru")),
        auth_source=str(user.get("auth_source", "identity")),
        sync_with_ad=bool(user.get("sync_with_ad", False)),
    )
    session_row = create_session(
        user_id=user_id,
        tenant_id=tenant_id,
        auth_source=str(user.get("auth_source", "identity")),
        client_ip=request.client.host if request.client else "unknown",
        user_agent=request.headers.get("user-agent", ""),
    )
    access_token = create_access_token(
        user_id=user_id,
        roles=trusted_roles,
        auth_source=str(user.get("auth_source", "identity")),
        tenant_id=tenant_id,
        session_id=str(session_row.get("session_id", "")),
        permissions=_token_permissions_for_roles(roles=trusted_roles, tenant_id=tenant_id),
    )
    refresh_token = create_refresh_token(
        user_id=user_id,
        roles=trusted_roles,
        auth_source=str(user.get("auth_source", "identity")),
        tenant_id=tenant_id,
        session_id=str(session_row.get("session_id", "")),
    )
    _apply_auth_cookie(response, access_token, request)
    _apply_refresh_cookie(response, refresh_token, request)
    clear_auth_failures(request, tenant_id=tenant_id, login_identifier=normalized_login)
    _log_auth_event(
        actor=user_id,
        tenant_id=tenant_id,
        auth_source=str(user.get("auth_source", "identity")),
        action="auth.login.success",
        request=request,
        result="success",
        metadata={"provider": user.get("provider")},
    )
    return {**session, "access_token": access_token, "refresh_token": refresh_token}


@router.post("/logout")
def logout(request: Request, response: Response) -> dict[str, str]:
    try:
        access_claims = parse_access_token_from_cookie(request)
    except Exception:
        access_claims = None
    if access_claims is not None:
        try:
            revoke_token(access_claims.jti, expires_at=access_claims.expires_at)
        except RevocationStoreUnavailable as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        if access_claims.session_id:
            revoke_session(session_id=access_claims.session_id)

    try:
        refresh_claims = parse_refresh_token_from_cookie(request)
    except Exception:
        refresh_claims = None
    if refresh_claims is not None:
        try:
            revoke_token(refresh_claims.jti, expires_at=refresh_claims.expires_at)
        except RevocationStoreUnavailable as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc

    response.delete_cookie(key=get_auth_cookie_name(), path="/")
    response.delete_cookie(key=get_auth_csrf_cookie_name(), path="/")
    response.delete_cookie(key=get_auth_refresh_cookie_name(), path="/api/auth")
    if access_claims is not None:
        _log_auth_event(
            actor=access_claims.user_id,
            tenant_id=access_claims.tenant_id,
            auth_source=access_claims.auth_source,
            action="auth.logout",
            request=request,
            result="success",
            metadata={"session_id": access_claims.session_id},
        )
    return {"status": "ok"}


@router.post("/refresh")
def refresh_session(request: Request, response: Response, payload: RefreshPayload | None = None) -> dict[str, object]:
    try:
        refresh_claims = parse_refresh_token_from_cookie(request)
        if refresh_claims is None and payload is not None and payload.refresh_token:
            refresh_claims = verify_refresh_token(payload.refresh_token)
    except RevocationStoreUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        # No trusted tenant context in this failure branch; avoid implicit tenant assignment.
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    if refresh_claims is None:
        raise HTTPException(status_code=401, detail="refresh token is required")

    try:
        revoke_token(refresh_claims.jti, expires_at=refresh_claims.expires_at)
    except RevocationStoreUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    new_access_token = create_access_token(
        user_id=refresh_claims.user_id,
        roles=list(refresh_claims.roles),
        auth_source=refresh_claims.auth_source,
        tenant_id=refresh_claims.tenant_id,
        session_id=refresh_claims.session_id,
        permissions=_token_permissions_for_roles(
            roles=list(refresh_claims.roles),
            tenant_id=refresh_claims.tenant_id,
        ),
    )
    new_refresh_token = create_refresh_token(
        user_id=refresh_claims.user_id,
        roles=list(refresh_claims.roles),
        auth_source=refresh_claims.auth_source,
        tenant_id=refresh_claims.tenant_id,
        session_id=refresh_claims.session_id,
    )

    _apply_auth_cookie(response, new_access_token, request)
    _apply_refresh_cookie(response, new_refresh_token, request)
    _log_auth_event(
        actor=refresh_claims.user_id,
        tenant_id=refresh_claims.tenant_id,
        auth_source=refresh_claims.auth_source,
        action="auth.refresh.success",
        request=request,
        result="success",
        metadata={"session_id": refresh_claims.session_id},
    )
    return {
        "status": "ok",
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
    }


@router.get("/csrf")
def issue_csrf(request: Request, response: Response) -> dict[str, str]:
    token = _issue_csrf_token(response, request)
    return {"csrf_token": token}


@router.get("/me/profile")
def get_my_profile(
    request: Request,
    authorization: Annotated[str | None, Header()] = None,
    x_user_id: Annotated[str | None, Header()] = None,
) -> dict[str, object]:
    resolved_user_id = _resolve_user_id_from_request(request, authorization, x_user_id)
    claims = getattr(request.state, "auth_claims", None)

    local_user = local_user_store.get_user(resolved_user_id)
    if local_user is None:
        if claims is not None and claims.auth_source == "ldap":
            fallback_display_name = resolved_user_id
            if resolved_user_id.startswith("ad.") and len(resolved_user_id) > 3:
                fallback_display_name = resolved_user_id[3:]
            return {
                "user_id": resolved_user_id,
                "display_name": fallback_display_name,
                "roles": [r for r in claims.roles if str(r).strip()],
                "permissions": _resolve_authoritative_permissions(
                    claims=claims,
                    roles=[r for r in claims.roles if str(r).strip()],
                    tenant_id=_require_tenant_id(claims.tenant_id, operation="profile_ldap_claims"),
                ),
                "tenant_id": _require_tenant_id(claims.tenant_id, operation="profile_ldap_claims"),
                "auth_source": "ldap",
                "sync_with_ad": True,
                "language": get_user_language(resolved_user_id) or "ru",
            }
        raise HTTPException(status_code=404, detail="user not found")

    return {
        "user_id": local_user["user_id"],
        "display_name": local_user["display_name"],
        "roles": local_user["roles"],
        "permissions": _resolve_authoritative_permissions(
            claims=claims,
            roles=list(local_user["roles"]),
            tenant_id=_require_tenant_id(local_user.get("tenant_id"), operation="profile_local_user"),
        ),
        "tenant_id": _require_tenant_id(local_user.get("tenant_id"), operation="profile_local_user"),
        "auth_source": "local",
        "sync_with_ad": False,
        "language": get_user_language(resolved_user_id) or local_user["default_language"],
    }


@router.get("/me/preferences")
def get_my_preferences(
    request: Request,
    authorization: Annotated[str | None, Header()] = None,
    x_user_id: Annotated[str | None, Header()] = None,
) -> dict[str, str | None]:
    resolved_user_id = _resolve_user_id_from_request(request, authorization, x_user_id)

    return {"language": get_user_language(resolved_user_id)}


@router.put("/me/preferences/language")
def set_my_language_preference(
    payload: LanguagePreferencePayload,
    request: Request,
    authorization: Annotated[str | None, Header()] = None,
    x_user_id: Annotated[str | None, Header()] = None,
) -> dict[str, str]:
    resolved_user_id = _resolve_user_id_from_request(request, authorization, x_user_id)

    normalized = normalize_code(payload.language)
    enabled_codes = {item["code"] for item in list_languages(enabled_only=True)}
    if normalized not in enabled_codes:
        raise HTTPException(status_code=400, detail="language is not enabled")

    saved = set_user_language(resolved_user_id, normalized)
    claims = getattr(request.state, "auth_claims", None)
    if claims is not None:
        _log_auth_event(
            actor=claims.user_id,
            tenant_id=claims.tenant_id,
            auth_source=claims.auth_source,
            action="auth.preferences.language.update",
            request=request,
            result="success",
            metadata={"language": saved},
        )
    return {"language": saved}


@router.post("/mfa/enable")
def mfa_enable(
    request: Request,
    authorization: Annotated[str | None, Header()] = None,
) -> dict[str, object]:
    claims = resolve_current_user_claims(request, authorization)
    payload = initiate_mfa_enrollment(user_id=claims.user_id, tenant_id=claims.tenant_id)
    _log_auth_event(
        actor=claims.user_id,
        tenant_id=claims.tenant_id,
        auth_source=claims.auth_source,
        action="auth.mfa.enable.initiated",
        request=request,
        result="success",
    )
    return payload


@router.post("/mfa/verify")
def mfa_verify(
    payload: MFAVerifyPayload,
    request: Request,
    authorization: Annotated[str | None, Header()] = None,
) -> dict[str, object]:
    claims = resolve_current_user_claims(request, authorization)
    enabled_now = enable_mfa(
        user_id=claims.user_id,
        tenant_id=claims.tenant_id,
        code=str(payload.code or ""),
    )
    if enabled_now:
        _log_auth_event(
            actor=claims.user_id,
            tenant_id=claims.tenant_id,
            auth_source=claims.auth_source,
            action="auth.mfa.enabled",
            request=request,
            result="success",
        )
        return {"status": "enabled"}

    verified = verify_mfa(
        user_id=claims.user_id,
        tenant_id=claims.tenant_id,
        code=payload.code,
        recovery_code=payload.recovery_code,
    )
    if not verified:
        _log_auth_event(
            actor=claims.user_id,
            tenant_id=claims.tenant_id,
            auth_source=claims.auth_source,
            action="auth.mfa.verify.failed",
            request=request,
            result="failed",
        )
        raise HTTPException(status_code=400, detail="invalid mfa code")

    _log_auth_event(
        actor=claims.user_id,
        tenant_id=claims.tenant_id,
        auth_source=claims.auth_source,
        action="auth.mfa.verify.success",
        request=request,
        result="success",
    )
    return {"status": "verified"}


@router.post("/mfa/disable")
def mfa_disable(
    payload: MFADisablePayload,
    request: Request,
    authorization: Annotated[str | None, Header()] = None,
) -> dict[str, object]:
    claims = resolve_current_user_claims(request, authorization)
    allowed = verify_mfa(
        user_id=claims.user_id,
        tenant_id=claims.tenant_id,
        code=payload.code,
        recovery_code=payload.recovery_code,
    )
    if not allowed:
        raise HTTPException(status_code=400, detail="invalid mfa code")
    disabled = disable_mfa(user_id=claims.user_id, tenant_id=claims.tenant_id)
    if not disabled:
        raise HTTPException(status_code=400, detail="mfa is not enabled")
    _log_auth_event(
        actor=claims.user_id,
        tenant_id=claims.tenant_id,
        auth_source=claims.auth_source,
        action="auth.mfa.disabled",
        request=request,
        result="success",
    )
    return {"status": "disabled"}


@router.get("/sessions")
def list_my_sessions(
    request: Request,
    authorization: Annotated[str | None, Header()] = None,
) -> dict[str, list[dict[str, object]]]:
    claims = resolve_current_user_claims(request, authorization)
    sessions = list_sessions_for_user(user_id=claims.user_id, tenant_id=claims.tenant_id)
    sanitized = [
        {
            "session_id": item.get("session_id"),
            "auth_source": item.get("auth_source"),
            "client_ip": item.get("client_ip"),
            "user_agent": item.get("user_agent"),
            "created_at": item.get("created_at"),
            "last_seen_at": item.get("last_seen_at"),
            "revoked_at": item.get("revoked_at"),
            "active": item.get("active"),
        }
        for item in sessions
    ]
    return {"sessions": sanitized}


@router.post("/sessions/revoke-current")
def revoke_current_session(
    request: Request,
    authorization: Annotated[str | None, Header()] = None,
) -> dict[str, object]:
    claims = resolve_current_user_claims(request, authorization)
    if not claims.session_id:
        raise HTTPException(status_code=400, detail="session id missing")
    revoked = revoke_session(session_id=claims.session_id)
    try:
        revoke_token(claims.jti, expires_at=claims.expires_at)
    except RevocationStoreUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    _log_auth_event(
        actor=claims.user_id,
        tenant_id=claims.tenant_id,
        auth_source=claims.auth_source,
        action="auth.sessions.revoke_current",
        request=request,
        result="success" if revoked else "noop",
        metadata={"session_id": claims.session_id},
    )
    return {"revoked": bool(revoked), "session_id": claims.session_id}


@router.post("/sessions/revoke-all")
def revoke_all_sessions(
    request: Request,
    authorization: Annotated[str | None, Header()] = None,
) -> dict[str, object]:
    claims = resolve_current_user_claims(request, authorization)
    revoked_count = revoke_all_sessions_for_user(user_id=claims.user_id, tenant_id=claims.tenant_id)
    try:
        revoke_token(claims.jti, expires_at=claims.expires_at)
    except RevocationStoreUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    _log_auth_event(
        actor=claims.user_id,
        tenant_id=claims.tenant_id,
        auth_source=claims.auth_source,
        action="auth.sessions.revoke_all",
        request=request,
        result="success",
        metadata={"revoked_count": revoked_count},
    )
    return {"revoked_count": revoked_count}


@router.post("/oidc/{provider}/initiate")
def initiate_oidc_login(
    provider: str,
    request: Request,
    tenant: Annotated[dict, Depends(_resolve_tenant_for_auth_entrypoint)],
) -> dict[str, object]:
    try:
        challenge = create_oidc_login_challenge(tenant_id=int(tenant["id"]), provider=provider)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    _log_auth_event(
        actor="anonymous",
        tenant_id=int(tenant["id"]),
        auth_source="oidc",
        action="auth.oidc.initiate",
        request=request,
        result="success",
        metadata={"provider": provider},
    )
    return challenge


@router.get("/oidc/{provider}/callback")
def oidc_callback(
    provider: str,
    state: str,
    code: str,
    request: Request,
    response: Response,
) -> dict[str, object]:
    consumed = consume_oidc_state(state=state)
    if consumed is None:
        # No trusted tenant context is available for invalid/unknown state.
        raise HTTPException(status_code=400, detail="invalid oidc state")

    tenant_id = _require_tenant_id(consumed.get("tenant_id"), operation="oidc_callback")
    if str(consumed.get("provider", "")).strip().lower() != str(provider).strip().lower():
        raise HTTPException(status_code=400, detail="provider mismatch")

    config = get_provider(tenant_id=tenant_id, provider=provider)
    if config is None:
        raise HTTPException(status_code=404, detail="identity provider not found")

    try:
        external_identity = exchange_oidc_code_for_identity(provider_config=config, code=code)
    except NotImplementedError as exc:
        _log_auth_event(
            actor="anonymous",
            tenant_id=tenant_id,
            auth_source="oidc",
            action="auth.oidc.callback.failed",
            request=request,
            result="failed",
            metadata={"provider": provider, "reason": str(exc)},
        )
        raise HTTPException(status_code=501, detail="oidc exchange not configured") from exc

    mapped_login = str(external_identity.email or "").strip().lower()
    local_user = local_user_store.find_user_by_login(mapped_login) if mapped_login else None
    if local_user is not None and _require_tenant_id(local_user.get("tenant_id"), operation="oidc_local_user_match") != tenant_id:
        local_user = None
    user_id = str(local_user["user_id"]) if local_user is not None else f"oidc.{provider}.{external_identity.subject}"
    roles = [str(item).strip() for item in (local_user.get("roles", []) if local_user else []) if str(item).strip()]

    sync_user_roles_from_trusted_source(user_id, roles, tenant_id=tenant_id)
    session_row = create_session(
        user_id=user_id,
        tenant_id=tenant_id,
        auth_source="oidc",
        client_ip=request.client.host if request.client else "unknown",
        user_agent=request.headers.get("user-agent", ""),
    )
    access_token = create_access_token(
        user_id=user_id,
        roles=roles,
        auth_source="oidc",
        tenant_id=tenant_id,
        session_id=str(session_row.get("session_id", "")),
    )
    refresh_token = create_refresh_token(
        user_id=user_id,
        roles=roles,
        auth_source="oidc",
        tenant_id=tenant_id,
        session_id=str(session_row.get("session_id", "")),
    )
    _apply_auth_cookie(response, access_token, request)
    _apply_refresh_cookie(response, refresh_token, request)
    _log_auth_event(
        actor=user_id,
        tenant_id=tenant_id,
        auth_source="oidc",
        action="auth.oidc.callback.success",
        request=request,
        result="success",
        metadata={"provider": provider, "roles_mapped_count": len(roles)},
    )
    return {
        "status": "ok",
        "user_id": user_id,
        "roles": roles,
        "tenant_id": tenant_id,
        "auth_source": "oidc",
        "access_token": access_token,
        "refresh_token": refresh_token,
    }
