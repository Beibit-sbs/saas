from __future__ import annotations

import csv
import io
from typing import Annotated, Any

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
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
    OptimisticLockConflictError,
    TenantResourceNotFoundError,
)
from app.core.tenant import get_current_tenant
from app.modules.interventions.dependencies import get_interventions_db
from app.modules.interventions.models import InterventionCaseSeverity, InterventionCaseStatus
from app.modules.interventions.schemas import (
    InterventionActionCreateSchema,
    InterventionActionListResponseSchema,
    InterventionActionReadSchema,
    InterventionCaseActionResultSchema,
    InterventionCaseAssignSchema,
    InterventionCaseCreateSchema,
    InterventionCaseListResponseSchema,
    InterventionCaseReadSchema,
    InterventionCaseStatusUpdateSchema,
    InterventionCaseTakeSchema,
)
from app.modules.interventions.service import InterventionService
from app.modules.rbac.security import get_actor, permission_dependency


router = APIRouter(prefix="/api/admin/interventions/cases", tags=["interventions"])


class ErrorDetailResponse(BaseModel):
    detail: Any


def _parse_payload(schema_cls: type[BaseModel], payload: dict[str, Any]) -> BaseModel:
    try:
        return schema_cls.model_validate(payload)
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail=exc.errors()) from exc


def _raise_intervention_http_error(exc: Exception) -> HTTPException:
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


@router.post(
    "",
    response_model=InterventionCaseReadSchema,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorDetailResponse},
        403: {"model": ErrorDetailResponse},
        404: {"model": ErrorDetailResponse},
        409: {"model": ErrorDetailResponse},
    },
)
async def create_case_endpoint(
    payload: dict[str, Any] = Body(...),
    actor: str = Depends(get_actor),
    _: Annotated[None, Depends(permission_dependency("admin.jobs.write"))] = None,
    tenant: dict[str, object] = Depends(get_current_tenant),
    db: Session = Depends(get_interventions_db),
) -> InterventionCaseReadSchema:
    request_model = _parse_payload(InterventionCaseCreateSchema, payload)
    service = InterventionService(db)
    try:
        created = await service.create_case(
            tenant_id=int(tenant["id"]),
            request=request_model,
            actor=actor,
        )
        return InterventionCaseReadSchema.model_validate(created)
    except (PermissionError, ValueError, IntegrityError, TenantResourceNotFoundError, OptimisticLockConflictError) as exc:
        raise _raise_intervention_http_error(exc) from exc


@router.get(
    "",
    response_model=InterventionCaseListResponseSchema,
    responses={403: {"model": ErrorDetailResponse}},
)
async def list_cases_endpoint(
    _: str = Depends(get_actor),
    __: Annotated[None, Depends(permission_dependency("admin.jobs.read"))] = None,
    tenant: dict[str, object] = Depends(get_current_tenant),
    db: Session = Depends(get_interventions_db),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status: InterventionCaseStatus | None = None,
    severity: InterventionCaseSeverity | None = None,
    assignee_ref: str | None = Query(default=None, min_length=2, max_length=255),
    overdue_only: bool = False,
) -> InterventionCaseListResponseSchema:
    service = InterventionService(db)
    total, items = await service.list_cases(
        tenant_id=int(tenant["id"]),
        page=page,
        page_size=page_size,
        status=status,
        severity=severity,
        assignee_ref=assignee_ref,
        overdue_only=overdue_only,
    )
    return InterventionCaseListResponseSchema(
        total=total,
        page=page,
        page_size=page_size,
        items=[InterventionCaseReadSchema.model_validate(item) for item in items],
    )


_CSV_FIELDS = [
    "id", "student_profile_id", "severity", "status",
    "title", "description", "owner_type", "owner_ref",
    "assignee_type", "assignee_ref", "due_at",
    "opened_at", "resolved_at", "created_at", "updated_at",
]


@router.get(
    "/export",
    response_class=StreamingResponse,
    responses={403: {"model": ErrorDetailResponse}},
    summary="Export intervention cases as CSV",
)
async def export_cases_csv_endpoint(
    _: str = Depends(get_actor),
    __: Annotated[None, Depends(permission_dependency("admin.jobs.read"))] = None,
    tenant: dict[str, object] = Depends(get_current_tenant),
    db: Session = Depends(get_interventions_db),
    status: InterventionCaseStatus | None = None,
    severity: InterventionCaseSeverity | None = None,
    assignee_ref: str | None = Query(default=None, min_length=2, max_length=255),
    overdue_only: bool = False,
) -> StreamingResponse:
    service = InterventionService(db)
    _total, items = await service.list_cases(
        tenant_id=int(tenant["id"]),
        page=1,
        page_size=500,
        status=status,
        severity=severity,
        assignee_ref=assignee_ref,
        overdue_only=overdue_only,
    )

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=_CSV_FIELDS, extrasaction="ignore")
    writer.writeheader()
    for item in items:
        row = {f: getattr(item, f, "") for f in _CSV_FIELDS}
        writer.writerow(row)

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=interventions.csv"},
    )


@router.get(
    "/{case_id}",
    response_model=InterventionCaseReadSchema,
    responses={403: {"model": ErrorDetailResponse}, 404: {"model": ErrorDetailResponse}},
)
async def get_case_endpoint(
    case_id: int,
    _: str = Depends(get_actor),
    __: Annotated[None, Depends(permission_dependency("admin.jobs.read"))] = None,
    tenant: dict[str, object] = Depends(get_current_tenant),
    db: Session = Depends(get_interventions_db),
) -> InterventionCaseReadSchema:
    service = InterventionService(db)
    try:
        case = await service.get_case(tenant_id=int(tenant["id"]), case_id=case_id)
        return InterventionCaseReadSchema.model_validate(case)
    except (PermissionError, ValueError, TenantResourceNotFoundError) as exc:
        raise _raise_intervention_http_error(exc) from exc


@router.post(
    "/{case_id}/assign",
    response_model=InterventionCaseReadSchema,
    responses={
        400: {"model": ErrorDetailResponse},
        403: {"model": ErrorDetailResponse},
        404: {"model": ErrorDetailResponse},
        409: {"model": ErrorDetailResponse},
    },
)
async def assign_case_endpoint(
    case_id: int,
    payload: dict[str, Any] = Body(...),
    actor: str = Depends(get_actor),
    _: Annotated[None, Depends(permission_dependency("admin.jobs.write"))] = None,
    tenant: dict[str, object] = Depends(get_current_tenant),
    db: Session = Depends(get_interventions_db),
) -> InterventionCaseReadSchema:
    request_model = _parse_payload(InterventionCaseAssignSchema, payload)
    service = InterventionService(db)
    try:
        case = await service.assign_case(
            tenant_id=int(tenant["id"]),
            case_id=case_id,
            request=request_model,
            actor=actor,
        )
        return InterventionCaseReadSchema.model_validate(case)
    except (PermissionError, ValueError, IntegrityError, TenantResourceNotFoundError, OptimisticLockConflictError) as exc:
        raise _raise_intervention_http_error(exc) from exc


@router.post(
    "/{case_id}/take",
    response_model=InterventionCaseReadSchema,
    responses={
        400: {"model": ErrorDetailResponse},
        403: {"model": ErrorDetailResponse},
        404: {"model": ErrorDetailResponse},
        409: {"model": ErrorDetailResponse},
    },
)
async def take_case_endpoint(
    case_id: int,
    payload: dict[str, Any] = Body(...),
    actor: str = Depends(get_actor),
    _: Annotated[None, Depends(permission_dependency("admin.jobs.write"))] = None,
    tenant: dict[str, object] = Depends(get_current_tenant),
    db: Session = Depends(get_interventions_db),
) -> InterventionCaseReadSchema:
    request_model = _parse_payload(InterventionCaseTakeSchema, payload)
    service = InterventionService(db)
    try:
        case = await service.take_case(
            tenant_id=int(tenant["id"]),
            case_id=case_id,
            request=request_model,
            actor=actor,
        )
        return InterventionCaseReadSchema.model_validate(case)
    except (PermissionError, ValueError, IntegrityError, TenantResourceNotFoundError, OptimisticLockConflictError) as exc:
        raise _raise_intervention_http_error(exc) from exc


@router.post(
    "/{case_id}/status",
    response_model=InterventionCaseReadSchema,
    responses={
        400: {"model": ErrorDetailResponse},
        403: {"model": ErrorDetailResponse},
        404: {"model": ErrorDetailResponse},
        409: {"model": ErrorDetailResponse},
    },
)
async def update_case_status_endpoint(
    case_id: int,
    payload: dict[str, Any] = Body(...),
    actor: str = Depends(get_actor),
    _: Annotated[None, Depends(permission_dependency("admin.jobs.write"))] = None,
    tenant: dict[str, object] = Depends(get_current_tenant),
    db: Session = Depends(get_interventions_db),
) -> InterventionCaseReadSchema:
    request_model = _parse_payload(InterventionCaseStatusUpdateSchema, payload)
    service = InterventionService(db)
    try:
        case = await service.update_case_status(
            tenant_id=int(tenant["id"]),
            case_id=case_id,
            request=request_model,
            actor=actor,
        )
        return InterventionCaseReadSchema.model_validate(case)
    except (PermissionError, ValueError, IntegrityError, TenantResourceNotFoundError, OptimisticLockConflictError) as exc:
        raise _raise_intervention_http_error(exc) from exc


@router.post(
    "/{case_id}/actions",
    response_model=InterventionCaseActionResultSchema,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorDetailResponse},
        403: {"model": ErrorDetailResponse},
        404: {"model": ErrorDetailResponse},
        409: {"model": ErrorDetailResponse},
    },
)
async def add_case_action_endpoint(
    case_id: int,
    payload: dict[str, Any] = Body(...),
    actor: str = Depends(get_actor),
    _: Annotated[None, Depends(permission_dependency("admin.jobs.write"))] = None,
    tenant: dict[str, object] = Depends(get_current_tenant),
    db: Session = Depends(get_interventions_db),
) -> InterventionCaseActionResultSchema:
    request_model = _parse_payload(InterventionActionCreateSchema, payload)
    service = InterventionService(db)
    try:
        case, action = await service.add_case_action(
            tenant_id=int(tenant["id"]),
            case_id=case_id,
            request=request_model,
            actor=actor,
        )
        return InterventionCaseActionResultSchema(
            case=InterventionCaseReadSchema.model_validate(case),
            action=InterventionActionReadSchema.model_validate(action),
        )
    except (PermissionError, ValueError, IntegrityError, TenantResourceNotFoundError, OptimisticLockConflictError) as exc:
        raise _raise_intervention_http_error(exc) from exc


@router.get(
    "/{case_id}/actions",
    response_model=InterventionActionListResponseSchema,
    responses={
        403: {"model": ErrorDetailResponse},
        404: {"model": ErrorDetailResponse},
    },
)
async def list_case_actions_endpoint(
    case_id: int,
    _: str = Depends(get_actor),
    __: Annotated[None, Depends(permission_dependency("admin.jobs.read"))] = None,
    tenant: dict[str, object] = Depends(get_current_tenant),
    db: Session = Depends(get_interventions_db),
    limit: int = Query(default=100, ge=1, le=500),
) -> InterventionActionListResponseSchema:
    service = InterventionService(db)
    try:
        actions = await service.list_case_actions(tenant_id=int(tenant["id"]), case_id=case_id, limit=limit)
        return InterventionActionListResponseSchema(
            total=len(actions),
            items=[InterventionActionReadSchema.model_validate(item) for item in actions],
        )
    except (PermissionError, ValueError, TenantResourceNotFoundError) as exc:
        raise _raise_intervention_http_error(exc) from exc
