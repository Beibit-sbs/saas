"""Router for Student Attendance Risk runtime (A-051.9-E1)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.modules.rbac.security import get_actor, permission_dependency
from app.modules.student_lifecycle.dependencies import get_student_lifecycle_db, require_student_lifecycle_tenant
from app.modules.student_success_runtime.student_attendance_risk_runtime_schemas import StudentAttendanceRiskRuntimeResponse
from app.modules.student_success_runtime.student_attendance_risk_runtime_service import get_student_attendance_risk_runtime


SUMMARY_READ = "student_success.summary.read"

router = APIRouter(prefix="/api/v1/student-success", tags=["student-attendance-risk-runtime"])

_Tenant = Annotated[int, Depends(require_student_lifecycle_tenant)]
_Actor = Annotated[str, Depends(get_actor)]
_DB = Annotated[Session, Depends(get_student_lifecycle_db)]


@router.get("/attendance-risk", response_model=StudentAttendanceRiskRuntimeResponse)
def get_student_attendance_risk_runtime_surface(
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(SUMMARY_READ))],
    tenant: _Tenant,
    db: _DB,
) -> StudentAttendanceRiskRuntimeResponse:
    return get_student_attendance_risk_runtime(db, tenant)
