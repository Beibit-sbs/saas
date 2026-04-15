from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Body, Depends, HTTPException, status
from pydantic import BaseModel, ValidationError
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
    TenantResourceNotFoundError,
)
from app.core.tenant import get_current_tenant
from app.modules.interventions.dependencies import get_interventions_db
from app.modules.interventions.effectiveness_schemas import (
    CohortAnalyzeRequestSchema,
    CohortAnalyzeResponseSchema,
    CohortFinalizeRequestSchema,
    CohortOutcomeListResponseSchema,
    CohortOutcomeReadSchema,
    CohortReadSchema,
)
from app.modules.interventions.effectiveness_service import InterventionEffectivenessService
from app.modules.rbac.security import get_actor, permission_dependency


router = APIRouter(prefix="/api/admin/interventions/cohorts", tags=["interventions-effectiveness"])


class ErrorDetailResponse(BaseModel):
    detail: Any


def _parse(schema_cls: type, payload: dict[str, Any]) -> Any:
    try:
        return schema_cls.model_validate(payload)
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail=exc.errors()) from exc


def _raise(exc: Exception) -> HTTPException:
    if isinstance(exc, HTTPException):
        return exc
    if isinstance(exc, PermissionError):
        return permission_error_to_http(exc)
    if isinstance(exc, TenantResourceNotFoundError):
        return tenant_not_found_to_http(exc)
    if isinstance(exc, DomainValidationError):
        return validation_error_to_http(exc)
    if isinstance(exc, IntegrityError):
        return integrity_error_to_http(exc)
    if isinstance(exc, ValueError):
        return validation_error_to_http(exc)
    raise HTTPException(status_code=400, detail=str(exc))


_common_errors = {
    400: {"model": ErrorDetailResponse},
    403: {"model": ErrorDetailResponse},
    404: {"model": ErrorDetailResponse},
    409: {"model": ErrorDetailResponse},
}


@router.post(
    "/finalize",
    response_model=CohortReadSchema,
    status_code=status.HTTP_201_CREATED,
    responses=_common_errors,
    dependencies=[Depends(permission_dependency("interventions:execute_playbook"))],
)
def finalize_cohort(
    payload: Annotated[dict[str, Any], Body()],
    tenant_id: Annotated[int, Depends(get_current_tenant)],
    actor: Annotated[str, Depends(get_actor)],
    db: Annotated[Session, Depends(get_interventions_db)],
) -> CohortReadSchema:
    try:
        data = _parse(CohortFinalizeRequestSchema, payload)
        cohort = InterventionEffectivenessService(db).finalize_cohort(
            tenant_id=tenant_id,
            actor=actor,
            payload=data,
        )
        db.commit()
        db.refresh(cohort)
    except Exception as exc:
        db.rollback()
        raise _raise(exc) from exc
    return CohortReadSchema.model_validate(cohort)


@router.get(
    "/{cohort_id}/outcomes",
    response_model=CohortOutcomeListResponseSchema,
    responses=_common_errors,
    dependencies=[Depends(permission_dependency("interventions:view"))],
)
def get_cohort_outcomes(
    cohort_id: int,
    tenant_id: Annotated[int, Depends(get_current_tenant)],
    db: Annotated[Session, Depends(get_interventions_db)],
) -> CohortOutcomeListResponseSchema:
    try:
        items = InterventionEffectivenessService(db).get_outcomes(
            tenant_id=tenant_id,
            cohort_id=cohort_id,
        )
    except Exception as exc:
        raise _raise(exc) from exc
    return CohortOutcomeListResponseSchema(
        items=[CohortOutcomeReadSchema.model_validate(item) for item in items],
        total=len(items),
    )


@router.get(
    "/latest/by-playbook/{playbook_id}",
    response_model=CohortReadSchema,
    responses=_common_errors,
    dependencies=[Depends(permission_dependency("interventions:view"))],
)
def get_latest_by_playbook(
    playbook_id: int,
    tenant_id: Annotated[int, Depends(get_current_tenant)],
    db: Annotated[Session, Depends(get_interventions_db)],
) -> CohortReadSchema:
    try:
        cohort = InterventionEffectivenessService(db).get_latest_by_playbook(
            tenant_id=tenant_id,
            playbook_id=playbook_id,
        )
    except Exception as exc:
        raise _raise(exc) from exc
    return CohortReadSchema.model_validate(cohort)


@router.post(
    "/{cohort_id}/analyze",
    response_model=CohortAnalyzeResponseSchema,
    responses=_common_errors,
    dependencies=[Depends(permission_dependency("interventions:execute_playbook"))],
)
def analyze_cohort(
    cohort_id: int,
    payload: Annotated[dict[str, Any], Body()],
    tenant_id: Annotated[int, Depends(get_current_tenant)],
    actor: Annotated[str, Depends(get_actor)],
    db: Annotated[Session, Depends(get_interventions_db)],
) -> CohortAnalyzeResponseSchema:
    try:
        data = _parse(CohortAnalyzeRequestSchema, payload)
        result = InterventionEffectivenessService(db).analyze_cohort(
            tenant_id=tenant_id,
            cohort_id=cohort_id,
            actor=actor,
            payload=data,
        )
        db.commit()
    except Exception as exc:
        db.rollback()
        raise _raise(exc) from exc
    return CohortAnalyzeResponseSchema.model_validate(result)
