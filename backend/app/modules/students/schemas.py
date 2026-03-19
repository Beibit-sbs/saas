from pydantic import BaseModel, Field


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
