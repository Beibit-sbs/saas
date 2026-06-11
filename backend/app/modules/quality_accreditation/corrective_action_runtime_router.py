"""Router for Quality / Accreditation corrective action runtime."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.modules.rbac.security import get_actor, permission_dependency
from app.modules.quality_accreditation import permissions
from app.modules.quality_accreditation.dependencies import get_quality_accreditation_db, require_quality_accreditation_tenant
from app.modules.quality_accreditation.quality_accreditation_corrective_action_schemas import CorrectiveActionRuntimeResponse
from app.modules.quality_accreditation.quality_accreditation_corrective_action_service import corrective_action_runtime_service


router = APIRouter(prefix="/api/v1/quality-accreditation", tags=["quality-accreditation-corrective-action-runtime"])

_Tenant = Annotated[int, Depends(require_quality_accreditation_tenant)]
_Actor = Annotated[str, Depends(get_actor)]
_DB = Annotated[Session, Depends(get_quality_accreditation_db)]


@router.get("/corrective-actions", response_model=CorrectiveActionRuntimeResponse)
def get_corrective_action_runtime(
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.SUMMARY_READ))],
    tenant: _Tenant,
    db: _DB,
) -> CorrectiveActionRuntimeResponse:
    del actor
    return corrective_action_runtime_service.get_corrective_action_runtime(db, tenant)
