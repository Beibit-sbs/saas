from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from app.core.tenant import get_current_tenant
from app.modules.audit.service import log_admin_action
from app.modules.identity.service import list_identity_providers, upsert_identity_provider
from app.modules.rbac.security import get_actor, permission_dependency


router = APIRouter(prefix="/api/admin/identity", tags=["identity-admin"])


class IdentityProviderPayload(BaseModel):
    provider: str = Field(min_length=2, max_length=64)
    type: str = Field(min_length=4, max_length=16)
    enabled: bool = True
    issuer: str | None = None
    client_id: str | None = None
    client_secret: str | None = None
    redirect_uri: str | None = None
    scopes: list[str] = Field(default_factory=lambda: ["openid", "profile", "email"])
    saml_metadata_url: str | None = None
    saml_sso_url: str | None = None
    saml_entity_id: str | None = None
    tenant_scope: str = Field(default="tenant", min_length=6, max_length=16)


@router.get("/providers")
def get_identity_providers(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.integrations.manage"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict[str, list[dict[str, object]]]:
    return {"providers": list_identity_providers(tenant_id=int(tenant["id"]))}


@router.put("/providers/{provider}")
def put_identity_provider(
    provider: str,
    payload: IdentityProviderPayload,
    request: Request,
    actor: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.integrations.manage"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict[str, dict[str, object]]:
    if provider.strip().lower() != payload.provider.strip().lower():
        raise HTTPException(status_code=400, detail="provider path mismatch")
    try:
        row = upsert_identity_provider(tenant_id=int(tenant["id"]), payload=payload.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    log_admin_action(
        actor=actor,
        tenant_id=int(tenant["id"]),
        action="identity.provider.upsert",
        path=str(request.url.path),
        client_ip=request.client.host if request.client else "unknown",
        correlation_id=getattr(request.state, "request_id", None),
        entity="identity",
        result="success",
        metadata={"provider": row.get("provider"), "type": row.get("type"), "enabled": row.get("enabled")},
    )
    return {"provider": row}
