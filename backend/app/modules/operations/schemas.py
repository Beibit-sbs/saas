from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


FacilityIssueStatus = Literal["reported", "in_progress", "resolved", "blocked"]
WorkOrderStatus = Literal["open", "assigned", "in_progress", "completed", "cancelled"]
CleaningCheckStatus = Literal["scheduled", "completed", "missed"]
RoomReadinessStatus = Literal["ready", "needs_cleaning", "maintenance_required", "blocked"]


class FacilityIssueCreateSchema(BaseModel):
    facility_code: str = Field(min_length=1, max_length=64)
    issue_type: str = Field(min_length=1, max_length=120)
    severity: str = Field(min_length=1, max_length=32)
    status: FacilityIssueStatus = "reported"


class FacilityIssueSchema(FacilityIssueCreateSchema):
    id: int
    tenant_id: str | None = None


class WorkOrderCreateSchema(BaseModel):
    work_order_code: str = Field(min_length=1, max_length=64)
    facility_code: str = Field(min_length=1, max_length=64)
    summary: str = Field(min_length=1, max_length=220)
    status: WorkOrderStatus = "open"
    assigned_team: str | None = Field(default=None, max_length=128)


class WorkOrderSchema(WorkOrderCreateSchema):
    id: int
    tenant_id: str | None = None


class CleaningCheckCreateSchema(BaseModel):
    room_code: str = Field(min_length=1, max_length=64)
    scheduled_slot: str = Field(min_length=1, max_length=120)
    status: CleaningCheckStatus = "scheduled"


class CleaningCheckSchema(CleaningCheckCreateSchema):
    id: int
    tenant_id: str | None = None


class RoomReadinessCreateSchema(BaseModel):
    room_code: str = Field(min_length=1, max_length=64)
    building_code: str = Field(min_length=1, max_length=64)
    status: RoomReadinessStatus = "ready"


class RoomReadinessSchema(RoomReadinessCreateSchema):
    id: int
    tenant_id: str | None = None


class MaintenanceAssetCreateSchema(BaseModel):
    asset_code: str = Field(min_length=1, max_length=64)
    facility_code: str = Field(min_length=1, max_length=64)
    asset_type: str = Field(min_length=1, max_length=120)
    health_score: float = Field(..., ge=0, le=100)
    days_since_maintenance: int = Field(..., ge=0)
    expected_service_interval_days: int = Field(..., ge=1)
    status: str = Field(default="monitored", min_length=1, max_length=32)


class MaintenanceAssetSchema(MaintenanceAssetCreateSchema):
    id: int
    tenant_id: str | None = None


class UtilityReadingCreateSchema(BaseModel):
    meter_code: str = Field(min_length=1, max_length=64)
    building_code: str = Field(min_length=1, max_length=64)
    utility_type: str = Field(min_length=1, max_length=32)
    usage_value: float = Field(..., ge=0)
    baseline_value: float = Field(..., ge=0)
    status: str = Field(default="normal", min_length=1, max_length=32)


class UtilityReadingSchema(UtilityReadingCreateSchema):
    id: int
    tenant_id: str | None = None


class FacilityIssueListResponseSchema(BaseModel):
    items: list[FacilityIssueSchema]


class WorkOrderListResponseSchema(BaseModel):
    items: list[WorkOrderSchema]


class CleaningCheckListResponseSchema(BaseModel):
    items: list[CleaningCheckSchema]


class RoomReadinessListResponseSchema(BaseModel):
    items: list[RoomReadinessSchema]


class MaintenanceAssetListResponseSchema(BaseModel):
    items: list[MaintenanceAssetSchema]


class UtilityReadingListResponseSchema(BaseModel):
    items: list[UtilityReadingSchema]


class FacilityIssueItemResponseSchema(BaseModel):
    item: FacilityIssueSchema


class WorkOrderItemResponseSchema(BaseModel):
    item: WorkOrderSchema


class CleaningCheckItemResponseSchema(BaseModel):
    item: CleaningCheckSchema


class RoomReadinessItemResponseSchema(BaseModel):
    item: RoomReadinessSchema


class MaintenanceAssetItemResponseSchema(BaseModel):
    item: MaintenanceAssetSchema


class UtilityReadingItemResponseSchema(BaseModel):
    item: UtilityReadingSchema


class OperationsHealthSnapshotSchema(BaseModel):
    tenant_id: int = Field(..., ge=1)
    facilities_total: int = Field(..., ge=0)
    open_facility_issues: int = Field(..., ge=0)
    work_orders_total: int = Field(..., ge=0)
    missed_cleaning_checks: int = Field(..., ge=0)
    rooms_total: int = Field(..., ge=0)
    rooms_not_ready: int = Field(..., ge=0)
    maintenance_assets_total: int = Field(..., ge=0)
    predictive_maintenance_due: int = Field(..., ge=0)
    utility_readings_total: int = Field(..., ge=0)
    utility_anomaly_readings: int = Field(..., ge=0)


class OperationsHealthResponseSchema(BaseModel):
    item: OperationsHealthSnapshotSchema