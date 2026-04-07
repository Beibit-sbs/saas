from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Numeric,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class TranscriptRecordModel(Base):
    __tablename__ = "app_transcripts_records"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("app_tenants.id", ondelete="CASCADE"),
        nullable=False,
    )
    student_profile_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    enrollment_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    course_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    term_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    grade_code: Mapped[str | None] = mapped_column(String(32), nullable=True)
    grade_points: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    credits: Mapped[int] = mapped_column(BigInteger, nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(
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
        UniqueConstraint("tenant_id", "id", name="ux_transcript_records_tenant_id_id"),
        UniqueConstraint("tenant_id", "enrollment_id", name="ux_transcript_records_enrollment"),
        ForeignKeyConstraint(
            ["tenant_id", "student_profile_id"],
            ["app_students_profiles.tenant_id", "app_students_profiles.id"],
            ondelete="CASCADE",
            name="fk_transcript_records_student",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "enrollment_id"],
            ["app_enrollments_enrollments.tenant_id", "app_enrollments_enrollments.id"],
            ondelete="CASCADE",
            name="fk_transcript_records_enrollment",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "term_id"],
            ["app_enrollments_terms.tenant_id", "app_enrollments_terms.id"],
            ondelete="RESTRICT",
            name="fk_transcript_records_term",
        ),
        Index("ix_transcript_records_tenant_student_term", "tenant_id", "student_profile_id", "term_id"),
    )


class TranscriptSnapshotModel(Base):
    __tablename__ = "app_transcripts_snapshots"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("app_tenants.id", ondelete="CASCADE"),
        nullable=False,
    )
    student_profile_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    snapshot_json: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )
    generated_by: Mapped[str] = mapped_column(String(255), nullable=False)
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
    )

    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="ux_transcript_snapshots_tenant_id_id"),
        ForeignKeyConstraint(
            ["tenant_id", "student_profile_id"],
            ["app_students_profiles.tenant_id", "app_students_profiles.id"],
            ondelete="CASCADE",
            name="fk_transcript_snapshots_student",
        ),
        Index("ix_transcript_snapshots_tenant_student_generated", "tenant_id", "student_profile_id", "generated_at"),
    )
