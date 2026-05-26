"""Document / Decree / Correspondence SQLAlchemy models."""

from __future__ import annotations

from sqlalchemy import BigInteger, Boolean, DateTime, Index, Integer, String, Text, text as sa_text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, declarative_mixin, mapped_column

from app.core.db import Base


MODULE_NAME = "document_decree_correspondence"
API_PREFIX = "/api/admin/document-decree-correspondence"
RUNTIME_MODE = "METADATA_EVIDENCE_READINESS_AUDIT_ARCHIVE_HUMAN_REVIEW_ONLY"
EXPECTED_TABLE_COUNT = 26
EXPECTED_ROUTE_COUNT = 53
EXPECTED_PERMISSION_COUNT = 50
TABLE_PREFIX = "ddc_"
TARGET_LEVEL = "L3"
CONTRACT_VERSION = "A-041.2.RUNTIME"
FOUNDATION_STATUS = "DOCUMENT_DECREE_CORRESPONDENCE_METADATA_EVIDENCE_BACKEND_FOUNDATION"
SOURCE_SPEC_COMMIT = "b357a0a"
SOURCE_PRODUCT_MAP_COMMIT = "f85706c"
SOURCE_VERTICAL_SELECTION_COMMIT = "fd9d172"
PRODUCT_VERTICAL = "Document / Decree / Correspondence Suite"
DATA_SOURCE = "computed_from_document_decree_correspondence_metadata"

FAKE_DOCUMENTS = False
FAKE_DECREES = False
FAKE_SIGNATURES = False
FAKE_DELIVERY_CONFIRMATIONS = False
FAKE_ARCHIVE_LEGAL_RECORD = False
OFFICIAL_LEGAL_EFFECT = False
EXTERNAL_SUBMISSION_ENABLED = False
AUTOMATIC_RECTOR_DECISION_ENABLED = False
AUTOMATIC_DECREE_APPROVAL_ENABLED = False
AUTOMATIC_DOCUMENT_SIGNING_ENABLED = False
HIDDEN_SCORE_PRESENT = False
HUMAN_REVIEW_REQUIRED = True

TABLE_NAMES = {
    "ddc_readiness_profiles",
    "ddc_dashboard_snapshots",
    "ddc_document_intake_records",
    "ddc_document_registration_records",
    "ddc_document_routing_records",
    "ddc_document_workflow_metadata",
    "ddc_rector_resolution_records",
    "ddc_decree_registry_records",
    "ddc_decree_draft_metadata",
    "ddc_incoming_correspondence_records",
    "ddc_outgoing_correspondence_records",
    "ddc_template_metadata",
    "ddc_committee_decision_bridge_records",
    "ddc_assignment_bridge_records",
    "ddc_execution_control_records",
    "ddc_sla_deadline_records",
    "ddc_overdue_visibility_records",
    "ddc_evidence_items",
    "ddc_attachment_metadata",
    "ddc_audit_events",
    "ddc_archive_readiness_records",
    "ddc_retention_metadata",
    "ddc_signature_readiness_profiles",
    "ddc_delivery_readiness_profiles",
    "ddc_bridge_records",
    "ddc_limitations",
}


def _table_args(table_name: str):
    return (
        Index(f"ix_{table_name}_tenant_id", "tenant_id"),
        Index(f"ix_{table_name}_tenant_status", "tenant_id", "status"),
    )


@declarative_mixin
class DdcMetadataMixin:
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    status: Mapped[str] = mapped_column(String(64), nullable=False, server_default=sa_text("'DRAFT'"))
    reference_key: Mapped[str] = mapped_column(String(128), nullable=False)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source_module: Mapped[str | None] = mapped_column(String(128), nullable=True)
    source_record_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=sa_text("'{}'::jsonb"))
    limitations_json: Mapped[list] = mapped_column(JSONB, nullable=False, server_default=sa_text("'[]'::jsonb"))
    human_review_required: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa_text("true"))
    fake_documents: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa_text("false"))
    fake_decrees: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa_text("false"))
    fake_signatures: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa_text("false"))
    fake_delivery_confirmations: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa_text("false"))
    fake_archive_legal_record: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa_text("false"))
    official_legal_effect: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa_text("false"))
    external_submission_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa_text("false"))
    automatic_rector_decision_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa_text("false"))
    automatic_decree_approval_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa_text("false"))
    automatic_document_signing_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa_text("false"))
    hidden_score_present: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa_text("false"))
    incomplete_data: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa_text("true"))
    created_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    updated_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=sa_text("NOW()"))
    updated_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=sa_text("NOW()"))
    archived_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ReadinessProfile(DdcMetadataMixin, Base):
    __tablename__ = "ddc_readiness_profiles"
    __table_args__ = _table_args(__tablename__)
    readiness_scope: Mapped[str] = mapped_column(String(128), nullable=False, server_default=sa_text("'suite'"))


class DashboardSnapshot(DdcMetadataMixin, Base):
    __tablename__ = "ddc_dashboard_snapshots"
    __table_args__ = _table_args(__tablename__)
    summary_json: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=sa_text("'{}'::jsonb"))


class DocumentIntakeRecord(DdcMetadataMixin, Base):
    __tablename__ = "ddc_document_intake_records"
    __table_args__ = _table_args(__tablename__)
    intake_channel: Mapped[str | None] = mapped_column(String(64), nullable=True)


class DocumentRegistrationRecord(DdcMetadataMixin, Base):
    __tablename__ = "ddc_document_registration_records"
    __table_args__ = _table_args(__tablename__)
    registry_number: Mapped[str | None] = mapped_column(String(128), nullable=True)


class DocumentRoutingRecord(DdcMetadataMixin, Base):
    __tablename__ = "ddc_document_routing_records"
    __table_args__ = _table_args(__tablename__)
    routed_to: Mapped[str | None] = mapped_column(String(255), nullable=True)


class DocumentWorkflowMetadata(DdcMetadataMixin, Base):
    __tablename__ = "ddc_document_workflow_metadata"
    __table_args__ = _table_args(__tablename__)
    workflow_stage: Mapped[str | None] = mapped_column(String(64), nullable=True)


class RectorResolutionRecord(DdcMetadataMixin, Base):
    __tablename__ = "ddc_rector_resolution_records"
    __table_args__ = _table_args(__tablename__)
    resolution_state: Mapped[str | None] = mapped_column(String(64), nullable=True)


class DecreeRegistryRecord(DdcMetadataMixin, Base):
    __tablename__ = "ddc_decree_registry_records"
    __table_args__ = _table_args(__tablename__)
    decree_type: Mapped[str | None] = mapped_column(String(64), nullable=True)


class DecreeDraftMetadata(DdcMetadataMixin, Base):
    __tablename__ = "ddc_decree_draft_metadata"
    __table_args__ = _table_args(__tablename__)
    draft_version: Mapped[int | None] = mapped_column(Integer, nullable=True)


class IncomingCorrespondenceRecord(DdcMetadataMixin, Base):
    __tablename__ = "ddc_incoming_correspondence_records"
    __table_args__ = _table_args(__tablename__)
    sender_name: Mapped[str | None] = mapped_column(String(255), nullable=True)


class OutgoingCorrespondenceRecord(DdcMetadataMixin, Base):
    __tablename__ = "ddc_outgoing_correspondence_records"
    __table_args__ = _table_args(__tablename__)
    recipient_name: Mapped[str | None] = mapped_column(String(255), nullable=True)


class TemplateMetadata(DdcMetadataMixin, Base):
    __tablename__ = "ddc_template_metadata"
    __table_args__ = _table_args(__tablename__)
    template_type: Mapped[str | None] = mapped_column(String(64), nullable=True)


class CommitteeDecisionBridgeRecord(DdcMetadataMixin, Base):
    __tablename__ = "ddc_committee_decision_bridge_records"
    __table_args__ = _table_args(__tablename__)
    committee_reference: Mapped[str | None] = mapped_column(String(255), nullable=True)


class AssignmentBridgeRecord(DdcMetadataMixin, Base):
    __tablename__ = "ddc_assignment_bridge_records"
    __table_args__ = _table_args(__tablename__)
    assignment_reference: Mapped[str | None] = mapped_column(String(255), nullable=True)


class ExecutionControlRecord(DdcMetadataMixin, Base):
    __tablename__ = "ddc_execution_control_records"
    __table_args__ = _table_args(__tablename__)
    control_state: Mapped[str | None] = mapped_column(String(64), nullable=True)


class SlaDeadlineRecord(DdcMetadataMixin, Base):
    __tablename__ = "ddc_sla_deadline_records"
    __table_args__ = _table_args(__tablename__)
    deadline_label: Mapped[str | None] = mapped_column(String(128), nullable=True)


class OverdueVisibilityRecord(DdcMetadataMixin, Base):
    __tablename__ = "ddc_overdue_visibility_records"
    __table_args__ = _table_args(__tablename__)
    overdue_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)


class EvidenceItem(Base):
    __tablename__ = "ddc_evidence_items"
    __table_args__ = (
        Index("ix_ddc_evidence_items_tenant_id", "tenant_id"),
        Index("ix_ddc_evidence_items_tenant_status", "tenant_id", "status"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    status: Mapped[str] = mapped_column(String(64), nullable=False, server_default=sa_text("'RECORDED'"))
    evidence_type: Mapped[str] = mapped_column(String(128), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    reference_uri: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source_module: Mapped[str | None] = mapped_column(String(128), nullable=True)
    source_record_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=sa_text("'{}'::jsonb"))
    limitations_json: Mapped[list] = mapped_column(JSONB, nullable=False, server_default=sa_text("'[]'::jsonb"))
    human_review_required: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa_text("true"))
    fake_documents: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa_text("false"))
    fake_decrees: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa_text("false"))
    fake_signatures: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa_text("false"))
    fake_delivery_confirmations: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa_text("false"))
    fake_archive_legal_record: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa_text("false"))
    official_legal_effect: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa_text("false"))
    external_submission_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa_text("false"))
    automatic_rector_decision_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa_text("false"))
    automatic_decree_approval_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa_text("false"))
    automatic_document_signing_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa_text("false"))
    hidden_score_present: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa_text("false"))
    incomplete_data: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa_text("true"))
    created_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=sa_text("NOW()"))


class AttachmentMetadata(DdcMetadataMixin, Base):
    __tablename__ = "ddc_attachment_metadata"
    __table_args__ = _table_args(__tablename__)
    attachment_uri: Mapped[str | None] = mapped_column(String(255), nullable=True)


class AuditEvent(Base):
    __tablename__ = "ddc_audit_events"
    __table_args__ = (
        Index("ix_ddc_audit_events_tenant_id", "tenant_id"),
        Index("ix_ddc_audit_events_tenant_created_at", "tenant_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    status: Mapped[str] = mapped_column(String(64), nullable=False, server_default=sa_text("'RECORDED'"))
    entity_type: Mapped[str] = mapped_column(String(128), nullable=False)
    entity_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    action: Mapped[str] = mapped_column(String(128), nullable=False)
    actor_user_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    before_json: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=sa_text("'{}'::jsonb"))
    after_json: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=sa_text("'{}'::jsonb"))
    metadata_json: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=sa_text("'{}'::jsonb"))
    human_review_required: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa_text("true"))
    hidden_score_present: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa_text("false"))
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=sa_text("NOW()"))


class ArchiveReadinessRecord(DdcMetadataMixin, Base):
    __tablename__ = "ddc_archive_readiness_records"
    __table_args__ = _table_args(__tablename__)
    archive_scope: Mapped[str | None] = mapped_column(String(128), nullable=True)


class RetentionMetadata(DdcMetadataMixin, Base):
    __tablename__ = "ddc_retention_metadata"
    __table_args__ = _table_args(__tablename__)
    retention_rule: Mapped[str | None] = mapped_column(String(128), nullable=True)


class SignatureReadinessProfile(DdcMetadataMixin, Base):
    __tablename__ = "ddc_signature_readiness_profiles"
    __table_args__ = _table_args(__tablename__)
    provider_name: Mapped[str | None] = mapped_column(String(128), nullable=True)


class DeliveryReadinessProfile(DdcMetadataMixin, Base):
    __tablename__ = "ddc_delivery_readiness_profiles"
    __table_args__ = _table_args(__tablename__)
    provider_name: Mapped[str | None] = mapped_column(String(128), nullable=True)


class BridgeRecord(DdcMetadataMixin, Base):
    __tablename__ = "ddc_bridge_records"
    __table_args__ = _table_args(__tablename__)
    bridge_family: Mapped[str] = mapped_column(String(128), nullable=False, server_default=sa_text("'executive'"))
    target_domain: Mapped[str | None] = mapped_column(String(128), nullable=True)
    read_only_first: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa_text("true"))
    mutation_allowed: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa_text("false"))


class Limitation(DdcMetadataMixin, Base):
    __tablename__ = "ddc_limitations"
    __table_args__ = _table_args(__tablename__)
    limitation_code: Mapped[str | None] = mapped_column(String(128), nullable=True)
