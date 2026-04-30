"""Phase XI-XI1: Facilities Work Orders router."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

import app.modules.facilities_work_orders.service as _svc
from app.core.module_helpers.service_validation import DomainValidationError
from app.core.tenant import get_current_tenant
from app.modules.facilities_work_orders.schemas import (
    MaintenanceRequestCreateSchema,
    MaintenanceRequestItemResponseSchema,
    MaintenanceRequestListResponseSchema,
    MaintenanceRequestStatusUpdateSchema,
    WorkOrderCreateSchema,
    WorkOrderItemResponseSchema,
    WorkOrderListResponseSchema,
    WorkOrderPriority,
    WorkOrderStatus,
    WorkOrderStatusUpdateSchema,
    WorkOrderType,
)
from app.modules.rbac.security import get_actor, permission_dependency


router = APIRouter(prefix="/api/admin/facilities", tags=["facilities-work-orders"])


@router.get("/work-orders", response_model=WorkOrderListResponseSchema)
def list_work_orders_endpoint(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("facilities.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
    status: WorkOrderStatus | None = None,
    priority: WorkOrderPriority | None = None,
    work_type: WorkOrderType | None = None,
) -> WorkOrderListResponseSchema:
    items = _svc.list_work_orders(int(tenant["id"]), status=status, priority=priority, work_type=work_type)
    return WorkOrderListResponseSchema(items=items)


@router.post("/work-orders", response_model=WorkOrderItemResponseSchema)
def create_work_order_endpoint(
    payload: WorkOrderCreateSchema,
    actor: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("facilities.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> WorkOrderItemResponseSchema:
    try:
        item = _svc.create_work_order(int(tenant["id"]), payload, actor)
    except (ValueError, DomainValidationError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return WorkOrderItemResponseSchema(item=item)


@router.get("/work-orders/{order_id}", response_model=WorkOrderItemResponseSchema)
def get_work_order_endpoint(
    order_id: int,
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("facilities.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> WorkOrderItemResponseSchema:
    item = _svc.get_work_order(int(tenant["id"]), order_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Work order not found")
    return WorkOrderItemResponseSchema(item=item)


@router.patch("/work-orders/{order_id}/status", response_model=WorkOrderItemResponseSchema)
def update_work_order_status_endpoint(
    order_id: int,
    payload: WorkOrderStatusUpdateSchema,
    actor: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("facilities.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> WorkOrderItemResponseSchema:
    item = _svc.update_work_order_status(int(tenant["id"]), order_id, payload, actor)
    if item is None:
        raise HTTPException(status_code=404, detail="Work order not found")
    return WorkOrderItemResponseSchema(item=item)


@router.get("/maintenance-requests", response_model=MaintenanceRequestListResponseSchema)
def list_maintenance_requests_endpoint(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("facilities.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> MaintenanceRequestListResponseSchema:
    items = _svc.list_maintenance_requests(int(tenant["id"]))
    return MaintenanceRequestListResponseSchema(items=items)


@router.post("/maintenance-requests", response_model=MaintenanceRequestItemResponseSchema)
def create_maintenance_request_endpoint(
    payload: MaintenanceRequestCreateSchema,
    actor: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("facilities.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> MaintenanceRequestItemResponseSchema:
    try:
        item = _svc.create_maintenance_request(int(tenant["id"]), payload, actor)
    except (ValueError, DomainValidationError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return MaintenanceRequestItemResponseSchema(item=item)


@router.get("/maintenance-requests/{req_id}", response_model=MaintenanceRequestItemResponseSchema)
def get_maintenance_request_endpoint(
    req_id: int,
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("facilities.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> MaintenanceRequestItemResponseSchema:
    item = _svc.get_maintenance_request(int(tenant["id"]), req_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Maintenance request not found")
    return MaintenanceRequestItemResponseSchema(item=item)


@router.patch("/maintenance-requests/{req_id}/status", response_model=MaintenanceRequestItemResponseSchema)
def update_maintenance_request_status_endpoint(
    req_id: int,
    payload: MaintenanceRequestStatusUpdateSchema,
    actor: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("facilities.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> MaintenanceRequestItemResponseSchema:
    item = _svc.update_maintenance_request_status(int(tenant["id"]), req_id, payload, actor)
    if item is None:
        raise HTTPException(status_code=404, detail="Maintenance request not found")
    return MaintenanceRequestItemResponseSchema(item=item)
