from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Path, status
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.module_helpers.router_errors import (
    integrity_error_to_http,
    permission_error_to_http,
    tenant_not_found_to_http,
    validation_error_to_http,
)
from app.core.module_helpers.service_validation import (
    DomainValidationError,
    OptimisticLockConflictError,
    TenantResourceNotFoundError,
)
from app.core.tenant import get_current_tenant
from app.modules.degree_progress.dependencies import get_degree_progress_db
from app.modules.degree_progress.schemas import DegreeProgressSchema, GraduationEligibilitySchema
from app.modules.degree_progress.service import DegreeProgressService
from app.modules.rbac.security import get_actor, permission_dependency


class ErrorDetailResponse(BaseModel):
    detail: Any


TrustedTenant = Annotated[dict[str, object], Depends(get_current_tenant)]
Actor = Annotated[str, Depends(get_actor)]
DegreeProgressDb = Annotated[Session, Depends(get_degree_progress_db)]


def _raise_degree_progress_http_error(exc: Exception) -> HTTPException:
    if isinstance(exc, PermissionError):
        return permission_error_to_http(exc)
    if isinstance(exc, TenantResourceNotFoundError):
        return tenant_not_found_to_http(exc)
    if isinstance(exc, DomainValidationError):
        return validation_error_to_http(exc)
    if isinstance(exc, (IntegrityError, OptimisticLockConflictError)):
        return integrity_error_to_http(exc)
    if isinstance(exc, ValueError):
        return validation_error_to_http(exc)
    raise HTTPException(status_code=400, detail=str(exc))


router = APIRouter(prefix="/api/admin", tags=["degree-progress"])


@router.get(
    "/students/{student_id}/degree-progress",
    summary="Evaluate student degree progress",
    description="Returns completed and remaining requirements with graduation readiness signal.",
    response_model=DegreeProgressSchema,
    status_code=status.HTTP_200_OK,
    responses={
        400: {"model": ErrorDetailResponse},
        403: {"model": ErrorDetailResponse},
        404: {"model": ErrorDetailResponse},
    },
)
async def get_degree_progress_endpoint(
    student_id: int = Path(..., gt=0),
    actor: Actor = None,
    _: Annotated[None, Depends(permission_dependency("degree_progress.read"))] = None,
    tenant: TrustedTenant = None,
    db: DegreeProgressDb = None,
) -> DegreeProgressSchema:
    service = DegreeProgressService(db)
    try:
        return await service.evaluate_degree_progress(
            tenant_id=int(tenant["id"]),
            student_profile_id=student_id,
            actor_id=actor,
        )
    except (PermissionError, ValueError, TenantResourceNotFoundError, DomainValidationError) as exc:
        raise _raise_degree_progress_http_error(exc) from exc


@router.get(
    "/students/{student_id}/graduation-eligibility",
    summary="Check graduation eligibility",
    description="Returns final graduation eligibility based on requirements, credits, and GPA.",
    response_model=GraduationEligibilitySchema,
    status_code=status.HTTP_200_OK,
    responses={
        400: {"model": ErrorDetailResponse},
        403: {"model": ErrorDetailResponse},
        404: {"model": ErrorDetailResponse},
    },
)
async def get_graduation_eligibility_endpoint(
    student_id: int = Path(..., gt=0),
    actor: Actor = None,
    _: Annotated[None, Depends(permission_dependency("degree_progress.read"))] = None,
    tenant: TrustedTenant = None,
    db: DegreeProgressDb = None,
) -> GraduationEligibilitySchema:
    service = DegreeProgressService(db)
    try:
        return await service.is_student_eligible_for_graduation(
            tenant_id=int(tenant["id"]),
            student_profile_id=student_id,
            actor_id=actor,
        )
    except (PermissionError, ValueError, TenantResourceNotFoundError, DomainValidationError) as exc:
        raise _raise_degree_progress_http_error(exc) from exc
