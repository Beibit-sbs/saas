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
