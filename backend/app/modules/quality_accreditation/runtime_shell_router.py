"""Router for Quality / Accreditation runtime shell (A-050.5-E1)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.modules.rbac.security import get_actor, permission_dependency
from app.modules.quality_accreditation import permissions
from app.modules.quality_accreditation.dependencies import get_quality_accreditation_db, require_quality_accreditation_tenant
from app.modules.quality_accreditation.quality_accreditation_runtime_shell_service import get_runtime_shell
from app.modules.quality_accreditation.runtime_shell_schemas import QualityAccreditationRuntimeShellResponse


router = APIRouter(prefix="/api/v1/quality-accreditation", tags=["quality-accreditation-runtime-shell"])

_Tenant = Annotated[int, Depends(require_quality_accreditation_tenant)]
_Actor = Annotated[str, Depends(get_actor)]
_DB = Annotated[Session, Depends(get_quality_accreditation_db)]


@router.get("/runtime-shell", response_model=QualityAccreditationRuntimeShellResponse)
def get_quality_accreditation_runtime_shell(
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.SUMMARY_READ))],
    tenant: _Tenant,
    db: _DB,
) -> QualityAccreditationRuntimeShellResponse:
    return get_runtime_shell(db, tenant)
