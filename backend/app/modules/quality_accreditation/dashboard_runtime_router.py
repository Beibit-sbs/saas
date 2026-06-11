"""Router for Quality / Accreditation dashboard runtime."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.modules.rbac.security import get_actor, permission_dependency
from app.modules.quality_accreditation import permissions
from app.modules.quality_accreditation.dependencies import get_quality_accreditation_db, require_quality_accreditation_tenant
from app.modules.quality_accreditation.quality_accreditation_dashboard_schemas import DashboardRuntimeResponseDTO
from app.modules.quality_accreditation.quality_accreditation_dashboard_service import dashboard_runtime_service


router = APIRouter(prefix="/api/v1/quality-accreditation", tags=["quality-accreditation-dashboard-runtime"])

_Tenant = Annotated[int, Depends(require_quality_accreditation_tenant)]
_Actor = Annotated[str, Depends(get_actor)]
_DB = Annotated[Session, Depends(get_quality_accreditation_db)]


@router.get("/dashboard-runtime", response_model=DashboardRuntimeResponseDTO)
def get_dashboard_runtime(
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.SUMMARY_READ))],
    tenant: _Tenant,
    db: _DB,
) -> DashboardRuntimeResponseDTO:
    del actor
    return dashboard_runtime_service.get_dashboard_runtime(db=db, tenant_id=tenant)
