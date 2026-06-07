"""A-046.2 runtime tables for Integration Provider Readiness backend foundation."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "ipr0462rt01"
down_revision = "acrm0452rt01"
branch_labels = None
depends_on = None


def _json_default():
    return sa.text("'{}'::jsonb")


def _readiness_columns(status_default: str = "'draft'") -> list[sa.Column]:
    return [
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("provider_id", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=64), nullable=False, server_default=sa.text(status_default)),
        sa.Column("payload_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=_json_default()),
        sa.Column("reason_code", sa.String(length=128), nullable=True),
        sa.Column("actor_user_id", sa.String(length=255), nullable=True),
        sa.Column("readiness_only", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("provider_connected", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("live_provider_calls", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("credentials_stored", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("external_submission", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("sync_execution", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("fake_health_metrics", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("fake_readiness_metrics", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_by_user_id", sa.String(length=255), nullable=True),
        sa.Column("updated_by_user_id", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    ]


def _create_standard_indexes(table_name: str) -> None:
    op.create_index(f"ix_{table_name}_tenant_id", table_name, ["tenant_id"], unique=False)
    op.create_index(f"ix_{table_name}_tenant_provider", table_name, ["tenant_id", "provider_id"], unique=False)


def upgrade() -> None:
    op.create_table(
        "ipr_provider_registry",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("provider_id", sa.String(length=64), nullable=False),
        sa.Column("provider_name", sa.String(length=255), nullable=False),
        sa.Column("provider_type", sa.String(length=128), nullable=False),
        sa.Column("readiness_level", sa.String(length=128), nullable=False),
        sa.Column("future_scope", sa.Text(), nullable=False),
        sa.Column("business_owner_role", sa.String(length=64), nullable=False),
        sa.Column("technical_owner_role", sa.String(length=64), nullable=False),
        sa.Column("security_owner_role", sa.String(length=64), nullable=False),
        sa.Column("auditor_visibility", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("executive_visibility", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("status", sa.String(length=64), nullable=False, server_default=sa.text("'catalogued'")),
        sa.Column("payload_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=_json_default()),
        sa.Column("readiness_only", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("provider_connected", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("live_provider_calls", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("credentials_stored", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("external_submission", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("sync_execution", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("fake_health_metrics", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("fake_readiness_metrics", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_by_user_id", sa.String(length=255), nullable=True),
        sa.Column("updated_by_user_id", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )

    table_names = [
        "ipr_provider_profile_versions",
        "ipr_provider_capability_matrix",
        "ipr_provider_readiness_assessments",
        "ipr_provider_readiness_assessment_scores",
        "ipr_provider_evidence_items",
        "ipr_provider_evidence_links",
        "ipr_provider_compliance_reviews",
        "ipr_provider_security_reviews",
        "ipr_provider_risk_register",
        "ipr_provider_risk_events",
        "ipr_provider_exception_cases",
        "ipr_provider_exception_actions",
        "ipr_provider_status_history",
        "ipr_provider_health_snapshots",
        "ipr_provider_integration_plans",
        "ipr_provider_dependency_edges",
        "ipr_provider_role_assignments",
        "ipr_provider_dashboard_snapshots",
        "ipr_provider_report_artifacts",
        "ipr_provider_policy_violations",
        "ipr_provider_audit_records",
    ]
    for table_name in table_names:
        op.create_table(table_name, *_readiness_columns())

    _create_standard_indexes("ipr_provider_registry")
    for table_name in table_names:
        _create_standard_indexes(table_name)


def downgrade() -> None:
    table_names = [
        "ipr_provider_registry",
        "ipr_provider_profile_versions",
        "ipr_provider_capability_matrix",
        "ipr_provider_readiness_assessments",
        "ipr_provider_readiness_assessment_scores",
        "ipr_provider_evidence_items",
        "ipr_provider_evidence_links",
        "ipr_provider_compliance_reviews",
        "ipr_provider_security_reviews",
        "ipr_provider_risk_register",
        "ipr_provider_risk_events",
        "ipr_provider_exception_cases",
        "ipr_provider_exception_actions",
        "ipr_provider_status_history",
        "ipr_provider_health_snapshots",
        "ipr_provider_integration_plans",
        "ipr_provider_dependency_edges",
        "ipr_provider_role_assignments",
        "ipr_provider_dashboard_snapshots",
        "ipr_provider_report_artifacts",
        "ipr_provider_policy_violations",
        "ipr_provider_audit_records",
    ]
    for table_name in reversed(table_names):
        op.drop_index(f"ix_{table_name}_tenant_provider", table_name=table_name)
        op.drop_index(f"ix_{table_name}_tenant_id", table_name=table_name)
        op.drop_table(table_name)