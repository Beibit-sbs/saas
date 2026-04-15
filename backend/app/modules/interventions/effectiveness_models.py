from __future__ import annotations

from datetime import date, datetime
from enum import Enum

from sqlalchemy import (
    BigInteger,
    Date,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class InterventionCohortOutcomeType(str, Enum):
    DROPOUT_RATE = "dropout_rate"
    GPA_IMPROVEMENT = "gpa_improvement"
    COURSE_COMPLETION_RATE = "course_completion_rate"
    PERSISTENCE_RATE = "persistence_rate"


class InterventionCohortModel(Base):
    """Immutable cohort snapshot used for F3 effectiveness analysis."""

    __tablename__ = "app_intervention_cohorts"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("app_tenants.id", ondelete="CASCADE"),
        nullable=False,
    )
    playbook_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("app_playbooks.id", ondelete="RESTRICT"),
        nullable=False,
    )
    cohort_name: Mapped[str] = mapped_column(String(255), nullable=False)
    analysis_window_start: Mapped[date] = mapped_column(Date, nullable=False)
    analysis_window_end: Mapped[date] = mapped_column(Date, nullable=False)
    student_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default=text("0")
    )
    data_completeness_pct: Mapped[float | None] = mapped_column(
        Numeric(5, 2), nullable=True
    )
    created_by: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("NOW()")
    )

    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "playbook_id",
            "analysis_window_start",
            "analysis_window_end",
            name="uq_intervention_cohorts_window",
        ),
        Index("ix_intervention_cohorts_tenant_id", "tenant_id"),
        Index("ix_intervention_cohorts_playbook_id", "playbook_id"),
    )


class InterventionCohortMemberModel(Base):
    """Cohort members linked to a concrete playbook execution."""

    __tablename__ = "app_intervention_cohort_members"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("app_tenants.id", ondelete="CASCADE"),
        nullable=False,
    )
    cohort_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("app_intervention_cohorts.id", ondelete="CASCADE"),
        nullable=False,
    )
    student_profile_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    playbook_execution_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("app_playbook_executions.id", ondelete="RESTRICT"),
        nullable=False,
    )
    risk_band_at_intervention: Mapped[str | None] = mapped_column(String(32), nullable=True)
    program_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    segment_key: Mapped[str | None] = mapped_column(String(128), nullable=True)
    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("NOW()")
    )

    __table_args__ = (
        UniqueConstraint(
            "cohort_id",
            "playbook_execution_id",
            name="uq_intervention_cohort_members_execution",
        ),
        Index("ix_intervention_cohort_members_tenant_id", "tenant_id"),
        Index("ix_intervention_cohort_members_cohort_id", "cohort_id"),
        Index(
            "ix_intervention_cohort_members_tenant_segment",
            "tenant_id",
            "segment_key",
        ),
    )


class InterventionCohortOutcomeModel(Base):
    """Outcome metrics by cohort and optional segment."""

    __tablename__ = "app_intervention_cohort_outcomes"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("app_tenants.id", ondelete="CASCADE"),
        nullable=False,
    )
    cohort_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("app_intervention_cohorts.id", ondelete="CASCADE"),
        nullable=False,
    )
    outcome_type: Mapped[InterventionCohortOutcomeType] = mapped_column(
        SAEnum(
            InterventionCohortOutcomeType,
            name="intervention_cohort_outcome_type",
        ),
        nullable=False,
    )
    segment_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    outcome_value_treated: Mapped[float] = mapped_column(Numeric(7, 4), nullable=False)
    outcome_value_control: Mapped[float] = mapped_column(Numeric(7, 4), nullable=False)
    uplift_pp: Mapped[float] = mapped_column(Numeric(7, 3), nullable=False)
    uplift_confidence_p5: Mapped[float | None] = mapped_column(Numeric(7, 3), nullable=True)
    uplift_confidence_p95: Mapped[float | None] = mapped_column(Numeric(7, 3), nullable=True)
    measurement_completeness_pct: Mapped[float | None] = mapped_column(
        Numeric(5, 2), nullable=True
    )
    measured_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("NOW()")
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        UniqueConstraint(
            "cohort_id",
            "outcome_type",
            "segment_name",
            name="uq_intervention_cohort_outcomes_key",
        ),
        Index("ix_intervention_cohort_outcomes_tenant_id", "tenant_id"),
        Index("ix_intervention_cohort_outcomes_cohort_id", "cohort_id"),
        Index(
            "ix_intervention_cohort_outcomes_type_segment",
            "outcome_type",
            "segment_name",
        ),
    )
