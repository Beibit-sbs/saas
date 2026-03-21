from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Request

from app.modules.audit.service import log_admin_action
from app.modules.rbac.security import get_actor, permission_dependency, resolve_current_user_claims
from app.modules.rbac.service import is_platform_admin
from app.modules.tenants.schemas import (
    TenantCreatePayload,
    TenantDeleteResponse,
    TenantItemResponse,
    TenantListResponse,
    TenantUpdatePayload,
)
from app.modules.tenants.service import create_tenant, delete_tenant, list_tenants, update_tenant

router = APIRouter(prefix="/api/admin/tenants", tags=["tenants"])


def _require_platform_tenant_context(
    request: Request,
    actor: Annotated[str, Depends(get_actor)],
    authorization: Annotated[str | None, Header()] = None,
) -> str:
    claims = resolve_current_user_claims(request, authorization)
    if int(claims.tenant_id) == 1:
        return actor
    if is_platform_admin(actor):
        return actor
    raise HTTPException(status_code=403, detail="platform tenant context required")


@router.get("", response_model=TenantListResponse)
def get_tenants(
    _: Annotated[str, Depends(_require_platform_tenant_context)],
    __: Annotated[None, Depends(permission_dependency("admin.tenants.read"))],
) -> TenantListResponse:
    return {"tenants": list_tenants()}


@router.post("", response_model=TenantItemResponse)
def create_tenant_endpoint(
    payload: TenantCreatePayload,
    request: Request,
    actor: Annotated[str, Depends(_require_platform_tenant_context)],
    _: Annotated[None, Depends(permission_dependency("admin.tenants.write"))],
) -> TenantItemResponse:
    try:
        tenant = create_tenant(payload.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    log_admin_action(
        actor=actor,
        action="tenants.create",
        path=str(request.url.path),
        client_ip=request.client.host if request.client else "unknown",
        correlation_id=getattr(request.state, "request_id", None),
        entity="app_tenants",
        result="success",
        metadata={"id": tenant["id"], "slug": tenant["slug"]},
    )
    return {"tenant": tenant}


@router.put("/{tenant_id}", response_model=TenantItemResponse)
def update_tenant_endpoint(
    tenant_id: int,
    payload: TenantUpdatePayload,
    request: Request,
    actor: Annotated[str, Depends(_require_platform_tenant_context)],
    _: Annotated[None, Depends(permission_dependency("admin.tenants.write"))],
) -> TenantItemResponse:
    try:
        tenant = update_tenant(tenant_id, payload.model_dump(exclude_none=True))
    except ValueError as exc:
        detail = str(exc)
        status = 404 if "not found" in detail else 400
        raise HTTPException(status_code=status, detail=detail) from exc

    log_admin_action(
        actor=actor,
        action="tenants.update",
        path=str(request.url.path),
        client_ip=request.client.host if request.client else "unknown",
        correlation_id=getattr(request.state, "request_id", None),
        entity="app_tenants",
        result="success",
        metadata={"id": tenant["id"], "slug": tenant["slug"]},
    )
    return {"tenant": tenant}


@router.delete("/{tenant_id}", response_model=TenantDeleteResponse)
def delete_tenant_endpoint(
    tenant_id: int,
    request: Request,
    actor: Annotated[str, Depends(_require_platform_tenant_context)],
    _: Annotated[None, Depends(permission_dependency("admin.tenants.write"))],
) -> TenantDeleteResponse:
    try:
        tenant = delete_tenant(tenant_id)
    except ValueError as exc:
        detail = str(exc)
        status = 404 if "not found" in detail else 400
        raise HTTPException(status_code=status, detail=detail) from exc

    log_admin_action(
        actor=actor,
        action="tenants.delete",
        path=str(request.url.path),
        client_ip=request.client.host if request.client else "unknown",
        correlation_id=getattr(request.state, "request_id", None),
        entity="app_tenants",
        result="success",
        metadata={"id": tenant["id"], "slug": tenant["slug"]},
    )
    return {"deleted": True, "tenant": tenant}
