"""A-043.2 runtime tables for Security / Access / Compliance."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "sac0432rt01"
down_revision = "sss0422rt01"
branch_labels = None
depends_on = None


CREATE_TABLES = [
    "sac_readiness_profiles",
    "sac_dashboard_snapshots",
    "sac_access_governance_records",
    "sac_role_permission_inventory_snapshots",
    "sac_rbac_evidence_records",
    "sac_abac_evidence_records",
    "sac_session_visibility_records",
    "sac_login_event_review_records",
    "sac_mfa_readiness_records",
    "sac_tenant_isolation_evidence_records",
    "sac_security_incident_records",
    "sac_incident_review_records",
    "sac_remediation_tracking_records",
    "sac_risk_register_records",
    "sac_compliance_control_records",
    "sac_policy_control_bridge_records",
    "sac_audit_event_review_records",
    "sac_sensitive_action_review_records",
    "sac_data_protection_readiness_records",
    "sac_privacy_readiness_records",
    "sac_security_exception_records",
    "sac_visitor_access_bridge_records",
    "sac_cross_vertical_bridge_records",
    "sac_limitations",
]


def _jsonb_default_empty_object():
    return sa.text("'{}'::jsonb")


def _jsonb_default_empty_list():
    return sa.text("'[]'::jsonb")


def _common_columns(status_default: str = "'active'") -> list[sa.Column]:
    return [
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("status", sa.String(length=64), nullable=False, server_default=sa.text(status_default)),
        sa.Column("human_review_required", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("certification_claimed", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("compliance_certified", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("soc_siem_replacement", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("autonomous_enforcement_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("external_submission_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("hidden_user_risk_score_present", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("incomplete_data", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("source_module", sa.String(length=128), nullable=True),
        sa.Column("source_entity_id", sa.String(length=128), nullable=True),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=_jsonb_default_empty_object()),
        sa.Column("limitations_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=_jsonb_default_empty_list()),
        sa.Column("created_by", sa.String(length=255), nullable=True),
        sa.Column("updated_by", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
    ]


def _extra_columns(table_name: str) -> list[sa.Column]:
    if table_name == "sac_readiness_profiles":
        return [sa.Column("readiness_level", sa.String(length=64), nullable=False, server_default=sa.text("'baseline'"))]
    if table_name == "sac_dashboard_snapshots":
        return [sa.Column("summary_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=_jsonb_default_empty_object())]
    if table_name in {"sac_security_incident_records", "sac_incident_review_records"}:
        return [sa.Column("incident_ref", sa.String(length=255), nullable=True)]
    if table_name == "sac_cross_vertical_bridge_records":
        return [sa.Column("bridge_key", sa.String(length=64), nullable=False)]
    if table_name == "sac_limitations":
        return [sa.Column("limitation_text", sa.Text(), nullable=False)]
    return []


def _create_standard_indexes(table_name: str) -> None:
    op.create_index(f"ix_{table_name}_tenant_id", table_name, ["tenant_id"], unique=False)
    op.create_index(f"ix_{table_name}_tenant_status", table_name, ["tenant_id", "status"], unique=False)


def upgrade() -> None:
    for table_name in CREATE_TABLES:
        op.create_table(table_name, *(_common_columns() + _extra_columns(table_name)))
        _create_standard_indexes(table_name)


def downgrade() -> None:
    for table_name in reversed(CREATE_TABLES):
        op.drop_index(f"ix_{table_name}_tenant_status", table_name=table_name)
        op.drop_index(f"ix_{table_name}_tenant_id", table_name=table_name)
        op.drop_table(table_name)
