"""FastAPI router for Quality / Accreditation backend foundation."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Body, Depends, HTTPException
from pydantic import BaseModel, ValidationError
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.module_helpers.router_errors import integrity_error_to_http, permission_error_to_http, tenant_not_found_to_http, validation_error_to_http
from app.core.module_helpers.service_validation import DomainValidationError, OptimisticLockConflictError, TenantResourceNotFoundError
from app.modules.rbac.security import get_actor, permission_dependency
from app.modules.quality_accreditation import permissions, service
from app.modules.quality_accreditation.dependencies import get_quality_accreditation_db, require_quality_accreditation_tenant
from app.modules.quality_accreditation.schemas import (
    QualityAuditEventListResponse,
    QualityAuditEventResponse,
    QualityDashboardResponse,
    QualityEvidenceReviewActionRequest,
    QualityHealthResponse,
    QualityLimitationsResponse,
    QualityMatrixSummaryResponse,
    QualityOverviewResponse,
    QualityRecordListResponse,
    QualityRecordRequest,
    QualityRecordResponse,
    QualityStatusHistoryListResponse,
    QualityStatusHistoryResponse,
)


router = APIRouter(prefix="/api/admin/quality-accreditation", tags=["quality-accreditation"])

_Tenant = Annotated[int, Depends(require_quality_accreditation_tenant)]
_Actor = Annotated[str, Depends(get_actor)]
_DB = Annotated[Session, Depends(get_quality_accreditation_db)]


class ErrorDetailResponse(BaseModel):
    detail: Any


def _parse_payload(schema_cls: type[BaseModel], payload: dict[str, Any]) -> BaseModel:
    try:
        return schema_cls.model_validate(payload)
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail=exc.errors()) from exc


def _handle(exc: Exception) -> None:
    if isinstance(exc, PermissionError):
        raise permission_error_to_http(exc)
    if isinstance(exc, TenantResourceNotFoundError):
        raise tenant_not_found_to_http(exc)
    if isinstance(exc, (DomainValidationError, ValueError)):
        raise validation_error_to_http(exc)
    if isinstance(exc, (IntegrityError, OptimisticLockConflictError)):
        raise integrity_error_to_http(exc)
    raise exc


def _resp(obj: Any, schema_cls):
    if isinstance(obj, dict):
        data = dict(obj)
    else:
        data = obj.__dict__.copy()
    if "limitations_json" in data:
        data["limitations"] = list(data.pop("limitations_json") or [])
    if "metadata_json" in data:
        data["metadata"] = dict(data.pop("metadata_json") or {})
    if "summary_json" in data:
        data["summary"] = dict(data.pop("summary_json") or {})
    if "payload_json" in data:
        data["payload"] = dict(data.pop("payload_json") or {})
    return schema_cls.model_validate(data)


@router.get("/health", response_model=QualityHealthResponse)
def get_health(actor: _Actor, _: Annotated[None, Depends(permission_dependency(permissions.HEALTH_READ))], tenant: _Tenant, db: _DB) -> QualityHealthResponse:
    try:
        return service.get_quality_health_service(db, tenant)
    except Exception as exc:
        _handle(exc)


@router.get("/overview", response_model=QualityOverviewResponse)
def get_overview(actor: _Actor, _: Annotated[None, Depends(permission_dependency(permissions.OVERVIEW_READ))], tenant: _Tenant, db: _DB) -> QualityOverviewResponse:
    try:
        return service.get_quality_overview_service(db, tenant)
    except Exception as exc:
        _handle(exc)


@router.get("/dashboard", response_model=QualityDashboardResponse)
def get_dashboard(actor: _Actor, _: Annotated[None, Depends(permission_dependency(permissions.DASHBOARD_READ))], tenant: _Tenant, db: _DB) -> QualityDashboardResponse:
    try:
        return service.get_quality_dashboard_service(db, tenant)
    except Exception as exc:
        _handle(exc)


@router.get("/matrix-summary", response_model=QualityMatrixSummaryResponse)
def get_matrix_summary(actor: _Actor, _: Annotated[None, Depends(permission_dependency(permissions.MATRIX_READ))], tenant: _Tenant, db: _DB) -> QualityMatrixSummaryResponse:
    try:
        return service.get_quality_matrix_summary_service(db, tenant)
    except Exception as exc:
        _handle(exc)


@router.get("/limitations", response_model=QualityLimitationsResponse)
def get_limitations(actor: _Actor, _: Annotated[None, Depends(permission_dependency(permissions.LIMITATIONS_READ))], tenant: _Tenant, db: _DB) -> QualityLimitationsResponse:
    try:
        return service.list_quality_limitations_service(db, tenant)
    except Exception as exc:
        _handle(exc)


def _register_collection_routes(
    path: str,
    resource_key: str,
    *,
    read_permission: str,
    create_permission: str | None = None,
    update_permission: str | None = None,
):
    def list_endpoint(
        actor: str = Depends(get_actor),
        permission_check: None = Depends(permission_dependency(read_permission)),
        tenant: int = Depends(require_quality_accreditation_tenant),
        db: Session = Depends(get_quality_accreditation_db),
    ) -> QualityRecordListResponse:
        try:
            del permission_check
            return QualityRecordListResponse(items=[_resp(item, QualityRecordResponse) for item in service.list_resource_service(db, tenant, resource_key)])
        except Exception as exc:
            _handle(exc)

    list_endpoint.__name__ = f"list_{resource_key}"
    router.add_api_route(path, list_endpoint, methods=["GET"], response_model=QualityRecordListResponse)

    if create_permission is not None:
        def create_endpoint(
            payload: dict[str, Any] = Body(...),
            actor: str = Depends(get_actor),
            permission_check: None = Depends(permission_dependency(create_permission)),
            tenant: int = Depends(require_quality_accreditation_tenant),
            db: Session = Depends(get_quality_accreditation_db),
        ) -> QualityRecordResponse:
            try:
                del permission_check
                body = _parse_payload(QualityRecordRequest, payload)
                return _resp(service.create_resource_service(db, tenant, actor, resource_key, body), QualityRecordResponse)
            except Exception as exc:
                _handle(exc)

        create_endpoint.__name__ = f"create_{resource_key}"
        router.add_api_route(path, create_endpoint, methods=["POST"], response_model=QualityRecordResponse, status_code=201)

    if update_permission is not None:
        def update_endpoint(
            resource_id: int,
            payload: dict[str, Any] = Body(...),
            actor: str = Depends(get_actor),
            permission_check: None = Depends(permission_dependency(update_permission)),
            tenant: int = Depends(require_quality_accreditation_tenant),
            db: Session = Depends(get_quality_accreditation_db),
        ) -> QualityRecordResponse:
            try:
                del permission_check
                body = _parse_payload(QualityRecordRequest, payload)
                return _resp(service.update_resource_service(db, tenant, actor, resource_key, resource_id, body), QualityRecordResponse)
            except Exception as exc:
                _handle(exc)

        update_endpoint.__name__ = f"update_{resource_key}"
        router.add_api_route(f"{path}/{{resource_id}}", update_endpoint, methods=["PATCH"], response_model=QualityRecordResponse)


_register_collection_routes("/frameworks", "frameworks", read_permission=permissions.STANDARDS_READ, create_permission=permissions.STANDARDS_CREATE)
_register_collection_routes("/standards", "standards", read_permission=permissions.STANDARDS_READ, create_permission=permissions.STANDARDS_CREATE, update_permission=permissions.STANDARDS_UPDATE)
_register_collection_routes("/criteria", "criteria", read_permission=permissions.CRITERIA_READ, create_permission=permissions.CRITERIA_CREATE, update_permission=permissions.CRITERIA_UPDATE)
_register_collection_routes("/standards-evidence-requirements", "standards_evidence_requirements", read_permission=permissions.STANDARDS_READ)
_register_collection_routes("/evidence", "evidence", read_permission=permissions.EVIDENCE_READ, create_permission=permissions.EVIDENCE_ATTACH, update_permission=permissions.EVIDENCE_ATTACH)
_register_collection_routes("/evidence-limitations", "evidence_limitations", read_permission=permissions.EVIDENCE_READ)
_register_collection_routes("/program-readiness", "program_readiness", read_permission=permissions.PROGRAM_READINESS_READ, create_permission=permissions.PROGRAM_READINESS_UPDATE, update_permission=permissions.PROGRAM_READINESS_UPDATE)
_register_collection_routes("/institutional-readiness", "institutional_readiness", read_permission=permissions.INSTITUTIONAL_READINESS_READ, create_permission=permissions.INSTITUTIONAL_READINESS_UPDATE, update_permission=permissions.INSTITUTIONAL_READINESS_UPDATE)
_register_collection_routes("/self-assessment", "self_assessment", read_permission=permissions.SELF_ASSESSMENT_READ, create_permission=permissions.SELF_ASSESSMENT_CREATE, update_permission=permissions.SELF_ASSESSMENT_UPDATE)
_register_collection_routes("/self-assessment-sections", "self_assessment_sections", read_permission=permissions.SELF_ASSESSMENT_READ, create_permission=permissions.SELF_ASSESSMENT_CREATE, update_permission=permissions.SELF_ASSESSMENT_UPDATE)
_register_collection_routes("/improvement-plans", "improvement_plans", read_permission=permissions.IMPROVEMENT_PLANS_READ, create_permission=permissions.IMPROVEMENT_PLANS_CREATE, update_permission=permissions.IMPROVEMENT_PLANS_UPDATE)
_register_collection_routes("/improvement-actions", "improvement_actions", read_permission=permissions.IMPROVEMENT_PLANS_READ, create_permission=permissions.IMPROVEMENT_PLANS_CREATE, update_permission=permissions.IMPROVEMENT_PLANS_UPDATE)
_register_collection_routes("/internal-audits", "internal_audits", read_permission=permissions.INTERNAL_AUDITS_READ, create_permission=permissions.INTERNAL_AUDITS_CREATE, update_permission=permissions.INTERNAL_AUDITS_UPDATE)
_register_collection_routes("/audit-findings", "audit_findings", read_permission=permissions.AUDIT_FINDINGS_READ, create_permission=permissions.AUDIT_FINDINGS_UPDATE, update_permission=permissions.AUDIT_FINDINGS_UPDATE)
_register_collection_routes("/program-review", "program_review", read_permission=permissions.PROGRAM_REVIEW_READ, create_permission=permissions.PROGRAM_REVIEW_CREATE, update_permission=permissions.PROGRAM_REVIEW_UPDATE)
_register_collection_routes("/learning-outcomes", "learning_outcomes", read_permission=permissions.LEARNING_OUTCOMES_READ, create_permission=permissions.PROGRAM_REVIEW_CREATE, update_permission=permissions.PROGRAM_REVIEW_UPDATE)
_register_collection_routes("/stakeholder-feedback", "stakeholder_feedback", read_permission=permissions.FEEDBACK_READ, create_permission=permissions.FEEDBACK_METADATA_CREATE)
_register_collection_routes("/committee", "committee", read_permission=permissions.COMMITTEE_READ, update_permission=permissions.COMMITTEE_UPDATE)
_register_collection_routes("/external-review", "external_review", read_permission=permissions.EXTERNAL_REVIEW_READ, update_permission=permissions.EXTERNAL_REVIEW_UPDATE)
_register_collection_routes("/expert-response-plans", "expert_response_plans", read_permission=permissions.EXTERNAL_REVIEW_READ)
_register_collection_routes("/gap-analysis", "gap_analysis", read_permission=permissions.GAP_ANALYSIS_READ, create_permission=permissions.GAP_ANALYSIS_UPDATE, update_permission=permissions.GAP_ANALYSIS_UPDATE)
_register_collection_routes("/calendar", "calendar", read_permission=permissions.CALENDAR_READ, create_permission=permissions.CALENDAR_UPDATE, update_permission=permissions.CALENDAR_UPDATE)
_register_collection_routes("/risk-register", "risk_register", read_permission=permissions.RISK_REGISTER_READ, create_permission=permissions.RISK_REGISTER_UPDATE, update_permission=permissions.RISK_REGISTER_UPDATE)
_register_collection_routes("/bridges", "bridges", read_permission=permissions.BRIDGES_READ, create_permission=permissions.BRIDGES_CREATE)
_register_collection_routes("/brain-signals", "brain_signals", read_permission=permissions.BRAIN_SIGNALS_READ)


@router.post("/evidence/{evidence_id}/review", response_model=QualityRecordResponse, status_code=201)
def review_evidence(evidence_id: int, payload: dict[str, Any] = Body(...), actor: _Actor = None, _: Annotated[None, Depends(permission_dependency(permissions.EVIDENCE_REVIEW))] = None, tenant: _Tenant = None, db: _DB = None) -> QualityRecordResponse:
    try:
        body = _parse_payload(QualityEvidenceReviewActionRequest, payload)
        return _resp(service.review_evidence_service(db, tenant, actor, evidence_id, body), QualityRecordResponse)
    except Exception as exc:
        _handle(exc)


@router.get("/audit", response_model=QualityAuditEventListResponse)
def list_audit_events(actor: _Actor, _: Annotated[None, Depends(permission_dependency(permissions.AUDIT_READ))], tenant: _Tenant, db: _DB) -> QualityAuditEventListResponse:
    try:
        return QualityAuditEventListResponse(items=[_resp(item, QualityAuditEventResponse) for item in service.list_quality_audit_events_service(db, tenant)])
    except Exception as exc:
        _handle(exc)


@router.get("/status-history", response_model=QualityStatusHistoryListResponse)
def list_status_history(actor: _Actor, _: Annotated[None, Depends(permission_dependency(permissions.STATUS_HISTORY_READ))], tenant: _Tenant, db: _DB) -> QualityStatusHistoryListResponse:
    try:
        return QualityStatusHistoryListResponse(items=[_resp(item, QualityStatusHistoryResponse) for item in service.list_quality_status_history_service(db, tenant)])
    except Exception as exc:
        _handle(exc)