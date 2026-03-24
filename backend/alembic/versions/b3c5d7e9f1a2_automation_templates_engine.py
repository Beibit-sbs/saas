"""Automation Templates Engine - add app_platform_automation_templates table."""

from alembic import op
import sqlalchemy as sa


def upgrade() -> None:
    """Create app_platform_automation_templates table."""
    op.create_table(
        "app_platform_automation_templates",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.func.gen_random_uuid()),
        sa.Column("template_key", sa.String(128), nullable=False, unique=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("category", sa.String(128), nullable=False),
        sa.Column("event_type", sa.String(128), nullable=False),
        sa.Column("condition_json", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("actions_json", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("is_system_template", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.PrimaryKeyConstraint("id"),
    )

    # Index on template_key for fast lookups
    op.create_index(
        "idx_automation_templates_key",
        "app_platform_automation_templates",
        ["template_key"],
        unique=True,
    )

    # Index on category for filtering
    op.create_index(
        "idx_automation_templates_category",
        "app_platform_automation_templates",
        ["category"],
    )

    # Index on event_type for filtering
    op.create_index(
        "idx_automation_templates_event_type",
        "app_platform_automation_templates",
        ["event_type"],
    )

    # Index on is_system_template
    op.create_index(
        "idx_automation_templates_system",
        "app_platform_automation_templates",
        ["is_system_template"],
    )


def downgrade() -> None:
    """Drop app_platform_automation_templates table."""
    op.drop_table("app_platform_automation_templates")
