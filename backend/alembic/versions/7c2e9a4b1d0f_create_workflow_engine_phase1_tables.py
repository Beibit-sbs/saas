"""create workflow engine phase 1 tables

Revision ID: 7c2e9a4b1d0f
Revises: a1b2c3d4e5f6
Create Date: 2026-03-23 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "7c2e9a4b1d0f"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    workflow_definition_status = postgresql.ENUM(
        "draft",
        "active",
        "archived",
        name="workflow_definition_status",
        create_type=False,
    )
    workflow_definition_version_status = postgresql.ENUM(
        "draft",
        "active",
        "retired",
        name="workflow_definition_version_status",
        create_type=False,
    )
    workflow_trigger_mode = postgresql.ENUM(
        "manual",
        "event",
        "api",
        name="workflow_trigger_mode",
        create_type=False,
    )
    workflow_step_type = postgresql.ENUM(
        "start",
        "task",
        "approval",
        "end",
        "gateway",
        name="workflow_step_type",
        create_type=False,
    )
    workflow_assignee_type = postgresql.ENUM(
        "user",
        "role",
        "group",
        "service_account",
        name="workflow_assignee_type",
        create_type=False,
    )
    workflow_instance_status = postgresql.ENUM(
        "pending",
        "in_progress",
        "approved",
        "rejected",
        "cancelled",
        "completed",
        name="workflow_instance_status",
        create_type=False,
    )
    workflow_task_status = postgresql.ENUM(
        "open",
        "assigned",
        "in_progress",
        "approved",
        "rejected",
        "returned",
        "completed",
        "cancelled",
        name="workflow_task_status",
        create_type=False,
    )
    workflow_comment_type = postgresql.ENUM(
        "note",
        "system",
        "escalation",
        name="workflow_comment_type",
        create_type=False,
    )
    workflow_comment_visibility = postgresql.ENUM(
        "internal",
        "requester_visible",
        name="workflow_comment_visibility",
        create_type=False,
    )
    workflow_approval_action = postgresql.ENUM(
        "approved",
        "rejected",
        "returned",
        "cancelled",
        "delegated",
        name="workflow_approval_action",
        create_type=False,
    )

    enum_types = [
        workflow_definition_status,
        workflow_definition_version_status,
        workflow_trigger_mode,
        workflow_step_type,
        workflow_assignee_type,
        workflow_instance_status,
        workflow_task_status,
        workflow_comment_type,
        workflow_comment_visibility,
        workflow_approval_action,
    ]
    for enum_type in enum_types:
        enum_type.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "app_workflows_definitions",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("key", sa.String(length=128), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", workflow_definition_status, nullable=False, server_default=sa.text("'draft'")),
        sa.Column("active_version_no", sa.Integer(), nullable=True),
        sa.Column(
            "metadata_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_by", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_by", sa.String(length=255), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.CheckConstraint("version >= 1", name="ck_workflows_definitions_version_positive"),
        sa.ForeignKeyConstraint(["tenant_id"], ["app_tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "id", name="ux_workflows_definitions_tenant_id_id"),
        sa.UniqueConstraint("tenant_id", "key", name="ux_workflows_definitions_tenant_key"),
    )
    op.create_index(
        "ix_workflows_definitions_tenant_status",
        "app_workflows_definitions",
        ["tenant_id", "status"],
    )

    op.create_table(
        "app_workflows_definition_versions",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("workflow_definition_id", sa.BigInteger(), nullable=False),
        sa.Column("version_no", sa.Integer(), nullable=False),
        sa.Column(
            "status",
            workflow_definition_version_status,
            nullable=False,
            server_default=sa.text("'draft'"),
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("trigger_mode", workflow_trigger_mode, nullable=False, server_default=sa.text("'manual'")),
        sa.Column(
            "definition_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "metadata_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("published_by", sa.String(length=255), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_by", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_by", sa.String(length=255), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.CheckConstraint("version >= 1", name="ck_workflow_definition_versions_version_positive"),
        sa.CheckConstraint("version_no >= 1", name="ck_workflow_definition_versions_version_no_positive"),
        sa.ForeignKeyConstraint(["tenant_id"], ["app_tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "workflow_definition_id"],
            ["app_workflows_definitions.tenant_id", "app_workflows_definitions.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "id", name="ux_workflow_definition_versions_tenant_id_id"),
        sa.UniqueConstraint(
            "tenant_id",
            "workflow_definition_id",
            "version_no",
            name="ux_workflow_definition_versions_tenant_definition_version",
        ),
    )
    op.create_index(
        "ix_workflow_definition_versions_tenant_status",
        "app_workflows_definition_versions",
        ["tenant_id", "status"],
    )
    op.create_index(
        "ix_workflow_definition_versions_tenant_definition",
        "app_workflows_definition_versions",
        ["tenant_id", "workflow_definition_id"],
    )
    op.create_index(
        "ux_workflow_definition_versions_active",
        "app_workflows_definition_versions",
        ["tenant_id", "workflow_definition_id"],
        unique=True,
        postgresql_where=sa.text("is_active = true"),
    )

    op.create_table(
        "app_workflows_steps",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("workflow_definition_version_id", sa.BigInteger(), nullable=False),
        sa.Column("step_key", sa.String(length=128), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("step_type", workflow_step_type, nullable=False),
        sa.Column("task_type", sa.String(length=64), nullable=True),
        sa.Column("assignee_type", workflow_assignee_type, nullable=True),
        sa.Column("assignee_ref", sa.String(length=255), nullable=True),
        sa.Column("sla_minutes", sa.Integer(), nullable=True),
        sa.Column("is_blocking", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("sequence_hint", sa.Integer(), nullable=True),
        sa.Column(
            "config_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "metadata_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_by", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_by", sa.String(length=255), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.CheckConstraint("version >= 1", name="ck_workflows_steps_version_positive"),
        sa.CheckConstraint(
            "sla_minutes IS NULL OR sla_minutes >= 0",
            name="ck_workflows_steps_sla_minutes_non_negative",
        ),
        sa.ForeignKeyConstraint(["tenant_id"], ["app_tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "workflow_definition_version_id"],
            ["app_workflows_definition_versions.tenant_id", "app_workflows_definition_versions.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "id", name="ux_workflows_steps_tenant_id_id"),
        sa.UniqueConstraint(
            "tenant_id",
            "workflow_definition_version_id",
            "step_key",
            name="ux_workflows_steps_tenant_version_step_key",
        ),
    )
    op.create_index("ix_workflows_steps_tenant_type", "app_workflows_steps", ["tenant_id", "step_type"])
    op.create_index(
        "ix_workflows_steps_tenant_version",
        "app_workflows_steps",
        ["tenant_id", "workflow_definition_version_id"],
    )

    op.create_table(
        "app_workflows_transitions",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("workflow_definition_version_id", sa.BigInteger(), nullable=False),
        sa.Column("from_step_id", sa.BigInteger(), nullable=False),
        sa.Column("to_step_id", sa.BigInteger(), nullable=False),
        sa.Column("action_key", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column(
            "condition_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column(
            "metadata_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_by", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_by", sa.String(length=255), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.CheckConstraint("version >= 1", name="ck_workflows_transitions_version_positive"),
        sa.CheckConstraint("from_step_id <> to_step_id", name="ck_workflows_transitions_no_self_loop"),
        sa.ForeignKeyConstraint(["tenant_id"], ["app_tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "workflow_definition_version_id"],
            ["app_workflows_definition_versions.tenant_id", "app_workflows_definition_versions.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "from_step_id"],
            ["app_workflows_steps.tenant_id", "app_workflows_steps.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "to_step_id"],
            ["app_workflows_steps.tenant_id", "app_workflows_steps.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "id", name="ux_workflows_transitions_tenant_id_id"),
        sa.UniqueConstraint(
            "tenant_id",
            "workflow_definition_version_id",
            "from_step_id",
            "action_key",
            name="ux_workflows_transitions_tenant_from_action",
        ),
    )
    op.create_index(
        "ix_workflows_transitions_tenant_from",
        "app_workflows_transitions",
        ["tenant_id", "workflow_definition_version_id", "from_step_id"],
    )

    op.create_table(
        "app_workflows_instances",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("workflow_definition_id", sa.BigInteger(), nullable=False),
        sa.Column("workflow_definition_version_id", sa.BigInteger(), nullable=False),
        sa.Column("entity_type", sa.String(length=128), nullable=False),
        sa.Column("entity_id", sa.BigInteger(), nullable=False),
        sa.Column("status", workflow_instance_status, nullable=False, server_default=sa.text("'pending'")),
        sa.Column("current_step_id", sa.BigInteger(), nullable=True),
        sa.Column("initiated_by", sa.String(length=255), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("priority", sa.SmallInteger(), nullable=False, server_default="0"),
        sa.Column(
            "metadata_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_by", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_by", sa.String(length=255), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.CheckConstraint("version >= 1", name="ck_workflows_instances_version_positive"),
        sa.CheckConstraint("entity_id > 0", name="ck_workflows_instances_entity_id_positive"),
        sa.ForeignKeyConstraint(["tenant_id"], ["app_tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "workflow_definition_id"],
            ["app_workflows_definitions.tenant_id", "app_workflows_definitions.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "workflow_definition_version_id"],
            ["app_workflows_definition_versions.tenant_id", "app_workflows_definition_versions.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "current_step_id"],
            ["app_workflows_steps.tenant_id", "app_workflows_steps.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "id", name="ux_workflows_instances_tenant_id_id"),
    )
    op.create_index(
        "ix_workflows_instances_tenant_entity",
        "app_workflows_instances",
        ["tenant_id", "entity_type", "entity_id"],
    )
    op.create_index(
        "ix_workflows_instances_tenant_status_due",
        "app_workflows_instances",
        ["tenant_id", "status", "due_at"],
    )
    op.create_index(
        "ix_workflows_instances_tenant_definition_version",
        "app_workflows_instances",
        ["tenant_id", "workflow_definition_version_id"],
    )

    op.create_table(
        "app_workflows_tasks",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("workflow_instance_id", sa.BigInteger(), nullable=False),
        sa.Column("workflow_step_id", sa.BigInteger(), nullable=True),
        sa.Column("task_type", sa.String(length=64), nullable=False),
        sa.Column("status", workflow_task_status, nullable=False, server_default=sa.text("'open'")),
        sa.Column("assignee_type", workflow_assignee_type, nullable=False),
        sa.Column("assignee_ref", sa.String(length=255), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("instructions", sa.Text(), nullable=True),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sequence_no", sa.Integer(), nullable=False),
        sa.Column("is_blocking", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("claimed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "metadata_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_by", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_by", sa.String(length=255), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.CheckConstraint("version >= 1", name="ck_workflows_tasks_version_positive"),
        sa.CheckConstraint("sequence_no > 0", name="ck_workflows_tasks_sequence_positive"),
        sa.ForeignKeyConstraint(["tenant_id"], ["app_tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "workflow_instance_id"],
            ["app_workflows_instances.tenant_id", "app_workflows_instances.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "workflow_step_id"],
            ["app_workflows_steps.tenant_id", "app_workflows_steps.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "id", name="ux_workflows_tasks_tenant_id_id"),
        sa.UniqueConstraint(
            "tenant_id",
            "workflow_instance_id",
            "sequence_no",
            name="ux_workflows_tasks_tenant_instance_sequence",
        ),
    )
    op.create_index(
        "ix_workflows_tasks_tenant_assignee_status",
        "app_workflows_tasks",
        ["tenant_id", "assignee_type", "assignee_ref", "status"],
    )
    op.create_index(
        "ix_workflows_tasks_tenant_status_due",
        "app_workflows_tasks",
        ["tenant_id", "status", "due_at"],
    )

    op.create_table(
        "app_workflows_task_comments",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("workflow_task_id", sa.BigInteger(), nullable=False),
        sa.Column("comment_type", workflow_comment_type, nullable=False, server_default=sa.text("'note'")),
        sa.Column("visibility", workflow_comment_visibility, nullable=False, server_default=sa.text("'internal'")),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column(
            "attachments_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "metadata_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("created_by", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.ForeignKeyConstraint(["tenant_id"], ["app_tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "workflow_task_id"],
            ["app_workflows_tasks.tenant_id", "app_workflows_tasks.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_workflows_task_comments_tenant_task_created",
        "app_workflows_task_comments",
        ["tenant_id", "workflow_task_id", "created_at"],
    )

    op.create_table(
        "app_workflows_approvals",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("workflow_instance_id", sa.BigInteger(), nullable=False),
        sa.Column("workflow_task_id", sa.BigInteger(), nullable=True),
        sa.Column("action", workflow_approval_action, nullable=False),
        sa.Column("actor", sa.String(length=255), nullable=False),
        sa.Column("actor_role", sa.String(length=128), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("acted_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("step_key", sa.String(length=128), nullable=True),
        sa.Column("sequence_no", sa.Integer(), nullable=False),
        sa.Column(
            "decision_payload_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "metadata_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("created_by", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.CheckConstraint("sequence_no > 0", name="ck_workflows_approvals_sequence_positive"),
        sa.CheckConstraint(
            "(action NOT IN ('rejected', 'returned', 'cancelled')) OR (reason IS NOT NULL AND length(trim(reason)) > 0)",
            name="ck_workflows_approvals_reason_required_for_negative_actions",
        ),
        sa.ForeignKeyConstraint(["tenant_id"], ["app_tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "workflow_instance_id"],
            ["app_workflows_instances.tenant_id", "app_workflows_instances.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "workflow_task_id"],
            ["app_workflows_tasks.tenant_id", "app_workflows_tasks.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_workflows_approvals_tenant_instance_acted",
        "app_workflows_approvals",
        ["tenant_id", "workflow_instance_id", "acted_at"],
    )
    op.create_index(
        "ix_workflows_approvals_tenant_task_acted",
        "app_workflows_approvals",
        ["tenant_id", "workflow_task_id", "acted_at"],
    )

    op.execute(
        """
        CREATE OR REPLACE FUNCTION app_workflows_prevent_comment_mutation()
        RETURNS trigger AS $$
        BEGIN
            RAISE EXCEPTION 'app_workflows_task_comments is append-only';
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_workflows_task_comments_no_update
        BEFORE UPDATE ON app_workflows_task_comments
        FOR EACH ROW EXECUTE FUNCTION app_workflows_prevent_comment_mutation();
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_workflows_task_comments_no_delete
        BEFORE DELETE ON app_workflows_task_comments
        FOR EACH ROW EXECUTE FUNCTION app_workflows_prevent_comment_mutation();
        """
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_workflows_task_comments_no_delete ON app_workflows_task_comments")
    op.execute("DROP TRIGGER IF EXISTS trg_workflows_task_comments_no_update ON app_workflows_task_comments")
    op.execute("DROP FUNCTION IF EXISTS app_workflows_prevent_comment_mutation")

    op.drop_index("ix_workflows_approvals_tenant_task_acted", table_name="app_workflows_approvals")
    op.drop_index("ix_workflows_approvals_tenant_instance_acted", table_name="app_workflows_approvals")
    op.drop_table("app_workflows_approvals")

    op.drop_index(
        "ix_workflows_task_comments_tenant_task_created",
        table_name="app_workflows_task_comments",
    )
    op.drop_table("app_workflows_task_comments")

    op.drop_index("ix_workflows_tasks_tenant_status_due", table_name="app_workflows_tasks")
    op.drop_index("ix_workflows_tasks_tenant_assignee_status", table_name="app_workflows_tasks")
    op.drop_table("app_workflows_tasks")

    op.drop_index(
        "ix_workflows_instances_tenant_definition_version",
        table_name="app_workflows_instances",
    )
    op.drop_index("ix_workflows_instances_tenant_status_due", table_name="app_workflows_instances")
    op.drop_index("ix_workflows_instances_tenant_entity", table_name="app_workflows_instances")
    op.drop_table("app_workflows_instances")

    op.drop_index("ix_workflows_transitions_tenant_from", table_name="app_workflows_transitions")
    op.drop_table("app_workflows_transitions")

    op.drop_index("ix_workflows_steps_tenant_version", table_name="app_workflows_steps")
    op.drop_index("ix_workflows_steps_tenant_type", table_name="app_workflows_steps")
    op.drop_table("app_workflows_steps")

    op.drop_index(
        "ux_workflow_definition_versions_active",
        table_name="app_workflows_definition_versions",
    )
    op.drop_index(
        "ix_workflow_definition_versions_tenant_definition",
        table_name="app_workflows_definition_versions",
    )
    op.drop_index(
        "ix_workflow_definition_versions_tenant_status",
        table_name="app_workflows_definition_versions",
    )
    op.drop_table("app_workflows_definition_versions")

    op.drop_index("ix_workflows_definitions_tenant_status", table_name="app_workflows_definitions")
    op.drop_table("app_workflows_definitions")

    op.execute("DROP TYPE IF EXISTS workflow_approval_action")
    op.execute("DROP TYPE IF EXISTS workflow_comment_visibility")
    op.execute("DROP TYPE IF EXISTS workflow_comment_type")
    op.execute("DROP TYPE IF EXISTS workflow_task_status")
    op.execute("DROP TYPE IF EXISTS workflow_instance_status")
    op.execute("DROP TYPE IF EXISTS workflow_assignee_type")
    op.execute("DROP TYPE IF EXISTS workflow_step_type")
    op.execute("DROP TYPE IF EXISTS workflow_trigger_mode")
    op.execute("DROP TYPE IF EXISTS workflow_definition_version_status")
    op.execute("DROP TYPE IF EXISTS workflow_definition_status")
