from pydantic import BaseModel, Field


class FacultyBase(BaseModel):
    faculty_id: str = Field(min_length=1, max_length=64)
    first_name: str = Field(min_length=1, max_length=128)
    last_name: str = Field(min_length=1, max_length=128)
    department: str = Field(min_length=1, max_length=128)
    email: str = Field(min_length=3, max_length=255)
    status: str = Field(min_length=1, max_length=64)


class FacultyCreatePayload(FacultyBase):
    pass


class FacultyUpdatePayload(FacultyBase):
    pass


class FacultyResponse(FacultyBase):
    id: int
    tenant_id: str | None = None


class FacultyListResponse(BaseModel):
    faculty: list[FacultyResponse]


class FacultyItemResponse(BaseModel):
    faculty: FacultyResponse


class FacultyDeleteResponse(BaseModel):
    deleted: bool
    faculty: FacultyResponse


class FacultyConsistencyIssueSchema(BaseModel):
    issue_type: str
    faculty_row_id: int | None = None
    faculty_id: str | None = None
    email: str | None = None


class FacultyConsistencyReportSchema(BaseModel):
    faculty_count: int
    issue_count: int
    issues: list[FacultyConsistencyIssueSchema]


class FacultyWorkloadSchema(BaseModel):
    faculty_id: str
    department: str
    term_id: int
    total_credit_hours: int
    max_credit_hours: int
    fte_ratio: float
    effective_capacity: int
    utilization: float
    primary_assignments: int
    assistant_assignments: int
    alerts: list[str]


class FacultyWorkloadItemResponse(BaseModel):
    workload: FacultyWorkloadSchema


class FacultyWorkloadListResponse(BaseModel):
    workloads: list[FacultyWorkloadSchema]


class FacultyCapacityUpdatePayload(BaseModel):
    max_credit_hours: int = Field(ge=1, le=100)
    fte_ratio: float = Field(gt=0.0, le=1.0)


class FacultyContractBase(BaseModel):
    faculty_id: str = Field(min_length=1, max_length=64)
    contract_type: str = Field(min_length=1, max_length=64)
    start_date: str = Field(min_length=4, max_length=32)
    end_date: str | None = Field(default=None, max_length=32)
    fte_ratio: float = Field(gt=0.0, le=1.0)
    max_credit_hours: int = Field(ge=1, le=100)
    status: str = Field(min_length=1, max_length=64)
    notes: str | None = Field(default=None, max_length=1000)
    termination_reason: str | None = Field(default=None, max_length=500)


class FacultyContractCreatePayload(FacultyContractBase):
    pass


class FacultyContractStatusUpdatePayload(BaseModel):
    status: str = Field(min_length=1, max_length=64)
    notes: str | None = Field(default=None, max_length=1000)


class FacultyContractResponse(FacultyContractBase):
    id: int
    tenant_id: str | None = None


class FacultyContractItemResponse(BaseModel):
    contract: FacultyContractResponse


class FacultyContractListResponse(BaseModel):
    contracts: list[FacultyContractResponse]


# --- Teaching Quality schemas (Phase IV-IV1) ---

class TeachingQualityCreatePayload(BaseModel):
    faculty_id: str = Field(min_length=1, max_length=64)
    course_id: str = Field(min_length=1, max_length=64)
    term_id: int = Field(ge=1)
    quality_score: float = Field(ge=0.0, le=100.0)
    kpi_score: float = Field(ge=0.0, le=100.0)
    improvement_plan: str | None = Field(default=None, max_length=2000)
    notes: str | None = Field(default=None, max_length=1000)


class TeachingQualityResponse(TeachingQualityCreatePayload):
    id: int
    tenant_id: str | None = None


class TeachingQualityItemResponse(BaseModel):
    record: TeachingQualityResponse


class TeachingQualityListResponse(BaseModel):
    records: list[TeachingQualityResponse]


# --- Proctoring schemas (Phase IV-IV2) ---

class ProctoringCreatePayload(BaseModel):
    exam_id: str = Field(min_length=1, max_length=64)
    faculty_id: str = Field(min_length=1, max_length=64)
    room_id: str | None = Field(default=None, max_length=64)
    violation_type: str = Field(min_length=1, max_length=128)
    severity: str = Field(min_length=1, max_length=32)
    student_id: str | None = Field(default=None, max_length=64)
    notes: str | None = Field(default=None, max_length=2000)
    status: str = Field(default="open", min_length=1, max_length=32)


class ProctoringResponse(ProctoringCreatePayload):
    id: int
    tenant_id: str | None = None


class ProctoringItemResponse(BaseModel):
    record: ProctoringResponse


class ProctoringListResponse(BaseModel):
    records: list[ProctoringResponse]


# --- Office hours schemas (Phase IV-IV3) ---

class OfficeHoursCreatePayload(BaseModel):
    faculty_id: str = Field(min_length=1, max_length=64)
    scheduled_at: str = Field(min_length=1, max_length=64)
    duration_minutes: int = Field(ge=5, le=480)
    location: str | None = Field(default=None, max_length=256)
    status: str = Field(default="scheduled", min_length=1, max_length=32)
    student_id: str | None = Field(default=None, max_length=64)
    notes: str | None = Field(default=None, max_length=2000)
    no_show: bool = Field(default=False)


class OfficeHoursResponse(OfficeHoursCreatePayload):
    id: int
    tenant_id: str | None = None


class OfficeHoursItemResponse(BaseModel):
    record: OfficeHoursResponse


class OfficeHoursListResponse(BaseModel):
    records: list[OfficeHoursResponse]
