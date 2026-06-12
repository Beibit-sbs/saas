"""Router for Curriculum runtime (A-052.7-E1)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.modules.academic_operations.dependencies import get_academic_operations_db, require_academic_operations_tenant
from app.modules.academic_operations_runtime.curriculum_runtime_schemas import CurriculumRuntimeResponse
from app.modules.academic_operations_runtime.curriculum_runtime_service import get_curriculum_runtime
from app.modules.rbac.security import get_actor, permission_dependency


router = APIRouter(prefix="/api/academic-operations/runtime", tags=["academic-operations-curriculum-runtime"])

_Tenant = Annotated[int, Depends(require_academic_operations_tenant)]
_Actor = Annotated[str, Depends(get_actor)]
_DB = Annotated[Session, Depends(get_academic_operations_db)]
SUMMARY_READ_PERMISSION = "academic_operations.summary.read"


@router.get("/curriculum", response_model=CurriculumRuntimeResponse)
def get_curriculum_runtime_endpoint(
    _actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(SUMMARY_READ_PERMISSION))],
    tenant: _Tenant,
    db: _DB,
) -> CurriculumRuntimeResponse:
    return get_curriculum_runtime(db, tenant)