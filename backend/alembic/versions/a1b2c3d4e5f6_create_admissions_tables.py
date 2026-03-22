"""Create Admissions module tables with tenant isolation.

Revision ID: a1b2c3d4e5f6
Revises: f6a2d1e9b3c4
Create Date: 2026-03-22 03:30:00+0500

Alembic migration for Phase 1 of AI University Operating System Admissions module.
Creates five core tables with full tenant isolation, indexing, and RLS-ready structure.

Tables:
- app_admissions_applicants: Core applicant entity
- app_admissions_applications: Application process with workflow state
- app_admissions_documents: Document references (safe keys, not paths)
- app_admissions_stage_history: Append-only workflow audit trail
- app_admissions_decisions: Final acceptance/rejection decisions

Constraints:
- All tables include tenant_id FK to app_tenants (CASCADE delete)
- All indexes scoped by tenant_id
- Stage history is append-only (enforced at service layer)
- Decision is one-to-one with application
- Documents store safe references only (s3 keys, not filesystem paths)
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


def upgrade() -> None:
    """Create Admissions tables."""
    
    # ============================================================================
    # app_admissions_applicants
    # ============================================================================
    op.create_table(
        "app_admissions_applicants",
        sa.Column("id", postgresql.BIGSERIAL(), autoincrement=True, nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("first_name", sa.String(128), nullable=False),
        sa.Column("last_name", sa.String(128), nullable=False),
        sa.Column("phone", sa.String(20), nullable=True),
        sa.Column("program_id", sa.BigInteger(), nullable=False),
        sa.Column("application_year", sa.SmallInteger(), nullable=False),
        sa.Column("status", sa.String(64), nullable=False, server_default="'active'"),
        sa.Column("external_id", sa.String(128), nullable=True),
        sa.Column(
            "metadata_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="'{}'::jsonb",
        ),
        sa.Column("created_by", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.ForeignKeyConstraint(["tenant_id"], ["app_tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "tenant_id",
            "email",
            "program_id",
            "application_year",
            name="ux_applicant_tenant_email_program_year",
        ),
    )
    op.create_index("ix_applicant_tenant_id", "app_admissions_applicants", ["tenant_id"])
    op.create_index("ix_applicant_tenant_email", "app_admissions_applicants", ["tenant_id", "email"])
    op.create_index(
        "ix_applicant_tenant_program_year",
        "app_admissions_applicants",
        ["tenant_id", "program_id", "application_year"],
    )
    
    # ============================================================================
    # app_admissions_applications
    # ============================================================================
    op.create_table(
        "app_admissions_applications",
        sa.Column("id", postgresql.BIGSERIAL(), autoincrement=True, nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("applicant_id", sa.BigInteger(), nullable=False),
        sa.Column("program_id", sa.BigInteger(), nullable=False),
        sa.Column("stage", sa.String(64), nullable=False, server_default="'new'"),
        sa.Column("conclusion_type", sa.String(64), nullable=True),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("decision_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version", sa.BigInteger(), nullable=False, server_default="1"),
        sa.Column(
            "metadata_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="'{}'::jsonb",
        ),
        sa.Column("created_by", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.ForeignKeyConstraint(["tenant_id"], ["app_tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["applicant_id"], ["app_admissions_applicants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "applicant_id", name="ux_application_tenant_applicant"),
    )
    op.create_index("ix_application_tenant_id", "app_admissions_applications", ["tenant_id"])
    op.create_index("ix_application_tenant_applicant", "app_admissions_applications", ["tenant_id", "applicant_id"])
    op.create_index(
        "ix_application_tenant_program_stage",
        "app_admissions_applications",
        ["tenant_id", "program_id", "stage"],
    )
    op.create_index("ix_application_tenant_stage", "app_admissions_applications", ["tenant_id", "stage"])
    
    # ============================================================================
    # app_admissions_documents
    # ============================================================================
    op.create_table(
        "app_admissions_documents",
        sa.Column("id", postgresql.BIGSERIAL(), autoincrement=True, nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("application_id", sa.BigInteger(), nullable=False),
        sa.Column("document_type", sa.String(64), nullable=False),
        sa.Column("document_key", sa.String(255), nullable=False),
        sa.Column("file_name", sa.String(255), nullable=False),
        sa.Column("file_size_bytes", sa.BigInteger(), nullable=True),
        sa.Column("mime_type", sa.String(128), nullable=True),
        sa.Column("status", sa.String(64), nullable=False, server_default="'received'"),
        sa.Column(
            "metadata_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="'{}'::jsonb",
        ),
        sa.Column("created_by", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("verified_by", sa.String(255), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["app_tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["application_id"], ["app_admissions_applications.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_document_tenant_id", "app_admissions_documents", ["tenant_id"])
    op.create_index("ix_document_tenant_application", "app_admissions_documents", ["tenant_id", "application_id"])
    op.create_index("ix_document_tenant_type", "app_admissions_documents", ["tenant_id", "document_type"])
    
    # ============================================================================
    # app_admissions_stage_history
    # ============================================================================
    op.create_table(
        "app_admissions_stage_history",
        sa.Column("id", postgresql.BIGSERIAL(), autoincrement=True, nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("application_id", sa.BigInteger(), nullable=False),
        sa.Column("from_stage", sa.String(64), nullable=False),
        sa.Column("to_stage", sa.String(64), nullable=False),
        sa.Column("reason", sa.String(255), nullable=True),
        sa.Column("actor_id", sa.String(255), nullable=False),
        sa.Column("action_type", sa.String(64), nullable=False),
        sa.Column(
            "metadata_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="'{}'::jsonb",
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.ForeignKeyConstraint(["tenant_id"], ["app_tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["application_id"], ["app_admissions_applications.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_stage_history_tenant_id", "app_admissions_stage_history", ["tenant_id"])
    op.create_index(
        "ix_stage_history_tenant_application",
        "app_admissions_stage_history",
        ["tenant_id", "application_id"],
    )
    op.create_index(
        "ix_stage_history_tenant_transition",
        "app_admissions_stage_history",
        ["tenant_id", "from_stage", "to_stage"],
    )
    op.create_index(
        "ix_stage_history_tenant_created_desc",
        "app_admissions_stage_history",
        ["tenant_id", "created_at"],
        postgresql_ops={"created_at": "DESC"},
    )
    
    # ============================================================================
    # app_admissions_decisions
    # ============================================================================
    op.create_table(
        "app_admissions_decisions",
        sa.Column("id", postgresql.BIGSERIAL(), autoincrement=True, nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("application_id", sa.BigInteger(), nullable=False, unique=True),
        sa.Column("decision_type", sa.String(64), nullable=False),
        sa.Column("decision_rationale", sa.String(500), nullable=True),
        sa.Column("decided_by_id", sa.String(255), nullable=False),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column(
            "conditions_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="'{}'::jsonb",
        ),
        sa.Column("version", sa.BigInteger(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.ForeignKeyConstraint(["tenant_id"], ["app_tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["application_id"], ["app_admissions_applications.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_decision_tenant_id", "app_admissions_decisions", ["tenant_id"])
    op.create_index("ix_decision_tenant_type", "app_admissions_decisions", ["tenant_id", "decision_type"])
    op.create_index(
        "ix_decision_tenant_decided_at_desc",
        "app_admissions_decisions",
        ["tenant_id", "decided_at"],
        postgresql_ops={"decided_at": "DESC"},
    )


def downgrade() -> None:
    """Drop Admissions tables (reverse order due to ForeignKey constraints)."""
    op.drop_table("app_admissions_decisions")
    op.drop_table("app_admissions_stage_history")
    op.drop_table("app_admissions_documents")
    op.drop_table("app_admissions_applications")
    op.drop_table("app_admissions_applicants")
