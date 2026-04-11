from __future__ import annotations

from typing import Annotated, Any, TypeAlias

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
from app.modules.rbac.security import get_actor, permission_dependency
from app.modules.transcripts.dependencies import get_transcripts_db
from app.modules.transcripts.schemas import (
    StudentTranscriptSchema,
    TranscriptConsistencyReportSchema,
    TranscriptTenantConsistencyReportSchema,
    TranscriptSnapshotSchema,
)
from app.modules.transcripts.service import TranscriptService


class ErrorDetailResponse(BaseModel):
    detail: Any


TrustedTenant: TypeAlias = Annotated[dict[str, object], Depends(get_current_tenant)]
Actor: TypeAlias = Annotated[str, Depends(get_actor)]
TranscriptsDb: TypeAlias = Annotated[Session, Depends(get_transcripts_db)]


def _raise_transcripts_http_error(exc: Exception) -> HTTPException:
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


router = APIRouter(prefix="/api/admin", tags=["transcripts"])


@router.get(
    "/students/{student_id}/transcript",
    summary="Get official student transcript",
    description="Returns ordered transcript items aggregated from enrollments and grades.",
    response_model=StudentTranscriptSchema,
    status_code=status.HTTP_200_OK,
    responses={
        400: {"model": ErrorDetailResponse},
        403: {"model": ErrorDetailResponse},
        404: {"model": ErrorDetailResponse},
    },
)
async def get_student_transcript_endpoint(
    student_id: int = Path(..., gt=0),
    _: Actor = None,
    __: Annotated[None, Depends(permission_dependency("transcripts.read"))] = None,
    tenant: TrustedTenant = None,
    db: TranscriptsDb = None,
) -> StudentTranscriptSchema:
    service = TranscriptService(db)
    try:
        return await service.get_student_transcript(
            tenant_id=int(tenant["id"]),
            student_profile_id=student_id,
        )
    except (PermissionError, ValueError, TenantResourceNotFoundError, DomainValidationError) as exc:
        raise _raise_transcripts_http_error(exc) from exc


@router.post(
    "/students/{student_id}/transcript/snapshot",
    summary="Create immutable transcript snapshot",
    description="Generates current transcript and stores an immutable JSON snapshot.",
    response_model=TranscriptSnapshotSchema,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorDetailResponse},
        403: {"model": ErrorDetailResponse},
        404: {"model": ErrorDetailResponse},
        409: {"model": ErrorDetailResponse},
    },
)
async def create_transcript_snapshot_endpoint(
    student_id: int = Path(..., gt=0),
    actor: Actor = None,
    _: Annotated[None, Depends(permission_dependency("transcripts.write"))] = None,
    tenant: TrustedTenant = None,
    db: TranscriptsDb = None,
) -> TranscriptSnapshotSchema:
    service = TranscriptService(db)
    try:
        return await service.create_transcript_snapshot(
            tenant_id=int(tenant["id"]),
            student_profile_id=student_id,
            actor_id=actor,
        )
    except (
        PermissionError,
        ValueError,
        TenantResourceNotFoundError,
        DomainValidationError,
        OptimisticLockConflictError,
        IntegrityError,
    ) as exc:
        raise _raise_transcripts_http_error(exc) from exc


@router.get(
    "/students/{student_id}/transcript/consistency",
    summary="Get transcript consistency issues",
    description="Read-only reconciliation between enrollments and transcript records for a student.",
    response_model=TranscriptConsistencyReportSchema,
    status_code=status.HTTP_200_OK,
    responses={
        400: {"model": ErrorDetailResponse},
        403: {"model": ErrorDetailResponse},
        404: {"model": ErrorDetailResponse},
    },
)
async def get_student_transcript_consistency_endpoint(
    student_id: int = Path(..., gt=0),
    _: Actor = None,
    __: Annotated[None, Depends(permission_dependency("transcripts.read"))] = None,
    tenant: TrustedTenant = None,
    db: TranscriptsDb = None,
) -> TranscriptConsistencyReportSchema:
    service = TranscriptService(db)
    try:
        return await service.get_student_transcript_consistency_report(
            tenant_id=int(tenant["id"]),
            student_profile_id=student_id,
        )
    except (PermissionError, ValueError, TenantResourceNotFoundError, DomainValidationError) as exc:
        raise _raise_transcripts_http_error(exc) from exc


@router.get(
    "/transcripts/consistency",
    summary="Get tenant transcript consistency report",
    description="Read-only reconciliation summary for all tenant students with transcript anomalies.",
    response_model=TranscriptTenantConsistencyReportSchema,
    status_code=status.HTTP_200_OK,
    responses={
        400: {"model": ErrorDetailResponse},
        403: {"model": ErrorDetailResponse},
    },
)
async def get_tenant_transcript_consistency_endpoint(
    _: Actor = None,
    __: Annotated[None, Depends(permission_dependency("transcripts.read"))] = None,
    tenant: TrustedTenant = None,
    db: TranscriptsDb = None,
) -> TranscriptTenantConsistencyReportSchema:
    service = TranscriptService(db)
    try:
        return await service.list_tenant_transcript_consistency_reports(tenant_id=int(tenant["id"]))
    except (PermissionError, ValueError, DomainValidationError) as exc:
        raise _raise_transcripts_http_error(exc) from exc
