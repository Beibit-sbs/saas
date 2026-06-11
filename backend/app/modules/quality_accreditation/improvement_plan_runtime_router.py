"""Router for Quality / Accreditation improvement plan runtime."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.modules.rbac.security import get_actor, permission_dependency
from app.modules.quality_accreditation import permissions
from app.modules.quality_accreditation.dependencies import get_quality_accreditation_db, require_quality_accreditation_tenant
from app.modules.quality_accreditation.quality_accreditation_improvement_plan_schemas import ImprovementPlanRuntimeResponseDTO
from app.modules.quality_accreditation.quality_accreditation_improvement_plan_service import improvement_plan_runtime_service


router = APIRouter(prefix="/api/v1/quality-accreditation", tags=["quality-accreditation-improvement-plan-runtime"])

_Tenant = Annotated[int, Depends(require_quality_accreditation_tenant)]
_Actor = Annotated[str, Depends(get_actor)]
_DB = Annotated[Session, Depends(get_quality_accreditation_db)]


@router.get("/improvement-plan-runtime", response_model=ImprovementPlanRuntimeResponseDTO)
def get_improvement_plan_runtime(
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.SUMMARY_READ))],
    tenant: _Tenant,
    db: _DB,
) -> ImprovementPlanRuntimeResponseDTO:
    del actor
    return improvement_plan_runtime_service.get_improvement_plan_runtime(db, tenant)
