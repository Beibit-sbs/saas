from pydantic import BaseModel, Field


class ProgramBase(BaseModel):
    program_code: str = Field(min_length=1, max_length=64)
    title: str = Field(min_length=1, max_length=255)
    degree_type: str = Field(min_length=1, max_length=64)
    faculty: str = Field(min_length=1, max_length=128)
    status: str = Field(min_length=1, max_length=64)
    accreditation_body: str | None = Field(default=None, max_length=128)


class ProgramCreatePayload(ProgramBase):
    pass


class ProgramUpdatePayload(ProgramBase):
    pass


class ProgramResponse(ProgramBase):
    id: int
    tenant_id: str | None = None


class ProgramListResponse(BaseModel):
    programs: list[ProgramResponse]


class ProgramItemResponse(BaseModel):
    program: ProgramResponse


class ProgramDeleteResponse(BaseModel):
    deleted: bool
    program: ProgramResponse


class ProgramConsistencyIssueSchema(BaseModel):
    issue_type: str
    program_id: int | None = None
    program_code: str | None = None


class ProgramConsistencyReportSchema(BaseModel):
    program_count: int
    issue_count: int
    issues: list[ProgramConsistencyIssueSchema]
