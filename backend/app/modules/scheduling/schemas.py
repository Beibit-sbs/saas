from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.modules.scheduling.models import DayOfWeek, InstructorRole, SectionStatus


class CourseSectionCreateSchema(BaseModel):
    course_id: int = Field(gt=0)
    term_id: int = Field(gt=0)
    section_code: str = Field(min_length=1, max_length=32)
    instructor_id: str | None = Field(default=None, max_length=255)
    max_capacity: int = Field(ge=0)


class SectionScheduleCreateSchema(BaseModel):
    time_slot_id: int = Field(gt=0)
    classroom_id: int = Field(gt=0)
    day_of_week: DayOfWeek


class SectionRescheduleSchema(BaseModel):
    time_slot_id: int = Field(gt=0)
    classroom_id: int = Field(gt=0)
    day_of_week: DayOfWeek
    expected_version: int = Field(ge=1)


class SectionCancelSchema(BaseModel):
    expected_version: int = Field(ge=1)


class InstructorAssignmentSchema(BaseModel):
    instructor_id: str = Field(min_length=1, max_length=255)
    role: InstructorRole = InstructorRole.PRIMARY


class CourseSectionReadSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: int
    course_id: int
    term_id: int
    section_code: str
    instructor_id: str | None
    max_capacity: int
    status: SectionStatus
    created_at: datetime
    updated_at: datetime
    version: int


class SectionScheduleReadSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: int
    section_id: int
    time_slot_id: int
    classroom_id: int
    day_of_week: DayOfWeek
    created_at: datetime
    updated_at: datetime
    version: int


class StudentScheduleItemSchema(BaseModel):
    student_profile_id: int
    section_id: int
    course_id: int
    term_id: int
    day_of_week: DayOfWeek
    start_time: str
    end_time: str
    classroom_id: int
    classroom_name: str | None


class InstructorScheduleItemSchema(BaseModel):
    instructor_id: str
    section_id: int
    course_id: int
    term_id: int
    day_of_week: DayOfWeek
    start_time: str
    end_time: str
    classroom_id: int
    classroom_name: str | None


class RoomScheduleItemSchema(BaseModel):
    classroom_id: int
    section_id: int
    course_id: int
    term_id: int
    day_of_week: DayOfWeek
    start_time: str
    end_time: str
    instructor_id: str | None


class ConflictReportSchema(BaseModel):
    has_room_conflict: bool
    room_conflict_section_id: int | None
    instructor_conflicts: list[dict]
