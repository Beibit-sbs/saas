# AI University Operating System — Admissions Module
## Production-Grade Backend Design

**Module:** Admissions  
**Status:** Design Phase (MVP)  
**Target:** First product module on SaaS core  
**Stack:** FastAPI, PostgreSQL + RLS, SQLAlchemy, Alembic, Python  
**Tenant Model:** Strict fail-closed, per-tenant isolation mandatory  

---

## 1. Architecture Analysis

### 1.1 Module Purpose
The Admissions module manages the complete application lifecycle from initial inquiry through acceptance/rejection. It is built as a first-class product module on top of the production SaaS core.

### 1.2 Design Principles
- **Tenant-First:** Every entity must be tenant-scoped. No implicit tenant=1 fallback.
- **Fail-Closed:** Cross-tenant access attempts result in 403. No default allow.
- **Audit-Mandatory:** All mutations (create, update, decide, reject) are audit-logged with actor, path, timestamp, metadata.
- **RBAC-Enforced:** All endpoints require explicit permission checks.
- **Workflow-Aware:** Stage transitions are explicit, traceable, and time-stamped.
- **Document-Safe:** File references are keyed; no exposed file paths in responses.

### 1.3 Core Workflow

```
Applicant (person) 
  ↓ 
Application (process, workflow state)
  ├→ ApplicationStageHistory (audit trail of state changes)
  ├→ ApplicationDocument (references: transcripts, essays, etc.)
  └→ ApplicationDecision (final outcome: accepted/rejected/waitlist)
```

### 1.4 Isolation Strategy
1. **Header-Level**: `X-Tenant-ID` header enforced; tenant_id from auth claims validated.
2. **Service-Level**: All queries filtered by tenant_id; no implicit defaults.
3. **Database-Level**: RLS policies on Admissions tables (phase 2); currently enforced in service layer.
4. **Audit-Level**: Every action logged with tenant_id for cross-tenant compliance audits.

---

## 2. Database Schema

### 2.1 Applicant Table

```sql
CREATE TABLE app_admissions_applicants (
    id BIGSERIAL PRIMARY KEY,
    tenant_id BIGINT NOT NULL REFERENCES app_tenants(id) ON DELETE CASCADE,
    
    -- Identity
    email VARCHAR(255) NOT NULL,
    first_name VARCHAR(128) NOT NULL,
    last_name VARCHAR(128) NOT NULL,
    phone VARCHAR(20),
    
    -- Application Context
    program_id BIGINT NOT NULL,  -- Links to university_programs or extern program reference
    application_year SMALLINT NOT NULL,  -- e.g., 2026
    
    -- Status
    status VARCHAR(64) NOT NULL DEFAULT 'active',  -- active|withdrawn|inactive
    
    -- Metadata
    external_id VARCHAR(128),  -- For import/integration
    metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,  -- {country, citizenship, gpa, ...}
    
    -- Audit
    created_by VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    UNIQUE(tenant_id, email, program_id, application_year),
    INDEX(tenant_id, program_id, application_year),
    INDEX(tenant_id, email)
);
```

### 2.2 Application Table

```sql
CREATE TABLE app_admissions_applications (
    id BIGSERIAL PRIMARY KEY,
    tenant_id BIGINT NOT NULL REFERENCES app_tenants(id) ON DELETE CASCADE,
    
    -- Entity References
    applicant_id BIGINT NOT NULL REFERENCES app_admissions_applicants(id) ON DELETE CASCADE,
    program_id BIGINT NOT NULL,  -- Denormalized reference
    
    -- Workflow State
    stage VARCHAR(64) NOT NULL DEFAULT 'new',  -- new|received|under_review|decision_pending|concluded
    conclusion_type VARCHAR(64),  -- accepted|rejected|waitlist|withdrawn (null until concluded)
    
    -- Timestamps
    received_at TIMESTAMP WITH TIME ZONE,  -- When application was submitted
    decision_at TIMESTAMP WITH TIME ZONE,  -- When decision was made
    
    -- Version Control
    version BIGINT NOT NULL DEFAULT 1,
    metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,  -- {gpa_on_submit, gre_score, ...}
    
    -- Audit
    created_by VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    INDEX(tenant_id, applicant_id),
    INDEX(tenant_id, program_id, stage),
    INDEX(tenant_id, stage),
    UNIQUE(tenant_id, applicant_id)  -- One active app per applicant per program/year
);
```

### 2.3 ApplicationDocument Table

```sql
CREATE TABLE app_admissions_documents (
    id BIGSERIAL PRIMARY KEY,
    tenant_id BIGINT NOT NULL REFERENCES app_tenants(id) ON DELETE CASCADE,
    
    -- Entity References
    application_id BIGINT NOT NULL REFERENCES app_admissions_applications(id) ON DELETE CASCADE,
    
    -- Document Info
    document_type VARCHAR(64) NOT NULL,  -- transcript|essay|recommendation|test_score|certificate|other
    document_key VARCHAR(255) NOT NULL,  -- Safe reference (e.g., s3://bucket/tenant_123/app_456/doc_789.pdf)
    file_name VARCHAR(255) NOT NULL,  -- Original filename
    file_size_bytes BIGINT,
    mime_type VARCHAR(128),
    
    -- Status
    status VARCHAR(64) NOT NULL DEFAULT 'received',  -- received|verified|rejected
    
    -- Metadata
    metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,  -- {upload_source: "portal|email", ...}
    
    -- Audit
    created_by VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    verified_at TIMESTAMP WITH TIME ZONE,
    verified_by VARCHAR(255),
    
    INDEX(tenant_id, application_id),
    INDEX(tenant_id, document_type)
);
```

### 2.4 ApplicationStageHistory Table

```sql
CREATE TABLE app_admissions_stage_history (
    id BIGSERIAL PRIMARY KEY,
    tenant_id BIGINT NOT NULL REFERENCES app_tenants(id) ON DELETE CASCADE,
    
    -- Entity Reference
    application_id BIGINT NOT NULL REFERENCES app_admissions_applications(id) ON DELETE CASCADE,
    
    -- Transition Details
    from_stage VARCHAR(64) NOT NULL,
    to_stage VARCHAR(64) NOT NULL,
    reason VARCHAR(255),  -- "submitted by applicant", "moved to review", etc.
    
    -- Actor & Audit
    actor_id VARCHAR(255) NOT NULL,  -- user_id from auth
    action_type VARCHAR(64) NOT NULL,  -- applicant_submit|admin_move|system_workflow|review_assessment
    
    -- Metadata
    metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,  -- {review_notes, moved_by_user_email, ...}
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    INDEX(tenant_id, application_id),
    INDEX(tenant_id, from_stage, to_stage),
    INDEX(tenant_id, created_at DESC)
);
```

### 2.5 ApplicationDecision Table

```sql
CREATE TABLE app_admissions_decisions (
    id BIGSERIAL PRIMARY KEY,
    tenant_id BIGINT NOT NULL REFERENCES app_tenants(id) ON DELETE CASCADE,
    
    -- Entity Reference
    application_id BIGINT NOT NULL UNIQUE REFERENCES app_admissions_applications(id) ON DELETE CASCADE,
    
    -- Decision
    decision_type VARCHAR(64) NOT NULL,  -- accepted|rejected|waitlist
    decision_rationale VARCHAR(500),
    
    -- Authority
    decided_by_id VARCHAR(255) NOT NULL,  -- user_id of decision maker
    decided_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    -- Conditional Acceptance
    conditions_json JSONB NOT NULL DEFAULT '{}'::jsonb,  -- {gpa >= 3.5, reply_by: "2026-05-01", ...}
    
    -- Version Control
    version BIGINT NOT NULL DEFAULT 1,
    
    -- Audit
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    INDEX(tenant_id, decision_type),
    INDEX(tenant_id, decided_at DESC)
);
```

---

## 3. SQLAlchemy Models

### 3.1 Models File Structure
```
backend/app/modules/admissions/
├── models.py              (SQLAlchemy ORM models)
├── schemas.py             (Pydantic request/response DTOs)
├── service.py             (Business logic, queries)
├── router.py              (FastAPI endpoints)
├── __init__.py
└── tests/
    ├── test_models.py
    ├── test_service.py
    ├── test_router.py
    └── test_isolation.py

backend/alembic/versions/
└── XXXXXX_create_admissions_tables.py
```

### 3.2 Models Skeleton (models.py)

```python
from datetime import datetime
from sqlalchemy import BigInteger, DateTime, ForeignKey, String, SmallInteger, Text, JSONB, Index, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class ApplicantModel(Base):
    __tablename__ = "app_admissions_applicants"
    
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("app_tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    first_name: Mapped[str] = mapped_column(String(128), nullable=False)
    last_name: Mapped[str] = mapped_column(String(128), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(20))
    
    program_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    application_year: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    
    status: Mapped[str] = mapped_column(String(64), nullable=False, default="active")
    external_id: Mapped[str | None] = mapped_column(String(128))
    metadata_json: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    
    created_by: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("NOW()"))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("NOW()"))
    
    tenant = relationship("TenantModel", foreign_keys=[tenant_id])
    applications = relationship("ApplicationModel", back_populates="applicant", cascade="all, delete-orphan")
    
    __table_args__ = (
        UniqueConstraint("tenant_id", "email", "program_id", "application_year", name="ux_applicant_unique"),
        Index("ix_applicant_tenant_program_year", "tenant_id", "program_id", "application_year"),
        Index("ix_applicant_tenant_email", "tenant_id", "email"),
    )


class ApplicationModel(Base):
    __tablename__ = "app_admissions_applications"
    
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("app_tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    
    applicant_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("app_admissions_applicants.id", ondelete="CASCADE"), nullable=False)
    program_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    
    stage: Mapped[str] = mapped_column(String(64), nullable=False, default="new")
    conclusion_type: Mapped[str | None] = mapped_column(String(64))
    
    received_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    decision_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    
    version: Mapped[int] = mapped_column(BigInteger, nullable=False, default=1)
    metadata_json: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    
    created_by: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("NOW()"))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("NOW()"))
    
    tenant = relationship("TenantModel", foreign_keys=[tenant_id])
    applicant = relationship("ApplicantModel", back_populates="applications", foreign_keys=[applicant_id])
    documents = relationship("ApplicationDocumentModel", back_populates="application", cascade="all, delete-orphan")
    stage_history = relationship("ApplicationStageHistoryModel", back_populates="application", cascade="all, delete-orphan")
    decision = relationship("ApplicationDecisionModel", back_populates="application", uselist=False, cascade="all, delete-orphan")
    
    __table_args__ = (
        UniqueConstraint("tenant_id", "applicant_id", name="ux_application_unique"),
        Index("ix_application_tenant_applicant", "tenant_id", "applicant_id"),
        Index("ix_application_tenant_program_stage", "tenant_id", "program_id", "stage"),
        Index("ix_application_tenant_stage", "tenant_id", "stage"),
    )


class ApplicationDocumentModel(Base):
    __tablename__ = "app_admissions_documents"
    
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("app_tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    
    application_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("app_admissions_applications.id", ondelete="CASCADE"), nullable=False)
    
    document_type: Mapped[str] = mapped_column(String(64), nullable=False)
    document_key: Mapped[str] = mapped_column(String(255), nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_size_bytes: Mapped[int | None] = mapped_column(BigInteger)
    mime_type: Mapped[str | None] = mapped_column(String(128))
    
    status: Mapped[str] = mapped_column(String(64), nullable=False, default="received")
    metadata_json: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    
    created_by: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("NOW()"))
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    verified_by: Mapped[str | None] = mapped_column(String(255))
    
    tenant = relationship("TenantModel", foreign_keys=[tenant_id])
    application = relationship("ApplicationModel", back_populates="documents", foreign_keys=[application_id])
    
    __table_args__ = (
        Index("ix_document_tenant_application", "tenant_id", "application_id"),
        Index("ix_document_tenant_type", "tenant_id", "document_type"),
    )


class ApplicationStageHistoryModel(Base):
    __tablename__ = "app_admissions_stage_history"
    
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("app_tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    
    application_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("app_admissions_applications.id", ondelete="CASCADE"), nullable=False)
    
    from_stage: Mapped[str] = mapped_column(String(64), nullable=False)
    to_stage: Mapped[str] = mapped_column(String(64), nullable=False)
    reason: Mapped[str | None] = mapped_column(String(255))
    
    actor_id: Mapped[str] = mapped_column(String(255), nullable=False)
    action_type: Mapped[str] = mapped_column(String(64), nullable=False)
    
    metadata_json: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("NOW()"))
    
    tenant = relationship("TenantModel", foreign_keys=[tenant_id])
    application = relationship("ApplicationModel", back_populates="stage_history", foreign_keys=[application_id])
    
    __table_args__ = (
        Index("ix_stage_history_tenant_application", "tenant_id", "application_id"),
        Index("ix_stage_history_tenant_transition", "tenant_id", "from_stage", "to_stage"),
        Index("ix_stage_history_tenant_created", "tenant_id", "created_at", "DESC"),
    )


class ApplicationDecisionModel(Base):
    __tablename__ = "app_admissions_decisions"
    
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("app_tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    
    application_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("app_admissions_applications.id", ondelete="CASCADE"), nullable=False, unique=True)
    
    decision_type: Mapped[str] = mapped_column(String(64), nullable=False)
    decision_rationale: Mapped[str | None] = mapped_column(String(500))
    
    decided_by_id: Mapped[str] = mapped_column(String(255), nullable=False)
    decided_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("NOW()"))
    
    conditions_json: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    
    version: Mapped[int] = mapped_column(BigInteger, nullable=False, default=1)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("NOW()"))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("NOW()"))
    
    tenant = relationship("TenantModel", foreign_keys=[tenant_id])
    application = relationship("ApplicationModel", back_populates="decision", foreign_keys=[application_id])
    
    __table_args__ = (
        Index("ix_decision_tenant_type", "tenant_id", "decision_type"),
        Index("ix_decision_tenant_decided_at", "tenant_id", "decided_at", "DESC"),
    )
```

---

## 4. Alembic Migration Plan

### 4.1 Migration Strategy
Single comprehensive migration file that creates all five tables with proper indexing, constraints, and RLS placeholders.

### 4.2 Migration File Structure (XXXXXX_create_admissions_tables.py)

```python
"""Create Admissions module tables with tenant isolation.

Revision ID: <auto-generated>
Revises: <latest>
Create Date: <auto-generated>
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


def upgrade() -> None:
    """Create Admissions tables."""
    
    # -- Applicant Table
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
        sa.Column("status", sa.String(64), nullable=False, server_default="active"),
        sa.Column("external_id", sa.String(128), nullable=True),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("created_by", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.ForeignKeyConstraint(["tenant_id"], ["app_tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "email", "program_id", "application_year", name="ux_applicant_unique"),
    )
    op.create_index("ix_applicant_tenant_program_year", "app_admissions_applicants", ["tenant_id", "program_id", "application_year"])
    op.create_index("ix_applicant_tenant_email", "app_admissions_applicants", ["tenant_id", "email"])
    op.create_index("ix_applicant_tenant_id", "app_admissions_applicants", ["tenant_id"])
    
    # -- Application Table
    op.create_table(
        "app_admissions_applications",
        sa.Column("id", postgresql.BIGSERIAL(), autoincrement=True, nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("applicant_id", sa.BigInteger(), nullable=False),
        sa.Column("program_id", sa.BigInteger(), nullable=False),
        sa.Column("stage", sa.String(64), nullable=False, server_default="new"),
        sa.Column("conclusion_type", sa.String(64), nullable=True),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("decision_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version", sa.BigInteger(), nullable=False, server_default="1"),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("created_by", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.ForeignKeyConstraint(["tenant_id"], ["app_tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["applicant_id"], ["app_admissions_applicants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "applicant_id", name="ux_application_unique"),
    )
    op.create_index("ix_application_tenant_applicant", "app_admissions_applications", ["tenant_id", "applicant_id"])
    op.create_index("ix_application_tenant_program_stage", "app_admissions_applications", ["tenant_id", "program_id", "stage"])
    op.create_index("ix_application_tenant_stage", "app_admissions_applications", ["tenant_id", "stage"])
    op.create_index("ix_application_tenant_id", "app_admissions_applications", ["tenant_id"])
    
    # -- Application Document Table
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
        sa.Column("status", sa.String(64), nullable=False, server_default="received"),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("created_by", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("verified_by", sa.String(255), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["app_tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["application_id"], ["app_admissions_applications.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_document_tenant_application", "app_admissions_documents", ["tenant_id", "application_id"])
    op.create_index("ix_document_tenant_type", "app_admissions_documents", ["tenant_id", "document_type"])
    op.create_index("ix_document_tenant_id", "app_admissions_documents", ["tenant_id"])
    
    # -- Application Stage History Table
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
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.ForeignKeyConstraint(["tenant_id"], ["app_tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["application_id"], ["app_admissions_applications.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_stage_history_tenant_application", "app_admissions_stage_history", ["tenant_id", "application_id"])
    op.create_index("ix_stage_history_tenant_transition", "app_admissions_stage_history", ["tenant_id", "from_stage", "to_stage"])
    op.create_index("ix_stage_history_tenant_created", "app_admissions_stage_history", ["tenant_id", "created_at", sa.desc("created_at")])
    op.create_index("ix_stage_history_tenant_id", "app_admissions_stage_history", ["tenant_id"])
    
    # -- Application Decision Table
    op.create_table(
        "app_admissions_decisions",
        sa.Column("id", postgresql.BIGSERIAL(), autoincrement=True, nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("application_id", sa.BigInteger(), nullable=False, unique=True),
        sa.Column("decision_type", sa.String(64), nullable=False),
        sa.Column("decision_rationale", sa.String(500), nullable=True),
        sa.Column("decided_by_id", sa.String(255), nullable=False),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("conditions_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("version", sa.BigInteger(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.ForeignKeyConstraint(["tenant_id"], ["app_tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["application_id"], ["app_admissions_applications.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_decision_tenant_type", "app_admissions_decisions", ["tenant_id", "decision_type"])
    op.create_index("ix_decision_tenant_decided_at", "app_admissions_decisions", ["tenant_id", "decided_at", sa.desc("decided_at")])
    op.create_index("ix_decision_tenant_id", "app_admissions_decisions", ["tenant_id"])


def downgrade() -> None:
    """Drop Admissions tables."""
    op.drop_table("app_admissions_decisions")
    op.drop_table("app_admissions_stage_history")
    op.drop_table("app_admissions_documents")
    op.drop_table("app_admissions_applications")
    op.drop_table("app_admissions_applicants")
```

---

## 5. Pydantic Schemas

### 5.1 Schemas File (schemas.py)

```python
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr


# -- APPLICANT SCHEMAS

class ApplicantBase(BaseModel):
    email: EmailStr = Field(min_length=3, max_length=255)
    first_name: str = Field(min_length=1, max_length=128)
    last_name: str = Field(min_length=1, max_length=128)
    phone: str | None = Field(default=None, min_length=5, max_length=20)
    program_id: int = Field(gt=0)
    application_year: int = Field(ge=2000, le=2100)
    status: str = Field(default="active", min_length=1, max_length=64)
    external_id: str | None = Field(default=None, min_length=1, max_length=128)
    metadata_json: dict = Field(default_factory=dict)


class ApplicantCreatePayload(ApplicantBase):
    pass


class ApplicantUpdatePayload(BaseModel):
    first_name: str | None = Field(default=None, min_length=1, max_length=128)
    last_name: str | None = Field(default=None, min_length=1, max_length=128)
    phone: str | None = Field(default=None, min_length=5, max_length=20)
    status: str | None = Field(default=None, min_length=1, max_length=64)
    metadata_json: dict | None = Field(default=None)


class ApplicantResponse(ApplicantBase):
    id: int
    created_by: str
    created_at: str
    updated_at: str


class ApplicantListResponse(BaseModel):
    applicants: list[ApplicantResponse]


class ApplicantItemResponse(BaseModel):
    applicant: ApplicantResponse


# -- APPLICATION SCHEMAS

class ApplicationBase(BaseModel):
    applicant_id: int = Field(gt=0)
    program_id: int = Field(gt=0)
    stage: str = Field(default="new", min_length=1, max_length=64)
    conclusion_type: str | None = Field(default=None, min_length=1, max_length=64)
    metadata_json: dict = Field(default_factory=dict)


class ApplicationCreatePayload(ApplicationBase):
    pass


class ApplicationUpdatePayload(BaseModel):
    stage: str | None = Field(default=None, min_length=1, max_length=64)
    metadata_json: dict | None = Field(default=None)


class ApplicationResponse(ApplicationBase):
    id: int
    stage: str
    conclusion_type: str | None
    received_at: str | None
    decision_at: str | None
    version: int
    created_by: str
    created_at: str
    updated_at: str


class ApplicationListResponse(BaseModel):
    applications: list[ApplicationResponse]


class ApplicationItemResponse(BaseModel):
    application: ApplicationResponse


# -- DOCUMENT SCHEMAS

class DocumentBase(BaseModel):
    application_id: int = Field(gt=0)
    document_type: str = Field(min_length=1, max_length=64)
    file_name: str = Field(min_length=1, max_length=255)
    file_size_bytes: int | None = Field(default=None, ge=0)
    mime_type: str | None = Field(default=None, min_length=1, max_length=128)
    status: str = Field(default="received", min_length=1, max_length=64)
    metadata_json: dict = Field(default_factory=dict)


class DocumentUploadPayload(BaseModel):
    application_id: int = Field(gt=0)
    document_type: str = Field(min_length=1, max_length=64)
    file_name: str = Field(min_length=1, max_length=255)
    file_size_bytes: int = Field(ge=100, le=104857600)  # 100 bytes to 100 MB
    mime_type: str = Field(min_length=1, max_length=128)


class DocumentVerifyPayload(BaseModel):
    status: str = Field(min_length=1, max_length=64)  # verified|rejected


class DocumentResponse(DocumentBase):
    id: int
    document_key: str
    created_by: str
    created_at: str
    verified_at: str | None
    verified_by: str | None


class DocumentListResponse(BaseModel):
    documents: list[DocumentResponse]


class DocumentItemResponse(BaseModel):
    document: DocumentResponse


# -- STAGE HISTORY SCHEMAS

class StageHistoryResponse(BaseModel):
    id: int
    from_stage: str
    to_stage: str
    reason: str | None
    actor_id: str
    action_type: str
    metadata_json: dict
    created_at: str


class StageHistoryListResponse(BaseModel):
    stage_history: list[StageHistoryResponse]


# -- DECISION SCHEMAS

class DecisionCreatePayload(BaseModel):
    application_id: int = Field(gt=0)
    decision_type: str = Field(min_length=1, max_length=64)  # accepted|rejected|waitlist
    decision_rationale: str | None = Field(default=None, min_length=1, max_length=500)
    conditions_json: dict = Field(default_factory=dict)


class DecisionResponse(BaseModel):
    id: int
    application_id: int
    decision_type: str
    decision_rationale: str | None
    decided_by_id: str
    decided_at: str
    conditions_json: dict
    version: int
    created_at: str
    updated_at: str


class DecisionItemResponse(BaseModel):
    decision: DecisionResponse
```

---

## 6. Service Layer Design

### 6.1 Service File Structure (service.py) — Methods Summary

```python
"""
Admissions Service Layer
- All methods enforce tenant isolation at service level
- All mutations are audit-logged externally
- No exceptions for cross-tenant calls (service returns None/ValueError)
"""

# APPLICANT SERVICE
def create_applicant(payload: dict, tenant_id: int, created_by: str) -> dict:
    """Create applicant for tenant. Forces tenant_id. Must audit externally."""
    
def get_applicant(applicant_id: int, tenant_id: int) -> dict | None:
    """Get applicant by ID, scope by tenant. Returns None if not found/wrong tenant."""
    
def list_applicants(tenant_id: int, program_id: int | None = None, year: int | None = None) -> list[dict]:
    """List applicants scoped by tenant. Optional filters."""
    
def update_applicant(applicant_id: int, payload: dict, tenant_id: int) -> dict:
    """Update applicant. Raises ValueError if not found/wrong tenant."""

# APPLICATION SERVICE
def create_application(applicant_id: int, program_id: int, tenant_id: int, created_by: str) -> dict:
    """Create application. Validates applicant exists in same tenant."""
    
def get_application(application_id: int, tenant_id: int) -> dict | None:
    """Get application by ID, scoped by tenant."""
    
def list_applications(tenant_id: int, program_id: int | None = None, stage: str | None = None, limit: int = 100) -> list[dict]:
    """List applications scoped by tenant with optional filters."""
    
def transition_application_stage(application_id: int, to_stage: str, tenant_id: int, actor_id: str, reason: str | None = None) -> dict:
    """Explicit stage transition. Updates stage, records history."""

# DOCUMENT SERVICE
def upload_document_reference(application_id: int, doc_type: str, file_name: str, document_key: str, file_size: int, mime_type: str, tenant_id: int, created_by: str) -> dict:
    """Register document reference. document_key is safe reference."""
    
def get_document(doc_id: int, tenant_id: int) -> dict | None:
    """Get document metadata (key, not content)."""
    
def list_documents(application_id: int, tenant_id: int) -> list[dict]:
    """List documents for application, scoped by tenant."""
    
def verify_document(doc_id: int, status: str, tenant_id: int, verified_by: str) -> dict:
    """Mark document as verified or rejected. Updates timestamp."""

# DECISION SERVICE
def make_decision(application_id: int, decision_type: str, tenant_id: int, decided_by_id: str, rationale: str | None = None, conditions: dict | None = None) -> dict:
    """Create decision. Validates application in same tenant. Updates application stage to 'concluded'."""
    
def get_decision(decision_id: int, tenant_id: int) -> dict | None:
    """Get decision by ID, scoped by tenant."""
    
def get_decision_by_application(application_id: int, tenant_id: int) -> dict | None:
    """Get decision for application."""

# QUERY HELPERS
def get_stage_history(application_id: int, tenant_id: int) -> list[dict]:
    """Full workflow history for application."""
    
def count_applications_by_stage(tenant_id: int) -> dict[str, int]:
    """Stats: {stage: count, ...}"""
```

### 6.2 Key Service Principles
- Queries explicitly filter by `tenant_id`.
- No implicit `tenant_id=1` defaults.
- Mutation methods accept `tenant_id` parameter; all ForeignKey values validated to be in same tenant.
- Exception handling: ValueError for not-found or validation failures.
- Audit logging delegated to router layer.

---

## 7. API Endpoints

### 7.1 Endpoint Structure (router.py)

```
PREFIX: /api/admin/admissions

-- APPLICANTS
POST   /applicants                              → create_applicant
GET    /applicants                              → list_applicants (filters: program_id, year)
GET    /applicants/{applicant_id}               → get_applicant
PUT    /applicants/{applicant_id}               → update_applicant

-- APPLICATIONS
POST   /applications                            → create_application
GET    /applications                            → list_applications (filters: program_id, stage)
GET    /applications/{application_id}           → get_application
PUT    /applications/{application_id}/stage     → transition_stage (move to next stage)

-- DOCUMENTS
POST   /applications/{application_id}/documents → upload_document_reference
GET    /applications/{application_id}/documents → list_documents
GET    /documents/{document_id}                 → get_document
PUT    /documents/{document_id}/verify          → verify_document

-- DECISIONS
POST   /applications/{application_id}/decision  → make_decision
GET    /applications/{application_id}/decision  → get_decision
GET    /decisions                               → list_decisions (filters: decision_type)

-- WORKFLOW
GET    /applications/{application_id}/history   → get_stage_history
GET    /applications/stats                      → application_stats_by_stage (admissions.applications.stats permission)
```

### 7.2 Endpoint Skeleton (router.py)

```python
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Request

from app.core.tenant import get_current_tenant
from app.modules.audit.service import log_admin_action
from app.modules.rbac.security import get_actor, permission_dependency
from app.modules.admissions.schemas import (
    ApplicantCreatePayload, ApplicantResponse, ApplicantListResponse, ApplicantItemResponse,
    ApplicationCreatePayload, ApplicationResponse, ApplicationListResponse, ApplicationItemResponse,
    DocumentUploadPayload, DocumentResponse, DocumentListResponse, DocumentItemResponse,
    DecisionCreatePayload, DecisionResponse, DecisionItemResponse,
    StageHistoryListResponse,
)
from app.modules.admissions import service

router = APIRouter(prefix="/api/admin/admissions", tags=["admissions"])


# -- APPLICANTS

@router.post("/applicants", response_model=ApplicantItemResponse)
def create_applicant_endpoint(
    payload: ApplicantCreatePayload,
    request: Request,
    actor: Annotated[str, Depends(get_actor)],
    _: Annotated[None, Depends(permission_dependency("admissions.applicants.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> ApplicantItemResponse:
    tenant_id = int(tenant["id"])
    try:
        applicant = service.create_applicant(payload.model_dump(), tenant_id, actor)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    
    log_admin_action(
        actor=actor,
        tenant_id=tenant_id,
        action="admissions.applicant.create",
        path=str(request.url.path),
        client_ip=request.client.host if request.client else "unknown",
        correlation_id=getattr(request.state, "request_id", None),
        entity="app_admissions_applicants",
        result="success",
        metadata={"id": applicant["id"], "email": applicant["email"]},
    )
    return {"applicant": applicant}


@router.get("/applicants", response_model=ApplicantListResponse)
def list_applicants_endpoint(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admissions.applicants.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
    program_id: int | None = None,
    application_year: int | None = None,
) -> ApplicantListResponse:
    tenant_id = int(tenant["id"])
    applicants = service.list_applicants(tenant_id, program_id, application_year)
    return {"applicants": applicants}


@router.get("/applicants/{applicant_id}", response_model=ApplicantItemResponse)
def get_applicant_endpoint(
    applicant_id: int,
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admissions.applicants.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> ApplicantItemResponse:
    tenant_id = int(tenant["id"])
    applicant = service.get_applicant(applicant_id, tenant_id)
    if applicant is None:
        raise HTTPException(status_code=404, detail="applicant not found")
    return {"applicant": applicant}


@router.put("/applicants/{applicant_id}", response_model=ApplicantItemResponse)
def update_applicant_endpoint(
    applicant_id: int,
    payload: ApplicantUpdatePayload,
    request: Request,
    actor: Annotated[str, Depends(get_actor)],
    _: Annotated[None, Depends(permission_dependency("admissions.applicants.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> ApplicantItemResponse:
    tenant_id = int(tenant["id"])
    try:
        applicant = service.update_applicant(applicant_id, payload.model_dump(exclude_none=True), tenant_id)
    except ValueError as exc:
        detail = str(exc)
        status = 404 if "not found" in detail else 400
        raise HTTPException(status_code=status, detail=detail)
    
    log_admin_action(
        actor=actor,
        tenant_id=tenant_id,
        action="admissions.applicant.update",
        path=str(request.url.path),
        client_ip=request.client.host if request.client else "unknown",
        correlation_id=getattr(request.state, "request_id", None),
        entity="app_admissions_applicants",
        result="success",
        metadata={"id": applicant["id"], "email": applicant["email"]},
    )
    return {"applicant": applicant}


# -- APPLICATIONS

@router.post("/applications", response_model=ApplicationItemResponse)
def create_application_endpoint(
    payload: ApplicationCreatePayload,
    request: Request,
    actor: Annotated[str, Depends(get_actor)],
    _: Annotated[None, Depends(permission_dependency("admissions.applications.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> ApplicationItemResponse:
    tenant_id = int(tenant["id"])
    try:
        application = service.create_application(payload.applicant_id, payload.program_id, tenant_id, actor)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    
    log_admin_action(
        actor=actor,
        tenant_id=tenant_id,
        action="admissions.application.create",
        path=str(request.url.path),
        client_ip=request.client.host if request.client else "unknown",
        correlation_id=getattr(request.state, "request_id", None),
        entity="app_admissions_applications",
        result="success",
        metadata={"id": application["id"], "applicant_id": application["applicant_id"]},
    )
    return {"application": application}


@router.get("/applications", response_model=ApplicationListResponse)
def list_applications_endpoint(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admissions.applications.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
    program_id: int | None = None,
    stage: str | None = None,
) -> ApplicationListResponse:
    tenant_id = int(tenant["id"])
    applications = service.list_applications(tenant_id, program_id, stage)
    return {"applications": applications}


@router.put("/applications/{application_id}/stage")
def transition_stage_endpoint(
    application_id: int,
    to_stage: str,
    request: Request,
    actor: Annotated[str, Depends(get_actor)],
    _: Annotated[None, Depends(permission_dependency("admissions.applications.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> ApplicationItemResponse:
    tenant_id = int(tenant["id"])
    try:
        application = service.transition_application_stage(application_id, to_stage, tenant_id, actor)
    except ValueError as exc:
        detail = str(exc)
        status = 404 if "not found" in detail else 400
        raise HTTPException(status_code=status, detail=detail)
    
    log_admin_action(
        actor=actor,
        tenant_id=tenant_id,
        action="admissions.application.stage_transition",
        path=str(request.url.path),
        client_ip=request.client.host if request.client else "unknown",
        correlation_id=getattr(request.state, "request_id", None),
        entity="app_admissions_applications",
        result="success",
        metadata={"id": application["id"], "stage": application["stage"]},
    )
    return {"application": application}


# -- DECISIONS

@router.post("/applications/{application_id}/decision", response_model=DecisionItemResponse)
def make_decision_endpoint(
    application_id: int,
    payload: DecisionCreatePayload,
    request: Request,
    actor: Annotated[str, Depends(get_actor)],
    _: Annotated[None, Depends(permission_dependency("admissions.applications.decide"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> DecisionItemResponse:
    tenant_id = int(tenant["id"])
    try:
        decision = service.make_decision(
            application_id,
            payload.decision_type,
            tenant_id,
            actor,
            payload.decision_rationale,
            payload.conditions_json,
        )
    except ValueError as exc:
        detail = str(exc)
        status = 404 if "not found" in detail else 400
        raise HTTPException(status_code=status, detail=detail)
    
    log_admin_action(
        actor=actor,
        tenant_id=tenant_id,
        action="admissions.application.decide",
        path=str(request.url.path),
        client_ip=request.client.host if request.client else "unknown",
        correlation_id=getattr(request.state, "request_id", None),
        entity="app_admissions_decisions",
        result="success",
        metadata={"id": decision["id"], "decision_type": decision["decision_type"], "application_id": application_id},
    )
    return {"decision": decision}


# -- STAGE HISTORY

@router.get("/applications/{application_id}/history", response_model=StageHistoryListResponse)
def get_stage_history_endpoint(
    application_id: int,
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admissions.applications.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> StageHistoryListResponse:
    tenant_id = int(tenant["id"])
    # Validate application is in tenant
    app = service.get_application(application_id, tenant_id)
    if app is None:
        raise HTTPException(status_code=404, detail="application not found")
    
    history = service.get_stage_history(application_id, tenant_id)
    return {"stage_history": history}
```

---

## 8. RBAC Requirements

### 8.1 Permission Matrix

| Permission | Role | Scope | Rationale |
|-----------|------|-------|-----------|
| `admissions.applicants.read` | admissions_staff, admin | tenant | View applicant records |
| `admissions.applicants.write` | admissions_staff, admin | tenant | Create/update applicants |
| `admissions.applications.read` | admissions_staff, admin, auditor | tenant | View applications |
| `admissions.applications.write` | admissions_staff, admin | tenant | Create/update applications, transition stages |
| `admissions.applications.decide` | admissions_officer, admin | tenant | Make final decisions (accept/reject/waitlist) |
| `admissions.documents.upload` | admissions_staff, admin | tenant | Upload/reference documents |
| `admissions.documents.verify` | admissions_officer, admin | tenant | Verify documents |
| `admissions.documents.download` | admissions_staff, admin, auditor | tenant | Access document content |
| `admissions.applications.stats` | admin, auditor | tenant | View application statistics |

### 8.2 Role Definitions (to be added to RBAC service)

```python
ADMISSION_ROLES = {
    "admissions_staff": {
        "admissions.applicants.read",
        "admissions.applicants.write",
        "admissions.applications.read",
        "admissions.applications.write",
        "admissions.documents.upload",
        "admissions.documents.download",
    },
    "admissions_officer": {
        "admissions.applicants.read",
        "admissions.applications.read",
        "admissions.applications.write",  # Can transition stages
        "admissions.applications.decide",  # Can make decisions
        "admissions.documents.download",
        "admissions.documents.verify",
    },
}
```

---

## 9. Audit Events

### 9.1 Audit Event Types

All audit events include: `actor`, `action`, `entity`, `path`, `client_ip`, `correlation_id`, `tenant_id`, `metadata`

| Action | Entity | Metadata | Trigger |
|--------|--------|----------|---------|
| `admissions.applicant.create` | `app_admissions_applicants` | `{id, email, program_id, year}` | Create applicant |
| `admissions.applicant.update` | `app_admissions_applicants` | `{id, email, changed_fields}` | Update applicant  |
| `admissions.application.create` | `app_admissions_applications` | `{id, applicant_id, program_id}` | Create application |
| `admissions.application.stage_transition` | `app_admissions_applications` | `{id, from_stage, to_stage, reason}` | Transition stage |
| `admissions.application.decide` | `app_admissions_decisions` | `{id, decision_type, conditions}` | Make decision |
| `admissions.document.upload` | `app_admissions_documents` | `{id, document_type, file_name}` | Reference document |
| `admissions.document.verify` | `app_admissions_documents` | `{id, status}` | Verify document |

### 9.2 Audit Integration

All mutations call `log_admin_action()` immediately after successful operation:

```python
log_admin_action(
    actor=actor,
    tenant_id=tenant_id,
    action="admissions.application.decide",
    path=str(request.url.path),
    client_ip=request.client.host or "unknown",
    correlation_id=getattr(request.state, "request_id", None),
    entity="app_admissions_decisions",
    result="success",  # or "failure"
    metadata={...},
)
```

---

## 10. Implementation Order

### Phase 1: Schema & Models (Week 1)
1. Create Alembic migration file: `create_admissions_tables.py`
2. Run migration: `alembic upgrade head`
3. Create `backend/app/modules/admissions/models.py` with all 5 SQLAlchemy models
4. Create `backend/app/modules/admissions/__init__.py`
5. Test: model imports, relationships resolve correctly

### Phase 2: Schemas & Service (Week 1-2)
6. Create `backend/app/modules/admissions/schemas.py` with all Pydantic DTOs
7. Create `backend/app/modules/admissions/service.py` with all service methods
   - Start with CRUD: applicants, applications
   - Add document reference methods
   - Add decision methods
   - All methods enforce tenant isolation
8. Test: service layer isolation tests

### Phase 3: API Routes (Week 2)
9. Create `backend/app/modules/admissions/router.py` with all endpoints
   - Register router in `backend/app/main.py`: `app.include_router(admissions_router)`
   - Add permission checks using `permission_dependency`
   - Add audit logging after each mutation
10. Test: endpoint isolation tests, permission checks

### Phase 4: Integration & Workflow (Week 2-3)
11. Add stage transition logic + stage history recording
12. Add decision logic + application stage update
13. Add document verification + status tracking
14. Test: full workflow (submit → review → decide → conclude)

### Phase 5: Testing (Week 3)
15. Unit tests: service layer (tenant isolation, validation)
16. Integration tests: routes + RBAC + audit logging
17. Contract tests: cross-tenant fail-closed checks
18. Load tests (optional): bulk applicant/application creation

### Phase 6: Deployment (Week 4)
19. Code review, lint, security audit
20. Deploy migration to staging, test schema
21. Deploy code to staging, run integration tests
22. Deploy to production with canary monitoring

---

## 11. Key Non-Functional Requirements

- **Tenant Isolation**: Fail-closed; all queries filter by tenant_id; no implicit defaults.
- **Auditability**: Every mutation logged with actor, timestamp, outcome.
- **Performance**: All queries indexed by tenant_id; stage/program queries use composite indexes.
- **Scalability**: Partitioning ready (future: by tenant_id + created_at).
- **Data Consistency**: Foreign keys enforce referential integrity; stage transitions validated.
- **Error Handling**: Graceful 400/404/403 responses; no internal exception leakage.

---

## 12. Summary

This design provides a **production-safe, tenant-aware, audit-logged Admissions module** that fits seamlessly into the existing SaaS core. Every entity is tenant-scoped, every mutation is audit-logged, and RBAC is enforced at all access points. The implementation plan is phased to allow parallel work and incremental testing.

**Ready to implement Phase 1 (schema & models)?**
