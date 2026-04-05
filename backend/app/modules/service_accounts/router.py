from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from app.core.tenant import get_current_tenant
from app.modules.audit.service import log_admin_action
from app.modules.auth.token_service import create_service_token
from app.modules.rbac.security import get_actor, permission_dependency
from app.modules.rbac.service import is_platform_admin
from app.modules.service_accounts.service import (
    create_service_account,
    get_service_account,
    issue_service_token_material,
    list_service_accounts,
    revoke_service_account,
)


router = APIRouter(prefix="/api/admin/service-accounts", tags=["service-accounts"])


class ServiceAccountCreatePayload(BaseModel):
    name: str = Field(min_length=2, max_length=128)
    permissions: list[str] = Field(min_length=1)
    platform_global: bool = False


class ServiceAccountTokenPayload(BaseModel):
    secret: str = Field(min_length=8, max_length=256)


@router.get("")
def get_service_accounts(
    actor: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.integrations.manage"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict[str, list[dict[str, object]]]:
    accounts = list_service_accounts(tenant_id=int(tenant["id"]))
    if not is_platform_admin(actor):
        accounts = [item for item in accounts if not bool(item.get("platform_global", False))]
    return {"accounts": accounts}


@router.post("")
def post_service_account(
    payload: ServiceAccountCreatePayload,
    request: Request,
    actor: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.integrations.manage"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict[str, dict[str, object]]:
    if payload.platform_global and not is_platform_admin(actor):
        raise HTTPException(status_code=403, detail="platform-global service account requires platform admin")
    try:
        account = create_service_account(
            tenant_id=int(tenant["id"]),
            name=payload.name,
            permissions=payload.permissions,
            platform_global=payload.platform_global,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    log_admin_action(
        actor=actor,
        tenant_id=int(tenant["id"]),
        action="service_accounts.create",
        path=str(request.url.path),
        client_ip=request.client.host if request.client else "unknown",
        correlation_id=getattr(request.state, "request_id", None),
        entity="service_accounts",
        result="success",
        metadata={"account_id": account.get("account_id"), "platform_global": account.get("platform_global")},
    )
    return {"account": account}


@router.post("/{account_id}/token")
def post_service_account_token(
    account_id: str,
    payload: ServiceAccountTokenPayload,
    request: Request,
    actor: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.integrations.manage"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict[str, str]:
    account = get_service_account(tenant_id=int(tenant["id"]), account_id=account_id)
    if account is None:
        raise HTTPException(status_code=404, detail="service account not found")
    if bool(account.get("platform_global", False)) and not is_platform_admin(actor):
        raise HTTPException(status_code=403, detail="platform-global service account requires platform admin")
    try:
        material = issue_service_token_material(
            tenant_id=int(tenant["id"]),
            account_id=account_id,
            secret=payload.secret,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    token = create_service_token(
        service_account_id=str(material["account_id"]),
        permissions=[str(item) for item in material["permissions"]],
        tenant_id=int(tenant["id"]),
        platform_global=bool(material.get("platform_global", False)),
    )
    log_admin_action(
        actor=actor,
        tenant_id=int(tenant["id"]),
        action="service_accounts.token.issue",
        path=str(request.url.path),
        client_ip=request.client.host if request.client else "unknown",
        correlation_id=getattr(request.state, "request_id", None),
        entity="service_accounts",
        result="success",
        metadata={"account_id": account_id},
    )
    return {"token": token}


@router.post("/{account_id}/revoke")
def post_service_account_revoke(
    account_id: str,
    request: Request,
    actor: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.integrations.manage"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict[str, object]:
    account = get_service_account(tenant_id=int(tenant["id"]), account_id=account_id)
    if account is None:
        raise HTTPException(status_code=404, detail="service account not found or already revoked")
    if bool(account.get("platform_global", False)) and not is_platform_admin(actor):
        raise HTTPException(status_code=403, detail="platform-global service account requires platform admin")
    revoked = revoke_service_account(tenant_id=int(tenant["id"]), account_id=account_id)
    if not revoked:
        raise HTTPException(status_code=404, detail="service account not found or already revoked")

    log_admin_action(
        actor=actor,
        tenant_id=int(tenant["id"]),
        action="service_accounts.revoke",
        path=str(request.url.path),
        client_ip=request.client.host if request.client else "unknown",
        correlation_id=getattr(request.state, "request_id", None),
        entity="service_accounts",
        result="success",
        metadata={"account_id": account_id},
    )
    return {"revoked": True, "account_id": account_id}
