from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


CounselingCaseStatus = Literal["open", "in_progress", "closed"]
WellbeingCheckinStatus = Literal["stable", "watch", "at_risk"]
AccessibilitySupportStatus = Literal["requested", "active", "completed", "denied"]
DisciplinaryCaseStatus = Literal[
    "reported",
    "under_review",
    "hearing_scheduled",
    "closed",
    "appealed",
]

# Allowed state transitions for disciplinary cases
DISCIPLINARY_ALLOWED_TRANSITIONS: dict[str, list[str]] = {
    "reported": ["under_review", "closed"],
    "under_review": ["hearing_scheduled", "closed"],
    "hearing_scheduled": ["closed", "appealed"],
    "closed": ["appealed"],
    "appealed": ["closed"],
}


class CounselingCaseCreateSchema(BaseModel):
    case_code: str = Field(min_length=1, max_length=64)
    student_id: str = Field(min_length=1, max_length=64)
    concern_type: str = Field(min_length=1, max_length=120)
    status: CounselingCaseStatus = "open"
    priority: str | None = Field(default=None, max_length=32)


class CounselingCaseSchema(CounselingCaseCreateSchema):
    id: int
    tenant_id: str | None = None


class WellbeingCheckinCreateSchema(BaseModel):
    student_id: str = Field(min_length=1, max_length=64)
    wellbeing_score: int = Field(..., ge=0, le=100)
    status: WellbeingCheckinStatus = "stable"


class WellbeingCheckinSchema(WellbeingCheckinCreateSchema):
    id: int
    tenant_id: str | None = None


class AccessibilitySupportCreateSchema(BaseModel):
    support_code: str = Field(min_length=1, max_length=64)
    student_id: str = Field(min_length=1, max_length=64)
    support_type: str = Field(min_length=1, max_length=120)
    status: AccessibilitySupportStatus = "requested"


class AccessibilitySupportSchema(AccessibilitySupportCreateSchema):
    id: int
    tenant_id: str | None = None


class DisciplinaryCaseCreateSchema(BaseModel):
    incident_code: str = Field(min_length=1, max_length=64)
    student_id: str = Field(min_length=1, max_length=64)
    incident_type: str = Field(min_length=1, max_length=120)
    severity: str = Field(min_length=1, max_length=32)
    status: DisciplinaryCaseStatus = "reported"
    reviewer_notes: str | None = Field(default=None, max_length=500)


class DisciplinaryCaseSchema(DisciplinaryCaseCreateSchema):
    id: int
    tenant_id: str | None = None


class CounselingCaseListResponseSchema(BaseModel):
    items: list[CounselingCaseSchema]


class WellbeingCheckinListResponseSchema(BaseModel):
    items: list[WellbeingCheckinSchema]


class AccessibilitySupportListResponseSchema(BaseModel):
    items: list[AccessibilitySupportSchema]


class DisciplinaryCaseListResponseSchema(BaseModel):
    items: list[DisciplinaryCaseSchema]


class CounselingCaseItemResponseSchema(BaseModel):
    item: CounselingCaseSchema


class WellbeingCheckinItemResponseSchema(BaseModel):
    item: WellbeingCheckinSchema


class AccessibilitySupportItemResponseSchema(BaseModel):
    item: AccessibilitySupportSchema


class DisciplinaryCaseItemResponseSchema(BaseModel):
    item: DisciplinaryCaseSchema


class DisciplinaryCaseStatusUpdateSchema(BaseModel):
    status: DisciplinaryCaseStatus
    reason: str | None = Field(default=None, max_length=512)


class StudentLifeHealthSnapshotSchema(BaseModel):
    tenant_id: int = Field(..., ge=1)
    counseling_cases_total: int = Field(..., ge=0)
    open_counseling_cases: int = Field(..., ge=0)
    wellbeing_checkins_total: int = Field(..., ge=0)
    at_risk_wellbeing_checkins: int = Field(..., ge=0)
    accessibility_supports_total: int = Field(..., ge=0)
    active_accessibility_supports: int = Field(..., ge=0)
    disciplinary_cases_total: int = Field(..., ge=0)
    unresolved_disciplinary_cases: int = Field(..., ge=0)


class StudentLifeHealthResponseSchema(BaseModel):
    item: StudentLifeHealthSnapshotSchema