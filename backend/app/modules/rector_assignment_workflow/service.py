"""Rector Assignment Workflow — Service layer.

Business logic, status transitions, audit event writes, status history writes.
No hard delete. No fake dashboard. No external notification dispatch.
No AI/autonomous status changes. No provider calls.
Tenant fail-closed: tenant_id required on every operation.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.core.module_helpers.audit_helpers import build_audit_action
from app.core.module_helpers.service_validation import (
    DomainValidationError,
    OptimisticLockConflictError,
    TenantRequiredError,
    TenantResourceNotFoundError,
    assert_resource_belongs_to_tenant,
    validate_tenant_id_provided,
    validate_version_match,
)
from app.modules.audit.service import log_admin_action
from app.modules.rector_assignment_workflow.models import (
    AssignmentStatus,
    AuditEventType,
    EscalationStatus,
    ReportStatus,
    RectorAssignment,
    RectorAssignmentAuditEvent,
    RectorAssignmentEscalation,
    RectorAssignmentReport,
    RectorAssignmentTemplate,
)
from app.modules.rector_assignment_workflow.repository import (
    repo_compute_dashboard_summary,
    repo_create_assignee,
    repo_create_audit_event,
    repo_create_comment,
    repo_create_escalation,
    repo_create_evidence,
    repo_create_report,
    repo_create_assignment,
    repo_create_status_history,
    repo_create_task,
    repo_create_template,
    repo_get_report,
    repo_get_template,
    repo_is_user_assignee,
    repo_list_assignees,
    repo_list_audit_events,
    repo_list_comments,
    repo_list_evidence,
    repo_list_reports,
    repo_list_templates,
    repo_require_assignment,
    repo_update_assignment,
    repo_update_template,
)
from app.modules.rector_assignment_workflow.schemas import (
    AssignmentAssignRequest,
    AssignmentCreateRequest,
    AssignmentReportCreateRequest,
    AssignmentTemplateCreateRequest,
    AssignmentTemplateUpdateRequest,
    AssignmentUpdateRequest,
    CommentCreateRequest,
    EscalationRequest,
    EvidenceCreateRequest,
    ReportReviewRequest,
    StatusActionRequest,
)

_MODULE = "rector_assignment_workflow"
_logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Transition guard
# ---------------------------------------------------------------------------

def _assert_transition_allowed(current_status: str, new_status: str) -> None:
    allowed = AssignmentStatus.ALLOWED_TRANSITIONS.get(current_status, frozenset())
    if new_status not in allowed:
        raise DomainValidationError(
            f"transition {current_status} → {new_status} is not allowed"
        )


def _write_audit(
    db: Session,
    tenant_id: int,
    event_type: str,
    entity: str,
    action: str,
    assignment_id: int | None = None,
    actor_user_id: int | None = None,
    actor_role: str | None = None,
    request_id: str | None = None,
    payload: dict | None = None,
) -> RectorAssignmentAuditEvent:
    action_str = build_audit_action(_MODULE, entity, action)
    return repo_create_audit_event(
        db,
        tenant_id=tenant_id,
        event_type=event_type,
        action=action_str,
        assignment_id=assignment_id,
        actor_user_id=actor_user_id,
        actor_role=actor_role,
        request_id=request_id,
        payload_json=payload or {},
    )


def _transition(
    db: Session,
    assignment: RectorAssignment,
    new_status: str,
    actor_user_id: int,
    *,
    actor_role: str | None = None,
    reason: str | None = None,
    request_id: str | None = None,
) -> None:
    _assert_transition_allowed(assignment.status, new_status)
    old_status = assignment.status
    assignment.status = new_status
    assignment.updated_at = datetime.now(UTC)
    repo_create_status_history(
        db,
        tenant_id=assignment.tenant_id,
        assignment_id=assignment.id,
        old_status=old_status,
        new_status=new_status,
        actor_user_id=actor_user_id,
        actor_role=actor_role,
        reason=reason,
        request_id=request_id,
    )


# ---------------------------------------------------------------------------
# Assignment CRUD
# ---------------------------------------------------------------------------

def create_assignment(
    tenant_id: int,
    originator_user_id: int,
    originator_role: str | None,
    payload: AssignmentCreateRequest,
    db: Session,
    *,
    request_id: str | None = None,
) -> RectorAssignment:
    validate_tenant_id_provided(tenant_id)
    assignment = repo_create_assignment(
        db,
        tenant_id=tenant_id,
        title=payload.title,
        description=payload.description,
        category=payload.category,
        priority=payload.priority,
        due_date=payload.due_date,
        responsible_unit_id=payload.responsible_unit_id,
        recurrence_type=payload.recurrence_type,
        originator_user_id=originator_user_id,
        originator_role=originator_role,
        status=AssignmentStatus.DRAFT,
        version=1,
    )
    repo_create_status_history(
        db,
        tenant_id=tenant_id,
        assignment_id=assignment.id,
        old_status=None,
        new_status=AssignmentStatus.DRAFT,
        actor_user_id=originator_user_id,
        actor_role=originator_role,
        request_id=request_id,
    )
    for task in payload.tasks:
        repo_create_task(
            db, tenant_id=tenant_id, assignment_id=assignment.id,
            title=task.title, description=task.description,
            assignee_user_id=task.assignee_user_id,
        )
    _write_audit(
        db, tenant_id, AuditEventType.ASSIGNMENT_CREATED,
        "assignment", "created",
        assignment_id=assignment.id,
        actor_user_id=originator_user_id,
        actor_role=originator_role,
        request_id=request_id,
        payload={"title": payload.title, "status": AssignmentStatus.DRAFT},
    )
    try:
        log_admin_action(
            actor=str(originator_user_id),
            action=build_audit_action(_MODULE, "assignment", "created"),
            entity="rector_assignment",
            entity_id=str(assignment.id),
            result="success",
            tenant_id=tenant_id,
        )
    except Exception:
        pass
    _queue_outbox_event(
        db, tenant_id, assignment.id, OutboxEventType.ASSIGNMENT_CREATED,
        actor_user_id=originator_user_id, actor_role=originator_role,
        request_id=request_id, payload={"title": payload.title},
    )
    db.commit()
    db.refresh(assignment)
    return assignment


def list_assignments(
    tenant_id: int,
    db: Session,
    *,
    status: list[str] | None = None,
    priority: str | None = None,
    due_before: datetime | None = None,
    due_after: datetime | None = None,
    assignee_user_id: int | None = None,
    responsible_unit_id: int | None = None,
    overdue_only: bool = False,
    search: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[RectorAssignment], int]:
    validate_tenant_id_provided(tenant_id)
    return repo_list_assignments(
        db, tenant_id,
        status=status, priority=priority,
        due_before=due_before, due_after=due_after,
        assignee_user_id=assignee_user_id,
        responsible_unit_id=responsible_unit_id,
        overdue_only=overdue_only,
        search=search,
        page=page, page_size=page_size,
    )


def get_assignment_detail(tenant_id: int, assignment_id: int, db: Session) -> RectorAssignment:
    validate_tenant_id_provided(tenant_id)
    return repo_require_assignment(db, tenant_id, assignment_id)


def update_assignment(
    tenant_id: int,
    assignment_id: int,
    actor_user_id: int,
    payload: AssignmentUpdateRequest,
    db: Session,
    *,
    request_id: str | None = None,
) -> RectorAssignment:
    validate_tenant_id_provided(tenant_id)
    assignment = repo_require_assignment(db, tenant_id, assignment_id)
    validate_version_match(assignment.version, payload.version)

    updates: dict = {}
    if payload.title is not None:
        updates["title"] = payload.title
    if payload.description is not None:
        updates["description"] = payload.description
    if payload.priority is not None:
        updates["priority"] = payload.priority
    if payload.due_date is not None:
        updates["due_date"] = payload.due_date
    if payload.responsible_unit_id is not None:
        updates["responsible_unit_id"] = payload.responsible_unit_id
    if payload.category is not None:
        updates["category"] = payload.category
    if updates:
        updates["version"] = assignment.version + 1
        assignment = repo_update_assignment(db, assignment, **updates)
    _write_audit(
        db, tenant_id, AuditEventType.ASSIGNMENT_UPDATED,
        "assignment", "updated",
        assignment_id=assignment.id,
        actor_user_id=actor_user_id,
        request_id=request_id,
        payload={"updates": list(updates.keys())},
    )
    db.commit()
    db.refresh(assignment)
    return assignment


# ---------------------------------------------------------------------------
# Lifecycle transitions
# ---------------------------------------------------------------------------

def assign_assignment(
    tenant_id: int,
    assignment_id: int,
    actor_user_id: int,
    actor_role: str | None,
    payload: AssignmentAssignRequest,
    db: Session,
    *,
    request_id: str | None = None,
) -> RectorAssignment:
    validate_tenant_id_provided(tenant_id)
    assignment = repo_require_assignment(db, tenant_id, assignment_id)
    _transition(
        db, assignment, AssignmentStatus.ASSIGNED, actor_user_id,
        actor_role=actor_role, reason=payload.reason, request_id=request_id,
    )
    assignment.assigned_at = datetime.now(UTC)
    for spec in payload.assignees:
        repo_create_assignee(
            db, tenant_id, assignment_id,
            user_id=spec.user_id,
            unit_id=spec.unit_id,
            role_on_assignment=spec.role_on_assignment,
            assigned_by_user_id=actor_user_id,
            notes=spec.notes,
        )
    _write_audit(
        db, tenant_id, AuditEventType.ASSIGNMENT_ASSIGNED,
        "assignment", "assigned",
        assignment_id=assignment.id,
        actor_user_id=actor_user_id, actor_role=actor_role, request_id=request_id,
        payload={"assignee_count": len(payload.assignees)},
    )
    _queue_outbox_event(
        db, tenant_id, assignment.id, OutboxEventType.ASSIGNMENT_ASSIGNED,
        actor_user_id=actor_user_id, actor_role=actor_role, request_id=request_id,
    )
    db.commit()
    db.refresh(assignment)
    return assignment


def accept_assignment(
    tenant_id: int,
    assignment_id: int,
    actor_user_id: int,
    payload: StatusActionRequest,
    db: Session,
    *,
    request_id: str | None = None,
) -> RectorAssignment:
    validate_tenant_id_provided(tenant_id)
    assignment = repo_require_assignment(db, tenant_id, assignment_id)
    is_assignee = repo_is_user_assignee(db, tenant_id, assignment_id, actor_user_id)
    if not is_assignee:
        raise DomainValidationError("actor is not assigned to this assignment")
    _transition(
        db, assignment, AssignmentStatus.ACCEPTED, actor_user_id,
        request_id=request_id,
    )
    assignment.accepted_at = datetime.now(UTC)
    _write_audit(
        db, tenant_id, AuditEventType.ASSIGNMENT_ACCEPTED,
        "assignment", "accepted",
        assignment_id=assignment.id,
        actor_user_id=actor_user_id, request_id=request_id,
    )
    _queue_outbox_event(
        db, tenant_id, assignment.id, OutboxEventType.ASSIGNMENT_ACCEPTED,
        actor_user_id=actor_user_id, request_id=request_id,
    )
    db.commit()
    db.refresh(assignment)
    return assignment


def submit_assignment_report(
    tenant_id: int,
    assignment_id: int,
    actor_user_id: int,
    payload: AssignmentReportCreateRequest,
    db: Session,
    *,
    request_id: str | None = None,
) -> RectorAssignmentReport:
    validate_tenant_id_provided(tenant_id)
    assignment = repo_require_assignment(db, tenant_id, assignment_id)
    allowed_for_report = {
        AssignmentStatus.ACCEPTED, AssignmentStatus.IN_PROGRESS,
        AssignmentStatus.OVERDUE, AssignmentStatus.RETURNED_FOR_REVISION,
        AssignmentStatus.ESCALATED,
    }
    if assignment.status not in allowed_for_report:
        raise DomainValidationError(
            f"cannot submit report in status {assignment.status}"
        )
    is_assignee = repo_is_user_assignee(db, tenant_id, assignment_id, actor_user_id)
    if not is_assignee:
        raise DomainValidationError("actor is not assigned to this assignment")
    report = repo_create_report(
        db, tenant_id, assignment_id,
        submitted_by_user_id=actor_user_id,
        reporting_period_start=payload.reporting_period_start,
        reporting_period_end=payload.reporting_period_end,
        progress_percent=payload.progress_percent,
        summary=payload.summary,
        blockers=payload.blockers,
        next_steps=payload.next_steps,
        status=ReportStatus.SUBMITTED,
    )
    _transition(
        db, assignment, AssignmentStatus.REPORT_SUBMITTED, actor_user_id,
        request_id=request_id,
    )
    _write_audit(
        db, tenant_id, AuditEventType.REPORT_SUBMITTED,
        "report", "submitted",
        assignment_id=assignment.id,
        actor_user_id=actor_user_id, request_id=request_id,
        payload={"report_id": report.id, "progress_percent": payload.progress_percent},
    )
    _queue_outbox_event(
        db, tenant_id, assignment.id, OutboxEventType.REPORT_SUBMITTED,
        actor_user_id=actor_user_id, request_id=request_id,
        payload={"report_id": report.id},
    )
    db.commit()
    db.refresh(report)
    return report


def attach_assignment_evidence(
    tenant_id: int,
    assignment_id: int,
    actor_user_id: int,
    payload: EvidenceCreateRequest,
    db: Session,
    *,
    request_id: str | None = None,
) -> object:
    validate_tenant_id_provided(tenant_id)
    assignment = repo_require_assignment(db, tenant_id, assignment_id)
    if payload.evidence_type == "LINK":
        if not payload.url or not payload.url.startswith("https://"):
            raise DomainValidationError("url must start with https:// for LINK evidence")
    evidence = repo_create_evidence(
        db, tenant_id, assignment_id,
        report_id=payload.report_id,
        evidence_type=payload.evidence_type,
        file_id=payload.file_id,
        url=payload.url,
        title=payload.title,
        description=payload.description,
        uploaded_by_user_id=actor_user_id,
    )
    _write_audit(
        db, tenant_id, AuditEventType.EVIDENCE_ATTACHED,
        "evidence", "attached",
        assignment_id=assignment.id,
        actor_user_id=actor_user_id, request_id=request_id,
        payload={"evidence_id": evidence.id, "evidence_type": payload.evidence_type},
    )
    _queue_outbox_event(
        db, tenant_id, assignment.id, OutboxEventType.EVIDENCE_ATTACHED,
        actor_user_id=actor_user_id, request_id=request_id,
        payload={"evidence_id": evidence.id},
    )
    db.commit()
    db.refresh(evidence)
    return evidence


def add_assignment_comment(
    tenant_id: int,
    assignment_id: int,
    actor_user_id: int,
    actor_role: str | None,
    payload: CommentCreateRequest,
    db: Session,
    *,
    request_id: str | None = None,
) -> object:
    validate_tenant_id_provided(tenant_id)
    assignment = repo_require_assignment(db, tenant_id, assignment_id)
    comment = repo_create_comment(
        db, tenant_id, assignment_id,
        author_user_id=actor_user_id,
        author_role=actor_role,
        body=payload.body,
        visibility=payload.visibility,
        parent_comment_id=payload.parent_comment_id,
    )
    _write_audit(
        db, tenant_id, AuditEventType.COMMENT_ADDED,
        "comment", "added",
        assignment_id=assignment.id,
        actor_user_id=actor_user_id, request_id=request_id,
        payload={"comment_id": comment.id, "visibility": payload.visibility},
    )
    _queue_outbox_event(
        db, tenant_id, assignment.id, OutboxEventType.COMMENT_ADDED,
        actor_user_id=actor_user_id, actor_role=actor_role, request_id=request_id,
    )
    db.commit()
    db.refresh(comment)
    return comment


def return_assignment_for_revision(
    tenant_id: int,
    assignment_id: int,
    actor_user_id: int,
    actor_role: str | None,
    reason: str,
    db: Session,
    *,
    request_id: str | None = None,
) -> RectorAssignment:
    validate_tenant_id_provided(tenant_id)
    if not reason or not reason.strip():
        raise DomainValidationError("reason is required for return")
    assignment = repo_require_assignment(db, tenant_id, assignment_id)
    _transition(
        db, assignment, AssignmentStatus.RETURNED_FOR_REVISION, actor_user_id,
        actor_role=actor_role, reason=reason, request_id=request_id,
    )
    _write_audit(
        db, tenant_id, AuditEventType.RETURNED_FOR_REVISION,
        "assignment", "returned",
        assignment_id=assignment.id,
        actor_user_id=actor_user_id, actor_role=actor_role, request_id=request_id,
        payload={"reason": reason},
    )
    _queue_outbox_event(
        db, tenant_id, assignment.id, OutboxEventType.RETURNED_FOR_REVISION,
        actor_user_id=actor_user_id, actor_role=actor_role, request_id=request_id,
        payload={"reason": reason},
    )
    db.commit()
    db.refresh(assignment)
    return assignment


def complete_assignment(
    tenant_id: int,
    assignment_id: int,
    actor_user_id: int,
    actor_role: str | None,
    note: str | None,
    db: Session,
    *,
    request_id: str | None = None,
) -> RectorAssignment:
    validate_tenant_id_provided(tenant_id)
    assignment = repo_require_assignment(db, tenant_id, assignment_id)
    _transition(
        db, assignment, AssignmentStatus.COMPLETED, actor_user_id,
        actor_role=actor_role, request_id=request_id,
    )
    assignment.completed_at = datetime.now(UTC)
    _write_audit(
        db, tenant_id, AuditEventType.ASSIGNMENT_COMPLETED,
        "assignment", "completed",
        assignment_id=assignment.id,
        actor_user_id=actor_user_id, actor_role=actor_role, request_id=request_id,
        payload={"note": note},
    )
    _queue_outbox_event(
        db, tenant_id, assignment.id, OutboxEventType.ASSIGNMENT_COMPLETED,
        actor_user_id=actor_user_id, actor_role=actor_role, request_id=request_id,
    )
    db.commit()
    db.refresh(assignment)
    return assignment


def escalate_assignment(
    tenant_id: int,
    assignment_id: int,
    actor_user_id: int,
    actor_role: str | None,
    payload: EscalationRequest,
    db: Session,
    *,
    request_id: str | None = None,
) -> tuple[RectorAssignment, RectorAssignmentEscalation]:
    validate_tenant_id_provided(tenant_id)
    assignment = repo_require_assignment(db, tenant_id, assignment_id)
    _transition(
        db, assignment, AssignmentStatus.ESCALATED, actor_user_id,
        actor_role=actor_role, reason=payload.reason, request_id=request_id,
    )
    escalation = repo_create_escalation(
        db, tenant_id, assignment_id,
        trigger_type="MANUAL",
        escalation_level=payload.escalation_level,
        reason=payload.reason,
        escalated_to_role=payload.escalated_to_role,
        escalated_to_user_id=payload.escalated_to_user_id,
        triggered_by_user_id=actor_user_id,
        status=EscalationStatus.OPEN,
    )
    _write_audit(
        db, tenant_id, AuditEventType.ASSIGNMENT_ESCALATED,
        "assignment", "escalated",
        assignment_id=assignment.id,
        actor_user_id=actor_user_id, actor_role=actor_role, request_id=request_id,
        payload={"escalation_id": escalation.id, "level": payload.escalation_level, "reason": payload.reason},
    )
    _queue_outbox_event(
        db, tenant_id, assignment.id, OutboxEventType.ASSIGNMENT_ESCALATED,
        actor_user_id=actor_user_id, actor_role=actor_role, request_id=request_id,
        payload={"level": payload.escalation_level},
    )
    db.commit()
    db.refresh(assignment)
    db.refresh(escalation)
    return assignment, escalation


def cancel_assignment(
    tenant_id: int,
    assignment_id: int,
    actor_user_id: int,
    actor_role: str | None,
    reason: str,
    db: Session,
    *,
    request_id: str | None = None,
) -> RectorAssignment:
    validate_tenant_id_provided(tenant_id)
    if not reason or not reason.strip():
        raise DomainValidationError("reason is required for cancel")
    assignment = repo_require_assignment(db, tenant_id, assignment_id)
    _transition(
        db, assignment, AssignmentStatus.CANCELLED, actor_user_id,
        actor_role=actor_role, reason=reason, request_id=request_id,
    )
    assignment.cancelled_at = datetime.now(UTC)
    _write_audit(
        db, tenant_id, AuditEventType.ASSIGNMENT_CANCELLED,
        "assignment", "cancelled",
        assignment_id=assignment.id,
        actor_user_id=actor_user_id, actor_role=actor_role, request_id=request_id,
        payload={"reason": reason},
    )
    db.commit()
    db.refresh(assignment)
    return assignment


def archive_assignment(
    tenant_id: int,
    assignment_id: int,
    actor_user_id: int,
    actor_role: str | None,
    db: Session,
    *,
    request_id: str | None = None,
) -> RectorAssignment:
    validate_tenant_id_provided(tenant_id)
    assignment = repo_require_assignment(db, tenant_id, assignment_id)
    _transition(
        db, assignment, AssignmentStatus.ARCHIVED, actor_user_id,
        actor_role=actor_role, request_id=request_id,
    )
    assignment.archived_at = datetime.now(UTC)
    assignment.is_archived = True
    _write_audit(
        db, tenant_id, AuditEventType.ASSIGNMENT_ARCHIVED,
        "assignment", "archived",
        assignment_id=assignment.id,
        actor_user_id=actor_user_id, actor_role=actor_role, request_id=request_id,
    )
    db.commit()
    db.refresh(assignment)
    return assignment


# ---------------------------------------------------------------------------
# Report review
# ---------------------------------------------------------------------------

def review_assignment_report(
    tenant_id: int,
    assignment_id: int,
    report_id: int,
    actor_user_id: int,
    actor_role: str | None,
    payload: ReportReviewRequest,
    db: Session,
    *,
    request_id: str | None = None,
) -> RectorAssignmentReport:
    validate_tenant_id_provided(tenant_id)
    assignment = repo_require_assignment(db, tenant_id, assignment_id)
    report = repo_get_report(db, tenant_id, report_id)
    if report is None or report.assignment_id != assignment_id:
        raise TenantResourceNotFoundError(f"report {report_id} not found for assignment {assignment_id}")
    if report.status != ReportStatus.SUBMITTED:
        raise DomainValidationError(f"report is not in SUBMITTED status (current: {report.status})")

    now = datetime.now(UTC)
    if payload.action == "return":
        if not payload.comment or not payload.comment.strip():
            raise DomainValidationError("comment is required when returning a report")
        report.status = ReportStatus.RETURNED
        report.reviewed_by_user_id = actor_user_id
        report.reviewed_at = now
        report.review_comment = payload.comment
        _transition(
            db, assignment, AssignmentStatus.RETURNED_FOR_REVISION, actor_user_id,
            actor_role=actor_role, reason=payload.comment, request_id=request_id,
        )
        _write_audit(
            db, tenant_id, AuditEventType.RETURNED_FOR_REVISION,
            "assignment", "returned",
            assignment_id=assignment.id,
            actor_user_id=actor_user_id, actor_role=actor_role, request_id=request_id,
            payload={"report_id": report_id},
        )
    else:
        report.status = ReportStatus.ACCEPTED
        report.reviewed_by_user_id = actor_user_id
        report.reviewed_at = now
        report.review_comment = payload.comment
        _write_audit(
            db, tenant_id, AuditEventType.REPORT_SUBMITTED,
            "report", "reviewed",
            assignment_id=assignment.id,
            actor_user_id=actor_user_id, request_id=request_id,
            payload={"report_id": report_id, "action": "approved"},
        )
    db.commit()
    db.refresh(report)
    return report


# ---------------------------------------------------------------------------
# Audit trail
# ---------------------------------------------------------------------------

def get_assignment_audit(
    tenant_id: int,
    assignment_id: int,
    db: Session,
    *,
    event_type: str | None = None,
    actor_user_id: int | None = None,
    limit: int = 100,
) -> list[RectorAssignmentAuditEvent]:
    validate_tenant_id_provided(tenant_id)
    repo_require_assignment(db, tenant_id, assignment_id)
    return repo_list_audit_events(
        db, tenant_id, assignment_id,
        event_type=event_type,
        actor_user_id=actor_user_id,
        limit=min(limit, 500),
    )


# ---------------------------------------------------------------------------
# Dashboard summary
# ---------------------------------------------------------------------------

def get_dashboard_summary(tenant_id: int, db: Session) -> dict:
    validate_tenant_id_provided(tenant_id)
    result = repo_compute_dashboard_summary(db, tenant_id)
    assert result["fake_metrics"] is False, "dashboard must never emit fake_metrics=True"
    assert result["data_source"] == "computed_from_assignments"
    try:
        expanded = repo_compute_expanded_dashboard_fields(db, tenant_id)
        result.update(expanded)
    except Exception:
        _logger.exception("expanded dashboard fields computation failed — returning base fields only")
    return result


# ---------------------------------------------------------------------------
# Templates
# ---------------------------------------------------------------------------

def create_assignment_template(
    tenant_id: int,
    actor_user_id: int,
    payload: AssignmentTemplateCreateRequest,
    db: Session,
    *,
    request_id: str | None = None,
) -> RectorAssignmentTemplate:
    validate_tenant_id_provided(tenant_id)
    template = repo_create_template(
        db, tenant_id,
        name=payload.name,
        description=payload.description,
        category=payload.category,
        default_priority=payload.default_priority,
        default_due_days=payload.default_due_days,
        default_recurrence_type=payload.default_recurrence_type,
        template_body={"tasks": payload.template_body} if payload.template_body else None,
        created_by_user_id=actor_user_id,
    )
    _write_audit(
        db, tenant_id, AuditEventType.TEMPLATE_CREATED,
        "template", "created",
        actor_user_id=actor_user_id, request_id=request_id,
        payload={"template_id": template.id, "name": payload.name},
    )
    db.commit()
    db.refresh(template)
    return template


def update_assignment_template(
    tenant_id: int,
    template_id: int,
    actor_user_id: int,
    payload: AssignmentTemplateUpdateRequest,
    db: Session,
    *,
    request_id: str | None = None,
) -> RectorAssignmentTemplate:
    validate_tenant_id_provided(tenant_id)
    template = repo_get_template(db, tenant_id, template_id)
    if template is None:
        raise TenantResourceNotFoundError(f"template {template_id} not found")
    updates: dict = {}
    for field in ("name", "description", "category", "default_priority",
                  "default_due_days", "default_recurrence_type", "is_active"):
        val = getattr(payload, field, None)
        if val is not None:
            updates[field] = val
    if payload.template_body is not None:
        updates["template_body"] = {"tasks": payload.template_body}
    if updates:
        template = repo_update_template(db, template, **updates)
    _write_audit(
        db, tenant_id, AuditEventType.TEMPLATE_UPDATED,
        "template", "updated",
        actor_user_id=actor_user_id, request_id=request_id,
        payload={"template_id": template_id, "updates": list(updates.keys())},
    )
    db.commit()
    db.refresh(template)
    return template


def list_assignment_templates(
    tenant_id: int,
    db: Session,
    *,
    active_only: bool = True,
) -> list[RectorAssignmentTemplate]:
    validate_tenant_id_provided(tenant_id)
    return repo_list_templates(db, tenant_id, active_only=active_only)


# ---------------------------------------------------------------------------
# Sub-resource lists
# ---------------------------------------------------------------------------

def list_assignment_reports(tenant_id: int, assignment_id: int, db: Session) -> list:
    validate_tenant_id_provided(tenant_id)
    repo_require_assignment(db, tenant_id, assignment_id)
    return repo_list_reports(db, tenant_id, assignment_id)


def list_assignment_evidence(tenant_id: int, assignment_id: int, db: Session) -> list:
    validate_tenant_id_provided(tenant_id)
    repo_require_assignment(db, tenant_id, assignment_id)
    return repo_list_evidence(db, tenant_id, assignment_id)


def list_assignment_comments(
    tenant_id: int, assignment_id: int, db: Session,
    *, exclude_internal: bool = False,
) -> list:
    validate_tenant_id_provided(tenant_id)
    repo_require_assignment(db, tenant_id, assignment_id)
    return repo_list_comments(db, tenant_id, assignment_id, exclude_internal=exclude_internal)


# ---------------------------------------------------------------------------
# A-031.5-RUNTIME: Outbox service helpers (imported at end to avoid circular deps)
# ---------------------------------------------------------------------------

from app.modules.rector_assignment_workflow.models import (  # noqa: E402
    OutboxEventType,
    RectorAssignmentEscalationPolicy,
    RectorAssignmentOutboxEvent,
    RectorAssignmentSlaPolicy,
)
from app.modules.rector_assignment_workflow.repository import (  # noqa: E402
    repo_archive_escalation_policy,
    repo_archive_sla_policy,
    repo_cancel_outbox_event,
    repo_compute_expanded_dashboard_fields,
    repo_create_escalation_policy,
    repo_create_outbox_event,
    repo_create_sla_policy,
    repo_get_escalation_policy,
    repo_get_outbox_event,
    repo_get_sla_policy,
    repo_list_assignment_outbox_events,
    repo_list_escalation_policies,
    repo_list_outbox_events,
    repo_list_sla_policies,
    repo_mark_outbox_event_ready,
    repo_update_escalation_policy,
    repo_update_sla_policy,
)
from app.modules.rector_assignment_workflow.schemas import (  # noqa: E402
    RectorAssignmentEscalationPolicyCreateRequest,
    RectorAssignmentEscalationPolicyUpdateRequest,
    RectorAssignmentSlaPolicyCreateRequest,
    RectorAssignmentSlaPolicyUpdateRequest,
)


def _queue_outbox_event(
    db: Session,
    tenant_id: int,
    assignment_id: int,
    event_type: str,
    *,
    actor_user_id: int | None = None,
    actor_role: str | None = None,
    request_id: str | None = None,
    payload: dict | None = None,
) -> RectorAssignmentOutboxEvent:
    """Create an outbox event row + audit it. No external dispatch."""
    event = repo_create_outbox_event(
        db,
        tenant_id=tenant_id,
        assignment_id=assignment_id,
        event_type=event_type,
        payload_json=payload or {},
    )
    _write_audit(
        db, tenant_id, AuditEventType.OUTBOX_EVENT_CREATED,
        "outbox_event", "created",
        assignment_id=assignment_id,
        actor_user_id=actor_user_id,
        actor_role=actor_role,
        request_id=request_id,
        payload={"outbox_event_id": event.id, "event_type": event_type},
    )
    return event


# ---------------------------------------------------------------------------
# Outbox management service functions
# ---------------------------------------------------------------------------

def list_assignment_outbox_events(
    tenant_id: int,
    assignment_id: int,
    db: Session,
    *,
    status: str | None = None,
    page: int = 1,
    page_size: int = 50,
) -> tuple[list[RectorAssignmentOutboxEvent], int]:
    validate_tenant_id_provided(tenant_id)
    repo_require_assignment(db, tenant_id, assignment_id)
    return repo_list_assignment_outbox_events(
        db, tenant_id, assignment_id, status=status, page=page, page_size=page_size,
    )


def list_outbox_events(
    tenant_id: int,
    db: Session,
    *,
    status: str | None = None,
    page: int = 1,
    page_size: int = 50,
) -> tuple[list[RectorAssignmentOutboxEvent], int]:
    validate_tenant_id_provided(tenant_id)
    return repo_list_outbox_events(db, tenant_id, status=status, page=page, page_size=page_size)


def mark_outbox_event_ready(
    tenant_id: int,
    assignment_id: int,
    event_id: int,
    actor_user_id: int,
    db: Session,
    *,
    request_id: str | None = None,
) -> RectorAssignmentOutboxEvent:
    validate_tenant_id_provided(tenant_id)
    repo_require_assignment(db, tenant_id, assignment_id)
    event = repo_get_outbox_event(db, tenant_id, event_id)
    if event is None or event.assignment_id != assignment_id:
        raise TenantResourceNotFoundError(f"outbox event {event_id} not found")
    if event.status != "PENDING":
        raise DomainValidationError(f"outbox event is not PENDING (current: {event.status})")
    event = repo_mark_outbox_event_ready(db, event)
    _write_audit(
        db, tenant_id, AuditEventType.OUTBOX_EVENT_READY_MARKED,
        "outbox_event", "ready_marked",
        assignment_id=assignment_id,
        actor_user_id=actor_user_id, request_id=request_id,
        payload={"outbox_event_id": event_id},
    )
    db.commit()
    db.refresh(event)
    return event


def cancel_outbox_event(
    tenant_id: int,
    assignment_id: int,
    event_id: int,
    actor_user_id: int,
    db: Session,
    *,
    request_id: str | None = None,
) -> RectorAssignmentOutboxEvent:
    validate_tenant_id_provided(tenant_id)
    repo_require_assignment(db, tenant_id, assignment_id)
    event = repo_get_outbox_event(db, tenant_id, event_id)
    if event is None or event.assignment_id != assignment_id:
        raise TenantResourceNotFoundError(f"outbox event {event_id} not found")
    if event.status not in ("PENDING", "READY"):
        raise DomainValidationError(f"outbox event cannot be cancelled in status {event.status}")
    event = repo_cancel_outbox_event(db, event)
    _write_audit(
        db, tenant_id, AuditEventType.OUTBOX_EVENT_CANCELLED,
        "outbox_event", "cancelled",
        assignment_id=assignment_id,
        actor_user_id=actor_user_id, request_id=request_id,
        payload={"outbox_event_id": event_id},
    )
    db.commit()
    db.refresh(event)
    return event


# ---------------------------------------------------------------------------
# SLA Policy service functions
# ---------------------------------------------------------------------------

def create_sla_policy(
    tenant_id: int,
    actor_user_id: int,
    payload: RectorAssignmentSlaPolicyCreateRequest,
    db: Session,
    *,
    request_id: str | None = None,
) -> RectorAssignmentSlaPolicy:
    validate_tenant_id_provided(tenant_id)
    policy = repo_create_sla_policy(
        db,
        tenant_id=tenant_id,
        name=payload.name,
        priority=payload.priority,
        due_days=payload.due_days,
        warning_before_hours=payload.warning_before_hours,
        overdue_after_hours=payload.overdue_after_hours,
        escalation_after_hours=payload.escalation_after_hours,
        created_by_user_id=actor_user_id,
    )
    _write_audit(
        db, tenant_id, AuditEventType.SLA_POLICY_CREATED,
        "sla_policy", "created",
        actor_user_id=actor_user_id, request_id=request_id,
        payload={"policy_id": policy.id, "name": payload.name},
    )
    db.commit()
    db.refresh(policy)
    return policy


def list_sla_policies(
    tenant_id: int,
    db: Session,
    *,
    active_only: bool = True,
    page: int = 1,
    page_size: int = 50,
) -> tuple[list[RectorAssignmentSlaPolicy], int]:
    validate_tenant_id_provided(tenant_id)
    return repo_list_sla_policies(db, tenant_id, active_only=active_only, page=page, page_size=page_size)


def update_sla_policy(
    tenant_id: int,
    policy_id: int,
    actor_user_id: int,
    payload: RectorAssignmentSlaPolicyUpdateRequest,
    db: Session,
    *,
    request_id: str | None = None,
) -> RectorAssignmentSlaPolicy:
    validate_tenant_id_provided(tenant_id)
    policy = repo_get_sla_policy(db, tenant_id, policy_id)
    if policy is None:
        raise TenantResourceNotFoundError(f"SLA policy {policy_id} not found")
    if not policy.is_active:
        raise DomainValidationError("cannot update archived SLA policy")
    updates: dict = {}
    for field in ("name", "priority", "due_days", "warning_before_hours",
                  "overdue_after_hours", "escalation_after_hours"):
        val = getattr(payload, field, None)
        if val is not None:
            updates[field] = val
    if updates:
        policy = repo_update_sla_policy(db, policy, **updates)
    _write_audit(
        db, tenant_id, AuditEventType.SLA_POLICY_UPDATED,
        "sla_policy", "updated",
        actor_user_id=actor_user_id, request_id=request_id,
        payload={"policy_id": policy_id, "updates": list(updates.keys())},
    )
    db.commit()
    db.refresh(policy)
    return policy


def archive_sla_policy(
    tenant_id: int,
    policy_id: int,
    actor_user_id: int,
    db: Session,
    *,
    request_id: str | None = None,
) -> RectorAssignmentSlaPolicy:
    validate_tenant_id_provided(tenant_id)
    policy = repo_get_sla_policy(db, tenant_id, policy_id)
    if policy is None:
        raise TenantResourceNotFoundError(f"SLA policy {policy_id} not found")
    if not policy.is_active:
        raise DomainValidationError("SLA policy is already archived")
    policy = repo_archive_sla_policy(db, policy)
    _write_audit(
        db, tenant_id, AuditEventType.SLA_POLICY_ARCHIVED,
        "sla_policy", "archived",
        actor_user_id=actor_user_id, request_id=request_id,
        payload={"policy_id": policy_id},
    )
    db.commit()
    db.refresh(policy)
    return policy


# ---------------------------------------------------------------------------
# Escalation Policy service functions
# ---------------------------------------------------------------------------

def create_escalation_policy(
    tenant_id: int,
    actor_user_id: int,
    payload: RectorAssignmentEscalationPolicyCreateRequest,
    db: Session,
    *,
    request_id: str | None = None,
) -> RectorAssignmentEscalationPolicy:
    validate_tenant_id_provided(tenant_id)
    policy = repo_create_escalation_policy(
        db,
        tenant_id=tenant_id,
        assignment_priority=payload.assignment_priority,
        escalation_level=payload.escalation_level,
        escalate_to_role=payload.escalate_to_role,
        escalate_after_hours=payload.escalate_after_hours,
        require_manual_confirmation=payload.require_manual_confirmation,
        created_by_user_id=actor_user_id,
    )
    _write_audit(
        db, tenant_id, AuditEventType.ESCALATION_POLICY_CREATED,
        "escalation_policy", "created",
        actor_user_id=actor_user_id, request_id=request_id,
        payload={"policy_id": policy.id, "level": payload.escalation_level},
    )
    db.commit()
    db.refresh(policy)
    return policy


def list_escalation_policies(
    tenant_id: int,
    db: Session,
    *,
    active_only: bool = True,
    page: int = 1,
    page_size: int = 50,
) -> tuple[list[RectorAssignmentEscalationPolicy], int]:
    validate_tenant_id_provided(tenant_id)
    return repo_list_escalation_policies(
        db, tenant_id, active_only=active_only, page=page, page_size=page_size,
    )


def update_escalation_policy(
    tenant_id: int,
    policy_id: int,
    actor_user_id: int,
    payload: RectorAssignmentEscalationPolicyUpdateRequest,
    db: Session,
    *,
    request_id: str | None = None,
) -> RectorAssignmentEscalationPolicy:
    validate_tenant_id_provided(tenant_id)
    policy = repo_get_escalation_policy(db, tenant_id, policy_id)
    if policy is None:
        raise TenantResourceNotFoundError(f"escalation policy {policy_id} not found")
    if not policy.is_active:
        raise DomainValidationError("cannot update archived escalation policy")
    updates: dict = {}
    for field in ("assignment_priority", "escalation_level", "escalate_to_role",
                  "escalate_after_hours", "require_manual_confirmation"):
        val = getattr(payload, field, None)
        if val is not None:
            updates[field] = val
    if updates:
        policy = repo_update_escalation_policy(db, policy, **updates)
    _write_audit(
        db, tenant_id, AuditEventType.ESCALATION_POLICY_UPDATED,
        "escalation_policy", "updated",
        actor_user_id=actor_user_id, request_id=request_id,
        payload={"policy_id": policy_id, "updates": list(updates.keys())},
    )
    db.commit()
    db.refresh(policy)
    return policy


def archive_escalation_policy(
    tenant_id: int,
    policy_id: int,
    actor_user_id: int,
    db: Session,
    *,
    request_id: str | None = None,
) -> RectorAssignmentEscalationPolicy:
    validate_tenant_id_provided(tenant_id)
    policy = repo_get_escalation_policy(db, tenant_id, policy_id)
    if policy is None:
        raise TenantResourceNotFoundError(f"escalation policy {policy_id} not found")
    if not policy.is_active:
        raise DomainValidationError("escalation policy is already archived")
    policy = repo_archive_escalation_policy(db, policy)
    _write_audit(
        db, tenant_id, AuditEventType.ESCALATION_POLICY_ARCHIVED,
        "escalation_policy", "archived",
        actor_user_id=actor_user_id, request_id=request_id,
        payload={"policy_id": policy_id},
    )
    db.commit()
    db.refresh(policy)
    return policy
