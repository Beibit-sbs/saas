from pydantic import BaseModel, Field


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
