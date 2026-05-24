"""Quality / Accreditation repository helpers."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from app.core.module_helpers.service_validation import TenantResourceNotFoundError
from app.modules.quality_accreditation import models


RESOURCE_MODELS = {
    "frameworks": models.QualityFramework,
    "policies": models.QualityPolicyRegistry,
    "standards": models.AccreditationStandard,
    "criteria": models.StandardCriterion,
    "standards_evidence_requirements": models.StandardsEvidenceRequirement,
    "evidence": models.QualityEvidenceRegistry,
    "evidence_reviews": models.EvidenceReview,
    "evidence_limitations": models.EvidenceLimitation,
    "program_readiness": models.ProgramAccreditationReadiness,
    "institutional_readiness": models.InstitutionalAccreditationReadiness,
    "self_assessment": models.SelfAssessmentReport,
    "self_assessment_sections": models.SelfAssessmentSection,
    "improvement_plans": models.QualityImprovementPlan,
    "improvement_actions": models.QualityImprovementAction,
    "internal_audits": models.InternalQualityAudit,
    "audit_findings": models.QualityAuditFinding,
    "program_review": models.ProgramReviewCycle,
    "learning_outcomes": models.LearningOutcomesAssessment,
    "stakeholder_feedback": models.StakeholderFeedbackMetadata,
    "survey_quality": models.SurveyQualityMetadata,
    "external_review": models.ExternalExpertReview,
    "expert_response_plans": models.ExpertRecommendationResponsePlan,
    "committee": models.AccreditationCommitteeWorkflow,
    "gap_analysis": models.ComplianceGapAnalysis,
    "calendar": models.AccreditationCalendar,
    "risk_register": models.QualityRiskRegister,
    "bridges": models.QualityBridgeMetadata,
    "dashboard_snapshots": models.QualityDashboardSnapshot,
    "brain_signals": models.QualityBrainSignal,
}


def _now() -> datetime:
    return datetime.now(UTC)


def _require(resource: object | None, tenant_id: int, resource_name: str, resource_id: int) -> object:
    if resource is None:
        raise TenantResourceNotFoundError(f"{resource_name} {resource_id} not found for tenant {tenant_id}")
    return resource


def create_resource(db: Session, model, tenant_id: int, **kwargs):
    obj = model(tenant_id=tenant_id, created_at=_now(), updated_at=_now(), **kwargs)
    db.add(obj)
    db.flush()
    db.refresh(obj)
    return obj


def get_resource(db: Session, model, tenant_id: int, resource_id: int):
    return db.execute(select(model).where(and_(model.tenant_id == tenant_id, model.id == resource_id))).scalar_one_or_none()


def list_resources(db: Session, model, tenant_id: int):
    order_column = getattr(model, "created_at", None)
    query = select(model).where(model.tenant_id == tenant_id)
    if order_column is not None:
        query = query.order_by(order_column.desc())
    return list(db.execute(query).scalars().all())


def update_resource(db: Session, model, tenant_id: int, resource_id: int, **kwargs):
    resource = _require(get_resource(db, model, tenant_id, resource_id), tenant_id, model.__tablename__, resource_id)
    for key, value in kwargs.items():
        setattr(resource, key, value)
    if hasattr(resource, "updated_at"):
        resource.updated_at = _now()
    db.flush()
    db.refresh(resource)
    return resource


def create_quality_audit_event(db: Session, tenant_id: int, **kwargs) -> models.QualityAuditEvent:
    obj = models.QualityAuditEvent(tenant_id=tenant_id, created_at=_now(), **kwargs)
    db.add(obj)
    db.flush()
    db.refresh(obj)
    return obj


def list_quality_audit_events(db: Session, tenant_id: int) -> list[models.QualityAuditEvent]:
    return list(
        db.execute(
            select(models.QualityAuditEvent)
            .where(models.QualityAuditEvent.tenant_id == tenant_id)
            .order_by(models.QualityAuditEvent.created_at.desc())
        ).scalars().all()
    )


def create_quality_status_history(db: Session, tenant_id: int, **kwargs) -> models.QualityStatusHistory:
    obj = models.QualityStatusHistory(tenant_id=tenant_id, created_at=_now(), **kwargs)
    db.add(obj)
    db.flush()
    db.refresh(obj)
    return obj


def list_quality_status_history(db: Session, tenant_id: int) -> list[models.QualityStatusHistory]:
    return list(
        db.execute(
            select(models.QualityStatusHistory)
            .where(models.QualityStatusHistory.tenant_id == tenant_id)
            .order_by(models.QualityStatusHistory.created_at.desc())
        ).scalars().all()
    )


def create_quality_limitation(db: Session, tenant_id: int, **kwargs) -> models.QualityLimitation:
    obj = models.QualityLimitation(tenant_id=tenant_id, created_at=_now(), **kwargs)
    db.add(obj)
    db.flush()
    db.refresh(obj)
    return obj


def list_quality_limitations(db: Session, tenant_id: int) -> list[models.QualityLimitation]:
    return list(
        db.execute(
            select(models.QualityLimitation)
            .where(models.QualityLimitation.tenant_id == tenant_id)
            .order_by(models.QualityLimitation.created_at.desc())
        ).scalars().all()
    )


def create_dashboard_snapshot(db: Session, tenant_id: int, **kwargs) -> models.QualityDashboardSnapshot:
    obj = models.QualityDashboardSnapshot(tenant_id=tenant_id, created_at=_now(), **kwargs)
    db.add(obj)
    db.flush()
    db.refresh(obj)
    return obj


def _count_by_status(db: Session, model, tenant_id: int) -> dict[str, int]:
    rows = db.execute(select(model.status, func.count()).where(model.tenant_id == tenant_id).group_by(model.status)).all()
    return {str(status): int(total) for status, total in rows}


def _count_by_field(db: Session, model, tenant_id: int, field_name: str) -> dict[str, int]:
    field = getattr(model, field_name)
    rows = db.execute(select(field, func.count()).where(model.tenant_id == tenant_id).group_by(field)).all()
    return {str(key): int(total) for key, total in rows}


def compute_dashboard_summary(db: Session, tenant_id: int) -> dict[str, dict[str, int]]:
    return {
        "frameworks_summary": _count_by_status(db, models.QualityFramework, tenant_id),
        "standards_summary": _count_by_status(db, models.AccreditationStandard, tenant_id),
        "evidence_summary": _count_by_status(db, models.QualityEvidenceRegistry, tenant_id),
        "readiness_summary": {
            **_count_by_status(db, models.ProgramAccreditationReadiness, tenant_id),
            **_count_by_status(db, models.InstitutionalAccreditationReadiness, tenant_id),
        },
        "self_assessment_summary": _count_by_status(db, models.SelfAssessmentReport, tenant_id),
        "improvement_summary": _count_by_status(db, models.QualityImprovementPlan, tenant_id),
        "audit_summary": _count_by_status(db, models.InternalQualityAudit, tenant_id),
        "program_review_summary": _count_by_status(db, models.ProgramReviewCycle, tenant_id),
        "bridge_summary": _count_by_field(db, models.QualityBridgeMetadata, tenant_id, "source_vertical_ref"),
        "brain_signal_summary": _count_by_field(db, models.QualityBrainSignal, tenant_id, "signal_type"),
    }


def get_health_summary(db: Session, tenant_id: int) -> dict[str, int]:
    counts = compute_dashboard_summary(db, tenant_id)
    readiness_items = sum(counts["readiness_summary"].values())
    evidence_items = sum(counts["evidence_summary"].values())
    bridge_items = sum(counts["bridge_summary"].values())
    return {
        "tenant_id": tenant_id,
        "readiness_items": readiness_items,
        "evidence_items": evidence_items,
        "bridge_items": bridge_items,
    }