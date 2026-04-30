"""Phase X-X3: Delinquency & Collections router."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.core.tenant import get_current_tenant
from app.core.module_helpers.service_validation import DomainValidationError
from app.modules.delinquency_collections.schemas import (
    DelinquencyEscalationUpdateSchema,
    DelinquencyItemResponseSchema,
    DelinquencyListResponseSchema,
    DelinquencyRecordCreateSchema,
    DelinquencyStatus,
    DelinquencyStatusUpdateSchema,
    EscalationStage,
)
import app.modules.delinquency_collections.service as _svc
from app.modules.rbac.security import get_actor, permission_dependency


router = APIRouter(prefix="/api/admin/delinquency-collections", tags=["delinquency-collections"])


@router.get("", response_model=DelinquencyListResponseSchema)
def list_delinquency_records_endpoint(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("finance.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
    status: DelinquencyStatus | None = None,
    escalation_stage: EscalationStage | None = None,
) -> DelinquencyListResponseSchema:
    items = _svc.list_delinquency_records(int(tenant["id"]), status=status, escalation_stage=escalation_stage)
    return DelinquencyListResponseSchema(items=items)


@router.post("", response_model=DelinquencyItemResponseSchema)
def create_delinquency_record_endpoint(
    payload: DelinquencyRecordCreateSchema,
    actor: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("finance.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> DelinquencyItemResponseSchema:
    try:
        item = _svc.create_delinquency_record(int(tenant["id"]), payload, actor)
    except (ValueError, DomainValidationError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return DelinquencyItemResponseSchema(item=item)


@router.get("/{record_id}", response_model=DelinquencyItemResponseSchema)
def get_delinquency_record_endpoint(
    record_id: int,
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("finance.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> DelinquencyItemResponseSchema:
    item = _svc.get_delinquency_record(int(tenant["id"]), record_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Delinquency record not found")
    return DelinquencyItemResponseSchema(item=item)


@router.patch("/{record_id}/status", response_model=DelinquencyItemResponseSchema)
def update_delinquency_status_endpoint(
    record_id: int,
    payload: DelinquencyStatusUpdateSchema,
    actor: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("finance.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> DelinquencyItemResponseSchema:
    try:
        item = _svc.update_delinquency_status(int(tenant["id"]), record_id, payload, actor)
    except (ValueError, DomainValidationError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    if item is None:
        raise HTTPException(status_code=404, detail="Delinquency record not found")
    return DelinquencyItemResponseSchema(item=item)


@router.patch("/{record_id}/escalation", response_model=DelinquencyItemResponseSchema)
def update_delinquency_escalation_endpoint(
    record_id: int,
    payload: DelinquencyEscalationUpdateSchema,
    actor: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("finance.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> DelinquencyItemResponseSchema:
    try:
        item = _svc.update_delinquency_escalation(int(tenant["id"]), record_id, payload, actor)
    except (ValueError, DomainValidationError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    if item is None:
        raise HTTPException(status_code=404, detail="Delinquency record not found")
    return DelinquencyItemResponseSchema(item=item)
