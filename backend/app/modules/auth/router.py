from typing import Annotated
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
    is_dev_demo_compatibility_mode,
)
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
from app.modules.i18n.service import list_languages, normalize_code
from app.modules.rbac.service import get_trusted_demo_roles, sync_user_roles_from_trusted_source
from app.modules.rbac.security import resolve_current_user_claims

router = APIRouter(prefix="/api/auth", tags=["auth"])

# Template-only demo identities for local/bootstrap use.
# Derived projects must remove, disable, or replace these flows before production launch.
DEMO_USERS = {
    "admin.001": {
        "user_id": "admin.001",
        "login": "admin",
        "password": "admin123",
        "display_name": "Администратор Айжан",
        "roles": ["admin"],
        "default_language": "ru",
    },
    "teacher.001": {
        "user_id": "teacher.001",
        "login": "teacher",
        "password": "teacher123",
        "display_name": "Преподаватель Иван",
        "roles": ["auditor"],
        "default_language": "kk",
    },
    "student.001": {
        "user_id": "student.001",
        "login": "student",
        "password": "student123",
        "display_name": "Студент Ли",
        "roles": ["student"],
        "default_language": "en",
    },
}


class LanguagePreferencePayload(BaseModel):
    language: str


class DemoLoginPayload(BaseModel):
    user_id: str


class MockLoginPayload(BaseModel):
    login: str
    password: str
    mfa_code: str | None = None
    mfa_recovery_code: str | None = None


class LdapLoginPayload(BaseModel):
    login: str
    password: str
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


def _require_demo_compatibility_mode() -> None:
    if not is_dev_demo_compatibility_mode():
        raise HTTPException(status_code=404, detail="not found")


@router.get("/modes")
def auth_modes() -> dict[str, dict[str, bool]]:
    return {"modes": get_auth_modes()}


@router.get("/demo-users")
def demo_users() -> dict[str, list[dict[str, object]]]:
    _require_demo_compatibility_mode()
    return {
        "users": [
            {
                "user_id": item["user_id"],
                "login": item["login"],
                "display_name": item["display_name"],
                "roles": item["roles"],
                "default_language": item["default_language"],
            }
            for item in DEMO_USERS.values()
        ]
    }


@router.post("/demo-login")
def demo_login(payload: DemoLoginPayload, request: Request, response: Response) -> dict[str, object]:
    _require_demo_compatibility_mode()
    user = DEMO_USERS.get(payload.user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="demo user not found")

    saved_language = get_user_language(payload.user_id)
    session = _session_payload(
        user_id=str(user["user_id"]),
        display_name=str(user["display_name"]),
        roles=list(user["roles"]),
        language=saved_language or str(user["default_language"]),
        auth_source="demo",
        sync_with_ad=False,
    )
    session_row = create_session(
        user_id=str(user["user_id"]),
        tenant_id=1,
        auth_source="demo",
        client_ip=request.client.host if request.client else "unknown",
        user_agent=request.headers.get("user-agent", ""),
    )
    sync_user_roles_from_trusted_source(str(user["user_id"]), get_trusted_demo_roles(str(user["user_id"])), tenant_id=1)
    access_token = create_access_token(
        user_id=str(user["user_id"]),
        roles=list(user["roles"]),
        auth_source="demo",
        tenant_id=1,
        session_id=str(session_row.get("session_id", "")),
    )
    refresh_token = create_refresh_token(
        user_id=str(user["user_id"]),
        roles=list(user["roles"]),
        auth_source="demo",
        tenant_id=1,
        session_id=str(session_row.get("session_id", "")),
    )
    _apply_auth_cookie(response, access_token, request)
    _apply_refresh_cookie(response, refresh_token, request)
    _log_auth_event(
        actor=str(user["user_id"]),
        tenant_id=1,
        auth_source="demo",
        action="auth.login.success",
        request=request,
        result="success",
    )
    return {**session, "access_token": access_token, "refresh_token": refresh_token}


@router.post("/mock-login")
def mock_login(payload: MockLoginPayload, request: Request, response: Response) -> dict[str, object]:
    local_user = local_user_store.authenticate(payload.login, payload.password)
    if local_user is not None:
        user_id = str(local_user["user_id"])
        tenant_id = int(local_user.get("tenant_id", 1))
        if is_mfa_enabled(user_id=user_id, tenant_id=tenant_id):
            valid_mfa = verify_mfa(
                user_id=user_id,
                tenant_id=tenant_id,
                code=payload.mfa_code,
                recovery_code=payload.mfa_recovery_code,
            )
            if not valid_mfa:
                _log_auth_event(
                    actor=user_id,
                    tenant_id=tenant_id,
                    auth_source="local",
                    action="auth.login.failed",
                    request=request,
                    result="failed",
                    metadata={"reason": "mfa_required_or_invalid"},
                )
                raise HTTPException(status_code=401, detail="mfa required")
        trusted_roles = [str(value).strip() for value in local_user.get("roles", []) if str(value).strip()]
        sync_user_roles_from_trusted_source(user_id, trusted_roles, tenant_id=tenant_id)
        saved_language = get_user_language(user_id)
        session = _session_payload(
            user_id=user_id,
            display_name=str(local_user["display_name"]),
            roles=list(local_user["roles"]),
            language=saved_language or str(local_user["default_language"]),
            auth_source="local",
            sync_with_ad=False,
        )
        session_row = create_session(
            user_id=user_id,
            tenant_id=tenant_id,
            auth_source="local",
            client_ip=request.client.host if request.client else "unknown",
            user_agent=request.headers.get("user-agent", ""),
        )
        access_token = create_access_token(
            user_id=user_id,
            roles=list(local_user["roles"]),
            auth_source="local",
            tenant_id=tenant_id,
            session_id=str(session_row.get("session_id", "")),
        )
        refresh_token = create_refresh_token(
            user_id=user_id,
            roles=list(local_user["roles"]),
            auth_source="local",
            tenant_id=tenant_id,
            session_id=str(session_row.get("session_id", "")),
        )
        _apply_auth_cookie(response, access_token, request)
        _apply_refresh_cookie(response, refresh_token, request)
        _log_auth_event(
            actor=user_id,
            tenant_id=tenant_id,
            auth_source="local",
            action="auth.login.success",
            request=request,
            result="success",
        )
        return {**session, "access_token": access_token, "refresh_token": refresh_token}

    if is_dev_demo_compatibility_mode():
        for user in DEMO_USERS.values():
            if user["login"] == payload.login and user["password"] == payload.password:
                demo_user_id = str(user["user_id"])
                sync_user_roles_from_trusted_source(demo_user_id, get_trusted_demo_roles(demo_user_id), tenant_id=1)
                saved_language = get_user_language(user["user_id"])
                session = _session_payload(
                    user_id=demo_user_id,
                    display_name=str(user["display_name"]),
                    roles=list(user["roles"]),
                    language=saved_language or str(user["default_language"]),
                    auth_source="demo",
                    sync_with_ad=False,
                )
                session_row = create_session(
                    user_id=demo_user_id,
                    tenant_id=1,
                    auth_source="demo",
                    client_ip=request.client.host if request.client else "unknown",
                    user_agent=request.headers.get("user-agent", ""),
                )
                access_token = create_access_token(
                    user_id=demo_user_id,
                    roles=list(user["roles"]),
                    auth_source="demo",
                    tenant_id=1,
                    session_id=str(session_row.get("session_id", "")),
                )
                refresh_token = create_refresh_token(
                    user_id=demo_user_id,
                    roles=list(user["roles"]),
                    auth_source="demo",
                    tenant_id=1,
                    session_id=str(session_row.get("session_id", "")),
                )
                _apply_auth_cookie(response, access_token, request)
                _apply_refresh_cookie(response, refresh_token, request)
                _log_auth_event(
                    actor=demo_user_id,
                    tenant_id=1,
                    auth_source="demo",
                    action="auth.login.success",
                    request=request,
                    result="success",
                )
                return {**session, "access_token": access_token, "refresh_token": refresh_token}

    _log_auth_event(
        actor=str(payload.login),
        tenant_id=1,
        auth_source="local",
        action="auth.login.failed",
        request=request,
        result="failed",
        metadata={"reason": "invalid_credentials"},
    )
    raise HTTPException(status_code=401, detail="invalid credentials")


@router.post("/ldap-login")
def ldap_login(
    payload: LdapLoginPayload,
    request: Request,
    response: Response,
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict[str, object]:
    try:
        user = authenticate_ldap_user(payload.login, payload.password, tenant_id=int(tenant["id"]))
    except ValueError as exc:
        _log_auth_event(
            actor=str(payload.login),
            tenant_id=int(tenant["id"]),
            auth_source="ldap",
            action="auth.login.failed",
            request=request,
            result="failed",
            metadata={"reason": str(exc)},
        )
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if is_mfa_enabled(user_id=str(user["user_id"]), tenant_id=int(tenant["id"])):
        valid_mfa = verify_mfa(
            user_id=str(user["user_id"]),
            tenant_id=int(tenant["id"]),
            code=payload.mfa_code,
            recovery_code=payload.mfa_recovery_code,
        )
        if not valid_mfa:
            _log_auth_event(
                actor=str(user["user_id"]),
                tenant_id=int(tenant["id"]),
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
    sync_user_roles_from_trusted_source(str(user["user_id"]), trusted_roles, tenant_id=int(tenant["id"]))
    session_row = create_session(
        user_id=str(user["user_id"]),
        tenant_id=int(tenant["id"]),
        auth_source="ldap",
        client_ip=request.client.host if request.client else "unknown",
        user_agent=request.headers.get("user-agent", ""),
    )
    access_token = create_access_token(
        user_id=str(user["user_id"]),
        roles=list(user["roles"]),
        auth_source="ldap",
        tenant_id=int(tenant["id"]),
        session_id=str(session_row.get("session_id", "")),
    )
    refresh_token = create_refresh_token(
        user_id=str(user["user_id"]),
        roles=list(user["roles"]),
        auth_source="ldap",
        tenant_id=int(tenant["id"]),
        session_id=str(session_row.get("session_id", "")),
    )
    _apply_auth_cookie(response, access_token, request)
    _apply_refresh_cookie(response, refresh_token, request)
    _log_auth_event(
        actor=str(user["user_id"]),
        tenant_id=int(tenant["id"]),
        auth_source="ldap",
        action="auth.login.success",
        request=request,
        result="success",
    )
    return {**session, "access_token": access_token, "refresh_token": refresh_token}


@router.post("/logout")
def logout(request: Request, response: Response) -> dict[str, str]:
    try:
        access_claims = parse_access_token_from_cookie(request)
    except Exception:
        access_claims = None
    if access_claims is not None:
        revoke_token(access_claims.jti, expires_at=access_claims.expires_at)
        if access_claims.session_id:
            revoke_session(session_id=access_claims.session_id)

    try:
        refresh_claims = parse_refresh_token_from_cookie(request)
    except Exception:
        refresh_claims = None
    if refresh_claims is not None:
        revoke_token(refresh_claims.jti, expires_at=refresh_claims.expires_at)

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
    except Exception as exc:
        _log_auth_event(
            actor="anonymous",
            tenant_id=1,
            auth_source="refresh",
            action="auth.refresh.failed",
            request=request,
            result="failed",
            metadata={"reason": str(exc)},
        )
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    if refresh_claims is None:
        raise HTTPException(status_code=401, detail="refresh token is required")

    revoke_token(refresh_claims.jti, expires_at=refresh_claims.expires_at)
    new_access_token = create_access_token(
        user_id=refresh_claims.user_id,
        roles=list(refresh_claims.roles),
        auth_source=refresh_claims.auth_source,
        tenant_id=refresh_claims.tenant_id,
        session_id=refresh_claims.session_id,
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

    user = DEMO_USERS.get(resolved_user_id)
    if user is not None:
        return {
            "user_id": user["user_id"],
            "display_name": user["display_name"],
            "roles": user["roles"],
            "auth_source": "demo",
            "sync_with_ad": False,
            "language": get_user_language(resolved_user_id) or user["default_language"],
        }

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
                "tenant_id": int(claims.tenant_id) if int(claims.tenant_id) > 0 else 1,
                "auth_source": "ldap",
                "sync_with_ad": True,
                "language": get_user_language(resolved_user_id) or "ru",
            }
        raise HTTPException(status_code=404, detail="user not found")

    return {
        "user_id": local_user["user_id"],
        "display_name": local_user["display_name"],
        "roles": local_user["roles"],
        "tenant_id": int(local_user.get("tenant_id", 1)),
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
    revoke_token(claims.jti, expires_at=claims.expires_at)
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
    revoke_token(claims.jti, expires_at=claims.expires_at)
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
    tenant: Annotated[dict, Depends(get_current_tenant)],
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
        _log_auth_event(
            actor="anonymous",
            tenant_id=1,
            auth_source="oidc",
            action="auth.oidc.callback.failed",
            request=request,
            result="failed",
            metadata={"provider": provider, "reason": "invalid_state"},
        )
        raise HTTPException(status_code=400, detail="invalid oidc state")

    tenant_id = int(consumed.get("tenant_id", 1))
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
    if local_user is not None and int(local_user.get("tenant_id", 1)) != tenant_id:
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
