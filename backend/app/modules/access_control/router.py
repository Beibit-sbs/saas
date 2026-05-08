"""Access Control router (A-018.3 maturity closure)."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.core.tenant import get_current_tenant
from app.modules.rbac.security import get_actor, permission_dependency
from app.modules.access_control.schemas import (
    AttemptAccessPayload,
    CardIdPayload,
    GenericAccessControlListResponse,
    GenericAccessControlResponse,
    IssueCardPayload,
    SuspendCardPayload,
)
from app.modules.access_control import service as access_control_service

router = APIRouter(prefix="/api/admin/access-control", tags=["access-control"])


def _to_http_422(exc: Exception) -> HTTPException:
    return HTTPException(status_code=422, detail=str(exc))


@router.get("/cards", response_model=GenericAccessControlListResponse)
def list_cards_endpoint(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("access_control.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
    status: str | None = None,
) -> GenericAccessControlListResponse:
    return GenericAccessControlListResponse(
        records=access_control_service.list_cards(int(tenant["id"]), status=status)
    )


@router.post("/cards/issue", response_model=GenericAccessControlResponse, status_code=201)
def issue_card_endpoint(
    payload: IssueCardPayload,
    actor: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("access_control.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> GenericAccessControlResponse:
    try:
        record = access_control_service.issue_card(
            int(tenant["id"]),
            holder_id=payload.holder_id,
            zones=payload.zones,
            actor=actor,
        )
    except ValueError as exc:
        raise _to_http_422(exc) from exc
    return GenericAccessControlResponse(record=record)


@router.post("/cards/suspend", response_model=GenericAccessControlResponse)
def suspend_card_endpoint(
    payload: SuspendCardPayload,
    actor: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("access_control.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> GenericAccessControlResponse:
    try:
        record = access_control_service.suspend_card(
            int(tenant["id"]),
            card_id=payload.card_id,
            reason=payload.reason,
            actor=actor,
        )
    except ValueError as exc:
        raise _to_http_422(exc) from exc
    return GenericAccessControlResponse(record=record)


@router.post("/cards/reactivate", response_model=GenericAccessControlResponse)
def reactivate_card_endpoint(
    payload: CardIdPayload,
    actor: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("access_control.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> GenericAccessControlResponse:
    try:
        record = access_control_service.reactivate_card(
            int(tenant["id"]),
            card_id=payload.card_id,
            actor=actor,
        )
    except ValueError as exc:
        raise _to_http_422(exc) from exc
    return GenericAccessControlResponse(record=record)


@router.post("/cards/revoke", response_model=GenericAccessControlResponse)
def revoke_card_endpoint(
    payload: CardIdPayload,
    actor: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("access_control.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> GenericAccessControlResponse:
    try:
        record = access_control_service.revoke_card(
            int(tenant["id"]),
            card_id=payload.card_id,
            actor=actor,
        )
    except ValueError as exc:
        raise _to_http_422(exc) from exc
    return GenericAccessControlResponse(record=record)


@router.post("/access/attempt", response_model=GenericAccessControlResponse)
def attempt_access_endpoint(
    payload: AttemptAccessPayload,
    actor: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("access_control.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> GenericAccessControlResponse:
    try:
        record = access_control_service.attempt_access(
            int(tenant["id"]),
            card_id=payload.card_id,
            zone=payload.zone,
            actor=actor,
        )
    except ValueError as exc:
        raise _to_http_422(exc) from exc
    return GenericAccessControlResponse(record=record)


@router.get("/access/logs", response_model=GenericAccessControlListResponse)
def list_access_logs_endpoint(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("access_control.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
    card_id: str | None = None,
    zone: str | None = None,
) -> GenericAccessControlListResponse:
    return GenericAccessControlListResponse(
        records=access_control_service.list_access_logs(
            int(tenant["id"]), card_id=card_id, zone=zone
        )
    )
