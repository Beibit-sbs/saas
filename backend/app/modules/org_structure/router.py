from __future__ import annotations

from typing import Annotated, Optional, TypeAlias

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.module_helpers.router_errors import (
    integrity_error_to_http,
    permission_error_to_http,
    tenant_not_found_to_http,
    validation_error_to_http,
)
from app.core.module_helpers.service_validation import (
    DomainValidationError,
    TenantResourceNotFoundError,
)
from app.core.tenant import get_current_tenant
from app.modules.org_structure.dependencies import get_org_structure_db
from app.modules.org_structure.models import OrgUnitModel, OrgUnitType
from app.modules.org_structure.schemas import (
    OrgUnitConsistencyReportSchema,
    OrgUnitCreateSchema,
    OrgUnitReadSchema,
    OrgUnitTreeNodeSchema,
    OrgUnitUpdateSchema,
)
from app.modules.org_structure import service
from app.modules.rbac.security import permission_dependency

router = APIRouter(prefix="/api/admin/org-units", tags=["org-units"])

TrustedTenant: TypeAlias = Annotated[dict[str, object], Depends(get_current_tenant)]
OrgDb: TypeAlias = Annotated[Session, Depends(get_org_structure_db)]


def _http_error(exc: Exception) -> HTTPException:
    if isinstance(exc, PermissionError):
        return permission_error_to_http(exc)
    if isinstance(exc, TenantResourceNotFoundError):
        return tenant_not_found_to_http(exc)
    if isinstance(exc, DomainValidationError):
        return validation_error_to_http(exc)
    if isinstance(exc, IntegrityError):
        return integrity_error_to_http(exc)
    raise exc


def _build_tree(
    units: list[OrgUnitModel],
    parent_id: int | None,
) -> list[OrgUnitTreeNodeSchema]:
    children = [u for u in units if u.parent_unit_id == parent_id]
    result = []
    for child in sorted(children, key=lambda u: u.name):
        node = OrgUnitTreeNodeSchema(
            id=child.id,
            name=child.name,
            code=child.code,
            unit_type=child.unit_type,
            active=child.active,
            children=_build_tree(units, child.id),
        )
        result.append(node)
    return result


@router.post(
    "",
    response_model=OrgUnitReadSchema,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(permission_dependency("admin.org_units.write"))],
)
def create_org_unit(
    payload: OrgUnitCreateSchema,
    tenant: TrustedTenant,
    db: OrgDb,
) -> OrgUnitReadSchema:
    tenant_id = int(tenant["id"])
    try:
        unit = service.create_org_unit(db, tenant_id, payload)
        db.commit()
    except Exception as exc:
        db.rollback()
        raise _http_error(exc)
    return OrgUnitReadSchema.model_validate(unit)


@router.get(
    "",
    response_model=list[OrgUnitReadSchema],
    dependencies=[Depends(permission_dependency("admin.org_units.read"))],
)
def list_org_units(
    tenant: TrustedTenant,
    db: OrgDb,
    unit_type: Optional[OrgUnitType] = Query(None),
    active_only: bool = Query(True),
) -> list[OrgUnitReadSchema]:
    tenant_id = int(tenant["id"])
    units = service.list_org_units(db, tenant_id, unit_type=unit_type, active_only=active_only)
    return [OrgUnitReadSchema.model_validate(u) for u in units]


@router.get(
    "/tree",
    response_model=list[OrgUnitTreeNodeSchema],
    dependencies=[Depends(permission_dependency("admin.org_units.read"))],
)
def get_tree(
    tenant: TrustedTenant,
    db: OrgDb,
) -> list[OrgUnitTreeNodeSchema]:
    tenant_id = int(tenant["id"])
    all_units = service.get_tree(db, tenant_id)
    return _build_tree(all_units, parent_id=None)


@router.get(
    "/consistency",
    response_model=OrgUnitConsistencyReportSchema,
    dependencies=[Depends(permission_dependency("admin.org_units.read"))],
)
def get_org_unit_consistency(
    tenant: TrustedTenant,
    db: OrgDb,
) -> OrgUnitConsistencyReportSchema:
    tenant_id = int(tenant["id"])
    return service.get_org_unit_consistency_report(db, tenant_id)


@router.get(
    "/{unit_id}",
    response_model=OrgUnitReadSchema,
    dependencies=[Depends(permission_dependency("admin.org_units.read"))],
)
def get_org_unit(
    unit_id: int,
    tenant: TrustedTenant,
    db: OrgDb,
) -> OrgUnitReadSchema:
    tenant_id = int(tenant["id"])
    try:
        unit = service.get_org_unit(db, tenant_id, unit_id)
    except Exception as exc:
        raise _http_error(exc)
    return OrgUnitReadSchema.model_validate(unit)


@router.patch(
    "/{unit_id}",
    response_model=OrgUnitReadSchema,
    dependencies=[Depends(permission_dependency("admin.org_units.write"))],
)
def update_org_unit(
    unit_id: int,
    payload: OrgUnitUpdateSchema,
    tenant: TrustedTenant,
    db: OrgDb,
) -> OrgUnitReadSchema:
    tenant_id = int(tenant["id"])
    try:
        unit = service.update_org_unit(db, tenant_id, unit_id, payload)
        db.commit()
    except Exception as exc:
        db.rollback()
        raise _http_error(exc)
    return OrgUnitReadSchema.model_validate(unit)


@router.delete(
    "/{unit_id}",
    response_model=OrgUnitReadSchema,
    dependencies=[Depends(permission_dependency("admin.org_units.write"))],
)
def deactivate_org_unit(
    unit_id: int,
    tenant: TrustedTenant,
    db: OrgDb,
) -> OrgUnitReadSchema:
    tenant_id = int(tenant["id"])
    try:
        unit = service.deactivate_org_unit(db, tenant_id, unit_id)
        db.commit()
    except Exception as exc:
        db.rollback()
        raise _http_error(exc)
    return OrgUnitReadSchema.model_validate(unit)
