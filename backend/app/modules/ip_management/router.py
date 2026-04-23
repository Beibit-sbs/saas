"""Phase VII-VII1: IP management router."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.tenant import get_current_tenant
from app.modules.rbac.security import get_actor, permission_dependency
from app.modules.ip_management.schemas import (
    IpAssetCreatePayload,
    IpAssetItemResponse,
    IpAssetListResponse,
    IpManagementBrainContextResponse,
)
from app.modules.ip_management.service import (
    create_ip_asset,
    get_ip_management_brain_context,
    list_ip_assets,
)

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
        records=list_ip_assets(int(tenant["id"]), ip_type=ip_type, status=status)
    )


@router.post("/assets", response_model=IpAssetItemResponse, status_code=201)
def create_ip_asset_endpoint(
    payload: IpAssetCreatePayload,
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("research.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> IpAssetItemResponse:
    return IpAssetItemResponse(
        record=create_ip_asset(payload.model_dump(), int(tenant["id"]))
    )


@router.get("/brain-context", response_model=IpManagementBrainContextResponse)
def get_ip_management_brain_context_endpoint(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("research.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> IpManagementBrainContextResponse:
    return IpManagementBrainContextResponse.model_validate(
        get_ip_management_brain_context(int(tenant["id"]))
    )
