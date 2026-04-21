from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.core.tenant import get_current_tenant
from app.modules.rbac.security import get_actor, permission_dependency
from app.modules.advising.schemas import (
    AdvisingSessionCreateSchema,
    AdvisingSessionItemResponseSchema,
    AdvisingSessionListResponseSchema,
    AdvisingSessionStatus,
    AdvisingSessionStatusUpdateSchema,
)
from app.modules.advising.service import (
    create_advising_session,
    list_advising_sessions,
    update_advising_session_status,
)


router = APIRouter(prefix="/api/admin/advising", tags=["advising"])


@router.get("", response_model=AdvisingSessionListResponseSchema)
def list_sessions_endpoint(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("advising.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
    status: AdvisingSessionStatus | None = None,
    student_id: int | None = None,
) -> AdvisingSessionListResponseSchema:
    items = list_advising_sessions(int(tenant["id"]), status=status, student_id=student_id)
    return AdvisingSessionListResponseSchema(items=items)


@router.post("", response_model=AdvisingSessionItemResponseSchema)
def create_session_endpoint(
    payload: AdvisingSessionCreateSchema,
    actor: Annotated[str, Depends(get_actor)],
    _: Annotated[None, Depends(permission_dependency("advising.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> AdvisingSessionItemResponseSchema:
    try:
        item = create_advising_session(int(tenant["id"]), payload, actor)
        return AdvisingSessionItemResponseSchema(item=item)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.patch("/{session_id}/status", response_model=AdvisingSessionItemResponseSchema)
def update_session_status_endpoint(
    session_id: int,
    payload: AdvisingSessionStatusUpdateSchema,
    actor: Annotated[str, Depends(get_actor)],
    _: Annotated[None, Depends(permission_dependency("advising.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> AdvisingSessionItemResponseSchema:
    try:
        item = update_advising_session_status(int(tenant["id"]), session_id, payload, actor)
        return AdvisingSessionItemResponseSchema(item=item)
    except ValueError as exc:
        detail = str(exc)
        status_code = 404 if "not found" in detail else 400
        raise HTTPException(status_code=status_code, detail=detail) from exc
