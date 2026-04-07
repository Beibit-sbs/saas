from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel, Field

from app.modules.audit.service import log_admin_action
from app.modules.i18n.service import add_language, delete_language, get_default_language, list_language_catalog, list_languages, set_default_language, set_language_enabled
from app.modules.rbac.security import get_actor, permission_dependency, resolve_current_user_claims
from app.modules.rbac.service import is_platform_admin

public_router = APIRouter(prefix="/api/i18n", tags=["i18n"])
admin_router = APIRouter(prefix="/api/admin/i18n", tags=["i18n-admin"])
PLATFORM_TENANT_ID = 1


def _require_platform_tenant_context(
    request: Request,
    actor: Annotated[str, Depends(get_actor)],
    authorization: Annotated[str | None, Header()] = None,
) -> str:
    claims = resolve_current_user_claims(request, authorization)
    if int(claims.tenant_id) == PLATFORM_TENANT_ID:
        return actor
    if is_platform_admin(actor):
        return actor
    raise HTTPException(status_code=403, detail="platform tenant context required")


class AddLanguagePayload(BaseModel):
    code: str = Field(min_length=2, max_length=20)
    name: str = Field(min_length=1, max_length=120)
    native_name: str | None = Field(default=None, max_length=120)


class UpdateLanguageStatusPayload(BaseModel):
    enabled: bool


class UpdateDefaultLanguagePayload(BaseModel):
    code: str = Field(min_length=2, max_length=20)


@public_router.get("/languages")
def get_public_languages() -> dict[str, list[dict[str, str | bool]] | str]:
    return {
        "languages": list_languages(enabled_only=True),
        "default_language": get_default_language(),
    }


@public_router.get("/catalog")
def get_language_catalog() -> dict[str, list[dict[str, str]]]:
    return {"languages": list_language_catalog()}


@admin_router.get("/languages")
def get_admin_languages(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.i18n.manage"))],
) -> dict[str, list[dict[str, str | bool]] | str]:
    return {
        "languages": list_languages(enabled_only=False),
        "default_language": get_default_language(),
    }


@admin_router.patch("/default-language")
def update_default_language(
    payload: UpdateDefaultLanguagePayload,
    request: Request,
    actor: Annotated[str, Depends(_require_platform_tenant_context)],
    __: Annotated[None, Depends(permission_dependency("admin.i18n.manage"))],
) -> dict[str, str]:
    try:
        code = set_default_language(payload.code)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    log_admin_action(
        actor=actor,
        tenant_id=PLATFORM_TENANT_ID,
        action="i18n.languages.default.update",
        path=str(request.url.path),
        client_ip=request.client.host if request.client else "unknown",
        correlation_id=getattr(request.state, "request_id", None),
        entity="i18n",
        result="success",
        metadata={"default_language": code},
    )
    return {"default_language": code}


@admin_router.post("/languages")
def create_language(
    payload: AddLanguagePayload,
    request: Request,
    actor: Annotated[str, Depends(_require_platform_tenant_context)],
    __: Annotated[None, Depends(permission_dependency("admin.i18n.manage"))],
) -> dict[str, dict[str, str | bool]]:
    try:
        language = add_language(payload.code, payload.name, payload.native_name)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    log_admin_action(
        actor=actor,
        tenant_id=PLATFORM_TENANT_ID,
        action="i18n.languages.create",
        path=str(request.url.path),
        client_ip=request.client.host if request.client else "unknown",
        correlation_id=getattr(request.state, "request_id", None),
        entity="i18n",
        result="success",
        metadata={"code": language.get("code"), "enabled": language.get("enabled")},
    )
    return {"language": language}


@admin_router.patch("/languages/{code}")
def update_language_status(
    code: str,
    payload: UpdateLanguageStatusPayload,
    request: Request,
    actor: Annotated[str, Depends(_require_platform_tenant_context)],
    __: Annotated[None, Depends(permission_dependency("admin.i18n.manage"))],
) -> dict[str, dict[str, str | bool]]:
    try:
        language = set_language_enabled(code, payload.enabled)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    log_admin_action(
        actor=actor,
        tenant_id=PLATFORM_TENANT_ID,
        action="i18n.languages.update",
        path=str(request.url.path),
        client_ip=request.client.host if request.client else "unknown",
        correlation_id=getattr(request.state, "request_id", None),
        entity="i18n",
        result="success",
        metadata={"code": language.get("code"), "enabled": language.get("enabled")},
    )
    return {"language": language}


@admin_router.delete("/languages/{code}")
def remove_language(
    code: str,
    request: Request,
    actor: Annotated[str, Depends(_require_platform_tenant_context)],
    __: Annotated[None, Depends(permission_dependency("admin.i18n.manage"))],
) -> dict[str, str]:
    try:
        delete_language(code)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    log_admin_action(
        actor=actor,
        tenant_id=PLATFORM_TENANT_ID,
        action="i18n.languages.delete",
        path=str(request.url.path),
        client_ip=request.client.host if request.client else "unknown",
        correlation_id=getattr(request.state, "request_id", None),
        entity="i18n",
        result="success",
        metadata={"code": code},
    )
    return {"status": "deleted", "code": code}
