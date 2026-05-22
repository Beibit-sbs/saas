"""Research / Science repository helpers."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from app.core.module_helpers.service_validation import TenantResourceNotFoundError
from app.modules.research_science.models import (
    ConferenceParticipation,
    GrantApplication,
    GrantDeliverable,
    PublicationRegistryEntry,
    ResearchAuditEvent,
    ResearchBridgeMetadata,
    ResearchDashboardSnapshot,
    ResearchEthicsAmendment,
    ResearchEthicsRequest,
    ResearchEvidenceMetadata,
    ResearchLimitation,
    ResearchProject,
    ResearchStatusHistory,
    ScientificSupervision,
    StudentResearchWork,
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
    order_column = getattr(model, "created_at", None)
    query = select(model).where(model.tenant_id == tenant_id)
    if order_column is not None:
        query = query.order_by(order_column.desc())
    return list(db.execute(query).scalars().all())


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


def _count_by_field(db: Session, model, tenant_id: int, field_name: str) -> dict[str, int]:
    field = getattr(model, field_name)
    rows = db.execute(select(field, func.count()).where(model.tenant_id == tenant_id).group_by(field)).all()
    return {str(key): int(total) for key, total in rows}


def create_research_project(db: Session, tenant_id: int, **kwargs) -> ResearchProject:
    return _create(db, ResearchProject, tenant_id, **kwargs)


def get_research_project(db: Session, tenant_id: int, project_id: int) -> ResearchProject | None:
    return _tenant_filtered_get(db, ResearchProject, tenant_id, project_id)


def list_research_projects(db: Session, tenant_id: int) -> list[ResearchProject]:
    return _tenant_filtered_list(db, ResearchProject, tenant_id)


def update_research_project(db: Session, tenant_id: int, project_id: int, **kwargs) -> ResearchProject:
    return _update(db, _require(get_research_project(db, tenant_id, project_id), tenant_id, "research_project", project_id), **kwargs)


def create_student_research_work(db: Session, tenant_id: int, **kwargs) -> StudentResearchWork:
    return _create(db, StudentResearchWork, tenant_id, **kwargs)


def get_student_research_work(db: Session, tenant_id: int, student_research_id: int) -> StudentResearchWork | None:
    return _tenant_filtered_get(db, StudentResearchWork, tenant_id, student_research_id)


def list_student_research_work(db: Session, tenant_id: int) -> list[StudentResearchWork]:
    return _tenant_filtered_list(db, StudentResearchWork, tenant_id)


def update_student_research_work(db: Session, tenant_id: int, student_research_id: int, **kwargs) -> StudentResearchWork:
    return _update(db, _require(get_student_research_work(db, tenant_id, student_research_id), tenant_id, "student_research_work", student_research_id), **kwargs)


def create_scientific_supervision(db: Session, tenant_id: int, **kwargs) -> ScientificSupervision:
    return _create(db, ScientificSupervision, tenant_id, **kwargs)


def get_scientific_supervision(db: Session, tenant_id: int, supervision_id: int) -> ScientificSupervision | None:
    return _tenant_filtered_get(db, ScientificSupervision, tenant_id, supervision_id)


def list_scientific_supervisions(db: Session, tenant_id: int) -> list[ScientificSupervision]:
    return _tenant_filtered_list(db, ScientificSupervision, tenant_id)


def update_scientific_supervision(db: Session, tenant_id: int, supervision_id: int, **kwargs) -> ScientificSupervision:
    return _update(db, _require(get_scientific_supervision(db, tenant_id, supervision_id), tenant_id, "scientific_supervision", supervision_id), **kwargs)


def create_publication_metadata(db: Session, tenant_id: int, **kwargs) -> PublicationRegistryEntry:
    return _create(db, PublicationRegistryEntry, tenant_id, **kwargs)


def get_publication_metadata(db: Session, tenant_id: int, publication_id: int) -> PublicationRegistryEntry | None:
    return _tenant_filtered_get(db, PublicationRegistryEntry, tenant_id, publication_id)


def list_publication_metadata(db: Session, tenant_id: int) -> list[PublicationRegistryEntry]:
    return _tenant_filtered_list(db, PublicationRegistryEntry, tenant_id)


def update_publication_metadata(db: Session, tenant_id: int, publication_id: int, **kwargs) -> PublicationRegistryEntry:
    return _update(db, _require(get_publication_metadata(db, tenant_id, publication_id), tenant_id, "publication_metadata", publication_id), **kwargs)


def create_conference_participation(db: Session, tenant_id: int, **kwargs) -> ConferenceParticipation:
    return _create(db, ConferenceParticipation, tenant_id, **kwargs)


def get_conference_participation(db: Session, tenant_id: int, conference_id: int) -> ConferenceParticipation | None:
    return _tenant_filtered_get(db, ConferenceParticipation, tenant_id, conference_id)


def list_conference_participation(db: Session, tenant_id: int) -> list[ConferenceParticipation]:
    return _tenant_filtered_list(db, ConferenceParticipation, tenant_id)


def update_conference_participation(db: Session, tenant_id: int, conference_id: int, **kwargs) -> ConferenceParticipation:
    return _update(db, _require(get_conference_participation(db, tenant_id, conference_id), tenant_id, "conference_participation", conference_id), **kwargs)


def create_grant_application(db: Session, tenant_id: int, **kwargs) -> GrantApplication:
    return _create(db, GrantApplication, tenant_id, **kwargs)


def get_grant_application(db: Session, tenant_id: int, grant_id: int) -> GrantApplication | None:
    return _tenant_filtered_get(db, GrantApplication, tenant_id, grant_id)


def list_grant_applications(db: Session, tenant_id: int) -> list[GrantApplication]:
    return _tenant_filtered_list(db, GrantApplication, tenant_id)


def update_grant_application(db: Session, tenant_id: int, grant_id: int, **kwargs) -> GrantApplication:
    return _update(db, _require(get_grant_application(db, tenant_id, grant_id), tenant_id, "grant_application", grant_id), **kwargs)


def create_grant_deliverable(db: Session, tenant_id: int, **kwargs) -> GrantDeliverable:
    return _create(db, GrantDeliverable, tenant_id, **kwargs)


def get_grant_deliverable(db: Session, tenant_id: int, deliverable_id: int) -> GrantDeliverable | None:
    return _tenant_filtered_get(db, GrantDeliverable, tenant_id, deliverable_id)


def list_grant_deliverables(db: Session, tenant_id: int) -> list[GrantDeliverable]:
    return _tenant_filtered_list(db, GrantDeliverable, tenant_id)


def update_grant_deliverable(db: Session, tenant_id: int, deliverable_id: int, **kwargs) -> GrantDeliverable:
    return _update(db, _require(get_grant_deliverable(db, tenant_id, deliverable_id), tenant_id, "grant_deliverable", deliverable_id), **kwargs)


def create_ethics_request(db: Session, tenant_id: int, **kwargs) -> ResearchEthicsRequest:
    return _create(db, ResearchEthicsRequest, tenant_id, **kwargs)


def get_ethics_request(db: Session, tenant_id: int, ethics_id: int) -> ResearchEthicsRequest | None:
    return _tenant_filtered_get(db, ResearchEthicsRequest, tenant_id, ethics_id)


def list_ethics_requests(db: Session, tenant_id: int) -> list[ResearchEthicsRequest]:
    return _tenant_filtered_list(db, ResearchEthicsRequest, tenant_id)


def update_ethics_request(db: Session, tenant_id: int, ethics_id: int, **kwargs) -> ResearchEthicsRequest:
    return _update(db, _require(get_ethics_request(db, tenant_id, ethics_id), tenant_id, "ethics_request", ethics_id), **kwargs)


def create_ethics_amendment(db: Session, tenant_id: int, **kwargs) -> ResearchEthicsAmendment:
    return _create(db, ResearchEthicsAmendment, tenant_id, **kwargs)


def list_ethics_amendments(db: Session, tenant_id: int) -> list[ResearchEthicsAmendment]:
    return _tenant_filtered_list(db, ResearchEthicsAmendment, tenant_id)


def attach_research_evidence(db: Session, tenant_id: int, **kwargs) -> ResearchEvidenceMetadata:
    return _create(db, ResearchEvidenceMetadata, tenant_id, **kwargs)


def get_research_evidence(db: Session, tenant_id: int, evidence_id: int) -> ResearchEvidenceMetadata | None:
    return _tenant_filtered_get(db, ResearchEvidenceMetadata, tenant_id, evidence_id)


def list_research_evidence(db: Session, tenant_id: int) -> list[ResearchEvidenceMetadata]:
    return _tenant_filtered_list(db, ResearchEvidenceMetadata, tenant_id)


def create_research_audit_event(db: Session, tenant_id: int, **kwargs) -> ResearchAuditEvent:
    obj = ResearchAuditEvent(tenant_id=tenant_id, created_at=_now(), **kwargs)
    db.add(obj)
    db.flush()
    db.refresh(obj)
    return obj


def list_research_audit_events(db: Session, tenant_id: int) -> list[ResearchAuditEvent]:
    return list(
        db.execute(
            select(ResearchAuditEvent)
            .where(ResearchAuditEvent.tenant_id == tenant_id)
            .order_by(ResearchAuditEvent.created_at.desc())
        ).scalars().all()
    )


def create_status_history(db: Session, tenant_id: int, **kwargs) -> ResearchStatusHistory:
    obj = ResearchStatusHistory(tenant_id=tenant_id, changed_at=_now(), **kwargs)
    db.add(obj)
    db.flush()
    db.refresh(obj)
    return obj


def list_status_history(db: Session, tenant_id: int) -> list[ResearchStatusHistory]:
    return list(
        db.execute(
            select(ResearchStatusHistory)
            .where(ResearchStatusHistory.tenant_id == tenant_id)
            .order_by(ResearchStatusHistory.changed_at.desc())
        ).scalars().all()
    )


def create_research_bridge_metadata(db: Session, tenant_id: int, **kwargs) -> ResearchBridgeMetadata:
    return _create(db, ResearchBridgeMetadata, tenant_id, **kwargs)


def list_research_bridge_metadata(db: Session, tenant_id: int) -> list[ResearchBridgeMetadata]:
    return _tenant_filtered_list(db, ResearchBridgeMetadata, tenant_id)


def get_research_bridge_summary(db: Session, tenant_id: int) -> dict[str, int]:
    return _count_by_field(db, ResearchBridgeMetadata, tenant_id, "bridge_target")


def create_dashboard_snapshot(db: Session, tenant_id: int, **kwargs) -> ResearchDashboardSnapshot:
    obj = ResearchDashboardSnapshot(tenant_id=tenant_id, created_at=_now(), **kwargs)
    db.add(obj)
    db.flush()
    db.refresh(obj)
    return obj


def compute_research_dashboard_summary(db: Session, tenant_id: int) -> dict[str, dict[str, int]]:
    return {
        "projects_summary": _count_by_status(db, ResearchProject, tenant_id),
        "student_research_summary": _count_by_status(db, StudentResearchWork, tenant_id),
        "supervision_summary": _count_by_status(db, ScientificSupervision, tenant_id),
        "publications_summary": _count_by_status(db, PublicationRegistryEntry, tenant_id),
        "conferences_summary": _count_by_status(db, ConferenceParticipation, tenant_id),
        "grants_summary": _count_by_status(db, GrantApplication, tenant_id),
        "ethics_summary": _count_by_status(db, ResearchEthicsRequest, tenant_id),
        "evidence_summary": _count_by_field(db, ResearchEvidenceMetadata, tenant_id, "verification_status"),
        "bridge_summary": _count_by_field(db, ResearchBridgeMetadata, tenant_id, "bridge_target"),
    }


def get_research_matrix_summary(db: Session, tenant_id: int) -> dict[str, int | str]:
    del db
    return {
        "tenant_id": tenant_id,
        "master_matrix_rows": 467,
        "capability_count": 60,
        "contract_version": "A-037.2",
    }


def get_research_health_summary(db: Session, tenant_id: int) -> dict[str, int]:
    counts = compute_research_dashboard_summary(db, tenant_id)
    total_records = sum(sum(group.values()) for group in counts.values())
    return {"tenant_id": tenant_id, "total_records": total_records, "bridge_records": sum(counts["bridge_summary"].values())}


def list_research_limitations(db: Session, tenant_id: int) -> list[ResearchLimitation]:
    return _tenant_filtered_list(db, ResearchLimitation, tenant_id)