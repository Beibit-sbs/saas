"""Rector Assignment Workflow — SQLAlchemy ORM Models.

All tables prefixed `rector_`.
tenant_id: BigInteger, indexed, required on every table.
Primary keys: BigInteger autoincrement.
Enums: String constants (VARCHAR) for portability.
No hard delete: archive/soft-delete pattern only.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


# ---------------------------------------------------------------------------
# Status / Enum constants
# ---------------------------------------------------------------------------

class AssignmentStatus:
    DRAFT = "DRAFT"
    ASSIGNED = "ASSIGNED"
    ACCEPTED = "ACCEPTED"
    IN_PROGRESS = "IN_PROGRESS"
    REPORT_SUBMITTED = "REPORT_SUBMITTED"
    RETURNED_FOR_REVISION = "RETURNED_FOR_REVISION"
    COMPLETED = "COMPLETED"
    OVERDUE = "OVERDUE"
    ESCALATED = "ESCALATED"
    CANCELLED = "CANCELLED"
    ARCHIVED = "ARCHIVED"

    ALL = frozenset({
        DRAFT, ASSIGNED, ACCEPTED, IN_PROGRESS, REPORT_SUBMITTED,
        RETURNED_FOR_REVISION, COMPLETED, OVERDUE, ESCALATED,
        CANCELLED, ARCHIVED,
    })

    ACTIVE = frozenset({
        ASSIGNED, ACCEPTED, IN_PROGRESS, REPORT_SUBMITTED,
        RETURNED_FOR_REVISION, OVERDUE, ESCALATED,
    })

    TERMINAL = frozenset({COMPLETED, CANCELLED, ARCHIVED})

    # Transitions: from_status -> set of allowed to_status
    ALLOWED_TRANSITIONS: dict[str, frozenset[str]] = {
        DRAFT: frozenset({ASSIGNED, CANCELLED}),
        ASSIGNED: frozenset({ACCEPTED, CANCELLED, OVERDUE}),
        ACCEPTED: frozenset({IN_PROGRESS, REPORT_SUBMITTED, OVERDUE}),
        IN_PROGRESS: frozenset({REPORT_SUBMITTED, OVERDUE}),
        REPORT_SUBMITTED: frozenset({RETURNED_FOR_REVISION, COMPLETED}),
        RETURNED_FOR_REVISION: frozenset({IN_PROGRESS, REPORT_SUBMITTED}),
        OVERDUE: frozenset({ESCALATED, REPORT_SUBMITTED}),
        ESCALATED: frozenset({IN_PROGRESS, REPORT_SUBMITTED, COMPLETED}),
        COMPLETED: frozenset({ARCHIVED}),
        CANCELLED: frozenset({ARCHIVED}),
        ARCHIVED: frozenset(),
    }


class AssignmentPriority:
    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"
    ALL = frozenset({LOW, NORMAL, HIGH, CRITICAL})


class RecurrenceType:
    NONE = "NONE"
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"
    CUSTOM = "CUSTOM"


class AssigneeRole:
    RESPONSIBLE = "RESPONSIBLE"
    CO_EXECUTOR = "CO_EXECUTOR"
    OBSERVER = "OBSERVER"
    CONTROLLER = "CONTROLLER"


class ReportStatus:
    SUBMITTED = "SUBMITTED"
    RETURNED = "RETURNED"
    ACCEPTED = "ACCEPTED"


class EvidenceType:
    FILE = "FILE"
    LINK = "LINK"
    TEXT = "TEXT"
    SYSTEM_REFERENCE = "SYSTEM_REFERENCE"


class CommentVisibility:
    INTERNAL = "INTERNAL"
    ASSIGNEES = "ASSIGNEES"
    LEADERSHIP = "LEADERSHIP"


class EscalationStatus:
    OPEN = "OPEN"
    RESOLVED = "RESOLVED"
    CANCELLED = "CANCELLED"


class AuditEventType:
    ASSIGNMENT_CREATED = "ASSIGNMENT_CREATED"
    ASSIGNMENT_ASSIGNED = "ASSIGNMENT_ASSIGNED"
    ASSIGNMENT_ACCEPTED = "ASSIGNMENT_ACCEPTED"
    ASSIGNMENT_UPDATED = "ASSIGNMENT_UPDATED"
    REPORT_SUBMITTED = "REPORT_SUBMITTED"
    EVIDENCE_ATTACHED = "EVIDENCE_ATTACHED"
    COMMENT_ADDED = "COMMENT_ADDED"
    RETURNED_FOR_REVISION = "RETURNED_FOR_REVISION"
    ASSIGNMENT_COMPLETED = "ASSIGNMENT_COMPLETED"
    ASSIGNMENT_OVERDUE_MARKED = "ASSIGNMENT_OVERDUE_MARKED"
    ASSIGNMENT_ESCALATED = "ASSIGNMENT_ESCALATED"
    ASSIGNMENT_CANCELLED = "ASSIGNMENT_CANCELLED"
    ASSIGNMENT_ARCHIVED = "ASSIGNMENT_ARCHIVED"
    TEMPLATE_CREATED = "TEMPLATE_CREATED"
    TEMPLATE_UPDATED = "TEMPLATE_UPDATED"


# ---------------------------------------------------------------------------
# Table 1: rector_assignments
# ---------------------------------------------------------------------------

class RectorAssignment(Base):
    __tablename__ = "rector_assignments"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    assignment_number: Mapped[str | None] = mapped_column(String(64), nullable=True)
    category: Mapped[str | None] = mapped_column(String(64), nullable=True)
    priority: Mapped[str] = mapped_column(
        String(16), nullable=False, default=AssignmentPriority.NORMAL,
        server_default=text("'NORMAL'"),
    )
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default=AssignmentStatus.DRAFT,
        server_default=text("'DRAFT'"),
    )
    originator_user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    originator_role: Mapped[str | None] = mapped_column(String(64), nullable=True)
    owner_user_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    responsible_unit_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    source_decree_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    due_date: Mapped[datetime | None] = mapped_column(Date, nullable=True)
    recurrence_type: Mapped[str] = mapped_column(
        String(16), nullable=False, default=RecurrenceType.NONE,
        server_default=text("'NONE'"),
    )
    recurrence_config: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True, default=None,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("NOW()"),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("NOW()"),
    )
    assigned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_archived: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=text("false"),
    )
    version: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1, server_default=text("1"),
    )

    tasks = relationship("RectorAssignmentTask", back_populates="assignment", cascade="all, delete-orphan", lazy="select")
    assignees = relationship("RectorAssignmentAssignee", back_populates="assignment", cascade="all, delete-orphan", lazy="select")
    reports = relationship("RectorAssignmentReport", back_populates="assignment", lazy="select")
    evidence = relationship("RectorAssignmentEvidence", back_populates="assignment", lazy="select")
    comments = relationship("RectorAssignmentComment", back_populates="assignment", lazy="select")
    status_history = relationship("RectorAssignmentStatusHistory", back_populates="assignment", cascade="all, delete-orphan", lazy="select")
    escalations = relationship("RectorAssignmentEscalation", back_populates="assignment", lazy="select")
    audit_events = relationship("RectorAssignmentAuditEvent", back_populates="assignment", lazy="select")

    __table_args__ = (
        Index("ix_rector_assignments_tenant_status", "tenant_id", "status"),
        Index("ix_rector_assignments_tenant_due_date", "tenant_id", "due_date"),
        Index("ix_rector_assignments_tenant_priority", "tenant_id", "priority"),
        Index("ix_rector_assignments_tenant_originator", "tenant_id", "originator_user_id"),
        Index("ix_rector_assignments_tenant_created", "tenant_id", "created_at"),
    )


# ---------------------------------------------------------------------------
# Table 2: rector_assignment_tasks
# ---------------------------------------------------------------------------

class RectorAssignmentTask(Base):
    __tablename__ = "rector_assignment_tasks"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    assignment_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("rector_assignments.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    assignee_user_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    assignee_unit_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="PENDING", server_default=text("'PENDING'"),
    )
    due_date: Mapped[datetime | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("NOW()"))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("NOW()"))

    assignment = relationship("RectorAssignment", back_populates="tasks")

    __table_args__ = (
        Index("ix_rector_assignment_tasks_tenant_assignment", "tenant_id", "assignment_id"),
    )


# ---------------------------------------------------------------------------
# Table 3: rector_assignment_assignees
# ---------------------------------------------------------------------------

class RectorAssignmentAssignee(Base):
    __tablename__ = "rector_assignment_assignees"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    assignment_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("rector_assignments.id"), nullable=False)
    user_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    unit_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    role_on_assignment: Mapped[str] = mapped_column(
        String(32), nullable=False, default=AssigneeRole.RESPONSIBLE,
        server_default=text("'RESPONSIBLE'"),
    )
    assigned_by_user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    assigned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("NOW()"))
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="PENDING", server_default=text("'PENDING'"),
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    assignment = relationship("RectorAssignment", back_populates="assignees")

    __table_args__ = (
        Index("ix_rector_assignment_assignees_tenant_assignment", "tenant_id", "assignment_id"),
        Index("ix_rector_assignment_assignees_tenant_user", "tenant_id", "user_id"),
    )


# ---------------------------------------------------------------------------
# Table 4: rector_assignment_reports
# ---------------------------------------------------------------------------

class RectorAssignmentReport(Base):
    __tablename__ = "rector_assignment_reports"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    assignment_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("rector_assignments.id"), nullable=False)
    submitted_by_user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    reporting_period_start: Mapped[datetime] = mapped_column(Date, nullable=False)
    reporting_period_end: Mapped[datetime] = mapped_column(Date, nullable=False)
    progress_percent: Mapped[int] = mapped_column(Integer, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    blockers: Mapped[str | None] = mapped_column(Text, nullable=True)
    next_steps: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default=ReportStatus.SUBMITTED,
        server_default=text("'SUBMITTED'"),
    )
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("NOW()"))
    reviewed_by_user_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    review_comment: Mapped[str | None] = mapped_column(Text, nullable=True)

    assignment = relationship("RectorAssignment", back_populates="reports")
    evidence = relationship("RectorAssignmentEvidence", back_populates="report", lazy="select")

    __table_args__ = (
        Index("ix_rector_assignment_reports_tenant_assignment", "tenant_id", "assignment_id"),
        Index("ix_rector_assignment_reports_tenant_submitted_by", "tenant_id", "submitted_by_user_id"),
    )


# ---------------------------------------------------------------------------
# Table 5: rector_assignment_evidence
# ---------------------------------------------------------------------------

class RectorAssignmentEvidence(Base):
    __tablename__ = "rector_assignment_evidence"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    assignment_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("rector_assignments.id"), nullable=False)
    report_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("rector_assignment_reports.id"), nullable=True)
    evidence_type: Mapped[str] = mapped_column(String(32), nullable=False)
    file_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    uploaded_by_user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("NOW()"))
    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=text("false"))
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deleted_by_user_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    assignment = relationship("RectorAssignment", back_populates="evidence")
    report = relationship("RectorAssignmentReport", back_populates="evidence")

    __table_args__ = (
        Index("ix_rector_assignment_evidence_tenant_assignment", "tenant_id", "assignment_id"),
    )


# ---------------------------------------------------------------------------
# Table 6: rector_assignment_comments
# ---------------------------------------------------------------------------

class RectorAssignmentComment(Base):
    __tablename__ = "rector_assignment_comments"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    assignment_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("rector_assignments.id"), nullable=False)
    parent_comment_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    author_user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    author_role: Mapped[str | None] = mapped_column(String(64), nullable=True)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    visibility: Mapped[str] = mapped_column(
        String(32), nullable=False, default=CommentVisibility.ASSIGNEES,
        server_default=text("'ASSIGNEES'"),
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("NOW()"))
    edited_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=text("false"))

    assignment = relationship("RectorAssignment", back_populates="comments")

    __table_args__ = (
        Index("ix_rector_assignment_comments_tenant_assignment", "tenant_id", "assignment_id"),
    )


# ---------------------------------------------------------------------------
# Table 7: rector_assignment_status_history (INSERT-ONLY)
# ---------------------------------------------------------------------------

class RectorAssignmentStatusHistory(Base):
    __tablename__ = "rector_assignment_status_history"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    assignment_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("rector_assignments.id"), nullable=False)
    old_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    new_status: Mapped[str] = mapped_column(String(32), nullable=False)
    actor_user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    actor_role: Mapped[str | None] = mapped_column(String(64), nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    request_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("NOW()"))

    assignment = relationship("RectorAssignment", back_populates="status_history")

    __table_args__ = (
        Index("ix_rector_assignment_status_history_tenant_assignment", "tenant_id", "assignment_id"),
    )


# ---------------------------------------------------------------------------
# Table 8: rector_assignment_escalations
# ---------------------------------------------------------------------------

class RectorAssignmentEscalation(Base):
    __tablename__ = "rector_assignment_escalations"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    assignment_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("rector_assignments.id"), nullable=False)
    trigger_type: Mapped[str] = mapped_column(String(32), nullable=False)
    escalation_level: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    escalated_to_user_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    escalated_to_role: Mapped[str] = mapped_column(String(64), nullable=False)
    triggered_by_user_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    triggered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("NOW()"))
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolution_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default=EscalationStatus.OPEN,
        server_default=text("'OPEN'"),
    )

    assignment = relationship("RectorAssignment", back_populates="escalations")

    __table_args__ = (
        Index("ix_rector_assignment_escalations_tenant_assignment", "tenant_id", "assignment_id"),
        Index("ix_rector_assignment_escalations_tenant_status", "tenant_id", "status"),
    )


# ---------------------------------------------------------------------------
# Table 9: rector_assignment_templates
# ---------------------------------------------------------------------------

class RectorAssignmentTemplate(Base):
    __tablename__ = "rector_assignment_templates"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str | None] = mapped_column(String(64), nullable=True)
    default_priority: Mapped[str] = mapped_column(
        String(16), nullable=False, default=AssignmentPriority.NORMAL,
        server_default=text("'NORMAL'"),
    )
    default_due_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    default_recurrence_type: Mapped[str] = mapped_column(
        String(16), nullable=False, default=RecurrenceType.NONE,
        server_default=text("'NONE'"),
    )
    template_body: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=text("true"))
    created_by_user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("NOW()"))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("NOW()"))

    __table_args__ = (
        Index("ix_rector_assignment_templates_tenant_active", "tenant_id", "is_active"),
    )


# ---------------------------------------------------------------------------
# Table 10: rector_assignment_audit_events (INSERT-ONLY)
# ---------------------------------------------------------------------------

class RectorAssignmentAuditEvent(Base):
    __tablename__ = "rector_assignment_audit_events"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    assignment_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("rector_assignments.id"), nullable=True)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    actor_user_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    actor_role: Mapped[str | None] = mapped_column(String(64), nullable=True)
    request_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    action: Mapped[str] = mapped_column(String(256), nullable=False)
    payload_json: Mapped[dict] = mapped_column(
        JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb"),
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("NOW()"))

    assignment = relationship("RectorAssignment", back_populates="audit_events")

    __table_args__ = (
        Index("ix_rector_assignment_audit_events_tenant_assignment", "tenant_id", "assignment_id"),
        Index("ix_rector_assignment_audit_events_tenant_event_type", "tenant_id", "event_type"),
        Index("ix_rector_assignment_audit_events_tenant_created", "tenant_id", "created_at"),
    )
