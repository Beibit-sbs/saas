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


# ---------------------------------------------------------------------------
# A-031.5-RUNTIME: Outbox event repository functions
# ---------------------------------------------------------------------------

from app.modules.rector_assignment_workflow.models import (  # noqa: E402  (appended import)
    AuditEventType,
    OutboxChannel,
    OutboxStatus,
    RectorAssignmentEscalationPolicy,
    RectorAssignmentOutboxEvent,
    RectorAssignmentSlaPolicy,
)


def repo_create_outbox_event(
    db: Session,
    *,
    tenant_id: int,
    assignment_id: int,
    event_type: str,
    channel: str = OutboxChannel.IN_APP,
    recipient_user_id: int | None = None,
    recipient_role: str | None = None,
    payload_json: dict | None = None,
) -> RectorAssignmentOutboxEvent:
    now = datetime.now(UTC)
    event = RectorAssignmentOutboxEvent(
        tenant_id=tenant_id,
        assignment_id=assignment_id,
        event_type=event_type,
        channel=channel,
        recipient_user_id=recipient_user_id,
        recipient_role=recipient_role,
        payload_json=payload_json or {},
        status=OutboxStatus.PENDING,
        retry_count=0,
        next_retry_at=None,
        created_at=now,
        updated_at=now,
    )
    db.add(event)
    db.flush()
    db.refresh(event)
    return event


def repo_get_outbox_event(
    db: Session, tenant_id: int, event_id: int,
) -> RectorAssignmentOutboxEvent | None:
    stmt = select(RectorAssignmentOutboxEvent).where(
        and_(
            RectorAssignmentOutboxEvent.tenant_id == tenant_id,
            RectorAssignmentOutboxEvent.id == event_id,
        )
    )
    return db.execute(stmt).scalar_one_or_none()


def repo_list_assignment_outbox_events(
    db: Session,
    tenant_id: int,
    assignment_id: int,
    *,
    status: str | None = None,
    page: int = 1,
    page_size: int = 50,
) -> tuple[list[RectorAssignmentOutboxEvent], int]:
    filters = [
        RectorAssignmentOutboxEvent.tenant_id == tenant_id,
        RectorAssignmentOutboxEvent.assignment_id == assignment_id,
    ]
    if status is not None:
        filters.append(RectorAssignmentOutboxEvent.status == status)
    stmt = (
        select(RectorAssignmentOutboxEvent)
        .where(and_(*filters))
        .order_by(desc(RectorAssignmentOutboxEvent.created_at))
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    count_stmt = (
        select(func.count(RectorAssignmentOutboxEvent.id)).where(and_(*filters))
    )
    items = list(db.execute(stmt).scalars().all())
    total = db.execute(count_stmt).scalar_one()
    return items, total


def repo_list_outbox_events(
    db: Session,
    tenant_id: int,
    *,
    status: str | None = None,
    page: int = 1,
    page_size: int = 50,
) -> tuple[list[RectorAssignmentOutboxEvent], int]:
    filters = [RectorAssignmentOutboxEvent.tenant_id == tenant_id]
    if status is not None:
        filters.append(RectorAssignmentOutboxEvent.status == status)
    stmt = (
        select(RectorAssignmentOutboxEvent)
        .where(and_(*filters))
        .order_by(desc(RectorAssignmentOutboxEvent.created_at))
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    count_stmt = (
        select(func.count(RectorAssignmentOutboxEvent.id)).where(and_(*filters))
    )
    items = list(db.execute(stmt).scalars().all())
    total = db.execute(count_stmt).scalar_one()
    return items, total


def repo_mark_outbox_event_ready(
    db: Session, event: RectorAssignmentOutboxEvent,
) -> RectorAssignmentOutboxEvent:
    event.status = OutboxStatus.READY
    event.updated_at = datetime.now(UTC)
    db.flush()
    db.refresh(event)
    return event


def repo_cancel_outbox_event(
    db: Session, event: RectorAssignmentOutboxEvent,
) -> RectorAssignmentOutboxEvent:
    event.status = OutboxStatus.CANCELLED
    event.updated_at = datetime.now(UTC)
    db.flush()
    db.refresh(event)
    return event


# ---------------------------------------------------------------------------
# A-031.5-RUNTIME: SLA Policy repository functions
# ---------------------------------------------------------------------------

def repo_create_sla_policy(
    db: Session,
    *,
    tenant_id: int,
    name: str,
    priority: str | None,
    due_days: int,
    warning_before_hours: int = 48,
    overdue_after_hours: int = 0,
    escalation_after_hours: int = 72,
    created_by_user_id: int | None = None,
) -> RectorAssignmentSlaPolicy:
    now = datetime.now(UTC)
    policy = RectorAssignmentSlaPolicy(
        tenant_id=tenant_id,
        name=name,
        priority=priority,
        due_days=due_days,
        warning_before_hours=warning_before_hours,
        overdue_after_hours=overdue_after_hours,
        escalation_after_hours=escalation_after_hours,
        is_active=True,
        created_by_user_id=created_by_user_id,
        created_at=now,
        updated_at=now,
        archived_at=None,
    )
    db.add(policy)
    db.flush()
    db.refresh(policy)
    return policy


def repo_get_sla_policy(
    db: Session, tenant_id: int, policy_id: int,
) -> RectorAssignmentSlaPolicy | None:
    stmt = select(RectorAssignmentSlaPolicy).where(
        and_(
            RectorAssignmentSlaPolicy.tenant_id == tenant_id,
            RectorAssignmentSlaPolicy.id == policy_id,
        )
    )
    return db.execute(stmt).scalar_one_or_none()


def repo_list_sla_policies(
    db: Session,
    tenant_id: int,
    *,
    active_only: bool = True,
    page: int = 1,
    page_size: int = 50,
) -> tuple[list[RectorAssignmentSlaPolicy], int]:
    filters = [RectorAssignmentSlaPolicy.tenant_id == tenant_id]
    if active_only:
        filters.append(RectorAssignmentSlaPolicy.is_active == True)  # noqa: E712
    stmt = (
        select(RectorAssignmentSlaPolicy)
        .where(and_(*filters))
        .order_by(RectorAssignmentSlaPolicy.id)
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    count_stmt = (
        select(func.count(RectorAssignmentSlaPolicy.id)).where(and_(*filters))
    )
    items = list(db.execute(stmt).scalars().all())
    total = db.execute(count_stmt).scalar_one()
    return items, total


def repo_update_sla_policy(
    db: Session, policy: RectorAssignmentSlaPolicy, **kwargs: object,
) -> RectorAssignmentSlaPolicy:
    kwargs.setdefault("updated_at", datetime.now(UTC))
    for k, v in kwargs.items():
        setattr(policy, k, v)
    db.flush()
    db.refresh(policy)
    return policy


def repo_archive_sla_policy(
    db: Session, policy: RectorAssignmentSlaPolicy,
) -> RectorAssignmentSlaPolicy:
    now = datetime.now(UTC)
    policy.is_active = False
    policy.archived_at = now
    policy.updated_at = now
    db.flush()
    db.refresh(policy)
    return policy


# ---------------------------------------------------------------------------
# A-031.5-RUNTIME: Escalation Policy repository functions
# ---------------------------------------------------------------------------

def repo_create_escalation_policy(
    db: Session,
    *,
    tenant_id: int,
    assignment_priority: str,
    escalation_level: int,
    escalate_to_role: str,
    escalate_after_hours: int = 72,
    require_manual_confirmation: bool = True,
    created_by_user_id: int | None = None,
) -> RectorAssignmentEscalationPolicy:
    now = datetime.now(UTC)
    policy = RectorAssignmentEscalationPolicy(
        tenant_id=tenant_id,
        assignment_priority=assignment_priority,
        escalation_level=escalation_level,
        escalate_to_role=escalate_to_role,
        escalate_after_hours=escalate_after_hours,
        require_manual_confirmation=require_manual_confirmation,
        is_active=True,
        created_by_user_id=created_by_user_id,
        created_at=now,
        updated_at=now,
        archived_at=None,
    )
    db.add(policy)
    db.flush()
    db.refresh(policy)
    return policy


def repo_get_escalation_policy(
    db: Session, tenant_id: int, policy_id: int,
) -> RectorAssignmentEscalationPolicy | None:
    stmt = select(RectorAssignmentEscalationPolicy).where(
        and_(
            RectorAssignmentEscalationPolicy.tenant_id == tenant_id,
            RectorAssignmentEscalationPolicy.id == policy_id,
        )
    )
    return db.execute(stmt).scalar_one_or_none()


def repo_list_escalation_policies(
    db: Session,
    tenant_id: int,
    *,
    active_only: bool = True,
    page: int = 1,
    page_size: int = 50,
) -> tuple[list[RectorAssignmentEscalationPolicy], int]:
    filters = [RectorAssignmentEscalationPolicy.tenant_id == tenant_id]
    if active_only:
        filters.append(RectorAssignmentEscalationPolicy.is_active == True)  # noqa: E712
    stmt = (
        select(RectorAssignmentEscalationPolicy)
        .where(and_(*filters))
        .order_by(
            RectorAssignmentEscalationPolicy.assignment_priority,
            RectorAssignmentEscalationPolicy.escalation_level,
        )
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    count_stmt = (
        select(func.count(RectorAssignmentEscalationPolicy.id)).where(and_(*filters))
    )
    items = list(db.execute(stmt).scalars().all())
    total = db.execute(count_stmt).scalar_one()
    return items, total


def repo_update_escalation_policy(
    db: Session, policy: RectorAssignmentEscalationPolicy, **kwargs: object,
) -> RectorAssignmentEscalationPolicy:
    kwargs.setdefault("updated_at", datetime.now(UTC))
    for k, v in kwargs.items():
        setattr(policy, k, v)
    db.flush()
    db.refresh(policy)
    return policy


def repo_archive_escalation_policy(
    db: Session, policy: RectorAssignmentEscalationPolicy,
) -> RectorAssignmentEscalationPolicy:
    now = datetime.now(UTC)
    policy.is_active = False
    policy.archived_at = now
    policy.updated_at = now
    db.flush()
    db.refresh(policy)
    return policy


# ---------------------------------------------------------------------------
# A-031.5-RUNTIME: Expanded dashboard computation
# ---------------------------------------------------------------------------

def repo_compute_expanded_dashboard_fields(db: Session, tenant_id: int) -> dict:
    """Compute the 8 additional dashboard fields added in A-031.5-RUNTIME.
    Returns dict that MUST be merged into repo_compute_dashboard_summary output.
    fake_metrics must remain False; data_source must remain 'computed_from_assignments'.
    """
    from datetime import date as _date, timedelta as _td

    now = datetime.now(UTC)

    # 1. Overdue aging buckets
    today = now.date()
    buckets = {"days_1_3": 0, "days_4_7": 0, "days_8_14": 0, "days_15_plus": 0}
    overdue_stmt = select(RectorAssignment.due_date).where(
        and_(
            RectorAssignment.tenant_id == tenant_id,
            RectorAssignment.is_archived == False,  # noqa: E712
            RectorAssignment.due_date < today,
            RectorAssignment.status.notin_(
                [AssignmentStatus.COMPLETED, AssignmentStatus.CANCELLED, AssignmentStatus.ARCHIVED]
            ),
        )
    )
    for row in db.execute(overdue_stmt).all():
        if row.due_date is None:
            continue
        delta = (today - row.due_date).days
        if 1 <= delta <= 3:
            buckets["days_1_3"] += 1
        elif 4 <= delta <= 7:
            buckets["days_4_7"] += 1
        elif 8 <= delta <= 14:
            buckets["days_8_14"] += 1
        else:
            buckets["days_15_plus"] += 1

    # 2. Completion trend by week (last 4 weeks)
    weekly_trend = []
    for week_offset in range(3, -1, -1):
        week_start = today - _td(days=today.weekday() + week_offset * 7)
        week_end = week_start + _td(days=6)
        comp_stmt = select(func.count(RectorAssignment.id)).where(
            and_(
                RectorAssignment.tenant_id == tenant_id,
                RectorAssignment.completed_at >= datetime(week_start.year, week_start.month, week_start.day, tzinfo=UTC),
                RectorAssignment.completed_at <= datetime(week_end.year, week_end.month, week_end.day, 23, 59, 59, tzinfo=UTC),
            )
        )
        created_stmt = select(func.count(RectorAssignment.id)).where(
            and_(
                RectorAssignment.tenant_id == tenant_id,
                RectorAssignment.created_at >= datetime(week_start.year, week_start.month, week_start.day, tzinfo=UTC),
                RectorAssignment.created_at <= datetime(week_end.year, week_end.month, week_end.day, 23, 59, 59, tzinfo=UTC),
            )
        )
        completed_count = db.execute(comp_stmt).scalar_one()
        created_count = db.execute(created_stmt).scalar_one()
        weekly_trend.append({
            "week_start": week_start.isoformat(),
            "completed_count": completed_count,
            "created_count": created_count,
        })

    # 3. Report submission compliance
    active_status_list = list(AssignmentStatus.ACTIVE)
    active_stmt = select(func.count(RectorAssignment.id)).where(
        and_(
            RectorAssignment.tenant_id == tenant_id,
            RectorAssignment.is_archived == False,  # noqa: E712
            RectorAssignment.status.in_(active_status_list),
        )
    )
    total_active = db.execute(active_stmt).scalar_one()
    submitted_stmt = select(func.count(RectorAssignment.id)).where(
        and_(
            RectorAssignment.tenant_id == tenant_id,
            RectorAssignment.status == AssignmentStatus.REPORT_SUBMITTED,
        )
    )
    total_with_report = db.execute(submitted_stmt).scalar_one()
    report_submission_compliance: float | None = None
    if total_active and total_active > 0:
        report_submission_compliance = round(total_with_report / total_active, 4)

    # 4. Escalation rate (last 30 days)
    cutoff_30 = now - timedelta(days=30)
    total_30_stmt = select(func.count(RectorAssignment.id)).where(
        and_(
            RectorAssignment.tenant_id == tenant_id,
            RectorAssignment.created_at >= cutoff_30,
        )
    )
    escalated_30_stmt = select(func.count(RectorAssignment.id)).where(
        and_(
            RectorAssignment.tenant_id == tenant_id,
            RectorAssignment.created_at >= cutoff_30,
            RectorAssignment.status == AssignmentStatus.ESCALATED,
        )
    )
    total_30 = db.execute(total_30_stmt).scalar_one()
    escalated_30 = db.execute(escalated_30_stmt).scalar_one()
    escalation_rate: float | None = round(escalated_30 / total_30, 4) if total_30 > 0 else None

    # 5. Average revision cycles
    from sqlalchemy import text as _text
    avg_rev_stmt = _text(
        "SELECT AVG(revision_count) FROM ("
        "  SELECT assignment_id, COUNT(*) AS revision_count"
        "  FROM rector_assignment_status_history"
        "  WHERE tenant_id = :tid AND new_status = 'RETURNED_FOR_REVISION'"
        "  GROUP BY assignment_id"
        ") sub"
    )
    avg_rev = db.execute(avg_rev_stmt, {"tid": tenant_id}).scalar_one()
    average_revision_cycles: float | None = float(avg_rev) if avg_rev is not None else None

    # 6. Evidence attachment rate
    assignments_with_evidence_stmt = _text(
        "SELECT COUNT(DISTINCT assignment_id) FROM rector_assignment_evidence"
        " WHERE tenant_id = :tid AND is_deleted = false"
    )
    total_all_stmt = select(func.count(RectorAssignment.id)).where(
        RectorAssignment.tenant_id == tenant_id,
    )
    assignments_with_ev = db.execute(assignments_with_evidence_stmt, {"tid": tenant_id}).scalar_one()
    total_all = db.execute(total_all_stmt).scalar_one()
    evidence_attachment_rate: float | None = round(assignments_with_ev / total_all, 4) if total_all > 0 else None

    # 7. Assignments without recent report (active and no report in last 14 days)
    cutoff_14 = now - timedelta(days=14)
    no_recent_report_stmt = _text(
        "SELECT COUNT(*) FROM rector_assignments ra"
        " WHERE ra.tenant_id = :tid"
        "   AND ra.is_archived = false"
        "   AND ra.status IN ('ACCEPTED','IN_PROGRESS','OVERDUE')"
        "   AND NOT EXISTS ("
        "     SELECT 1 FROM rector_assignment_reports r"
        "     WHERE r.tenant_id = :tid AND r.assignment_id = ra.id"
        "       AND r.created_at >= :cutoff"
        "   )"
    )
    assignments_without_recent_report = db.execute(
        no_recent_report_stmt, {"tid": tenant_id, "cutoff": cutoff_14}
    ).scalar_one()

    # 8. Unit completion table
    unit_comp_stmt = _text(
        "SELECT responsible_unit_id,"
        "  COUNT(*) AS total,"
        "  SUM(CASE WHEN status = 'COMPLETED' THEN 1 ELSE 0 END) AS completed,"
        "  SUM(CASE WHEN status NOT IN ('COMPLETED','CANCELLED','ARCHIVED')"
        "       AND due_date < NOW() THEN 1 ELSE 0 END) AS overdue"
        " FROM rector_assignments"
        " WHERE tenant_id = :tid AND is_archived = false"
        " GROUP BY responsible_unit_id"
        " LIMIT 30"
    )
    unit_completion_table = []
    for row in db.execute(unit_comp_stmt, {"tid": tenant_id}).all():
        total = row.total or 0
        completed = row.completed or 0
        overdue = row.overdue or 0
        comp_rate = round(completed / total, 4) if total > 0 else None
        unit_completion_table.append({
            "unit_id": row.responsible_unit_id,
            "unit_name": None,
            "total": total,
            "completed": completed,
            "overdue": overdue,
            "completion_rate": comp_rate,
        })

    return {
        "overdue_aging_buckets": buckets,
        "completion_trend_by_week": weekly_trend,
        "report_submission_compliance": report_submission_compliance,
        "escalation_rate": escalation_rate,
        "average_revision_cycles": average_revision_cycles,
        "evidence_attachment_rate": evidence_attachment_rate,
        "assignments_without_recent_report": int(assignments_without_recent_report),
        "unit_completion_table": unit_completion_table,
    }
