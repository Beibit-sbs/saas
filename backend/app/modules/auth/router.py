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
    get_auth_modes,
)
from app.core.tenant import get_current_tenant
from app.modules.ldap.service import authenticate_ldap_user
from app.modules.auth.local_users_service import local_user_store
from app.modules.auth.preferences_service import get_user_language, set_user_language
from app.modules.auth.token_service import create_access_token
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


class LdapLoginPayload(BaseModel):
    login: str
    password: str


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
        "access_token": create_access_token(user_id=user_id, roles=roles, auth_source=auth_source),
    }


def _apply_auth_cookie(response: Response, access_token: str, request: Request) -> None:
    same_site = get_auth_cookie_same_site()
    # Secure cookies are enforced on HTTPS; local HTTP dev remains functional.
    secure = request.url.scheme == "https"
    response.set_cookie(
        key=get_auth_cookie_name(),
        value=access_token,
        httponly=True,
        secure=secure,
        samesite=same_site,
        path="/",
    )


def _issue_csrf_token(response: Response, request: Request) -> str:
    token = secrets.token_urlsafe(32)
    same_site = get_auth_csrf_cookie_same_site()
    secure = request.url.scheme == "https"
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
    if x_user_id and x_user_id != claims.user_id:
        if allow_legacy_header_auth():
            raise HTTPException(status_code=401, detail="header user mismatch with token")
    return claims.user_id


@router.get("/modes")
def auth_modes() -> dict[str, dict[str, bool]]:
    return {"modes": get_auth_modes()}


@router.get("/demo-users")
def demo_users() -> dict[str, list[dict[str, object]]]:
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
    sync_user_roles_from_trusted_source(str(user["user_id"]), get_trusted_demo_roles(str(user["user_id"])))
    _apply_auth_cookie(response, str(session["access_token"]), request)
    return session


@router.post("/mock-login")
def mock_login(payload: MockLoginPayload, request: Request, response: Response) -> dict[str, object]:
    local_user = local_user_store.authenticate(payload.login, payload.password)
    if local_user is not None:
        user_id = str(local_user["user_id"])
        trusted_roles = [str(value).strip() for value in local_user.get("roles", []) if str(value).strip()]
        sync_user_roles_from_trusted_source(user_id, trusted_roles)
        saved_language = get_user_language(user_id)
        session = _session_payload(
            user_id=user_id,
            display_name=str(local_user["display_name"]),
            roles=list(local_user["roles"]),
            language=saved_language or str(local_user["default_language"]),
            auth_source="local",
            sync_with_ad=False,
        )
        _apply_auth_cookie(response, str(session["access_token"]), request)
        return session

    for user in DEMO_USERS.values():
        if user["login"] == payload.login and user["password"] == payload.password:
            demo_user_id = str(user["user_id"])
            sync_user_roles_from_trusted_source(demo_user_id, get_trusted_demo_roles(demo_user_id))
            saved_language = get_user_language(user["user_id"])
            session = _session_payload(
                user_id=demo_user_id,
                display_name=str(user["display_name"]),
                roles=list(user["roles"]),
                language=saved_language or str(user["default_language"]),
                auth_source="demo",
                sync_with_ad=False,
            )
            _apply_auth_cookie(response, str(session["access_token"]), request)
            return session

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
        raise HTTPException(status_code=400, detail=str(exc)) from exc

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
    sync_user_roles_from_trusted_source(str(user["user_id"]), trusted_roles)
    _apply_auth_cookie(response, str(session["access_token"]), request)
    return session


@router.post("/logout")
def logout(response: Response) -> dict[str, str]:
    response.delete_cookie(key=get_auth_cookie_name(), path="/")
    response.delete_cookie(key=get_auth_csrf_cookie_name(), path="/")
    return {"status": "ok"}


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
        raise HTTPException(status_code=404, detail="user not found")

    return {
        "user_id": local_user["user_id"],
        "display_name": local_user["display_name"],
        "roles": local_user["roles"],
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
    return {"language": saved}
