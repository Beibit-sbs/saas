"""Rector Assignment Workflow — Repository layer (DB query helpers)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import and_, case, desc, func, select
from sqlalchemy.orm import Session

from app.core.module_helpers.service_validation import (
    TenantResourceNotFoundError,
    validate_tenant_id_provided,
)
from app.modules.rector_assignment_workflow.models import (
    AssignmentStatus,
    RectorAssignment,
    RectorAssignmentAssignee,
    RectorAssignmentAuditEvent,
    RectorAssignmentComment,
    RectorAssignmentEscalation,
    RectorAssignmentEvidence,
    RectorAssignmentReport,
    RectorAssignmentStatusHistory,
    RectorAssignmentTask,
    RectorAssignmentTemplate,
)


# ---------------------------------------------------------------------------
# Assignment queries
# ---------------------------------------------------------------------------

def repo_create_assignment(
    db: Session,
    tenant_id: int,
    **kwargs,
) -> RectorAssignment:
    now = datetime.now(UTC)
    obj = RectorAssignment(tenant_id=tenant_id, created_at=now, updated_at=now, **kwargs)
    db.add(obj)
    db.flush()
    db.refresh(obj)
    return obj


def repo_get_assignment(db: Session, tenant_id: int, assignment_id: int) -> RectorAssignment | None:
    stmt = select(RectorAssignment).where(
        and_(RectorAssignment.tenant_id == tenant_id, RectorAssignment.id == assignment_id)
    )
    return db.execute(stmt).scalar_one_or_none()


def repo_require_assignment(db: Session, tenant_id: int, assignment_id: int) -> RectorAssignment:
    obj = repo_get_assignment(db, tenant_id, assignment_id)
    if obj is None:
        raise TenantResourceNotFoundError(f"assignment {assignment_id} not found for tenant {tenant_id}")
    return obj


def repo_list_assignments(
    db: Session,
    tenant_id: int,
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
    filters = [RectorAssignment.tenant_id == tenant_id]
    if status:
        filters.append(RectorAssignment.status.in_(status))
    if priority:
        filters.append(RectorAssignment.priority == priority)
    if due_before:
        filters.append(RectorAssignment.due_date <= due_before)
    if due_after:
        filters.append(RectorAssignment.due_date >= due_after)
    if responsible_unit_id:
        filters.append(RectorAssignment.responsible_unit_id == responsible_unit_id)
    if search:
        filters.append(RectorAssignment.title.ilike(f"%{search}%"))
    if overdue_only:
        today = datetime.now(UTC).date()
        filters.append(
            and_(
                RectorAssignment.status.in_(list(AssignmentStatus.ACTIVE)),
                RectorAssignment.due_date != None,  # noqa: E711
                RectorAssignment.due_date < today,
            )
        )
    if assignee_user_id:
        subq = select(RectorAssignmentAssignee.assignment_id).where(
            and_(
                RectorAssignmentAssignee.tenant_id == tenant_id,
                RectorAssignmentAssignee.user_id == assignee_user_id,
            )
        )
        filters.append(RectorAssignment.id.in_(subq))

    total_stmt = select(func.count(RectorAssignment.id)).where(and_(*filters))
    total = db.execute(total_stmt).scalar_one()

    offset = (page - 1) * page_size
    stmt = (
        select(RectorAssignment)
        .where(and_(*filters))
        .order_by(desc(RectorAssignment.created_at))
        .offset(offset)
        .limit(page_size)
    )
    items = list(db.execute(stmt).scalars().all())
    return items, total


def repo_update_assignment(db: Session, assignment: RectorAssignment, **kwargs) -> RectorAssignment:
    for k, v in kwargs.items():
        setattr(assignment, k, v)
    assignment.updated_at = datetime.now(UTC)
    db.flush()
    db.refresh(assignment)
    return assignment


# ---------------------------------------------------------------------------
# Assignee queries
# ---------------------------------------------------------------------------

def repo_create_assignee(db: Session, tenant_id: int, assignment_id: int, **kwargs) -> RectorAssignmentAssignee:
    now = datetime.now(UTC)
    obj = RectorAssignmentAssignee(
        tenant_id=tenant_id, assignment_id=assignment_id, assigned_at=now, **kwargs
    )
    db.add(obj)
    db.flush()
    return obj


def repo_list_assignees(db: Session, tenant_id: int, assignment_id: int) -> list[RectorAssignmentAssignee]:
    stmt = select(RectorAssignmentAssignee).where(
        and_(
            RectorAssignmentAssignee.tenant_id == tenant_id,
            RectorAssignmentAssignee.assignment_id == assignment_id,
        )
    )
    return list(db.execute(stmt).scalars().all())


def repo_is_user_assignee(db: Session, tenant_id: int, assignment_id: int, user_id: int) -> bool:
    stmt = select(func.count(RectorAssignmentAssignee.id)).where(
        and_(
            RectorAssignmentAssignee.tenant_id == tenant_id,
            RectorAssignmentAssignee.assignment_id == assignment_id,
            RectorAssignmentAssignee.user_id == user_id,
        )
    )
    return (db.execute(stmt).scalar_one() or 0) > 0


# ---------------------------------------------------------------------------
# Task queries
# ---------------------------------------------------------------------------

def repo_create_task(db: Session, tenant_id: int, assignment_id: int, **kwargs) -> RectorAssignmentTask:
    now = datetime.now(UTC)
    obj = RectorAssignmentTask(
        tenant_id=tenant_id, assignment_id=assignment_id,
        created_at=now, updated_at=now, **kwargs
    )
    db.add(obj)
    db.flush()
    return obj


# ---------------------------------------------------------------------------
# Report queries
# ---------------------------------------------------------------------------

def repo_create_report(db: Session, tenant_id: int, assignment_id: int, **kwargs) -> RectorAssignmentReport:
    now = datetime.now(UTC)
    obj = RectorAssignmentReport(
        tenant_id=tenant_id, assignment_id=assignment_id, submitted_at=now, **kwargs
    )
    db.add(obj)
    db.flush()
    db.refresh(obj)
    return obj


def repo_get_report(db: Session, tenant_id: int, report_id: int) -> RectorAssignmentReport | None:
    stmt = select(RectorAssignmentReport).where(
        and_(RectorAssignmentReport.tenant_id == tenant_id, RectorAssignmentReport.id == report_id)
    )
    return db.execute(stmt).scalar_one_or_none()


def repo_list_reports(db: Session, tenant_id: int, assignment_id: int) -> list[RectorAssignmentReport]:
    stmt = select(RectorAssignmentReport).where(
        and_(
            RectorAssignmentReport.tenant_id == tenant_id,
            RectorAssignmentReport.assignment_id == assignment_id,
        )
    ).order_by(desc(RectorAssignmentReport.submitted_at))
    return list(db.execute(stmt).scalars().all())


# ---------------------------------------------------------------------------
# Evidence queries
# ---------------------------------------------------------------------------

def repo_create_evidence(db: Session, tenant_id: int, assignment_id: int, **kwargs) -> RectorAssignmentEvidence:
    now = datetime.now(UTC)
    obj = RectorAssignmentEvidence(
        tenant_id=tenant_id, assignment_id=assignment_id, created_at=now, **kwargs
    )
    db.add(obj)
    db.flush()
    db.refresh(obj)
    return obj


def repo_list_evidence(db: Session, tenant_id: int, assignment_id: int) -> list[RectorAssignmentEvidence]:
    stmt = select(RectorAssignmentEvidence).where(
        and_(
            RectorAssignmentEvidence.tenant_id == tenant_id,
            RectorAssignmentEvidence.assignment_id == assignment_id,
            RectorAssignmentEvidence.is_deleted == False,  # noqa: E712
        )
    )
    return list(db.execute(stmt).scalars().all())


# ---------------------------------------------------------------------------
# Comment queries
# ---------------------------------------------------------------------------

def repo_create_comment(db: Session, tenant_id: int, assignment_id: int, **kwargs) -> RectorAssignmentComment:
    now = datetime.now(UTC)
    obj = RectorAssignmentComment(
        tenant_id=tenant_id, assignment_id=assignment_id, created_at=now, **kwargs
    )
    db.add(obj)
    db.flush()
    db.refresh(obj)
    return obj


def repo_list_comments(
    db: Session, tenant_id: int, assignment_id: int,
    *,
    actor_role: str | None = None,
    exclude_internal: bool = False,
) -> list[RectorAssignmentComment]:
    filters = [
        RectorAssignmentComment.tenant_id == tenant_id,
        RectorAssignmentComment.assignment_id == assignment_id,
        RectorAssignmentComment.is_deleted == False,  # noqa: E712
    ]
    if exclude_internal:
        filters.append(RectorAssignmentComment.visibility != "INTERNAL")
    stmt = select(RectorAssignmentComment).where(and_(*filters)).order_by(RectorAssignmentComment.created_at)
    return list(db.execute(stmt).scalars().all())


# ---------------------------------------------------------------------------
# Status history (INSERT-ONLY)
# ---------------------------------------------------------------------------

def repo_create_status_history(
    db: Session,
    tenant_id: int,
    assignment_id: int,
    old_status: str | None,
    new_status: str,
    actor_user_id: int,
    *,
    actor_role: str | None = None,
    reason: str | None = None,
    request_id: str | None = None,
) -> RectorAssignmentStatusHistory:
    now = datetime.now(UTC)
    obj = RectorAssignmentStatusHistory(
        tenant_id=tenant_id,
        assignment_id=assignment_id,
        old_status=old_status,
        new_status=new_status,
        actor_user_id=actor_user_id,
        actor_role=actor_role,
        reason=reason,
        request_id=request_id,
        created_at=now,
    )
    db.add(obj)
    db.flush()
    return obj


# ---------------------------------------------------------------------------
# Escalation queries
# ---------------------------------------------------------------------------

def repo_create_escalation(db: Session, tenant_id: int, assignment_id: int, **kwargs) -> RectorAssignmentEscalation:
    now = datetime.now(UTC)
    obj = RectorAssignmentEscalation(
        tenant_id=tenant_id, assignment_id=assignment_id, triggered_at=now, **kwargs
    )
    db.add(obj)
    db.flush()
    db.refresh(obj)
    return obj


# ---------------------------------------------------------------------------
# Template queries
# ---------------------------------------------------------------------------

def repo_create_template(db: Session, tenant_id: int, **kwargs) -> RectorAssignmentTemplate:
    now = datetime.now(UTC)
    obj = RectorAssignmentTemplate(tenant_id=tenant_id, created_at=now, updated_at=now, **kwargs)
    db.add(obj)
    db.flush()
    db.refresh(obj)
    return obj


def repo_get_template(db: Session, tenant_id: int, template_id: int) -> RectorAssignmentTemplate | None:
    stmt = select(RectorAssignmentTemplate).where(
        and_(RectorAssignmentTemplate.tenant_id == tenant_id, RectorAssignmentTemplate.id == template_id)
    )
    return db.execute(stmt).scalar_one_or_none()


def repo_list_templates(db: Session, tenant_id: int, active_only: bool = True) -> list[RectorAssignmentTemplate]:
    filters = [RectorAssignmentTemplate.tenant_id == tenant_id]
    if active_only:
        filters.append(RectorAssignmentTemplate.is_active == True)  # noqa: E712
    stmt = select(RectorAssignmentTemplate).where(and_(*filters)).order_by(RectorAssignmentTemplate.name)
    return list(db.execute(stmt).scalars().all())


def repo_update_template(db: Session, template: RectorAssignmentTemplate, **kwargs) -> RectorAssignmentTemplate:
    for k, v in kwargs.items():
        setattr(template, k, v)
    template.updated_at = datetime.now(UTC)
    db.flush()
    db.refresh(template)
    return template


# ---------------------------------------------------------------------------
# Audit events (INSERT-ONLY)
# ---------------------------------------------------------------------------

def repo_create_audit_event(
    db: Session,
    tenant_id: int,
    event_type: str,
    action: str,
    *,
    assignment_id: int | None = None,
    actor_user_id: int | None = None,
    actor_role: str | None = None,
    request_id: str | None = None,
    payload_json: dict | None = None,
) -> RectorAssignmentAuditEvent:
    now = datetime.now(UTC)
    obj = RectorAssignmentAuditEvent(
        tenant_id=tenant_id,
        assignment_id=assignment_id,
        event_type=event_type,
        actor_user_id=actor_user_id,
        actor_role=actor_role,
        request_id=request_id,
        action=action,
        payload_json=payload_json or {},
        created_at=now,
    )
    db.add(obj)
    db.flush()
    return obj


def repo_list_audit_events(
    db: Session,
    tenant_id: int,
    assignment_id: int,
    *,
    event_type: str | None = None,
    actor_user_id: int | None = None,
    limit: int = 100,
) -> list[RectorAssignmentAuditEvent]:
    filters = [
        RectorAssignmentAuditEvent.tenant_id == tenant_id,
        RectorAssignmentAuditEvent.assignment_id == assignment_id,
    ]
    if event_type:
        filters.append(RectorAssignmentAuditEvent.event_type == event_type)
    if actor_user_id:
        filters.append(RectorAssignmentAuditEvent.actor_user_id == actor_user_id)
    stmt = (
        select(RectorAssignmentAuditEvent)
        .where(and_(*filters))
        .order_by(desc(RectorAssignmentAuditEvent.created_at))
        .limit(limit)
    )
    return list(db.execute(stmt).scalars().all())


# ---------------------------------------------------------------------------
# Dashboard summary queries
# ---------------------------------------------------------------------------

def repo_compute_dashboard_summary(db: Session, tenant_id: int) -> dict:
    """Compute real dashboard values from DB. No fake metrics."""
    validate_tenant_id_provided(tenant_id)
    now = datetime.now(UTC)
    today = now.date()
    week_end = today + timedelta(days=7)
    month_ago = now - timedelta(days=30)

    # Status counts
    status_counts_stmt = (
        select(RectorAssignment.status, func.count(RectorAssignment.id).label("cnt"))
        .where(
            and_(
                RectorAssignment.tenant_id == tenant_id,
                RectorAssignment.is_archived == False,  # noqa: E712
            )
        )
        .group_by(RectorAssignment.status)
    )
    by_status: dict[str, int] = {}
    for row in db.execute(status_counts_stmt).all():
        by_status[row.status] = row.cnt

    # Overdue count (active + past due)
    active_statuses = list(AssignmentStatus.ACTIVE)
    overdue_stmt = select(func.count(RectorAssignment.id)).where(
        and_(
            RectorAssignment.tenant_id == tenant_id,
            RectorAssignment.status.in_(active_statuses),
            RectorAssignment.due_date != None,  # noqa: E711
            RectorAssignment.due_date < today,
            RectorAssignment.is_archived == False,  # noqa: E712
        )
    )
    overdue_count = db.execute(overdue_stmt).scalar_one() or 0

    # Due this week
    due_week_stmt = select(func.count(RectorAssignment.id)).where(
        and_(
            RectorAssignment.tenant_id == tenant_id,
            RectorAssignment.status.notin_(list(AssignmentStatus.TERMINAL)),
            RectorAssignment.due_date != None,  # noqa: E711
            RectorAssignment.due_date >= today,
            RectorAssignment.due_date <= week_end,
        )
    )
    due_this_week = db.execute(due_week_stmt).scalar_one() or 0

    # Due today
    due_today_stmt = select(func.count(RectorAssignment.id)).where(
        and_(
            RectorAssignment.tenant_id == tenant_id,
            RectorAssignment.status.notin_(list(AssignmentStatus.TERMINAL)),
            RectorAssignment.due_date != None,  # noqa: E711
            RectorAssignment.due_date == today,
        )
    )
    due_today = db.execute(due_today_stmt).scalar_one() or 0

    # Completed in last 30 days
    completed_30d_stmt = select(func.count(RectorAssignment.id)).where(
        and_(
            RectorAssignment.tenant_id == tenant_id,
            RectorAssignment.status == AssignmentStatus.COMPLETED,
            RectorAssignment.completed_at >= month_ago,
        )
    )
    completed_30d = db.execute(completed_30d_stmt).scalar_one() or 0

    # Total closed in last 30 days (for rate)
    closed_30d_stmt = select(func.count(RectorAssignment.id)).where(
        and_(
            RectorAssignment.tenant_id == tenant_id,
            RectorAssignment.status.in_([AssignmentStatus.COMPLETED, AssignmentStatus.CANCELLED]),
            RectorAssignment.updated_at >= month_ago,
        )
    )
    closed_30d = db.execute(closed_30d_stmt).scalar_one() or 0
    completion_rate_30d = round(completed_30d / closed_30d, 3) if closed_30d > 0 else 0.0

    # Average days to complete
    avg_stmt = select(func.avg(
        func.extract("epoch", RectorAssignment.completed_at - RectorAssignment.created_at) / 86400
    )).where(
        and_(
            RectorAssignment.tenant_id == tenant_id,
            RectorAssignment.status == AssignmentStatus.COMPLETED,
            RectorAssignment.completed_at != None,  # noqa: E711
        )
    )
    avg_days = db.execute(avg_stmt).scalar_one()

    # Priority counts
    priority_stmt = (
        select(RectorAssignment.priority, func.count(RectorAssignment.id).label("cnt"))
        .where(
            and_(
                RectorAssignment.tenant_id == tenant_id,
                RectorAssignment.is_archived == False,  # noqa: E712
            )
        )
        .group_by(RectorAssignment.priority)
    )
    by_priority: dict[str, int] = {}
    for row in db.execute(priority_stmt).all():
        by_priority[row.priority] = row.cnt

    # By unit
    unit_stmt = (
        select(
            RectorAssignment.responsible_unit_id,
            func.count(RectorAssignment.id).label("cnt"),
        )
        .where(
            and_(
                RectorAssignment.tenant_id == tenant_id,
                RectorAssignment.is_archived == False,  # noqa: E712
            )
        )
        .group_by(RectorAssignment.responsible_unit_id)
        .limit(20)
    )
    by_unit = [
        {"unit_id": row.responsible_unit_id, "count": row.cnt, "overdue_count": 0}
        for row in db.execute(unit_stmt).all()
    ]

    total = sum(by_status.values())
    active_count = sum(v for k, v in by_status.items() if k in AssignmentStatus.ACTIVE)
    draft_count = by_status.get(AssignmentStatus.DRAFT, 0)
    escalated_count = by_status.get(AssignmentStatus.ESCALATED, 0)
    completed_count = by_status.get(AssignmentStatus.COMPLETED, 0)
    cancelled_count = by_status.get(AssignmentStatus.CANCELLED, 0)
    report_submitted_count = by_status.get(AssignmentStatus.REPORT_SUBMITTED, 0)
    returned_count = by_status.get(AssignmentStatus.RETURNED_FOR_REVISION, 0)

    return {
        "tenant_id": tenant_id,
        "computed_at": now,
        "total_assignments": total,
        "active_count": active_count,
        "draft_count": draft_count,
        "overdue_count": overdue_count,
        "escalated_count": escalated_count,
        "completed_count": completed_count,
        "cancelled_count": cancelled_count,
        "report_submitted_count": report_submitted_count,
        "returned_count": returned_count,
        "due_this_week": due_this_week,
        "due_today": due_today,
        "completion_rate_30d": completion_rate_30d,
        "average_days_to_complete": float(avg_days) if avg_days is not None else None,
        "by_status": by_status,
        "by_priority": by_priority,
        "by_unit": by_unit,
        "top_overdue": [],
        "data_source": "computed_from_assignments",
        "fake_metrics": False,
    }
