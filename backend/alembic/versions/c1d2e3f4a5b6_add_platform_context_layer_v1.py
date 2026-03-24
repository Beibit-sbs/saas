"""add platform context layer v1

Revision ID: c1d2e3f4a5b6
Revises: a1b2c3d4e5f7
Create Date: 2026-03-24 00:00:00.000000

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "c1d2e3f4a5b6"
down_revision = "a1b2c3d4e5f7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "app_platform_context_entities",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("entity_type", sa.String(64), nullable=False),
        sa.Column("entity_id", sa.String(128), nullable=False),
        sa.Column(
            "data_json",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["app_tenants.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "tenant_id",
            "entity_type",
            "entity_id",
            name="uq_context_entities_tenant_type_id",
        ),
    )

    op.create_table(
        "app_platform_context_relations",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("source_entity_type", sa.String(64), nullable=False),
        sa.Column("source_entity_id", sa.String(128), nullable=False),
        sa.Column("relation_type", sa.String(64), nullable=False),
        sa.Column("target_entity_type", sa.String(64), nullable=False),
        sa.Column("target_entity_id", sa.String(128), nullable=False),
        sa.Column(
            "metadata_json",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["app_tenants.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "tenant_id",
            "source_entity_type",
            "source_entity_id",
            "relation_type",
            "target_entity_type",
            "target_entity_id",
            name="uq_context_relations_full",
        ),
    )

    # Indexes for entities
    op.create_index(
        "ix_platform_context_entities_tenant",
        "app_platform_context_entities",
        ["tenant_id"],
    )
    op.create_index(
        "ix_platform_context_entities_type_id",
        "app_platform_context_entities",
        ["tenant_id", "entity_type", "entity_id"],
    )

    # Indexes for relations
    op.create_index(
        "ix_platform_context_relations_tenant",
        "app_platform_context_relations",
        ["tenant_id"],
    )
    op.create_index(
        "ix_platform_context_relations_source",
        "app_platform_context_relations",
        ["tenant_id", "source_entity_type", "source_entity_id"],
    )
    op.create_index(
        "ix_platform_context_relations_target",
        "app_platform_context_relations",
        ["tenant_id", "target_entity_type", "target_entity_id"],
    )
    op.create_index(
        "ix_platform_context_relations_type",
        "app_platform_context_relations",
        ["tenant_id", "relation_type"],
    )


def downgrade() -> None:
    op.drop_index("ix_platform_context_relations_type", table_name="app_platform_context_relations")
    op.drop_index("ix_platform_context_relations_target", table_name="app_platform_context_relations")
    op.drop_index("ix_platform_context_relations_source", table_name="app_platform_context_relations")
    op.drop_index("ix_platform_context_relations_tenant", table_name="app_platform_context_relations")
    op.drop_index("ix_platform_context_entities_type_id", table_name="app_platform_context_entities")
    op.drop_index("ix_platform_context_entities_tenant", table_name="app_platform_context_entities")
    op.drop_table("app_platform_context_relations")
    op.drop_table("app_platform_context_entities")
