"""Phase LXXI — Payment Reconciliation Router.

Endpoints:
  POST   /api/reconciliations
  GET    /api/reconciliations
  GET    /api/reconciliations/{reconciliation_id}
  POST   /api/reconciliations/{reconciliation_id}/cancel
  POST   /api/reconciliations/auto
"""
from __future__ import annotations

from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.modules.rbac.security import permission_dependency
from app.modules.payment_reconciliation.service import (
    auto_reconcile,
    get_reconciliation,
    list_reconciliations,
    reconcile_payment,
    unreconcile,
)

router = APIRouter(
    prefix="/api/reconciliations",
    tags=["reconciliations"],
    # A-009 Phase 2.1: Add permission_dependency guard (HIGH severity fix for 64 unguarded endpoints)
    dependencies=[Depends(permission_dependency("payment_reconciliation.admin.write"))],
)


# ─── schemas ──────────────────────────────────────────────────────────────────

class ReconcilePayload(BaseModel):
    tenant_id: int = Field(gt=0)
    payment_id: str = Field(min_length=1)
    invoice_id: str = Field(min_length=1)
    notes: str = ""


class CancelPayload(BaseModel):
    tenant_id: int = Field(gt=0)
    reason: str = ""


class AutoReconcilePayload(BaseModel):
    tenant_id: int = Field(gt=0)
    invoice_id: str = Field(min_length=1)


# ─── POST /api/reconciliations ────────────────────────────────────────────────

@router.post("")
def reconcile_endpoint(payload: ReconcilePayload) -> dict:
    try:
        return reconcile_payment(
            payload.tenant_id,
            payment_id=payload.payment_id,
            invoice_id=payload.invoice_id,
            notes=payload.notes,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


# ─── GET /api/reconciliations ─────────────────────────────────────────────────

@router.get("")
def list_reconciliations_endpoint(
    tenant_id: int = Query(gt=0),
    invoice_id: Optional[str] = Query(default=None),
    payment_id: Optional[str] = Query(default=None),
) -> list[dict]:
    try:
        return list_reconciliations(
            tenant_id,
            invoice_id=invoice_id,
            payment_id=payment_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


# ─── GET /api/reconciliations/{reconciliation_id} ─────────────────────────────

@router.get("/{reconciliation_id}")
def get_reconciliation_endpoint(
    reconciliation_id: str,
    tenant_id: int = Query(gt=0),
) -> dict:
    try:
        return get_reconciliation(tenant_id, reconciliation_id=reconciliation_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


# ─── POST /api/reconciliations/{reconciliation_id}/cancel ────────────────────

@router.post("/{reconciliation_id}/cancel")
def cancel_reconciliation_endpoint(
    reconciliation_id: str,
    payload: CancelPayload,
) -> dict:
    try:
        return unreconcile(
            payload.tenant_id,
            reconciliation_id=reconciliation_id,
            reason=payload.reason,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


# ─── POST /api/reconciliations/auto ──────────────────────────────────────────

@router.post("/auto")
def auto_reconcile_endpoint(payload: AutoReconcilePayload) -> dict:
    try:
        return auto_reconcile(payload.tenant_id, invoice_id=payload.invoice_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
