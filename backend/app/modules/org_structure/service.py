from __future__ import annotations

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.module_helpers.service_validation import (
    DomainValidationError,
    TenantResourceNotFoundError,
)
from app.modules.org_structure.models import OrgUnitModel, OrgUnitType
from app.modules.org_structure.schemas import OrgUnitCreateSchema, OrgUnitUpdateSchema


def create_org_unit(
    db: Session, tenant_id: int, payload: OrgUnitCreateSchema
) -> OrgUnitModel:
    if payload.parent_unit_id is not None:
        parent = (
            db.query(OrgUnitModel)
            .filter(
                OrgUnitModel.tenant_id == tenant_id,
                OrgUnitModel.id == payload.parent_unit_id,
            )
            .first()
        )
        if parent is None:
            raise DomainValidationError(
                f"Parent unit {payload.parent_unit_id} not found in tenant {tenant_id}"
            )

    unit = OrgUnitModel(
        tenant_id=tenant_id,
        name=payload.name,
        code=payload.code,
        unit_type=payload.unit_type,
        parent_unit_id=payload.parent_unit_id,
        head_person_id=payload.head_person_id,
        email=payload.email,
        phone=payload.phone,
        location=payload.location,
    )
    db.add(unit)
    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise DomainValidationError(
            f"Org unit with code '{payload.code}' already exists in tenant {tenant_id}"
        ) from exc
    db.refresh(unit)
    return unit


def get_org_unit(db: Session, tenant_id: int, unit_id: int) -> OrgUnitModel:
    unit = (
        db.query(OrgUnitModel)
        .filter(
            OrgUnitModel.tenant_id == tenant_id,
            OrgUnitModel.id == unit_id,
        )
        .first()
    )
    if unit is None:
        raise TenantResourceNotFoundError(f"Org unit {unit_id} not found")
    return unit


def list_org_units(
    db: Session,
    tenant_id: int,
    *,
    unit_type: OrgUnitType | None = None,
    active_only: bool = True,
) -> list[OrgUnitModel]:
    q = db.query(OrgUnitModel).filter(OrgUnitModel.tenant_id == tenant_id)
    if active_only:
        q = q.filter(OrgUnitModel.active.is_(True))
    if unit_type is not None:
        q = q.filter(OrgUnitModel.unit_type == unit_type)
    return q.order_by(OrgUnitModel.name).all()


def get_tree(db: Session, tenant_id: int) -> list[OrgUnitModel]:
    """Return all active units in the tenant; callers build the tree from parent_unit_id."""
    return (
        db.query(OrgUnitModel)
        .filter(OrgUnitModel.tenant_id == tenant_id)
        .order_by(OrgUnitModel.name)
        .all()
    )


def update_org_unit(
    db: Session, tenant_id: int, unit_id: int, payload: OrgUnitUpdateSchema
) -> OrgUnitModel:
    unit = get_org_unit(db, tenant_id, unit_id)

    if payload.parent_unit_id is not None and payload.parent_unit_id != unit.parent_unit_id:
        if payload.parent_unit_id == unit_id:
            raise DomainValidationError("Unit cannot be its own parent")
        parent = (
            db.query(OrgUnitModel)
            .filter(
                OrgUnitModel.tenant_id == tenant_id,
                OrgUnitModel.id == payload.parent_unit_id,
            )
            .first()
        )
        if parent is None:
            raise DomainValidationError(
                f"Parent unit {payload.parent_unit_id} not found in tenant {tenant_id}"
            )

    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(unit, field, value)

    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise DomainValidationError("Update violated a uniqueness constraint") from exc
    db.refresh(unit)
    return unit


def deactivate_org_unit(db: Session, tenant_id: int, unit_id: int) -> OrgUnitModel:
    unit = get_org_unit(db, tenant_id, unit_id)
    unit.active = False
    db.flush()
    db.refresh(unit)
    return unit


def bootstrap_university_root(db: Session, tenant_id: int, name: str = "Университет") -> OrgUnitModel:
    """Create the root university OrgUnit for a new tenant. Idempotent."""
    existing = (
        db.query(OrgUnitModel)
        .filter(
            OrgUnitModel.tenant_id == tenant_id,
            OrgUnitModel.unit_type == OrgUnitType.UNIVERSITY,
            OrgUnitModel.parent_unit_id.is_(None),
        )
        .first()
    )
    if existing:
        return existing

    root = OrgUnitModel(
        tenant_id=tenant_id,
        name=name,
        code="ROOT",
        unit_type=OrgUnitType.UNIVERSITY,
        parent_unit_id=None,
        active=True,
    )
    db.add(root)
    db.flush()
    db.refresh(root)
    return root
