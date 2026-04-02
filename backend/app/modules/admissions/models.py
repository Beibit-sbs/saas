"""
Admissions Module - SQLAlchemy ORM Models

Schema: Five core entities for admissions workflow management
- ApplicantModel: Person applying to program
- ApplicationModel: Admission application process with workflow state
- ApplicationDocumentModel: Document references (safe keys, not file paths)
- ApplicationStageHistoryModel: Append-only workflow audit trail
- ApplicationDecisionModel: Final acceptance/rejection/waitlist decision

Tenant Isolation:
- All tables include tenant_id (BigInteger, FK to app_tenants)
- All queries filtered by tenant_id at service level (phase 2)
- RLS policies prepared (phase 2)
- No implicit tenant defaults; fail-closed contract

Audit Readiness:
- Timestamps: created_at, updated_at, (verified_at, decided_at where applicable)
- Actors: created_by, verified_by, decided_by_id, actor_id (in history)
- Metadata: metadata_json JSONB for extensibility
- Stage history: append-only, immutable records
"""

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Index,
    String,
    SmallInteger,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class ApplicantModel(Base):
    """
    Applicant Entity: Person applying to a program.
    
    Uniqueness constraints:
    - (tenant_id, email, program_id, application_year) must be unique
      (one application per person per program per year)
    
    Relationships:
    - tenant_id FK to app_tenants
    - applications: 1:Many to ApplicationModel
    
    Indexes:
    - Primary: tenant_id (all tenant access)
    - Composite: (tenant_id, email) for quick lookup
    - Composite: (tenant_id, program_id, application_year) for list/filter
    """
    
    __tablename__ = "app_admissions_applicants"
    
    # Primary key and tenant scope
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("app_tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Identity
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    first_name: Mapped[str] = mapped_column(String(128), nullable=False)
    last_name: Mapped[str] = mapped_column(String(128), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    
    # Application context (program reference; assumes university_programs.id or external)
    program_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    application_year: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    
    # Status tracking
    status: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        default="active",
        server_default=text("'active'"),
    )
    
    # External integration
    external_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    
    # Flexible metadata (country, citizenship, gpa_estimate, etc.)
    metadata_json: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )
    
    # Audit trail
    created_by: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
        onupdate=text("NOW()"),
    )
    
    # Relationships
    tenant = relationship("TenantModel", foreign_keys=[tenant_id], viewonly=True)
    applications = relationship(
        "ApplicationModel",
        back_populates="applicant",
        cascade="all, delete-orphan",
        foreign_keys="ApplicationModel.applicant_id",
    )
    
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "email",
            "program_id",
            "application_year",
            name="ux_applicant_tenant_email_program_year",
        ),
        Index("ix_applicant_tenant_email", "tenant_id", "email"),
        Index("ix_applicant_tenant_program_year", "tenant_id", "program_id", "application_year"),
    )


class ApplicationModel(Base):
    """
    Application Entity: Admission application process with workflow state.
    
    Workflow stages: new → received → under_review → decision_pending → concluded
    Conclusion types (once stage=concluded): accepted, rejected, waitlist, withdrawn
    
    Uniqueness constraints:
    - (tenant_id, applicant_id) one active application per applicant
    
    Relationships:
    - tenant_id FK to app_tenants
    - applicant_id FK to ApplicantModel
    - documents: 1:Many to ApplicationDocumentModel
    - stage_history: 1:Many to ApplicationStageHistoryModel
    - decision: 1:1 to ApplicationDecisionModel
    
    Indexes:
    - Primary: tenant_id
    - Composite: (tenant_id, applicant_id)
    - Composite: (tenant_id, program_id, stage) for stage filtering
    - Composite: (tenant_id, stage) for workflow queries
    """
    
    __tablename__ = "app_admissions_applications"
    
    # Primary key and tenant scope
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("app_tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Entity references
    applicant_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("app_admissions_applicants.id", ondelete="CASCADE"),
        nullable=False,
    )
    program_id: Mapped[int] = mapped_column(BigInteger, nullable=False)  # Denormalized
    
    # Workflow state
    stage: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        default="new",
        server_default=text("'new'"),
    )
    conclusion_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    
    # Timestamps for workflow
    received_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    decision_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Version control for conflict resolution
    version: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        default=1,
        server_default=text("1"),
    )
    
    # Flexible metadata (gpa_on_submit, gre_score, etc.)
    metadata_json: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )
    
    # Audit trail
    created_by: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
        onupdate=text("NOW()"),
    )
    
    # Relationships
    tenant = relationship("TenantModel", foreign_keys=[tenant_id], viewonly=True)
    applicant = relationship(
        "ApplicantModel",
        back_populates="applications",
        foreign_keys=[applicant_id],
    )
    documents = relationship(
        "ApplicationDocumentModel",
        back_populates="application",
        cascade="all, delete-orphan",
        foreign_keys="ApplicationDocumentModel.application_id",
    )
    stage_history = relationship(
        "ApplicationStageHistoryModel",
        back_populates="application",
        cascade="all, delete-orphan",
        foreign_keys="ApplicationStageHistoryModel.application_id",
    )
    decision = relationship(
        "ApplicationDecisionModel",
        back_populates="application",
        uselist=False,
        cascade="all, delete-orphan",
        foreign_keys="ApplicationDecisionModel.application_id",
    )
    
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "applicant_id",
            name="ux_application_tenant_applicant",
        ),
        Index("ix_application_tenant_applicant", "tenant_id", "applicant_id"),
        Index("ix_application_tenant_program_stage", "tenant_id", "program_id", "stage"),
        Index("ix_application_tenant_stage", "tenant_id", "stage"),
    )


class ApplicationDocumentModel(Base):
    """
    Document Reference Entity: Store document metadata, not content.
    
    CRITICAL: document_key is a SAFE REFERENCE (e.g., s3://bucket/tenant_123/app_456/doc_789.pdf)
    - Never store raw filesystem paths
    - Never return document_key to untrusted callers during preview
    - File content retrieval is a separate secured endpoint (not in MVP)
    
    Relationships:
    - tenant_id FK to app_tenants
    - application_id FK to ApplicationModel
    
    Indexes:
    - Primary: tenant_id
    - Composite: (tenant_id, application_id) for document list
    - Composite: (tenant_id, document_type) for type-based queries
    """
    
    __tablename__ = "app_admissions_documents"
    
    # Primary key and tenant scope
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("app_tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Entity reference
    application_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("app_admissions_applications.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # Document metadata
    document_type: Mapped[str] = mapped_column(String(64), nullable=False)
    document_key: Mapped[str] = mapped_column(String(255), nullable=False)  # Safe reference
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_size_bytes: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    mime_type: Mapped[str | None] = mapped_column(String(128), nullable=True)
    
    # Status
    status: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        default="received",
        server_default=text("'received'"),
    )
    
    # Flexible metadata (upload_source: "portal|email", virus_scan_status, etc.)
    metadata_json: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )
    
    # Audit trail
    created_by: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
    )
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    verified_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    
    # Relationships
    tenant = relationship("TenantModel", foreign_keys=[tenant_id], viewonly=True)
    application = relationship(
        "ApplicationModel",
        back_populates="documents",
        foreign_keys=[application_id],
    )
    
    __table_args__ = (
        Index("ix_document_tenant_application", "tenant_id", "application_id"),
        Index("ix_document_tenant_type", "tenant_id", "document_type"),
    )


class ApplicationStageHistoryModel(Base):
    """
    Stage History Entity: Append-only audit trail of workflow transitions.
    
    IMMUTABLE: Once inserted, never updated or deleted (enforced at service layer)
    Records every transition with actor, reason, and metadata.
    
    Relationships:
    - tenant_id FK to app_tenants
    - application_id FK to ApplicationModel
    
    Indexes:
    - Primary: tenant_id
    - Composite: (tenant_id, application_id) for application history
    - Composite: (tenant_id, from_stage, to_stage) for transition analysis
    - Composite: (tenant_id, created_at DESC) for timeline queries
    """
    
    __tablename__ = "app_admissions_stage_history"
    
    # Primary key and tenant scope
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("app_tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Entity reference
    application_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("app_admissions_applications.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # Transition details
    from_stage: Mapped[str] = mapped_column(String(64), nullable=False)
    to_stage: Mapped[str] = mapped_column(String(64), nullable=False)
    reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    
    # Actor and action type
    actor_id: Mapped[str] = mapped_column(String(255), nullable=False)
    action_type: Mapped[str] = mapped_column(String(64), nullable=False)
    
    # Flexible metadata (review_notes, moved_by_user_email, etc.)
    metadata_json: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )
    
    # Timestamp (created_at only; append-only)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
    )
    
    # Relationships
    tenant = relationship("TenantModel", foreign_keys=[tenant_id], viewonly=True)
    application = relationship(
        "ApplicationModel",
        back_populates="stage_history",
        foreign_keys=[application_id],
    )
    
    __table_args__ = (
        Index("ix_stage_history_tenant_application", "tenant_id", "application_id"),
        Index("ix_stage_history_tenant_transition", "tenant_id", "from_stage", "to_stage"),
        Index("ix_stage_history_tenant_created_desc", "tenant_id", created_at.desc()),
    )


class ApplicationDecisionModel(Base):
    """
    Decision Entity: Final admission decision (accepted/rejected/waitlist).
    
    One-to-one with ApplicationModel.
    Explicit, traceable, with conditional acceptance support.
    
    Relationships:
    - tenant_id FK to app_tenants
    - application_id FK to ApplicationModel (UNIQUE, one decision per application)
    
    Indexes:
    - Primary: tenant_id
    - Composite: (tenant_id, decision_type) for decision type analysis
    - Composite: (tenant_id, decided_at DESC) for timeline queries
    """
    
    __tablename__ = "app_admissions_decisions"
    
    # Primary key and tenant scope
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("app_tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Entity reference (unique: one decision per application)
    application_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("app_admissions_applications.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    
    # Decision
    decision_type: Mapped[str] = mapped_column(String(64), nullable=False)
    decision_rationale: Mapped[str | None] = mapped_column(String(500), nullable=True)
    
    # Authority
    decided_by_id: Mapped[str] = mapped_column(String(255), nullable=False)
    decided_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
    )
    
    # Conditional acceptance (e.g., {gpa >= 3.5, reply_by: "2026-05-01", ...})
    conditions_json: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )
    
    # Version control
    version: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        default=1,
        server_default=text("1"),
    )
    
    # Audit trail
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
        onupdate=text("NOW()"),
    )
    
    # Relationships
    tenant = relationship("TenantModel", foreign_keys=[tenant_id], viewonly=True)
    application = relationship(
        "ApplicationModel",
        back_populates="decision",
        foreign_keys=[application_id],
    )
    
    __table_args__ = (
        Index("ix_decision_tenant_type", "tenant_id", "decision_type"),
        Index("ix_decision_tenant_decided_at_desc", "tenant_id", decided_at.desc()),
    )
