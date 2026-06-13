"""Academic Operations Dashboard runtime router (A-052.14-E1)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.modules.academic_operations.dependencies import get_academic_operations_db, require_academic_operations_tenant
from app.modules.academic_operations_runtime.academic_operations_dashboard_runtime_schemas import (
    AcademicOperationsDashboardRuntimeResponse,
)
from app.modules.academic_operations_runtime.academic_operations_dashboard_runtime_service import (
    get_academic_operations_dashboard_runtime,
)
from app.modules.rbac.security import get_actor, permission_dependency

router = APIRouter(prefix="/api/academic-operations/runtime", tags=["academic-operations-dashboard-runtime"])

_DB = Annotated[Session, Depends(get_academic_operations_db)]
_Tenant = Annotated[int, Depends(require_academic_operations_tenant)]
_Actor = Annotated[str, Depends(get_actor)]

SUMMARY_READ_PERMISSION = "academic_operations.summary.read"


@router.get("/dashboard", response_model=AcademicOperationsDashboardRuntimeResponse)
def get_academic_operations_dashboard_runtime_endpoint(
    _actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(SUMMARY_READ_PERMISSION))],
    tenant: _Tenant,
    db: _DB,
) -> AcademicOperationsDashboardRuntimeResponse:
    return get_academic_operations_dashboard_runtime(db, tenant)
