from __future__ import annotations

from datetime import date, datetime, time
from enum import Enum

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Date,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    JSON,
    Float,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class DayOfWeek(str, Enum):
    MONDAY = "monday"
    TUESDAY = "tuesday"
    WEDNESDAY = "wednesday"
    THURSDAY = "thursday"
    FRIDAY = "friday"
    SATURDAY = "saturday"
    SUNDAY = "sunday"


class RoomType(str, Enum):
    LECTURE = "lecture"
    LAB = "lab"
    SEMINAR = "seminar"


class SectionStatus(str, Enum):
    PLANNED = "planned"
    SCHEDULED = "scheduled"
    CANCELLED = "cancelled"


class InstructorRole(str, Enum):
    PRIMARY = "primary"
    ASSISTANT = "assistant"


class LessonStatus(str, Enum):
    PLANNED = "planned"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class AttendanceStatus(str, Enum):
    PRESENT = "present"
    ABSENT = "absent"
    LATE = "late"
    EXCUSED = "excused"


class TopicDifficultyLevel(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class TopicProgressStatus(str, Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


day_of_week_enum = SAEnum(
    DayOfWeek,
    name="scheduling_day_of_week",
    values_callable=lambda enum_cls: [item.value for item in enum_cls],
    validate_strings=True,
)
room_type_enum = SAEnum(
    RoomType,
    name="scheduling_room_type",
    values_callable=lambda enum_cls: [item.value for item in enum_cls],
    validate_strings=True,
)
section_status_enum = SAEnum(
    SectionStatus,
    name="scheduling_section_status",
    values_callable=lambda enum_cls: [item.value for item in enum_cls],
    validate_strings=True,
)
instructor_role_enum = SAEnum(
    InstructorRole,
    name="scheduling_instructor_role",
    values_callable=lambda enum_cls: [item.value for item in enum_cls],
    validate_strings=True,
)
lesson_status_enum = SAEnum(
    LessonStatus,
    name="scheduling_lesson_status",
    values_callable=lambda enum_cls: [item.value for item in enum_cls],
    validate_strings=True,
)
attendance_status_enum = SAEnum(
    AttendanceStatus,
    name="scheduling_attendance_status",
    values_callable=lambda enum_cls: [item.value for item in enum_cls],
    validate_strings=True,
)
topic_difficulty_level_enum = SAEnum(
    TopicDifficultyLevel,
    name="scheduling_topic_difficulty_level",
    values_callable=lambda enum_cls: [item.value for item in enum_cls],
    validate_strings=True,
)
topic_progress_status_enum = SAEnum(
    TopicProgressStatus,
    name="scheduling_topic_progress_status",
    values_callable=lambda enum_cls: [item.value for item in enum_cls],
    validate_strings=True,
)


class TimeSlotModel(Base):
    __tablename__ = "app_scheduling_time_slots"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("app_tenants.id", ondelete="CASCADE"),
        nullable=False,
    )
    day_of_week: Mapped[DayOfWeek] = mapped_column(day_of_week_enum, nullable=False)
    start_time: Mapped[time] = mapped_column(nullable=False)
    end_time: Mapped[time] = mapped_column(nullable=False)
    is_active: Mapped[bool] = mapped_column(nullable=False, default=True, server_default=text("true"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("NOW()"))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
        onupdate=text("NOW()"),
    )

    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="ux_scheduling_time_slots_tenant_id_id"),
        CheckConstraint("end_time > start_time", name="ck_scheduling_time_slots_end_after_start"),
        Index("ix_scheduling_time_slots_tenant_day_active", "tenant_id", "day_of_week", "is_active"),
    )


class ClassroomModel(Base):
    __tablename__ = "app_scheduling_classrooms"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("app_tenants.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    building: Mapped[str | None] = mapped_column(String(128), nullable=True)
    capacity: Mapped[int] = mapped_column(BigInteger, nullable=False)
    room_type: Mapped[RoomType] = mapped_column(room_type_enum, nullable=False)
    is_active: Mapped[bool] = mapped_column(nullable=False, default=True, server_default=text("true"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("NOW()"))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
        onupdate=text("NOW()"),
    )
    version: Mapped[int] = mapped_column(BigInteger, nullable=False, default=1, server_default=text("1"))

    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="ux_scheduling_classrooms_tenant_id_id"),
        UniqueConstraint("tenant_id", "name", name="ux_scheduling_classrooms_tenant_name"),
        CheckConstraint("capacity >= 0", name="ck_scheduling_classrooms_capacity_non_negative"),
        CheckConstraint("version >= 1", name="ck_scheduling_classrooms_version_positive"),
        Index("ix_scheduling_classrooms_tenant_active", "tenant_id", "is_active"),
    )


class CourseSectionModel(Base):
    __tablename__ = "app_scheduling_course_sections"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("app_tenants.id", ondelete="CASCADE"),
        nullable=False,
    )
    course_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    term_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    section_code: Mapped[str] = mapped_column(String(32), nullable=False)
    instructor_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    max_capacity: Mapped[int] = mapped_column(BigInteger, nullable=False)
    status: Mapped[SectionStatus] = mapped_column(
        section_status_enum,
        nullable=False,
        default=SectionStatus.PLANNED,
        server_default=text("'planned'"),
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("NOW()"))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
        onupdate=text("NOW()"),
    )
    version: Mapped[int] = mapped_column(BigInteger, nullable=False, default=1, server_default=text("1"))

    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="ux_scheduling_sections_tenant_id_id"),
        UniqueConstraint(
            "tenant_id",
            "course_id",
            "term_id",
            "section_code",
            name="ux_scheduling_sections_course_term_code",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "term_id"],
            ["app_enrollments_terms.tenant_id", "app_enrollments_terms.id"],
            ondelete="RESTRICT",
            name="fk_scheduling_sections_term",
        ),
        CheckConstraint("max_capacity >= 0", name="ck_scheduling_sections_capacity_non_negative"),
        CheckConstraint("version >= 1", name="ck_scheduling_sections_version_positive"),
        Index("ix_scheduling_sections_tenant_term_status", "tenant_id", "term_id", "status"),
        Index("ix_scheduling_sections_tenant_course", "tenant_id", "course_id"),
    )


class SectionScheduleModel(Base):
    __tablename__ = "app_scheduling_section_schedules"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("app_tenants.id", ondelete="CASCADE"),
        nullable=False,
    )
    section_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    time_slot_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    classroom_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    day_of_week: Mapped[DayOfWeek] = mapped_column(day_of_week_enum, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("NOW()"))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
        onupdate=text("NOW()"),
    )
    version: Mapped[int] = mapped_column(BigInteger, nullable=False, default=1, server_default=text("1"))

    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="ux_scheduling_section_schedules_tenant_id_id"),
        UniqueConstraint(
            "tenant_id",
            "classroom_id",
            "time_slot_id",
            "day_of_week",
            name="ux_scheduling_room_slot_day",
        ),
        UniqueConstraint("tenant_id", "section_id", name="ux_scheduling_one_schedule_per_section"),
        ForeignKeyConstraint(
            ["tenant_id", "section_id"],
            ["app_scheduling_course_sections.tenant_id", "app_scheduling_course_sections.id"],
            ondelete="CASCADE",
            name="fk_scheduling_section_schedules_section",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "time_slot_id"],
            ["app_scheduling_time_slots.tenant_id", "app_scheduling_time_slots.id"],
            ondelete="RESTRICT",
            name="fk_scheduling_section_schedules_time_slot",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "classroom_id"],
            ["app_scheduling_classrooms.tenant_id", "app_scheduling_classrooms.id"],
            ondelete="RESTRICT",
            name="fk_scheduling_section_schedules_classroom",
        ),
        CheckConstraint("version >= 1", name="ck_scheduling_section_schedules_version_positive"),
        Index("ix_scheduling_section_schedules_tenant_day_slot", "tenant_id", "day_of_week", "time_slot_id"),
    )


class InstructorAssignmentModel(Base):
    __tablename__ = "app_scheduling_instructor_assignments"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("app_tenants.id", ondelete="CASCADE"),
        nullable=False,
    )
    section_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    instructor_id: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[InstructorRole] = mapped_column(
        instructor_role_enum,
        nullable=False,
        default=InstructorRole.PRIMARY,
        server_default=text("'primary'"),
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("NOW()"))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
        onupdate=text("NOW()"),
    )

    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="ux_scheduling_instructor_assignments_tenant_id_id"),
        UniqueConstraint(
            "tenant_id",
            "section_id",
            "instructor_id",
            name="ux_scheduling_instructor_assignment_unique",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "section_id"],
            ["app_scheduling_course_sections.tenant_id", "app_scheduling_course_sections.id"],
            ondelete="CASCADE",
            name="fk_scheduling_instructor_assignments_section",
        ),
        Index("ix_scheduling_instructor_assignments_tenant_instructor", "tenant_id", "instructor_id"),
    )


class LessonInstanceModel(Base):
    __tablename__ = "app_scheduling_lesson_instances"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("app_tenants.id", ondelete="CASCADE"),
        nullable=False,
    )
    section_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    scheduled_date: Mapped[date] = mapped_column(Date, nullable=False)
    actual_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    topic_title: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[LessonStatus] = mapped_column(
        lesson_status_enum,
        nullable=False,
        default=LessonStatus.PLANNED,
        server_default=text("'planned'"),
    )
    notes: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict, server_default=text("'{}'::json"))
    created_by: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("NOW()"))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
        onupdate=text("NOW()"),
    )
    version: Mapped[int] = mapped_column(BigInteger, nullable=False, default=1, server_default=text("1"))

    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="ux_scheduling_lesson_instances_tenant_id_id"),
        ForeignKeyConstraint(
            ["tenant_id", "section_id"],
            ["app_scheduling_course_sections.tenant_id", "app_scheduling_course_sections.id"],
            ondelete="CASCADE",
            name="fk_scheduling_lesson_instances_section",
        ),
        CheckConstraint("version >= 1", name="ck_scheduling_lesson_instances_version_positive"),
        Index("ix_scheduling_lesson_instances_tenant_section_date", "tenant_id", "section_id", "scheduled_date"),
        Index("ix_scheduling_lesson_instances_tenant_status", "tenant_id", "status"),
    )


class LessonAttendanceModel(Base):
    __tablename__ = "app_scheduling_lesson_attendance"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("app_tenants.id", ondelete="CASCADE"),
        nullable=False,
    )
    lesson_instance_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    student_profile_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    attendance_status: Mapped[AttendanceStatus] = mapped_column(
        attendance_status_enum,
        nullable=False,
        default=AttendanceStatus.PRESENT,
        server_default=text("'present'"),
    )
    marked_by: Mapped[str] = mapped_column(String(255), nullable=False)
    marked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("NOW()"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("NOW()"))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
        onupdate=text("NOW()"),
    )
    version: Mapped[int] = mapped_column(BigInteger, nullable=False, default=1, server_default=text("1"))

    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="ux_scheduling_lesson_attendance_tenant_id_id"),
        UniqueConstraint(
            "tenant_id",
            "lesson_instance_id",
            "student_profile_id",
            name="ux_scheduling_lesson_attendance_one_row_per_student",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "lesson_instance_id"],
            ["app_scheduling_lesson_instances.tenant_id", "app_scheduling_lesson_instances.id"],
            ondelete="CASCADE",
            name="fk_scheduling_lesson_attendance_lesson_instance",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "student_profile_id"],
            ["app_students_profiles.tenant_id", "app_students_profiles.id"],
            ondelete="CASCADE",
            name="fk_scheduling_lesson_attendance_student_profile",
        ),
        CheckConstraint("version >= 1", name="ck_scheduling_lesson_attendance_version_positive"),
        Index("ix_scheduling_lesson_attendance_tenant_lesson", "tenant_id", "lesson_instance_id"),
        Index("ix_scheduling_lesson_attendance_tenant_student", "tenant_id", "student_profile_id"),
    )


class DisciplineModel(Base):
    __tablename__ = "app_scheduling_disciplines"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("app_tenants.id", ondelete="CASCADE"),
        nullable=False,
    )
    unique_code: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    credits: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    prerequisites_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict, server_default=text("'{}'::json"))
    learning_outcomes_json: Mapped[list] = mapped_column(JSON, nullable=False, default=list, server_default=text("'[]'::json"))
    is_active: Mapped[bool] = mapped_column(nullable=False, default=True, server_default=text("true"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("NOW()"))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
        onupdate=text("NOW()"),
    )
    version: Mapped[int] = mapped_column(BigInteger, nullable=False, default=1, server_default=text("1"))

    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="ux_scheduling_disciplines_tenant_id_id"),
        UniqueConstraint("tenant_id", "unique_code", name="ux_scheduling_disciplines_tenant_code"),
        CheckConstraint("credits IS NULL OR credits >= 0", name="ck_scheduling_disciplines_credits_non_negative"),
        CheckConstraint("version >= 1", name="ck_scheduling_disciplines_version_positive"),
        Index("ix_scheduling_disciplines_tenant_active", "tenant_id", "is_active"),
    )


class LessonTopicModel(Base):
    __tablename__ = "app_scheduling_lesson_topics"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("app_tenants.id", ondelete="CASCADE"),
        nullable=False,
    )
    discipline_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    module_num: Mapped[int] = mapped_column(BigInteger, nullable=False)
    topic_num: Mapped[int] = mapped_column(BigInteger, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    difficulty_level: Mapped[TopicDifficultyLevel] = mapped_column(
        topic_difficulty_level_enum,
        nullable=False,
        default=TopicDifficultyLevel.BEGINNER,
        server_default=text("'beginner'"),
    )
    recommended_materials_json: Mapped[list] = mapped_column(
        JSON,
        nullable=False,
        default=list,
        server_default=text("'[]'::json"),
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("NOW()"))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
        onupdate=text("NOW()"),
    )
    version: Mapped[int] = mapped_column(BigInteger, nullable=False, default=1, server_default=text("1"))

    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="ux_scheduling_lesson_topics_tenant_id_id"),
        UniqueConstraint(
            "tenant_id",
            "discipline_id",
            "module_num",
            "topic_num",
            name="ux_scheduling_lesson_topics_tenant_discipline_module_topic",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "discipline_id"],
            ["app_scheduling_disciplines.tenant_id", "app_scheduling_disciplines.id"],
            ondelete="CASCADE",
            name="fk_scheduling_lesson_topics_discipline",
        ),
        CheckConstraint("module_num >= 1", name="ck_scheduling_lesson_topics_module_num_positive"),
        CheckConstraint("topic_num >= 1", name="ck_scheduling_lesson_topics_topic_num_positive"),
        CheckConstraint("version >= 1", name="ck_scheduling_lesson_topics_version_positive"),
        Index("ix_scheduling_lesson_topics_tenant_discipline", "tenant_id", "discipline_id"),
        Index("ix_scheduling_lesson_topics_tenant_difficulty", "tenant_id", "difficulty_level"),
    )


class StudentTopicProgressModel(Base):
    __tablename__ = "app_scheduling_student_topic_progress"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("app_tenants.id", ondelete="CASCADE"),
        nullable=False,
    )
    student_profile_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    topic_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    discipline_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    first_seen_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    last_reviewed_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[TopicProgressStatus] = mapped_column(
        topic_progress_status_enum,
        nullable=False,
        default=TopicProgressStatus.NOT_STARTED,
        server_default=text("'not_started'"),
    )
    materials_opened: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0, server_default=text("0"))
    materials_completed: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0, server_default=text("0"))
    quiz_attempts: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0, server_default=text("0"))
    quiz_best_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("NOW()"))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
        onupdate=text("NOW()"),
    )
    version: Mapped[int] = mapped_column(BigInteger, nullable=False, default=1, server_default=text("1"))

    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="ux_scheduling_student_topic_progress_tenant_id_id"),
        UniqueConstraint(
            "tenant_id",
            "student_profile_id",
            "topic_id",
            name="ux_scheduling_student_topic_progress_student_topic",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "student_profile_id"],
            ["app_students_profiles.tenant_id", "app_students_profiles.id"],
            ondelete="CASCADE",
            name="fk_scheduling_student_topic_progress_student_profile",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "topic_id"],
            ["app_scheduling_lesson_topics.tenant_id", "app_scheduling_lesson_topics.id"],
            ondelete="CASCADE",
            name="fk_scheduling_student_topic_progress_topic",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "discipline_id"],
            ["app_scheduling_disciplines.tenant_id", "app_scheduling_disciplines.id"],
            ondelete="CASCADE",
            name="fk_scheduling_student_topic_progress_discipline",
        ),
        CheckConstraint("materials_opened >= 0", name="ck_sched_stp_mat_open_ge0"),
        CheckConstraint(
            "materials_completed >= 0",
            name="ck_sched_stp_mat_done_ge0",
        ),
        CheckConstraint("quiz_attempts >= 0", name="ck_sched_stp_quiz_attempts_ge0"),
        CheckConstraint(
            "quiz_best_score IS NULL OR (quiz_best_score >= 0 AND quiz_best_score <= 100)",
            name="ck_sched_stp_quiz_score_range",
        ),
        CheckConstraint("version >= 1", name="ck_sched_stp_ver_ge1"),
        Index("ix_scheduling_student_topic_progress_tenant_student", "tenant_id", "student_profile_id"),
        Index("ix_scheduling_student_topic_progress_tenant_topic", "tenant_id", "topic_id"),
        Index("ix_scheduling_student_topic_progress_tenant_status", "tenant_id", "status"),
    )
