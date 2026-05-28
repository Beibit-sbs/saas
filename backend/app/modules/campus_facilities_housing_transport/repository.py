"""Repository helpers for Campus / Facilities / Housing / Transport runtime."""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.module_helpers.service_validation import DomainValidationError, TenantResourceNotFoundError, validate_tenant_id_provided
from app.modules.campus_facilities_housing_transport import models


FAMILY_TO_MODEL = models.MODEL_BY_FAMILY


def verify_tenant_scope(tenant_id: int) -> int:
    return validate_tenant_id_provided(tenant_id)


def _get_model(family: str):
    model = FAMILY_TO_MODEL.get(family)
    if model is None:
        raise DomainValidationError(f"Unsupported campus facilities family: {family}")
    return model


def _serialize(record: object) -> dict[str, Any]:
    return {
        "id": getattr(record, "id", None),
        "tenant_id": getattr(record, "tenant_id", None),
        "status": getattr(record, "status", "active"),
        "reference_key": getattr(record, "reference_key", None),
        "title": getattr(record, "title", None),
        "source_module": getattr(record, "source_module", None),
        "source_entity_id": getattr(record, "source_entity_id", None),
        "metadata": getattr(record, "metadata_json", {}) or {},
        "limitations": getattr(record, "limitations_json", []) or [],
        "incomplete_data": bool(getattr(record, "incomplete_data", True)),
        "created_by": getattr(record, "created_by", None),
        "updated_by": getattr(record, "updated_by", None),
        "created_at": getattr(record, "created_at", None),
        "updated_at": getattr(record, "updated_at", None),
    }


def list_family_records(db: Session, tenant_id: int, family: str) -> list[dict[str, Any]]:
    normalized_tenant_id = verify_tenant_scope(tenant_id)
    model = _get_model(family)
    statement = select(model).where(model.tenant_id == normalized_tenant_id).order_by(model.id.desc())
    return [_serialize(record) for record in db.execute(statement).scalars().all()]


def get_dashboard_inputs(db: Session, tenant_id: int) -> dict[str, int]:
    normalized_tenant_id = verify_tenant_scope(tenant_id)
    counts: dict[str, int] = {}
    for family, model in FAMILY_TO_MODEL.items():
        if family == "dashboard":
            continue
        statement = select(model).where(model.tenant_id == normalized_tenant_id)
        counts[family] = len(db.execute(statement).scalars().all())
    return counts


def create_family_record(db: Session, tenant_id: int, family: str, actor: str, payload: Any) -> dict[str, Any]:
    normalized_tenant_id = verify_tenant_scope(tenant_id)
    model = _get_model(family)
    record_kwargs = {
        "tenant_id": normalized_tenant_id,
        "status": payload.status,
        "reference_key": getattr(payload, "reference_key", None),
        "title": getattr(payload, "title", None),
        "source_module": getattr(payload, "source_module", None),
        "source_entity_id": getattr(payload, "source_entity_id", None),
        "metadata_json": dict(getattr(payload, "metadata", {}) or {}),
        "limitations_json": list(getattr(payload, "limitations", []) or []),
        "incomplete_data": bool(getattr(payload, "incomplete_data", True)),
        "created_by": actor,
        "updated_by": actor,
    }
    if hasattr(model, "evidence_type"):
        record_kwargs["evidence_type"] = getattr(payload, "evidence_type", "metadata_only")
    if hasattr(model, "reference_uri"):
        record_kwargs["reference_uri"] = getattr(payload, "reference_uri", None)
    if hasattr(model, "bridge_key"):
        record_kwargs["bridge_key"] = getattr(payload, "reference_key", family)
    if hasattr(model, "limitation_text"):
        limitation_values = list(getattr(payload, "limitations", []) or [])
        record_kwargs["limitation_text"] = "; ".join(limitation_values) if limitation_values else "human review required"
    if hasattr(model, "summary_json"):
        record_kwargs["summary_json"] = dict(getattr(payload, "metadata", {}) or {})
    if hasattr(model, "campus_code"):
        record_kwargs["campus_code"] = getattr(payload, "reference_key", None)

    record = model(**record_kwargs)
    db.add(record)
    db.commit()
    db.refresh(record)
    return _serialize(record)


def get_family_record(db: Session, tenant_id: int, family: str, record_id: int) -> dict[str, Any]:
    normalized_tenant_id = verify_tenant_scope(tenant_id)
    model = _get_model(family)
    statement = select(model).where(model.id == int(record_id), model.tenant_id == normalized_tenant_id)
    record = db.execute(statement).scalar_one_or_none()
    if record is None:
        raise TenantResourceNotFoundError(f"{family} record {record_id} not found for tenant {normalized_tenant_id}")
    return _serialize(record)
