from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.core.module_helpers.service_validation import DomainValidationError

from app.core.tenant import get_current_tenant
from app.modules.rbac.security import get_actor, permission_dependency
from app.modules.student_services.schemas import (
    StudentServiceTicketCreateSchema,
    StudentServiceTicketItemResponseSchema,
    StudentServiceTicketListResponseSchema,
    StudentTicketStatus,
    StudentServiceTicketStatusUpdateSchema,
)
from app.modules.student_services.service import (
    create_student_service_ticket,
    get_student_services_brain_context,
    list_student_service_tickets,
    update_student_service_ticket_status,
)


router = APIRouter(prefix="/api/admin/student-services/tickets", tags=["student-services"])


@router.get("", response_model=StudentServiceTicketListResponseSchema)
def list_tickets_endpoint(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("student_services.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
    status: StudentTicketStatus | None = None,
    student_id: int | None = None,
) -> StudentServiceTicketListResponseSchema:
    items = list_student_service_tickets(int(tenant["id"]), status=status, student_id=student_id)
    return StudentServiceTicketListResponseSchema(items=items)


@router.post("", response_model=StudentServiceTicketItemResponseSchema)
def create_ticket_endpoint(
    payload: StudentServiceTicketCreateSchema,
    actor: Annotated[str, Depends(get_actor)],
    _: Annotated[None, Depends(permission_dependency("student_services.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> StudentServiceTicketItemResponseSchema:
    try:
        item = create_student_service_ticket(int(tenant["id"]), payload, actor)
        return StudentServiceTicketItemResponseSchema(item=item)
    except (ValueError, DomainValidationError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.patch("/{ticket_id}/status", response_model=StudentServiceTicketItemResponseSchema)
def update_ticket_status_endpoint(
    ticket_id: int,
    payload: StudentServiceTicketStatusUpdateSchema,
    actor: Annotated[str, Depends(get_actor)],
    _: Annotated[None, Depends(permission_dependency("student_services.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> StudentServiceTicketItemResponseSchema:
    try:
        item = update_student_service_ticket_status(int(tenant["id"]), ticket_id, payload, actor)
        return StudentServiceTicketItemResponseSchema(item=item)
    except ValueError as exc:
        detail = str(exc)
        status_code = 404 if "not found" in detail else 400
        raise HTTPException(status_code=status_code, detail=detail) from exc


@router.get("/brain-context", response_model=dict, tags=["student-services", "brain-core"])
def get_student_services_brain_context_endpoint(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("student_services.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict:
    """Return aggregated brain-context snapshot for Brain Core context builder.

    Used by Brain Core to enrich decisions with student services signals:
    total tickets, open tickets, escalated high-priority tickets, risk level.
    """
    return get_student_services_brain_context(int(tenant["id"]))
