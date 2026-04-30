"""Phase VII-VII2: Equipment booking schemas."""
from __future__ import annotations

from pydantic import BaseModel, Field


class EquipmentItemCreatePayload(BaseModel):
    equipment_code: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=256)
    category: str = Field(min_length=1, max_length=64)
    location: str | None = Field(default=None, max_length=128)
    status: str = Field(default="available", min_length=1, max_length=32)
    capacity: int | None = Field(default=None, ge=1)
    notes: str | None = Field(default=None, max_length=2000)
    integration_source: str | None = Field(default=None, max_length=64)


class EquipmentItemResponse(EquipmentItemCreatePayload):
    id: int
    tenant_id: int


class EquipmentItemItemResponse(BaseModel):
    record: EquipmentItemResponse


class EquipmentItemListResponse(BaseModel):
    records: list[EquipmentItemResponse]


class EquipmentBookingCreatePayload(BaseModel):
    equipment_code: str = Field(min_length=1, max_length=64)
    requester_id: str = Field(min_length=1, max_length=64)
    start_time: str = Field(min_length=1, max_length=64)
    end_time: str = Field(min_length=1, max_length=64)
    booking_status: str = Field(default="pending", min_length=1, max_length=32)
    purpose: str | None = Field(default=None, max_length=512)
    conflict_flag: bool = False
    cancellation_reason: str | None = Field(default=None, max_length=500)
    integration_source: str | None = Field(default=None, max_length=64)


class EquipmentBookingStatusUpdatePayload(BaseModel):
    booking_status: str = Field(min_length=1, max_length=32)


class EquipmentBookingResponse(EquipmentBookingCreatePayload):
    id: int
    tenant_id: int


class EquipmentBookingItemResponse(BaseModel):
    record: EquipmentBookingResponse


class EquipmentBookingListResponse(BaseModel):
    records: list[EquipmentBookingResponse]


class EquipmentBookingBrainContextResponse(BaseModel):
    module: str
    tenant_id: int
    total_equipment: int
    available_equipment: int
    total_bookings: int
    active_bookings: int
    conflict_bookings: int
    utilization_rate: float
    availability_status: str
