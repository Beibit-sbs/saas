"""Document Workflow OS — SQLAlchemy ORM Models.

All tables prefixed doc_.
tenant_id: BigInteger, indexed, required on every table.
Primary keys: BigInteger autoincrement.
Enums: String constants (VARCHAR) for portability.
No hard delete: archive/soft-delete pattern only.
A-031 assignment references: BigInteger ID only (no ORM FK cross-module).
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
    text as sa_text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


# ---------------------------------------------------------------------------
# Enum constants
# ---------------------------------------------------------------------------

class DocumentStatus:
    DRAFT                   = "DRAFT"
    REGISTERED              = "REGISTERED"
    UNDER_REVIEW            = "UNDER_REVIEW"
    RETURNED_FOR_REVISION   = "RETURNED_FOR_REVISION"
    APPROVED                = "APPROVED"
    SIGNED                  = "SIGNED"
    ISSUED                  = "ISSUED"
    LINKED_TO_ASSIGNMENT    = "LINKED_TO_ASSIGNMENT"
    IN_EXECUTION            = "IN_EXECUTION"
    EXECUTION_REPORTED      = "EXECUTION_REPORTED"
    ARCHIVED                = "ARCHIVED"
    CANCELLED               = "CANCELLED"

    ALL = frozenset({
        "DRAFT", "REGISTERED", "UNDER_REVIEW", "RETURNED_FOR_REVISION",
        "APPROVED", "SIGNED", "ISSUED", "LINKED_TO_ASSIGNMENT",
        "IN_EXECUTION", "EXECUTION_REPORTED", "ARCHIVED", "CANCELLED",
    })
    TERMINAL = frozenset({"ARCHIVED", "CANCELLED"})
    ACTIVE = ALL - TERMINAL

    ALLOWED_TRANSITIONS: dict[str, frozenset[str]] = {
        "DRAFT":                   frozenset({"REGISTERED", "CANCELLED"}),
        "REGISTERED":              frozenset({"UNDER_REVIEW", "CANCELLED"}),
        "UNDER_REVIEW":            frozenset({"RETURNED_FOR_REVISION", "APPROVED", "CANCELLED"}),
        "RETURNED_FOR_REVISION":   frozenset({"UNDER_REVIEW", "CANCELLED"}),
        "APPROVED":                frozenset({"SIGNED", "CANCELLED"}),
        "SIGNED":                  frozenset({"ISSUED", "CANCELLED"}),
        "ISSUED":                  frozenset({"LINKED_TO_ASSIGNMENT", "ARCHIVED", "CANCELLED"}),
        "LINKED_TO_ASSIGNMENT":    frozenset({"IN_EXECUTION", "ARCHIVED", "CANCELLED"}),
        "IN_EXECUTION":            frozenset({"EXECUTION_REPORTED", "CANCELLED"}),
        "EXECUTION_REPORTED":      frozenset({"ARCHIVED", "CANCELLED"}),
        "ARCHIVED":                frozenset(),
        "CANCELLED":               frozenset({"ARCHIVED"}),
    }


class DecreeStatus:
    DRAFT_ORDER             = "DRAFT_ORDER"
    LEGAL_REVIEW            = "LEGAL_REVIEW"
    RECTOR_REVIEW           = "RECTOR_REVIEW"
    APPROVED_FOR_SIGNING    = "APPROVED_FOR_SIGNING"
    SIGNED                  = "SIGNED"
    REGISTERED              = "REGISTERED"
    PUBLISHED_INTERNAL      = "PUBLISHED_INTERNAL"
    ASSIGNED_FOR_EXECUTION  = "ASSIGNED_FOR_EXECUTION"
    EXECUTION_TRACKED       = "EXECUTION_TRACKED"
    COMPLETED               = "COMPLETED"
    ARCHIVED                = "ARCHIVED"
    CANCELLED               = "CANCELLED"

    ALL = frozenset({
        "DRAFT_ORDER", "LEGAL_REVIEW", "RECTOR_REVIEW", "APPROVED_FOR_SIGNING",
        "SIGNED", "REGISTERED", "PUBLISHED_INTERNAL", "ASSIGNED_FOR_EXECUTION",
        "EXECUTION_TRACKED", "COMPLETED", "ARCHIVED", "CANCELLED",
    })
    TERMINAL = frozenset({"ARCHIVED", "CANCELLED"})
    ACTIVE = ALL - TERMINAL

    ALLOWED_TRANSITIONS: dict[str, frozenset[str]] = {
        "DRAFT_ORDER":              frozenset({"LEGAL_REVIEW", "CANCELLED"}),
        "LEGAL_REVIEW":             frozenset({"RECTOR_REVIEW", "DRAFT_ORDER", "CANCELLED"}),
        "RECTOR_REVIEW":            frozenset({"APPROVED_FOR_SIGNING", "DRAFT_ORDER", "CANCELLED"}),
        "APPROVED_FOR_SIGNING":     frozenset({"SIGNED", "CANCELLED"}),
        "SIGNED":                   frozenset({"REGISTERED", "CANCELLED"}),
        "REGISTERED":               frozenset({"PUBLISHED_INTERNAL", "CANCELLED"}),
        "PUBLISHED_INTERNAL":       frozenset({"ASSIGNED_FOR_EXECUTION", "COMPLETED", "ARCHIVED", "CANCELLED"}),
        "ASSIGNED_FOR_EXECUTION":   frozenset({"EXECUTION_TRACKED", "CANCELLED"}),
        "EXECUTION_TRACKED":        frozenset({"COMPLETED", "CANCELLED"}),
        "COMPLETED":                frozenset({"ARCHIVED"}),
        "ARCHIVED":                 frozenset(),
        "CANCELLED":                frozenset({"ARCHIVED"}),
    }


class CorrespondenceDirection:
    INCOMING = "INCOMING"
    OUTGOING = "OUTGOING"
    ALL = frozenset({"INCOMING", "OUTGOING"})


class IncomingCorrespondenceStatus:
    RECEIVED    = "RECEIVED"
    REGISTERED  = "REGISTERED"
    CLASSIFIED  = "CLASSIFIED"
    ROUTED      = "ROUTED"
    ASSIGNED    = "ASSIGNED"
    IN_PROGRESS = "IN_PROGRESS"
    RESPONDED   = "RESPONDED"
    ARCHIVED    = "ARCHIVED"

    ALL = frozenset({
        "RECEIVED", "REGISTERED", "CLASSIFIED", "ROUTED",
        "ASSIGNED", "IN_PROGRESS", "RESPONDED", "ARCHIVED",
    })
    TERMINAL = frozenset({"ARCHIVED"})

    ALLOWED_TRANSITIONS: dict[str, frozenset[str]] = {
        "RECEIVED":     frozenset({"REGISTERED", "ARCHIVED"}),
        "REGISTERED":   frozenset({"CLASSIFIED", "ARCHIVED"}),
        "CLASSIFIED":   frozenset({"ROUTED", "ARCHIVED"}),
        "ROUTED":       frozenset({"ASSIGNED", "ARCHIVED"}),
        "ASSIGNED":     frozenset({"IN_PROGRESS", "ARCHIVED"}),
        "IN_PROGRESS":  frozenset({"RESPONDED", "ARCHIVED"}),
        "RESPONDED":    frozenset({"ARCHIVED"}),
        "ARCHIVED":     frozenset(),
    }


class OutgoingCorrespondenceStatus:
    DRAFT                   = "DRAFT"
    UNDER_REVIEW            = "UNDER_REVIEW"
    APPROVED                = "APPROVED"
    REGISTERED              = "REGISTERED"
    SENT_METADATA_ONLY      = "SENT_METADATA_ONLY"
    DELIVERED_METADATA_ONLY = "DELIVERED_METADATA_ONLY"
    ARCHIVED                = "ARCHIVED"

    ALL = frozenset({
        "DRAFT", "UNDER_REVIEW", "APPROVED", "REGISTERED",
        "SENT_METADATA_ONLY", "DELIVERED_METADATA_ONLY", "ARCHIVED",
    })
    TERMINAL = frozenset({"ARCHIVED"})

    ALLOWED_TRANSITIONS: dict[str, frozenset[str]] = {
        "DRAFT":                    frozenset({"UNDER_REVIEW", "ARCHIVED"}),
        "UNDER_REVIEW":             frozenset({"APPROVED", "DRAFT", "ARCHIVED"}),
        "APPROVED":                 frozenset({"REGISTERED", "ARCHIVED"}),
        "REGISTERED":               frozenset({"SENT_METADATA_ONLY", "ARCHIVED"}),
        "SENT_METADATA_ONLY":       frozenset({"DELIVERED_METADATA_ONLY", "ARCHIVED"}),
        "DELIVERED_METADATA_ONLY":  frozenset({"ARCHIVED"}),
        "ARCHIVED":                 frozenset(),
    }


class DocumentType:
    INTERNAL_MEMO   = "INTERNAL_MEMO"
    ORDER           = "ORDER"
    DECREE          = "DECREE"
    LETTER          = "LETTER"
    PROTOCOL        = "PROTOCOL"
    RESOLUTION      = "RESOLUTION"
    REPORT          = "REPORT"
    OTHER           = "OTHER"
    CORRESPONDENCE  = "CORRESPONDENCE"

    ALL = frozenset({
        "INTERNAL_MEMO", "ORDER", "DECREE", "LETTER", "PROTOCOL",
        "RESOLUTION", "REPORT", "OTHER", "CORRESPONDENCE",
    })


class ReviewDecision:
    APPROVED                = "APPROVED"
    RETURNED_FOR_REVISION   = "RETURNED_FOR_REVISION"
    REJECTED_METADATA_ONLY  = "REJECTED_METADATA_ONLY"

    ALL = frozenset({"APPROVED", "RETURNED_FOR_REVISION", "REJECTED_METADATA_ONLY"})


class AuditEventType:
    DOCUMENT_CREATED                    = "DOCUMENT_CREATED"
    DOCUMENT_UPDATED                    = "DOCUMENT_UPDATED"
    DOCUMENT_REGISTERED                 = "DOCUMENT_REGISTERED"
    DOCUMENT_SUBMITTED_FOR_REVIEW       = "DOCUMENT_SUBMITTED_FOR_REVIEW"
    DOCUMENT_RETURNED                   = "DOCUMENT_RETURNED"
    DOCUMENT_APPROVED                   = "DOCUMENT_APPROVED"
    DOCUMENT_SIGNED_METADATA_RECORDED   = "DOCUMENT_SIGNED_METADATA_RECORDED"
    DOCUMENT_ISSUED                     = "DOCUMENT_ISSUED"
    DOCUMENT_ARCHIVED                   = "DOCUMENT_ARCHIVED"
    DOCUMENT_CANCELLED                  = "DOCUMENT_CANCELLED"
    DOCUMENT_ASSIGNMENT_LINKED          = "DOCUMENT_ASSIGNMENT_LINKED"
    DECREE_CREATED                      = "DECREE_CREATED"
    DECREE_UPDATED                      = "DECREE_UPDATED"
    DECREE_LEGAL_REVIEW_STARTED         = "DECREE_LEGAL_REVIEW_STARTED"
    DECREE_APPROVED_FOR_SIGNING         = "DECREE_APPROVED_FOR_SIGNING"
    DECREE_SIGNED_METADATA_RECORDED     = "DECREE_SIGNED_METADATA_RECORDED"
    DECREE_REGISTERED                   = "DECREE_REGISTERED"
    DECREE_ARCHIVED                     = "DECREE_ARCHIVED"
    DECREE_CANCELLED                    = "DECREE_CANCELLED"
    CORRESPONDENCE_REGISTERED           = "CORRESPONDENCE_REGISTERED"
    CORRESPONDENCE_ROUTED               = "CORRESPONDENCE_ROUTED"
    CORRESPONDENCE_SENT_METADATA_RECORDED = "CORRESPONDENCE_SENT_METADATA_RECORDED"
    CORRESPONDENCE_ARCHIVED             = "CORRESPONDENCE_ARCHIVED"
    RESOLUTION_CREATED                  = "RESOLUTION_CREATED"
    RESOLUTION_ASSIGNMENT_LINKED        = "RESOLUTION_ASSIGNMENT_LINKED"
    ASSIGNMENT_LINKED                   = "ASSIGNMENT_LINKED"
    DASHBOARD_VIEWED                    = "DASHBOARD_VIEWED"
    ARCHIVE_RECORDED                    = "ARCHIVE_RECORDED"

    ALL = frozenset({
        "DOCUMENT_CREATED", "DOCUMENT_UPDATED", "DOCUMENT_REGISTERED",
        "DOCUMENT_SUBMITTED_FOR_REVIEW", "DOCUMENT_RETURNED", "DOCUMENT_APPROVED",
        "DOCUMENT_SIGNED_METADATA_RECORDED", "DOCUMENT_ISSUED", "DOCUMENT_ARCHIVED",
        "DOCUMENT_CANCELLED", "DOCUMENT_ASSIGNMENT_LINKED",
        "DECREE_CREATED", "DECREE_UPDATED", "DECREE_LEGAL_REVIEW_STARTED",
        "DECREE_APPROVED_FOR_SIGNING", "DECREE_SIGNED_METADATA_RECORDED",
        "DECREE_REGISTERED", "DECREE_ARCHIVED", "DECREE_CANCELLED",
        "CORRESPONDENCE_REGISTERED", "CORRESPONDENCE_ROUTED",
        "CORRESPONDENCE_SENT_METADATA_RECORDED", "CORRESPONDENCE_ARCHIVED",
        "RESOLUTION_CREATED", "RESOLUTION_ASSIGNMENT_LINKED",
        "ASSIGNMENT_LINKED", "DASHBOARD_VIEWED", "ARCHIVE_RECORDED",
    })


# ---------------------------------------------------------------------------
# 1. doc_documents
# ---------------------------------------------------------------------------

class Document(Base):
    __tablename__ = "doc_documents"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    document_type: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default=DocumentStatus.DRAFT,
        server_default=sa_text("'DRAFT'"),
    )
    registry_number: Mapped[str | None] = mapped_column(String(64), nullable=True)
    registry_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    source_department_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    owner_user_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    created_by_user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    current_version_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    linked_assignment_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    linked_decree_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("doc_order_decrees.id"), nullable=True
    )
    version: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1, server_default=sa_text("1")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=sa_text("NOW()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=sa_text("NOW()")
    )
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    versions: Mapped[list["DocumentVersion"]] = relationship(
        "DocumentVersion", back_populates="document", lazy="select",
        foreign_keys="DocumentVersion.document_id",
    )
    reviews: Mapped[list["DocumentReview"]] = relationship(
        "DocumentReview", back_populates="document", lazy="select",
    )
    assignment_links: Mapped[list["DocumentAssignmentLink"]] = relationship(
        "DocumentAssignmentLink", back_populates="document", lazy="select",
    )

    __table_args__ = (
        Index("ix_doc_documents_tenant_id", "tenant_id"),
        Index("ix_doc_documents_tenant_status", "tenant_id", "status"),
    )


# ---------------------------------------------------------------------------
# 2. doc_document_versions
# ---------------------------------------------------------------------------

class DocumentVersion(Base):
    __tablename__ = "doc_document_versions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    document_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("doc_documents.id"), nullable=False
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    body_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[dict] = mapped_column(
        JSONB, nullable=False, default=dict, server_default=sa_text("'{}'::jsonb")
    )
    created_by_user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=sa_text("NOW()")
    )

    document: Mapped["Document"] = relationship(
        "Document", back_populates="versions",
        foreign_keys="DocumentVersion.document_id",
    )

    __table_args__ = (
        Index("ix_doc_document_versions_tenant_doc", "tenant_id", "document_id"),
    )


# ---------------------------------------------------------------------------
# 3. doc_document_status_history
# ---------------------------------------------------------------------------

class DocumentStatusHistory(Base):
    __tablename__ = "doc_document_status_history"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    document_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("doc_documents.id"), nullable=False
    )
    from_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    to_status: Mapped[str] = mapped_column(String(32), nullable=False)
    actor_user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=sa_text("NOW()")
    )

    __table_args__ = (
        Index("ix_doc_status_history_tenant_doc", "tenant_id", "document_id"),
    )


# ---------------------------------------------------------------------------
# 4. doc_audit_events
# ---------------------------------------------------------------------------

class DocumentAuditEvent(Base):
    __tablename__ = "doc_audit_events"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    actor_user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    actor_role: Mapped[str | None] = mapped_column(String(64), nullable=True)
    request_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    action: Mapped[str] = mapped_column(String(256), nullable=False)
    payload_json: Mapped[dict] = mapped_column(
        JSONB, nullable=False, default=dict, server_default=sa_text("'{}'::jsonb")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=sa_text("NOW()")
    )

    __table_args__ = (
        Index("ix_doc_audit_events_tenant_entity", "tenant_id", "entity_type", "entity_id"),
    )


# ---------------------------------------------------------------------------
# 5. doc_document_reviews
# ---------------------------------------------------------------------------

class DocumentReview(Base):
    __tablename__ = "doc_document_reviews"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    document_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("doc_documents.id"), nullable=False
    )
    reviewer_user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    decision: Mapped[str] = mapped_column(String(32), nullable=False)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=sa_text("NOW()")
    )

    document: Mapped["Document"] = relationship("Document", back_populates="reviews")

    __table_args__ = (
        Index("ix_doc_reviews_tenant_doc", "tenant_id", "document_id"),
    )


# ---------------------------------------------------------------------------
# 6. doc_order_decrees
# ---------------------------------------------------------------------------

class OrderDecree(Base):
    __tablename__ = "doc_order_decrees"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    decree_type: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default=DecreeStatus.DRAFT_ORDER,
        server_default=sa_text("'DRAFT_ORDER'"),
    )
    registry_number: Mapped[str | None] = mapped_column(String(64), nullable=True)
    registry_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    effective_date: Mapped[datetime | None] = mapped_column(Date, nullable=True)
    signed_by_user_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    signed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    linked_document_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("doc_documents.id"), nullable=True
    )
    linked_assignment_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    created_by_user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    version: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1, server_default=sa_text("1")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=sa_text("NOW()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=sa_text("NOW()")
    )
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_doc_order_decrees_tenant_id", "tenant_id"),
        Index("ix_doc_order_decrees_tenant_status", "tenant_id", "status"),
    )


# ---------------------------------------------------------------------------
# 7. doc_decree_registry_entries
# ---------------------------------------------------------------------------

class OrderDecreeRegistryEntry(Base):
    __tablename__ = "doc_decree_registry_entries"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    decree_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("doc_order_decrees.id"), nullable=False
    )
    registry_number: Mapped[str] = mapped_column(String(64), nullable=False)
    registry_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    registry_year: Mapped[int] = mapped_column(Integer, nullable=False)
    created_by_user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=sa_text("NOW()")
    )
    correction_of_entry_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    correction_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        Index("ix_doc_decree_registry_tenant", "tenant_id"),
        UniqueConstraint("tenant_id", "registry_number", name="uq_doc_decree_registry_number"),
    )


# ---------------------------------------------------------------------------
# 8. doc_correspondence_items
# ---------------------------------------------------------------------------

class CorrespondenceItem(Base):
    __tablename__ = "doc_correspondence_items"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    direction: Mapped[str] = mapped_column(String(16), nullable=False)
    subject: Mapped[str] = mapped_column(String(500), nullable=False)
    correspondence_type: Mapped[str] = mapped_column(String(32), nullable=False, server_default=sa_text("'LETTER'"))
    sender_name: Mapped[str | None] = mapped_column(String(256), nullable=True)
    sender_organization: Mapped[str | None] = mapped_column(String(256), nullable=True)
    recipient_name: Mapped[str | None] = mapped_column(String(256), nullable=True)
    recipient_organization: Mapped[str | None] = mapped_column(String(256), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    registry_number: Mapped[str | None] = mapped_column(String(64), nullable=True)
    registry_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    received_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    linked_document_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("doc_documents.id"), nullable=True
    )
    linked_assignment_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    created_by_user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=sa_text("NOW()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=sa_text("NOW()")
    )
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    routes: Mapped[list["CorrespondenceRoute"]] = relationship(
        "CorrespondenceRoute", back_populates="correspondence", lazy="select",
    )

    __table_args__ = (
        Index("ix_doc_correspondence_tenant_id", "tenant_id"),
        Index("ix_doc_correspondence_tenant_dir_status", "tenant_id", "direction", "status"),
    )


# ---------------------------------------------------------------------------
# 9. doc_correspondence_routes
# ---------------------------------------------------------------------------

class CorrespondenceRoute(Base):
    __tablename__ = "doc_correspondence_routes"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    correspondence_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("doc_correspondence_items.id"), nullable=False
    )
    from_user_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    to_user_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    to_role: Mapped[str | None] = mapped_column(String(64), nullable=True)
    route_comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by_user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=sa_text("NOW()")
    )

    correspondence: Mapped["CorrespondenceItem"] = relationship(
        "CorrespondenceItem", back_populates="routes"
    )

    __table_args__ = (
        Index("ix_doc_correspondence_routes_tenant", "tenant_id", "correspondence_id"),
    )


# ---------------------------------------------------------------------------
# 10. doc_correspondence_registry_entries
# ---------------------------------------------------------------------------

class CorrespondenceRegistryEntry(Base):
    __tablename__ = "doc_correspondence_registry_entries"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    correspondence_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("doc_correspondence_items.id"), nullable=False
    )
    registry_number: Mapped[str] = mapped_column(String(64), nullable=False)
    registry_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    direction: Mapped[str] = mapped_column(String(16), nullable=False)
    created_by_user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=sa_text("NOW()")
    )

    __table_args__ = (
        Index("ix_doc_corr_registry_tenant", "tenant_id"),
        UniqueConstraint(
            "tenant_id", "registry_number", "direction",
            name="uq_doc_corr_registry_number_dir",
        ),
    )


# ---------------------------------------------------------------------------
# 11. doc_resolutions
# ---------------------------------------------------------------------------

class Resolution(Base):
    __tablename__ = "doc_resolutions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="DRAFT", server_default=sa_text("'DRAFT'")
    )
    created_by_user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    assigned_to_user_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    linked_document_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("doc_documents.id"), nullable=True
    )
    linked_decree_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("doc_order_decrees.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=sa_text("NOW()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=sa_text("NOW()")
    )
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    assignment_links: Mapped[list["ResolutionAssignmentLink"]] = relationship(
        "ResolutionAssignmentLink", back_populates="resolution", lazy="select",
    )

    __table_args__ = (
        Index("ix_doc_resolutions_tenant_id", "tenant_id"),
    )


# ---------------------------------------------------------------------------
# 12. doc_resolution_assignment_links
# ---------------------------------------------------------------------------

class ResolutionAssignmentLink(Base):
    __tablename__ = "doc_resolution_assignment_links"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    resolution_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("doc_resolutions.id"), nullable=False
    )
    assignment_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    created_by_user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=sa_text("NOW()")
    )

    resolution: Mapped["Resolution"] = relationship(
        "Resolution", back_populates="assignment_links"
    )

    __table_args__ = (
        Index("ix_doc_res_asgn_links_tenant", "tenant_id"),
        UniqueConstraint(
            "tenant_id", "resolution_id", "assignment_id",
            name="uq_doc_resolution_assignment_link",
        ),
    )


# ---------------------------------------------------------------------------
# 13. doc_document_assignment_links
# ---------------------------------------------------------------------------

class DocumentAssignmentLink(Base):
    __tablename__ = "doc_document_assignment_links"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    document_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("doc_documents.id"), nullable=False
    )
    assignment_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    link_type: Mapped[str] = mapped_column(
        String(32), nullable=False, server_default=sa_text("'SOURCE_DOCUMENT'")
    )
    created_by_user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=sa_text("NOW()")
    )

    document: Mapped["Document"] = relationship(
        "Document", back_populates="assignment_links"
    )

    __table_args__ = (
        Index("ix_doc_doc_asgn_links_tenant", "tenant_id"),
        UniqueConstraint(
            "tenant_id", "document_id", "assignment_id",
            name="uq_doc_document_assignment_link",
        ),
    )


# ---------------------------------------------------------------------------
# 14. doc_archive_records
# ---------------------------------------------------------------------------

class ArchiveRecord(Base):
    __tablename__ = "doc_archive_records"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    archive_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    archived_by_user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    archived_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=sa_text("NOW()")
    )

    __table_args__ = (
        Index("ix_doc_archive_records_tenant_entity", "tenant_id", "entity_type", "entity_id"),
    )
