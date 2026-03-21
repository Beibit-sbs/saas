from typing import Annotated

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field

from app.core.tenant import get_current_tenant
from app.modules.audit.service import log_admin_action
from app.modules.feature_flags.service import list_flags, set_flag
from app.modules.rbac.security import get_actor, permission_dependency

router = APIRouter(prefix="/api/admin/feature-flags", tags=["feature-flags"])


class FeatureFlagPayload(BaseModel):
    key: str = Field(min_length=3, max_length=128)
    enabled: bool
    description: str | None = Field(default=None, max_length=256)
    scope: str = Field(default="global", min_length=3, max_length=64)


@router.get("")
def get_feature_flags(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.integrations.manage"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict[str, list[dict[str, object]]]:
    return {"flags": list_flags(tenant_id=int(tenant["id"]))}


@router.post("")
def upsert_feature_flag(
    payload: FeatureFlagPayload,
    request: Request,
    actor: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.integrations.manage"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict[str, dict[str, object]]:
    updated = set_flag(
        key=payload.key,
        enabled=payload.enabled,
        description=payload.description,
        scope=payload.scope,
        tenant_id=int(tenant["id"]),
    )
    log_admin_action(
        actor=actor,
        action="feature_flags.upsert",
        path=str(request.url.path),
        client_ip=request.client.host if request.client else "unknown",
        correlation_id=getattr(request.state, "request_id", None),
        entity="feature_flags",
        result="success",
        metadata={"flag_key": payload.key, "enabled": payload.enabled, "scope": payload.scope},
        tenant_id=int(tenant["id"]),
    )
    return {"flag": updated}
