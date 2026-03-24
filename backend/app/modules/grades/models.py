from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
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


class GradingScaleModel(Base):
    __tablename__ = "app_grades_scales"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("app_tenants.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=text("true"))

    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="ux_grades_scales_tenant_id_id"),
        UniqueConstraint("tenant_id", "name", name="ux_grades_scales_tenant_name"),
        Index("ix_grades_scales_tenant_active", "tenant_id", "is_active"),
    )


class GradingScaleItemModel(Base):
    __tablename__ = "app_grades_scale_items"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("app_tenants.id", ondelete="CASCADE"),
        nullable=False,
    )
    scale_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    grade_code: Mapped[str] = mapped_column(String(32), nullable=False)
    grade_points: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    min_percentage: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    max_percentage: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)

    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="ux_grades_scale_items_tenant_id_id"),
        UniqueConstraint("tenant_id", "scale_id", "grade_code", name="ux_grades_scale_items_scale_code"),
        ForeignKeyConstraint(
            ["tenant_id", "scale_id"],
            ["app_grades_scales.tenant_id", "app_grades_scales.id"],
            ondelete="CASCADE",
            name="fk_grades_scale_items_scale",
        ),
        CheckConstraint("min_percentage >= 0", name="ck_grades_scale_items_min_non_negative"),
        CheckConstraint("max_percentage <= 100", name="ck_grades_scale_items_max_hundred"),
        CheckConstraint("min_percentage <= max_percentage", name="ck_grades_scale_items_range_valid"),
        Index("ix_grades_scale_items_tenant_scale", "tenant_id", "scale_id"),
    )


class GradeSubmissionModel(Base):
    __tablename__ = "app_grades_submissions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("app_tenants.id", ondelete="CASCADE"),
        nullable=False,
    )
    enrollment_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    grade_code: Mapped[str] = mapped_column(String(32), nullable=False)
    grade_points: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    grading_scale_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    submitted_by: Mapped[str] = mapped_column(String(255), nullable=False)
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
    )
    version: Mapped[int] = mapped_column(BigInteger, nullable=False, default=1, server_default=text("1"))
    metadata_json: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )

    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="ux_grades_submissions_tenant_id_id"),
        UniqueConstraint("tenant_id", "enrollment_id", name="ux_grades_submissions_active_enrollment"),
        ForeignKeyConstraint(
            ["tenant_id", "enrollment_id"],
            ["app_enrollments_enrollments.tenant_id", "app_enrollments_enrollments.id"],
            ondelete="CASCADE",
            name="fk_grades_submissions_enrollment",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "grading_scale_id"],
            ["app_grades_scales.tenant_id", "app_grades_scales.id"],
            ondelete="RESTRICT",
            name="fk_grades_submissions_scale",
        ),
        CheckConstraint("version >= 1", name="ck_grades_submissions_version_positive"),
        Index("ix_grades_submissions_tenant_scale", "tenant_id", "grading_scale_id"),
    )


class GradeHistoryModel(Base):
    __tablename__ = "app_grades_history"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("app_tenants.id", ondelete="CASCADE"),
        nullable=False,
    )
    enrollment_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    previous_grade_code: Mapped[str | None] = mapped_column(String(32), nullable=True)
    new_grade_code: Mapped[str] = mapped_column(String(32), nullable=False)
    previous_grade_points: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    new_grade_points: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    changed_by: Mapped[str] = mapped_column(String(255), nullable=False)
    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
    )
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    version: Mapped[int] = mapped_column(BigInteger, nullable=False)

    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="ux_grades_history_tenant_id_id"),
        ForeignKeyConstraint(
            ["tenant_id", "enrollment_id"],
            ["app_enrollments_enrollments.tenant_id", "app_enrollments_enrollments.id"],
            ondelete="CASCADE",
            name="fk_grades_history_enrollment",
        ),
        CheckConstraint("version >= 1", name="ck_grades_history_version_positive"),
        Index("ix_grades_history_tenant_enrollment_changed", "tenant_id", "enrollment_id", "changed_at"),
    )
