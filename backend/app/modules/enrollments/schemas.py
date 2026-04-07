from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.modules.enrollments.models import EnrollmentStatus, EnrollmentType


class AcademicTermReadSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: int
    term_code: str
    term_name: str
    start_date: datetime | None
    end_date: datetime | None
    status: str
    metadata_json: dict
    created_at: datetime
    updated_at: datetime


class EnrollmentCreateSchema(BaseModel):
    student_profile_id: int = Field(gt=0)
    course_id: int = Field(gt=0)
    term_id: int = Field(gt=0)
    enrollment_status: EnrollmentStatus = EnrollmentStatus.ENROLLED
    enrollment_type: EnrollmentType = EnrollmentType.REGULAR
    enrolled_at: datetime | None = None
    metadata_json: dict = Field(default_factory=dict)


class EnrollmentReadSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: int
    student_profile_id: int
    course_id: int
    term_id: int
    enrollment_status: EnrollmentStatus
    enrollment_type: EnrollmentType
    enrolled_at: datetime
    dropped_at: datetime | None
    grade_code: str | None
    grade_points: Decimal | None
    metadata_json: dict
    version: int
    created_by: str
    updated_by: str
    created_at: datetime
    updated_at: datetime


class EnrollmentListResponseSchema(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[EnrollmentReadSchema]


class EnrollmentStatusHistoryReadSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: int
    enrollment_id: int
    version: int
    from_status: EnrollmentStatus | None
    to_status: EnrollmentStatus
    reason: str | None
    actor_id: str
    changed_at: datetime
    metadata_json: dict


class EnrollmentStatusChangeSchema(BaseModel):
    expected_version: int = Field(ge=1)
    to_status: EnrollmentStatus
    reason: str | None = Field(default=None, max_length=1000)
    metadata_json: dict = Field(default_factory=dict)


class EnrollmentDropSchema(BaseModel):
    expected_version: int = Field(ge=1)
    reason: str | None = Field(default=None, max_length=1000)
    dropped_at: datetime | None = None
    metadata_json: dict = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Legacy compatibility for current router (to be removed in future phase).
# ---------------------------------------------------------------------------


class EnrollmentBase(BaseModel):
    student_id: int = Field(gt=0)
    course_id: int = Field(gt=0)
    semester: str = Field(min_length=1, max_length=64)
    status: str = Field(min_length=1, max_length=64)


class EnrollmentCreatePayload(EnrollmentBase):
    pass


class EnrollmentUpdatePayload(EnrollmentBase):
    pass


class EnrollmentResponse(EnrollmentBase):
    id: int
    tenant_id: str | None = None


class EnrollmentListResponse(BaseModel):
    enrollments: list[EnrollmentResponse]


class EnrollmentItemResponse(BaseModel):
    enrollment: EnrollmentResponse


class EnrollmentDeleteResponse(BaseModel):
    deleted: bool
    enrollment: EnrollmentResponse
