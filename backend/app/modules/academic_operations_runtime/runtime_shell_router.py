"""Router for Academic Operations runtime shell (A-052.5-E1)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.modules.academic_operations.dependencies import get_academic_operations_db, require_academic_operations_tenant
from app.modules.academic_operations_runtime.academic_operations_runtime_shell_service import get_runtime_shell
from app.modules.academic_operations_runtime.runtime_shell_schemas import AcademicOperationsRuntimeShellResponse
from app.modules.rbac.security import get_actor, permission_dependency


router = APIRouter(prefix="/api/v1/academic-operations", tags=["academic-operations-runtime-shell"])

_Tenant = Annotated[int, Depends(require_academic_operations_tenant)]
_Actor = Annotated[str, Depends(get_actor)]
_DB = Annotated[Session, Depends(get_academic_operations_db)]
SUMMARY_READ_PERMISSION = "academic_operations.summary.read"


@router.get("/runtime-shell", response_model=AcademicOperationsRuntimeShellResponse)
def get_academic_operations_runtime_shell(
    _actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(SUMMARY_READ_PERMISSION))],
    tenant: _Tenant,
    db: _DB,
) -> AcademicOperationsRuntimeShellResponse:
    return get_runtime_shell(db, tenant)
