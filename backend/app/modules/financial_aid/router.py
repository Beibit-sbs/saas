from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.core.module_helpers.service_validation import DomainValidationError
from app.core.tenant import get_current_tenant
from app.modules.financial_aid.schemas import (
    AidStatus,
    FinancialAidRecordCreateSchema,
    FinancialAidRecordItemResponseSchema,
    FinancialAidRecordListResponseSchema,
    FinancialAidRecordStatusUpdateSchema,
)
import app.modules.financial_aid.service as _svc
from app.modules.rbac.security import get_actor, permission_dependency


router = APIRouter(prefix="/api/admin/financial-aid", tags=["financial-aid"])


@router.get("", response_model=FinancialAidRecordListResponseSchema)
def list_records_endpoint(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("financial_aid.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
    status: AidStatus | None = None,
    student_id: int | None = None,
) -> FinancialAidRecordListResponseSchema:
    items = _svc.list_financial_aid_records(int(tenant["id"]), status=status, student_id=student_id)
    return FinancialAidRecordListResponseSchema(items=items)


@router.post("", response_model=FinancialAidRecordItemResponseSchema)
def create_record_endpoint(
    payload: FinancialAidRecordCreateSchema,
    actor: Annotated[str, Depends(get_actor)],
    _: Annotated[None, Depends(permission_dependency("financial_aid.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> FinancialAidRecordItemResponseSchema:
    try:
        item = _svc.create_financial_aid_record(int(tenant["id"]), payload, actor)
        return FinancialAidRecordItemResponseSchema(item=item)
    except (ValueError, DomainValidationError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.patch("/{record_id}/status", response_model=FinancialAidRecordItemResponseSchema)
def update_record_status_endpoint(
    record_id: int,
    payload: FinancialAidRecordStatusUpdateSchema,
    actor: Annotated[str, Depends(get_actor)],
    _: Annotated[None, Depends(permission_dependency("financial_aid.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> FinancialAidRecordItemResponseSchema:
    try:
        item = _svc.update_financial_aid_status(int(tenant["id"]), record_id, payload, actor)
        return FinancialAidRecordItemResponseSchema(item=item)
    except DomainValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except ValueError as exc:
        detail = str(exc)
        status_code = 404 if "not found" in detail else 400
        raise HTTPException(status_code=status_code, detail=detail) from exc
