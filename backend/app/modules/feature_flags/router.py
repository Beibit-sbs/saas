from typing import Annotated

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field

from app.core.tenant import get_current_tenant
from app.modules.audit.service import log_admin_action
from app.modules.rbac.security import get_actor, permission_dependency
from app.platform.feature_flags import service as platform_flags_service

router = APIRouter(prefix="/api/admin/feature-flags", tags=["feature-flags"])


def _split_legacy_key(composite_key: str) -> tuple[str, str]:
    """Split a flat legacy key 'module.rest.of.key' into (module, rest.of.key)."""
    parts = composite_key.split(".", 1)
    if len(parts) == 2 and parts[0] and parts[1]:
        return parts[0], parts[1]
    return "global", composite_key


def _to_legacy_dict(row: dict[str, object]) -> dict[str, object]:
    module = str(row.get("module", ""))
    key = str(row.get("key", ""))
    composite = f"{module}.{key}" if module and module != "global" else key
    return {
        "key": composite,
        "description": str(row.get("description", "")),
        "enabled": bool(row.get("enabled", False)),
        "scope": str(row.get("scope", "tenant")),
        "rollout_percentage": int(row.get("rollout_percentage", 100)),
        "updated_at": str(row.get("updated_at", "")),
    }


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
    rows = platform_flags_service.list_tenant_features(int(tenant["id"]))
    return {"flags": [_to_legacy_dict(row) for row in rows]}


@router.post("")
def upsert_feature_flag(
    payload: FeatureFlagPayload,
    request: Request,
    actor: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.integrations.manage"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict[str, dict[str, object]]:
    module, key = _split_legacy_key(payload.key)
    row = platform_flags_service.set_tenant_feature(int(tenant["id"]), module, key, payload.enabled)
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
    return {"flag": _to_legacy_dict(row)}

