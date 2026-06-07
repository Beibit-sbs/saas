"""SQLAlchemy models for Integration Provider Readiness backend foundation."""

from __future__ import annotations

from sqlalchemy import BigInteger, Boolean, DateTime, Index, String, Text, text as sa_text
from sqlalchemy.orm import Mapped, declarative_mixin, mapped_column
from sqlalchemy.types import JSON

from app.core.db import Base
from app.modules.integration_provider_readiness import CONTRACT_VERSION, MODULE_NAME


TABLE_PREFIX = "ipr_"


def _table_args(table_name: str):
    return (
        Index(f"ix_{table_name}_tenant_id", "tenant_id"),
        Index(f"ix_{table_name}_tenant_provider", "tenant_id", "provider_id"),
    )


@declarative_mixin
class ReadinessOnlyMixin:
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    provider_id: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(64), nullable=False, server_default=sa_text("'draft'"))
    payload_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    reason_code: Mapped[str | None] = mapped_column(String(128), nullable=True)
    actor_user_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    readiness_only: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa_text("true"))
    provider_connected: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa_text("false"))
    live_provider_calls: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa_text("false"))
    credentials_stored: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa_text("false"))
    external_submission: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa_text("false"))
    sync_execution: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa_text("false"))
    fake_health_metrics: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa_text("false"))
    fake_readiness_metrics: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa_text("false"))
    created_by_user_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    updated_by_user_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=sa_text("NOW()"))
    updated_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=sa_text("NOW()"))


class ProviderRegistry(Base):
    __tablename__ = f"{TABLE_PREFIX}provider_registry"
    __table_args__ = _table_args(__tablename__)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    provider_id: Mapped[str] = mapped_column(String(64), nullable=False)
    provider_name: Mapped[str] = mapped_column(String(255), nullable=False)
    provider_type: Mapped[str] = mapped_column(String(128), nullable=False)
    readiness_level: Mapped[str] = mapped_column(String(128), nullable=False)
    future_scope: Mapped[str] = mapped_column(Text, nullable=False)
    business_owner_role: Mapped[str] = mapped_column(String(64), nullable=False)
    technical_owner_role: Mapped[str] = mapped_column(String(64), nullable=False)
    security_owner_role: Mapped[str] = mapped_column(String(64), nullable=False)
    auditor_visibility: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa_text("true"))
    executive_visibility: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa_text("true"))
    status: Mapped[str] = mapped_column(String(64), nullable=False, server_default=sa_text("'catalogued'"))
    payload_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    readiness_only: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa_text("true"))
    provider_connected: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa_text("false"))
    live_provider_calls: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa_text("false"))
    credentials_stored: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa_text("false"))
    external_submission: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa_text("false"))
    sync_execution: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa_text("false"))
    fake_health_metrics: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa_text("false"))
    fake_readiness_metrics: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa_text("false"))
    created_by_user_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    updated_by_user_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=sa_text("NOW()"))
    updated_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=sa_text("NOW()"))


class ProviderProfileVersion(ReadinessOnlyMixin, Base):
    __tablename__ = f"{TABLE_PREFIX}provider_profile_versions"
    __table_args__ = _table_args(__tablename__)


class ProviderCapabilityMatrix(ReadinessOnlyMixin, Base):
    __tablename__ = f"{TABLE_PREFIX}provider_capability_matrix"
    __table_args__ = _table_args(__tablename__)


class ProviderReadinessAssessment(ReadinessOnlyMixin, Base):
    __tablename__ = f"{TABLE_PREFIX}provider_readiness_assessments"
    __table_args__ = _table_args(__tablename__)


class ProviderReadinessAssessmentScore(ReadinessOnlyMixin, Base):
    __tablename__ = f"{TABLE_PREFIX}provider_readiness_assessment_scores"
    __table_args__ = _table_args(__tablename__)


class ProviderEvidenceItem(ReadinessOnlyMixin, Base):
    __tablename__ = f"{TABLE_PREFIX}provider_evidence_items"
    __table_args__ = _table_args(__tablename__)


class ProviderEvidenceLink(ReadinessOnlyMixin, Base):
    __tablename__ = f"{TABLE_PREFIX}provider_evidence_links"
    __table_args__ = _table_args(__tablename__)


class ProviderComplianceReview(ReadinessOnlyMixin, Base):
    __tablename__ = f"{TABLE_PREFIX}provider_compliance_reviews"
    __table_args__ = _table_args(__tablename__)


class ProviderSecurityReview(ReadinessOnlyMixin, Base):
    __tablename__ = f"{TABLE_PREFIX}provider_security_reviews"
    __table_args__ = _table_args(__tablename__)


class ProviderRiskRegister(ReadinessOnlyMixin, Base):
    __tablename__ = f"{TABLE_PREFIX}provider_risk_register"
    __table_args__ = _table_args(__tablename__)


class ProviderRiskEvent(ReadinessOnlyMixin, Base):
    __tablename__ = f"{TABLE_PREFIX}provider_risk_events"
    __table_args__ = _table_args(__tablename__)


class ProviderExceptionCase(ReadinessOnlyMixin, Base):
    __tablename__ = f"{TABLE_PREFIX}provider_exception_cases"
    __table_args__ = _table_args(__tablename__)


class ProviderExceptionAction(ReadinessOnlyMixin, Base):
    __tablename__ = f"{TABLE_PREFIX}provider_exception_actions"
    __table_args__ = _table_args(__tablename__)


class ProviderStatusHistory(ReadinessOnlyMixin, Base):
    __tablename__ = f"{TABLE_PREFIX}provider_status_history"
    __table_args__ = _table_args(__tablename__)


class ProviderHealthSnapshot(ReadinessOnlyMixin, Base):
    __tablename__ = f"{TABLE_PREFIX}provider_health_snapshots"
    __table_args__ = _table_args(__tablename__)


class ProviderIntegrationPlan(ReadinessOnlyMixin, Base):
    __tablename__ = f"{TABLE_PREFIX}provider_integration_plans"
    __table_args__ = _table_args(__tablename__)


class ProviderDependencyEdge(ReadinessOnlyMixin, Base):
    __tablename__ = f"{TABLE_PREFIX}provider_dependency_edges"
    __table_args__ = _table_args(__tablename__)


class ProviderRoleAssignment(ReadinessOnlyMixin, Base):
    __tablename__ = f"{TABLE_PREFIX}provider_role_assignments"
    __table_args__ = _table_args(__tablename__)


class ProviderDashboardSnapshot(ReadinessOnlyMixin, Base):
    __tablename__ = f"{TABLE_PREFIX}provider_dashboard_snapshots"
    __table_args__ = _table_args(__tablename__)


class ProviderReportArtifact(ReadinessOnlyMixin, Base):
    __tablename__ = f"{TABLE_PREFIX}provider_report_artifacts"
    __table_args__ = _table_args(__tablename__)


class ProviderPolicyViolation(ReadinessOnlyMixin, Base):
    __tablename__ = f"{TABLE_PREFIX}provider_policy_violations"
    __table_args__ = _table_args(__tablename__)


class ProviderAuditRecord(ReadinessOnlyMixin, Base):
    __tablename__ = f"{TABLE_PREFIX}provider_audit_records"
    __table_args__ = _table_args(__tablename__)


ENTITY_MODEL_NAMES = (
    "ProviderRegistry",
    "ProviderProfileVersion",
    "ProviderCapabilityMatrix",
    "ProviderReadinessAssessment",
    "ProviderEvidenceItem",
    "ProviderComplianceReview",
    "ProviderSecurityReview",
    "ProviderRiskRegister",
    "ProviderAuditRecord",
    "ProviderHealthSnapshot",
    "ProviderIntegrationPlan",
    "ProviderDependencyEdge",
    "ProviderExceptionCase",
    "ProviderStatusHistory",
    "ProviderRoleAssignment",
    "ProviderDashboardSnapshot",
    "ProviderReportArtifact",
    "ProviderPolicyViolation",
)

TABLE_NAMES = (
    ProviderRegistry.__tablename__,
    ProviderProfileVersion.__tablename__,
    ProviderCapabilityMatrix.__tablename__,
    ProviderReadinessAssessment.__tablename__,
    ProviderReadinessAssessmentScore.__tablename__,
    ProviderEvidenceItem.__tablename__,
    ProviderEvidenceLink.__tablename__,
    ProviderComplianceReview.__tablename__,
    ProviderSecurityReview.__tablename__,
    ProviderRiskRegister.__tablename__,
    ProviderRiskEvent.__tablename__,
    ProviderExceptionCase.__tablename__,
    ProviderExceptionAction.__tablename__,
    ProviderStatusHistory.__tablename__,
    ProviderHealthSnapshot.__tablename__,
    ProviderIntegrationPlan.__tablename__,
    ProviderDependencyEdge.__tablename__,
    ProviderRoleAssignment.__tablename__,
    ProviderDashboardSnapshot.__tablename__,
    ProviderReportArtifact.__tablename__,
    ProviderPolicyViolation.__tablename__,
    ProviderAuditRecord.__tablename__,
)

ALL_MODELS = (
    ProviderRegistry,
    ProviderProfileVersion,
    ProviderCapabilityMatrix,
    ProviderReadinessAssessment,
    ProviderReadinessAssessmentScore,
    ProviderEvidenceItem,
    ProviderEvidenceLink,
    ProviderComplianceReview,
    ProviderSecurityReview,
    ProviderRiskRegister,
    ProviderRiskEvent,
    ProviderExceptionCase,
    ProviderExceptionAction,
    ProviderStatusHistory,
    ProviderHealthSnapshot,
    ProviderIntegrationPlan,
    ProviderDependencyEdge,
    ProviderRoleAssignment,
    ProviderDashboardSnapshot,
    ProviderReportArtifact,
    ProviderPolicyViolation,
    ProviderAuditRecord,
)

MODEL_METADATA = {
    "module": MODULE_NAME,
    "contract_version": CONTRACT_VERSION,
    "expected_entity_count": len(ENTITY_MODEL_NAMES),
    "expected_table_count": len(TABLE_NAMES),
    "readiness_only": True,
}
