"""Phase VI-VI2: Dining schemas."""
from __future__ import annotations

from pydantic import BaseModel, Field


class DiningMenuCreatePayload(BaseModel):
    menu_code: str = Field(min_length=1, max_length=64)
    facility_code: str = Field(min_length=1, max_length=64)
    meal_type: str = Field(min_length=1, max_length=32)
    date: str | None = Field(default=None, max_length=32)
    status: str = Field(default="active", min_length=1, max_length=32)
    capacity: int | None = Field(default=None, ge=0)
    available_capacity: int | None = Field(default=None)


class DiningMenuResponse(DiningMenuCreatePayload):
    id: int
    tenant_id: int


class DiningMenuItemResponse(BaseModel):
    record: DiningMenuResponse


class DiningMenuListResponse(BaseModel):
    records: list[DiningMenuResponse]


class DiningOrderCreatePayload(BaseModel):
    order_code: str = Field(min_length=1, max_length=64)
    menu_code: str = Field(min_length=1, max_length=64)
    facility_code: str = Field(min_length=1, max_length=64)
    meal_type: str = Field(min_length=1, max_length=32)
    status: str = Field(default="pending", min_length=1, max_length=32)
    student_id: str | None = Field(default=None, max_length=64)
    special_request: str | None = Field(default=None, max_length=512)


class DiningOrderResponse(DiningOrderCreatePayload):
    id: int
    tenant_id: int


class DiningOrderItemResponse(BaseModel):
    record: DiningOrderResponse


class DiningOrderListResponse(BaseModel):
    records: list[DiningOrderResponse]


class DiningBrainContextResponse(BaseModel):
    module: str
    tenant_id: int
    total_menus: int
    active_menus: int
    capacity_exceeded_menus: int
    total_orders: int
    risk_level: str
