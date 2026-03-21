from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field

from app.core.tenant import get_current_tenant
from app.modules.audit.service import log_admin_action
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
_PLATFORM_TENANT_ID = 1
_PLATFORM_ONLY_ROLES = {"superadmin"}


def _actor_is_platform_admin(actor: str) -> bool:
    # Deliberately does NOT check JWT claim roles — those are tenant-scoped.
    # A tenant superadmin MUST NOT gain platform control-plane access.
    return is_platform_admin(actor)


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
    target_tenant_id = tenant_id if tenant_id is not None and _actor_is_platform_admin(actor) else current_tenant_id
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
    actor_is_platform_admin = _actor_is_platform_admin(actor)
    if payload.tenant_id is not None and payload.tenant_id != current_tenant_id and not actor_is_platform_admin:
        raise HTTPException(status_code=403, detail="cross-tenant role management requires platform admin")
    target_tenant_id = payload.tenant_id if payload.tenant_id is not None and actor_is_platform_admin else current_tenant_id
    normalized_role_name = payload.name.strip().lower()
    if normalized_role_name in _PLATFORM_ONLY_ROLES and target_tenant_id != _PLATFORM_TENANT_ID:
        raise HTTPException(status_code=403, detail="role 'superadmin' is reserved for the platform tenant")
    try:
        result = {"role": add_or_update_role_for_tenant(target_tenant_id, payload.name, payload.permissions)}
        log_admin_action(
            actor=actor,
            action="rbac.role.upsert",
            path=str(request.url.path),
            client_ip=request.client.host if request.client else "unknown",
            correlation_id=getattr(request.state, "request_id", None),
            entity="rbac_roles",
            result="success",
            metadata={"role": payload.name, "permissions": payload.permissions},
            tenant_id=target_tenant_id,
        )
        return result
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/assign")
def assign_user_role(
    request: Request,
    payload: AssignRolePayload,
    actor: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.roles.manage"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict[str, object]:
    current_tenant_id = int(tenant["id"])
    target_tenant_id = payload.tenant_id if payload.tenant_id is not None and _actor_is_platform_admin(actor) else current_tenant_id
    try:
        assigned = assign_role_to_user(target_tenant_id, payload.user_id, payload.role)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    log_admin_action(
        actor=actor,
        action="rbac.assignment.create",
        path=str(request.url.path),
        client_ip=request.client.host if request.client else "unknown",
        correlation_id=getattr(request.state, "request_id", None),
        entity="rbac_assignments",
        result="success",
        metadata={"user_id": payload.user_id, "role": payload.role},
        tenant_id=target_tenant_id,
    )
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
    target_tenant_id = tenant_id if tenant_id is not None and _actor_is_platform_admin(actor) else current_tenant_id
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
    target_tenant_id = tenant_id if tenant_id is not None and _actor_is_platform_admin(actor) else current_tenant_id
    try:
        result = revoke_role_for_tenant(tenant_id=target_tenant_id, user_id=user_id, role=role)
        log_admin_action(
            actor=actor,
            action="rbac.assignment.delete",
            path=str(request.url.path),
            client_ip=request.client.host if request.client else "unknown",
            correlation_id=getattr(request.state, "request_id", None),
            entity="rbac_assignments",
            result="success",
            metadata={"user_id": user_id, "role": role},
            tenant_id=target_tenant_id,
        )
        return result
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
