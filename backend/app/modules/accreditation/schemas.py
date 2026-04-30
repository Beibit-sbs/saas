from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


AccreditationStatus = Literal[
    "draft",
    "evidence_requested",
    "evidence_collected",
    "under_review",
    "compliant",
    "remediation_required",
]

AccreditationStandardType = Literal[
    "institutional",
    "programmatic",
    "curriculum",
    "faculty_qualifications",
    "learning_outcomes",
]

RiskLevel = Literal["low", "medium", "high"]


class AccreditationRecordBaseSchema(BaseModel):
    standard_code: str = Field(min_length=1, max_length=64)
    standard_type: AccreditationStandardType
    title: str = Field(min_length=3, max_length=300)
    owner_department: str = Field(min_length=2, max_length=120)
    review_cycle_year: int = Field(ge=2020, le=2100)
    due_date: date | None = None
    evidence_summary: str | None = Field(default=None, max_length=1000)
    risk_level: RiskLevel = "medium"
    status: AccreditationStatus = "draft"
    reviewer_notes: str | None = Field(default=None, max_length=1000)
    remediation_plan: str | None = Field(default=None, max_length=1000)


class AccreditationCreateSchema(BaseModel):
    standard_code: str = Field(min_length=1, max_length=64)
    standard_type: AccreditationStandardType
    title: str = Field(min_length=3, max_length=300)
    owner_department: str = Field(min_length=2, max_length=120)
    review_cycle_year: int = Field(ge=2020, le=2100)
    due_date: date | None = None
    evidence_summary: str | None = Field(default=None, max_length=1000)
    risk_level: RiskLevel = "medium"
    external_auditor_id: str | None = Field(default=None, max_length=64)


class AccreditationStatusUpdateSchema(BaseModel):
    status: AccreditationStatus
    reviewer_notes: str | None = Field(default=None, max_length=1000)
    remediation_plan: str | None = Field(default=None, max_length=1000)


class AccreditationRecordSchema(AccreditationRecordBaseSchema):
    id: int
    tenant_id: str | None = None


class AccreditationListResponseSchema(BaseModel):
    items: list[AccreditationRecordSchema]


class AccreditationItemResponseSchema(BaseModel):
    item: AccreditationRecordSchema
