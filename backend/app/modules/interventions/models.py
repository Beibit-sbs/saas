from __future__ import annotations

from datetime import date, datetime
from enum import Enum

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    Date,
    Enum as SAEnum,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class InterventionCaseType(str, Enum):
    ACADEMIC_RISK = "academic_risk"


class InterventionCaseSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class InterventionCaseStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


class InterventionAssigneeType(str, Enum):
    USER = "user"
    GROUP = "group"


class InterventionActionType(str, Enum):
    ASSIGNMENT = "assignment"
    STATUS_CHANGE = "status_change"
    CONSULTATION_SCHEDULED = "consultation_scheduled"
    NOTIFICATION_SENT = "notification_sent"
    PLAN_UPDATED = "plan_updated"
    NOTE = "note"


class RiskThresholdComparison(str, Enum):
    LTE = "lte"
    GTE = "gte"
    EQ = "eq"


class RiskThresholdCategory(str, Enum):
    ATTENDANCE = "attendance"
    TOPIC_MASTERY = "topic_mastery"
    FAILED_ASSESSMENT = "failed_assessment"


class RiskMetric(str, Enum):
    ABSENCE_COUNT = "absence_count"
    QUIZ_BEST_SCORE = "quiz_best_score"


class RiskSignalType(str, Enum):
    ATTENDANCE_RISK = "attendance_risk"
    PROGRESS_RISK = "progress_risk"
    ASSESSMENT_RISK = "assessment_risk"


class OutcomeTrackingStatus(str, Enum):
    IMPROVED = "improved"
    UNCHANGED = "unchanged"
    WORSENED = "worsened"


class InterventionCaseModel(Base):
    __tablename__ = "app_intervention_cases"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("app_tenants.id", ondelete="CASCADE"),
        nullable=False,
    )
    case_type: Mapped[InterventionCaseType] = mapped_column(
        SAEnum(InterventionCaseType, name="intervention_case_type"),
        nullable=False,
        default=InterventionCaseType.ACADEMIC_RISK,
        server_default=text("'academic_risk'"),
    )
    student_profile_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    severity: Mapped[InterventionCaseSeverity] = mapped_column(
        SAEnum(InterventionCaseSeverity, name="intervention_case_severity"),
        nullable=False,
        default=InterventionCaseSeverity.MEDIUM,
        server_default=text("'medium'"),
    )
    status: Mapped[InterventionCaseStatus] = mapped_column(
        SAEnum(InterventionCaseStatus, name="intervention_case_status"),
        nullable=False,
        default=InterventionCaseStatus.OPEN,
        server_default=text("'open'"),
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    risk_snapshot_json: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )
    assignee_type: Mapped[InterventionAssigneeType] = mapped_column(
        SAEnum(InterventionAssigneeType, name="intervention_assignee_type"),
        nullable=False,
        default=InterventionAssigneeType.GROUP,
        server_default=text("'group'"),
    )
    assignee_ref: Mapped[str] = mapped_column(String(255), nullable=False)
    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    opened_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
    )
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    metadata_json: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default=text("1"))
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
        UniqueConstraint("tenant_id", "id", name="ux_intervention_cases_tenant_id_id"),
        ForeignKeyConstraint(
            ["tenant_id", "student_profile_id"],
            ["app_students_profiles.tenant_id", "app_students_profiles.id"],
            ondelete="RESTRICT",
        ),
        CheckConstraint("version >= 1", name="ck_intervention_cases_version_positive"),
        CheckConstraint("due_at >= opened_at", name="ck_intervention_cases_due_after_open"),
        Index("ix_intervention_cases_tenant_status", "tenant_id", "status"),
        Index("ix_intervention_cases_tenant_severity", "tenant_id", "severity"),
        Index("ix_intervention_cases_tenant_assignee", "tenant_id", "assignee_type", "assignee_ref"),
        Index("ix_intervention_cases_tenant_due", "tenant_id", "due_at"),
    )


class InterventionActionModel(Base):
    __tablename__ = "app_intervention_actions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("app_tenants.id", ondelete="CASCADE"),
        nullable=False,
    )
    case_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    action_type: Mapped[InterventionActionType] = mapped_column(
        SAEnum(InterventionActionType, name="intervention_action_type"),
        nullable=False,
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)
    outcome_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    performed_by: Mapped[str] = mapped_column(String(255), nullable=False)
    performed_at: Mapped[datetime] = mapped_column(
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
        UniqueConstraint("tenant_id", "id", name="ux_intervention_actions_tenant_id_id"),
        ForeignKeyConstraint(
            ["tenant_id", "case_id"],
            ["app_intervention_cases.tenant_id", "app_intervention_cases.id"],
            ondelete="CASCADE",
        ),
        Index("ix_intervention_actions_tenant_case_performed", "tenant_id", "case_id", "performed_at"),
        Index("ix_intervention_actions_tenant_type", "tenant_id", "action_type"),
    )


class RiskThresholdModel(Base):
    __tablename__ = "app_risk_thresholds"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("app_tenants.id", ondelete="CASCADE"),
        nullable=False,
    )
    risk_category: Mapped[RiskThresholdCategory] = mapped_column(
        SAEnum(RiskThresholdCategory, name="risk_threshold_category"),
        nullable=False,
    )
    rule_name: Mapped[str] = mapped_column(String(128), nullable=False)
    metric: Mapped[RiskMetric] = mapped_column(
        SAEnum(RiskMetric, name="risk_metric"),
        nullable=False,
    )
    threshold_value: Mapped[float] = mapped_column(nullable=False)
    comparison: Mapped[RiskThresholdComparison] = mapped_column(
        SAEnum(RiskThresholdComparison, name="risk_threshold_comparison"),
        nullable=False,
    )
    severity_level: Mapped[InterventionCaseSeverity] = mapped_column(
        SAEnum(InterventionCaseSeverity, name="intervention_case_severity"),
        nullable=False,
        default=InterventionCaseSeverity.MEDIUM,
        server_default=text("'medium'"),
    )
    signal_type: Mapped[RiskSignalType] = mapped_column(
        SAEnum(RiskSignalType, name="risk_signal_type"),
        nullable=False,
    )
    enabled: Mapped[bool] = mapped_column(nullable=False, default=True, server_default=text("true"))
    auto_create_case: Mapped[bool] = mapped_column(nullable=False, default=True, server_default=text("true"))
    window_days: Mapped[int] = mapped_column(Integer, nullable=False, default=30, server_default=text("30"))
    escalate_to_refs_json: Mapped[list] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        server_default=text("'[]'::jsonb"),
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
        UniqueConstraint("tenant_id", "id", name="ux_risk_thresholds_tenant_id_id"),
        UniqueConstraint("tenant_id", "rule_name", name="ux_risk_thresholds_tenant_rule_name"),
        CheckConstraint("threshold_value >= 0", name="ck_risk_thresholds_threshold_non_negative"),
        CheckConstraint("window_days >= 1", name="ck_risk_thresholds_window_days_positive"),
        Index("ix_risk_thresholds_tenant_enabled", "tenant_id", "enabled"),
        Index("ix_risk_thresholds_tenant_category", "tenant_id", "risk_category"),
    )


class RiskSignalModel(Base):
    __tablename__ = "app_risk_signals"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("app_tenants.id", ondelete="CASCADE"),
        nullable=False,
    )
    student_profile_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    threshold_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    signal_type: Mapped[RiskSignalType] = mapped_column(
        SAEnum(RiskSignalType, name="risk_signal_type"),
        nullable=False,
    )
    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
    )
    detected_on: Mapped[date] = mapped_column(Date, nullable=False)
    current_value: Mapped[float] = mapped_column(nullable=False)
    threshold_value: Mapped[float] = mapped_column(nullable=False)
    severity: Mapped[InterventionCaseSeverity] = mapped_column(
        SAEnum(InterventionCaseSeverity, name="intervention_case_severity"),
        nullable=False,
    )
    signal_data_json: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )
    associated_case_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="ux_risk_signals_tenant_id_id"),
        UniqueConstraint(
            "tenant_id",
            "student_profile_id",
            "threshold_id",
            "detected_on",
            name="ux_risk_signals_tenant_student_threshold_day",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "student_profile_id"],
            ["app_students_profiles.tenant_id", "app_students_profiles.id"],
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "threshold_id"],
            ["app_risk_thresholds.tenant_id", "app_risk_thresholds.id"],
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "associated_case_id"],
            ["app_intervention_cases.tenant_id", "app_intervention_cases.id"],
            ondelete="SET NULL",
        ),
        Index("ix_risk_signals_tenant_student_detected", "tenant_id", "student_profile_id", "detected_at"),
        Index("ix_risk_signals_tenant_severity", "tenant_id", "severity"),
    )


class OutcomeTrackingModel(Base):
    __tablename__ = "app_outcome_tracking"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("app_tenants.id", ondelete="CASCADE"),
        nullable=False,
    )
    case_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    baseline_risk_score: Mapped[float] = mapped_column(nullable=False)
    current_risk_score: Mapped[float] = mapped_column(nullable=False)
    outcome: Mapped[OutcomeTrackingStatus] = mapped_column(
        SAEnum(OutcomeTrackingStatus, name="outcome_tracking_status"),
        nullable=False,
    )
    improvement_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    measurement_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    outcome_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
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
        UniqueConstraint("tenant_id", "id", name="ux_outcome_tracking_tenant_id_id"),
        UniqueConstraint("tenant_id", "case_id", name="ux_outcome_tracking_tenant_case"),
        ForeignKeyConstraint(
            ["tenant_id", "case_id"],
            ["app_intervention_cases.tenant_id", "app_intervention_cases.id"],
            ondelete="CASCADE",
        ),
        Index("ix_outcome_tracking_tenant_outcome", "tenant_id", "outcome"),
    )
