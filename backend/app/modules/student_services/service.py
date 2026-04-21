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


_ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    "open": {"in_progress", "resolved", "closed"},
    "in_progress": {"resolved", "closed"},
    "resolved": {"closed", "in_progress"},
    "closed": set(),
}


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
    return StudentServiceTicketSchema.model_validate(updated)
