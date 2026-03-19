from pydantic import BaseModel, Field


class CourseBase(BaseModel):
    course_code: str = Field(min_length=1, max_length=64)
    title: str = Field(min_length=1, max_length=255)
    credits: int = Field(ge=0)
    program_id: int = Field(gt=0)
    status: str = Field(min_length=1, max_length=64)


class CourseCreatePayload(CourseBase):
    pass


class CourseUpdatePayload(CourseBase):
    pass


class CourseResponse(CourseBase):
    id: int
    tenant_id: str | None = None


class CourseListResponse(BaseModel):
    courses: list[CourseResponse]


class CourseItemResponse(BaseModel):
    course: CourseResponse


class CourseDeleteResponse(BaseModel):
    deleted: bool
    course: CourseResponse
