from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


AlumniStatus = Literal["active", "engaged", "donor", "inactive"]
AlumniEngagementType = Literal["mentoring", "event", "donation", "referral"]


class AlumniRecordBaseSchema(BaseModel):
    student_id: int = Field(ge=1)
    graduation_year: int = Field(ge=1950, le=2100)
    status: AlumniStatus = "active"
    engagement_type: AlumniEngagementType = "event"
    employer: str | None = Field(default=None, max_length=120)
    contact_email: str | None = Field(default=None, max_length=120)
    notes: str | None = Field(default=None, max_length=3000)


class AlumniRecordCreateSchema(BaseModel):
    student_id: int = Field(ge=1)
    graduation_year: int = Field(ge=1950, le=2100)
    engagement_type: AlumniEngagementType = "event"
    employer: str | None = Field(default=None, max_length=120)
    contact_email: str | None = Field(default=None, max_length=120)
    notes: str | None = Field(default=None, max_length=3000)


class AlumniRecordStatusUpdateSchema(BaseModel):
    status: AlumniStatus
    notes: str | None = Field(default=None, max_length=3000)


class AlumniRecordSchema(AlumniRecordBaseSchema):
    id: int
    tenant_id: str | None = None


class AlumniRecordListResponseSchema(BaseModel):
    items: list[AlumniRecordSchema]


class AlumniRecordItemResponseSchema(BaseModel):
    item: AlumniRecordSchema
