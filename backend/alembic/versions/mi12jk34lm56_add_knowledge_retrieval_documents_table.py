"""Add persistent storage table for knowledge retrieval documents.

Revision ID: mi12jk34lm56
Revises: lh01ij23kl45
Create Date: 2026-04-26 00:30:00.000000
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "mi12jk34lm56"
down_revision: Union[str, None] = "lh01ij23kl45"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "university_knowledge_documents",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("doc_id", sa.String(length=64), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("doc_type", sa.String(length=32), nullable=False),
        sa.Column("source_ref", sa.Text(), nullable=True),
        sa.Column("tags", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("chunks", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("ingested_by", sa.String(length=255), nullable=False),
        sa.Column("ingested_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.UniqueConstraint("tenant_id", "doc_id", name="uq_knowledge_docs_tenant_doc"),
    )

    op.create_index(
        "ix_knowledge_docs_tenant_id",
        "university_knowledge_documents",
        ["tenant_id"],
    )
    op.create_index(
        "ix_knowledge_docs_tenant_doc_type",
        "university_knowledge_documents",
        ["tenant_id", "doc_type"],
    )


def downgrade() -> None:
    op.drop_index("ix_knowledge_docs_tenant_doc_type", table_name="university_knowledge_documents")
    op.drop_index("ix_knowledge_docs_tenant_id", table_name="university_knowledge_documents")
    op.drop_table("university_knowledge_documents")
