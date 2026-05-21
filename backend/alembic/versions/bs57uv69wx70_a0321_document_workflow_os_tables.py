"""A-032.1 document workflow OS tables.

Revision ID: bs57uv69wx70
Revises: ar46st58uv69
Create Date: 2025-01-01 00:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "bs57uv69wx70"
down_revision = "ar46st58uv69"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "doc_order_decrees",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("decree_type", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="DRAFT_ORDER"),
        sa.Column("registry_number", sa.String(length=64), nullable=True),
        sa.Column("registry_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("effective_date", sa.Date(), nullable=True),
        sa.Column("signed_by_user_id", sa.BigInteger(), nullable=True),
        sa.Column("signed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("linked_document_id", sa.BigInteger(), nullable=True),
        sa.Column("linked_assignment_id", sa.BigInteger(), nullable=True),
        sa.Column("created_by_user_id", sa.BigInteger(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_doc_order_decrees_tenant_id", "doc_order_decrees", ["tenant_id"])
    op.create_index("ix_doc_order_decrees_tenant_status", "doc_order_decrees", ["tenant_id", "status"])

    op.create_table(
        "doc_documents",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("document_type", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="DRAFT"),
        sa.Column("registry_number", sa.String(length=64), nullable=True),
        sa.Column("registry_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("source_department_id", sa.BigInteger(), nullable=True),
        sa.Column("owner_user_id", sa.BigInteger(), nullable=True),
        sa.Column("created_by_user_id", sa.BigInteger(), nullable=False),
        sa.Column("current_version_id", sa.BigInteger(), nullable=True),
        sa.Column("linked_assignment_id", sa.BigInteger(), nullable=True),
        sa.Column("linked_decree_id", sa.BigInteger(), sa.ForeignKey("doc_order_decrees.id"), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_doc_documents_tenant_id", "doc_documents", ["tenant_id"])
    op.create_index("ix_doc_documents_tenant_status", "doc_documents", ["tenant_id", "status"])
    op.create_foreign_key(
        "fk_doc_order_decrees_linked_document_id",
        "doc_order_decrees",
        "doc_documents",
        ["linked_document_id"],
        ["id"],
    )

    op.create_table(
        "doc_document_versions",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("document_id", sa.BigInteger(), sa.ForeignKey("doc_documents.id"), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("body_text", sa.Text(), nullable=True),
        sa.Column("metadata_json", JSONB(), nullable=False, server_default="'{}'::jsonb"),
        sa.Column("created_by_user_id", sa.BigInteger(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )
    op.create_index("ix_doc_document_versions_tenant_doc", "doc_document_versions", ["tenant_id", "document_id"])

    op.create_table(
        "doc_document_status_history",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("document_id", sa.BigInteger(), sa.ForeignKey("doc_documents.id"), nullable=False),
        sa.Column("from_status", sa.String(length=32), nullable=True),
        sa.Column("to_status", sa.String(length=32), nullable=False),
        sa.Column("actor_user_id", sa.BigInteger(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )
    op.create_index("ix_doc_status_history_tenant_doc", "doc_document_status_history", ["tenant_id", "document_id"])

    op.create_table(
        "doc_audit_events",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("entity_type", sa.String(length=64), nullable=False),
        sa.Column("entity_id", sa.BigInteger(), nullable=False),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("actor_user_id", sa.BigInteger(), nullable=False),
        sa.Column("actor_role", sa.String(length=64), nullable=True),
        sa.Column("request_id", sa.String(length=64), nullable=True),
        sa.Column("action", sa.String(length=256), nullable=False),
        sa.Column("payload_json", JSONB(), nullable=False, server_default="'{}'::jsonb"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )
    op.create_index("ix_doc_audit_events_tenant_entity", "doc_audit_events", ["tenant_id", "entity_type", "entity_id"])

    op.create_table(
        "doc_document_reviews",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("document_id", sa.BigInteger(), sa.ForeignKey("doc_documents.id"), nullable=False),
        sa.Column("reviewer_user_id", sa.BigInteger(), nullable=False),
        sa.Column("decision", sa.String(length=32), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )
    op.create_index("ix_doc_reviews_tenant_doc", "doc_document_reviews", ["tenant_id", "document_id"])

    op.create_table(
        "doc_decree_registry_entries",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("decree_id", sa.BigInteger(), sa.ForeignKey("doc_order_decrees.id"), nullable=False),
        sa.Column("registry_number", sa.String(length=64), nullable=False),
        sa.Column("registry_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("registry_year", sa.Integer(), nullable=False),
        sa.Column("created_by_user_id", sa.BigInteger(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("correction_of_entry_id", sa.BigInteger(), nullable=True),
        sa.Column("correction_reason", sa.Text(), nullable=True),
        sa.UniqueConstraint("tenant_id", "registry_number", name="uq_doc_decree_registry_number"),
    )
    op.create_index("ix_doc_decree_registry_tenant", "doc_decree_registry_entries", ["tenant_id"])

    op.create_table(
        "doc_correspondence_items",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("direction", sa.String(length=16), nullable=False),
        sa.Column("subject", sa.String(length=500), nullable=False),
        sa.Column("correspondence_type", sa.String(length=32), nullable=False, server_default="LETTER"),
        sa.Column("sender_name", sa.String(length=256), nullable=True),
        sa.Column("sender_organization", sa.String(length=256), nullable=True),
        sa.Column("recipient_name", sa.String(length=256), nullable=True),
        sa.Column("recipient_organization", sa.String(length=256), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("registry_number", sa.String(length=64), nullable=True),
        sa.Column("registry_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("linked_document_id", sa.BigInteger(), sa.ForeignKey("doc_documents.id"), nullable=True),
        sa.Column("linked_assignment_id", sa.BigInteger(), nullable=True),
        sa.Column("created_by_user_id", sa.BigInteger(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_doc_correspondence_tenant_id", "doc_correspondence_items", ["tenant_id"])
    op.create_index("ix_doc_correspondence_tenant_dir_status", "doc_correspondence_items", ["tenant_id", "direction", "status"])

    op.create_table(
        "doc_correspondence_routes",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("correspondence_id", sa.BigInteger(), sa.ForeignKey("doc_correspondence_items.id"), nullable=False),
        sa.Column("from_user_id", sa.BigInteger(), nullable=True),
        sa.Column("to_user_id", sa.BigInteger(), nullable=True),
        sa.Column("to_role", sa.String(length=64), nullable=True),
        sa.Column("route_comment", sa.Text(), nullable=True),
        sa.Column("created_by_user_id", sa.BigInteger(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )
    op.create_index("ix_doc_correspondence_routes_tenant", "doc_correspondence_routes", ["tenant_id", "correspondence_id"])

    op.create_table(
        "doc_correspondence_registry_entries",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("correspondence_id", sa.BigInteger(), sa.ForeignKey("doc_correspondence_items.id"), nullable=False),
        sa.Column("registry_number", sa.String(length=64), nullable=False),
        sa.Column("registry_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("direction", sa.String(length=16), nullable=False),
        sa.Column("created_by_user_id", sa.BigInteger(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.UniqueConstraint("tenant_id", "registry_number", "direction", name="uq_doc_corr_registry_number_dir"),
    )
    op.create_index("ix_doc_corr_registry_tenant", "doc_correspondence_registry_entries", ["tenant_id"])

    op.create_table(
        "doc_resolutions",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="DRAFT"),
        sa.Column("created_by_user_id", sa.BigInteger(), nullable=False),
        sa.Column("assigned_to_user_id", sa.BigInteger(), nullable=True),
        sa.Column("linked_document_id", sa.BigInteger(), sa.ForeignKey("doc_documents.id"), nullable=True),
        sa.Column("linked_decree_id", sa.BigInteger(), sa.ForeignKey("doc_order_decrees.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_doc_resolutions_tenant_id", "doc_resolutions", ["tenant_id"])

    op.create_table(
        "doc_resolution_assignment_links",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("resolution_id", sa.BigInteger(), sa.ForeignKey("doc_resolutions.id"), nullable=False),
        sa.Column("assignment_id", sa.BigInteger(), nullable=False),
        sa.Column("created_by_user_id", sa.BigInteger(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.UniqueConstraint("tenant_id", "resolution_id", "assignment_id", name="uq_doc_resolution_assignment_link"),
    )
    op.create_index("ix_doc_res_asgn_links_tenant", "doc_resolution_assignment_links", ["tenant_id"])

    op.create_table(
        "doc_document_assignment_links",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("document_id", sa.BigInteger(), sa.ForeignKey("doc_documents.id"), nullable=False),
        sa.Column("assignment_id", sa.BigInteger(), nullable=False),
        sa.Column("link_type", sa.String(length=32), nullable=False, server_default="SOURCE_DOCUMENT"),
        sa.Column("created_by_user_id", sa.BigInteger(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.UniqueConstraint("tenant_id", "document_id", "assignment_id", name="uq_doc_document_assignment_link"),
    )
    op.create_index("ix_doc_doc_asgn_links_tenant", "doc_document_assignment_links", ["tenant_id"])

    op.create_table(
        "doc_archive_records",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("entity_type", sa.String(length=64), nullable=False),
        sa.Column("entity_id", sa.BigInteger(), nullable=False),
        sa.Column("archive_reason", sa.Text(), nullable=True),
        sa.Column("archived_by_user_id", sa.BigInteger(), nullable=False),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )
    op.create_index("ix_doc_archive_records_tenant_entity", "doc_archive_records", ["tenant_id", "entity_type", "entity_id"])


def downgrade() -> None:
    op.drop_index("ix_doc_archive_records_tenant_entity", table_name="doc_archive_records")
    op.drop_table("doc_archive_records")
    op.drop_index("ix_doc_doc_asgn_links_tenant", table_name="doc_document_assignment_links")
    op.drop_table("doc_document_assignment_links")
    op.drop_index("ix_doc_res_asgn_links_tenant", table_name="doc_resolution_assignment_links")
    op.drop_table("doc_resolution_assignment_links")
    op.drop_index("ix_doc_resolutions_tenant_id", table_name="doc_resolutions")
    op.drop_table("doc_resolutions")
    op.drop_index("ix_doc_corr_registry_tenant", table_name="doc_correspondence_registry_entries")
    op.drop_table("doc_correspondence_registry_entries")
    op.drop_index("ix_doc_correspondence_routes_tenant", table_name="doc_correspondence_routes")
    op.drop_table("doc_correspondence_routes")
    op.drop_index("ix_doc_correspondence_tenant_dir_status", table_name="doc_correspondence_items")
    op.drop_index("ix_doc_correspondence_tenant_id", table_name="doc_correspondence_items")
    op.drop_table("doc_correspondence_items")
    op.drop_index("ix_doc_decree_registry_tenant", table_name="doc_decree_registry_entries")
    op.drop_table("doc_decree_registry_entries")
    op.drop_index("ix_doc_reviews_tenant_doc", table_name="doc_document_reviews")
    op.drop_table("doc_document_reviews")
    op.drop_index("ix_doc_audit_events_tenant_entity", table_name="doc_audit_events")
    op.drop_table("doc_audit_events")
    op.drop_index("ix_doc_status_history_tenant_doc", table_name="doc_document_status_history")
    op.drop_table("doc_document_status_history")
    op.drop_index("ix_doc_document_versions_tenant_doc", table_name="doc_document_versions")
    op.drop_table("doc_document_versions")
    op.drop_constraint("fk_doc_order_decrees_linked_document_id", "doc_order_decrees", type_="foreignkey")
    op.drop_index("ix_doc_documents_tenant_status", table_name="doc_documents")
    op.drop_index("ix_doc_documents_tenant_id", table_name="doc_documents")
    op.drop_table("doc_documents")
    op.drop_index("ix_doc_order_decrees_tenant_status", table_name="doc_order_decrees")
    op.drop_index("ix_doc_order_decrees_tenant_id", table_name="doc_order_decrees")
    op.drop_table("doc_order_decrees")
