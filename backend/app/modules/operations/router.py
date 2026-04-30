from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.core.module_helpers.service_validation import DomainValidationError
from app.core.tenant import get_current_tenant
from app.modules.operations.schemas import (
    CleaningCheckCreateSchema,
    CleaningCheckItemResponseSchema,
    CleaningCheckListResponseSchema,
    FacilityIssueCreateSchema,
    FacilityIssueItemResponseSchema,
    FacilityIssueListResponseSchema,
    MaintenanceAssetCreateSchema,
    MaintenanceAssetItemResponseSchema,
    MaintenanceAssetListResponseSchema,
    OperationsHealthResponseSchema,
    RoomReadinessCreateSchema,
    RoomReadinessItemResponseSchema,
    RoomReadinessListResponseSchema,
    UtilityReadingCreateSchema,
    UtilityReadingItemResponseSchema,
    UtilityReadingListResponseSchema,
    WorkOrderCreateSchema,
    WorkOrderItemResponseSchema,
    WorkOrderListResponseSchema,
)
from app.modules.operations.service import (
    create_cleaning_check,
    create_facility_issue,
    create_maintenance_asset,
    create_room_readiness,
    create_utility_reading,
    create_work_order,
    get_operations_health_snapshot,
    list_cleaning_checks,
    list_facility_issues,
    list_maintenance_assets,
    list_room_readiness,
    list_utility_readings,
    list_work_orders,
)
from app.modules.rbac.security import get_actor, permission_dependency


router = APIRouter(prefix="/api/admin/operations", tags=["operations"])


@router.get("/health", response_model=OperationsHealthResponseSchema)
def get_operations_health_endpoint(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("operations.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> OperationsHealthResponseSchema:
    item = get_operations_health_snapshot(int(tenant["id"]))
    return OperationsHealthResponseSchema(item=item)


@router.get("/facility-issues", response_model=FacilityIssueListResponseSchema)
def list_facility_issues_endpoint(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("operations.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> FacilityIssueListResponseSchema:
    return FacilityIssueListResponseSchema(items=list_facility_issues(int(tenant["id"])))


@router.post("/facility-issues", response_model=FacilityIssueItemResponseSchema)
def create_facility_issue_endpoint(
    payload: FacilityIssueCreateSchema,
    actor: Annotated[str, Depends(get_actor)],
    _: Annotated[None, Depends(permission_dependency("operations.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> FacilityIssueItemResponseSchema:
    try:
        item = create_facility_issue(int(tenant["id"]), payload, actor)
        return FacilityIssueItemResponseSchema(item=item)
    except (ValueError, DomainValidationError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/work-orders", response_model=WorkOrderListResponseSchema)
def list_work_orders_endpoint(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("operations.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> WorkOrderListResponseSchema:
    return WorkOrderListResponseSchema(items=list_work_orders(int(tenant["id"])))


@router.post("/work-orders", response_model=WorkOrderItemResponseSchema)
def create_work_order_endpoint(
    payload: WorkOrderCreateSchema,
    actor: Annotated[str, Depends(get_actor)],
    _: Annotated[None, Depends(permission_dependency("operations.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> WorkOrderItemResponseSchema:
    try:
        item = create_work_order(int(tenant["id"]), payload, actor)
        return WorkOrderItemResponseSchema(item=item)
    except (ValueError, DomainValidationError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/cleaning-checks", response_model=CleaningCheckListResponseSchema)
def list_cleaning_checks_endpoint(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("operations.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> CleaningCheckListResponseSchema:
    return CleaningCheckListResponseSchema(items=list_cleaning_checks(int(tenant["id"])))


@router.post("/cleaning-checks", response_model=CleaningCheckItemResponseSchema)
def create_cleaning_check_endpoint(
    payload: CleaningCheckCreateSchema,
    actor: Annotated[str, Depends(get_actor)],
    _: Annotated[None, Depends(permission_dependency("operations.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> CleaningCheckItemResponseSchema:
    try:
        item = create_cleaning_check(int(tenant["id"]), payload, actor)
        return CleaningCheckItemResponseSchema(item=item)
    except (ValueError, DomainValidationError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/room-readiness", response_model=RoomReadinessListResponseSchema)
def list_room_readiness_endpoint(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("operations.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> RoomReadinessListResponseSchema:
    return RoomReadinessListResponseSchema(items=list_room_readiness(int(tenant["id"])))


@router.post("/room-readiness", response_model=RoomReadinessItemResponseSchema)
def create_room_readiness_endpoint(
    payload: RoomReadinessCreateSchema,
    actor: Annotated[str, Depends(get_actor)],
    _: Annotated[None, Depends(permission_dependency("operations.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> RoomReadinessItemResponseSchema:
    try:
        item = create_room_readiness(int(tenant["id"]), payload, actor)
        return RoomReadinessItemResponseSchema(item=item)
    except (ValueError, DomainValidationError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/maintenance-assets", response_model=MaintenanceAssetListResponseSchema)
def list_maintenance_assets_endpoint(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("operations.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> MaintenanceAssetListResponseSchema:
    return MaintenanceAssetListResponseSchema(items=list_maintenance_assets(int(tenant["id"])))


@router.post("/maintenance-assets", response_model=MaintenanceAssetItemResponseSchema)
def create_maintenance_asset_endpoint(
    payload: MaintenanceAssetCreateSchema,
    actor: Annotated[str, Depends(get_actor)],
    _: Annotated[None, Depends(permission_dependency("operations.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> MaintenanceAssetItemResponseSchema:
    try:
        item = create_maintenance_asset(int(tenant["id"]), payload, actor)
        return MaintenanceAssetItemResponseSchema(item=item)
    except (ValueError, DomainValidationError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/utility-readings", response_model=UtilityReadingListResponseSchema)
def list_utility_readings_endpoint(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("operations.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> UtilityReadingListResponseSchema:
    return UtilityReadingListResponseSchema(items=list_utility_readings(int(tenant["id"])))


@router.post("/utility-readings", response_model=UtilityReadingItemResponseSchema)
def create_utility_reading_endpoint(
    payload: UtilityReadingCreateSchema,
    actor: Annotated[str, Depends(get_actor)],
    _: Annotated[None, Depends(permission_dependency("operations.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> UtilityReadingItemResponseSchema:
    try:
        item = create_utility_reading(int(tenant["id"]), payload, actor)
        return UtilityReadingItemResponseSchema(item=item)
    except (ValueError, DomainValidationError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc