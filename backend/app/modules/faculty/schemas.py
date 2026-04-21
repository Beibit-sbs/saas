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
