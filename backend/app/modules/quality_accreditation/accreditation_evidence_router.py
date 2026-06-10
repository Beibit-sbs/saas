"""Router for Quality / Accreditation evidence runtime."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.modules.rbac.security import get_actor, permission_dependency
from app.modules.quality_accreditation import permissions
from app.modules.quality_accreditation.dependencies import get_quality_accreditation_db, require_quality_accreditation_tenant
from app.modules.quality_accreditation.quality_accreditation_evidence_schemas import AccreditationEvidenceRuntimeResponse
from app.modules.quality_accreditation.quality_accreditation_evidence_service import accreditation_evidence_runtime_service


router = APIRouter(prefix="/api/v1/quality-accreditation", tags=["quality-accreditation-accreditation-evidence"])

_Tenant = Annotated[int, Depends(require_quality_accreditation_tenant)]
_Actor = Annotated[str, Depends(get_actor)]
_DB = Annotated[Session, Depends(get_quality_accreditation_db)]


@router.get("/accreditation-evidence", response_model=AccreditationEvidenceRuntimeResponse)
def get_accreditation_evidence_runtime(
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.SUMMARY_READ))],
    tenant: _Tenant,
    db: _DB,
) -> AccreditationEvidenceRuntimeResponse:
    del actor
    return accreditation_evidence_runtime_service.get_accreditation_evidence_runtime(db, tenant)
