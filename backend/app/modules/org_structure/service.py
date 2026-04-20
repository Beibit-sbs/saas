from __future__ import annotations

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.module_helpers.service_validation import (
    DomainValidationError,
    MutationResult,
    TenantResourceNotFoundError,
)
from app.modules.org_structure.models import OrgUnitModel, OrgUnitType
from app.modules.org_structure.schemas import (
    OrgUnitConsistencyReportSchema,
    OrgUnitCreateSchema,
    OrgUnitReadSchema,
    OrgUnitUpdateSchema,
)


ALLOWED_PARENT_TYPES: dict[OrgUnitType, set[OrgUnitType] | None] = {
    OrgUnitType.UNIVERSITY: None,
    OrgUnitType.SCHOOL: {OrgUnitType.UNIVERSITY},
    OrgUnitType.FACULTY: {OrgUnitType.UNIVERSITY, OrgUnitType.SCHOOL},
    OrgUnitType.DEPARTMENT: {OrgUnitType.FACULTY, OrgUnitType.SCHOOL},
    OrgUnitType.UMO: {OrgUnitType.UNIVERSITY, OrgUnitType.SCHOOL, OrgUnitType.FACULTY},
    OrgUnitType.REGISTRAR_OFFICE: {OrgUnitType.UNIVERSITY},
    OrgUnitType.DEANS_OFFICE: {OrgUnitType.SCHOOL, OrgUnitType.FACULTY},
    OrgUnitType.ADVISORY_UNIT: {OrgUnitType.UNIVERSITY, OrgUnitType.SCHOOL, OrgUnitType.FACULTY},
    OrgUnitType.ACADEMIC_COMMITTEE: {
        OrgUnitType.UNIVERSITY,
        OrgUnitType.SCHOOL,
        OrgUnitType.FACULTY,
        OrgUnitType.DEPARTMENT,
    },
    OrgUnitType.ACADEMIC_COMMISSION: {
        OrgUnitType.UNIVERSITY,
        OrgUnitType.SCHOOL,
        OrgUnitType.FACULTY,
        OrgUnitType.DEPARTMENT,
    },
}


def create_org_unit(
    db: Session, tenant_id: int, payload: OrgUnitCreateSchema
) -> MutationResult[OrgUnitReadSchema]:
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

    existing = (
        db.query(OrgUnitModel)
        .filter(OrgUnitModel.tenant_id == tenant_id, OrgUnitModel.code == payload.code)
        .first()
    )
    if existing is not None:
        return MutationResult(
            entity=OrgUnitReadSchema.model_validate(existing),
            idempotent_replay=True,
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
    return MutationResult(entity=OrgUnitReadSchema.model_validate(unit))


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
) -> MutationResult[OrgUnitReadSchema]:
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
    is_noop = all(getattr(unit, field) == value for field, value in data.items())
    if is_noop:
        return MutationResult(
            entity=OrgUnitReadSchema.model_validate(unit),
            idempotent_replay=True,
        )
    for field, value in data.items():
        setattr(unit, field, value)

    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise DomainValidationError("Update violated a uniqueness constraint") from exc
    db.refresh(unit)
    return MutationResult(entity=OrgUnitReadSchema.model_validate(unit))


def deactivate_org_unit(db: Session, tenant_id: int, unit_id: int) -> MutationResult[OrgUnitReadSchema]:
    unit = get_org_unit(db, tenant_id, unit_id)
    if not unit.active:
        return MutationResult(
            entity=OrgUnitReadSchema.model_validate(unit),
            idempotent_replay=True,
        )
    unit.active = False
    db.flush()
    db.refresh(unit)
    return MutationResult(entity=OrgUnitReadSchema.model_validate(unit))


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


def get_org_unit_consistency_report(
    db: Session,
    tenant_id: int,
) -> OrgUnitConsistencyReportSchema:
    units = get_tree(db, tenant_id)

    issues: list[dict[str, object]] = []
    units_by_id = {int(unit.id): unit for unit in units}
    root_units = [unit for unit in units if unit.parent_unit_id is None]
    university_roots = [unit for unit in root_units if unit.unit_type == OrgUnitType.UNIVERSITY]
    active_university_roots = [unit for unit in university_roots if bool(unit.active)]

    if units and len(root_units) == 0:
        issues.append(
            {
                "issue_type": "missing_root_unit",
            }
        )

    if len(root_units) > 1:
        for unit in root_units:
            issues.append(
                {
                    "issue_type": "multiple_root_units",
                    "unit_id": int(unit.id),
                    "unit_type": unit.unit_type,
                }
            )

    if units and len(university_roots) == 0:
        issues.append(
            {
                "issue_type": "missing_university_root",
            }
        )

    if units and len(active_university_roots) == 0:
        issues.append(
            {
                "issue_type": "missing_active_university_root",
            }
        )

    if len(university_roots) > 1:
        for unit in university_roots:
            issues.append(
                {
                    "issue_type": "multiple_university_roots",
                    "unit_id": int(unit.id),
                    "unit_type": unit.unit_type,
                }
            )

    if len(active_university_roots) > 1:
        for unit in active_university_roots:
            issues.append(
                {
                    "issue_type": "multiple_active_university_roots",
                    "unit_id": int(unit.id),
                    "unit_type": unit.unit_type,
                }
            )

    for unit in university_roots:
        if not bool(unit.active):
            issues.append(
                {
                    "issue_type": "inactive_university_root",
                    "unit_id": int(unit.id),
                    "unit_type": unit.unit_type,
                }
            )

    for unit in root_units:
        if unit.unit_type != OrgUnitType.UNIVERSITY:
            issues.append(
                {
                    "issue_type": "non_university_root_unit",
                    "unit_id": int(unit.id),
                    "unit_type": unit.unit_type,
                }
            )

    for unit in units:
        unit_id = int(unit.id)
        parent_unit_id = int(unit.parent_unit_id) if unit.parent_unit_id is not None else None

        if parent_unit_id is not None and parent_unit_id == unit_id:
            issues.append(
                {
                    "issue_type": "unit_self_parent",
                    "unit_id": unit_id,
                    "parent_unit_id": parent_unit_id,
                    "unit_type": unit.unit_type,
                }
            )
            continue

        if parent_unit_id is not None and parent_unit_id not in units_by_id:
            issues.append(
                {
                    "issue_type": "unit_missing_parent",
                    "unit_id": unit_id,
                    "parent_unit_id": parent_unit_id,
                    "unit_type": unit.unit_type,
                }
            )

        if parent_unit_id is not None and parent_unit_id in units_by_id:
            parent_unit = units_by_id[parent_unit_id]
            allowed_parents = ALLOWED_PARENT_TYPES.get(unit.unit_type)

            if bool(unit.active) and not bool(parent_unit.active):
                issues.append(
                    {
                        "issue_type": "unit_active_child_inactive_parent",
                        "unit_id": unit_id,
                        "parent_unit_id": parent_unit_id,
                        "unit_type": unit.unit_type,
                    }
                )

            if unit.unit_type == OrgUnitType.UNIVERSITY:
                issues.append(
                    {
                        "issue_type": "unit_invalid_parent_type",
                        "unit_id": unit_id,
                        "parent_unit_id": parent_unit_id,
                        "unit_type": unit.unit_type,
                    }
                )
            elif allowed_parents is not None and parent_unit.unit_type not in allowed_parents:
                issues.append(
                    {
                        "issue_type": "unit_invalid_parent_type",
                        "unit_id": unit_id,
                        "parent_unit_id": parent_unit_id,
                        "unit_type": unit.unit_type,
                    }
                )

    code_to_unit_ids: dict[str, list[int]] = {}
    for unit in units:
        code_to_unit_ids.setdefault(str(unit.code), []).append(int(unit.id))

    for code, unit_ids in code_to_unit_ids.items():
        if len(unit_ids) <= 1:
            continue
        for unit_id in sorted(unit_ids):
            issues.append(
                {
                    "issue_type": "unit_duplicate_code",
                    "unit_id": unit_id,
                    "unit_type": units_by_id[unit_id].unit_type,
                }
            )

    parent_by_id: dict[int, int | None] = {
        int(unit.id): (int(unit.parent_unit_id) if unit.parent_unit_id is not None else None)
        for unit in units
    }
    self_parent_ids = {
        int(unit.id)
        for unit in units
        if unit.parent_unit_id is not None and int(unit.parent_unit_id) == int(unit.id)
    }
    visited: set[int] = set()
    cycle_nodes: set[int] = set()

    for start_id in parent_by_id:
        if start_id in visited:
            continue

        chain_index: dict[int, int] = {}
        chain: list[int] = []
        current_id = start_id

        while current_id is not None:
            if current_id in visited:
                break
            if current_id not in parent_by_id:
                break
            if current_id in chain_index:
                cycle_start = chain_index[current_id]
                cycle_nodes.update(chain[cycle_start:])
                break

            chain_index[current_id] = len(chain)
            chain.append(current_id)

            next_id = parent_by_id[current_id]
            if next_id in self_parent_ids:
                break
            current_id = next_id

        visited.update(chain)

    for unit_id in sorted(cycle_nodes):
        if unit_id in self_parent_ids:
            continue
        issues.append(
            {
                "issue_type": "unit_cycle_detected",
                "unit_id": unit_id,
                "parent_unit_id": parent_by_id.get(unit_id),
                "unit_type": units_by_id[unit_id].unit_type,
            }
        )

    return OrgUnitConsistencyReportSchema(
        unit_count=len(units),
        issue_count=len(issues),
        issues=issues,
    )
