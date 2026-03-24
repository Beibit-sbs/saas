from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import Enum

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class EnrollmentStatus(str, Enum):
    PENDING = "pending"
    ENROLLED = "enrolled"
    WAITLIST = "waitlist"
    DROPPED = "dropped"
    COMPLETED = "completed"
    WITHDRAWN = "withdrawn"
    SUSPENDED = "suspended"


class EnrollmentType(str, Enum):
    REGULAR = "regular"
    AUDIT = "audit"
    RETAKE = "retake"
    TRANSFER_CREDIT = "transfer_credit"


enrollment_status_enum = SAEnum(EnrollmentStatus, name="enrollment_status")
enrollment_type_enum = SAEnum(EnrollmentType, name="enrollment_type")


class AcademicTermModel(Base):
    """
    Minimal placeholder for academic terms.

    Term is an external academic reference; Enrollment links to it via
    composite (tenant_id, term_id) FK.  A full canonical Terms module
    may replace this table in a future phase.
    """

    __tablename__ = "app_enrollments_terms"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("app_tenants.id", ondelete="CASCADE"),
        nullable=False,
    )
    term_code: Mapped[str] = mapped_column(String(64), nullable=False)
    term_name: Mapped[str] = mapped_column(String(255), nullable=False)
    start_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    end_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="active",
        server_default=text("'active'"),
    )
    metadata_json: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )
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
        UniqueConstraint("tenant_id", "id", name="ux_enrollment_terms_tenant_id_id"),
        UniqueConstraint("tenant_id", "term_code", name="ux_enrollment_terms_tenant_code"),
        CheckConstraint(
            "status IN ('active', 'inactive', 'archived')",
            name="ck_enrollment_terms_status",
        ),
        Index("ix_enrollment_terms_tenant_status", "tenant_id", "status"),
    )


class EnrollmentModel(Base):
    """
    Canonical enrollment edge in the University Core Graph.

    Design notes:
    - tenant-scoped and RLS-ready
    - links only to canonical Student directly; Course/Term stay external references
    - current status is cached on the row while full audit trail lives in history
    """

    __tablename__ = "app_enrollments_enrollments"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("app_tenants.id", ondelete="CASCADE"),
        nullable=False,
    )
    student_profile_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    course_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    term_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    enrollment_status: Mapped[EnrollmentStatus] = mapped_column(
        enrollment_status_enum,
        nullable=False,
        default=EnrollmentStatus.ENROLLED,
        server_default=text("'enrolled'"),
    )
    enrollment_type: Mapped[EnrollmentType] = mapped_column(
        enrollment_type_enum,
        nullable=False,
        default=EnrollmentType.REGULAR,
        server_default=text("'regular'"),
    )
    enrolled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
    )
    dropped_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # Grades — nullable placeholders; grade logic lives in the future Grades module.
    grade_code: Mapped[str | None] = mapped_column(String(32), nullable=True)
    grade_points: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
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
        UniqueConstraint("tenant_id", "id", name="ux_enrollments_tenant_id_id"),
        ForeignKeyConstraint(
            ["tenant_id", "student_profile_id"],
            ["app_students_profiles.tenant_id", "app_students_profiles.id"],
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "term_id"],
            ["app_enrollments_terms.tenant_id", "app_enrollments_terms.id"],
            ondelete="RESTRICT",
            name="fk_enrollments_tenant_term_id",
        ),
        CheckConstraint("version >= 1", name="ck_enrollments_version_positive"),
        CheckConstraint(
            "dropped_at IS NULL OR dropped_at >= enrolled_at",
            name="ck_enrollments_dropped_after_enrolled",
        ),
        Index(
            "ix_enrollments_tenant_student_status",
            "tenant_id",
            "student_profile_id",
            "enrollment_status",
        ),
        Index(
            "ix_enrollments_tenant_course_term_status",
            "tenant_id",
            "course_id",
            "term_id",
            "enrollment_status",
        ),
        Index(
            "ix_enrollments_tenant_student_term",
            "tenant_id",
            "student_profile_id",
            "term_id",
        ),
        Index(
            "ix_enrollments_tenant_enrolled_desc",
            "tenant_id",
            "enrolled_at",
        ),
        Index(
            "ix_enrollments_one_active_triplet",
            "tenant_id",
            "student_profile_id",
            "course_id",
            "term_id",
            unique=True,
            postgresql_where=text(
                "enrollment_status IN ('pending', 'enrolled', 'waitlist', 'suspended')"
            ),
        ),
    )


class EnrollmentStatusHistoryModel(Base):
    """Append-only audit log of enrollment status transitions."""

    __tablename__ = "app_enrollments_status_history"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("app_tenants.id", ondelete="CASCADE"),
        nullable=False,
    )
    enrollment_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    version: Mapped[int] = mapped_column(BigInteger, nullable=False)
    from_status: Mapped[EnrollmentStatus | None] = mapped_column(
        enrollment_status_enum,
        nullable=True,
    )
    to_status: Mapped[EnrollmentStatus] = mapped_column(
        enrollment_status_enum,
        nullable=False,
    )
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
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
        UniqueConstraint(
            "tenant_id",
            "id",
            name="ux_enrollment_status_history_tenant_id_id",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "enrollment_id"],
            ["app_enrollments_enrollments.tenant_id", "app_enrollments_enrollments.id"],
            ondelete="CASCADE",
        ),
        CheckConstraint(
            "from_status IS NULL OR from_status <> to_status",
            name="ck_enrollment_status_history_transition_changed",
        ),
        CheckConstraint(
            "version >= 1",
            name="ck_enrollment_status_history_version_positive",
        ),
        Index(
            "ix_enrollment_status_history_tenant_enrollment_changed",
            "tenant_id",
            "enrollment_id",
            "changed_at",
        ),
        Index(
            "ix_enrollment_status_history_tenant_to_status_changed",
            "tenant_id",
            "to_status",
            "changed_at",
        ),
    )
