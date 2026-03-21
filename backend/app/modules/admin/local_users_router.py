from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field

from app.core.tenant import get_current_tenant
from app.modules.auth.local_users_service import local_user_store
from app.modules.audit.service import log_admin_action
from app.modules.i18n.service import list_languages, normalize_code
from app.modules.rbac.service import clear_user_roles_for_user, sync_user_roles_from_trusted_source
from app.modules.rbac.security import get_actor, permission_dependency

router = APIRouter(prefix="/api/admin/local-users", tags=["local-users"])


class CreateLocalUserPayload(BaseModel):
    login: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=6, max_length=128)
    display_name: str = Field(min_length=1, max_length=128)
    roles: list[str] = Field(default_factory=lambda: ["student"])
    default_language: str = Field(default="ru", min_length=2, max_length=12)


class UpdateLocalUserPayload(BaseModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=128)
    language: str | None = Field(default=None, min_length=2, max_length=12)
    roles: list[str] | None = None


class UpdateLocalUserPasswordPayload(BaseModel):
    password: str = Field(min_length=6, max_length=128)


def _ensure_enabled_language(language: str) -> str:
    normalized_language = normalize_code(language)
    enabled_codes = {item["code"] for item in list_languages(enabled_only=True)}
    if normalized_language not in enabled_codes:
        raise HTTPException(status_code=400, detail="language is not enabled")
    return normalized_language


@router.get("")
def get_local_users(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.users.manage"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
    search: str | None = Query(default=None),
    role: str | None = Query(default=None),
    language: str | None = Query(default=None),
) -> dict[str, list[dict[str, object]]]:
    return {
        "users": local_user_store.list_users(
            search=search,
            role=role,
            language=normalize_code(language) if language else None,
            tenant_id=int(tenant["id"]),
        )
    }


@router.post("")
def create_local_user(
    payload: CreateLocalUserPayload,
    request: Request,
    actor: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.users.manage"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict[str, dict[str, object]]:
    normalized_language = _ensure_enabled_language(payload.default_language)

    created = local_user_store.create_user(
        login=payload.login,
        password=payload.password,
        display_name=payload.display_name,
        roles=payload.roles,
        default_language=normalized_language,
        tenant_id=int(tenant["id"]),
    )
    sync_user_roles_from_trusted_source(
        str(created["user_id"]),
        [str(value) for value in created.get("roles", [])],
    )
    log_admin_action(
        actor=actor,
        tenant_id=int(tenant["id"]),
        action="local_users.create",
        path=str(request.url.path),
        client_ip=request.client.host if request.client else "unknown",
        correlation_id=getattr(request.state, "request_id", None),
        entity="local_users",
        result="success",
        metadata={"user_id": str(created.get("user_id", "")), "login": str(created.get("login", ""))},
    )
    return {"user": created}


@router.patch("/{user_id}")
def update_local_user(
    user_id: str,
    payload: UpdateLocalUserPayload,
    request: Request,
    actor: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.users.manage"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict[str, dict[str, object]]:
    updated = local_user_store.update_user(
        user_id=user_id,
        tenant_id=int(tenant["id"]),
        display_name=payload.display_name,
        language=_ensure_enabled_language(payload.language) if payload.language is not None else None,
        roles=payload.roles,
    )
    sync_user_roles_from_trusted_source(
        str(updated["user_id"]),
        [str(value) for value in updated.get("roles", [])],
    )
    log_admin_action(
        actor=actor,
        tenant_id=int(tenant["id"]),
        action="local_users.update",
        path=str(request.url.path),
        client_ip=request.client.host if request.client else "unknown",
        correlation_id=getattr(request.state, "request_id", None),
        entity="local_users",
        result="success",
        metadata={"user_id": str(updated.get("user_id", ""))},
    )
    return {"user": updated}


@router.delete("/{user_id}")
def delete_local_user(
    user_id: str,
    request: Request,
    actor: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.users.manage"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict[str, object]:
    local_user_store.delete_user(user_id, tenant_id=int(tenant["id"]))
    clear_user_roles_for_user(user_id)
    log_admin_action(
        actor=actor,
        tenant_id=int(tenant["id"]),
        action="local_users.delete",
        path=str(request.url.path),
        client_ip=request.client.host if request.client else "unknown",
        correlation_id=getattr(request.state, "request_id", None),
        entity="local_users",
        result="success",
        metadata={"user_id": user_id},
    )
    return {"status": "deleted", "user_id": user_id}


@router.post("/{user_id}/password")
def set_local_user_password(
    user_id: str,
    payload: UpdateLocalUserPasswordPayload,
    request: Request,
    actor: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.users.manage"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict[str, str]:
    local_user_store.set_password(user_id, payload.password, tenant_id=int(tenant["id"]))
    log_admin_action(
        actor=actor,
        tenant_id=int(tenant["id"]),
        action="local_users.set_password",
        path=str(request.url.path),
        client_ip=request.client.host if request.client else "unknown",
        correlation_id=getattr(request.state, "request_id", None),
        entity="local_users",
        result="success",
        metadata={"user_id": user_id},
    )
    return {"status": "updated"}
