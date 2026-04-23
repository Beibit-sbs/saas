"""Phase XI-XI2: Asset Inventory router."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.core.tenant import get_current_tenant
from app.modules.asset_inventory.schemas import (
    AssetCategory,
    AssetCondition,
    AssetItemCreateSchema,
    AssetItemResponseSchema,
    AssetItemStatusUpdateSchema,
    AssetListResponseSchema,
    AssetStatus,
    DepreciationRecordCreateSchema,
    DepreciationRecordItemResponseSchema,
    DepreciationRecordListResponseSchema,
    DepreciationStatus,
)
from app.modules.asset_inventory.service import (
    create_asset_item,
    create_depreciation_record,
    get_asset_item,
    get_depreciation_record,
    list_asset_items,
    list_depreciation_records,
    update_asset_item_status,
)
from app.modules.rbac.security import get_actor, permission_dependency


router = APIRouter(prefix="/api/admin/asset-inventory", tags=["asset-inventory"])


@router.get("/items", response_model=AssetListResponseSchema)
def list_asset_items_endpoint(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("asset_inventory.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
    status: AssetStatus | None = None,
    category: AssetCategory | None = None,
    condition: AssetCondition | None = None,
) -> AssetListResponseSchema:
    items = list_asset_items(int(tenant["id"]), status=status, category=category, condition=condition)
    return AssetListResponseSchema(items=items)


@router.post("/items", response_model=AssetItemResponseSchema)
def create_asset_item_endpoint(
    payload: AssetItemCreateSchema,
    actor: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("asset_inventory.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> AssetItemResponseSchema:
    item = create_asset_item(int(tenant["id"]), payload, actor)
    return AssetItemResponseSchema(item=item)


@router.get("/items/{asset_id}", response_model=AssetItemResponseSchema)
def get_asset_item_endpoint(
    asset_id: int,
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("asset_inventory.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> AssetItemResponseSchema:
    item = get_asset_item(int(tenant["id"]), asset_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Asset not found")
    return AssetItemResponseSchema(item=item)


@router.patch("/items/{asset_id}/status", response_model=AssetItemResponseSchema)
def update_asset_item_status_endpoint(
    asset_id: int,
    payload: AssetItemStatusUpdateSchema,
    actor: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("asset_inventory.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> AssetItemResponseSchema:
    item = update_asset_item_status(int(tenant["id"]), asset_id, payload, actor)
    if item is None:
        raise HTTPException(status_code=404, detail="Asset not found")
    return AssetItemResponseSchema(item=item)


@router.get("/depreciation", response_model=DepreciationRecordListResponseSchema)
def list_depreciation_records_endpoint(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("asset_inventory.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
    status: DepreciationStatus | None = None,
) -> DepreciationRecordListResponseSchema:
    items = list_depreciation_records(int(tenant["id"]), status=status)
    return DepreciationRecordListResponseSchema(items=items)


@router.post("/depreciation", response_model=DepreciationRecordItemResponseSchema)
def create_depreciation_record_endpoint(
    payload: DepreciationRecordCreateSchema,
    actor: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("asset_inventory.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> DepreciationRecordItemResponseSchema:
    item = create_depreciation_record(int(tenant["id"]), payload, actor)
    return DepreciationRecordItemResponseSchema(item=item)


@router.get("/depreciation/{record_id}", response_model=DepreciationRecordItemResponseSchema)
def get_depreciation_record_endpoint(
    record_id: int,
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("asset_inventory.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> DepreciationRecordItemResponseSchema:
    item = get_depreciation_record(int(tenant["id"]), record_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Depreciation record not found")
    return DepreciationRecordItemResponseSchema(item=item)
