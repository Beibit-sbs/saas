from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


AdvisingSessionType = Literal["academic", "career", "personal", "mentoring"]

AdvisingSessionStatus = Literal["scheduled", "completed", "cancelled", "no_show"]


class AdvisingSessionBaseSchema(BaseModel):
    student_id: int = Field(ge=1)
    advisor_id: str = Field(min_length=1, max_length=64)
    session_type: AdvisingSessionType = "academic"
    status: AdvisingSessionStatus = "scheduled"
    scheduled_at: str | None = Field(default=None, max_length=32)
    notes: str | None = Field(default=None, max_length=2000)
    outcome: str | None = Field(default=None, max_length=1000)


class AdvisingSessionCreateSchema(BaseModel):
    student_id: int = Field(ge=1)
    advisor_id: str = Field(min_length=1, max_length=64)
    session_type: AdvisingSessionType = "academic"
    scheduled_at: str | None = Field(default=None, max_length=32)
    notes: str | None = Field(default=None, max_length=2000)


class AdvisingSessionStatusUpdateSchema(BaseModel):
    status: AdvisingSessionStatus
    outcome: str | None = Field(default=None, max_length=1000)


class AdvisingSessionSchema(AdvisingSessionBaseSchema):
    id: int
    tenant_id: str | None = None


class AdvisingSessionListResponseSchema(BaseModel):
    items: list[AdvisingSessionSchema]


class AdvisingSessionItemResponseSchema(BaseModel):
    item: AdvisingSessionSchema
