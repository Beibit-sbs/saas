"""Phase LXVI — Invoice Management Router."""
from __future__ import annotations

from dataclasses import asdict
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.modules.invoices.service import (
    InvoiceError,
    add_item,
    create_invoice,
    finalize_invoice,
    get_invoice,
    list_invoices,
    mark_paid,
    send_invoice,
    void_invoice,
)

router = APIRouter(prefix="/api/invoices", tags=["invoices"])


class CreateInvoicePayload(BaseModel):
    tenant_id: int = Field(gt=0)
    currency_code: str = Field(min_length=3, max_length=3)
    due_date: str = Field(min_length=1)
    notes: str = ""


class AddItemPayload(BaseModel):
    tenant_id: int = Field(gt=0)
    description: str = Field(min_length=1)
    quantity: int = Field(gt=0)
    unit_price_cents: int = Field(ge=0)


class MarkPaidPayload(BaseModel):
    tenant_id: int = Field(gt=0)
    amount_cents: int = Field(gt=0)
    method: str = Field(min_length=1)
    reference: Optional[str] = None


class VoidInvoicePayload(BaseModel):
    tenant_id: int = Field(gt=0)
    reason: str = ""


@router.post("")
def create_invoice_endpoint(payload: CreateInvoicePayload) -> dict:
    try:
        invoice = create_invoice(
            tenant_id=payload.tenant_id,
            currency_code=payload.currency_code,
            due_date=payload.due_date,
            notes=payload.notes,
        )
    except InvoiceError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return asdict(invoice)


@router.get("")
def list_invoices_endpoint(
    tenant_id: int = Query(gt=0),
    status: Optional[str] = Query(default=None),
) -> list[dict]:
    try:
        invoices = list_invoices(tenant_id=tenant_id, status=status)
    except InvoiceError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return [asdict(inv) for inv in invoices]


@router.get("/{invoice_id}")
def get_invoice_endpoint(invoice_id: int, tenant_id: int = Query(gt=0)) -> dict:
    try:
        invoice = get_invoice(invoice_id=invoice_id, tenant_id=tenant_id)
    except InvoiceError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return asdict(invoice)


@router.post("/{invoice_id}/items")
def add_item_endpoint(invoice_id: int, payload: AddItemPayload) -> dict:
    try:
        item = add_item(
            invoice_id=invoice_id,
            tenant_id=payload.tenant_id,
            description=payload.description,
            quantity=payload.quantity,
            unit_price_cents=payload.unit_price_cents,
        )
    except InvoiceError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return asdict(item)


@router.post("/{invoice_id}/finalize")
def finalize_invoice_endpoint(invoice_id: int, tenant_id: int = Query(gt=0)) -> dict:
    try:
        invoice = finalize_invoice(invoice_id=invoice_id, tenant_id=tenant_id)
    except InvoiceError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return asdict(invoice)


@router.post("/{invoice_id}/send")
def send_invoice_endpoint(invoice_id: int, tenant_id: int = Query(gt=0)) -> dict:
    try:
        invoice = send_invoice(invoice_id=invoice_id, tenant_id=tenant_id)
    except InvoiceError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return asdict(invoice)


@router.post("/{invoice_id}/pay")
def mark_paid_endpoint(invoice_id: int, payload: MarkPaidPayload) -> dict:
    try:
        payment = mark_paid(
            invoice_id=invoice_id,
            tenant_id=payload.tenant_id,
            amount_cents=payload.amount_cents,
            method=payload.method,
            reference=payload.reference,
        )
    except InvoiceError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return asdict(payment)


@router.post("/{invoice_id}/void")
def void_invoice_endpoint(invoice_id: int, payload: VoidInvoicePayload) -> dict:
    try:
        invoice = void_invoice(
            invoice_id=invoice_id,
            tenant_id=payload.tenant_id,
            reason=payload.reason,
        )
    except InvoiceError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return asdict(invoice)
