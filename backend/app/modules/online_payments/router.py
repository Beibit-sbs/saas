"""Phase LXVIII — Online Payments Router."""
from __future__ import annotations

from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.modules.rbac.security import permission_dependency
from app.modules.online_payments.service import (
    check_failure_pattern,
    complete_payment,
    create_payment,
    fail_payment,
    get_payment,
    list_payments,
    process_payment,
    refund_payment,
)

router = APIRouter(
    prefix="/api/payments",
    tags=["payments"],
    # A-009 Phase 2.1: Add permission_dependency guard (HIGH severity fix for 64 unguarded endpoints)
    dependencies=[Depends(permission_dependency("payments.admin.write"))],
)


class CreatePaymentPayload(BaseModel):
    tenant_id: int = Field(gt=0)
    student_id: str = Field(min_length=1)
    amount: float = Field(gt=0)
    currency: str = "KZT"
    method: str = Field(min_length=1)
    description: str = ""


class CompletePaymentPayload(BaseModel):
    tenant_id: int = Field(gt=0)
    transaction_ref: str = Field(min_length=1)


class FailPaymentPayload(BaseModel):
    tenant_id: int = Field(gt=0)
    reason: str = Field(min_length=1)


class RefundPaymentPayload(BaseModel):
    tenant_id: int = Field(gt=0)
    reason: str = Field(min_length=1)


# ─── POST /api/payments ───────────────────────────────────────────────────────

@router.post("")
def create_payment_endpoint(payload: CreatePaymentPayload) -> dict:
    try:
        result = create_payment(
            payload.tenant_id,
            student_id=payload.student_id,
            amount=payload.amount,
            currency=payload.currency,
            method=payload.method,
            description=payload.description,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return result


# ─── GET /api/payments ────────────────────────────────────────────────────────

@router.get("")
def list_payments_endpoint(
    tenant_id: int = Query(gt=0),
    student_id: Optional[str] = Query(default=None),
    status: Optional[str] = Query(default=None),
) -> list[dict]:
    try:
        return list_payments(tenant_id=tenant_id, student_id=student_id, status=status)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


# ─── GET /api/payments/failure-pattern ───────────────────────────────────────

@router.get("/failure-pattern")
def failure_pattern_endpoint(
    tenant_id: int = Query(gt=0),
    student_id: str = Query(min_length=1),
) -> dict:
    try:
        return check_failure_pattern(tenant_id, student_id=student_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


# ─── GET /api/payments/{payment_id} ──────────────────────────────────────────

@router.get("/{payment_id}")
def get_payment_endpoint(
    payment_id: str,
    tenant_id: int = Query(gt=0),
) -> dict:
    try:
        return get_payment(tenant_id, payment_id=payment_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


# ─── POST /api/payments/{payment_id}/process ─────────────────────────────────

@router.post("/{payment_id}/process")
def process_payment_endpoint(
    payment_id: str,
    tenant_id: int = Query(gt=0),
) -> dict:
    try:
        return process_payment(tenant_id, payment_id=payment_id)
    except (ValueError, LookupError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


# ─── POST /api/payments/{payment_id}/complete ────────────────────────────────

@router.post("/{payment_id}/complete")
def complete_payment_endpoint(payment_id: str, payload: CompletePaymentPayload) -> dict:
    try:
        return complete_payment(
            payload.tenant_id,
            payment_id=payment_id,
            transaction_ref=payload.transaction_ref,
        )
    except (ValueError, LookupError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


# ─── POST /api/payments/{payment_id}/fail ────────────────────────────────────

@router.post("/{payment_id}/fail")
def fail_payment_endpoint(payment_id: str, payload: FailPaymentPayload) -> dict:
    try:
        return fail_payment(
            payload.tenant_id,
            payment_id=payment_id,
            reason=payload.reason,
        )
    except (ValueError, LookupError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


# ─── POST /api/payments/{payment_id}/refund ──────────────────────────────────

@router.post("/{payment_id}/refund")
def refund_payment_endpoint(payment_id: str, payload: RefundPaymentPayload) -> dict:
    try:
        return refund_payment(
            payload.tenant_id,
            payment_id=payment_id,
            reason=payload.reason,
        )
    except (ValueError, LookupError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
