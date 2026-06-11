"""Router for Quality / Accreditation audit findings runtime."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.modules.rbac.security import get_actor, permission_dependency
from app.modules.quality_accreditation import permissions
from app.modules.quality_accreditation.dependencies import get_quality_accreditation_db, require_quality_accreditation_tenant
from app.modules.quality_accreditation.quality_accreditation_audit_findings_schemas import AuditFindingsRuntimeResponseDTO
from app.modules.quality_accreditation.quality_accreditation_audit_findings_service import audit_findings_runtime_service


router = APIRouter(prefix="/api/v1/quality-accreditation", tags=["quality-accreditation-audit-findings-runtime"])

_Tenant = Annotated[int, Depends(require_quality_accreditation_tenant)]
_Actor = Annotated[str, Depends(get_actor)]
_DB = Annotated[Session, Depends(get_quality_accreditation_db)]


@router.get("/audit-findings-runtime", response_model=AuditFindingsRuntimeResponseDTO)
def get_audit_findings_runtime(
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.SUMMARY_READ))],
    tenant: _Tenant,
    db: _DB,
) -> AuditFindingsRuntimeResponseDTO:
    del actor
    return audit_findings_runtime_service.get_audit_findings_runtime(db=db, tenant_id=tenant)
