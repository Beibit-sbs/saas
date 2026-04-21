from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


HousingRequestType = Literal["assignment", "transfer", "maintenance", "checkout"]
HousingRequestStatus = Literal["submitted", "in_review", "approved", "rejected", "completed"]


class HousingRequestBaseSchema(BaseModel):
    student_id: int = Field(ge=1)
    request_type: HousingRequestType = "assignment"
    dormitory: str = Field(min_length=1, max_length=120)
    room_preference: str | None = Field(default=None, max_length=64)
    status: HousingRequestStatus = "submitted"
    manager_id: str | None = Field(default=None, max_length=64)
    notes: str | None = Field(default=None, max_length=3000)


class HousingRequestCreateSchema(BaseModel):
    student_id: int = Field(ge=1)
    request_type: HousingRequestType = "assignment"
    dormitory: str = Field(min_length=1, max_length=120)
    room_preference: str | None = Field(default=None, max_length=64)
    manager_id: str | None = Field(default=None, max_length=64)
    notes: str | None = Field(default=None, max_length=3000)


class HousingRequestStatusUpdateSchema(BaseModel):
    status: HousingRequestStatus
    notes: str | None = Field(default=None, max_length=3000)


class HousingRequestSchema(HousingRequestBaseSchema):
    id: int
    tenant_id: str | None = None


class HousingRequestListResponseSchema(BaseModel):
    items: list[HousingRequestSchema]


class HousingRequestItemResponseSchema(BaseModel):
    item: HousingRequestSchema
