"""A-018.6: Visitor Management router."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.core.tenant import get_current_tenant
from app.modules.rbac.security import get_actor, permission_dependency
from app.modules.visitor_management.schemas import (
    UnauthorizedAttemptPayload,
    UnauthorizedAttemptResponse,
    VisitActionResponse,
    VisitActionWithBadgeResponse,
    VisitCancelPayload,
    VisitCheckInPayload,
    VisitListResponse,
    VisitRejectPayload,
    VisitorRegisterPayload,
    VisitorRegisterResponse,
)
import app.modules.visitor_management.service as _svc


router = APIRouter(prefix="/api/admin/visitor-management", tags=["visitor-management"])


@router.post("/visitors", response_model=VisitorRegisterResponse, status_code=201)
def register_visitor_endpoint(
    payload: VisitorRegisterPayload,
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("operations.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> VisitorRegisterResponse:
    try:
        return VisitorRegisterResponse(
            **_svc.register_visitor(
                int(tenant["id"]),
                name=payload.name,
                host_id=payload.host_id,
                purpose=payload.purpose,
                visit_date=payload.visit_date,
            )
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/visitors", response_model=VisitListResponse)
def list_visits_endpoint(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("operations.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
    status: str | None = None,
    host_id: str | None = None,
) -> VisitListResponse:
    return VisitListResponse(
        records=_svc.list_visits(int(tenant["id"]), status=status, host_id=host_id)
    )


@router.post("/visitors/{visit_id}/approve", response_model=VisitActionResponse)
def approve_visit_endpoint(
    visit_id: str,
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("operations.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> VisitActionResponse:
    try:
        return VisitActionResponse(**_svc.approve_visit(int(tenant["id"]), visit_id=visit_id))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/visitors/{visit_id}/reject", response_model=VisitActionResponse)
def reject_visit_endpoint(
    visit_id: str,
    payload: VisitRejectPayload,
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("operations.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> VisitActionResponse:
    try:
        return VisitActionResponse(
            **_svc.reject_visit(int(tenant["id"]), visit_id=visit_id, reason=payload.reason)
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/visitors/{visit_id}/cancel", response_model=VisitActionResponse)
def cancel_visit_endpoint(
    visit_id: str,
    payload: VisitCancelPayload,
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("operations.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> VisitActionResponse:
    try:
        return VisitActionResponse(
            **_svc.cancel_visit(int(tenant["id"]), visit_id=visit_id, reason=payload.reason)
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/visitors/{visit_id}/check-in", response_model=VisitActionWithBadgeResponse)
def check_in_visitor_endpoint(
    visit_id: str,
    payload: VisitCheckInPayload,
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("operations.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> VisitActionWithBadgeResponse:
    try:
        return VisitActionWithBadgeResponse(
            **_svc.check_in_visitor(int(tenant["id"]), visit_id=visit_id, badge_number=payload.badge_number)
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/visitors/{visit_id}/check-out", response_model=VisitActionResponse)
def check_out_visitor_endpoint(
    visit_id: str,
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("operations.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> VisitActionResponse:
    try:
        return VisitActionResponse(**_svc.check_out_visitor(int(tenant["id"]), visit_id=visit_id))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/unauthorized-attempts", response_model=UnauthorizedAttemptResponse, status_code=201)
def record_unauthorized_attempt_endpoint(
    payload: UnauthorizedAttemptPayload,
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("operations.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> UnauthorizedAttemptResponse:
    try:
        result = _svc.record_unauthorized_attempt(
            int(tenant["id"]),
            visitor_name=payload.visitor_name,
            zone=payload.zone,
            access_point_id=payload.access_point_id,
            reason=payload.reason,
        )
        return UnauthorizedAttemptResponse(**result)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
