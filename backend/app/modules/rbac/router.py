from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.modules.rbac.security import get_actor, permission_dependency
from app.modules.rbac.service import add_or_update_role, assign_role, list_roles, list_user_role_assignments, revoke_role

router = APIRouter(prefix="/api/admin/rbac", tags=["rbac"])


class RolePayload(BaseModel):
    name: str = Field(min_length=2, max_length=64)
    permissions: List[str] = Field(default_factory=list)


class AssignRolePayload(BaseModel):
    user_id: str = Field(min_length=1)
    role: str = Field(min_length=2)


@router.get("/roles")
def get_roles(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.roles.manage"))],
) -> dict[str, dict[str, list[str]]]:
    return {"roles": list_roles()}


@router.post("/roles")
def upsert_role(
    payload: RolePayload,
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.roles.manage"))],
) -> dict[str, dict[str, list[str]]]:
    return {"role": add_or_update_role(payload.name, payload.permissions)}


@router.post("/assign")
def assign_user_role(
    payload: AssignRolePayload,
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.roles.manage"))],
) -> dict[str, object]:
    try:
        assigned = assign_role(payload.user_id, payload.role)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return assigned


@router.get("/assignments")
def get_role_assignments(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.roles.manage"))],
    user_id: str | None = Query(default=None),
    role: str | None = Query(default=None),
) -> dict[str, list[dict[str, object]]]:
    return {"assignments": list_user_role_assignments(user_id=user_id, role=role)}


@router.delete("/assignments/{user_id}/{role}")
def delete_role_assignment(
    user_id: str,
    role: str,
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.roles.manage"))],
) -> dict[str, object]:
    try:
        return revoke_role(user_id=user_id, role=role)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
