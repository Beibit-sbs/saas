from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.modules.i18n.service import add_language, delete_language, list_language_catalog, list_languages, set_language_enabled
from app.modules.rbac.security import get_actor, permission_dependency

public_router = APIRouter(prefix="/api/i18n", tags=["i18n"])
admin_router = APIRouter(prefix="/api/admin/i18n", tags=["i18n-admin"])


class AddLanguagePayload(BaseModel):
    code: str = Field(min_length=2, max_length=20)
    name: str = Field(min_length=1, max_length=120)
    native_name: str | None = Field(default=None, max_length=120)


class UpdateLanguageStatusPayload(BaseModel):
    enabled: bool


@public_router.get("/languages")
def get_public_languages() -> dict[str, list[dict[str, str | bool]]]:
    return {"languages": list_languages(enabled_only=True)}


@public_router.get("/catalog")
def get_language_catalog() -> dict[str, list[dict[str, str]]]:
    return {"languages": list_language_catalog()}


@admin_router.get("/languages")
def get_admin_languages(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.i18n.manage"))],
) -> dict[str, list[dict[str, str | bool]]]:
    return {"languages": list_languages(enabled_only=False)}


@admin_router.post("/languages")
def create_language(
    payload: AddLanguagePayload,
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.i18n.manage"))],
) -> dict[str, dict[str, str | bool]]:
    try:
        language = add_language(payload.code, payload.name, payload.native_name)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {"language": language}


@admin_router.patch("/languages/{code}")
def update_language_status(
    code: str,
    payload: UpdateLanguageStatusPayload,
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.i18n.manage"))],
) -> dict[str, dict[str, str | bool]]:
    try:
        language = set_language_enabled(code, payload.enabled)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {"language": language}


@admin_router.delete("/languages/{code}")
def remove_language(
    code: str,
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.i18n.manage"))],
) -> dict[str, str]:
    try:
        delete_language(code)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {"status": "deleted", "code": code}
