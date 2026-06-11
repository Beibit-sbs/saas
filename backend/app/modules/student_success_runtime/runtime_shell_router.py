"""Router for Student Success runtime shell (A-051.5-E1)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.modules.rbac.security import get_actor, permission_dependency
from app.modules.student_lifecycle.dependencies import get_student_lifecycle_db, require_student_lifecycle_tenant
from app.modules.student_success_runtime.runtime_shell_schemas import StudentSuccessRuntimeShellResponse
from app.modules.student_success_runtime.student_success_runtime_shell_service import get_runtime_shell


SUMMARY_READ = "student_success.summary.read"

router = APIRouter(prefix="/api/v1/student-success", tags=["student-success-runtime-shell"])

_Tenant = Annotated[int, Depends(require_student_lifecycle_tenant)]
_Actor = Annotated[str, Depends(get_actor)]
_DB = Annotated[Session, Depends(get_student_lifecycle_db)]


@router.get("/runtime-shell", response_model=StudentSuccessRuntimeShellResponse)
def get_student_success_runtime_shell(
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(SUMMARY_READ))],
    tenant: _Tenant,
    db: _DB,
) -> StudentSuccessRuntimeShellResponse:
    return get_runtime_shell(db, tenant)
