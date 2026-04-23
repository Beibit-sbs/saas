"""Phase XI-XI1: Facilities Work Orders schemas."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


WorkOrderPriority = Literal["low", "medium", "high", "critical"]
WorkOrderType = Literal["repair", "maintenance", "installation", "inspection"]
WorkOrderStatus = Literal["open", "in_progress", "on_hold", "completed", "cancelled"]

MaintenanceRequestSeverity = Literal["low", "medium", "high", "critical"]
MaintenanceRequestIssueType = Literal["plumbing", "electrical", "hvac", "structural", "other"]
MaintenanceRequestStatus = Literal["pending", "assigned", "in_progress", "resolved", "closed"]


class WorkOrderCreateSchema(BaseModel):
    order_code: str = Field(min_length=1, max_length=64)
    facility_code: str = Field(min_length=1, max_length=64)
    title: str = Field(min_length=1, max_length=200)
    work_type: WorkOrderType = "repair"
    priority: WorkOrderPriority = "medium"
    assigned_to: str | None = Field(default=None, max_length=128)
    status: WorkOrderStatus = "open"


class WorkOrderSchema(WorkOrderCreateSchema):
    id: int
    tenant_id: str | None = None


class WorkOrderStatusUpdateSchema(BaseModel):
    status: WorkOrderStatus


class WorkOrderItemResponseSchema(BaseModel):
    item: WorkOrderSchema


class WorkOrderListResponseSchema(BaseModel):
    items: list[WorkOrderSchema]


class MaintenanceRequestCreateSchema(BaseModel):
    request_code: str = Field(min_length=1, max_length=64)
    facility_code: str = Field(min_length=1, max_length=64)
    issue_type: MaintenanceRequestIssueType = "other"
    severity: MaintenanceRequestSeverity = "medium"
    notes: str | None = Field(default=None, max_length=500)
    status: MaintenanceRequestStatus = "pending"


class MaintenanceRequestSchema(MaintenanceRequestCreateSchema):
    id: int
    tenant_id: str | None = None


class MaintenanceRequestStatusUpdateSchema(BaseModel):
    status: MaintenanceRequestStatus


class MaintenanceRequestItemResponseSchema(BaseModel):
    item: MaintenanceRequestSchema


class MaintenanceRequestListResponseSchema(BaseModel):
    items: list[MaintenanceRequestSchema]
