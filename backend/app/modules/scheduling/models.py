from __future__ import annotations

from datetime import datetime, time
from enum import Enum

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
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


day_of_week_enum = SAEnum(DayOfWeek, name="scheduling_day_of_week")
room_type_enum = SAEnum(RoomType, name="scheduling_room_type")
section_status_enum = SAEnum(SectionStatus, name="scheduling_section_status")
instructor_role_enum = SAEnum(InstructorRole, name="scheduling_instructor_role")


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
