from __future__ import annotations

from dataclasses import asdict
from typing import Annotated, Any

from fastapi import APIRouter, Body, Depends, HTTPException, Query, Request
from pydantic import BaseModel, ValidationError
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.module_helpers.audit_helpers import build_audit_action
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
from app.modules.audit.service import log_admin_action
from app.modules.feature_flags.service import is_flag_enabled
from app.modules.interventions.dependencies import get_interventions_db
from app.modules.interventions.risk_service import InterventionRiskService
from app.modules.interventions.schemas import (
    InterventionRiskKpiSummarySchema,
    RiskDetectionRunResultSchema,
    RiskRecommendationAckRequestSchema,
    RiskRecommendationAckResponseSchema,
    RiskStudentHistoryResponseSchema,
    RiskStudentLatestSchema,
)
from app.modules.rbac.security import get_actor, permission_dependency


router = APIRouter(prefix="/api/v1/risk", tags=["risk-v1"])
_RISK_V1_FLAG_KEY = "ai.early_warning_engine"


class ErrorDetailResponse(BaseModel):
    detail: Any


def _audit_risk_action(
    *,
    request: Request,
    tenant_id: int,
    actor: str,
    action: str,
    metadata: dict[str, Any],
) -> None:
    log_admin_action(
        actor=actor,
        tenant_id=tenant_id,
        action=action,
        path=str(request.url.path),
        client_ip=request.client.host if request.client else "unknown",
        correlation_id=getattr(request.state, "request_id", None),
        entity="intervention_risk",
        result="success",
        metadata=metadata,
    )


def _parse_payload(schema_cls: type[BaseModel], payload: dict[str, Any]) -> BaseModel:
    try:
        return schema_cls.model_validate(payload)
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail=exc.errors()) from exc


def _ensure_risk_v1_enabled(tenant_id: int) -> None:
    if not is_flag_enabled(_RISK_V1_FLAG_KEY, tenant_id=tenant_id, default=False):
        raise HTTPException(status_code=403, detail="risk early-warning feature is disabled")


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
    "/score/recompute",
    response_model=RiskDetectionRunResultSchema,
    responses={400: {"model": ErrorDetailResponse}, 403: {"model": ErrorDetailResponse}},
)
async def recompute_risk_scores_endpoint(
    request: Request,
    actor: str = Depends(get_actor),
    _: Annotated[None, Depends(permission_dependency("admin.jobs.write"))] = None,
    tenant: dict[str, object] = Depends(get_current_tenant),
    db: Session = Depends(get_interventions_db),
) -> RiskDetectionRunResultSchema:
    service = InterventionRiskService(db)
    try:
        tenant_id = int(tenant["id"])
        _ensure_risk_v1_enabled(tenant_id)
        result = await service.recompute_scores(tenant_id=tenant_id, actor=actor)
        _audit_risk_action(
            request=request,
            tenant_id=tenant_id,
            actor=actor,
            action=build_audit_action("interventions", "risk_score", "recompute"),
            metadata={
                "thresholds_evaluated": result.thresholds_evaluated,
                "signals_created": result.signals_created,
                "cases_created": result.cases_created,
            },
        )
        return RiskDetectionRunResultSchema(**asdict(result))
    except (PermissionError, ValueError, IntegrityError, TenantResourceNotFoundError, DomainValidationError) as exc:
        raise _raise_intervention_risk_http_error(exc) from exc


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


@router.get(
    "/cohorts/summary",
    response_model=InterventionRiskKpiSummarySchema,
    responses={403: {"model": ErrorDetailResponse}},
)
async def get_risk_cohort_summary_endpoint(
    _: str = Depends(get_actor),
    __: Annotated[None, Depends(permission_dependency("admin.jobs.read"))] = None,
    tenant: dict[str, object] = Depends(get_current_tenant),
    db: Session = Depends(get_interventions_db),
) -> InterventionRiskKpiSummarySchema:
    service = InterventionRiskService(db)
    summary = await service.get_kpi_summary(tenant_id=int(tenant["id"]))
    return InterventionRiskKpiSummarySchema.model_validate(summary)


@router.post(
    "/recommendations/{recommendation_id}/ack",
    response_model=RiskRecommendationAckResponseSchema,
    responses={400: {"model": ErrorDetailResponse}, 403: {"model": ErrorDetailResponse}, 404: {"model": ErrorDetailResponse}},
)
async def acknowledge_risk_recommendation_endpoint(
    recommendation_id: int,
    request: Request,
    payload: dict[str, Any] = Body(default_factory=dict),
    actor: str = Depends(get_actor),
    _: Annotated[None, Depends(permission_dependency("admin.jobs.write"))] = None,
    tenant: dict[str, object] = Depends(get_current_tenant),
    db: Session = Depends(get_interventions_db),
) -> RiskRecommendationAckResponseSchema:
    request_model = _parse_payload(RiskRecommendationAckRequestSchema, payload)
    service = InterventionRiskService(db)
    try:
        tenant_id = int(tenant["id"])
        _ensure_risk_v1_enabled(tenant_id)
        action = await service.acknowledge_recommendation(
            tenant_id=tenant_id,
            recommendation_id=recommendation_id,
            actor=actor,
            note=request_model.note,
        )
        _audit_risk_action(
            request=request,
            tenant_id=tenant_id,
            actor=actor,
            action=build_audit_action("interventions", "risk_recommendation", "ack"),
            metadata={
                "recommendation_id": recommendation_id,
                "action_id": action.id,
                "case_id": action.case_id,
            },
        )
        return RiskRecommendationAckResponseSchema(
            recommendation_id=recommendation_id,
            case_id=action.case_id,
            acknowledged=True,
            action_id=action.id,
            acknowledged_at=action.performed_at,
        )
    except (PermissionError, ValueError, IntegrityError, TenantResourceNotFoundError, DomainValidationError) as exc:
        raise _raise_intervention_risk_http_error(exc) from exc
