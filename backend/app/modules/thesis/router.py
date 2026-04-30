from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.core.tenant import get_current_tenant
from app.modules.rbac.security import get_actor, permission_dependency
from app.modules.thesis.schemas import (
    ThesisCreateSchema,
    ThesisItemResponseSchema,
    ThesisListResponseSchema,
    ThesisStatus,
    ThesisStatusUpdateSchema,
)
from app.modules.thesis.service import create_thesis_record, list_thesis_records, update_thesis_status


router = APIRouter(prefix="/api/admin/thesis", tags=["thesis"])


@router.get("", response_model=ThesisListResponseSchema)
def list_thesis_endpoint(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("transcripts.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
    status: ThesisStatus | None = None,
) -> ThesisListResponseSchema:
    items = list_thesis_records(int(tenant["id"]), status=status)
    return ThesisListResponseSchema(items=items)


@router.post("", response_model=ThesisItemResponseSchema)
def create_thesis_endpoint(
    payload: ThesisCreateSchema,
    actor: Annotated[str, Depends(get_actor)],
    _: Annotated[None, Depends(permission_dependency("transcripts.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> ThesisItemResponseSchema:
    try:
        item = create_thesis_record(int(tenant["id"]), payload, actor)
        return ThesisItemResponseSchema(item=item)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.patch("/{thesis_id}/status", response_model=ThesisItemResponseSchema)
def update_thesis_status_endpoint(
    thesis_id: int,
    payload: ThesisStatusUpdateSchema,
    actor: Annotated[str, Depends(get_actor)],
    _: Annotated[None, Depends(permission_dependency("transcripts.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> ThesisItemResponseSchema:
    try:
        item = update_thesis_status(int(tenant["id"]), thesis_id, payload, actor)
        return ThesisItemResponseSchema(item=item)
    except ValueError as exc:
        detail = str(exc)
        status_code = 404 if "not found" in detail else 400
        raise HTTPException(status_code=status_code, detail=detail) from exc
