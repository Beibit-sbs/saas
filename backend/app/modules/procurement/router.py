from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.core.tenant import get_current_tenant
from app.core.module_helpers.service_validation import DomainValidationError
from app.modules.procurement.schemas import (
    AssetCreateSchema,
    AssetItemResponseSchema,
    AssetListResponseSchema,
    ContractCreateSchema,
    ContractItemResponseSchema,
    ContractListResponseSchema,
    ContractStatusUpdateSchema,
    InventoryItemCreateSchema,
    InventoryItemItemResponseSchema,
    InventoryItemListResponseSchema,
    ProcurementHealthResponseSchema,
    VendorCreateSchema,
    VendorItemResponseSchema,
    VendorListResponseSchema,
)
import app.modules.procurement.service as _svc
from app.modules.rbac.security import get_actor, permission_dependency


router = APIRouter(prefix="/api/admin/procurement", tags=["procurement"])


@router.get("/health", response_model=ProcurementHealthResponseSchema)
def get_procurement_health_endpoint(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("procurement.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> ProcurementHealthResponseSchema:
    item = _svc.get_procurement_health_snapshot(int(tenant["id"]))
    return ProcurementHealthResponseSchema(item=item)


@router.get("/vendors", response_model=VendorListResponseSchema)
def list_vendors_endpoint(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("procurement.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> VendorListResponseSchema:
    return VendorListResponseSchema(items=_svc.list_vendors(int(tenant["id"])))


@router.post("/vendors", response_model=VendorItemResponseSchema)
def create_vendor_endpoint(
    payload: VendorCreateSchema,
    actor: Annotated[str, Depends(get_actor)],
    _: Annotated[None, Depends(permission_dependency("procurement.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> VendorItemResponseSchema:
    try:
        item = _svc.create_vendor(int(tenant["id"]), payload, actor)
        return VendorItemResponseSchema(item=item)
    except (ValueError, DomainValidationError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/contracts", response_model=ContractListResponseSchema)
def list_contracts_endpoint(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("procurement.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> ContractListResponseSchema:
    return ContractListResponseSchema(items=_svc.list_contracts(int(tenant["id"])))


@router.post("/contracts", response_model=ContractItemResponseSchema)
def create_contract_endpoint(
    payload: ContractCreateSchema,
    actor: Annotated[str, Depends(get_actor)],
    _: Annotated[None, Depends(permission_dependency("procurement.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> ContractItemResponseSchema:
    try:
        item = _svc.create_contract(int(tenant["id"]), payload, actor)
        return ContractItemResponseSchema(item=item)
    except (ValueError, DomainValidationError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.patch("/contracts/{contract_id}/status", response_model=ContractItemResponseSchema)
def update_contract_status_endpoint(
    contract_id: int,
    payload: ContractStatusUpdateSchema,
    actor: Annotated[str, Depends(get_actor)],
    _: Annotated[None, Depends(permission_dependency("procurement.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> ContractItemResponseSchema:
    try:
        item = _svc.update_contract_status(int(tenant["id"]), contract_id, payload, actor)
    except DomainValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if item is None:
        raise HTTPException(status_code=404, detail="Contract not found")
    return ContractItemResponseSchema(item=item)


@router.get("/assets", response_model=AssetListResponseSchema)
def list_assets_endpoint(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("procurement.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> AssetListResponseSchema:
    return AssetListResponseSchema(items=_svc.list_assets(int(tenant["id"])))


@router.post("/assets", response_model=AssetItemResponseSchema)
def create_asset_endpoint(
    payload: AssetCreateSchema,
    actor: Annotated[str, Depends(get_actor)],
    _: Annotated[None, Depends(permission_dependency("procurement.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> AssetItemResponseSchema:
    try:
        item = _svc.create_asset(int(tenant["id"]), payload, actor)
        return AssetItemResponseSchema(item=item)
    except (ValueError, DomainValidationError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/inventory-items", response_model=InventoryItemListResponseSchema)
def list_inventory_items_endpoint(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("procurement.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> InventoryItemListResponseSchema:
    return InventoryItemListResponseSchema(items=_svc.list_inventory_items(int(tenant["id"])))


@router.post("/inventory-items", response_model=InventoryItemItemResponseSchema)
def create_inventory_item_endpoint(
    payload: InventoryItemCreateSchema,
    actor: Annotated[str, Depends(get_actor)],
    _: Annotated[None, Depends(permission_dependency("procurement.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> InventoryItemItemResponseSchema:
    try:
        item = _svc.create_inventory_item(int(tenant["id"]), payload, actor)
        return InventoryItemItemResponseSchema(item=item)
    except (ValueError, DomainValidationError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
