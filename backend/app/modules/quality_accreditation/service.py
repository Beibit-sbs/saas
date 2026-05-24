"""Quality / Accreditation service layer."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.orm import Session

from app.core.module_helpers.service_validation import DomainValidationError
from app.modules.quality_accreditation import models, repository
from app.modules.quality_accreditation.dependencies import validate_tenant_id
from app.modules.quality_accreditation.schemas import (
    QualityDashboardResponse,
    QualityHealthResponse,
    QualityLimitationsResponse,
    QualityMatrixSummaryResponse,
    QualityOverviewResponse,
)


PROVIDER_INTEGRATION_ENABLED = False
EXTERNAL_DATABASE_SYNC_ENABLED = False
OFFICIAL_ACCREDITATION_APPROVAL_ENABLED = False
OFFICIAL_MINISTRY_SUBMISSION_ENABLED = False
OFFICIAL_RANKING_CLAIM_ENABLED = False
AUTOMATIC_ACCREDITATION_DECISION_ENABLED = False
HIDDEN_SCORE_PRESENT = False
FAKE_METRICS = False
FAKE_EVIDENCE = False
HUMAN_REVIEW_REQUIRED = True
SOURCE_BACKEND_SPEC_COMMIT = models.SOURCE_SPEC_COMMIT
SOURCE_PRODUCT_MAP_COMMIT = models.SOURCE_PRODUCT_MAP_COMMIT
RUNTIME_MODE = models.RUNTIME_MODE
EXPECTED_ROUTE_COUNT = 70
EXPECTED_TABLE_COUNT = 32
EXPECTED_PERMISSION_COUNT = 55

REQUIRED_LIMITATIONS = [
    "metadata_only_foundation",
    "evidence_metadata_only",
    "no_official_accreditation_approval",
    "no_official_ministry_submission",
    "no_official_ranking_claim",
    "no_provider_integration",
    "no_external_database_sync",
    "human_review_required",
]


@dataclass(frozen=True)
class ResourceConfig:
    key: str
    model: Any
    ref_field: str | None
    source_entity_type: str
    create_event: str
    update_event: str
    default_status: str = models.QualityFrameworkStatus.DRAFT
    title_fallback: str = "Metadata Record"


RESOURCE_CONFIGS: dict[str, ResourceConfig] = {
    "frameworks": ResourceConfig("frameworks", models.QualityFramework, "framework_ref", "quality_framework", models.QualityAuditEventType.FRAMEWORK_CREATED, models.QualityAuditEventType.FRAMEWORK_UPDATED, title_fallback="Quality Framework"),
    "standards": ResourceConfig("standards", models.AccreditationStandard, "standard_ref", "accreditation_standard", models.QualityAuditEventType.STANDARD_CREATED, models.QualityAuditEventType.STANDARD_CREATED, default_status=models.AccreditationStandardStatus.DRAFT, title_fallback="Accreditation Standard"),
    "criteria": ResourceConfig("criteria", models.StandardCriterion, "criterion_ref", "standard_criterion", models.QualityAuditEventType.CRITERION_CREATED, models.QualityAuditEventType.CRITERION_CREATED, title_fallback="Standard Criterion"),
    "standards_evidence_requirements": ResourceConfig("standards_evidence_requirements", models.StandardsEvidenceRequirement, "requirement_ref", "evidence_requirement", models.QualityAuditEventType.CRITERION_CREATED, models.QualityAuditEventType.CRITERION_CREATED, title_fallback="Evidence Requirement"),
    "evidence": ResourceConfig("evidence", models.QualityEvidenceRegistry, "evidence_ref", "quality_evidence", models.QualityAuditEventType.EVIDENCE_REGISTERED, models.QualityAuditEventType.EVIDENCE_REGISTERED, default_status=models.EvidenceReviewStatus.DRAFT, title_fallback="Quality Evidence"),
    "evidence_limitations": ResourceConfig("evidence_limitations", models.EvidenceLimitation, "limitation_ref", "evidence_limitation", models.QualityAuditEventType.LIMITATION_ACKNOWLEDGED, models.QualityAuditEventType.LIMITATION_ACKNOWLEDGED, title_fallback="Evidence Limitation"),
    "program_readiness": ResourceConfig("program_readiness", models.ProgramAccreditationReadiness, "readiness_ref", "program_readiness", models.QualityAuditEventType.PROGRAM_READINESS_UPDATED, models.QualityAuditEventType.PROGRAM_READINESS_UPDATED, default_status=models.ReadinessStatus.NOT_STARTED, title_fallback="Program Readiness"),
    "institutional_readiness": ResourceConfig("institutional_readiness", models.InstitutionalAccreditationReadiness, "readiness_ref", "institutional_readiness", models.QualityAuditEventType.INSTITUTIONAL_READINESS_UPDATED, models.QualityAuditEventType.INSTITUTIONAL_READINESS_UPDATED, default_status=models.ReadinessStatus.NOT_STARTED, title_fallback="Institutional Readiness"),
    "self_assessment": ResourceConfig("self_assessment", models.SelfAssessmentReport, "report_ref", "self_assessment_report", models.QualityAuditEventType.SELF_ASSESSMENT_CREATED, models.QualityAuditEventType.SELF_ASSESSMENT_CREATED, default_status=models.SelfAssessmentStatus.DRAFT, title_fallback="Self Assessment Report"),
    "self_assessment_sections": ResourceConfig("self_assessment_sections", models.SelfAssessmentSection, "section_ref", "self_assessment_section", models.QualityAuditEventType.SELF_ASSESSMENT_SECTION_UPDATED, models.QualityAuditEventType.SELF_ASSESSMENT_SECTION_UPDATED, default_status=models.SelfAssessmentStatus.DRAFT, title_fallback="Self Assessment Section"),
    "improvement_plans": ResourceConfig("improvement_plans", models.QualityImprovementPlan, "plan_ref", "quality_improvement_plan", models.QualityAuditEventType.IMPROVEMENT_PLAN_CREATED, models.QualityAuditEventType.IMPROVEMENT_PLAN_CREATED, default_status=models.ImprovementPlanStatus.DRAFT, title_fallback="Improvement Plan"),
    "improvement_actions": ResourceConfig("improvement_actions", models.QualityImprovementAction, "action_ref", "quality_improvement_action", models.QualityAuditEventType.IMPROVEMENT_ACTION_UPDATED, models.QualityAuditEventType.IMPROVEMENT_ACTION_UPDATED, default_status=models.ImprovementPlanStatus.DRAFT, title_fallback="Improvement Action"),
    "internal_audits": ResourceConfig("internal_audits", models.InternalQualityAudit, "audit_ref", "internal_quality_audit", models.QualityAuditEventType.INTERNAL_AUDIT_CREATED, models.QualityAuditEventType.INTERNAL_AUDIT_CREATED, default_status=models.InternalAuditStatus.PLANNED, title_fallback="Internal Quality Audit"),
    "audit_findings": ResourceConfig("audit_findings", models.QualityAuditFinding, "finding_ref", "quality_audit_finding", models.QualityAuditEventType.AUDIT_FINDING_RECORDED, models.QualityAuditEventType.AUDIT_FINDING_RECORDED, default_status=models.InternalAuditStatus.FINDINGS_RECORDED, title_fallback="Audit Finding"),
    "program_review": ResourceConfig("program_review", models.ProgramReviewCycle, "cycle_ref", "program_review_cycle", models.QualityAuditEventType.PROGRAM_REVIEW_CREATED, models.QualityAuditEventType.PROGRAM_REVIEW_CREATED, title_fallback="Program Review"),
    "learning_outcomes": ResourceConfig("learning_outcomes", models.LearningOutcomesAssessment, "assessment_ref", "learning_outcomes_assessment", models.QualityAuditEventType.PROGRAM_REVIEW_CREATED, models.QualityAuditEventType.PROGRAM_REVIEW_CREATED, title_fallback="Learning Outcomes Assessment"),
    "stakeholder_feedback": ResourceConfig("stakeholder_feedback", models.StakeholderFeedbackMetadata, "feedback_ref", "stakeholder_feedback_metadata", models.QualityAuditEventType.STAKEHOLDER_FEEDBACK_METADATA_ADDED, models.QualityAuditEventType.STAKEHOLDER_FEEDBACK_METADATA_ADDED, title_fallback="Stakeholder Feedback"),
    "external_review": ResourceConfig("external_review", models.ExternalExpertReview, "review_ref", "external_expert_review", models.QualityAuditEventType.EXTERNAL_REVIEW_METADATA_ADDED, models.QualityAuditEventType.EXTERNAL_REVIEW_METADATA_ADDED, title_fallback="External Expert Review"),
    "expert_response_plans": ResourceConfig("expert_response_plans", models.ExpertRecommendationResponsePlan, "response_plan_ref", "expert_recommendation_response_plan", models.QualityAuditEventType.EXTERNAL_REVIEW_METADATA_ADDED, models.QualityAuditEventType.EXTERNAL_REVIEW_METADATA_ADDED, title_fallback="Expert Response Plan"),
    "committee": ResourceConfig("committee", models.AccreditationCommitteeWorkflow, "workflow_ref", "committee_workflow", models.QualityAuditEventType.COMMITTEE_WORKFLOW_UPDATED, models.QualityAuditEventType.COMMITTEE_WORKFLOW_UPDATED, title_fallback="Committee Workflow"),
    "gap_analysis": ResourceConfig("gap_analysis", models.ComplianceGapAnalysis, "gap_ref", "compliance_gap_analysis", models.QualityAuditEventType.GAP_ANALYSIS_UPDATED, models.QualityAuditEventType.GAP_ANALYSIS_UPDATED, title_fallback="Compliance Gap"),
    "calendar": ResourceConfig("calendar", models.AccreditationCalendar, "calendar_ref", "accreditation_calendar", models.QualityAuditEventType.GAP_ANALYSIS_UPDATED, models.QualityAuditEventType.GAP_ANALYSIS_UPDATED, title_fallback="Accreditation Calendar"),
    "risk_register": ResourceConfig("risk_register", models.QualityRiskRegister, "risk_ref", "quality_risk", models.QualityAuditEventType.GAP_ANALYSIS_UPDATED, models.QualityAuditEventType.GAP_ANALYSIS_UPDATED, title_fallback="Quality Risk"),
    "bridges": ResourceConfig("bridges", models.QualityBridgeMetadata, "bridge_ref", "quality_bridge", models.QualityAuditEventType.BRIDGE_CREATED, models.QualityAuditEventType.BRIDGE_CREATED, default_status=models.BridgeStatus.DRAFT, title_fallback="Quality Bridge"),
    "brain_signals": ResourceConfig("brain_signals", models.QualityBrainSignal, "signal_ref", "quality_brain_signal", models.QualityAuditEventType.BRAIN_SIGNAL_RECORDED, models.QualityAuditEventType.BRAIN_SIGNAL_RECORDED, title_fallback="Quality Brain Signal"),
}


def _now() -> datetime:
    return datetime.now(UTC)


def _validate_actor(actor_user_id: str | int | None) -> str:
    actor = str(actor_user_id or "").strip()
    if not actor:
        raise DomainValidationError("actor_user_id is required")
    return actor


def _commit(db: Session):
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise


def _merge_limitations(values: list[str] | None) -> list[str]:
    merged = list(values or [])
    for item in REQUIRED_LIMITATIONS:
        if item not in merged:
            merged.append(item)
    return merged


def _base_safety_defaults(actor: str | None = None, source_capability_id: str | None = None, source_family_id: str | None = None) -> dict[str, Any]:
    return {
        "human_review_required": True,
        "official_accreditation_approval_enabled": False,
        "official_ministry_submission_enabled": False,
        "official_ranking_claim_enabled": False,
        "automatic_accreditation_decision_enabled": False,
        "provider_integration_enabled": False,
        "external_database_sync_enabled": False,
        "hidden_score_present": False,
        "autonomous_decision": False,
        "incomplete_data": True,
        "created_by_user_id": actor,
        "updated_by_user_id": actor,
        "source_capability_id": source_capability_id,
        "source_family_id": source_family_id,
    }


def _generate_ref(prefix: str, tenant_id: int) -> str:
    return f"{prefix.upper()}-{tenant_id}-{int(_now().timestamp() * 1000)}"


def _normalize_request_payload(request, config: ResourceConfig, actor: str, *, for_update: bool = False) -> dict[str, Any]:
    payload = request.model_dump(exclude_none=True)
    payload["limitations_json"] = _merge_limitations(payload.pop("limitations", None))
    payload["metadata_json"] = payload.pop("metadata", {})
    if for_update:
        payload["updated_by_user_id"] = actor
    else:
        payload |= _base_safety_defaults(actor, payload.get("source_capability_id"), payload.get("source_family_id"))
    payload["provider_integration_enabled"] = False
    payload["external_database_sync_enabled"] = False
    payload["official_accreditation_approval_enabled"] = False
    payload["official_ministry_submission_enabled"] = False
    payload["official_ranking_claim_enabled"] = False
    payload["automatic_accreditation_decision_enabled"] = False
    payload["hidden_score_present"] = False
    payload["autonomous_decision"] = False
    payload["incomplete_data"] = True
    if "title" not in payload and not for_update:
        payload["title"] = config.title_fallback
    if config.ref_field and config.ref_field not in payload and not for_update:
        payload[config.ref_field] = _generate_ref(config.key, validate_tenant_id(payload.get("tenant_id", 1) if isinstance(payload.get("tenant_id"), int) else 1))
    if "status" not in payload and not for_update:
        payload["status"] = config.default_status
    return payload


def _audit(
    db: Session,
    tenant_id: int,
    *,
    source_entity_type: str,
    source_entity_id: int | None,
    event_type: str,
    actor_user_id: str,
    previous_status: str | None = None,
    new_status: str | None = None,
    payload: dict[str, Any] | None = None,
) -> None:
    repository.create_quality_audit_event(
        db,
        tenant_id,
        event_type=event_type,
        source_entity_type=source_entity_type,
        source_entity_id=source_entity_id,
        actor_user_id=actor_user_id,
        previous_status=previous_status,
        new_status=new_status,
        payload_json=payload or {},
        human_review_required=True,
        provider_integration_enabled=False,
        hidden_score_present=False,
    )


def _status_history(db: Session, tenant_id: int, *, source_entity_type: str, source_entity_id: int | None, previous_status: str | None, new_status: str, actor_user_id: str) -> None:
    repository.create_quality_status_history(
        db,
        tenant_id,
        source_entity_type=source_entity_type,
        source_entity_id=source_entity_id,
        previous_status=previous_status,
        new_status=new_status,
        changed_by_user_id=actor_user_id,
        metadata_json={},
    )


def create_resource_service(db: Session, tenant_id: int, actor_user_id: str, resource_key: str, request):
    tenant_id = validate_tenant_id(tenant_id)
    actor = _validate_actor(actor_user_id)
    config = RESOURCE_CONFIGS[resource_key]
    payload = _normalize_request_payload(request, config, actor)
    if config.ref_field and config.ref_field not in payload:
        payload[config.ref_field] = _generate_ref(config.key, tenant_id)
    entity = repository.create_resource(db, config.model, tenant_id, **payload)
    _audit(db, tenant_id, source_entity_type=config.source_entity_type, source_entity_id=entity.id, event_type=config.create_event, actor_user_id=actor, new_status=getattr(entity, "status", None))
    if hasattr(entity, "status"):
        _status_history(db, tenant_id, source_entity_type=config.source_entity_type, source_entity_id=entity.id, previous_status=None, new_status=entity.status, actor_user_id=actor)
    _commit(db)
    return entity


def list_resource_service(db: Session, tenant_id: int, resource_key: str):
    tenant_id = validate_tenant_id(tenant_id)
    config = RESOURCE_CONFIGS[resource_key]
    return repository.list_resources(db, config.model, tenant_id)


def update_resource_service(db: Session, tenant_id: int, actor_user_id: str, resource_key: str, resource_id: int, request):
    tenant_id = validate_tenant_id(tenant_id)
    actor = _validate_actor(actor_user_id)
    config = RESOURCE_CONFIGS[resource_key]
    current = repository.get_resource(db, config.model, tenant_id, resource_id)
    if current is None:
        raise DomainValidationError(f"{config.source_entity_type} {resource_id} not found in tenant scope")
    payload = _normalize_request_payload(request, config, actor, for_update=True)
    entity = repository.update_resource(db, config.model, tenant_id, resource_id, **payload)
    _audit(db, tenant_id, source_entity_type=config.source_entity_type, source_entity_id=entity.id, event_type=config.update_event, actor_user_id=actor, previous_status=getattr(current, "status", None), new_status=getattr(entity, "status", None))
    if hasattr(entity, "status") and getattr(current, "status", None) != getattr(entity, "status", None):
        _status_history(db, tenant_id, source_entity_type=config.source_entity_type, source_entity_id=entity.id, previous_status=current.status, new_status=entity.status, actor_user_id=actor)
    _commit(db)
    return entity


def review_evidence_service(db: Session, tenant_id: int, actor_user_id: str, evidence_id: int, request):
    tenant_id = validate_tenant_id(tenant_id)
    actor = _validate_actor(actor_user_id)
    evidence = repository.get_resource(db, models.QualityEvidenceRegistry, tenant_id, evidence_id)
    if evidence is None:
        raise DomainValidationError(f"quality_evidence {evidence_id} not found in tenant scope")
    payload = request.model_dump(exclude_none=True)
    payload["review_ref"] = payload.get("review_ref") or _generate_ref("evidence_review", tenant_id)
    payload["evidence_ref"] = getattr(evidence, "evidence_ref", None)
    payload["status"] = payload.get("status") or models.EvidenceReviewStatus.REVIEWED_METADATA_ONLY
    payload["limitations_json"] = _merge_limitations(payload.pop("limitations", None))
    payload["metadata_json"] = payload.pop("metadata", {})
    payload |= _base_safety_defaults(actor)
    entity = repository.create_resource(db, models.EvidenceReview, tenant_id, **payload)
    repository.update_resource(db, models.QualityEvidenceRegistry, tenant_id, evidence_id, status=payload["status"], updated_by_user_id=actor)
    _audit(db, tenant_id, source_entity_type="quality_evidence", source_entity_id=evidence_id, event_type=models.QualityAuditEventType.EVIDENCE_REVIEWED, actor_user_id=actor, previous_status=getattr(evidence, "status", None), new_status=payload["status"])
    _status_history(db, tenant_id, source_entity_type="quality_evidence", source_entity_id=evidence_id, previous_status=getattr(evidence, "status", None), new_status=payload["status"], actor_user_id=actor)
    _commit(db)
    return entity


def get_quality_overview_service(db: Session, tenant_id: int) -> QualityOverviewResponse:
    tenant_id = validate_tenant_id(tenant_id)
    health = repository.get_health_summary(db, tenant_id)
    return QualityOverviewResponse(
        tenant_id=tenant_id,
        module=models.MODULE_NAME,
        product_vertical=models.PRODUCT_VERTICAL,
        contract_version=models.CONTRACT_VERSION,
        runtime_mode=models.RUNTIME_MODE,
        table_count=EXPECTED_TABLE_COUNT,
        route_count=EXPECTED_ROUTE_COUNT,
        readiness_items=health["readiness_items"],
        evidence_items=health["evidence_items"],
        bridge_items=health["bridge_items"],
        limitations=list(REQUIRED_LIMITATIONS),
        boundary_summary={
            "provider_integration_enabled": False,
            "external_database_sync_enabled": False,
            "official_accreditation_approval_enabled": False,
            "official_ministry_submission_enabled": False,
            "official_ranking_claim_enabled": False,
            "hidden_score_present": False,
        },
    )


def get_quality_health_service(db: Session, tenant_id: int) -> QualityHealthResponse:
    validate_tenant_id(tenant_id)
    return QualityHealthResponse(
        tenant_id=tenant_id,
        module=models.MODULE_NAME,
        target_level=models.TARGET_LEVEL,
        foundation_status=models.FOUNDATION_STATUS,
        runtime_mode=models.RUNTIME_MODE,
        contract_version=models.CONTRACT_VERSION,
        provider_integration_enabled=False,
        external_database_sync_enabled=False,
        official_accreditation_approval_enabled=False,
        official_ministry_submission_enabled=False,
        official_ranking_claim_enabled=False,
        hidden_score_present=False,
        fake_metrics=False,
        incomplete_data=True,
        limitations=list(REQUIRED_LIMITATIONS),
        route_count=EXPECTED_ROUTE_COUNT,
        table_count=EXPECTED_TABLE_COUNT,
    )


def get_quality_dashboard_service(db: Session, tenant_id: int) -> QualityDashboardResponse:
    tenant_id = validate_tenant_id(tenant_id)
    summary = repository.compute_dashboard_summary(db, tenant_id)
    result = QualityDashboardResponse(
        tenant_id=tenant_id,
        generated_at=_now(),
        contract_version=models.CONTRACT_VERSION,
        source_spec_commit=models.SOURCE_SPEC_COMMIT,
        source_product_map_commit=models.SOURCE_PRODUCT_MAP_COMMIT,
        source_vertical_selection_commit=models.SOURCE_VERTICAL_SELECTION_COMMIT,
        master_matrix_commit=models.MASTER_MATRIX_COMMIT,
        master_matrix_rows=models.MASTER_MATRIX_ROW_COUNT,
        detailed_capability_count=models.DETAILED_CAPABILITY_COUNT,
        capability_family_count=models.CAPABILITY_FAMILY_COUNT,
        data_source=models.DATA_SOURCE,
        fake_metrics=False,
        incomplete_data=False,
        limitations=list(REQUIRED_LIMITATIONS),
        frameworks_summary=summary["frameworks_summary"],
        standards_summary=summary["standards_summary"],
        evidence_summary=summary["evidence_summary"],
        readiness_summary=summary["readiness_summary"],
        self_assessment_summary=summary["self_assessment_summary"],
        improvement_summary=summary["improvement_summary"],
        audit_summary=summary["audit_summary"],
        program_review_summary=summary["program_review_summary"],
        bridge_summary=summary["bridge_summary"],
        brain_signal_summary=summary["brain_signal_summary"],
        boundary_summary={
            "provider_integration_enabled": False,
            "external_database_sync_enabled": False,
            "official_accreditation_approval_enabled": False,
            "official_ministry_submission_enabled": False,
            "official_ranking_claim_enabled": False,
            "hidden_score_present": False,
            "fake_metrics": False,
        },
    )
    repository.create_dashboard_snapshot(
        db,
        tenant_id,
        status=models.QualityFrameworkStatus.ACTIVE_METADATA_ONLY,
        fake_metrics=False,
        incomplete_data=False,
        data_source=models.DATA_SOURCE,
        summary_json=result.model_dump(mode="json"),
        limitations_json=list(REQUIRED_LIMITATIONS),
    )
    _audit(db, tenant_id, source_entity_type="quality_dashboard", source_entity_id=None, event_type=models.QualityAuditEventType.DASHBOARD_SNAPSHOT_CREATED, actor_user_id="system", new_status=models.QualityFrameworkStatus.ACTIVE_METADATA_ONLY)
    _commit(db)
    return result


def get_quality_matrix_summary_service(db: Session, tenant_id: int) -> QualityMatrixSummaryResponse:
    del db
    validate_tenant_id(tenant_id)
    return QualityMatrixSummaryResponse(
        contract_version=models.CONTRACT_VERSION,
        source_spec_commit=models.SOURCE_SPEC_COMMIT,
        source_product_map_commit=models.SOURCE_PRODUCT_MAP_COMMIT,
        source_vertical_selection_commit=models.SOURCE_VERTICAL_SELECTION_COMMIT,
        master_matrix_commit=models.MASTER_MATRIX_COMMIT,
        master_matrix_rows=models.MASTER_MATRIX_ROW_COUNT,
        detailed_capability_count=models.DETAILED_CAPABILITY_COUNT,
        capability_family_count=models.CAPABILITY_FAMILY_COUNT,
        runtime_mode=models.RUNTIME_MODE,
        route_count_expected="55-70",
        table_count_expected=EXPECTED_TABLE_COUNT,
        permission_count_expected=EXPECTED_PERMISSION_COUNT,
    )


def list_quality_limitations_service(db: Session, tenant_id: int) -> QualityLimitationsResponse:
    tenant_id = validate_tenant_id(tenant_id)
    rows = repository.list_quality_limitations(db, tenant_id)
    if not rows:
        return QualityLimitationsResponse(items=list(REQUIRED_LIMITATIONS))
    return QualityLimitationsResponse(items=[row.limitation_text for row in rows])


def list_quality_audit_events_service(db: Session, tenant_id: int):
    return repository.list_quality_audit_events(db, validate_tenant_id(tenant_id))


def list_quality_status_history_service(db: Session, tenant_id: int):
    return repository.list_quality_status_history(db, validate_tenant_id(tenant_id))