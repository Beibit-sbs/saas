from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field

from app.core.tenant import get_current_tenant
from app.modules.audit.service import log_admin_action
from app.modules.rbac.security import get_actor, permission_dependency
from app.modules.rbac.service import (
    add_or_update_role_for_tenant_with_replay,
    assign_role_to_user,
    is_platform_admin,
    list_roles_for_tenant,
    list_user_role_assignments_for_tenant,
    revoke_role_for_tenant,
    get_role_hierarchy_level,
    get_highest_role_level,
    get_user_roles_for_tenant,
)

router = APIRouter(prefix="/api/admin/rbac", tags=["rbac"])
_PLATFORM_TENANT_ID = 1
_PLATFORM_ONLY_ROLES = {"superadmin"}


def _actor_is_platform_admin(actor: str) -> bool:
    # Deliberately does NOT check JWT claim roles — those are tenant-scoped.
    # A tenant superadmin MUST NOT gain platform control-plane access.
    return is_platform_admin(actor)


def _enforce_role_mutation_guard(
    *,
    actor: str,
    target_user_id: str | None,
    role_name: str,
    target_tenant_id: int,
    actor_claim_roles: List[str] | None = None,
) -> None:
    normalized_actor = str(actor or "").strip()
    normalized_target_user = str(target_user_id or "").strip()
    normalized_role = str(role_name or "").strip().lower()

    # GOVERNANCE.1: Prevent self-escalation
    if normalized_actor and normalized_target_user and normalized_actor == normalized_target_user:
        raise HTTPException(status_code=403, detail="self-role modification forbidden")

    # GOVERNANCE.2: Platform-only roles (superadmin) can only be assigned in platform tenant
    # and only by platform admins
    if normalized_role in _PLATFORM_ONLY_ROLES:
        if target_tenant_id != _PLATFORM_TENANT_ID:
            raise HTTPException(status_code=403, detail="role 'superadmin' is reserved for the platform tenant")
        if not _actor_is_platform_admin(actor):
            raise HTTPException(status_code=403, detail="platform-only role management requires platform admin")
        return  # Platform admin can assign any role

    # GOVERNANCE.3: Role hierarchy validation
    # Prevent users from assigning roles higher or equal to their own level
    # Exception: platform admins can assign any role
    if _actor_is_platform_admin(actor):
        return  # Platform admin bypass

    # Get actor's current roles in target tenant
    actor_roles = get_user_roles_for_tenant(normalized_actor, target_tenant_id)
    if not actor_roles and actor_claim_roles:
        actor_roles = sorted({str(item).strip().lower() for item in actor_claim_roles if str(item).strip()})
    actor_max_level = get_highest_role_level(actor_roles)

    # Get target role's privilege level
    target_role_level = get_role_hierarchy_level(normalized_role)

    # Actor can only assign roles with lower privilege than their highest role
    if target_role_level >= actor_max_level:
        raise HTTPException(
            status_code=403,
            detail=f"cannot assign role '{normalized_role}' (level {target_role_level}): "
                   f"your maximum privilege level is {actor_max_level}"
        )


class RolePayload(BaseModel):
    name: str = Field(min_length=2, max_length=64)
    permissions: List[str] = Field(default_factory=list)
    tenant_id: int | None = Field(default=None, gt=0)


class AssignRolePayload(BaseModel):
    user_id: str = Field(min_length=1)
    role: str = Field(min_length=2)
    tenant_id: int | None = Field(default=None, gt=0)


class RoleUpsertResponse(BaseModel):
    role: dict[str, list[str]]
    idempotent_replay: bool


class RoleAssignResponse(BaseModel):
    user_id: str
    roles: list[str]
    idempotent_replay: bool


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


@router.post("/roles", response_model=RoleUpsertResponse)
def upsert_role(
    request: Request,
    payload: RolePayload,
    actor: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.roles.manage"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> RoleUpsertResponse:
    current_tenant_id = int(tenant["id"])
    actor_is_platform_admin = _actor_is_platform_admin(actor)
    if payload.tenant_id is not None and payload.tenant_id != current_tenant_id and not actor_is_platform_admin:
        raise HTTPException(status_code=403, detail="cross-tenant role management requires platform admin")
    target_tenant_id = payload.tenant_id if payload.tenant_id is not None and actor_is_platform_admin else current_tenant_id
    normalized_role_name = payload.name.strip().lower()
    _enforce_role_mutation_guard(
        actor=actor,
        target_user_id=None,
        role_name=normalized_role_name,
        target_tenant_id=target_tenant_id,
        actor_claim_roles=getattr(getattr(request.state, "auth_claims", None), "roles", None),
    )
    if normalized_role_name in _PLATFORM_ONLY_ROLES and target_tenant_id != _PLATFORM_TENANT_ID:
        raise HTTPException(status_code=403, detail="role 'superadmin' is reserved for the platform tenant")
    try:
        result = add_or_update_role_for_tenant_with_replay(target_tenant_id, payload.name, payload.permissions)
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
        return RoleUpsertResponse.model_validate(result)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/assign", response_model=RoleAssignResponse)
def assign_user_role(
    request: Request,
    payload: AssignRolePayload,
    actor: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.roles.manage"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> RoleAssignResponse:
    current_tenant_id = int(tenant["id"])
    target_tenant_id = payload.tenant_id if payload.tenant_id is not None and _actor_is_platform_admin(actor) else current_tenant_id

    try:
        # Governance validation — role hierarchy, self-escalation checks
        _enforce_role_mutation_guard(
            actor=actor,
            target_user_id=payload.user_id,
            role_name=payload.role,
            target_tenant_id=target_tenant_id,
            actor_claim_roles=getattr(getattr(request.state, "auth_claims", None), "roles", None),
        )

        # Service call
        before_roles = get_user_roles_for_tenant(payload.user_id, target_tenant_id)
        assigned = assign_role_to_user(target_tenant_id, payload.user_id, payload.role)
        replayed = sorted(before_roles) == sorted(assigned.get("roles", []))

        # Log success
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
        return RoleAssignResponse(
            user_id=str(assigned.get("user_id", payload.user_id)),
            roles=[str(item) for item in assigned.get("roles", [])],
            idempotent_replay=replayed,
        )
    except HTTPException as exc:
        # Log governance denials (403, 400, etc)
        log_admin_action(
            actor=actor,
            action="rbac.assignment.create",
            path=str(request.url.path),
            client_ip=request.client.host if request.client else "unknown",
            correlation_id=getattr(request.state, "request_id", None),
            entity="rbac_assignments",
            result="denied",
            metadata={
                "user_id": payload.user_id,
                "role": payload.role,
                "reason": exc.detail,
            },
            tenant_id=target_tenant_id,
        )
        raise
    except (PermissionError, ValueError) as exc:
        # Log service-layer errors
        log_admin_action(
            actor=actor,
            action="rbac.assignment.create",
            path=str(request.url.path),
            client_ip=request.client.host if request.client else "unknown",
            correlation_id=getattr(request.state, "request_id", None),
            entity="rbac_assignments",
            result="error",
            metadata={
                "user_id": payload.user_id,
                "role": payload.role,
                "error": str(exc),
            },
            tenant_id=target_tenant_id,
        )
        if isinstance(exc, PermissionError):
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        raise HTTPException(status_code=400, detail=str(exc)) from exc


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
    _enforce_role_mutation_guard(
        actor=actor,
        target_user_id=user_id,
        role_name=role,
        target_tenant_id=target_tenant_id,
        actor_claim_roles=getattr(getattr(request.state, "auth_claims", None), "roles", None),
    )
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
