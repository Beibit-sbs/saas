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
    Integer,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class WorkflowDefinitionStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"


class WorkflowDefinitionVersionStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    RETIRED = "retired"


class WorkflowTriggerMode(str, Enum):
    MANUAL = "manual"
    EVENT = "event"
    API = "api"


class WorkflowStepType(str, Enum):
    START = "start"
    TASK = "task"
    APPROVAL = "approval"
    END = "end"
    GATEWAY = "gateway"


class WorkflowAssigneeType(str, Enum):
    USER = "user"
    ROLE = "role"
    GROUP = "group"
    SERVICE_ACCOUNT = "service_account"


class WorkflowInstanceStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    APPROVED = "approved"
    REJECTED = "rejected"
    FAILED = "failed"
    TIMED_OUT = "timed_out"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class WorkflowTaskStatus(str, Enum):
    OPEN = "open"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    APPROVED = "approved"
    REJECTED = "rejected"
    FAILED = "failed"
    TIMED_OUT = "timed_out"
    RETURNED = "returned"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class WorkflowCommentType(str, Enum):
    NOTE = "note"
    SYSTEM = "system"
    ESCALATION = "escalation"


class WorkflowCommentVisibility(str, Enum):
    INTERNAL = "internal"
    REQUESTER_VISIBLE = "requester_visible"


class WorkflowApprovalAction(str, Enum):
    APPROVED = "approved"
    REJECTED = "rejected"
    RETURNED = "returned"
    CANCELLED = "cancelled"
    DELEGATED = "delegated"


class WorkflowDefinitionModel(Base):
    __tablename__ = "app_workflows_definitions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("app_tenants.id", ondelete="CASCADE"),
        nullable=False,
    )
    key: Mapped[str] = mapped_column(String(128), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[WorkflowDefinitionStatus] = mapped_column(
        SAEnum(WorkflowDefinitionStatus, name="workflow_definition_status"),
        nullable=False,
        default=WorkflowDefinitionStatus.DRAFT,
        server_default=text("'draft'"),
    )
    active_version_no: Mapped[int | None] = mapped_column(Integer, nullable=True)
    metadata_json: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )
    version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        server_default=text("1"),
    )
    created_by: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
    )
    updated_by: Mapped[str] = mapped_column(String(255), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
        onupdate=text("NOW()"),
    )

    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="ux_workflows_definitions_tenant_id_id"),
        UniqueConstraint("tenant_id", "key", name="ux_workflows_definitions_tenant_key"),
        CheckConstraint("version >= 1", name="ck_workflows_definitions_version_positive"),
        Index("ix_workflows_definitions_tenant_status", "tenant_id", "status"),
    )


class WorkflowDefinitionVersionModel(Base):
    __tablename__ = "app_workflows_definition_versions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("app_tenants.id", ondelete="CASCADE"),
        nullable=False,
    )
    workflow_definition_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    version_no: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[WorkflowDefinitionVersionStatus] = mapped_column(
        SAEnum(WorkflowDefinitionVersionStatus, name="workflow_definition_version_status"),
        nullable=False,
        default=WorkflowDefinitionVersionStatus.DRAFT,
        server_default=text("'draft'"),
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("false"),
    )
    trigger_mode: Mapped[WorkflowTriggerMode] = mapped_column(
        SAEnum(WorkflowTriggerMode, name="workflow_trigger_mode"),
        nullable=False,
        default=WorkflowTriggerMode.MANUAL,
        server_default=text("'manual'"),
    )
    definition_json: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )
    metadata_json: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )
    published_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        server_default=text("1"),
    )
    created_by: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
    )
    updated_by: Mapped[str] = mapped_column(String(255), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
        onupdate=text("NOW()"),
    )

    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="ux_workflow_definition_versions_tenant_id_id"),
        UniqueConstraint(
            "tenant_id",
            "workflow_definition_id",
            "version_no",
            name="ux_workflow_definition_versions_tenant_definition_version",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "workflow_definition_id"],
            ["app_workflows_definitions.tenant_id", "app_workflows_definitions.id"],
            ondelete="CASCADE",
        ),
        CheckConstraint("version >= 1", name="ck_workflow_definition_versions_version_positive"),
        CheckConstraint("version_no >= 1", name="ck_workflow_definition_versions_version_no_positive"),
        Index("ix_workflow_definition_versions_tenant_status", "tenant_id", "status"),
        Index(
            "ix_workflow_definition_versions_tenant_definition",
            "tenant_id",
            "workflow_definition_id",
        ),
    )


class WorkflowStepModel(Base):
    __tablename__ = "app_workflows_steps"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("app_tenants.id", ondelete="CASCADE"),
        nullable=False,
    )
    workflow_definition_version_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    step_key: Mapped[str] = mapped_column(String(128), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    step_type: Mapped[WorkflowStepType] = mapped_column(
        SAEnum(WorkflowStepType, name="workflow_step_type"),
        nullable=False,
    )
    task_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    assignee_type: Mapped[WorkflowAssigneeType | None] = mapped_column(
        SAEnum(WorkflowAssigneeType, name="workflow_assignee_type"),
        nullable=True,
    )
    assignee_ref: Mapped[str | None] = mapped_column(String(255), nullable=True)
    sla_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_blocking: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("true"),
    )
    sequence_hint: Mapped[int | None] = mapped_column(Integer, nullable=True)
    config_json: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )
    metadata_json: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )
    version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        server_default=text("1"),
    )
    created_by: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
    )
    updated_by: Mapped[str] = mapped_column(String(255), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
        onupdate=text("NOW()"),
    )

    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="ux_workflows_steps_tenant_id_id"),
        UniqueConstraint(
            "tenant_id",
            "workflow_definition_version_id",
            "step_key",
            name="ux_workflows_steps_tenant_version_step_key",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "workflow_definition_version_id"],
            ["app_workflows_definition_versions.tenant_id", "app_workflows_definition_versions.id"],
            ondelete="CASCADE",
        ),
        CheckConstraint("version >= 1", name="ck_workflows_steps_version_positive"),
        CheckConstraint(
            "sla_minutes IS NULL OR sla_minutes >= 0",
            name="ck_workflows_steps_sla_minutes_non_negative",
        ),
        Index("ix_workflows_steps_tenant_type", "tenant_id", "step_type"),
        Index("ix_workflows_steps_tenant_version", "tenant_id", "workflow_definition_version_id"),
    )


class WorkflowTransitionModel(Base):
    __tablename__ = "app_workflows_transitions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("app_tenants.id", ondelete="CASCADE"),
        nullable=False,
    )
    workflow_definition_version_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    from_step_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    to_step_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    action_key: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    condition_json: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )
    is_default: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("false"),
    )
    metadata_json: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )
    version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        server_default=text("1"),
    )
    created_by: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
    )
    updated_by: Mapped[str] = mapped_column(String(255), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
        onupdate=text("NOW()"),
    )

    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="ux_workflows_transitions_tenant_id_id"),
        UniqueConstraint(
            "tenant_id",
            "workflow_definition_version_id",
            "from_step_id",
            "action_key",
            name="ux_workflows_transitions_tenant_from_action",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "workflow_definition_version_id"],
            ["app_workflows_definition_versions.tenant_id", "app_workflows_definition_versions.id"],
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "from_step_id"],
            ["app_workflows_steps.tenant_id", "app_workflows_steps.id"],
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "to_step_id"],
            ["app_workflows_steps.tenant_id", "app_workflows_steps.id"],
            ondelete="CASCADE",
        ),
        CheckConstraint("version >= 1", name="ck_workflows_transitions_version_positive"),
        CheckConstraint("from_step_id <> to_step_id", name="ck_workflows_transitions_no_self_loop"),
        Index(
            "ix_workflows_transitions_tenant_from",
            "tenant_id",
            "workflow_definition_version_id",
            "from_step_id",
        ),
    )


class WorkflowInstanceModel(Base):
    __tablename__ = "app_workflows_instances"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("app_tenants.id", ondelete="CASCADE"),
        nullable=False,
    )
    workflow_definition_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    workflow_definition_version_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    entity_type: Mapped[str] = mapped_column(String(128), nullable=False)
    entity_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    status: Mapped[WorkflowInstanceStatus] = mapped_column(
        SAEnum(WorkflowInstanceStatus, name="workflow_instance_status"),
        nullable=False,
        default=WorkflowInstanceStatus.PENDING,
        server_default=text("'pending'"),
    )
    current_step_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    initiated_by: Mapped[str] = mapped_column(String(255), nullable=False)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
    )
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    priority: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
        default=0,
        server_default=text("0"),
    )
    metadata_json: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )
    version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        server_default=text("1"),
    )
    created_by: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
    )
    updated_by: Mapped[str] = mapped_column(String(255), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
        onupdate=text("NOW()"),
    )

    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="ux_workflows_instances_tenant_id_id"),
        ForeignKeyConstraint(
            ["tenant_id", "workflow_definition_id"],
            ["app_workflows_definitions.tenant_id", "app_workflows_definitions.id"],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "workflow_definition_version_id"],
            ["app_workflows_definition_versions.tenant_id", "app_workflows_definition_versions.id"],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "current_step_id"],
            ["app_workflows_steps.tenant_id", "app_workflows_steps.id"],
            ondelete="SET NULL",
        ),
        CheckConstraint("version >= 1", name="ck_workflows_instances_version_positive"),
        CheckConstraint("entity_id > 0", name="ck_workflows_instances_entity_id_positive"),
        Index("ix_workflows_instances_tenant_entity", "tenant_id", "entity_type", "entity_id"),
        Index("ix_workflows_instances_tenant_status_due", "tenant_id", "status", "due_at"),
        Index(
            "ix_workflows_instances_tenant_definition_version",
            "tenant_id",
            "workflow_definition_version_id",
        ),
    )


class WorkflowTaskModel(Base):
    __tablename__ = "app_workflows_tasks"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("app_tenants.id", ondelete="CASCADE"),
        nullable=False,
    )
    workflow_instance_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    workflow_step_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    task_type: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[WorkflowTaskStatus] = mapped_column(
        SAEnum(WorkflowTaskStatus, name="workflow_task_status"),
        nullable=False,
        default=WorkflowTaskStatus.OPEN,
        server_default=text("'open'"),
    )
    assignee_type: Mapped[WorkflowAssigneeType] = mapped_column(
        SAEnum(WorkflowAssigneeType, name="workflow_assignee_type"),
        nullable=False,
    )
    assignee_ref: Mapped[str] = mapped_column(String(255), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    instructions: Mapped[str | None] = mapped_column(Text, nullable=True)
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    sequence_no: Mapped[int] = mapped_column(Integer, nullable=False)
    is_blocking: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("true"),
    )
    claimed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    metadata_json: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )
    version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        server_default=text("1"),
    )
    created_by: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
    )
    updated_by: Mapped[str] = mapped_column(String(255), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
        onupdate=text("NOW()"),
    )

    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="ux_workflows_tasks_tenant_id_id"),
        UniqueConstraint(
            "tenant_id",
            "workflow_instance_id",
            "sequence_no",
            name="ux_workflows_tasks_tenant_instance_sequence",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "workflow_instance_id"],
            ["app_workflows_instances.tenant_id", "app_workflows_instances.id"],
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "workflow_step_id"],
            ["app_workflows_steps.tenant_id", "app_workflows_steps.id"],
            ondelete="SET NULL",
        ),
        CheckConstraint("version >= 1", name="ck_workflows_tasks_version_positive"),
        CheckConstraint("sequence_no > 0", name="ck_workflows_tasks_sequence_positive"),
        Index(
            "ix_workflows_tasks_tenant_assignee_status",
            "tenant_id",
            "assignee_type",
            "assignee_ref",
            "status",
        ),
        Index("ix_workflows_tasks_tenant_status_due", "tenant_id", "status", "due_at"),
    )


class WorkflowTaskCommentModel(Base):
    __tablename__ = "app_workflows_task_comments"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("app_tenants.id", ondelete="CASCADE"),
        nullable=False,
    )
    workflow_task_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    comment_type: Mapped[WorkflowCommentType] = mapped_column(
        SAEnum(WorkflowCommentType, name="workflow_comment_type"),
        nullable=False,
        default=WorkflowCommentType.NOTE,
        server_default=text("'note'"),
    )
    visibility: Mapped[WorkflowCommentVisibility] = mapped_column(
        SAEnum(WorkflowCommentVisibility, name="workflow_comment_visibility"),
        nullable=False,
        default=WorkflowCommentVisibility.INTERNAL,
        server_default=text("'internal'"),
    )
    body: Mapped[str] = mapped_column(Text, nullable=False)
    attachments_json: Mapped[list] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        server_default=text("'[]'::jsonb"),
    )
    metadata_json: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )
    created_by: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
    )

    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "workflow_task_id"],
            ["app_workflows_tasks.tenant_id", "app_workflows_tasks.id"],
            ondelete="CASCADE",
        ),
        Index(
            "ix_workflows_task_comments_tenant_task_created",
            "tenant_id",
            "workflow_task_id",
            "created_at",
        ),
    )


class WorkflowApprovalModel(Base):
    __tablename__ = "app_workflows_approvals"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("app_tenants.id", ondelete="CASCADE"),
        nullable=False,
    )
    workflow_instance_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    workflow_task_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    action: Mapped[WorkflowApprovalAction] = mapped_column(
        SAEnum(WorkflowApprovalAction, name="workflow_approval_action"),
        nullable=False,
    )
    actor: Mapped[str] = mapped_column(String(255), nullable=False)
    actor_role: Mapped[str | None] = mapped_column(String(128), nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    acted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
    )
    step_key: Mapped[str | None] = mapped_column(String(128), nullable=True)
    sequence_no: Mapped[int] = mapped_column(Integer, nullable=False)
    decision_payload_json: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )
    metadata_json: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )
    created_by: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
    )

    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "workflow_instance_id"],
            ["app_workflows_instances.tenant_id", "app_workflows_instances.id"],
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "workflow_task_id"],
            ["app_workflows_tasks.tenant_id", "app_workflows_tasks.id"],
            ondelete="SET NULL",
        ),
        CheckConstraint("sequence_no > 0", name="ck_workflows_approvals_sequence_positive"),
        CheckConstraint(
            "(action NOT IN ('rejected', 'returned', 'cancelled')) OR (reason IS NOT NULL AND length(trim(reason)) > 0)",
            name="ck_workflows_approvals_reason_required_for_negative_actions",
        ),
        Index("ix_workflows_approvals_tenant_instance_acted", "tenant_id", "workflow_instance_id", "acted_at"),
        Index("ix_workflows_approvals_tenant_task_acted", "tenant_id", "workflow_task_id", "acted_at"),
    )
