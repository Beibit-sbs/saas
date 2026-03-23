from __future__ import annotations

from datetime import datetime
from enum import Enum

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    SmallInteger,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class StudentStatus(str, Enum):
    ADMITTED = "admitted"
    ACTIVE = "active"
    INACTIVE = "inactive"
    LEAVE_OF_ABSENCE = "leave_of_absence"
    SUSPENDED = "suspended"
    GRADUATED = "graduated"
    WITHDRAWN = "withdrawn"


class StudentAcademicLevel(str, Enum):
    UNDERGRADUATE = "undergraduate"
    GRADUATE = "graduate"
    DOCTORAL = "doctoral"
    NON_DEGREE = "non_degree"
    CERTIFICATE = "certificate"


class StudentAdmissionSource(str, Enum):
    ADMISSIONS_WORKFLOW = "admissions_workflow"
    MANUAL = "manual"
    EXTERNAL_SYNC = "external_sync"
    MIGRATION = "migration"


class StudentProgramBindingState(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


student_status_enum = SAEnum(StudentStatus, name="student_status")
student_academic_level_enum = SAEnum(
    StudentAcademicLevel,
    name="student_academic_level",
)
student_admission_source_enum = SAEnum(
    StudentAdmissionSource,
    name="student_admission_source",
)
student_program_binding_state_enum = SAEnum(
    StudentProgramBindingState,
    name="student_program_binding_state",
)


class StudentProfileModel(Base):
    """
    Canonical student node in the University Core Graph.

    Design notes:
    - one student profile per Person inside a tenant
    - canonical student_number is tenant-scoped and immutable in practice
    - current_status is the cached current state; full audit trail lives in status history
    - links to tenant-owned Person using composite tenant-safe FK
    """

    __tablename__ = "app_students_profiles"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("app_tenants.id", ondelete="CASCADE"),
        nullable=False,
    )
    person_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    student_number: Mapped[str] = mapped_column(String(64), nullable=False)
    cohort_year: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    academic_level: Mapped[StudentAcademicLevel | None] = mapped_column(
        student_academic_level_enum,
        nullable=True,
    )
    current_status: Mapped[StudentStatus] = mapped_column(
        student_status_enum,
        nullable=False,
        default=StudentStatus.ADMITTED,
        server_default=text("'admitted'"),
    )
    admission_source: Mapped[StudentAdmissionSource] = mapped_column(
        student_admission_source_enum,
        nullable=False,
        default=StudentAdmissionSource.ADMISSIONS_WORKFLOW,
        server_default=text("'admissions_workflow'"),
    )
    metadata_json: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )
    version: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        default=1,
        server_default=text("1"),
    )
    created_by: Mapped[str] = mapped_column(String(255), nullable=False)
    updated_by: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
        onupdate=text("NOW()"),
    )

    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="ux_students_profiles_tenant_id_id"),
        UniqueConstraint("tenant_id", "person_id", name="ux_students_profiles_tenant_person"),
        UniqueConstraint(
            "tenant_id",
            "student_number",
            name="ux_students_profiles_tenant_student_number",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "person_id"],
            ["app_profiles_people.tenant_id", "app_profiles_people.id"],
            ondelete="RESTRICT",
        ),
        CheckConstraint("version >= 1", name="ck_students_profiles_version_positive"),
        CheckConstraint(
            "cohort_year >= 2000 AND cohort_year <= 2100",
            name="ck_students_profiles_cohort_year_range",
        ),
        Index("ix_students_profiles_tenant_status", "tenant_id", "current_status"),
        Index("ix_students_profiles_tenant_cohort", "tenant_id", "cohort_year"),
        Index("ix_students_profiles_tenant_person", "tenant_id", "person_id"),
    )


class StudentStatusHistoryModel(Base):
    """
    Append-only audit trail of student status transitions.

    current_status is derived by ordering history rows by (changed_at DESC, id DESC)
    if the service layer chooses not to trust the cached field on student_profiles.
    """

    __tablename__ = "app_students_status_history"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("app_tenants.id", ondelete="CASCADE"),
        nullable=False,
    )
    student_profile_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    from_status: Mapped[StudentStatus | None] = mapped_column(
        student_status_enum,
        nullable=True,
    )
    to_status: Mapped[StudentStatus] = mapped_column(
        student_status_enum,
        nullable=False,
    )
    reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    actor_id: Mapped[str] = mapped_column(String(255), nullable=False)
    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
    )
    metadata_json: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )

    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="ux_students_status_history_tenant_id_id"),
        ForeignKeyConstraint(
            ["tenant_id", "student_profile_id"],
            ["app_students_profiles.tenant_id", "app_students_profiles.id"],
            ondelete="CASCADE",
        ),
        CheckConstraint(
            "from_status IS NULL OR from_status <> to_status",
            name="ck_students_status_history_transition_changed",
        ),
        Index(
            "ix_students_status_history_tenant_student_changed_desc",
            "tenant_id",
            "student_profile_id",
            "changed_at",
        ),
        Index(
            "ix_students_status_history_tenant_to_status_changed_desc",
            "tenant_id",
            "to_status",
            "changed_at",
        ),
    )


class StudentProgramBindingModel(Base):
    """
    Program membership edges for a student.

    Phase 1 rules:
    - supports one active primary binding per student
    - supports active/inactive state only
    - allows future extension for transfers, secondary programs, double degree
    """

    __tablename__ = "app_students_program_bindings"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("app_tenants.id", ondelete="CASCADE"),
        nullable=False,
    )
    student_profile_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    program_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    is_primary: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("true"),
    )
    binding_state: Mapped[StudentProgramBindingState] = mapped_column(
        student_program_binding_state_enum,
        nullable=False,
        default=StudentProgramBindingState.ACTIVE,
        server_default=text("'active'"),
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
    )
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    metadata_json: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )
    version: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        default=1,
        server_default=text("1"),
    )
    created_by: Mapped[str] = mapped_column(String(255), nullable=False)
    updated_by: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
        onupdate=text("NOW()"),
    )

    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "id",
            name="ux_students_program_bindings_tenant_id_id",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "student_profile_id"],
            ["app_students_profiles.tenant_id", "app_students_profiles.id"],
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "program_id"],
            ["app_profiles_programs.tenant_id", "app_profiles_programs.id"],
            ondelete="RESTRICT",
        ),
        CheckConstraint(
            "version >= 1",
            name="ck_students_program_bindings_version_positive",
        ),
        CheckConstraint(
            "ended_at IS NULL OR ended_at >= started_at",
            name="ck_students_program_bindings_end_after_start",
        ),
        Index(
            "ix_students_program_bindings_tenant_student_state",
            "tenant_id",
            "student_profile_id",
            "binding_state",
        ),
        Index(
            "ix_students_program_bindings_tenant_program_state",
            "tenant_id",
            "program_id",
            "binding_state",
        ),
        Index(
            "ix_students_program_bindings_one_active_primary",
            "tenant_id",
            "student_profile_id",
            unique=True,
            postgresql_where=text("binding_state = 'active' AND is_primary = true"),
        ),
        Index(
            "ix_students_program_bindings_one_active_program",
            "tenant_id",
            "student_profile_id",
            "program_id",
            unique=True,
            postgresql_where=text("binding_state = 'active'"),
        ),
    )
