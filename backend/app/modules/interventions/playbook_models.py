from __future__ import annotations

from datetime import datetime
from enum import Enum

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Index,
    Integer,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class PlaybookStepActionType(str, Enum):
    CONSULTATION_SCHEDULED = "consultation_scheduled"
    NOTIFICATION_SENT = "notification_sent"
    PLAN_UPDATED = "plan_updated"
    ADVISOR_MEETING = "advisor_meeting"
    ESCALATION = "escalation"
    RESOURCE_ASSIGNED = "resource_assigned"
    NOTE = "note"


class PlaybookExecutionStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class PlaybookStepExecutionStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    SKIPPED = "skipped"


class PlaybookTriggerType(str, Enum):
    MANUAL = "manual"
    AUTO = "auto"


class PlaybookAssigneeRole(str, Enum):
    ADVISOR = "advisor"
    REGISTRAR = "registrar"
    PROGRAM_MANAGER = "program_manager"
    DEAN = "dean"


class PlaybookModel(Base):
    """Playbook template: reusable multi-step intervention workflow."""

    __tablename__ = "app_playbooks"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("app_tenants.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    trigger_threshold_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("app_risk_thresholds.id", ondelete="SET NULL"),
        nullable=True,
    )
    enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=text("true")
    )
    version: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1, server_default=text("1")
    )
    metadata_json: Mapped[dict] = mapped_column(
        JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb")
    )
    created_by: Mapped[str] = mapped_column(String(255), nullable=False)
    updated_by: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("NOW()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("NOW()")
    )

    steps: Mapped[list["PlaybookStepModel"]] = relationship(
        "PlaybookStepModel", back_populates="playbook", cascade="all, delete-orphan", order_by="PlaybookStepModel.step_order"
    )
    executions: Mapped[list["PlaybookExecutionModel"]] = relationship(
        "PlaybookExecutionModel", back_populates="playbook"
    )

    __table_args__ = (
        UniqueConstraint("tenant_id", "name", name="uq_playbooks_tenant_name"),
        Index("ix_playbooks_tenant_id", "tenant_id"),
        Index("ix_playbooks_trigger_threshold_id", "trigger_threshold_id"),
    )


class PlaybookStepModel(Base):
    """Ordered step in a playbook template."""

    __tablename__ = "app_playbook_steps"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    playbook_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("app_playbooks.id", ondelete="CASCADE"),
        nullable=False,
    )
    step_order: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    action_type: Mapped[PlaybookStepActionType] = mapped_column(
        SAEnum(PlaybookStepActionType, name="playbook_step_action_type"),
        nullable=False,
    )
    rationale: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_mandatory: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=text("true")
    )
    due_days_offset: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, default=3, server_default=text("3")
    )
    assignee_role: Mapped[PlaybookAssigneeRole] = mapped_column(
        SAEnum(PlaybookAssigneeRole, name="playbook_assignee_role"),
        nullable=False,
        default=PlaybookAssigneeRole.ADVISOR,
        server_default=text("'advisor'"),
    )
    metadata_json: Mapped[dict] = mapped_column(
        JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb")
    )

    playbook: Mapped["PlaybookModel"] = relationship(
        "PlaybookModel", back_populates="steps"
    )

    __table_args__ = (
        UniqueConstraint("playbook_id", "step_order", name="uq_playbook_steps_order"),
        Index("ix_playbook_steps_playbook_id", "playbook_id"),
    )


class PlaybookExecutionModel(Base):
    """Running instance of a playbook for a specific case/student."""

    __tablename__ = "app_playbook_executions"

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
    case_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("app_intervention_cases.id", ondelete="SET NULL"),
        nullable=True,
    )
    student_profile_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    triggered_by: Mapped[PlaybookTriggerType] = mapped_column(
        SAEnum(PlaybookTriggerType, name="playbook_trigger_type"),
        nullable=False,
        default=PlaybookTriggerType.MANUAL,
        server_default=text("'manual'"),
    )
    status: Mapped[PlaybookExecutionStatus] = mapped_column(
        SAEnum(PlaybookExecutionStatus, name="playbook_execution_status"),
        nullable=False,
        default=PlaybookExecutionStatus.PENDING,
        server_default=text("'pending'"),
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("NOW()")
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    abandoned_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    abandon_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    outcome_delta_score: Mapped[float | None] = mapped_column(nullable=True)
    metadata_json: Mapped[dict] = mapped_column(
        JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb")
    )
    created_by: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("NOW()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("NOW()")
    )

    playbook: Mapped["PlaybookModel"] = relationship(
        "PlaybookModel", back_populates="executions"
    )
    step_executions: Mapped[list["PlaybookStepExecutionModel"]] = relationship(
        "PlaybookStepExecutionModel", back_populates="execution", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_playbook_executions_tenant_id", "tenant_id"),
        Index("ix_playbook_executions_playbook_id", "playbook_id"),
        Index("ix_playbook_executions_case_id", "case_id"),
        Index("ix_playbook_executions_status", "tenant_id", "status"),
        Index(
            "ix_playbook_executions_student",
            "tenant_id",
            "student_profile_id",
            "started_at",
        ),
    )


class PlaybookStepExecutionModel(Base):
    """Individual step result within a playbook execution."""

    __tablename__ = "app_playbook_step_executions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    execution_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("app_playbook_executions.id", ondelete="CASCADE"),
        nullable=False,
    )
    step_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("app_playbook_steps.id", ondelete="RESTRICT"),
        nullable=False,
    )
    status: Mapped[PlaybookStepExecutionStatus] = mapped_column(
        SAEnum(PlaybookStepExecutionStatus, name="playbook_step_execution_status"),
        nullable=False,
        default=PlaybookStepExecutionStatus.PENDING,
        server_default=text("'pending'"),
    )
    performed_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    performed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    outcome_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[dict] = mapped_column(
        JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb")
    )

    execution: Mapped["PlaybookExecutionModel"] = relationship(
        "PlaybookExecutionModel", back_populates="step_executions"
    )

    __table_args__ = (
        UniqueConstraint(
            "execution_id", "step_id", name="uq_playbook_step_executions_exec_step"
        ),
        Index("ix_playbook_step_executions_execution_id", "execution_id"),
    )
