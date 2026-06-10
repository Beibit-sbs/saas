"""Router for Quality / Accreditation self-assessment runtime."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.modules.rbac.security import get_actor, permission_dependency
from app.modules.quality_accreditation import permissions
from app.modules.quality_accreditation.dependencies import get_quality_accreditation_db, require_quality_accreditation_tenant
from app.modules.quality_accreditation.quality_accreditation_self_assessment_schemas import SelfAssessmentRuntimeResponse
from app.modules.quality_accreditation.quality_accreditation_self_assessment_service import self_assessment_runtime_service


router = APIRouter(prefix="/api/v1/quality-accreditation", tags=["quality-accreditation-self-assessment-runtime"])

_Tenant = Annotated[int, Depends(require_quality_accreditation_tenant)]
_Actor = Annotated[str, Depends(get_actor)]
_DB = Annotated[Session, Depends(get_quality_accreditation_db)]


@router.get("/self-assessment", response_model=SelfAssessmentRuntimeResponse)
def get_self_assessment_runtime(
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.SUMMARY_READ))],
    tenant: _Tenant,
    db: _DB,
) -> SelfAssessmentRuntimeResponse:
    del actor
    return self_assessment_runtime_service.get_self_assessment_runtime(db, tenant)
