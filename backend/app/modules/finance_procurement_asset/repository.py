"""Finance / Procurement / Asset repository helpers."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from app.core.module_helpers.service_validation import TenantRequiredError, TenantResourceNotFoundError
from app.modules.finance_procurement_asset import models


def _now() -> datetime:
    return datetime.now(UTC)


def verify_tenant_scope(tenant_id: int) -> int:
    if tenant_id is None:
        raise TenantRequiredError("tenant_id must be a positive integer")
    if isinstance(tenant_id, bool) or not isinstance(tenant_id, int) or tenant_id <= 0:
        raise TenantRequiredError("tenant_id must be a positive integer")
    return int(tenant_id)


def _tenant_filtered_get(db: Session, model, tenant_id: int, resource_id: int):
    return db.execute(select(model).where(and_(model.tenant_id == tenant_id, model.id == resource_id))).scalar_one_or_none()


def _tenant_filtered_list(db: Session, model, tenant_id: int):
    query = select(model).where(model.tenant_id == tenant_id)
    if hasattr(model, "created_at"):
        query = query.order_by(model.created_at.desc())
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


def list_family_rows(db: Session, tenant_id: int, family: str):
    tenant_id = verify_tenant_scope(tenant_id)
    return _tenant_filtered_list(db, models.MODEL_BY_FAMILY[family], tenant_id)


def read_family_row(db: Session, tenant_id: int, family: str, resource_id: int):
    tenant_id = verify_tenant_scope(tenant_id)
    resource = _tenant_filtered_get(db, models.MODEL_BY_FAMILY[family], tenant_id, resource_id)
    if resource is None:
        raise TenantResourceNotFoundError(f"{family} {resource_id} not found for tenant {tenant_id}")
    return resource


def create_family_row(db: Session, tenant_id: int, family: str, **kwargs):
    tenant_id = verify_tenant_scope(tenant_id)
    return _create(db, models.MODEL_BY_FAMILY[family], tenant_id, **kwargs)


def update_family_row(db: Session, tenant_id: int, family: str, resource_id: int, **kwargs):
    tenant_id = verify_tenant_scope(tenant_id)
    return _update(db, read_family_row(db, tenant_id, family, resource_id), **kwargs)


def create_audit_event(db: Session, tenant_id: int, **kwargs):
    tenant_id = verify_tenant_scope(tenant_id)
    obj = models.AuditEvent(tenant_id=tenant_id, created_at=_now(), **kwargs)
    db.add(obj)
    db.flush()
    db.refresh(obj)
    return obj


def create_evidence_item(db: Session, tenant_id: int, **kwargs):
    tenant_id = verify_tenant_scope(tenant_id)
    obj = models.EvidenceItem(tenant_id=tenant_id, created_at=_now(), **kwargs)
    db.add(obj)
    db.flush()
    db.refresh(obj)
    return obj


def get_dashboard_inputs(db: Session, tenant_id: int) -> dict[str, dict[str, int]]:
    tenant_id = verify_tenant_scope(tenant_id)
    result: dict[str, dict[str, int]] = {}
    for family, model in models.MODEL_BY_FAMILY.items():
        if family in {"audit", "evidence", "limitations"}:
            continue
        if hasattr(model, "status"):
            rows = db.execute(select(model.status, func.count()).where(model.tenant_id == tenant_id).group_by(model.status)).all()
            result[family] = {str(status): int(total) for status, total in rows}
        else:
            result[family] = {"count": len(_tenant_filtered_list(db, model, tenant_id))}
    return result


def get_bridge_inputs(db: Session, tenant_id: int, bridge_family: str | None = None):
    tenant_id = verify_tenant_scope(tenant_id)
    query = select(models.FinanceBridgeRecord).where(models.FinanceBridgeRecord.tenant_id == tenant_id)
    if bridge_family is not None:
        query = query.where(models.FinanceBridgeRecord.bridge_family == bridge_family)
    query = query.order_by(models.FinanceBridgeRecord.created_at.desc())
    return list(db.execute(query).scalars().all())