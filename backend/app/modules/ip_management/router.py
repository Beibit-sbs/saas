"""Phase VII-VII1: IP management router."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.core.module_helpers.service_validation import DomainValidationError
from app.core.tenant import get_current_tenant
from app.modules.rbac.security import get_actor, permission_dependency
from app.modules.ip_management.schemas import (
    IpAssetCreatePayload,
    IpAssetItemResponse,
    IpAssetListResponse,
    IpManagementBrainContextResponse,
)
import app.modules.ip_management.service as _svc

router = APIRouter(prefix="/api/admin/ip-management", tags=["ip-management"])


@router.get("/assets", response_model=IpAssetListResponse)
def list_ip_assets_endpoint(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("research.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
    ip_type: str | None = None,
    status: str | None = None,
) -> IpAssetListResponse:
    return IpAssetListResponse(
        records=_svc.list_ip_assets(int(tenant["id"]), ip_type=ip_type, status=status)
    )


@router.post("/assets", response_model=IpAssetItemResponse, status_code=201)
def create_ip_asset_endpoint(
    payload: IpAssetCreatePayload,
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("research.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> IpAssetItemResponse:
    try:
        return IpAssetItemResponse(
            record=_svc.create_ip_asset(payload.model_dump(), int(tenant["id"]))
        )
    except (ValueError, DomainValidationError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/brain-context", response_model=IpManagementBrainContextResponse)
def get_ip_management_brain_context_endpoint(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("research.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> IpManagementBrainContextResponse:
    return IpManagementBrainContextResponse.model_validate(
        _svc.get_ip_management_brain_context(int(tenant["id"]))
    )
