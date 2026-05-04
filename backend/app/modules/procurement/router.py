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
    # A-009 Phase 2.3: Request lifecycle schemas
    ApprovalStepSchema,
    ProcurementAuditEntrySchema,
    ProcurementDashboardSummarySchema,
    ProcurementListItemSchema,
    ProcurementOrderCreateSchema,
    ProcurementOrderSchema,
    ProcurementRequestCreateSchema,
    ProcurementRequestSchema,
    ProcurementRequestUpdateSchema,
    ProcurementStatusUpdateSchema,
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


# ─── A-009 Phase 2.3: Request lifecycle endpoints ─────────────────────────────


@router.get("/dashboard/summary", response_model=ProcurementDashboardSummarySchema)
def get_dashboard_summary_endpoint(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("procurement.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> ProcurementDashboardSummarySchema:
    return _svc.get_procurement_dashboard_summary(int(tenant["id"]))


@router.get("/requests/status/{status}", response_model=list[ProcurementListItemSchema])
def list_requests_by_status_endpoint(
    status: str,
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("procurement.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> list[ProcurementListItemSchema]:
    return _svc.list_procurement_requests(int(tenant["id"]), status=status)


@router.get("/requests/requester/{requester_id}", response_model=list[ProcurementListItemSchema])
def list_requests_by_requester_endpoint(
    requester_id: str,
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("procurement.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> list[ProcurementListItemSchema]:
    return _svc.list_procurement_requests(int(tenant["id"]), requester_id=requester_id)


@router.get("/requests", response_model=list[ProcurementListItemSchema])
def list_requests_endpoint(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("procurement.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
    status: str | None = None,
    requester_id: str | None = None,
) -> list[ProcurementListItemSchema]:
    return _svc.list_procurement_requests(int(tenant["id"]), status=status, requester_id=requester_id)


@router.post("/requests", response_model=ProcurementRequestSchema, status_code=201)
def create_request_endpoint(
    payload: ProcurementRequestCreateSchema,
    actor: Annotated[str, Depends(get_actor)],
    _: Annotated[None, Depends(permission_dependency("procurement.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> ProcurementRequestSchema:
    return _svc.create_procurement_request(int(tenant["id"]), payload, actor)


@router.get("/requests/{request_id}/approvals", response_model=list[ApprovalStepSchema])
def get_approval_steps_endpoint(
    request_id: str,
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("procurement.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> list[ApprovalStepSchema]:
    return _svc.get_approval_steps(int(tenant["id"]), request_id)


@router.get("/requests/{request_id}/audit-trail", response_model=list[ProcurementAuditEntrySchema])
def get_audit_trail_endpoint(
    request_id: str,
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("procurement.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> list[ProcurementAuditEntrySchema]:
    return _svc.get_audit_trail(int(tenant["id"]), request_id)


@router.get("/requests/{request_id}/order", response_model=ProcurementOrderSchema)
def get_request_order_endpoint(
    request_id: str,
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("procurement.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> ProcurementOrderSchema:
    order = _svc.get_request_order(int(tenant["id"]), request_id)
    if order is None:
        raise HTTPException(status_code=404, detail="No order found for this request")
    return order


@router.get("/requests/{request_id}", response_model=ProcurementRequestSchema)
def get_request_endpoint(
    request_id: str,
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("procurement.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> ProcurementRequestSchema:
    req = _svc.get_procurement_request(int(tenant["id"]), request_id)
    if req is None:
        raise HTTPException(status_code=404, detail="Request not found")
    return req


@router.put("/requests/{request_id}", response_model=ProcurementRequestSchema)
def update_request_endpoint(
    request_id: str,
    payload: ProcurementRequestUpdateSchema,
    actor: Annotated[str, Depends(get_actor)],
    _: Annotated[None, Depends(permission_dependency("procurement.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> ProcurementRequestSchema:
    req = _svc.update_procurement_request(int(tenant["id"]), request_id, payload, actor)
    if req is None:
        raise HTTPException(status_code=404, detail="Request not found")
    return req


@router.post("/requests/{request_id}/submit", response_model=ProcurementRequestSchema)
def submit_request_endpoint(
    request_id: str,
    actor: Annotated[str, Depends(get_actor)],
    _: Annotated[None, Depends(permission_dependency("procurement.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> ProcurementRequestSchema:
    try:
        req = _svc.submit_procurement_request(int(tenant["id"]), request_id, actor)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    if req is None:
        raise HTTPException(status_code=404, detail="Request not found")
    return req


@router.patch("/requests/{request_id}/status", response_model=ProcurementRequestSchema)
def update_request_status_endpoint(
    request_id: str,
    payload: ProcurementStatusUpdateSchema,
    actor: Annotated[str, Depends(get_actor)],
    _: Annotated[None, Depends(permission_dependency("procurement.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> ProcurementRequestSchema:
    try:
        req = _svc.update_procurement_status(int(tenant["id"]), request_id, payload, actor)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    if req is None:
        raise HTTPException(status_code=404, detail="Request not found")
    return req


@router.post("/requests/{request_id}/fulfill", response_model=ProcurementOrderSchema)
def fulfill_request_endpoint(
    request_id: str,
    actor: Annotated[str, Depends(get_actor)],
    _: Annotated[None, Depends(permission_dependency("procurement.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> ProcurementOrderSchema:
    try:
        order = _svc.fulfill_procurement_request(int(tenant["id"]), request_id, actor)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    if order is None:
        raise HTTPException(status_code=404, detail="Request not found or no order exists")
    return order


@router.post("/orders", response_model=ProcurementOrderSchema, status_code=201)
def create_order_endpoint(
    payload: ProcurementOrderCreateSchema,
    actor: Annotated[str, Depends(get_actor)],
    _: Annotated[None, Depends(permission_dependency("procurement.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> ProcurementOrderSchema:
    try:
        return _svc.create_procurement_order(int(tenant["id"]), payload, actor)
    except (ValueError, DomainValidationError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
