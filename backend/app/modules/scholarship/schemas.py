"""Phase VIII-1: Scholarship module schemas."""
from __future__ import annotations

from pydantic import BaseModel, Field


class ScholarshipApplicationCreatePayload(BaseModel):
    application_code: str = Field(min_length=1, max_length=64)
    student_id: str = Field(min_length=1, max_length=64)
    scholarship_type: str = Field(min_length=1, max_length=64)
    status: str = Field(default="pending", min_length=1, max_length=32)
    gpa: float = Field(ge=0.0, le=4.0)
    requested_amount: float = Field(ge=0.0)
    notes: str | None = Field(default=None, max_length=2000)
    integration_source: str | None = Field(default=None, max_length=64)


class ScholarshipApplicationResponse(ScholarshipApplicationCreatePayload):
    id: int
    tenant_id: int


class ScholarshipApplicationItemResponse(BaseModel):
    record: ScholarshipApplicationResponse


class ScholarshipApplicationListResponse(BaseModel):
    records: list[ScholarshipApplicationResponse]


class ScholarshipAwardCreatePayload(BaseModel):
    award_code: str = Field(min_length=1, max_length=64)
    student_id: str = Field(min_length=1, max_length=64)
    scholarship_type: str = Field(min_length=1, max_length=64)
    status: str = Field(default="active", min_length=1, max_length=32)
    amount: float = Field(ge=0.0)
    renewal_deadline: str | None = Field(default=None, max_length=32)
    gpa_threshold: float = Field(default=2.5, ge=0.0, le=4.0)
    current_gpa: float = Field(ge=0.0, le=4.0)
    notes: str | None = Field(default=None, max_length=2000)
    integration_source: str | None = Field(default=None, max_length=64)


class ScholarshipAwardResponse(ScholarshipAwardCreatePayload):
    id: int
    tenant_id: int
    at_risk: bool


class ScholarshipAwardItemResponse(BaseModel):
    record: ScholarshipAwardResponse


class ScholarshipAwardListResponse(BaseModel):
    records: list[ScholarshipAwardResponse]


class ScholarshipBrainContextResponse(BaseModel):
    module: str
    tenant_id: int
    total_applications: int
    pending_applications: int
    total_awards: int
    at_risk_awards: int
    at_risk_rate: float
    retention_health: str
