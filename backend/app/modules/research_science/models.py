"""Research / Science backend foundation SQLAlchemy models."""

from __future__ import annotations

from sqlalchemy import BigInteger, Boolean, DateTime, Index, String, Text, UniqueConstraint, text as sa_text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, declarative_mixin, mapped_column

from app.core.db import Base


MODULE_NAME = "research_science"
TABLE_PREFIX = "rs_"
TARGET_LEVEL = "L3"
CONTRACT_VERSION = "A-037.2"
FOUNDATION_STATUS = "RESEARCH_SCIENCE_METADATA_EVIDENCE_BACKEND_FOUNDATION"
MASTER_MATRIX_COMMIT = "c79cc31"
MASTER_MATRIX_ROW_COUNT = 467
SOURCE_SPEC_COMMIT = "02b5564"
SOURCE_PRODUCT_MAP_COMMIT = "10d833e"
PRODUCT_VERTICAL = "Research / Science Suite"
RESEARCH_SCIENCE_CAPABILITY_COUNT = 60
RUNTIME_MODE = "METADATA_EVIDENCE_ONLY"
DATA_SOURCE = "computed_from_research_science_metadata"
OFFICIAL_VERIFICATION_MODE = "NOT_IMPLEMENTED"
PROVIDER_INTEGRATION_MODE = "FUTURE_READINESS_ONLY"
AUTONOMY_MODE = "FORBIDDEN"

PROVIDER_INTEGRATION_ENABLED = False
EXTERNAL_DATABASE_SYNC_ENABLED = False
OFFICIAL_VERIFICATION_ENABLED = False
AUTONOMOUS_DECISION_ENABLED = False
HIDDEN_SCORE_PRESENT = False
FAKE_METRICS = False
HUMAN_REVIEW_REQUIRED = True


class ResearchProjectStatus:
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    ON_HOLD = "ON_HOLD"
    COMPLETED = "COMPLETED"
    ARCHIVED = "ARCHIVED"
    ALL = frozenset({DRAFT, ACTIVE, ON_HOLD, COMPLETED, ARCHIVED})


class StudentResearchStatus:
    DRAFT = "DRAFT"
    SUPERVISOR_ASSIGNED = "SUPERVISOR_ASSIGNED"
    IN_PROGRESS = "IN_PROGRESS"
    MILESTONE_REVIEW = "MILESTONE_REVIEW"
    COMPLETED_METADATA_ONLY = "COMPLETED_METADATA_ONLY"
    ARCHIVED = "ARCHIVED"
    ALL = frozenset({DRAFT, SUPERVISOR_ASSIGNED, IN_PROGRESS, MILESTONE_REVIEW, COMPLETED_METADATA_ONLY, ARCHIVED})


class ScientificSupervisionStatus:
    ASSIGNED = "ASSIGNED"
    ACTIVE = "ACTIVE"
    DELAYED = "DELAYED"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    COMPLETED_METADATA_ONLY = "COMPLETED_METADATA_ONLY"
    ARCHIVED = "ARCHIVED"
    ALL = frozenset({ASSIGNED, ACTIVE, DELAYED, REVIEW_REQUIRED, COMPLETED_METADATA_ONLY, ARCHIVED})


class PublicationMetadataStatus:
    DRAFT = "DRAFT"
    SUBMITTED_FOR_REVIEW = "SUBMITTED_FOR_REVIEW"
    EVIDENCE_PENDING = "EVIDENCE_PENDING"
    REVIEWED_METADATA_ONLY = "REVIEWED_METADATA_ONLY"
    REJECTED_METADATA_ONLY = "REJECTED_METADATA_ONLY"
    ARCHIVED = "ARCHIVED"
    ALL = frozenset({DRAFT, SUBMITTED_FOR_REVIEW, EVIDENCE_PENDING, REVIEWED_METADATA_ONLY, REJECTED_METADATA_ONLY, ARCHIVED})


class ConferenceParticipationStatus:
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    ACCEPTED_METADATA_ONLY = "ACCEPTED_METADATA_ONLY"
    PRESENTED_METADATA_ONLY = "PRESENTED_METADATA_ONLY"
    CERTIFICATE_METADATA_ATTACHED = "CERTIFICATE_METADATA_ATTACHED"
    REJECTED_METADATA_ONLY = "REJECTED_METADATA_ONLY"
    ARCHIVED = "ARCHIVED"
    ALL = frozenset({DRAFT, SUBMITTED, ACCEPTED_METADATA_ONLY, PRESENTED_METADATA_ONLY, CERTIFICATE_METADATA_ATTACHED, REJECTED_METADATA_ONLY, ARCHIVED})


class GrantApplicationStatus:
    DRAFT = "DRAFT"
    INTERNAL_REVIEW = "INTERNAL_REVIEW"
    SUBMITTED_EXTERNALLY_BY_HUMAN = "SUBMITTED_EXTERNALLY_BY_HUMAN"
    FUNDED_METADATA_ONLY = "FUNDED_METADATA_ONLY"
    NOT_FUNDED_METADATA_ONLY = "NOT_FUNDED_METADATA_ONLY"
    DELIVERABLE_TRACKING = "DELIVERABLE_TRACKING"
    CLOSED = "CLOSED"
    ARCHIVED = "ARCHIVED"
    ALL = frozenset({DRAFT, INTERNAL_REVIEW, SUBMITTED_EXTERNALLY_BY_HUMAN, FUNDED_METADATA_ONLY, NOT_FUNDED_METADATA_ONLY, DELIVERABLE_TRACKING, CLOSED, ARCHIVED})


class EthicsRequestStatus:
    DRAFT = "DRAFT"
    SUBMITTED_FOR_HUMAN_REVIEW = "SUBMITTED_FOR_HUMAN_REVIEW"
    IN_COMMITTEE_REVIEW = "IN_COMMITTEE_REVIEW"
    APPROVED_BY_HUMAN_COMMITTEE_METADATA_ONLY = "APPROVED_BY_HUMAN_COMMITTEE_METADATA_ONLY"
    REJECTED_BY_HUMAN_COMMITTEE_METADATA_ONLY = "REJECTED_BY_HUMAN_COMMITTEE_METADATA_ONLY"
    AMENDMENT_REQUIRED = "AMENDMENT_REQUIRED"
    CLOSED = "CLOSED"
    ARCHIVED = "ARCHIVED"
    ALL = frozenset({DRAFT, SUBMITTED_FOR_HUMAN_REVIEW, IN_COMMITTEE_REVIEW, APPROVED_BY_HUMAN_COMMITTEE_METADATA_ONLY, REJECTED_BY_HUMAN_COMMITTEE_METADATA_ONLY, AMENDMENT_REQUIRED, CLOSED, ARCHIVED})


class EvidenceVerificationStatus:
    METADATA_ONLY = "METADATA_ONLY"
    PENDING_REVIEW = "PENDING_REVIEW"
    REVIEWED = "REVIEWED"
    REJECTED = "REJECTED"
    EXTERNAL_VERIFICATION_NOT_AVAILABLE = "EXTERNAL_VERIFICATION_NOT_AVAILABLE"
    ALL = frozenset({METADATA_ONLY, PENDING_REVIEW, REVIEWED, REJECTED, EXTERNAL_VERIFICATION_NOT_AVAILABLE})


class ResearchAuditEventType:
    PROJECT_CREATED = "PROJECT_CREATED"
    PROJECT_UPDATED = "PROJECT_UPDATED"
    STUDENT_RESEARCH_CREATED = "STUDENT_RESEARCH_CREATED"
    STUDENT_RESEARCH_UPDATED = "STUDENT_RESEARCH_UPDATED"
    SUPERVISION_ASSIGNED = "SUPERVISION_ASSIGNED"
    SUPERVISION_UPDATED = "SUPERVISION_UPDATED"
    PUBLICATION_METADATA_ADDED = "PUBLICATION_METADATA_ADDED"
    PUBLICATION_METADATA_UPDATED = "PUBLICATION_METADATA_UPDATED"
    CONFERENCE_METADATA_ADDED = "CONFERENCE_METADATA_ADDED"
    CONFERENCE_METADATA_UPDATED = "CONFERENCE_METADATA_UPDATED"
    GRANT_APPLICATION_ADDED = "GRANT_APPLICATION_ADDED"
    GRANT_APPLICATION_UPDATED = "GRANT_APPLICATION_UPDATED"
    GRANT_DELIVERABLE_ADDED = "GRANT_DELIVERABLE_ADDED"
    ETHICS_REQUEST_CREATED = "ETHICS_REQUEST_CREATED"
    ETHICS_REVIEW_STATUS_UPDATED = "ETHICS_REVIEW_STATUS_UPDATED"
    ETHICS_AMENDMENT_CREATED = "ETHICS_AMENDMENT_CREATED"
    EVIDENCE_ATTACHED = "EVIDENCE_ATTACHED"
    BRIDGE_METADATA_ADDED = "BRIDGE_METADATA_ADDED"
    DASHBOARD_SNAPSHOT_CREATED = "DASHBOARD_SNAPSHOT_CREATED"
    LIMITATION_ACKNOWLEDGED = "LIMITATION_ACKNOWLEDGED"


@declarative_mixin
class ResearchScienceSafetyMixin:
    tenant_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(64), nullable=False, default=ResearchProjectStatus.DRAFT, server_default=sa_text("'DRAFT'"))
    human_review_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=sa_text("true"))
    autonomous_decision: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=sa_text("false"))
    provider_integration_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=sa_text("false"))
    external_database_sync_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=sa_text("false"))
    official_verification_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=sa_text("false"))
    hidden_score_present: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=sa_text("false"))
    incomplete_data: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=sa_text("true"))
    limitations_json: Mapped[list] = mapped_column(JSONB, nullable=False, default=list, server_default=sa_text("'[]'::jsonb"))
    metadata_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict, server_default=sa_text("'{}'::jsonb"))
    source_capability_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    source_matrix_row_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_by_user_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    updated_by_user_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=sa_text("NOW()"))
    updated_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=sa_text("NOW()"))
    archived_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ResearchProject(Base, ResearchScienceSafetyMixin):
    __tablename__ = "rs_research_projects"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    project_ref: Mapped[str] = mapped_column(String(128), nullable=False)
    department_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)
    program_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)
    external_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    __table_args__ = (
        UniqueConstraint("tenant_id", "project_ref", name="uq_rs_research_projects_tenant_ref"),
        Index("ix_rs_research_projects_tenant_status", "tenant_id", "status"),
    )


class StudentResearchWork(Base, ResearchScienceSafetyMixin):
    __tablename__ = "rs_student_research_work"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    student_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)
    faculty_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)
    project_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)
    publication_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)
    conference_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)
    topic_title: Mapped[str] = mapped_column(String(255), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    __table_args__ = (Index("ix_rs_student_research_work_tenant_status", "tenant_id", "status"),)


class ScientificSupervision(Base, ResearchScienceSafetyMixin):
    __tablename__ = "rs_scientific_supervision"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    student_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)
    faculty_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)
    project_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)
    supervision_ref: Mapped[str] = mapped_column(String(128), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    __table_args__ = (
        UniqueConstraint("tenant_id", "supervision_ref", name="uq_rs_scientific_supervision_tenant_ref"),
        Index("ix_rs_scientific_supervision_tenant_status", "tenant_id", "status"),
    )


class PublicationRegistryEntry(Base, ResearchScienceSafetyMixin):
    __tablename__ = "rs_publication_registry"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    publication_ref: Mapped[str] = mapped_column(String(128), nullable=False)
    faculty_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)
    student_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)
    project_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)
    external_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    fake_publication: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=sa_text("false"))
    autonomous_publication_verification_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=sa_text("false"))
    __table_args__ = (
        UniqueConstraint("tenant_id", "publication_ref", name="uq_rs_publication_registry_tenant_ref"),
        Index("ix_rs_publication_registry_tenant_status", "tenant_id", "status"),
    )


class ConferenceParticipation(Base, ResearchScienceSafetyMixin):
    __tablename__ = "rs_conference_participation"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    conference_ref: Mapped[str] = mapped_column(String(128), nullable=False)
    faculty_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)
    student_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)
    project_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)
    external_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    fake_certificate: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=sa_text("false"))
    __table_args__ = (
        UniqueConstraint("tenant_id", "conference_ref", name="uq_rs_conference_participation_tenant_ref"),
        Index("ix_rs_conference_participation_tenant_status", "tenant_id", "status"),
    )


class GrantApplication(Base, ResearchScienceSafetyMixin):
    __tablename__ = "rs_grant_applications"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    grant_ref: Mapped[str] = mapped_column(String(128), nullable=False)
    project_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)
    department_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)
    faculty_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)
    external_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    fake_grant_evidence: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=sa_text("false"))
    autonomous_grant_submission_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=sa_text("false"))
    __table_args__ = (
        UniqueConstraint("tenant_id", "grant_ref", name="uq_rs_grant_applications_tenant_ref"),
        Index("ix_rs_grant_applications_tenant_status", "tenant_id", "status"),
    )


class GrantDeliverable(Base, ResearchScienceSafetyMixin):
    __tablename__ = "rs_grant_deliverables"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    grant_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)
    project_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)
    external_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)
    deliverable_ref: Mapped[str] = mapped_column(String(128), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    fake_grant_evidence: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=sa_text("false"))
    __table_args__ = (
        UniqueConstraint("tenant_id", "deliverable_ref", name="uq_rs_grant_deliverables_tenant_ref"),
        Index("ix_rs_grant_deliverables_tenant_status", "tenant_id", "status"),
    )


class ResearchEthicsRequest(Base, ResearchScienceSafetyMixin):
    __tablename__ = "rs_research_ethics_requests"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ethics_ref: Mapped[str] = mapped_column(String(128), nullable=False)
    project_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)
    faculty_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)
    student_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    autonomous_ethics_approval_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=sa_text("false"))
    __table_args__ = (
        UniqueConstraint("tenant_id", "ethics_ref", name="uq_rs_research_ethics_requests_tenant_ref"),
        Index("ix_rs_research_ethics_requests_tenant_status", "tenant_id", "status"),
    )


class ResearchEthicsAmendment(Base, ResearchScienceSafetyMixin):
    __tablename__ = "rs_research_ethics_amendments"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ethics_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)
    project_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)
    external_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)
    amendment_ref: Mapped[str] = mapped_column(String(128), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    __table_args__ = (
        UniqueConstraint("tenant_id", "amendment_ref", name="uq_rs_research_ethics_amendments_tenant_ref"),
        Index("ix_rs_research_ethics_amendments_tenant_status", "tenant_id", "status"),
    )


class ResearchEvidenceMetadata(Base, ResearchScienceSafetyMixin):
    __tablename__ = "rs_research_evidence_metadata"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    source_entity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    source_entity_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    evidence_type: Mapped[str] = mapped_column(String(128), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    reference_uri: Mapped[str | None] = mapped_column(String(255), nullable=True)
    storage_ref: Mapped[str | None] = mapped_column(String(255), nullable=True)
    submitted_by_user_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    submitted_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True)
    verification_status: Mapped[str] = mapped_column(String(64), nullable=False, default=EvidenceVerificationStatus.METADATA_ONLY, server_default=sa_text("'METADATA_ONLY'"))
    verified_by_user_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    reviewed_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True)
    fake_evidence: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=sa_text("false"))
    provider_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=sa_text("false"))
    __table_args__ = (Index("ix_rs_research_evidence_tenant_entity", "tenant_id", "source_entity_type", "source_entity_id"),)


class ResearchBridgeMetadata(Base, ResearchScienceSafetyMixin):
    __tablename__ = "rs_research_bridge_metadata"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    bridge_target: Mapped[str] = mapped_column(String(64), nullable=False)
    source_entity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    source_entity_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    target_reference: Mapped[str | None] = mapped_column(String(255), nullable=True)
    bridge_status: Mapped[str] = mapped_column(String(64), nullable=False, default=ResearchProjectStatus.DRAFT, server_default=sa_text("'DRAFT'"))
    bridge_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)
    read_only_first: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=sa_text("true"))
    mutation_allowed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=sa_text("false"))
    provider_sync_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=sa_text("false"))
    external_submission_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=sa_text("false"))
    __table_args__ = (Index("ix_rs_research_bridge_tenant_target", "tenant_id", "bridge_target"),)


class ResearchDashboardSnapshot(Base):
    __tablename__ = "rs_research_dashboard_snapshots"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(64), nullable=False, default=ResearchProjectStatus.ACTIVE, server_default=sa_text("'ACTIVE'"))
    fake_metrics: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=sa_text("false"))
    incomplete_data: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=sa_text("true"))
    data_source: Mapped[str] = mapped_column(String(128), nullable=False, default=DATA_SOURCE, server_default=sa_text("'computed_from_research_science_metadata'"))
    summary_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict, server_default=sa_text("'{}'::jsonb"))
    limitations_json: Mapped[list] = mapped_column(JSONB, nullable=False, default=list, server_default=sa_text("'[]'::jsonb"))
    source_capability_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    source_matrix_row_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=sa_text("NOW()"))
    __table_args__ = (Index("ix_rs_dashboard_snapshots_tenant_status", "tenant_id", "status"),)


class ResearchAuditEvent(Base):
    __tablename__ = "rs_research_audit_events"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(128), nullable=False)
    source_entity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    source_entity_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    actor_user_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    previous_status: Mapped[str | None] = mapped_column(String(64), nullable=True)
    new_status: Mapped[str | None] = mapped_column(String(64), nullable=True)
    payload_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict, server_default=sa_text("'{}'::jsonb"))
    request_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=sa_text("NOW()"))
    human_review_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=sa_text("true"))
    autonomous_decision: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=sa_text("false"))
    provider_integration_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=sa_text("false"))
    hidden_score_present: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=sa_text("false"))
    __table_args__ = (Index("ix_rs_audit_events_tenant_entity", "tenant_id", "source_entity_type", "source_entity_id"),)


class ResearchStatusHistory(Base):
    __tablename__ = "rs_research_status_history"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    source_entity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    source_entity_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    previous_status: Mapped[str | None] = mapped_column(String(64), nullable=True)
    new_status: Mapped[str] = mapped_column(String(64), nullable=False)
    changed_by_user_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    changed_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=sa_text("NOW()"))
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict, server_default=sa_text("'{}'::jsonb"))
    human_review_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=sa_text("true"))
    __table_args__ = (Index("ix_rs_status_history_tenant_entity", "tenant_id", "source_entity_type", "source_entity_id"),)


class ResearchLimitation(Base):
    __tablename__ = "rs_research_limitations"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    source_entity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    source_entity_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    limitation_code: Mapped[str] = mapped_column(String(128), nullable=False)
    limitation_text: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict, server_default=sa_text("'{}'::jsonb"))
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=sa_text("NOW()"))
    __table_args__ = (Index("ix_rs_limitations_tenant_entity", "tenant_id", "source_entity_type", "source_entity_id"),)