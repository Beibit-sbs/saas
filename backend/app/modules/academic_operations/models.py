"""Academic Operations backend foundation SQLAlchemy models."""

from __future__ import annotations

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint, text as sa_text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, declarative_mixin, mapped_column

from app.core.db import Base


MODULE_NAME = "academic_operations"
TABLE_PREFIX = "ao_"
TARGET_LEVEL = "L3"
CONTRACT_VERSION = "A-036.2"
FOUNDATION_STATUS = "MATRIX_GUIDED_CANONICAL_AWARE_BACKEND_FOUNDATION"
MASTER_MATRIX_COMMIT = "c79cc31"
MATRIX_ROW_COUNT = 467
DUPLICATE_MODULE_POLICY = "REUSE_CANONICALS_AND_BRIDGE_ONLY"


class AcademicOperationsStatus:
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    READY_FOR_REUSE = "READY_FOR_REUSE"
    ARCHIVED = "ARCHIVED"
    ALL = frozenset({DRAFT, ACTIVE, REVIEW_REQUIRED, READY_FOR_REUSE, ARCHIVED})


class AcademicOperationsAuditEventType:
    ACADEMIC_GROUP_CREATED = "ACADEMIC_GROUP_CREATED"
    ACADEMIC_GROUP_UPDATED = "ACADEMIC_GROUP_UPDATED"
    COHORT_CREATED = "COHORT_CREATED"
    COHORT_UPDATED = "COHORT_UPDATED"
    COURSE_REGISTRATION_METADATA_CREATED = "COURSE_REGISTRATION_METADATA_CREATED"
    GRADEBOOK_METADATA_CREATED = "GRADEBOOK_METADATA_CREATED"
    GRADEBOOK_METADATA_UPDATED = "GRADEBOOK_METADATA_UPDATED"
    RETAKE_PLAN_CREATED = "RETAKE_PLAN_CREATED"
    RETAKE_PLAN_UPDATED = "RETAKE_PLAN_UPDATED"
    SUMMER_SEMESTER_CREATED = "SUMMER_SEMESTER_CREATED"
    SUMMER_SEMESTER_UPDATED = "SUMMER_SEMESTER_UPDATED"
    ADVISOR_TUTOR_ASSIGNMENT_CREATED = "ADVISOR_TUTOR_ASSIGNMENT_CREATED"
    ADVISOR_TUTOR_ASSIGNMENT_UPDATED = "ADVISOR_TUTOR_ASSIGNMENT_UPDATED"
    CANONICAL_BRIDGE_CREATED = "CANONICAL_BRIDGE_CREATED"
    EVIDENCE_METADATA_ATTACHED = "EVIDENCE_METADATA_ATTACHED"
    DASHBOARD_VIEWED = "DASHBOARD_VIEWED"
    MATRIX_SUMMARY_VIEWED = "MATRIX_SUMMARY_VIEWED"
    HEALTH_VIEWED = "HEALTH_VIEWED"


@declarative_mixin
class AcademicOperationsSafetyMixin:
    tenant_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(64), nullable=False, default=AcademicOperationsStatus.DRAFT, server_default=sa_text("'DRAFT'"))
    human_review_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=sa_text("true"))
    automated_decision: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=sa_text("false"))
    provider_integration_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=sa_text("false"))
    platonus_sync_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=sa_text("false"))
    sis_sync_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=sa_text("false"))
    hidden_score_present: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=sa_text("false"))
    official_grade_publication_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=sa_text("false"))
    automated_grading_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=sa_text("false"))
    automatic_sanction_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=sa_text("false"))
    incomplete_data: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=sa_text("true"))
    limitations_json: Mapped[list] = mapped_column(JSONB, nullable=False, default=list, server_default=sa_text("'[]'::jsonb"))
    source_capability_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    source_matrix_row_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_by_user_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    updated_by_user_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=sa_text("NOW()"))
    updated_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=sa_text("NOW()"))
    archived_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True)


class AcademicOperationsAcademicGroup(Base, AcademicOperationsSafetyMixin):
    __tablename__ = "ao_academic_groups"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    group_code: Mapped[str] = mapped_column(String(64), nullable=False)
    group_name: Mapped[str] = mapped_column(String(255), nullable=False)
    external_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    __table_args__ = (
        UniqueConstraint("tenant_id", "group_code", name="uq_ao_academic_groups_tenant_code"),
        Index("ix_ao_academic_groups_tenant_status", "tenant_id", "status"),
    )


class AcademicOperationsCohort(Base, AcademicOperationsSafetyMixin):
    __tablename__ = "ao_cohorts"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    cohort_code: Mapped[str] = mapped_column(String(64), nullable=False)
    cohort_name: Mapped[str] = mapped_column(String(255), nullable=False)
    academic_group_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    __table_args__ = (
        UniqueConstraint("tenant_id", "cohort_code", name="uq_ao_cohorts_tenant_code"),
        Index("ix_ao_cohorts_tenant_status", "tenant_id", "status"),
    )


class AcademicOperationsCourseRegistrationMetadata(Base, AcademicOperationsSafetyMixin):
    __tablename__ = "ao_course_registration_metadata"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    student_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)
    course_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)
    canonical_module_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict, server_default=sa_text("'{}'::jsonb"))
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    __table_args__ = (Index("ix_ao_course_registration_tenant_status", "tenant_id", "status"),)


class AcademicOperationsGradebookMetadata(Base, AcademicOperationsSafetyMixin):
    __tablename__ = "ao_gradebook_metadata"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    student_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)
    course_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)
    gradebook_key: Mapped[str] = mapped_column(String(128), nullable=False)
    metadata_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict, server_default=sa_text("'{}'::jsonb"))
    __table_args__ = (
        UniqueConstraint("tenant_id", "gradebook_key", name="uq_ao_gradebook_metadata_tenant_key"),
        Index("ix_ao_gradebook_metadata_tenant_status", "tenant_id", "status"),
    )


class AcademicOperationsRetakePlan(Base, AcademicOperationsSafetyMixin):
    __tablename__ = "ao_retake_plans"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    student_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)
    course_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)
    plan_code: Mapped[str] = mapped_column(String(128), nullable=False)
    retake_window: Mapped[str | None] = mapped_column(String(128), nullable=True)
    __table_args__ = (
        UniqueConstraint("tenant_id", "plan_code", name="uq_ao_retake_plans_tenant_code"),
        Index("ix_ao_retake_plans_tenant_status", "tenant_id", "status"),
    )


class AcademicOperationsSummerSemesterTerm(Base, AcademicOperationsSafetyMixin):
    __tablename__ = "ao_summer_semester_terms"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    term_code: Mapped[str] = mapped_column(String(64), nullable=False)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    calendar_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)
    __table_args__ = (
        UniqueConstraint("tenant_id", "term_code", name="uq_ao_summer_terms_tenant_code"),
        Index("ix_ao_summer_terms_tenant_status", "tenant_id", "status"),
    )


class AcademicOperationsAdvisorTutorAssignment(Base, AcademicOperationsSafetyMixin):
    __tablename__ = "ao_advisor_tutor_assignments"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    student_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)
    faculty_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)
    assignment_code: Mapped[str] = mapped_column(String(128), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    __table_args__ = (
        UniqueConstraint("tenant_id", "assignment_code", name="uq_ao_advisor_tutor_assignments_tenant_code"),
        Index("ix_ao_advisor_tutor_tenant_status", "tenant_id", "status"),
    )


class AcademicOperationsCanonicalModuleBridge(Base, AcademicOperationsSafetyMixin):
    __tablename__ = "ao_canonical_module_bridges"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    bridge_type: Mapped[str] = mapped_column(String(64), nullable=False)
    canonical_module_ref: Mapped[str] = mapped_column(String(128), nullable=False)
    external_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict, server_default=sa_text("'{}'::jsonb"))
    __table_args__ = (Index("ix_ao_canonical_bridges_tenant_type", "tenant_id", "bridge_type"),)


class AcademicOperationsStudentLifecycleBridgeMetadata(Base, AcademicOperationsSafetyMixin):
    __tablename__ = "ao_student_lifecycle_bridge_metadata"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    bridge_key: Mapped[str] = mapped_column(String(128), nullable=False)
    student_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict, server_default=sa_text("'{}'::jsonb"))
    __table_args__ = (Index("ix_ao_student_lifecycle_bridge_tenant_status", "tenant_id", "status"),)


class AcademicOperationsDocumentWorkflowBridgeMetadata(Base, AcademicOperationsSafetyMixin):
    __tablename__ = "ao_document_workflow_bridge_metadata"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    bridge_key: Mapped[str] = mapped_column(String(128), nullable=False)
    external_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict, server_default=sa_text("'{}'::jsonb"))
    __table_args__ = (Index("ix_ao_document_bridge_tenant_status", "tenant_id", "status"),)


class AcademicOperationsExecutiveGovernanceBridgeMetadata(Base, AcademicOperationsSafetyMixin):
    __tablename__ = "ao_executive_governance_bridge_metadata"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    bridge_key: Mapped[str] = mapped_column(String(128), nullable=False)
    external_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict, server_default=sa_text("'{}'::jsonb"))
    __table_args__ = (Index("ix_ao_executive_bridge_tenant_status", "tenant_id", "status"),)


class AcademicOperationsQualityAccreditationBridgeMetadata(Base, AcademicOperationsSafetyMixin):
    __tablename__ = "ao_quality_accreditation_bridge_metadata"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    bridge_key: Mapped[str] = mapped_column(String(128), nullable=False)
    external_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict, server_default=sa_text("'{}'::jsonb"))
    __table_args__ = (Index("ix_ao_quality_bridge_tenant_status", "tenant_id", "status"),)


class AcademicOperationsDashboardSnapshot(Base):
    __tablename__ = "ao_academic_operations_dashboard_snapshots"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(64), nullable=False, default=AcademicOperationsStatus.ACTIVE, server_default=sa_text("'ACTIVE'"))
    fake_metrics: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=sa_text("false"))
    incomplete_data: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=sa_text("true"))
    data_source: Mapped[str] = mapped_column(String(128), nullable=False, default="computed_from_academic_operations_metadata", server_default=sa_text("'computed_from_academic_operations_metadata'"))
    summary_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict, server_default=sa_text("'{}'::jsonb"))
    limitations_json: Mapped[list] = mapped_column(JSONB, nullable=False, default=list, server_default=sa_text("'[]'::jsonb"))
    source_capability_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    source_matrix_row_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=sa_text("NOW()"))
    __table_args__ = (Index("ix_ao_dashboard_snapshots_tenant_status", "tenant_id", "status"),)


class AcademicOperationsAuditEvent(Base):
    __tablename__ = "ao_academic_operations_audit_events"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    event_type: Mapped[str] = mapped_column(String(128), nullable=False)
    action: Mapped[str] = mapped_column(String(128), nullable=False)
    actor_user_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    previous_status: Mapped[str | None] = mapped_column(String(64), nullable=True)
    new_status: Mapped[str | None] = mapped_column(String(64), nullable=True)
    human_review_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=sa_text("true"))
    automated_decision: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=sa_text("false"))
    provider_integration_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=sa_text("false"))
    payload_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict, server_default=sa_text("'{}'::jsonb"))
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=sa_text("NOW()"))
    __table_args__ = (Index("ix_ao_audit_events_tenant_entity", "tenant_id", "entity_type"),)


class AcademicOperationsEvidenceMetadata(Base, AcademicOperationsSafetyMixin):
    __tablename__ = "ao_academic_operations_evidence_metadata"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    evidence_kind: Mapped[str] = mapped_column(String(128), nullable=False)
    external_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict, server_default=sa_text("'{}'::jsonb"))
    __table_args__ = (Index("ix_ao_evidence_tenant_entity", "tenant_id", "entity_type"),)


class AcademicOperationsLimitation(Base):
    __tablename__ = "ao_academic_operations_limitations"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    limitation_code: Mapped[str] = mapped_column(String(128), nullable=False)
    limitation_text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=sa_text("NOW()"))
    __table_args__ = (Index("ix_ao_limitations_tenant_entity", "tenant_id", "entity_type"),)


class AcademicOperationsStatusHistory(Base):
    __tablename__ = "ao_academic_operations_status_history"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    previous_status: Mapped[str | None] = mapped_column(String(64), nullable=True)
    new_status: Mapped[str] = mapped_column(String(64), nullable=False)
    actor_user_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=sa_text("NOW()"))
    __table_args__ = (Index("ix_ao_status_history_tenant_entity", "tenant_id", "entity_type", "entity_id"),)


class AcademicOperationsGradebookStatusHistory(Base):
    __tablename__ = "ao_gradebook_status_history"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    gradebook_metadata_id: Mapped[int] = mapped_column(ForeignKey("ao_gradebook_metadata.id"), nullable=False)
    previous_status: Mapped[str | None] = mapped_column(String(64), nullable=True)
    new_status: Mapped[str] = mapped_column(String(64), nullable=False)
    actor_user_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=sa_text("NOW()"))
    __table_args__ = (Index("ix_ao_gradebook_status_history_tenant_gradebook", "tenant_id", "gradebook_metadata_id"),)


class AcademicOperationsRetakeStatusHistory(Base):
    __tablename__ = "ao_retake_status_history"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    retake_plan_id: Mapped[int] = mapped_column(ForeignKey("ao_retake_plans.id"), nullable=False)
    previous_status: Mapped[str | None] = mapped_column(String(64), nullable=True)
    new_status: Mapped[str] = mapped_column(String(64), nullable=False)
    actor_user_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=sa_text("NOW()"))
    __table_args__ = (Index("ix_ao_retake_status_history_tenant_retake", "tenant_id", "retake_plan_id"),)