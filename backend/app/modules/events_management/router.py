"""Events Management router (A-018.4 maturity closure)."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.core.tenant import get_current_tenant
from app.modules.events_management import service as events_management_service
from app.modules.events_management.schemas import (
    EventCreatePayload,
    GenericEventsManagementListResponse,
    GenericEventsManagementResponse,
    ParticipantRegistrationPayload,
)
from app.modules.rbac.security import get_actor, permission_dependency

router = APIRouter(prefix="/api/admin/events-management", tags=["events-management"])


def _to_http_422(exc: Exception) -> HTTPException:
    return HTTPException(status_code=422, detail=str(exc))


@router.get("/events", response_model=GenericEventsManagementListResponse)
def list_events_endpoint(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("scheduling.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
    status: str | None = None,
    category_id: str | None = None,
) -> GenericEventsManagementListResponse:
    records = events_management_service.list_events(
        int(tenant["id"]),
        status=status,
        category_id=category_id,
    )
    return GenericEventsManagementListResponse(records=records)


@router.post("/events", response_model=GenericEventsManagementResponse, status_code=201)
def create_event_endpoint(
    payload: EventCreatePayload,
    actor: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("scheduling.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> GenericEventsManagementResponse:
    try:
        record = events_management_service.create_event(
            int(tenant["id"]),
            **payload.model_dump(),
            actor=actor,
        )
    except ValueError as exc:
        raise _to_http_422(exc) from exc
    return GenericEventsManagementResponse(record=record)


@router.post("/events/{event_id}/publish", response_model=GenericEventsManagementResponse)
def publish_event_endpoint(
    event_id: str,
    actor: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("scheduling.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> GenericEventsManagementResponse:
    try:
        record = events_management_service.publish_event(
            int(tenant["id"]),
            event_id=event_id,
            actor=actor,
        )
    except ValueError as exc:
        raise _to_http_422(exc) from exc
    return GenericEventsManagementResponse(record=record)


@router.post("/events/{event_id}/open-registration", response_model=GenericEventsManagementResponse)
def open_registration_endpoint(
    event_id: str,
    actor: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("scheduling.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> GenericEventsManagementResponse:
    try:
        record = events_management_service.open_registration(
            int(tenant["id"]),
            event_id=event_id,
            actor=actor,
        )
    except ValueError as exc:
        raise _to_http_422(exc) from exc
    return GenericEventsManagementResponse(record=record)


@router.post("/events/{event_id}/start", response_model=GenericEventsManagementResponse)
def start_event_endpoint(
    event_id: str,
    actor: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("scheduling.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> GenericEventsManagementResponse:
    try:
        record = events_management_service.start_event(
            int(tenant["id"]),
            event_id=event_id,
            actor=actor,
        )
    except ValueError as exc:
        raise _to_http_422(exc) from exc
    return GenericEventsManagementResponse(record=record)


@router.post("/events/{event_id}/complete", response_model=GenericEventsManagementResponse)
def complete_event_endpoint(
    event_id: str,
    actor: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("scheduling.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> GenericEventsManagementResponse:
    try:
        record = events_management_service.complete_event(
            int(tenant["id"]),
            event_id=event_id,
            actor=actor,
        )
    except ValueError as exc:
        raise _to_http_422(exc) from exc
    return GenericEventsManagementResponse(record=record)


@router.post("/events/{event_id}/cancel", response_model=GenericEventsManagementResponse)
def cancel_event_endpoint(
    event_id: str,
    actor: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("scheduling.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> GenericEventsManagementResponse:
    try:
        record = events_management_service.cancel_event(
            int(tenant["id"]),
            event_id=event_id,
            actor=actor,
        )
    except ValueError as exc:
        raise _to_http_422(exc) from exc
    return GenericEventsManagementResponse(record=record)


@router.get("/registrations", response_model=GenericEventsManagementListResponse)
def list_registrations_endpoint(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("scheduling.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
    event_id: str | None = None,
    student_id: str | None = None,
) -> GenericEventsManagementListResponse:
    records = events_management_service.list_registrations(
        int(tenant["id"]),
        event_id=event_id,
        student_id=student_id,
    )
    return GenericEventsManagementListResponse(records=records)


@router.post("/events/{event_id}/register", response_model=GenericEventsManagementResponse, status_code=201)
def register_participant_endpoint(
    event_id: str,
    payload: ParticipantRegistrationPayload,
    actor: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("scheduling.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> GenericEventsManagementResponse:
    try:
        record = events_management_service.register_participant(
            int(tenant["id"]),
            event_id=event_id,
            student_id=payload.student_id,
            actor=actor,
        )
    except ValueError as exc:
        raise _to_http_422(exc) from exc
    return GenericEventsManagementResponse(record=record)