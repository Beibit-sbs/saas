from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.modules.auth.local_users_service import local_user_store
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
    search: str | None = Query(default=None),
    role: str | None = Query(default=None),
    language: str | None = Query(default=None),
) -> dict[str, list[dict[str, object]]]:
    return {
        "users": local_user_store.list_users(
            search=search,
            role=role,
            language=normalize_code(language) if language else None,
        )
    }


@router.post("")
def create_local_user(
    payload: CreateLocalUserPayload,
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.users.manage"))],
) -> dict[str, dict[str, object]]:
    normalized_language = _ensure_enabled_language(payload.default_language)

    created = local_user_store.create_user(
        login=payload.login,
        password=payload.password,
        display_name=payload.display_name,
        roles=payload.roles,
        default_language=normalized_language,
    )
    sync_user_roles_from_trusted_source(
        str(created["user_id"]),
        [str(value) for value in created.get("roles", [])],
    )
    return {"user": created}


@router.patch("/{user_id}")
def update_local_user(
    user_id: str,
    payload: UpdateLocalUserPayload,
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.users.manage"))],
) -> dict[str, dict[str, object]]:
    updated = local_user_store.update_user(
        user_id=user_id,
        display_name=payload.display_name,
        language=_ensure_enabled_language(payload.language) if payload.language is not None else None,
        roles=payload.roles,
    )
    sync_user_roles_from_trusted_source(
        str(updated["user_id"]),
        [str(value) for value in updated.get("roles", [])],
    )
    return {"user": updated}


@router.delete("/{user_id}")
def delete_local_user(
    user_id: str,
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.users.manage"))],
) -> dict[str, object]:
    local_user_store.delete_user(user_id)
    clear_user_roles_for_user(user_id)
    return {"status": "deleted", "user_id": user_id}


@router.post("/{user_id}/password")
def set_local_user_password(
    user_id: str,
    payload: UpdateLocalUserPasswordPayload,
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.users.manage"))],
) -> dict[str, str]:
    local_user_store.set_password(user_id, payload.password)
    return {"status": "updated"}
