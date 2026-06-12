"""Teaching Load runtime router (A-052.11-E1)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.modules.academic_operations.dependencies import get_academic_operations_db, require_academic_operations_tenant
from app.modules.academic_operations_runtime.teaching_load_runtime_schemas import TeachingLoadRuntimeResponse
from app.modules.academic_operations_runtime.teaching_load_runtime_service import get_teaching_load_runtime
from app.modules.rbac.security import get_actor, permission_dependency

router = APIRouter(prefix="/api/academic-operations/runtime", tags=["academic-operations-teaching-load-runtime"])

_DB = Annotated[Session, Depends(get_academic_operations_db)]
_Tenant = Annotated[int, Depends(require_academic_operations_tenant)]
_Actor = Annotated[str, Depends(get_actor)]

SUMMARY_READ_PERMISSION = "academic_operations.summary.read"


@router.get("/teaching-load", response_model=TeachingLoadRuntimeResponse)
def get_teaching_load_runtime_endpoint(
    _actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(SUMMARY_READ_PERMISSION))],
    tenant: _Tenant,
    db: _DB,
) -> TeachingLoadRuntimeResponse:
    return get_teaching_load_runtime(db, tenant)