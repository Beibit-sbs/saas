"""Router for Timetable runtime (A-052.8-E1)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.modules.academic_operations.dependencies import get_academic_operations_db, require_academic_operations_tenant
from app.modules.academic_operations_runtime.timetable_runtime_schemas import TimetableRuntimeResponse
from app.modules.academic_operations_runtime.timetable_runtime_service import get_timetable_runtime
from app.modules.rbac.security import get_actor, permission_dependency


router = APIRouter(prefix="/api/academic-operations/runtime", tags=["academic-operations-timetable-runtime"])

_Tenant = Annotated[int, Depends(require_academic_operations_tenant)]
_Actor = Annotated[str, Depends(get_actor)]
_DB = Annotated[Session, Depends(get_academic_operations_db)]
SUMMARY_READ_PERMISSION = "academic_operations.summary.read"


@router.get("/timetable", response_model=TimetableRuntimeResponse)
def get_timetable_runtime_endpoint(
    _actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(SUMMARY_READ_PERMISSION))],
    tenant: _Tenant,
    db: _DB,
) -> TimetableRuntimeResponse:
    return get_timetable_runtime(db, tenant)