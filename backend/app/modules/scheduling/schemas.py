from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.modules.scheduling.models import (
    AttendanceStatus,
    DayOfWeek,
    InstructorRole,
    LessonStatus,
    SectionStatus,
    TopicDifficultyLevel,
    TopicProgressStatus,
)


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


class LessonInstanceCreateSchema(BaseModel):
    scheduled_date: date
    topic_title: str = Field(min_length=1, max_length=255)
    notes: str | None = Field(default=None, max_length=2000)
    metadata_json: dict = Field(default_factory=dict)


class LessonInstanceListResponseSchema(BaseModel):
    total: int
    page: int
    page_size: int
    items: list["LessonInstanceReadSchema"]


class LessonAttendanceUpsertSchema(BaseModel):
    student_profile_id: int = Field(gt=0)
    attendance_status: AttendanceStatus


class LessonAttendanceReadSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: int
    lesson_instance_id: int
    student_profile_id: int
    attendance_status: AttendanceStatus
    marked_by: str
    marked_at: datetime
    created_at: datetime
    updated_at: datetime
    version: int


class LessonAttendanceListResponseSchema(BaseModel):
    total: int
    items: list[LessonAttendanceReadSchema]


class DisciplineCreateSchema(BaseModel):
    unique_code: str = Field(min_length=1, max_length=64)
    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)
    credits: int | None = Field(default=None, ge=0)
    prerequisites_json: dict = Field(default_factory=dict)
    learning_outcomes_json: list = Field(default_factory=list)


class DisciplineReadSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: int
    unique_code: str
    title: str
    description: str | None
    credits: int | None
    prerequisites_json: dict
    learning_outcomes_json: list
    is_active: bool
    created_at: datetime
    updated_at: datetime
    version: int


class DisciplineListResponseSchema(BaseModel):
    total: int
    items: list[DisciplineReadSchema]


class LessonTopicCreateSchema(BaseModel):
    module_num: int = Field(ge=1)
    topic_num: int = Field(ge=1)
    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)
    difficulty_level: TopicDifficultyLevel = TopicDifficultyLevel.BEGINNER
    recommended_materials_json: list = Field(default_factory=list)


class LessonTopicReadSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: int
    discipline_id: int
    module_num: int
    topic_num: int
    title: str
    description: str | None
    difficulty_level: TopicDifficultyLevel
    recommended_materials_json: list
    created_at: datetime
    updated_at: datetime
    version: int


class LessonTopicListResponseSchema(BaseModel):
    total: int
    items: list[LessonTopicReadSchema]


class StudentTopicProgressUpsertSchema(BaseModel):
    discipline_id: int = Field(gt=0)
    first_seen_date: date | None = None
    last_reviewed_date: date | None = None
    status: TopicProgressStatus
    materials_opened: int = Field(ge=0)
    materials_completed: int = Field(ge=0)
    quiz_attempts: int = Field(ge=0)
    quiz_best_score: float | None = Field(default=None, ge=0, le=100)


class StudentTopicProgressReadSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: int
    student_profile_id: int
    topic_id: int
    discipline_id: int
    first_seen_date: date | None
    last_reviewed_date: date | None
    status: TopicProgressStatus
    materials_opened: int
    materials_completed: int
    quiz_attempts: int
    quiz_best_score: float | None
    created_at: datetime
    updated_at: datetime
    version: int


class StudentTopicProgressListResponseSchema(BaseModel):
    total: int
    items: list[StudentTopicProgressReadSchema]


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


class LessonInstanceReadSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: int
    section_id: int
    scheduled_date: date
    actual_date: date | None
    topic_title: str
    status: LessonStatus
    notes: str | None
    metadata_json: dict
    created_by: str
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
    
    


class SchedulingConsistencyIssueSchema(BaseModel):
    issue_type: str
    section_id: int | None = None
    lesson_attendance_id: int | None = None
    student_profile_id: int | None = None
    detail: str | None = None


class SchedulingConsistencyReportSchema(BaseModel):
    section_count: int
    attendance_count: int
    issue_count: int
    issues: list[SchedulingConsistencyIssueSchema]
