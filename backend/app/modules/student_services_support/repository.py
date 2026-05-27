"""Repository helpers for Student Services / Welfare / Support."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from app.core.module_helpers.service_validation import TenantResourceNotFoundError, validate_tenant_id_provided
from app.modules.student_services_support import models


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


def create_service_request(db: Session, tenant_id: int, **kwargs) -> models.StudentServiceRequest:
    obj = models.StudentServiceRequest(tenant_id=tenant_id, created_at=_now(), updated_at=_now(), **kwargs)
    db.add(obj)
    db.flush()
    db.refresh(obj)
    return obj


def list_service_requests(db: Session, tenant_id: int) -> list[models.StudentServiceRequest]:
    return _tenant_filtered_list(db, models.StudentServiceRequest, tenant_id)


def get_service_request(db: Session, tenant_id: int, request_id: int) -> models.StudentServiceRequest | None:
    return _tenant_filtered_get(db, models.StudentServiceRequest, tenant_id, request_id)


def update_service_request(db: Session, tenant_id: int, request_id: int, **kwargs) -> models.StudentServiceRequest:
    obj = _require(get_service_request(db, tenant_id, request_id), tenant_id, "service_request", request_id)
    for key, value in kwargs.items():
        setattr(obj, key, value)
    obj.updated_at = _now()
    db.flush()
    db.refresh(obj)
    return obj


def create_service_request_event(db: Session, tenant_id: int, **kwargs) -> models.StudentServiceRequestEvent:
    obj = models.StudentServiceRequestEvent(tenant_id=tenant_id, created_at=_now(), **kwargs)
    db.add(obj)
    db.flush()
    return obj


def create_support_case(db: Session, tenant_id: int, **kwargs) -> models.StudentSupportCase:
    obj = models.StudentSupportCase(tenant_id=tenant_id, created_at=_now(), updated_at=_now(), **kwargs)
    db.add(obj)
    db.flush()
    db.refresh(obj)
    return obj


def list_support_cases(db: Session, tenant_id: int) -> list[models.StudentSupportCase]:
    return _tenant_filtered_list(db, models.StudentSupportCase, tenant_id)


def get_support_case(db: Session, tenant_id: int, case_id: int) -> models.StudentSupportCase | None:
    return _tenant_filtered_get(db, models.StudentSupportCase, tenant_id, case_id)


def update_support_case(db: Session, tenant_id: int, case_id: int, **kwargs) -> models.StudentSupportCase:
    obj = _require(get_support_case(db, tenant_id, case_id), tenant_id, "support_case", case_id)
    for key, value in kwargs.items():
        setattr(obj, key, value)
    obj.updated_at = _now()
    db.flush()
    db.refresh(obj)
    return obj


def create_support_case_note(db: Session, tenant_id: int, **kwargs) -> models.StudentSupportCaseNote:
    obj = models.StudentSupportCaseNote(tenant_id=tenant_id, created_at=_now(), **kwargs)
    db.add(obj)
    db.flush()
    db.refresh(obj)
    return obj


def create_support_case_event(db: Session, tenant_id: int, **kwargs) -> models.StudentSupportCaseEvent:
    obj = models.StudentSupportCaseEvent(tenant_id=tenant_id, created_at=_now(), **kwargs)
    db.add(obj)
    db.flush()
    return obj


def create_support_evidence(db: Session, tenant_id: int, **kwargs) -> models.StudentSupportEvidence:
    obj = models.StudentSupportEvidence(tenant_id=tenant_id, created_at=_now(), **kwargs)
    db.add(obj)
    db.flush()
    db.refresh(obj)
    return obj


def create_hardship_request(db: Session, tenant_id: int, **kwargs) -> models.HardshipSupportRequest:
    obj = models.HardshipSupportRequest(tenant_id=tenant_id, created_at=_now(), updated_at=_now(), **kwargs)
    db.add(obj)
    db.flush()
    db.refresh(obj)
    return obj


def create_accommodation_request(db: Session, tenant_id: int, **kwargs) -> models.DisabilityAccommodationRequest:
    obj = models.DisabilityAccommodationRequest(tenant_id=tenant_id, created_at=_now(), updated_at=_now(), **kwargs)
    db.add(obj)
    db.flush()
    db.refresh(obj)
    return obj


def create_complaint(db: Session, tenant_id: int, **kwargs) -> models.StudentComplaint:
    obj = models.StudentComplaint(tenant_id=tenant_id, created_at=_now(), updated_at=_now(), **kwargs)
    db.add(obj)
    db.flush()
    db.refresh(obj)
    return obj


def update_complaint(db: Session, tenant_id: int, complaint_id: int, **kwargs) -> models.StudentComplaint:
    obj = _require(_tenant_filtered_get(db, models.StudentComplaint, tenant_id, complaint_id), tenant_id, "complaint", complaint_id)
    for key, value in kwargs.items():
        setattr(obj, key, value)
    obj.updated_at = _now()
    db.flush()
    db.refresh(obj)
    return obj


def create_escalation(db: Session, tenant_id: int, **kwargs) -> models.StudentSupportEscalation:
    obj = models.StudentSupportEscalation(tenant_id=tenant_id, created_at=_now(), updated_at=_now(), **kwargs)
    db.add(obj)
    db.flush()
    db.refresh(obj)
    return obj


def create_dashboard_snapshot(db: Session, tenant_id: int, **kwargs) -> models.StudentSupportDashboardSnapshot:
    obj = models.StudentSupportDashboardSnapshot(tenant_id=tenant_id, created_at=_now(), updated_at=_now(), **kwargs)
    db.add(obj)
    db.flush()
    db.refresh(obj)
    return obj


def count_by_status(db: Session, model, tenant_id: int) -> dict[str, int]:
    rows = db.execute(
        select(model.status, func.count()).where(model.tenant_id == validate_tenant_id_provided(tenant_id)).group_by(model.status)
    ).all()
    return {str(status): int(total) for status, total in rows}
