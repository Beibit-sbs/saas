from __future__ import annotations

from app.core.module_helpers.audit_helpers import build_audit_action
from app.modules.audit.service import log_admin_action
from app.modules.student_services.schemas import (
    StudentServiceTicketCreateSchema,
    StudentServiceTicketSchema,
    StudentTicketStatus,
    StudentServiceTicketStatusUpdateSchema,
)
from app.modules.university_core.tenant_entity_service import (
    create_entity_for_tenant,
    list_entities_for_tenant,
    update_entity_for_tenant,
)

# ---------------------------------------------------------------------------
# SLA tier caps: max allowed target_resolution_hours per priority
# ---------------------------------------------------------------------------
_TICKET_PRIORITY_MAX_RESOLUTION_HOURS: dict[str, int] = {
    "urgent": 4,
    "high": 24,
    "medium": 72,
    "low": 168,
}

# ---------------------------------------------------------------------------
# Queue capacity caps: max allowed unresolved tickets per priority level
# ---------------------------------------------------------------------------
_TICKET_QUEUE_MAX_ACTIVE: dict[str, int] = {
    "urgent": 20,
    "high": 50,
    "medium": 100,
    "low": 150,
}

# ---------------------------------------------------------------------------
# Ticket statuses that indicate active/unresolved state
# ---------------------------------------------------------------------------
_UNRESOLVED_TICKET_STATUSES: frozenset[str] = frozenset({"open", "in_progress"})

# ---------------------------------------------------------------------------
# W128: Enrollment statuses that permit service ticket creation
# ---------------------------------------------------------------------------
_STUDENT_TICKET_ENROLLMENT_ACTIVE_STATUSES: frozenset[str] = frozenset({"enrolled", "active"})

# ---------------------------------------------------------------------------
# Ticket statuses that trigger unresolved risk alerts
# ---------------------------------------------------------------------------
_UNRESOLVED_RISK_STATUSES: frozenset[str] = frozenset({"open", "in_progress"})

_ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    "open": {"in_progress", "resolved", "closed"},
    "in_progress": {"resolved", "closed"},
    "resolved": {"closed", "in_progress"},
    "closed": set(),
}

# ---------------------------------------------------------------------------
# W99: ticket resolution quality guard
# A ticket cannot be marked "resolved" without meaningful resolution notes
# and must have a real owner (not the unassigned sentinel).
# Prevents fake SLA compliance: tickets closed with no evidence of work done.
# ---------------------------------------------------------------------------
_TICKET_RESOLVED_TARGET_STATUS: str = "resolved"
_RESOLUTION_NOTES_PLACEHOLDER_VALUES: frozenset[str] = frozenset(
    {"pending", "n/a", "", "none", "tbd", "no notes"}
)
_UNASSIGNED_OWNER_SENTINEL: str = "unassigned"


def _check_student_is_enrolled_for_service_ticket(
    *,
    tenant_id: int,
    student_id: int,
) -> None:
    """W128: Cross-entity guard — student_service_tickets × enrollments.

    A service ticket cannot be created for a student without an active enrollment.
    Creating tickets for unenrolled, withdrawn, or graduated students:
    - creates ghost service records with no real student relationship
    - corrupts SLA analytics and department reporting
    - may violate FERPA by building service history for non-enrolled persons

    Fail-closed: any enrollment lookup failure blocks ticket creation.
    """
    from app.core.module_helpers.service_validation import DomainValidationError

    try:
        rows = list_entities_for_tenant("enrollments", tenant_id)
    except Exception as exc:  # noqa: BLE001
        raise DomainValidationError(
            f"Cannot create service ticket: enrollment lookup failed for student_id={student_id}. "
            f"Student eligibility cannot be verified. Reason: {exc}"
        ) from exc

    matching_enrolled = next(
        (
            r for r in rows
            if int(r.get("student_id") or 0) == student_id
            and str(r.get("status") or "").strip().lower() in _STUDENT_TICKET_ENROLLMENT_ACTIVE_STATUSES
        ),
        None,
    )

    student_exists = any(
        int(r.get("student_id") or 0) == student_id for r in rows
    )

    if not student_exists:
        raise DomainValidationError(
            f"Cannot create service ticket: student_id={student_id} not found in enrollment records. "
            f"Only students with enrollment records are eligible for student services."
        )

    if matching_enrolled is None:
        raise DomainValidationError(
            f"Cannot create service ticket: student_id={student_id} has no active enrollment "
            f"— withdrawn or graduated students cannot open service tickets."
        )


def _check_ticket_resolution_requirements(
    *,
    ticket_id: int,
    owner_id: str,
    resolution_notes: str | None,
    target_status: str,
) -> None:
    """W99: Cross-entity transition guard — student_service_tickets resolution quality.

    A ticket cannot be moved to 'resolved' unless:
      1. The ticket has a real owner (owner_id != 'unassigned').
         An unowned ticket being marked resolved is a ghost resolution:
         no staff member actually did the work.
      2. Non-empty, non-placeholder resolution_notes are provided.
         Allows brain context and audit trail to confirm actual resolution.

    HARDENING: fail-closed — any missing or invalid state blocks the transition.
    No silent fallback. A query error on owner or notes is treated as a block.
    """
    from app.core.module_helpers.service_validation import DomainValidationError

    if target_status != _TICKET_RESOLVED_TARGET_STATUS:
        return

    normalised_owner = str(owner_id or "").strip().lower()
    if normalised_owner == _UNASSIGNED_OWNER_SENTINEL or not normalised_owner:
        raise DomainValidationError(
            f"Cannot resolve ticket_id={ticket_id}: owner_id is 'unassigned'. "
            f"Assign a responsible staff member before marking the ticket resolved. "
            f"Resolving an unowned ticket creates a ghost resolution with no accountability."
        )

    normalised_notes = str(resolution_notes or "").strip().lower()
    if normalised_notes in _RESOLUTION_NOTES_PLACEHOLDER_VALUES:
        raise DomainValidationError(
            f"Cannot resolve ticket_id={ticket_id}: resolution_notes is missing or "
            f"placeholder (got {resolution_notes!r}). "
            f"Provide meaningful resolution documentation before closing. "
            f"Tickets closed without resolution evidence create false SLA compliance."
        )


def _emit_audit(*, actor: str, action: str, path: str, metadata: dict, tenant_id: int) -> None:
    log_admin_action(
        actor=actor,
        action=action,
        path=path,
        client_ip="service",
        entity="student_service_ticket",
        metadata=metadata,
        tenant_id=tenant_id,
    )


def _ensure_sla_alert(tenant_id: int, ticket_id: int, ticket_data: dict) -> None:
    """Idempotent cross-module side effect: create student_service_sla_alerts record.

    Uses integration_source + source_entity_id to prevent duplicates.
    """
    existing = [
        r for r in list_entities_for_tenant("student_service_sla_alerts", tenant_id)
        if str(r.get("integration_source")) == "student_service_sla"
        and str(r.get("source_entity_id")) == str(ticket_id)
    ]
    if existing:
        return

    create_entity_for_tenant(
        "student_service_sla_alerts",
        {
            "ticket_id": ticket_id,
            "student_id": ticket_data.get("student_id"),
            "priority": ticket_data.get("priority"),
            "category": ticket_data.get("category"),
            "alert_level": "critical",
            "status": "active",
            "integration_source": "student_service_sla",
            "source_entity_id": str(ticket_id),
            "tenant_id": tenant_id,
        },
        tenant_id,
    )


def _ensure_unresolved_alert_record(tenant_id: int, ticket_id: int, ticket_data: dict) -> None:
    """Idempotent cross-module side effect: create student_service_unresolved_alerts record.

    Uses integration_source + source_entity_id to prevent duplicates.
    Publishes 'campus.student_services.ticket_unresolved_risk_detected' event.
    """
    existing = [
        r for r in list_entities_for_tenant("student_service_unresolved_alerts", tenant_id)
        if str(r.get("integration_source")) == "student_service_unresolved_queue"
        and str(r.get("source_entity_id")) == str(ticket_id)
    ]
    if existing:
        return

    create_entity_for_tenant(
        "student_service_unresolved_alerts",
        {
            "ticket_id": ticket_id,
            "student_id": ticket_data.get("student_id"),
            "priority": ticket_data.get("priority"),
            "category": ticket_data.get("category"),
            "status": ticket_data.get("status"),
            "alert_level": "warning",
            "risk_status": "active",
            "integration_source": "student_service_unresolved_queue",
            "source_entity_id": str(ticket_id),
            "tenant_id": tenant_id,
        },
        tenant_id,
    )

    from app.platform.events.publisher import EventPublisher
    EventPublisher().publish_event(
        tenant_id=tenant_id,
        event_type="campus.student_services.ticket_unresolved_risk_detected",
        aggregate_type="student_service_ticket",
        aggregate_id=ticket_id,
        payload_json={
            "ticket_id": ticket_id,
            "student_id": ticket_data.get("student_id"),
            "priority": ticket_data.get("priority"),
            "category": ticket_data.get("category"),
        },
    )


def list_student_service_tickets(
    tenant_id: int,
    status: StudentTicketStatus | None = None,
    student_id: int | None = None,
) -> list[StudentServiceTicketSchema]:
    rows = list_entities_for_tenant("student_service_tickets", tenant_id)
    if status is not None:
        rows = [r for r in rows if str(r.get("status") or "") == status]
    if student_id is not None:
        rows = [r for r in rows if int(r.get("student_id") or 0) == student_id]
    return [StudentServiceTicketSchema.model_validate(r) for r in rows]


def create_student_service_ticket(
    tenant_id: int,
    request: StudentServiceTicketCreateSchema,
    actor: str,
) -> StudentServiceTicketSchema:
    # W128: cross-entity guard — student must have active enrollment FIRST
    _check_student_is_enrolled_for_service_ticket(
        tenant_id=tenant_id, student_id=int(request.student_id)
    )
    # Enforce queue capacity cap before creation
    all_tickets = list_entities_for_tenant("student_service_tickets", tenant_id)
    active_count_for_priority = sum(
        1 for t in all_tickets
        if str(t.get("priority") or "") == request.priority
        and str(t.get("status") or "") in _UNRESOLVED_TICKET_STATUSES
    )
    cap_for_priority = _TICKET_QUEUE_MAX_ACTIVE.get(request.priority)
    if cap_for_priority is not None and active_count_for_priority >= cap_for_priority:
        raise ValueError(f"ticket queue cap reached for priority '{request.priority}'")

    max_hours = _TICKET_PRIORITY_MAX_RESOLUTION_HOURS.get(request.priority)
    if request.target_resolution_hours is not None and max_hours is not None:
        if request.target_resolution_hours > max_hours:
            raise ValueError(
                f"priority='{request.priority}' exceeds maximum target_resolution_hours={max_hours}; "
                f"got {request.target_resolution_hours}"
            )

    created = create_entity_for_tenant(
        "student_service_tickets",
        {
            "student_id": int(request.student_id),
            "category": request.category.strip(),
            "subject": request.subject.strip(),
            "description": request.description.strip(),
            "priority": request.priority,
            "status": "open",
            "owner_id": (request.owner_id or "unassigned").strip() or "unassigned",
            "channel": request.channel.strip() or "portal",
            "resolution_notes": "pending",
        },
        tenant_id,
    )

    _emit_audit(
        actor=actor,
        action=build_audit_action("student_services", "ticket", "create"),
        path="/internal/student-services/tickets",
        metadata={
            "resource_id": str(created.get("id")),
            "student_id": str(request.student_id),
            "category": request.category,
            "priority": request.priority,
        },
        tenant_id=tenant_id,
    )

    if request.priority in ("urgent", "high"):
        ticket_id = int(created.get("id") or 0)
        if request.priority == "urgent":
            _ensure_sla_alert(tenant_id, ticket_id, dict(created))
        from app.platform.events.publisher import EventPublisher
        EventPublisher().publish_event(
            tenant_id=tenant_id,
            event_type="student_services.ticket.escalated",
            aggregate_type="student_service_ticket",
            aggregate_id=ticket_id,
            payload_json={
                "ticket_id": ticket_id,
                "student_id": int(request.student_id),
                "category": request.category,
                "priority": request.priority,
                "source_module": "student_services",
            },
        )

    return StudentServiceTicketSchema.model_validate(created)


def update_student_service_ticket_status(
    tenant_id: int,
    ticket_id: int,
    request: StudentServiceTicketStatusUpdateSchema,
    actor: str,
) -> StudentServiceTicketSchema:
    rows = list_entities_for_tenant("student_service_tickets", tenant_id)
    existing = next((r for r in rows if int(r.get("id") or 0) == ticket_id), None)
    if existing is None:
        raise ValueError(f"ticket {ticket_id} not found")

    current_status = str(existing.get("status") or "open")
    if request.status not in _ALLOWED_TRANSITIONS.get(current_status, set()):
        raise ValueError(f"transition from '{current_status}' to '{request.status}' is not allowed")

    # W99: resolution quality guard — must be wired BEFORE persist
    _check_ticket_resolution_requirements(
        ticket_id=ticket_id,
        owner_id=str(existing.get("owner_id") or ""),
        resolution_notes=request.resolution_notes,
        target_status=request.status,
    )

    updated = update_entity_for_tenant(
        "student_service_tickets",
        ticket_id,
        {
            "student_id": int(existing.get("student_id") or 0),
            "category": str(existing.get("category") or "general"),
            "subject": str(existing.get("subject") or "No subject"),
            "description": str(existing.get("description") or "No description"),
            "priority": str(existing.get("priority") or "medium"),
            "status": request.status,
            "owner_id": str(existing.get("owner_id") or "unassigned"),
            "channel": str(existing.get("channel") or "portal"),
            "resolution_notes": (request.resolution_notes or str(existing.get("resolution_notes") or "pending")).strip()
            or "pending",
        },
        tenant_id,
    )

    _emit_audit(
        actor=actor,
        action=build_audit_action("student_services", "ticket", "status_update"),
        path=f"/internal/student-services/tickets/{ticket_id}/status",
        metadata={
            "resource_id": str(ticket_id),
            "old_status": current_status,
            "new_status": request.status,
        },
        tenant_id=tenant_id,
    )

    # Trigger unresolved alert if status transitions to risk set
    if request.status in _UNRESOLVED_RISK_STATUSES:
        _ensure_unresolved_alert_record(tenant_id, ticket_id, dict(updated))

    return StudentServiceTicketSchema.model_validate(updated)


def get_student_services_brain_context(tenant_id: int) -> dict[str, object]:
    """Return aggregated brain-context snapshot for Brain Core context builder."""
    tickets = list_entities_for_tenant("student_service_tickets", tenant_id)
    open_count = sum(1 for t in tickets if str(t.get("status", "")).lower() in {"open", "in_progress"})
    escalated_count = sum(
        1 for t in tickets
        if str(t.get("priority", "")).lower() == "high" and str(t.get("status", "")).lower() in {"open", "in_progress"}
    )
    return {
        "snapshot_type": "brain_context",
        "module": "student_services",
        "tenant_id": tenant_id,
        "total_tickets": len(tickets),
        "open_tickets": open_count,
        "escalated_high_priority_tickets": escalated_count,
        "student_services_risk_level": "high" if escalated_count > 0 else ("medium" if open_count > 5 else "low"),
    }
