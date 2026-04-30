from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


ThesisStatus = Literal[
    "draft",
    "submitted",
    "under_review",
    "approved",
    "rejected",
    "defended",
]


class ThesisRecordBaseSchema(BaseModel):
    thesis_code: str = Field(min_length=1, max_length=64)
    student_id: int = Field(ge=1)
    title: str = Field(min_length=3, max_length=300)
    advisor_faculty_id: str | None = Field(default=None, max_length=64)
    status: ThesisStatus = "draft"
    defense_date: date | None = None
    repository_url: str | None = Field(default=None, max_length=500)


class ThesisCreateSchema(BaseModel):
    thesis_code: str = Field(min_length=1, max_length=64)
    student_id: int = Field(ge=1)
    title: str = Field(min_length=3, max_length=300)
    advisor_faculty_id: str | None = Field(default=None, max_length=64)
    repository_url: str | None = Field(default=None, max_length=500)
    keywords: str | None = Field(default=None, max_length=256)
    reviewer_notes: str | None = Field(default=None, max_length=500)


class ThesisStatusUpdateSchema(BaseModel):
    status: ThesisStatus
    defense_date: date | None = None


class ThesisRecordSchema(ThesisRecordBaseSchema):
    id: int
    tenant_id: str | None = None


class ThesisListResponseSchema(BaseModel):
    items: list[ThesisRecordSchema]


class ThesisItemResponseSchema(BaseModel):
    item: ThesisRecordSchema
