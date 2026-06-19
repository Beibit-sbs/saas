"""Student Services / Welfare / Support SQLAlchemy models."""

from __future__ import annotations

from sqlalchemy import BigInteger, Boolean, DateTime, Index, String, Text, text as sa_text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, declarative_mixin, mapped_column

from app.core.db import Base


MODULE_NAME = "student_services_support"
API_PREFIX = "/api/admin/student-services"
RUNTIME_MODE = "METADATA_EVIDENCE_READINESS_HUMAN_REVIEW_ONLY"
EXPECTED_TABLE_COUNT = 12
EXPECTED_ROUTE_COUNT = 21
EXPECTED_PERMISSION_COUNT = 6
TABLE_PREFIX = "sss_"
CONTRACT_VERSION = "A-042.2.RUNTIME"
DATA_SOURCE = "computed_from_student_services_support_records"

FAKE_METRICS = False
PROVIDER_LIVE_ENABLED = False
AUTONOMOUS_DECISION_ENABLED = False
HIDDEN_SCORE_PRESENT = False
HUMAN_REVIEW_REQUIRED = True

TABLE_NAMES = {
    "sss_student_service_requests",
    "sss_student_service_request_events",
    "sss_student_support_cases",
    "sss_student_support_case_notes",
    "sss_student_support_case_events",
    "sss_student_support_evidence",
    "sss_hardship_support_requests",
    "sss_disability_accommodation_requests",
    "sss_student_complaints",
    "sss_student_service_sla_policies",
    "sss_student_support_escalations",
    "sss_student_support_dashboard_snapshots",
}


def _table_args(table_name: str):
    return (
        Index(f"ix_{table_name}_tenant_id", "tenant_id"),
        Index(f"ix_{table_name}_tenant_status", "tenant_id", "status"),
    )


@declarative_mixin
class SssCommonMixin:
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    status: Mapped[str] = mapped_column(String(64), nullable=False, server_default=sa_text("'draft'"))
    human_review_required: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa_text("true"))
    fake_metrics: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa_text("false"))
    provider_live_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa_text("false"))
    autonomous_decision_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa_text("false"))
    hidden_score_present: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa_text("false"))
    source_module: Mapped[str | None] = mapped_column(String(128), nullable=True)
    source_entity_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=sa_text("'{}'::jsonb"))
    limitations_json: Mapped[list] = mapped_column(JSONB, nullable=False, server_default=sa_text("'[]'::jsonb"))
    created_by_user_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    updated_by_user_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=sa_text("NOW()"))
    updated_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=sa_text("NOW()"))
    archived_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True)


class StudentServiceRequest(SssCommonMixin, Base):
    __tablename__ = "sss_student_service_requests"
    __table_args__ = _table_args(__tablename__)

    request_type: Mapped[str] = mapped_column(String(64), nullable=False)
    support_priority: Mapped[str] = mapped_column(String(32), nullable=False, server_default=sa_text("'medium'"))
    student_id: Mapped[str] = mapped_column(String(128), nullable=False)
    assigned_to_user_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    subject: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)


class StudentServiceRequestEvent(Base):
    __tablename__ = "sss_student_service_request_events"
    __table_args__ = (
        Index("ix_sss_student_service_request_events_tenant_id", "tenant_id"),
        Index("ix_sss_student_service_request_events_tenant_request", "tenant_id", "request_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    request_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    event_type: Mapped[str] = mapped_column(String(128), nullable=False)
    actor_user_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    payload_json: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=sa_text("'{}'::jsonb"))
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=sa_text("NOW()"))


class StudentSupportCase(SssCommonMixin, Base):
    __tablename__ = "sss_student_support_cases"
    __table_args__ = _table_args(__tablename__)

    case_type: Mapped[str] = mapped_column(String(64), nullable=False)
    request_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    assigned_to_user_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)


class StudentSupportCaseNote(Base):
    __tablename__ = "sss_student_support_case_notes"
    __table_args__ = (
        Index("ix_sss_student_support_case_notes_tenant_id", "tenant_id"),
        Index("ix_sss_student_support_case_notes_tenant_case", "tenant_id", "case_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    case_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    note: Mapped[str] = mapped_column(Text, nullable=False)
    actor_user_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=sa_text("'{}'::jsonb"))
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=sa_text("NOW()"))


class StudentSupportCaseEvent(Base):
    __tablename__ = "sss_student_support_case_events"
    __table_args__ = (
        Index("ix_sss_student_support_case_events_tenant_id", "tenant_id"),
        Index("ix_sss_student_support_case_events_tenant_case", "tenant_id", "case_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    case_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    event_type: Mapped[str] = mapped_column(String(128), nullable=False)
    actor_user_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    payload_json: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=sa_text("'{}'::jsonb"))
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=sa_text("NOW()"))


class StudentSupportEvidence(Base):
    __tablename__ = "sss_student_support_evidence"
    __table_args__ = (
        Index("ix_sss_student_support_evidence_tenant_id", "tenant_id"),
        Index("ix_sss_student_support_evidence_tenant_case", "tenant_id", "case_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    case_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    evidence_type: Mapped[str] = mapped_column(String(128), nullable=False)
    evidence_ref: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source_available: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa_text("false"))
    limitations: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=sa_text("'{}'::jsonb"))
    created_by_user_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=sa_text("NOW()"))


class HardshipSupportRequest(SssCommonMixin, Base):
    __tablename__ = "sss_hardship_support_requests"
    __table_args__ = _table_args(__tablename__)

    request_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    readiness_status: Mapped[str] = mapped_column(String(64), nullable=False, server_default=sa_text("'insufficient_evidence'"))
    missing_evidence_json: Mapped[list] = mapped_column(JSONB, nullable=False, server_default=sa_text("'[]'::jsonb"))
    recommended_next_step: Mapped[str | None] = mapped_column(String(255), nullable=True)


class DisabilityAccommodationRequest(SssCommonMixin, Base):
    __tablename__ = "sss_disability_accommodation_requests"
    __table_args__ = _table_args(__tablename__)

    request_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    readiness_status: Mapped[str] = mapped_column(String(64), nullable=False, server_default=sa_text("'insufficient_evidence'"))
    missing_evidence_json: Mapped[list] = mapped_column(JSONB, nullable=False, server_default=sa_text("'[]'::jsonb"))
    recommended_next_step: Mapped[str | None] = mapped_column(String(255), nullable=True)


class StudentComplaint(SssCommonMixin, Base):
    __tablename__ = "sss_student_complaints"
    __table_args__ = _table_args(__tablename__)

    request_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    routed_to: Mapped[str | None] = mapped_column(String(255), nullable=True)
    complaint_summary: Mapped[str | None] = mapped_column(Text, nullable=True)


class StudentServiceSlaPolicy(SssCommonMixin, Base):
    __tablename__ = "sss_student_service_sla_policies"
    __table_args__ = _table_args(__tablename__)

    policy_code: Mapped[str] = mapped_column(String(128), nullable=False)
    target_hours: Mapped[int] = mapped_column(BigInteger, nullable=False, server_default=sa_text("72"))


class StudentSupportEscalation(SssCommonMixin, Base):
    __tablename__ = "sss_student_support_escalations"
    __table_args__ = _table_args(__tablename__)

    case_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    escalation_status: Mapped[str] = mapped_column(String(64), nullable=False, server_default=sa_text("'pending'"))
    reason: Mapped[str] = mapped_column(Text, nullable=False)


class StudentSupportDashboardSnapshot(SssCommonMixin, Base):
    __tablename__ = "sss_student_support_dashboard_snapshots"
    __table_args__ = _table_args(__tablename__)

    data_source: Mapped[str] = mapped_column(String(128), nullable=False, server_default=sa_text("'computed_from_student_services_support_records'"))
    summary_json: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=sa_text("'{}'::jsonb"))
