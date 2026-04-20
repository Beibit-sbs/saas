from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.modules.students.models import (
    StudentAcademicLevel,
    StudentAdmissionSource,
    StudentProgramBindingState,
    StudentStatus,
)


class StudentBase(BaseModel):
    student_id: str = Field(min_length=1, max_length=64)
    first_name: str = Field(min_length=1, max_length=128)
    last_name: str = Field(min_length=1, max_length=128)
    email: str = Field(min_length=3, max_length=255)
    status: str = Field(min_length=1, max_length=64)


class StudentCreatePayload(StudentBase):
    pass


class StudentUpdatePayload(StudentBase):
    pass


class StudentResponse(StudentBase):
    id: int
    created_at: str
    tenant_id: str | None = None


class StudentListResponse(BaseModel):
    students: list[StudentResponse]


class StudentItemResponse(BaseModel):
    student: StudentResponse


class StudentDeleteResponse(BaseModel):
    deleted: bool
    student: StudentResponse


class StudentProfileCreateSchema(BaseModel):
    person_id: int = Field(gt=0)
    student_number: str = Field(min_length=1, max_length=64)
    cohort_year: int = Field(ge=2000, le=2100)
    academic_level: StudentAcademicLevel | None = None
    admission_source: StudentAdmissionSource = StudentAdmissionSource.ADMISSIONS_WORKFLOW
    metadata_json: dict = Field(default_factory=dict)


class StudentProfileReadSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: int
    person_id: int
    student_number: str
    cohort_year: int
    academic_level: StudentAcademicLevel | None
    current_status: StudentStatus
    admission_source: StudentAdmissionSource
    metadata_json: dict
    version: int
    created_by: str
    updated_by: str
    created_at: datetime
    updated_at: datetime


class StudentProfileListResponseSchema(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[StudentProfileReadSchema]


class StudentStatusHistoryReadSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: int
    student_profile_id: int
    from_status: StudentStatus | None
    to_status: StudentStatus
    reason: str | None
    actor_id: str
    changed_at: datetime
    metadata_json: dict


class StudentStatusChangeSchema(BaseModel):
    expected_version: int = Field(ge=1)
    to_status: StudentStatus
    reason: str | None = Field(default=None, max_length=500)
    metadata_json: dict = Field(default_factory=dict)


class StudentProgramBindingCreateSchema(BaseModel):
    student_profile_id: int = Field(gt=0)
    program_id: int = Field(gt=0)
    is_primary: bool = True
    binding_state: StudentProgramBindingState = StudentProgramBindingState.ACTIVE
    started_at: datetime | None = None
    metadata_json: dict = Field(default_factory=dict)


class StudentProgramBindingReadSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: int
    student_profile_id: int
    program_id: int
    is_primary: bool
    binding_state: StudentProgramBindingState
    started_at: datetime
    ended_at: datetime | None
    metadata_json: dict
    version: int
    created_by: str
    updated_by: str
    created_at: datetime
    updated_at: datetime


class StudentProfileMutationResponse(BaseModel):
    student: StudentProfileReadSchema
    idempotent_replay: bool = False


class StudentProgramBindingMutationResponse(BaseModel):
    binding: StudentProgramBindingReadSchema
    idempotent_replay: bool = False


class StudentProgramBindingConsistencyIssueSchema(BaseModel):
    student_profile_id: int
    issue_type: str
    active_binding_count: int
    active_primary_count: int
    program_ids: list[int] = Field(default_factory=list)


class AdmissionsProvisionStudentRequestSchema(BaseModel):
    person_id: int = Field(gt=0)
    program_id: int = Field(gt=0)
    student_number: str = Field(min_length=1, max_length=64)
    cohort_year: int = Field(ge=2000, le=2100)
    metadata_json: dict = Field(default_factory=dict)


class AdmissionsProvisionStudentResultSchema(BaseModel):
    student_profile: StudentProfileReadSchema
    active_primary_program: StudentProgramBindingReadSchema
