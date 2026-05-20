"""Rector Assignment Workflow — FastAPI router (24 routes)."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query
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
from app.modules.rector_assignment_workflow import permissions
from app.modules.rector_assignment_workflow.dependencies import get_rector_assignment_db
from app.modules.rector_assignment_workflow.schemas import (
    AssignmentAssignRequest,
    AssignmentCommentListResponse,
    AssignmentCommentResponse,
    AssignmentCreateRequest,
    AssignmentDetailResponse,
    AssignmentEvidenceListResponse,
    AssignmentEvidenceResponse,
    AssignmentListResponse,
    AssignmentReportCreateRequest,
    AssignmentReportListResponse,
    AssignmentReportResponse,
    AssignmentResponse,
    AssignmentTemplateCreateRequest,
    AssignmentTemplateListResponse,
    AssignmentTemplateResponse,
    AssignmentTemplateUpdateRequest,
    AssignmentAuditEventListResponse,
    AssignmentAuditEventResponse,
    CommentCreateRequest,
    DashboardSummaryResponse,
    EscalationRequest,
    EvidenceCreateRequest,
    ReportReviewRequest,
    StatusActionRequest,
    AssignmentUpdateRequest,
)
from app.modules.rector_assignment_workflow.service import (
    accept_assignment,
    add_assignment_comment,
    archive_assignment,
    assign_assignment,
    attach_assignment_evidence,
    cancel_assignment,
    complete_assignment,
    create_assignment,
    create_assignment_template,
    escalate_assignment,
    get_assignment_audit,
    get_assignment_detail,
    get_dashboard_summary,
    list_assignment_comments,
    list_assignment_evidence,
    list_assignment_reports,
    list_assignment_templates,
    list_assignments,
    return_assignment_for_revision,
    review_assignment_report,
    submit_assignment_report,
    update_assignment,
    update_assignment_template,
)

router = APIRouter(prefix="/api/admin/rector-assignments", tags=["rector-assignments"])

_Tenant = Annotated[dict, Depends(get_current_tenant)]
_Actor = Annotated[str, Depends(get_actor)]
_DB = Annotated[Session, Depends(get_rector_assignment_db)]


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


# ---------------------------------------------------------------------------
# Dashboard (must come before /{assignment_id} routes)
# ---------------------------------------------------------------------------

@router.get(
    "/dashboard/summary",
    response_model=DashboardSummaryResponse,
)
def get_dashboard_summary_endpoint(
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.DASHBOARD_READ))],
    tenant: _Tenant,
    db: _DB,
) -> DashboardSummaryResponse:
    tenant_id = int(tenant["id"])
    try:
        data = get_dashboard_summary(tenant_id, db)
        return DashboardSummaryResponse(**data)
    except Exception as exc:
        _handle(exc)


# ---------------------------------------------------------------------------
# Templates (must come before /{assignment_id} routes)
# ---------------------------------------------------------------------------

@router.get("/templates", response_model=AssignmentTemplateListResponse)
def list_templates_endpoint(
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.DASHBOARD_READ))],
    tenant: _Tenant,
    db: _DB,
    active_only: bool = Query(default=True),
) -> AssignmentTemplateListResponse:
    tenant_id = int(tenant["id"])
    try:
        items = list_assignment_templates(tenant_id, db, active_only=active_only)
        return AssignmentTemplateListResponse(items=items, total=len(items))
    except Exception as exc:
        _handle(exc)


@router.post("/templates", response_model=AssignmentTemplateResponse, status_code=201)
def create_template_endpoint(
    body: AssignmentTemplateCreateRequest,
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.TEMPLATES_MANAGE))],
    tenant: _Tenant,
    db: _DB,
) -> AssignmentTemplateResponse:
    tenant_id = int(tenant["id"])
    try:
        tmpl = create_assignment_template(tenant_id, int(actor), body, db)
        return AssignmentTemplateResponse.model_validate(tmpl)
    except Exception as exc:
        _handle(exc)


@router.patch("/templates/{template_id}", response_model=AssignmentTemplateResponse)
def update_template_endpoint(
    template_id: int,
    body: AssignmentTemplateUpdateRequest,
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.TEMPLATES_MANAGE))],
    tenant: _Tenant,
    db: _DB,
) -> AssignmentTemplateResponse:
    tenant_id = int(tenant["id"])
    try:
        tmpl = update_assignment_template(tenant_id, template_id, int(actor), body, db)
        return AssignmentTemplateResponse.model_validate(tmpl)
    except Exception as exc:
        _handle(exc)


# ---------------------------------------------------------------------------
# Core CRUD
# ---------------------------------------------------------------------------

@router.get("", response_model=AssignmentListResponse)
def list_assignments_endpoint(
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.READ_ALL))],
    tenant: _Tenant,
    db: _DB,
    status: list[str] | None = Query(default=None),
    priority: str | None = Query(default=None),
    assignee_user_id: int | None = Query(default=None),
    responsible_unit_id: int | None = Query(default=None),
    overdue_only: bool = Query(default=False),
    search: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> AssignmentListResponse:
    tenant_id = int(tenant["id"])
    try:
        items, total = list_assignments(
            tenant_id, db,
            status=status,
            priority=priority,
            assignee_user_id=assignee_user_id,
            responsible_unit_id=responsible_unit_id,
            overdue_only=overdue_only,
            search=search,
            page=page,
            page_size=page_size,
        )
        has_next = (page * page_size) < total
        return AssignmentListResponse(
            items=[AssignmentResponse.model_validate(a) for a in items],
            total=total,
            page=page,
            page_size=page_size,
            has_next=has_next,
        )
    except Exception as exc:
        _handle(exc)


@router.post("", response_model=AssignmentResponse, status_code=201)
def create_assignment_endpoint(
    body: AssignmentCreateRequest,
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.CREATE))],
    tenant: _Tenant,
    db: _DB,
) -> AssignmentResponse:
    tenant_id = int(tenant["id"])
    try:
        assignment = create_assignment(
            tenant_id=tenant_id,
            originator_user_id=int(actor),
            originator_role=None,
            payload=body,
            db=db,
        )
        return AssignmentResponse.model_validate(assignment)
    except Exception as exc:
        _handle(exc)


@router.get("/{assignment_id}", response_model=AssignmentDetailResponse)
def get_assignment_endpoint(
    assignment_id: int,
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.READ))],
    tenant: _Tenant,
    db: _DB,
) -> AssignmentDetailResponse:
    tenant_id = int(tenant["id"])
    try:
        assignment = get_assignment_detail(tenant_id, assignment_id, db)
        return AssignmentDetailResponse.model_validate(assignment)
    except Exception as exc:
        _handle(exc)


@router.patch("/{assignment_id}", response_model=AssignmentResponse)
def update_assignment_endpoint(
    assignment_id: int,
    body: AssignmentUpdateRequest,
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.STATUS_CHANGE))],
    tenant: _Tenant,
    db: _DB,
) -> AssignmentResponse:
    tenant_id = int(tenant["id"])
    try:
        assignment = update_assignment(tenant_id, assignment_id, int(actor), body, db)
        return AssignmentResponse.model_validate(assignment)
    except Exception as exc:
        _handle(exc)


# ---------------------------------------------------------------------------
# Lifecycle transitions
# ---------------------------------------------------------------------------

@router.post("/{assignment_id}/assign", response_model=AssignmentResponse)
def assign_assignment_endpoint(
    assignment_id: int,
    body: AssignmentAssignRequest,
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.ASSIGN))],
    tenant: _Tenant,
    db: _DB,
) -> AssignmentResponse:
    tenant_id = int(tenant["id"])
    try:
        assignment = assign_assignment(tenant_id, assignment_id, int(actor), None, body, db)
        return AssignmentResponse.model_validate(assignment)
    except Exception as exc:
        _handle(exc)


@router.post("/{assignment_id}/accept", response_model=AssignmentResponse)
def accept_assignment_endpoint(
    assignment_id: int,
    body: StatusActionRequest,
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.ACCEPT))],
    tenant: _Tenant,
    db: _DB,
) -> AssignmentResponse:
    tenant_id = int(tenant["id"])
    try:
        assignment = accept_assignment(tenant_id, assignment_id, int(actor), body, db)
        return AssignmentResponse.model_validate(assignment)
    except Exception as exc:
        _handle(exc)


@router.post("/{assignment_id}/return", response_model=AssignmentResponse)
def return_assignment_endpoint(
    assignment_id: int,
    body: StatusActionRequest,
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.RETURN))],
    tenant: _Tenant,
    db: _DB,
) -> AssignmentResponse:
    tenant_id = int(tenant["id"])
    try:
        reason = body.reason or ""
        assignment = return_assignment_for_revision(tenant_id, assignment_id, int(actor), None, reason, db)
        return AssignmentResponse.model_validate(assignment)
    except Exception as exc:
        _handle(exc)


@router.post("/{assignment_id}/complete", response_model=AssignmentResponse)
def complete_assignment_endpoint(
    assignment_id: int,
    body: StatusActionRequest,
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.COMPLETE))],
    tenant: _Tenant,
    db: _DB,
) -> AssignmentResponse:
    tenant_id = int(tenant["id"])
    try:
        assignment = complete_assignment(tenant_id, assignment_id, int(actor), None, body.comment, db)
        return AssignmentResponse.model_validate(assignment)
    except Exception as exc:
        _handle(exc)


@router.post("/{assignment_id}/escalate", response_model=AssignmentResponse)
def escalate_assignment_endpoint(
    assignment_id: int,
    body: EscalationRequest,
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.ESCALATE))],
    tenant: _Tenant,
    db: _DB,
) -> AssignmentResponse:
    tenant_id = int(tenant["id"])
    try:
        assignment, _ = escalate_assignment(tenant_id, assignment_id, int(actor), None, body, db)
        return AssignmentResponse.model_validate(assignment)
    except Exception as exc:
        _handle(exc)


@router.post("/{assignment_id}/cancel", response_model=AssignmentResponse)
def cancel_assignment_endpoint(
    assignment_id: int,
    body: StatusActionRequest,
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.CANCEL))],
    tenant: _Tenant,
    db: _DB,
) -> AssignmentResponse:
    tenant_id = int(tenant["id"])
    try:
        reason = body.reason or ""
        assignment = cancel_assignment(tenant_id, assignment_id, int(actor), None, reason, db)
        return AssignmentResponse.model_validate(assignment)
    except Exception as exc:
        _handle(exc)


@router.post("/{assignment_id}/archive", response_model=AssignmentResponse)
def archive_assignment_endpoint(
    assignment_id: int,
    body: StatusActionRequest,
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.ARCHIVE))],
    tenant: _Tenant,
    db: _DB,
) -> AssignmentResponse:
    tenant_id = int(tenant["id"])
    try:
        assignment = archive_assignment(tenant_id, assignment_id, int(actor), None, db)
        return AssignmentResponse.model_validate(assignment)
    except Exception as exc:
        _handle(exc)


# ---------------------------------------------------------------------------
# Reports
# ---------------------------------------------------------------------------

@router.get("/{assignment_id}/reports", response_model=AssignmentReportListResponse)
def list_reports_endpoint(
    assignment_id: int,
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.READ))],
    tenant: _Tenant,
    db: _DB,
) -> AssignmentReportListResponse:
    tenant_id = int(tenant["id"])
    try:
        items = list_assignment_reports(tenant_id, assignment_id, db)
        return AssignmentReportListResponse(
            items=[AssignmentReportResponse.model_validate(r) for r in items],
            total=len(items),
        )
    except Exception as exc:
        _handle(exc)


@router.post("/{assignment_id}/reports", response_model=AssignmentReportResponse, status_code=201)
def create_report_endpoint(
    assignment_id: int,
    body: AssignmentReportCreateRequest,
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.REPORT_SUBMIT))],
    tenant: _Tenant,
    db: _DB,
) -> AssignmentReportResponse:
    tenant_id = int(tenant["id"])
    try:
        report = submit_assignment_report(tenant_id, assignment_id, int(actor), body, db)
        return AssignmentReportResponse.model_validate(report)
    except Exception as exc:
        _handle(exc)


@router.patch("/{assignment_id}/reports/{report_id}", response_model=AssignmentReportResponse)
def review_report_endpoint(
    assignment_id: int,
    report_id: int,
    body: ReportReviewRequest,
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.REPORT_REVIEW))],
    tenant: _Tenant,
    db: _DB,
) -> AssignmentReportResponse:
    tenant_id = int(tenant["id"])
    try:
        report = review_assignment_report(tenant_id, assignment_id, report_id, int(actor), None, body, db)
        return AssignmentReportResponse.model_validate(report)
    except Exception as exc:
        _handle(exc)


# ---------------------------------------------------------------------------
# Evidence
# ---------------------------------------------------------------------------

@router.get("/{assignment_id}/evidence", response_model=AssignmentEvidenceListResponse)
def list_evidence_endpoint(
    assignment_id: int,
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.READ))],
    tenant: _Tenant,
    db: _DB,
) -> AssignmentEvidenceListResponse:
    tenant_id = int(tenant["id"])
    try:
        items = list_assignment_evidence(tenant_id, assignment_id, db)
        return AssignmentEvidenceListResponse(
            items=[AssignmentEvidenceResponse.model_validate(e) for e in items],
            total=len(items),
        )
    except Exception as exc:
        _handle(exc)


@router.post("/{assignment_id}/evidence", response_model=AssignmentEvidenceResponse, status_code=201)
def attach_evidence_endpoint(
    assignment_id: int,
    body: EvidenceCreateRequest,
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.EVIDENCE_ATTACH))],
    tenant: _Tenant,
    db: _DB,
) -> AssignmentEvidenceResponse:
    tenant_id = int(tenant["id"])
    try:
        evidence = attach_assignment_evidence(tenant_id, assignment_id, int(actor), body, db)
        return AssignmentEvidenceResponse.model_validate(evidence)
    except Exception as exc:
        _handle(exc)


# ---------------------------------------------------------------------------
# Comments
# ---------------------------------------------------------------------------

@router.get("/{assignment_id}/comments", response_model=AssignmentCommentListResponse)
def list_comments_endpoint(
    assignment_id: int,
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.READ))],
    tenant: _Tenant,
    db: _DB,
    exclude_internal: bool = Query(default=False),
) -> AssignmentCommentListResponse:
    tenant_id = int(tenant["id"])
    try:
        items = list_assignment_comments(tenant_id, assignment_id, db, exclude_internal=exclude_internal)
        return AssignmentCommentListResponse(
            items=[AssignmentCommentResponse.model_validate(c) for c in items],
            total=len(items),
        )
    except Exception as exc:
        _handle(exc)


@router.post("/{assignment_id}/comments", response_model=AssignmentCommentResponse, status_code=201)
def add_comment_endpoint(
    assignment_id: int,
    body: CommentCreateRequest,
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.COMMENT))],
    tenant: _Tenant,
    db: _DB,
) -> AssignmentCommentResponse:
    tenant_id = int(tenant["id"])
    try:
        comment = add_assignment_comment(tenant_id, assignment_id, int(actor), None, body, db)
        return AssignmentCommentResponse.model_validate(comment)
    except Exception as exc:
        _handle(exc)


# ---------------------------------------------------------------------------
# Audit trail
# ---------------------------------------------------------------------------

@router.get("/{assignment_id}/audit", response_model=AssignmentAuditEventListResponse)
def get_audit_endpoint(
    assignment_id: int,
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.AUDIT_READ))],
    tenant: _Tenant,
    db: _DB,
    event_type: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
) -> AssignmentAuditEventListResponse:
    tenant_id = int(tenant["id"])
    try:
        items = get_assignment_audit(tenant_id, assignment_id, db, event_type=event_type, limit=limit)
        return AssignmentAuditEventListResponse(
            items=[AssignmentAuditEventResponse.model_validate(e) for e in items],
            total=len(items),
        )
    except Exception as exc:
        _handle(exc)
