"""Router for Quality / Accreditation readiness monitoring runtime."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.modules.rbac.security import get_actor, permission_dependency
from app.modules.quality_accreditation import permissions
from app.modules.quality_accreditation.dependencies import get_quality_accreditation_db, require_quality_accreditation_tenant
from app.modules.quality_accreditation.quality_accreditation_readiness_monitoring_schemas import ReadinessMonitoringRuntimeResponseDTO
from app.modules.quality_accreditation.quality_accreditation_readiness_monitoring_service import readiness_monitoring_runtime_service


router = APIRouter(prefix="/api/v1/quality-accreditation", tags=["quality-accreditation-readiness-monitoring-runtime"])

_Tenant = Annotated[int, Depends(require_quality_accreditation_tenant)]
_Actor = Annotated[str, Depends(get_actor)]
_DB = Annotated[Session, Depends(get_quality_accreditation_db)]


@router.get("/readiness-monitoring-runtime", response_model=ReadinessMonitoringRuntimeResponseDTO)
def get_readiness_monitoring_runtime(
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.SUMMARY_READ))],
    tenant: _Tenant,
    db: _DB,
) -> ReadinessMonitoringRuntimeResponseDTO:
    del actor
    return readiness_monitoring_runtime_service.get_readiness_monitoring_runtime(db=db, tenant_id=tenant)
