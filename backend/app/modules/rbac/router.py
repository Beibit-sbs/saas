from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field

from app.core.tenant import get_current_tenant
from app.modules.rbac.security import get_actor, permission_dependency
from app.modules.rbac.service import (
    add_or_update_role_for_tenant,
    assign_role_to_user,
    is_platform_admin,
    list_roles_for_tenant,
    list_user_role_assignments_for_tenant,
    revoke_role_for_tenant,
)

router = APIRouter(prefix="/api/admin/rbac", tags=["rbac"])


def _actor_is_platform_admin(actor: str, request: Request) -> bool:
    claims = getattr(request.state, "auth_claims", None)
    claim_roles = [r.strip() for r in getattr(claims, "roles", []) if str(r).strip()]
    return "superadmin" in claim_roles or is_platform_admin(actor)


class RolePayload(BaseModel):
    name: str = Field(min_length=2, max_length=64)
    permissions: List[str] = Field(default_factory=list)
    tenant_id: int | None = Field(default=None, gt=0)


class AssignRolePayload(BaseModel):
    user_id: str = Field(min_length=1)
    role: str = Field(min_length=2)
    tenant_id: int | None = Field(default=None, gt=0)


@router.get("/roles")
def get_roles(
    request: Request,
    actor: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.roles.manage"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
    tenant_id: int | None = Query(default=None, gt=0),
) -> dict[str, dict[str, list[str]]]:
    current_tenant_id = int(tenant["id"])
    target_tenant_id = tenant_id if tenant_id is not None and _actor_is_platform_admin(actor, request) else current_tenant_id
    return {"roles": list_roles_for_tenant(target_tenant_id)}


@router.post("/roles")
def upsert_role(
    request: Request,
    payload: RolePayload,
    actor: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.roles.manage"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict[str, dict[str, list[str]]]:
    current_tenant_id = int(tenant["id"])
    target_tenant_id = payload.tenant_id if payload.tenant_id is not None and _actor_is_platform_admin(actor, request) else current_tenant_id
    return {"role": add_or_update_role_for_tenant(target_tenant_id, payload.name, payload.permissions)}


@router.post("/assign")
def assign_user_role(
    request: Request,
    payload: AssignRolePayload,
    actor: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.roles.manage"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict[str, object]:
    current_tenant_id = int(tenant["id"])
    target_tenant_id = payload.tenant_id if payload.tenant_id is not None and _actor_is_platform_admin(actor, request) else current_tenant_id
    try:
        assigned = assign_role_to_user(target_tenant_id, payload.user_id, payload.role)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return assigned


@router.get("/assignments")
def get_role_assignments(
    request: Request,
    actor: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.roles.manage"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
    user_id: str | None = Query(default=None),
    role: str | None = Query(default=None),
    tenant_id: int | None = Query(default=None, gt=0),
) -> dict[str, list[dict[str, object]]]:
    current_tenant_id = int(tenant["id"])
    target_tenant_id = tenant_id if tenant_id is not None and _actor_is_platform_admin(actor, request) else current_tenant_id
    return {
        "assignments": list_user_role_assignments_for_tenant(
            target_tenant_id,
            user_id=user_id,
            role=role,
        )
    }


@router.delete("/assignments/{user_id}/{role}")
def delete_role_assignment(
    request: Request,
    user_id: str,
    role: str,
    actor: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.roles.manage"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
    tenant_id: int | None = Query(default=None, gt=0),
) -> dict[str, object]:
    current_tenant_id = int(tenant["id"])
    target_tenant_id = tenant_id if tenant_id is not None and _actor_is_platform_admin(actor, request) else current_tenant_id
    try:
        return revoke_role_for_tenant(tenant_id=target_tenant_id, user_id=user_id, role=role)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
