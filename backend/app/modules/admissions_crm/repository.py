"""Repository helpers for Admissions CRM Batch 1."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.core.module_helpers.service_validation import TenantResourceNotFoundError, validate_tenant_id_provided
from app.modules.admissions_crm import models


def _now() -> datetime:
    return datetime.now(UTC)


def _require(resource: object | None, tenant_id: int, resource_name: str, resource_id: int) -> object:
    if resource is None:
        raise TenantResourceNotFoundError(f"{resource_name} {resource_id} not found for tenant {tenant_id}")
    return resource


def _tenant_filtered_get(db: Session, model, tenant_id: int, resource_id: int):
    validate_tenant_id_provided(tenant_id)
    return db.execute(select(model).where(and_(model.tenant_id == tenant_id, model.id == resource_id))).scalar_one_or_none()


def _tenant_filtered_list(db: Session, model, tenant_id: int):
    validate_tenant_id_provided(tenant_id)
    return list(db.execute(select(model).where(model.tenant_id == tenant_id).order_by(model.created_at.desc())).scalars().all())


def create_lead(db: Session, tenant_id: int, **kwargs) -> models.Lead:
    obj = models.Lead(tenant_id=tenant_id, created_at=_now(), updated_at=_now(), **kwargs)
    db.add(obj)
    db.flush()
    db.refresh(obj)
    return obj


def list_leads(db: Session, tenant_id: int) -> list[models.Lead]:
    return _tenant_filtered_list(db, models.Lead, tenant_id)


def get_lead(db: Session, tenant_id: int, lead_id: int) -> models.Lead | None:
    return _tenant_filtered_get(db, models.Lead, tenant_id, lead_id)


def update_lead(db: Session, tenant_id: int, lead_id: int, **kwargs) -> models.Lead:
    obj = _require(get_lead(db, tenant_id, lead_id), tenant_id, "lead", lead_id)
    for key, value in kwargs.items():
        setattr(obj, key, value)
    obj.updated_at = _now()
    db.flush()
    db.refresh(obj)
    return obj


def create_applicant(db: Session, tenant_id: int, **kwargs) -> models.Applicant:
    obj = models.Applicant(tenant_id=tenant_id, created_at=_now(), updated_at=_now(), **kwargs)
    db.add(obj)
    db.flush()
    db.refresh(obj)
    return obj


def list_applicants(db: Session, tenant_id: int) -> list[models.Applicant]:
    return _tenant_filtered_list(db, models.Applicant, tenant_id)


def get_applicant(db: Session, tenant_id: int, applicant_id: int) -> models.Applicant | None:
    return _tenant_filtered_get(db, models.Applicant, tenant_id, applicant_id)


def create_application(db: Session, tenant_id: int, **kwargs) -> models.Application:
    obj = models.Application(tenant_id=tenant_id, created_at=_now(), updated_at=_now(), **kwargs)
    db.add(obj)
    db.flush()
    db.refresh(obj)
    return obj


def list_applications(db: Session, tenant_id: int) -> list[models.Application]:
    return _tenant_filtered_list(db, models.Application, tenant_id)


def get_application(db: Session, tenant_id: int, application_id: int) -> models.Application | None:
    return _tenant_filtered_get(db, models.Application, tenant_id, application_id)


def update_application(db: Session, tenant_id: int, application_id: int, **kwargs) -> models.Application:
    obj = _require(get_application(db, tenant_id, application_id), tenant_id, "application", application_id)
    for key, value in kwargs.items():
        setattr(obj, key, value)
    obj.updated_at = _now()
    db.flush()
    db.refresh(obj)
    return obj


def create_workflow_event(db: Session, tenant_id: int, **kwargs) -> models.WorkflowTransitionEvent:
    obj = models.WorkflowTransitionEvent(tenant_id=tenant_id, created_at=_now(), **kwargs)
    db.add(obj)
    db.flush()
    return obj


def create_audit_event(db: Session, tenant_id: int, **kwargs) -> models.AuditEvent:
    obj = models.AuditEvent(tenant_id=tenant_id, created_at=_now(), **kwargs)
    db.add(obj)
    db.flush()
    return obj


def create_lead_status_history(db: Session, tenant_id: int, **kwargs) -> models.LeadStatusHistory:
    obj = models.LeadStatusHistory(tenant_id=tenant_id, created_at=_now(), **kwargs)
    db.add(obj)
    db.flush()
    return obj


def create_application_status_history(db: Session, tenant_id: int, **kwargs) -> models.ApplicationStatusHistory:
    obj = models.ApplicationStatusHistory(tenant_id=tenant_id, created_at=_now(), **kwargs)
    db.add(obj)
    db.flush()
    return obj
