"""Security / Access / Compliance SQLAlchemy models."""

from __future__ import annotations

from sqlalchemy import BigInteger, Boolean, DateTime, Index, String, Text, text as sa_text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, declarative_mixin, mapped_column

from app.core.db import Base


MODULE_NAME = "security_access_compliance"
API_PREFIX = "/api/admin/security-access-compliance"
RUNTIME_MODE = "GOVERNANCE_READINESS_EVIDENCE_AUDIT_CONTROL_METADATA_HUMAN_REVIEW_ONLY"
EXPECTED_TABLE_COUNT = 24
EXPECTED_ROUTE_COUNT = 47
EXPECTED_PERMISSION_COUNT = 44
TABLE_PREFIX = "sac_"
CONTRACT_VERSION = "A-043.2.RUNTIME"
DATA_SOURCE = "computed_from_security_access_compliance_records"

FAKE_SECURITY_CERTIFICATION = False
FAKE_COMPLIANCE_CERTIFICATION = False
LEGAL_REGULATORY_COMPLIANCE_CLAIMED = False
SOC_SIEM_REPLACEMENT_CLAIMED = False
FAKE_INCIDENT_RESOLUTION = False
FAKE_AUDIT_PROOF = False
FAKE_PENETRATION_TEST_RESULT = False
FAKE_VULNERABILITY_SCAN_RESULT = False
FAKE_RISK_SCORE = False
HIDDEN_USER_RISK_SCORE_PRESENT = False
DISCRIMINATORY_RANKING_PRESENT = False
AUTONOMOUS_ENFORCEMENT_ENABLED = False
AUTOMATIC_USER_BLOCKING_ENABLED = False
AUTOMATIC_USER_SANCTION_ENABLED = False
AUTOMATIC_DATA_DELETION_ENABLED = False
EXTERNAL_REGULATOR_SUBMISSION_ENABLED = False
PRODUCTION_SECURITY_CLAIMED = False
HUMAN_REVIEW_REQUIRED = True

TABLE_NAMES = {
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
}


def _table_args(table_name: str):
    return (
        Index(f"ix_{table_name}_tenant_id", "tenant_id"),
        Index(f"ix_{table_name}_tenant_status", "tenant_id", "status"),
    )


@declarative_mixin
class SacCommonMixin:
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    status: Mapped[str] = mapped_column(String(64), nullable=False, server_default=sa_text("'active'"))
    human_review_required: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa_text("true"))
    certification_claimed: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa_text("false"))
    compliance_certified: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa_text("false"))
    soc_siem_replacement: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa_text("false"))
    autonomous_enforcement_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa_text("false"))
    external_submission_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa_text("false"))
    hidden_user_risk_score_present: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa_text("false"))
    incomplete_data: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa_text("false"))
    source_module: Mapped[str | None] = mapped_column(String(128), nullable=True)
    source_entity_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=sa_text("'{}'::jsonb"))
    limitations_json: Mapped[list] = mapped_column(JSONB, nullable=False, server_default=sa_text("'[]'::jsonb"))
    created_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    updated_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=sa_text("NOW()"))
    updated_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=sa_text("NOW()"))
    archived_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True)


class SacReadinessProfile(SacCommonMixin, Base):
    __tablename__ = "sac_readiness_profiles"
    __table_args__ = _table_args(__tablename__)

    readiness_level: Mapped[str] = mapped_column(String(64), nullable=False, server_default=sa_text("'baseline'"))


class SacDashboardSnapshot(SacCommonMixin, Base):
    __tablename__ = "sac_dashboard_snapshots"
    __table_args__ = _table_args(__tablename__)

    summary_json: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=sa_text("'{}'::jsonb"))


class SacAccessGovernanceRecord(SacCommonMixin, Base):
    __tablename__ = "sac_access_governance_records"
    __table_args__ = _table_args(__tablename__)


class SacRolePermissionInventorySnapshot(SacCommonMixin, Base):
    __tablename__ = "sac_role_permission_inventory_snapshots"
    __table_args__ = _table_args(__tablename__)


class SacRbacEvidenceRecord(SacCommonMixin, Base):
    __tablename__ = "sac_rbac_evidence_records"
    __table_args__ = _table_args(__tablename__)


class SacAbacEvidenceRecord(SacCommonMixin, Base):
    __tablename__ = "sac_abac_evidence_records"
    __table_args__ = _table_args(__tablename__)


class SacSessionVisibilityRecord(SacCommonMixin, Base):
    __tablename__ = "sac_session_visibility_records"
    __table_args__ = _table_args(__tablename__)


class SacLoginEventReviewRecord(SacCommonMixin, Base):
    __tablename__ = "sac_login_event_review_records"
    __table_args__ = _table_args(__tablename__)


class SacMfaReadinessRecord(SacCommonMixin, Base):
    __tablename__ = "sac_mfa_readiness_records"
    __table_args__ = _table_args(__tablename__)


class SacTenantIsolationEvidenceRecord(SacCommonMixin, Base):
    __tablename__ = "sac_tenant_isolation_evidence_records"
    __table_args__ = _table_args(__tablename__)


class SacSecurityIncidentRecord(SacCommonMixin, Base):
    __tablename__ = "sac_security_incident_records"
    __table_args__ = _table_args(__tablename__)

    incident_ref: Mapped[str | None] = mapped_column(String(255), nullable=True)


class SacIncidentReviewRecord(SacCommonMixin, Base):
    __tablename__ = "sac_incident_review_records"
    __table_args__ = _table_args(__tablename__)

    incident_ref: Mapped[str | None] = mapped_column(String(255), nullable=True)


class SacRemediationTrackingRecord(SacCommonMixin, Base):
    __tablename__ = "sac_remediation_tracking_records"
    __table_args__ = _table_args(__tablename__)


class SacRiskRegisterRecord(SacCommonMixin, Base):
    __tablename__ = "sac_risk_register_records"
    __table_args__ = _table_args(__tablename__)


class SacComplianceControlRecord(SacCommonMixin, Base):
    __tablename__ = "sac_compliance_control_records"
    __table_args__ = _table_args(__tablename__)


class SacPolicyControlBridgeRecord(SacCommonMixin, Base):
    __tablename__ = "sac_policy_control_bridge_records"
    __table_args__ = _table_args(__tablename__)


class SacAuditEventReviewRecord(SacCommonMixin, Base):
    __tablename__ = "sac_audit_event_review_records"
    __table_args__ = _table_args(__tablename__)


class SacSensitiveActionReviewRecord(SacCommonMixin, Base):
    __tablename__ = "sac_sensitive_action_review_records"
    __table_args__ = _table_args(__tablename__)


class SacDataProtectionReadinessRecord(SacCommonMixin, Base):
    __tablename__ = "sac_data_protection_readiness_records"
    __table_args__ = _table_args(__tablename__)


class SacPrivacyReadinessRecord(SacCommonMixin, Base):
    __tablename__ = "sac_privacy_readiness_records"
    __table_args__ = _table_args(__tablename__)


class SacSecurityExceptionRecord(SacCommonMixin, Base):
    __tablename__ = "sac_security_exception_records"
    __table_args__ = _table_args(__tablename__)


class SacVisitorAccessBridgeRecord(SacCommonMixin, Base):
    __tablename__ = "sac_visitor_access_bridge_records"
    __table_args__ = _table_args(__tablename__)


class SacCrossVerticalBridgeRecord(SacCommonMixin, Base):
    __tablename__ = "sac_cross_vertical_bridge_records"
    __table_args__ = _table_args(__tablename__)

    bridge_key: Mapped[str] = mapped_column(String(64), nullable=False)


class SacLimitation(SacCommonMixin, Base):
    __tablename__ = "sac_limitations"
    __table_args__ = _table_args(__tablename__)

    limitation_text: Mapped[str] = mapped_column(Text, nullable=False)
