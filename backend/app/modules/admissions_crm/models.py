"""Admissions CRM Batch 1 SQLAlchemy models."""

from __future__ import annotations

from sqlalchemy import BigInteger, Boolean, DateTime, Index, String, Text, text as sa_text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, declarative_mixin, mapped_column

from app.core.db import Base


MODULE_NAME = "admissions_crm"
API_PREFIX = "/api/admin/admissions-crm"
RUNTIME_MODE = "HUMAN_REVIEW_DECISION_SUPPORT_ONLY"
EXPECTED_TABLE_COUNT = 12
EXPECTED_ROUTE_COUNT = 12
EXPECTED_PERMISSION_COUNT = 6
TABLE_PREFIX = "acrm_"
CONTRACT_VERSION = "A-045.2.RUNTIME.BATCH1"

FAKE_METRICS = False
PROVIDER_LIVE_ENABLED = False
AUTONOMOUS_DECISION_ENABLED = False
HIDDEN_SCORE_PRESENT = False
HUMAN_REVIEW_REQUIRED = True

TABLE_NAMES = {
    "acrm_leads",
    "acrm_lead_status_history",
    "acrm_lead_notes",
    "acrm_lead_tags",
    "acrm_applicants",
    "acrm_applicant_notes",
    "acrm_applications",
    "acrm_application_status_history",
    "acrm_workflow_transition_events",
    "acrm_audit_events",
    "acrm_counselor_assignments",
    "acrm_assignment_history",
}


def _table_args(table_name: str):
    return (
        Index(f"ix_{table_name}_tenant_id", "tenant_id"),
        Index(f"ix_{table_name}_tenant_status", "tenant_id", "status"),
    )


@declarative_mixin
class AcrmCommonMixin:
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    status: Mapped[str] = mapped_column(String(64), nullable=False, server_default=sa_text("'draft'"))
    human_review_required: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa_text("true"))
    fake_metrics: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa_text("false"))
    provider_live_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa_text("false"))
    autonomous_decision_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa_text("false"))
    hidden_score_present: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa_text("false"))
    metadata_json: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=sa_text("'{}'::jsonb"))
    created_by_user_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    updated_by_user_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=sa_text("NOW()"))
    updated_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=sa_text("NOW()"))


class Lead(AcrmCommonMixin, Base):
    __tablename__ = "acrm_leads"
    __table_args__ = _table_args(__tablename__)

    lead_ref: Mapped[str] = mapped_column(String(64), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(64), nullable=True)
    source_channel: Mapped[str] = mapped_column(String(64), nullable=False, server_default=sa_text("'direct'"))


class LeadStatusHistory(Base):
    __tablename__ = "acrm_lead_status_history"
    __table_args__ = (
        Index("ix_acrm_lead_status_history_tenant_id", "tenant_id"),
        Index("ix_acrm_lead_status_history_tenant_lead", "tenant_id", "lead_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    lead_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    from_status: Mapped[str | None] = mapped_column(String(64), nullable=True)
    to_status: Mapped[str] = mapped_column(String(64), nullable=False)
    changed_by_user_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=sa_text("NOW()"))


class LeadNote(Base):
    __tablename__ = "acrm_lead_notes"
    __table_args__ = (
        Index("ix_acrm_lead_notes_tenant_id", "tenant_id"),
        Index("ix_acrm_lead_notes_tenant_lead", "tenant_id", "lead_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    lead_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    note: Mapped[str] = mapped_column(Text, nullable=False)
    actor_user_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=sa_text("NOW()"))


class LeadTag(Base):
    __tablename__ = "acrm_lead_tags"
    __table_args__ = (
        Index("ix_acrm_lead_tags_tenant_id", "tenant_id"),
        Index("ix_acrm_lead_tags_tenant_lead", "tenant_id", "lead_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    lead_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    tag: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=sa_text("NOW()"))


class Applicant(AcrmCommonMixin, Base):
    __tablename__ = "acrm_applicants"
    __table_args__ = _table_args(__tablename__)

    lead_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    applicant_ref: Mapped[str] = mapped_column(String(64), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)


class ApplicantNote(Base):
    __tablename__ = "acrm_applicant_notes"
    __table_args__ = (
        Index("ix_acrm_applicant_notes_tenant_id", "tenant_id"),
        Index("ix_acrm_applicant_notes_tenant_applicant", "tenant_id", "applicant_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    applicant_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    note: Mapped[str] = mapped_column(Text, nullable=False)
    actor_user_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=sa_text("NOW()"))


class Application(AcrmCommonMixin, Base):
    __tablename__ = "acrm_applications"
    __table_args__ = _table_args(__tablename__)

    applicant_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    application_ref: Mapped[str] = mapped_column(String(64), nullable=False)
    program_code: Mapped[str] = mapped_column(String(64), nullable=False)
    intake_term: Mapped[str] = mapped_column(String(64), nullable=False)


class ApplicationStatusHistory(Base):
    __tablename__ = "acrm_application_status_history"
    __table_args__ = (
        Index("ix_acrm_application_status_history_tenant_id", "tenant_id"),
        Index("ix_acrm_application_status_history_tenant_app", "tenant_id", "application_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    application_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    from_status: Mapped[str | None] = mapped_column(String(64), nullable=True)
    to_status: Mapped[str] = mapped_column(String(64), nullable=False)
    changed_by_user_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=sa_text("NOW()"))


class WorkflowTransitionEvent(Base):
    __tablename__ = "acrm_workflow_transition_events"
    __table_args__ = (
        Index("ix_acrm_workflow_transition_events_tenant_id", "tenant_id"),
        Index("ix_acrm_workflow_transition_events_tenant_entity", "tenant_id", "entity_type", "entity_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    event_type: Mapped[str] = mapped_column(String(128), nullable=False)
    from_status: Mapped[str | None] = mapped_column(String(64), nullable=True)
    to_status: Mapped[str | None] = mapped_column(String(64), nullable=True)
    actor_user_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    payload_json: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=sa_text("'{}'::jsonb"))
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=sa_text("NOW()"))


class AuditEvent(Base):
    __tablename__ = "acrm_audit_events"
    __table_args__ = (
        Index("ix_acrm_audit_events_tenant_id", "tenant_id"),
        Index("ix_acrm_audit_events_tenant_action", "tenant_id", "action"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    action: Mapped[str] = mapped_column(String(128), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    actor_user_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=sa_text("'{}'::jsonb"))
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=sa_text("NOW()"))


class CounselorAssignment(AcrmCommonMixin, Base):
    __tablename__ = "acrm_counselor_assignments"
    __table_args__ = _table_args(__tablename__)

    lead_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    applicant_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    counselor_user_id: Mapped[str] = mapped_column(String(255), nullable=False)


class AssignmentHistory(Base):
    __tablename__ = "acrm_assignment_history"
    __table_args__ = (
        Index("ix_acrm_assignment_history_tenant_id", "tenant_id"),
        Index("ix_acrm_assignment_history_tenant_assignment", "tenant_id", "assignment_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    assignment_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    previous_counselor_user_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    new_counselor_user_id: Mapped[str] = mapped_column(String(255), nullable=False)
    actor_user_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=sa_text("NOW()"))
