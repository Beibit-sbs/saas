from pydantic import BaseModel, Field


class RecordBase(BaseModel):
    student_id: int = Field(gt=0)
    course_id: int = Field(gt=0)
    grade: str = Field(min_length=1, max_length=16)
    semester: str = Field(min_length=1, max_length=64)
    status: str = Field(min_length=1, max_length=64)
    notes: str | None = Field(default=None, max_length=1000)


class RecordCreatePayload(RecordBase):
    pass


class RecordUpdatePayload(RecordBase):
    pass


class RecordResponse(RecordBase):
    id: int
    tenant_id: str | None = None


class RecordListResponse(BaseModel):
    records: list[RecordResponse]


class RecordItemResponse(BaseModel):
    record: RecordResponse


class RecordDeleteResponse(BaseModel):
    deleted: bool
    record: RecordResponse


class AcademicRecordConsistencyIssueSchema(BaseModel):
    issue_type: str
    record_id: int
    student_id: int | None = None
    course_id: int | None = None


class AcademicRecordConsistencyReportSchema(BaseModel):
    record_count: int
    issue_count: int
    issues: list[AcademicRecordConsistencyIssueSchema]
