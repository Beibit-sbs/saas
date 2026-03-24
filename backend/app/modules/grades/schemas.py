from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator


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
