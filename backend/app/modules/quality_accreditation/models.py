"""Quality / Accreditation backend foundation SQLAlchemy models."""

from __future__ import annotations

from sqlalchemy import BigInteger, Boolean, DateTime, Index, Integer, String, Text, UniqueConstraint, text as sa_text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, declarative_mixin, mapped_column

from app.core.db import Base


MODULE_NAME = "quality_accreditation"
TABLE_PREFIX = "qa_"
TARGET_LEVEL = "L3"
CONTRACT_VERSION = "A-038.2"
FOUNDATION_STATUS = "QUALITY_ACCREDITATION_METADATA_EVIDENCE_BACKEND_FOUNDATION"
SOURCE_SPEC_COMMIT = "ad2cad9"
SOURCE_PRODUCT_MAP_COMMIT = "1253e19"
SOURCE_VERTICAL_SELECTION_COMMIT = "7da0c70"
SOURCE_PREVIOUS_VERTICAL_CLOSURE_COMMIT = "e8dd4a0"
MASTER_MATRIX_COMMIT = "c79cc31"
MASTER_MATRIX_ROW_COUNT = 467
PRODUCT_VERTICAL = "Quality / Accreditation Suite"
DETAILED_CAPABILITY_COUNT = 44
CAPABILITY_FAMILY_COUNT = 10
RUNTIME_MODE = "METADATA_EVIDENCE_ONLY"
DATA_SOURCE = "computed_from_quality_accreditation_metadata"

OFFICIAL_ACCREDITATION_APPROVAL_ENABLED = False
OFFICIAL_MINISTRY_SUBMISSION_ENABLED = False
OFFICIAL_RANKING_CLAIM_ENABLED = False
AUTOMATIC_ACCREDITATION_DECISION_ENABLED = False
PROVIDER_INTEGRATION_ENABLED = False
EXTERNAL_DATABASE_SYNC_ENABLED = False
HIDDEN_SCORE_PRESENT = False
FAKE_METRICS = False
FAKE_EVIDENCE = False
HUMAN_REVIEW_REQUIRED = True


class QualityFrameworkStatus:
    DRAFT = "DRAFT"
    ACTIVE_METADATA_ONLY = "ACTIVE_METADATA_ONLY"
    UNDER_REVIEW = "UNDER_REVIEW"
    ARCHIVED = "ARCHIVED"


class AccreditationStandardStatus:
    DRAFT = "DRAFT"
    ACTIVE_METADATA_ONLY = "ACTIVE_METADATA_ONLY"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    ARCHIVED = "ARCHIVED"


class EvidenceReviewStatus:
    DRAFT = "DRAFT"
    SUBMITTED_FOR_REVIEW = "SUBMITTED_FOR_REVIEW"
    REVIEWED_METADATA_ONLY = "REVIEWED_METADATA_ONLY"
    ACCEPTED_METADATA_ONLY = "ACCEPTED_METADATA_ONLY"
    REJECTED_METADATA_ONLY = "REJECTED_METADATA_ONLY"
    MISSING = "MISSING"
    EXPIRED = "EXPIRED"
    LIMITATION_RECORDED = "LIMITATION_RECORDED"


class ReadinessStatus:
    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    EVIDENCE_INCOMPLETE = "EVIDENCE_INCOMPLETE"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    READY_FOR_INTERNAL_REVIEW = "READY_FOR_INTERNAL_REVIEW"
    INTERNAL_REVIEWED_METADATA_ONLY = "INTERNAL_REVIEWED_METADATA_ONLY"
    BLOCKED_BY_MISSING_EVIDENCE = "BLOCKED_BY_MISSING_EVIDENCE"
    ARCHIVED = "ARCHIVED"


class SelfAssessmentStatus:
    DRAFT = "DRAFT"
    SECTION_OWNER_REVIEW = "SECTION_OWNER_REVIEW"
    QA_REVIEW = "QA_REVIEW"
    COMMITTEE_REVIEW = "COMMITTEE_REVIEW"
    INTERNAL_APPROVED_METADATA_ONLY = "INTERNAL_APPROVED_METADATA_ONLY"
    REVISION_REQUIRED = "REVISION_REQUIRED"
    ARCHIVED = "ARCHIVED"


class ImprovementPlanStatus:
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    DELAYED = "DELAYED"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    COMPLETED_METADATA_ONLY = "COMPLETED_METADATA_ONLY"
    ARCHIVED = "ARCHIVED"


class InternalAuditStatus:
    PLANNED = "PLANNED"
    IN_PROGRESS = "IN_PROGRESS"
    FINDINGS_RECORDED = "FINDINGS_RECORDED"
    CORRECTIVE_ACTIONS_ASSIGNED = "CORRECTIVE_ACTIONS_ASSIGNED"
    CLOSED_METADATA_ONLY = "CLOSED_METADATA_ONLY"
    ARCHIVED = "ARCHIVED"


class GapRiskBand:
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"
    UNKNOWN = "UNKNOWN"


class BridgeStatus:
    DRAFT = "DRAFT"
    LINKED_METADATA_ONLY = "LINKED_METADATA_ONLY"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    BROKEN_SOURCE_REFERENCE = "BROKEN_SOURCE_REFERENCE"
    ARCHIVED = "ARCHIVED"


class QualityAuditEventType:
    FRAMEWORK_CREATED = "FRAMEWORK_CREATED"
    FRAMEWORK_UPDATED = "FRAMEWORK_UPDATED"
    STANDARD_CREATED = "STANDARD_CREATED"
    CRITERION_CREATED = "CRITERION_CREATED"
    EVIDENCE_REGISTERED = "EVIDENCE_REGISTERED"
    EVIDENCE_REVIEWED = "EVIDENCE_REVIEWED"
    PROGRAM_READINESS_UPDATED = "PROGRAM_READINESS_UPDATED"
    INSTITUTIONAL_READINESS_UPDATED = "INSTITUTIONAL_READINESS_UPDATED"
    SELF_ASSESSMENT_CREATED = "SELF_ASSESSMENT_CREATED"
    SELF_ASSESSMENT_SECTION_UPDATED = "SELF_ASSESSMENT_SECTION_UPDATED"
    IMPROVEMENT_PLAN_CREATED = "IMPROVEMENT_PLAN_CREATED"
    IMPROVEMENT_ACTION_UPDATED = "IMPROVEMENT_ACTION_UPDATED"
    INTERNAL_AUDIT_CREATED = "INTERNAL_AUDIT_CREATED"
    AUDIT_FINDING_RECORDED = "AUDIT_FINDING_RECORDED"
    PROGRAM_REVIEW_CREATED = "PROGRAM_REVIEW_CREATED"
    STAKEHOLDER_FEEDBACK_METADATA_ADDED = "STAKEHOLDER_FEEDBACK_METADATA_ADDED"
    EXTERNAL_REVIEW_METADATA_ADDED = "EXTERNAL_REVIEW_METADATA_ADDED"
    COMMITTEE_WORKFLOW_UPDATED = "COMMITTEE_WORKFLOW_UPDATED"
    GAP_ANALYSIS_UPDATED = "GAP_ANALYSIS_UPDATED"
    BRIDGE_CREATED = "BRIDGE_CREATED"
    DASHBOARD_SNAPSHOT_CREATED = "DASHBOARD_SNAPSHOT_CREATED"
    BRAIN_SIGNAL_RECORDED = "BRAIN_SIGNAL_RECORDED"
    LIMITATION_ACKNOWLEDGED = "LIMITATION_ACKNOWLEDGED"


@declarative_mixin
class QualityAccreditationSafetyMixin:
    tenant_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(64), nullable=False, default=QualityFrameworkStatus.DRAFT, server_default=sa_text("'DRAFT'"))
    created_by_user_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    updated_by_user_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source_capability_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    source_family_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    limitations_json: Mapped[list] = mapped_column(JSONB, nullable=False, default=list, server_default=sa_text("'[]'::jsonb"))
    metadata_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict, server_default=sa_text("'{}'::jsonb"))
    human_review_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=sa_text("true"))
    official_accreditation_approval_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=sa_text("false"))
    official_ministry_submission_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=sa_text("false"))
    official_ranking_claim_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=sa_text("false"))
    automatic_accreditation_decision_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=sa_text("false"))
    provider_integration_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=sa_text("false"))
    external_database_sync_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=sa_text("false"))
    hidden_score_present: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=sa_text("false"))
    autonomous_decision: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=sa_text("false"))
    incomplete_data: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=sa_text("true"))
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=sa_text("NOW()"))
    updated_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=sa_text("NOW()"))
    archived_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True)


@declarative_mixin
class QualityEvidenceMixin:
    standard_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)
    criterion_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)


class QualityFramework(Base, QualityAccreditationSafetyMixin):
    __tablename__ = "qa_quality_frameworks"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    framework_ref: Mapped[str] = mapped_column(String(128), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    __table_args__ = (
        UniqueConstraint("tenant_id", "framework_ref", name="uq_qa_quality_frameworks_tenant_ref"),
        Index("ix_qa_quality_frameworks_tenant_status", "tenant_id", "status"),
    )


class QualityPolicyRegistry(Base, QualityAccreditationSafetyMixin):
    __tablename__ = "qa_quality_policy_registry"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    policy_ref: Mapped[str] = mapped_column(String(128), nullable=False)
    owner_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    __table_args__ = (
        UniqueConstraint("tenant_id", "policy_ref", name="uq_qa_quality_policy_registry_tenant_ref"),
        Index("ix_qa_quality_policy_registry_tenant_status", "tenant_id", "status"),
    )


class AccreditationStandard(Base, QualityAccreditationSafetyMixin):
    __tablename__ = "qa_accreditation_standards"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    framework_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)
    standard_ref: Mapped[str] = mapped_column(String(128), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    __table_args__ = (
        UniqueConstraint("tenant_id", "standard_ref", name="uq_qa_accreditation_standards_tenant_ref"),
        Index("ix_qa_accreditation_standards_tenant_status", "tenant_id", "status"),
        Index("ix_qa_accreditation_standards_tenant_standard", "tenant_id", "standard_ref"),
    )


class StandardCriterion(Base, QualityAccreditationSafetyMixin, QualityEvidenceMixin):
    __tablename__ = "qa_standard_criteria"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    criterion_ref: Mapped[str] = mapped_column(String(128), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    __table_args__ = (
        UniqueConstraint("tenant_id", "criterion_ref", name="uq_qa_standard_criteria_tenant_ref"),
        Index("ix_qa_standard_criteria_tenant_status", "tenant_id", "status"),
        Index("ix_qa_standard_criteria_tenant_standard_criterion", "tenant_id", "standard_ref", "criterion_ref"),
    )


class StandardsEvidenceRequirement(Base, QualityAccreditationSafetyMixin, QualityEvidenceMixin):
    __tablename__ = "qa_standards_evidence_requirements"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    requirement_ref: Mapped[str] = mapped_column(String(128), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    __table_args__ = (
        UniqueConstraint("tenant_id", "requirement_ref", name="uq_qa_stds_evidence_requirements_tenant_ref"),
        Index("ix_qa_stds_evidence_requirements_tenant_status", "tenant_id", "status"),
        Index("ix_qa_stds_evidence_requirements_tenant_std_crit", "tenant_id", "standard_ref", "criterion_ref"),
    )


class QualityEvidenceRegistry(Base, QualityAccreditationSafetyMixin, QualityEvidenceMixin):
    __tablename__ = "qa_quality_evidence_registry"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    evidence_ref: Mapped[str] = mapped_column(String(128), nullable=False)
    source_entity_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    reference_uri: Mapped[str | None] = mapped_column(String(255), nullable=True)
    fake_evidence: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=sa_text("false"))
    __table_args__ = (
        UniqueConstraint("tenant_id", "evidence_ref", name="uq_qa_quality_evidence_registry_tenant_ref"),
        Index("ix_qa_quality_evidence_registry_tenant_status", "tenant_id", "status"),
        Index("ix_qa_quality_evidence_registry_tenant_std_crit", "tenant_id", "standard_ref", "criterion_ref"),
    )


class EvidenceReview(Base, QualityAccreditationSafetyMixin):
    __tablename__ = "qa_evidence_review"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    review_ref: Mapped[str] = mapped_column(String(128), nullable=False)
    evidence_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)
    reviewer_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    __table_args__ = (
        UniqueConstraint("tenant_id", "review_ref", name="uq_qa_evidence_review_tenant_ref"),
        Index("ix_qa_evidence_review_tenant_status", "tenant_id", "status"),
    )


class EvidenceLimitation(Base, QualityAccreditationSafetyMixin, QualityEvidenceMixin):
    __tablename__ = "qa_evidence_limitations"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    limitation_ref: Mapped[str] = mapped_column(String(128), nullable=False)
    evidence_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)
    limitation_code: Mapped[str] = mapped_column(String(128), nullable=False)
    limitation_text: Mapped[str] = mapped_column(Text, nullable=False)
    __table_args__ = (
        UniqueConstraint("tenant_id", "limitation_ref", name="uq_qa_evidence_limitations_tenant_ref"),
        Index("ix_qa_evidence_limitations_tenant_status", "tenant_id", "status"),
        Index("ix_qa_evidence_limitations_tenant_std_crit", "tenant_id", "standard_ref", "criterion_ref"),
    )


class ProgramAccreditationReadiness(Base, QualityAccreditationSafetyMixin):
    __tablename__ = "qa_program_accreditation_readiness"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    readiness_ref: Mapped[str] = mapped_column(String(128), nullable=False)
    program_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)
    framework_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)
    completion_percent: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default=sa_text("0"))
    __table_args__ = (
        UniqueConstraint("tenant_id", "readiness_ref", name="uq_qa_program_accred_readiness_tenant_ref"),
        Index("ix_qa_program_accred_readiness_tenant_status", "tenant_id", "status"),
    )


class InstitutionalAccreditationReadiness(Base, QualityAccreditationSafetyMixin):
    __tablename__ = "qa_institutional_accreditation_readiness"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    readiness_ref: Mapped[str] = mapped_column(String(128), nullable=False)
    framework_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)
    completion_percent: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default=sa_text("0"))
    __table_args__ = (
        UniqueConstraint("tenant_id", "readiness_ref", name="uq_qa_inst_accred_readiness_tenant_ref"),
        Index("ix_qa_inst_accred_readiness_tenant_status", "tenant_id", "status"),
    )


class SelfAssessmentReport(Base, QualityAccreditationSafetyMixin):
    __tablename__ = "qa_self_assessment_reports"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    report_ref: Mapped[str] = mapped_column(String(128), nullable=False)
    framework_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)
    program_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    __table_args__ = (
        UniqueConstraint("tenant_id", "report_ref", name="uq_qa_self_assessment_reports_tenant_ref"),
        Index("ix_qa_self_assessment_reports_tenant_status", "tenant_id", "status"),
    )


class SelfAssessmentSection(Base, QualityAccreditationSafetyMixin, QualityEvidenceMixin):
    __tablename__ = "qa_self_assessment_sections"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    section_ref: Mapped[str] = mapped_column(String(128), nullable=False)
    report_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)
    owner_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    __table_args__ = (
        UniqueConstraint("tenant_id", "section_ref", name="uq_qa_self_assessment_sections_tenant_ref"),
        Index("ix_qa_self_assessment_sections_tenant_status", "tenant_id", "status"),
        Index("ix_qa_self_assessment_sections_tenant_std_crit", "tenant_id", "standard_ref", "criterion_ref"),
    )


class QualityImprovementPlan(Base, QualityAccreditationSafetyMixin):
    __tablename__ = "qa_quality_improvement_plans"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    plan_ref: Mapped[str] = mapped_column(String(128), nullable=False)
    report_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)
    owner_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    __table_args__ = (
        UniqueConstraint("tenant_id", "plan_ref", name="uq_qa_quality_improvement_plans_tenant_ref"),
        Index("ix_qa_quality_improvement_plans_tenant_status", "tenant_id", "status"),
    )


class QualityImprovementAction(Base, QualityAccreditationSafetyMixin):
    __tablename__ = "qa_quality_improvement_actions"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    action_ref: Mapped[str] = mapped_column(String(128), nullable=False)
    plan_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)
    owner_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    __table_args__ = (
        UniqueConstraint("tenant_id", "action_ref", name="uq_qa_quality_improvement_actions_tenant_ref"),
        Index("ix_qa_quality_improvement_actions_tenant_status", "tenant_id", "status"),
    )


class InternalQualityAudit(Base, QualityAccreditationSafetyMixin):
    __tablename__ = "qa_internal_quality_audits"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    audit_ref: Mapped[str] = mapped_column(String(128), nullable=False)
    framework_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)
    committee_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    __table_args__ = (
        UniqueConstraint("tenant_id", "audit_ref", name="uq_qa_internal_quality_audits_tenant_ref"),
        Index("ix_qa_internal_quality_audits_tenant_status", "tenant_id", "status"),
    )


class QualityAuditFinding(Base, QualityAccreditationSafetyMixin, QualityEvidenceMixin):
    __tablename__ = "qa_quality_audit_findings"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    finding_ref: Mapped[str] = mapped_column(String(128), nullable=False)
    audit_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)
    risk_band: Mapped[str] = mapped_column(String(32), nullable=False, default=GapRiskBand.UNKNOWN, server_default=sa_text("'UNKNOWN'"))
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    __table_args__ = (
        UniqueConstraint("tenant_id", "finding_ref", name="uq_qa_quality_audit_findings_tenant_ref"),
        Index("ix_qa_quality_audit_findings_tenant_status", "tenant_id", "status"),
        Index("ix_qa_quality_audit_findings_tenant_std_crit", "tenant_id", "standard_ref", "criterion_ref"),
    )


class ProgramReviewCycle(Base, QualityAccreditationSafetyMixin):
    __tablename__ = "qa_program_review_cycles"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    cycle_ref: Mapped[str] = mapped_column(String(128), nullable=False)
    program_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)
    framework_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    __table_args__ = (
        UniqueConstraint("tenant_id", "cycle_ref", name="uq_qa_program_review_cycles_tenant_ref"),
        Index("ix_qa_program_review_cycles_tenant_status", "tenant_id", "status"),
    )


class LearningOutcomesAssessment(Base, QualityAccreditationSafetyMixin):
    __tablename__ = "qa_learning_outcomes_assessment"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    assessment_ref: Mapped[str] = mapped_column(String(128), nullable=False)
    program_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)
    criterion_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    __table_args__ = (
        UniqueConstraint("tenant_id", "assessment_ref", name="uq_qa_learning_outcomes_assessment_tenant_ref"),
        Index("ix_qa_learning_outcomes_assessment_tenant_status", "tenant_id", "status"),
    )


class StakeholderFeedbackMetadata(Base, QualityAccreditationSafetyMixin):
    __tablename__ = "qa_stakeholder_feedback_metadata"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    feedback_ref: Mapped[str] = mapped_column(String(128), nullable=False)
    program_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)
    student_group_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    __table_args__ = (
        UniqueConstraint("tenant_id", "feedback_ref", name="uq_qa_stakeholder_feedback_metadata_tenant_ref"),
        Index("ix_qa_stakeholder_feedback_metadata_tenant_status", "tenant_id", "status"),
    )


class SurveyQualityMetadata(Base, QualityAccreditationSafetyMixin):
    __tablename__ = "qa_survey_quality_metadata"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    survey_ref: Mapped[str] = mapped_column(String(128), nullable=False)
    program_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)
    owner_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    __table_args__ = (
        UniqueConstraint("tenant_id", "survey_ref", name="uq_qa_survey_quality_metadata_tenant_ref"),
        Index("ix_qa_survey_quality_metadata_tenant_status", "tenant_id", "status"),
    )


class ExternalExpertReview(Base, QualityAccreditationSafetyMixin):
    __tablename__ = "qa_external_expert_reviews"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    review_ref: Mapped[str] = mapped_column(String(128), nullable=False)
    program_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)
    reviewer_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    __table_args__ = (
        UniqueConstraint("tenant_id", "review_ref", name="uq_qa_external_expert_reviews_tenant_ref"),
        Index("ix_qa_external_expert_reviews_tenant_status", "tenant_id", "status"),
    )


class ExpertRecommendationResponsePlan(Base, QualityAccreditationSafetyMixin):
    __tablename__ = "qa_expert_recommendation_response_plans"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    response_plan_ref: Mapped[str] = mapped_column(String(128), nullable=False)
    review_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)
    owner_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    __table_args__ = (
        UniqueConstraint("tenant_id", "response_plan_ref", name="uq_qa_expert_response_plans_tenant_ref"),
        Index("ix_qa_expert_response_plans_tenant_status", "tenant_id", "status"),
    )


class AccreditationCommitteeWorkflow(Base, QualityAccreditationSafetyMixin):
    __tablename__ = "qa_accreditation_committee_workflow"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    workflow_ref: Mapped[str] = mapped_column(String(128), nullable=False)
    report_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)
    committee_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    __table_args__ = (
        UniqueConstraint("tenant_id", "workflow_ref", name="uq_qa_accred_committee_workflow_tenant_ref"),
        Index("ix_qa_accred_committee_workflow_tenant_status", "tenant_id", "status"),
    )


class ComplianceGapAnalysis(Base, QualityAccreditationSafetyMixin, QualityEvidenceMixin):
    __tablename__ = "qa_compliance_gap_analysis"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    gap_ref: Mapped[str] = mapped_column(String(128), nullable=False)
    risk_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)
    risk_band: Mapped[str] = mapped_column(String(32), nullable=False, default=GapRiskBand.UNKNOWN, server_default=sa_text("'UNKNOWN'"))
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    __table_args__ = (
        UniqueConstraint("tenant_id", "gap_ref", name="uq_qa_compliance_gap_analysis_tenant_ref"),
        Index("ix_qa_compliance_gap_analysis_tenant_status", "tenant_id", "status"),
        Index("ix_qa_compliance_gap_analysis_tenant_std_crit", "tenant_id", "standard_ref", "criterion_ref"),
    )


class AccreditationCalendar(Base, QualityAccreditationSafetyMixin):
    __tablename__ = "qa_accreditation_calendar"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    calendar_ref: Mapped[str] = mapped_column(String(128), nullable=False)
    owner_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    __table_args__ = (
        UniqueConstraint("tenant_id", "calendar_ref", name="uq_qa_accreditation_calendar_tenant_ref"),
        Index("ix_qa_accreditation_calendar_tenant_status", "tenant_id", "status"),
    )


class QualityRiskRegister(Base, QualityAccreditationSafetyMixin):
    __tablename__ = "qa_quality_risk_register"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    risk_ref: Mapped[str] = mapped_column(String(128), nullable=False)
    program_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)
    standard_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)
    risk_band: Mapped[str] = mapped_column(String(32), nullable=False, default=GapRiskBand.UNKNOWN, server_default=sa_text("'UNKNOWN'"))
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    __table_args__ = (
        UniqueConstraint("tenant_id", "risk_ref", name="uq_qa_quality_risk_register_tenant_ref"),
        Index("ix_qa_quality_risk_register_tenant_status", "tenant_id", "status"),
    )


class QualityBridgeMetadata(Base, QualityAccreditationSafetyMixin):
    __tablename__ = "qa_quality_bridge_metadata"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    bridge_ref: Mapped[str] = mapped_column(String(128), nullable=False)
    source_vertical_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)
    source_entity_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)
    target_reference: Mapped[str | None] = mapped_column(String(255), nullable=True)
    read_only_first: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=sa_text("true"))
    mutation_allowed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=sa_text("false"))
    __table_args__ = (
        UniqueConstraint("tenant_id", "bridge_ref", name="uq_qa_quality_bridge_metadata_tenant_ref"),
        Index("ix_qa_quality_bridge_metadata_tenant_status", "tenant_id", "status"),
        Index("ix_qa_quality_bridge_metadata_tenant_source", "tenant_id", "source_vertical_ref", "source_entity_ref"),
    )


class QualityDashboardSnapshot(Base):
    __tablename__ = "qa_quality_dashboard_snapshots"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(64), nullable=False, default=QualityFrameworkStatus.ACTIVE_METADATA_ONLY, server_default=sa_text("'ACTIVE_METADATA_ONLY'"))
    fake_metrics: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=sa_text("false"))
    incomplete_data: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=sa_text("true"))
    data_source: Mapped[str] = mapped_column(String(128), nullable=False, default=DATA_SOURCE, server_default=sa_text("'computed_from_quality_accreditation_metadata'"))
    summary_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict, server_default=sa_text("'{}'::jsonb"))
    limitations_json: Mapped[list] = mapped_column(JSONB, nullable=False, default=list, server_default=sa_text("'[]'::jsonb"))
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=sa_text("NOW()"))
    __table_args__ = (Index("ix_qa_quality_dashboard_snapshots_tenant_created", "tenant_id", "created_at"),)


class QualityBrainSignal(Base, QualityAccreditationSafetyMixin):
    __tablename__ = "qa_quality_brain_signals"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    signal_ref: Mapped[str] = mapped_column(String(128), nullable=False)
    source_entity_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)
    signal_type: Mapped[str] = mapped_column(String(128), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    __table_args__ = (
        UniqueConstraint("tenant_id", "signal_ref", name="uq_qa_quality_brain_signals_tenant_ref"),
        Index("ix_qa_quality_brain_signals_tenant_status", "tenant_id", "status"),
    )


class QualityAuditEvent(Base):
    __tablename__ = "qa_quality_audit_events"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(128), nullable=False)
    source_entity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    source_entity_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    actor_user_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    previous_status: Mapped[str | None] = mapped_column(String(64), nullable=True)
    new_status: Mapped[str | None] = mapped_column(String(64), nullable=True)
    payload_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict, server_default=sa_text("'{}'::jsonb"))
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=sa_text("NOW()"))
    human_review_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=sa_text("true"))
    provider_integration_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=sa_text("false"))
    hidden_score_present: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=sa_text("false"))
    __table_args__ = (Index("ix_qa_quality_audit_events_tenant_created", "tenant_id", "created_at"),)


class QualityStatusHistory(Base):
    __tablename__ = "qa_quality_status_history"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    source_entity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    source_entity_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    previous_status: Mapped[str | None] = mapped_column(String(64), nullable=True)
    new_status: Mapped[str] = mapped_column(String(64), nullable=False)
    changed_by_user_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict, server_default=sa_text("'{}'::jsonb"))
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=sa_text("NOW()"))
    __table_args__ = (Index("ix_qa_quality_status_history_tenant_created", "tenant_id", "created_at"),)


class QualityLimitation(Base):
    __tablename__ = "qa_quality_limitations"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    source_entity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    source_entity_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    limitation_code: Mapped[str] = mapped_column(String(128), nullable=False)
    limitation_text: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict, server_default=sa_text("'{}'::jsonb"))
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=sa_text("NOW()"))
    __table_args__ = (Index("ix_qa_quality_limitations_tenant_created", "tenant_id", "created_at"),)