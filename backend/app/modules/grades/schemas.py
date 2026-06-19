from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class GradingScaleItemCreateSchema(BaseModel):
    grade_code: str = Field(min_length=1, max_length=32)
    grade_points: Decimal = Field(ge=0)
    min_percentage: Decimal = Field(ge=0, le=100)
    max_percentage: Decimal = Field(ge=0, le=100)

    @field_validator("grade_code")
    @classmethod
    def normalize_grade_code(cls, value: str) -> str:
        normalized = value.strip().upper()
        if not normalized:
            raise ValueError("grade_code must be provided")
        return normalized

    @model_validator(mode="after")
    def validate_percentage_range(self) -> "GradingScaleItemCreateSchema":
        if self.min_percentage > self.max_percentage:
            raise ValueError("min_percentage must be less than or equal to max_percentage")
        return self


class GradingScaleCreateSchema(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    description: str | None = Field(default=None, max_length=2000)
    is_active: bool = True
    items: list[GradingScaleItemCreateSchema] = Field(min_length=1)

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("name must be provided")
        return normalized


class GradingScaleItemReadSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: int
    scale_id: int
    grade_code: str
    grade_points: Decimal
    min_percentage: Decimal
    max_percentage: Decimal


class GradingScaleReadSchema(BaseModel):
    id: int
    tenant_id: int
    name: str
    description: str | None
    is_active: bool
    items: list[GradingScaleItemReadSchema]


class GradingScaleListResponseSchema(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[GradingScaleReadSchema]


class GradeSubmitSchema(BaseModel):
    enrollment_id: int = Field(gt=0)
    grading_scale_id: int = Field(gt=0)
    grade_code: str = Field(min_length=1, max_length=32)
    grade_points: Decimal | None = Field(default=None, ge=0)
    metadata_json: dict = Field(default_factory=dict)

    @field_validator("grade_code")
    @classmethod
    def normalize_grade_code(cls, value: str) -> str:
        normalized = value.strip().upper()
        if not normalized:
            raise ValueError("grade_code must be provided")
        return normalized


class GradeChangeSchema(BaseModel):
    enrollment_id: int = Field(gt=0)
    grading_scale_id: int = Field(gt=0)
    new_grade_code: str = Field(min_length=1, max_length=32)
    new_grade_points: Decimal | None = Field(default=None, ge=0)
    expected_version: int = Field(ge=1)
    reason: str | None = Field(default=None, max_length=1000)
    metadata_json: dict = Field(default_factory=dict)

    @field_validator("new_grade_code")
    @classmethod
    def normalize_new_grade_code(cls, value: str) -> str:
        normalized = value.strip().upper()
        if not normalized:
            raise ValueError("new_grade_code must be provided")
        return normalized


class GradeReadSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: int
    enrollment_id: int
    grade_code: str
    grade_points: Decimal
    grading_scale_id: int
    submitted_by: str
    submitted_at: datetime
    version: int
    metadata_json: dict


class GradeListResponseSchema(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[GradeReadSchema]


class TranscriptItemSchema(BaseModel):
    term_id: int
    term_code: str | None
    term_name: str | None
    course_id: int
    course_code: str | None
    course_title: str | None
    credits: int
    grade_code: str | None
    grade_points: Decimal | None


class StudentTranscriptSchema(BaseModel):
    student_profile_id: int
    total_credits: int
    gpa: Decimal | None
    items: list[TranscriptItemSchema]


class GradeMutationResponse(BaseModel):
    grade: GradeReadSchema
    idempotent_replay: bool = False


class GradeEnrollmentConsistencyIssueSchema(BaseModel):
    issue_type: str
    enrollment_id: int | None = None
    grade_submission_id: int | None = None
    field: str | None = None
    expected: str | None = None
    actual: str | None = None


class GradeEnrollmentConsistencyReportSchema(BaseModel):
    enrollment_count: int
    grade_submission_count: int
    issue_count: int
    issues: list[GradeEnrollmentConsistencyIssueSchema]
