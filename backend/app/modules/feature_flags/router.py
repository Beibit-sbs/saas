from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request

from app.core.tenant import get_current_tenant
from app.modules.audit.service import log_admin_action
from app.modules.feature_flags.schemas import FeatureFlagPatchPayload, FeatureFlagPayload
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


@router.get("/{key:path}")
def get_feature_flag(
    key: str,
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.integrations.manage"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict[str, dict[str, object]]:
    module, flag_key = _split_legacy_key(key)
    row = platform_flags_service.get_tenant_feature(int(tenant["id"]), module, flag_key)
    if row is None:
        raise HTTPException(status_code=404, detail=f"Feature flag '{key}' not found")
    return {"flag": _to_legacy_dict(row)}


@router.patch("/{key:path}")
def patch_feature_flag(
    key: str,
    payload: FeatureFlagPatchPayload,
    request: Request,
    actor: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.integrations.manage"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict[str, dict[str, object]]:
    module, flag_key = _split_legacy_key(key)
    existing = platform_flags_service.get_tenant_feature(int(tenant["id"]), module, flag_key)
    if existing is None:
        raise HTTPException(status_code=404, detail=f"Feature flag '{key}' not found")
    new_enabled = payload.enabled if payload.enabled is not None else bool(existing.get("enabled"))
    row = platform_flags_service.set_tenant_feature(int(tenant["id"]), module, flag_key, new_enabled)
    log_admin_action(
        actor=actor,
        action="feature_flags.patch",
        path=str(request.url.path),
        client_ip=request.client.host if request.client else "unknown",
        correlation_id=getattr(request.state, "request_id", None),
        entity="feature_flags",
        result="success",
        metadata={"flag_key": key, "enabled": new_enabled},
        tenant_id=int(tenant["id"]),
    )
    return {"flag": _to_legacy_dict(row)}


@router.delete("/{key:path}", status_code=204)
def delete_feature_flag(
    key: str,
    request: Request,
    actor: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.integrations.manage"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> None:
    module, flag_key = _split_legacy_key(key)
    deleted = platform_flags_service.delete_tenant_feature(int(tenant["id"]), module, flag_key)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Feature flag '{key}' not found")
    log_admin_action(
        actor=actor,
        action="feature_flags.delete",
        path=str(request.url.path),
        client_ip=request.client.host if request.client else "unknown",
        correlation_id=getattr(request.state, "request_id", None),
        entity="feature_flags",
        result="success",
        metadata={"flag_key": key},
        tenant_id=int(tenant["id"]),
    )


