"""Router for Student Success Dashboard runtime (A-051.13-E1)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.modules.rbac.security import get_actor, permission_dependency
from app.modules.student_lifecycle.dependencies import get_student_lifecycle_db
from app.modules.student_success_runtime.dependencies import require_student_success_tenant
from app.modules.student_success_runtime.student_success_dashboard_runtime_schemas import StudentSuccessDashboardRuntimeResponse
from app.modules.student_success_runtime.student_success_dashboard_runtime_service import get_student_success_dashboard_runtime


SUMMARY_READ = "student_success.summary.read"

router = APIRouter(prefix="/api/v1/student-success", tags=["student-success-dashboard-runtime"])

_Tenant = Annotated[int, Depends(require_student_success_tenant)]
_Actor = Annotated[str, Depends(get_actor)]
_DB = Annotated[Session, Depends(get_student_lifecycle_db)]


@router.get("/dashboard", response_model=StudentSuccessDashboardRuntimeResponse)
def get_student_success_dashboard_runtime_surface(
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(SUMMARY_READ))],
    tenant: _Tenant,
    db: _DB,
) -> StudentSuccessDashboardRuntimeResponse:
    return get_student_success_dashboard_runtime(db, tenant)
