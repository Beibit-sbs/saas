"""Academic Operations repository helpers."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from app.core.module_helpers.service_validation import TenantResourceNotFoundError
from app.modules.academic_operations.models import (
    AcademicOperationsAcademicGroup,
    AcademicOperationsAdvisorTutorAssignment,
    AcademicOperationsAuditEvent,
    AcademicOperationsCanonicalModuleBridge,
    AcademicOperationsCohort,
    AcademicOperationsCourseRegistrationMetadata,
    AcademicOperationsDashboardSnapshot,
    AcademicOperationsDocumentWorkflowBridgeMetadata,
    AcademicOperationsEvidenceMetadata,
    AcademicOperationsExecutiveGovernanceBridgeMetadata,
    AcademicOperationsGradebookMetadata,
    AcademicOperationsQualityAccreditationBridgeMetadata,
    AcademicOperationsRetakePlan,
    AcademicOperationsStudentLifecycleBridgeMetadata,
    AcademicOperationsSummerSemesterTerm,
)


def _now() -> datetime:
    return datetime.now(UTC)


def _require(resource: object | None, tenant_id: int, resource_name: str, resource_id: int) -> object:
    if resource is None:
        raise TenantResourceNotFoundError(f"{resource_name} {resource_id} not found for tenant {tenant_id}")
    return resource


def _tenant_filtered_get(db: Session, model, tenant_id: int, resource_id: int):
    return db.execute(select(model).where(and_(model.tenant_id == tenant_id, model.id == resource_id))).scalar_one_or_none()


def _tenant_filtered_list(db: Session, model, tenant_id: int):
    return list(db.execute(select(model).where(model.tenant_id == tenant_id).order_by(model.created_at.desc())).scalars().all())


def _create(db: Session, model, tenant_id: int, **kwargs):
    obj = model(tenant_id=tenant_id, created_at=_now(), updated_at=_now(), **kwargs)
    db.add(obj)
    db.flush()
    db.refresh(obj)
    return obj


def _update(db: Session, resource, **kwargs):
    for key, value in kwargs.items():
        setattr(resource, key, value)
    if hasattr(resource, "updated_at"):
        resource.updated_at = _now()
    db.flush()
    db.refresh(resource)
    return resource


def _count_by_status(db: Session, model, tenant_id: int) -> dict[str, int]:
    rows = db.execute(select(model.status, func.count()).where(model.tenant_id == tenant_id).group_by(model.status)).all()
    return {str(status): int(total) for status, total in rows}


def create_academic_group(db: Session, tenant_id: int, **kwargs) -> AcademicOperationsAcademicGroup:
    return _create(db, AcademicOperationsAcademicGroup, tenant_id, **kwargs)


def get_academic_group(db: Session, tenant_id: int, group_id: int) -> AcademicOperationsAcademicGroup | None:
    return _tenant_filtered_get(db, AcademicOperationsAcademicGroup, tenant_id, group_id)


def list_academic_groups(db: Session, tenant_id: int) -> list[AcademicOperationsAcademicGroup]:
    return _tenant_filtered_list(db, AcademicOperationsAcademicGroup, tenant_id)


def update_academic_group(db: Session, tenant_id: int, group_id: int, **kwargs) -> AcademicOperationsAcademicGroup:
    return _update(db, _require(get_academic_group(db, tenant_id, group_id), tenant_id, "academic_group", group_id), **kwargs)


def create_cohort(db: Session, tenant_id: int, **kwargs) -> AcademicOperationsCohort:
    return _create(db, AcademicOperationsCohort, tenant_id, **kwargs)


def get_cohort(db: Session, tenant_id: int, cohort_id: int) -> AcademicOperationsCohort | None:
    return _tenant_filtered_get(db, AcademicOperationsCohort, tenant_id, cohort_id)


def list_cohorts(db: Session, tenant_id: int) -> list[AcademicOperationsCohort]:
    return _tenant_filtered_list(db, AcademicOperationsCohort, tenant_id)


def update_cohort(db: Session, tenant_id: int, cohort_id: int, **kwargs) -> AcademicOperationsCohort:
    return _update(db, _require(get_cohort(db, tenant_id, cohort_id), tenant_id, "cohort", cohort_id), **kwargs)


def create_course_registration_metadata(db: Session, tenant_id: int, **kwargs) -> AcademicOperationsCourseRegistrationMetadata:
    return _create(db, AcademicOperationsCourseRegistrationMetadata, tenant_id, **kwargs)


def list_course_registration_metadata(db: Session, tenant_id: int) -> list[AcademicOperationsCourseRegistrationMetadata]:
    return _tenant_filtered_list(db, AcademicOperationsCourseRegistrationMetadata, tenant_id)


def create_gradebook_metadata(db: Session, tenant_id: int, **kwargs) -> AcademicOperationsGradebookMetadata:
    return _create(db, AcademicOperationsGradebookMetadata, tenant_id, **kwargs)


def get_gradebook_metadata(db: Session, tenant_id: int, gradebook_id: int) -> AcademicOperationsGradebookMetadata | None:
    return _tenant_filtered_get(db, AcademicOperationsGradebookMetadata, tenant_id, gradebook_id)


def list_gradebook_metadata(db: Session, tenant_id: int) -> list[AcademicOperationsGradebookMetadata]:
    return _tenant_filtered_list(db, AcademicOperationsGradebookMetadata, tenant_id)


def update_gradebook_metadata(db: Session, tenant_id: int, gradebook_id: int, **kwargs) -> AcademicOperationsGradebookMetadata:
    return _update(db, _require(get_gradebook_metadata(db, tenant_id, gradebook_id), tenant_id, "gradebook_metadata", gradebook_id), **kwargs)


def create_retake_plan(db: Session, tenant_id: int, **kwargs) -> AcademicOperationsRetakePlan:
    return _create(db, AcademicOperationsRetakePlan, tenant_id, **kwargs)


def get_retake_plan(db: Session, tenant_id: int, retake_id: int) -> AcademicOperationsRetakePlan | None:
    return _tenant_filtered_get(db, AcademicOperationsRetakePlan, tenant_id, retake_id)


def list_retake_plans(db: Session, tenant_id: int) -> list[AcademicOperationsRetakePlan]:
    return _tenant_filtered_list(db, AcademicOperationsRetakePlan, tenant_id)


def update_retake_plan(db: Session, tenant_id: int, retake_id: int, **kwargs) -> AcademicOperationsRetakePlan:
    return _update(db, _require(get_retake_plan(db, tenant_id, retake_id), tenant_id, "retake_plan", retake_id), **kwargs)


def create_summer_semester_term(db: Session, tenant_id: int, **kwargs) -> AcademicOperationsSummerSemesterTerm:
    return _create(db, AcademicOperationsSummerSemesterTerm, tenant_id, **kwargs)


def get_summer_semester_term(db: Session, tenant_id: int, term_id: int) -> AcademicOperationsSummerSemesterTerm | None:
    return _tenant_filtered_get(db, AcademicOperationsSummerSemesterTerm, tenant_id, term_id)


def list_summer_semester_terms(db: Session, tenant_id: int) -> list[AcademicOperationsSummerSemesterTerm]:
    return _tenant_filtered_list(db, AcademicOperationsSummerSemesterTerm, tenant_id)


def update_summer_semester_term(db: Session, tenant_id: int, term_id: int, **kwargs) -> AcademicOperationsSummerSemesterTerm:
    return _update(db, _require(get_summer_semester_term(db, tenant_id, term_id), tenant_id, "summer_semester_term", term_id), **kwargs)


def create_advisor_tutor_assignment(db: Session, tenant_id: int, **kwargs) -> AcademicOperationsAdvisorTutorAssignment:
    return _create(db, AcademicOperationsAdvisorTutorAssignment, tenant_id, **kwargs)


def get_advisor_tutor_assignment(db: Session, tenant_id: int, assignment_id: int) -> AcademicOperationsAdvisorTutorAssignment | None:
    return _tenant_filtered_get(db, AcademicOperationsAdvisorTutorAssignment, tenant_id, assignment_id)


def list_advisor_tutor_assignments(db: Session, tenant_id: int) -> list[AcademicOperationsAdvisorTutorAssignment]:
    return _tenant_filtered_list(db, AcademicOperationsAdvisorTutorAssignment, tenant_id)


def update_advisor_tutor_assignment(db: Session, tenant_id: int, assignment_id: int, **kwargs) -> AcademicOperationsAdvisorTutorAssignment:
    return _update(db, _require(get_advisor_tutor_assignment(db, tenant_id, assignment_id), tenant_id, "advisor_tutor_assignment", assignment_id), **kwargs)


def create_canonical_module_bridge(db: Session, tenant_id: int, **kwargs) -> AcademicOperationsCanonicalModuleBridge:
    return _create(db, AcademicOperationsCanonicalModuleBridge, tenant_id, **kwargs)


def list_canonical_module_bridges(db: Session, tenant_id: int) -> list[AcademicOperationsCanonicalModuleBridge]:
    return _tenant_filtered_list(db, AcademicOperationsCanonicalModuleBridge, tenant_id)


def get_canonical_bridge_summary(db: Session, tenant_id: int) -> dict[str, int]:
    rows = db.execute(
        select(AcademicOperationsCanonicalModuleBridge.bridge_type, func.count())
        .where(AcademicOperationsCanonicalModuleBridge.tenant_id == tenant_id)
        .group_by(AcademicOperationsCanonicalModuleBridge.bridge_type)
    ).all()
    return {str(key): int(total) for key, total in rows}


def _bridge_summary(db: Session, model, tenant_id: int) -> list:
    return _tenant_filtered_list(db, model, tenant_id)


def get_student_lifecycle_bridge_summary(db: Session, tenant_id: int) -> list[AcademicOperationsStudentLifecycleBridgeMetadata]:
    return _bridge_summary(db, AcademicOperationsStudentLifecycleBridgeMetadata, tenant_id)


def get_document_workflow_bridge_summary(db: Session, tenant_id: int) -> list[AcademicOperationsDocumentWorkflowBridgeMetadata]:
    return _bridge_summary(db, AcademicOperationsDocumentWorkflowBridgeMetadata, tenant_id)


def get_executive_governance_bridge_summary(db: Session, tenant_id: int) -> list[AcademicOperationsExecutiveGovernanceBridgeMetadata]:
    return _bridge_summary(db, AcademicOperationsExecutiveGovernanceBridgeMetadata, tenant_id)


def get_quality_accreditation_bridge_summary(db: Session, tenant_id: int) -> list[AcademicOperationsQualityAccreditationBridgeMetadata]:
    return _bridge_summary(db, AcademicOperationsQualityAccreditationBridgeMetadata, tenant_id)


def create_audit_event(db: Session, tenant_id: int, **kwargs) -> AcademicOperationsAuditEvent:
    obj = AcademicOperationsAuditEvent(tenant_id=tenant_id, created_at=_now(), **kwargs)
    db.add(obj)
    db.flush()
    db.refresh(obj)
    return obj


def list_audit_events(db: Session, tenant_id: int) -> list[AcademicOperationsAuditEvent]:
    return list(db.execute(select(AcademicOperationsAuditEvent).where(AcademicOperationsAuditEvent.tenant_id == tenant_id).order_by(AcademicOperationsAuditEvent.created_at.desc())).scalars().all())


def attach_evidence_metadata(db: Session, tenant_id: int, **kwargs) -> AcademicOperationsEvidenceMetadata:
    return _create(db, AcademicOperationsEvidenceMetadata, tenant_id, **kwargs)


def list_evidence_metadata(db: Session, tenant_id: int) -> list[AcademicOperationsEvidenceMetadata]:
    return _tenant_filtered_list(db, AcademicOperationsEvidenceMetadata, tenant_id)


def create_dashboard_snapshot(db: Session, tenant_id: int, **kwargs) -> AcademicOperationsDashboardSnapshot:
    obj = AcademicOperationsDashboardSnapshot(tenant_id=tenant_id, created_at=_now(), **kwargs)
    db.add(obj)
    db.flush()
    db.refresh(obj)
    return obj


def compute_dashboard_summary(db: Session, tenant_id: int) -> dict[str, dict[str, int]]:
    return {
        "academic_groups": _count_by_status(db, AcademicOperationsAcademicGroup, tenant_id),
        "cohorts": _count_by_status(db, AcademicOperationsCohort, tenant_id),
        "gradebook_metadata": _count_by_status(db, AcademicOperationsGradebookMetadata, tenant_id),
        "retake_plans": _count_by_status(db, AcademicOperationsRetakePlan, tenant_id),
        "summer_semester_terms": _count_by_status(db, AcademicOperationsSummerSemesterTerm, tenant_id),
        "advisor_tutor_assignments": _count_by_status(db, AcademicOperationsAdvisorTutorAssignment, tenant_id),
        "canonical_bridges": _count_by_status(db, AcademicOperationsCanonicalModuleBridge, tenant_id),
    }


def get_matrix_summary(db: Session, tenant_id: int) -> dict[str, int]:
    del db
    return {"tenant_id": tenant_id, "master_matrix_rows": 467}


def get_health_summary(db: Session, tenant_id: int) -> dict[str, int]:
    counts = compute_dashboard_summary(db, tenant_id)
    total_records = sum(sum(group.values()) for group in counts.values())
    return {"tenant_id": tenant_id, "total_records": total_records, "bridge_records": sum(counts["canonical_bridges"].values())}