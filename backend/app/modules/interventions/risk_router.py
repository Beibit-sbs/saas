from __future__ import annotations

from dataclasses import asdict
from typing import Annotated, Any

from fastapi import APIRouter, Body, Depends, HTTPException, Query
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
from app.modules.interventions.risk_service import InterventionRiskService
from app.modules.interventions.schemas import (
    InterventionRiskKpiSummarySchema,
    OutcomeTrackingReadSchema,
    OutcomeTrackingUpsertSchema,
    RiskDetectionRunResultSchema,
    RiskSignalListResponseSchema,
    RiskSignalReadSchema,
    RiskStudentHistoryResponseSchema,
    RiskStudentLatestSchema,
    RiskThresholdCreateSchema,
    RiskThresholdListResponseSchema,
    RiskThresholdReadSchema,
    RiskThresholdUpdateSchema,
)
from app.modules.rbac.security import get_actor, permission_dependency


router = APIRouter(prefix="/api/admin/interventions/risk", tags=["interventions-risk"])


class ErrorDetailResponse(BaseModel):
    detail: Any


def _parse_payload(schema_cls: type[BaseModel], payload: dict[str, Any]) -> BaseModel:
    try:
        return schema_cls.model_validate(payload)
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail=exc.errors()) from exc


def _raise_intervention_risk_http_error(exc: Exception) -> HTTPException:
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


@router.post(
    "/thresholds",
    response_model=RiskThresholdReadSchema,
    responses={400: {"model": ErrorDetailResponse}, 403: {"model": ErrorDetailResponse}},
)
async def create_risk_threshold_endpoint(
    payload: dict[str, Any] = Body(...),
    _: str = Depends(get_actor),
    __: Annotated[None, Depends(permission_dependency("admin.jobs.write"))] = None,
    tenant: dict[str, object] = Depends(get_current_tenant),
    db: Session = Depends(get_interventions_db),
) -> RiskThresholdReadSchema:
    request_model = _parse_payload(RiskThresholdCreateSchema, payload)
    service = InterventionRiskService(db)
    try:
        row = await service.create_threshold(tenant_id=int(tenant["id"]), request=request_model)
        return RiskThresholdReadSchema.model_validate(row)
    except (PermissionError, ValueError, IntegrityError, TenantResourceNotFoundError, DomainValidationError) as exc:
        raise _raise_intervention_risk_http_error(exc) from exc


@router.get(
    "/thresholds",
    response_model=RiskThresholdListResponseSchema,
    responses={403: {"model": ErrorDetailResponse}},
)
async def list_risk_thresholds_endpoint(
    _: str = Depends(get_actor),
    __: Annotated[None, Depends(permission_dependency("admin.jobs.read"))] = None,
    tenant: dict[str, object] = Depends(get_current_tenant),
    db: Session = Depends(get_interventions_db),
) -> RiskThresholdListResponseSchema:
    service = InterventionRiskService(db)
    rows = await service.list_thresholds(tenant_id=int(tenant["id"]))
    return RiskThresholdListResponseSchema(total=len(rows), items=[RiskThresholdReadSchema.model_validate(i) for i in rows])


@router.patch(
    "/thresholds/{threshold_id}",
    response_model=RiskThresholdReadSchema,
    responses={400: {"model": ErrorDetailResponse}, 403: {"model": ErrorDetailResponse}, 404: {"model": ErrorDetailResponse}},
)
async def update_risk_threshold_endpoint(
    threshold_id: int,
    payload: dict[str, Any] = Body(...),
    _: str = Depends(get_actor),
    __: Annotated[None, Depends(permission_dependency("admin.jobs.write"))] = None,
    tenant: dict[str, object] = Depends(get_current_tenant),
    db: Session = Depends(get_interventions_db),
) -> RiskThresholdReadSchema:
    request_model = _parse_payload(RiskThresholdUpdateSchema, payload)
    service = InterventionRiskService(db)
    try:
        row = await service.update_threshold(
            tenant_id=int(tenant["id"]),
            threshold_id=threshold_id,
            request=request_model,
        )
        return RiskThresholdReadSchema.model_validate(row)
    except (PermissionError, ValueError, IntegrityError, TenantResourceNotFoundError, DomainValidationError) as exc:
        raise _raise_intervention_risk_http_error(exc) from exc


@router.post(
    "/run-detection",
    response_model=RiskDetectionRunResultSchema,
    responses={400: {"model": ErrorDetailResponse}, 403: {"model": ErrorDetailResponse}},
)
async def run_risk_detection_endpoint(
    actor: str = Depends(get_actor),
    _: Annotated[None, Depends(permission_dependency("admin.jobs.write"))] = None,
    tenant: dict[str, object] = Depends(get_current_tenant),
    db: Session = Depends(get_interventions_db),
) -> RiskDetectionRunResultSchema:
    service = InterventionRiskService(db)
    try:
        result = await service.run_daily_detection(tenant_id=int(tenant["id"]), actor=actor)
        return RiskDetectionRunResultSchema(**asdict(result))
    except (PermissionError, ValueError, IntegrityError, TenantResourceNotFoundError, DomainValidationError) as exc:
        raise _raise_intervention_risk_http_error(exc) from exc


@router.get(
    "/signals",
    response_model=RiskSignalListResponseSchema,
    responses={403: {"model": ErrorDetailResponse}},
)
async def list_risk_signals_endpoint(
    _: str = Depends(get_actor),
    __: Annotated[None, Depends(permission_dependency("admin.jobs.read"))] = None,
    tenant: dict[str, object] = Depends(get_current_tenant),
    db: Session = Depends(get_interventions_db),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> RiskSignalListResponseSchema:
    service = InterventionRiskService(db)
    total, rows = await service.list_signals(tenant_id=int(tenant["id"]), page=page, page_size=page_size)
    return RiskSignalListResponseSchema(
        total=total,
        page=page,
        page_size=page_size,
        items=[RiskSignalReadSchema.model_validate(i) for i in rows],
    )


@router.get(
    "/students/{student_profile_id}/latest",
    response_model=RiskStudentLatestSchema,
    responses={403: {"model": ErrorDetailResponse}, 404: {"model": ErrorDetailResponse}},
)
async def get_student_latest_risk_endpoint(
    student_profile_id: int,
    _: str = Depends(get_actor),
    __: Annotated[None, Depends(permission_dependency("admin.jobs.read"))] = None,
    tenant: dict[str, object] = Depends(get_current_tenant),
    db: Session = Depends(get_interventions_db),
) -> RiskStudentLatestSchema:
    service = InterventionRiskService(db)
    try:
        row = await service.get_student_latest_signal(
            tenant_id=int(tenant["id"]),
            student_profile_id=student_profile_id,
        )
        return RiskStudentLatestSchema(
            student_profile_id=row.student_profile_id,
            severity=row.severity,
            signal_type=row.signal_type,
            detected_at=row.detected_at,
            current_value=row.current_value,
            threshold_value=row.threshold_value,
            associated_case_id=row.associated_case_id,
            signal_data_json=row.signal_data_json,
        )
    except (PermissionError, ValueError, TenantResourceNotFoundError, DomainValidationError) as exc:
        raise _raise_intervention_risk_http_error(exc) from exc


@router.get(
    "/students/{student_profile_id}/history",
    response_model=RiskStudentHistoryResponseSchema,
    responses={403: {"model": ErrorDetailResponse}},
)
async def get_student_risk_history_endpoint(
    student_profile_id: int,
    _: str = Depends(get_actor),
    __: Annotated[None, Depends(permission_dependency("admin.jobs.read"))] = None,
    tenant: dict[str, object] = Depends(get_current_tenant),
    db: Session = Depends(get_interventions_db),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> RiskStudentHistoryResponseSchema:
    service = InterventionRiskService(db)
    total, rows = await service.list_student_signal_history(
        tenant_id=int(tenant["id"]),
        student_profile_id=student_profile_id,
        page=page,
        page_size=page_size,
    )
    return RiskStudentHistoryResponseSchema(
        student_profile_id=student_profile_id,
        total=total,
        page=page,
        page_size=page_size,
        items=[
            RiskStudentLatestSchema(
                student_profile_id=item.student_profile_id,
                severity=item.severity,
                signal_type=item.signal_type,
                detected_at=item.detected_at,
                current_value=item.current_value,
                threshold_value=item.threshold_value,
                associated_case_id=item.associated_case_id,
                signal_data_json=item.signal_data_json,
            )
            for item in rows
        ],
    )


@router.put(
    "/outcomes/{case_id}",
    response_model=OutcomeTrackingReadSchema,
    responses={400: {"model": ErrorDetailResponse}, 403: {"model": ErrorDetailResponse}, 404: {"model": ErrorDetailResponse}},
)
async def upsert_outcome_endpoint(
    case_id: int,
    payload: dict[str, Any] = Body(...),
    _: str = Depends(get_actor),
    __: Annotated[None, Depends(permission_dependency("admin.jobs.write"))] = None,
    tenant: dict[str, object] = Depends(get_current_tenant),
    db: Session = Depends(get_interventions_db),
) -> OutcomeTrackingReadSchema:
    request_model = _parse_payload(OutcomeTrackingUpsertSchema, payload)
    service = InterventionRiskService(db)
    try:
        row = await service.upsert_outcome(tenant_id=int(tenant["id"]), case_id=case_id, request=request_model)
        return OutcomeTrackingReadSchema.model_validate(row)
    except (PermissionError, ValueError, IntegrityError, TenantResourceNotFoundError, DomainValidationError) as exc:
        raise _raise_intervention_risk_http_error(exc) from exc


@router.get(
    "/outcomes/{case_id}",
    response_model=OutcomeTrackingReadSchema,
    responses={403: {"model": ErrorDetailResponse}, 404: {"model": ErrorDetailResponse}},
)
async def get_outcome_endpoint(
    case_id: int,
    _: str = Depends(get_actor),
    __: Annotated[None, Depends(permission_dependency("admin.jobs.read"))] = None,
    tenant: dict[str, object] = Depends(get_current_tenant),
    db: Session = Depends(get_interventions_db),
) -> OutcomeTrackingReadSchema:
    service = InterventionRiskService(db)
    try:
        row = await service.get_outcome(tenant_id=int(tenant["id"]), case_id=case_id)
        return OutcomeTrackingReadSchema.model_validate(row)
    except (PermissionError, ValueError, TenantResourceNotFoundError, DomainValidationError) as exc:
        raise _raise_intervention_risk_http_error(exc) from exc


@router.get(
    "/kpi-summary",
    response_model=InterventionRiskKpiSummarySchema,
    responses={403: {"model": ErrorDetailResponse}},
)
async def get_intervention_risk_kpi_summary_endpoint(
    _: str = Depends(get_actor),
    __: Annotated[None, Depends(permission_dependency("admin.jobs.read"))] = None,
    tenant: dict[str, object] = Depends(get_current_tenant),
    db: Session = Depends(get_interventions_db),
) -> InterventionRiskKpiSummarySchema:
    service = InterventionRiskService(db)
    summary = await service.get_kpi_summary(tenant_id=int(tenant["id"]))
    return InterventionRiskKpiSummarySchema.model_validate(summary)
