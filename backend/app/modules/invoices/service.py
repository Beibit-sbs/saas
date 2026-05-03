"""Phase LXV — Invoice Management Service."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional
import uuid

from app.modules.university_core.tenant_entity_api import (
    create_entity_for_tenant,
    list_entities_for_tenant,
    update_entity_for_tenant,
)
from app.platform.events.publisher import EventPublisher

INVOICE_STATUSES = {"draft", "finalized", "sent", "paid", "overdue", "void"}
PAYMENT_METHODS = {"card", "bank_transfer", "cash", "kaspi", "cheque"}
CURRENCY_CODES = {"USD", "EUR", "KZT", "RUB", "GBP", "CNY", "AED"}


class InvoiceError(Exception):
    """Raised on invalid Invoice operations."""


@dataclass
class InvoiceItem:
    id: int
    invoice_id: int
    description: str
    quantity: int
    unit_price_cents: int
    total_cents: int


@dataclass
class Invoice:
    invoice_id: int
    tenant_id: int
    invoice_number: str
    status: str
    currency_code: str
    total_cents: int
    due_date: str
    issued_at: Optional[str]
    paid_at: Optional[str]
    voided_at: Optional[str]
    items: list = field(default_factory=list)


@dataclass
class InvoicePayment:
    payment_id: int
    invoice_id: int
    amount_cents: int
    method: str
    paid_at: str
    reference: Optional[str]


def _get_invoice_row(invoice_id: int, tenant_id: int) -> Optional[dict]:
    rows = list_entities_for_tenant("invoices", tenant_id)
    matched = [r for r in rows if r.get("id") == invoice_id]
    return matched[0] if matched else None


def _row_to_invoice(row: dict, tenant_id: int) -> Invoice:
    return Invoice(
        invoice_id=row["id"],
        tenant_id=tenant_id,
        invoice_number=row["invoice_number"],
        status=row["status"],
        currency_code=row["currency_code"],
        total_cents=row["total_cents"],
        due_date=row["due_date"],
        issued_at=row.get("issued_at"),
        paid_at=row.get("paid_at"),
        voided_at=row.get("voided_at"),
    )


def _next_invoice_number(tenant_id: int) -> str:
    short = str(uuid.uuid4())[:8].upper()
    return f"INV-{tenant_id}-{short}"


def create_invoice(
    tenant_id: int,
    currency_code: str,
    due_date: str,
    notes: str = "",
) -> Invoice:
    if not isinstance(tenant_id, int) or tenant_id <= 0:
        raise InvoiceError("tenant_id must be a positive integer")
    if currency_code not in CURRENCY_CODES:
        raise InvoiceError(f"unsupported currency_code: {currency_code}")
    try:
        date.fromisoformat(due_date)
    except (ValueError, TypeError):
        raise InvoiceError("due_date must be a valid ISO date string (YYYY-MM-DD)")

    invoice_number = _next_invoice_number(tenant_id)
    row = create_entity_for_tenant(
        "invoices",
        {
            "invoice_number": invoice_number,
            "status": "draft",
            "currency_code": currency_code,
            "total_cents": 0,
            "due_date": due_date,
            "notes": notes,
            "issued_at": None,
            "paid_at": None,
            "voided_at": None,
        },
        tenant_id,
    )
    return _row_to_invoice(row, tenant_id)


def add_item(
    invoice_id: int,
    tenant_id: int,
    description: str,
    quantity: int,
    unit_price_cents: int,
) -> InvoiceItem:
    invoice_row = _get_invoice_row(invoice_id, tenant_id)
    if invoice_row is None:
        raise InvoiceError("invoice not found")
    if invoice_row["status"] != "draft":
        raise InvoiceError("can only add items to draft invoices")
    if not description or not description.strip():
        raise InvoiceError("description is required")
    if not isinstance(quantity, int) or quantity <= 0:
        raise InvoiceError("quantity must be a positive integer")
    if not isinstance(unit_price_cents, int) or unit_price_cents < 0:
        raise InvoiceError("unit_price_cents must be a non-negative integer")

    total_cents = quantity * unit_price_cents
    item_row = create_entity_for_tenant(
        "invoice_items",
        {
            "invoice_id": invoice_id,
            "description": description.strip(),
            "quantity": quantity,
            "unit_price_cents": unit_price_cents,
            "total_cents": total_cents,
        },
        tenant_id,
    )
    return InvoiceItem(
        id=item_row["id"],
        invoice_id=invoice_id,
        description=item_row["description"],
        quantity=item_row["quantity"],
        unit_price_cents=item_row["unit_price_cents"],
        total_cents=item_row["total_cents"],
    )


def finalize_invoice(invoice_id: int, tenant_id: int) -> Invoice:
    invoice_row = _get_invoice_row(invoice_id, tenant_id)
    if invoice_row is None:
        raise InvoiceError("invoice not found")
    if invoice_row["status"] != "draft":
        raise InvoiceError("only draft invoices can be finalized")

    all_items = list_entities_for_tenant("invoice_items", tenant_id)
    items = [it for it in all_items if it.get("invoice_id") == invoice_id]
    if not items:
        raise InvoiceError("cannot finalize an invoice with no items")

    total_cents = sum(it["total_cents"] for it in items)
    issued_at = datetime.utcnow().isoformat()
    updated = update_entity_for_tenant(
        "invoices",
        invoice_id,
        {"status": "finalized", "total_cents": total_cents, "issued_at": issued_at},
        tenant_id,
    )

    try:
        EventPublisher.publish(
            tenant_id=tenant_id,
            event_type="invoice.finalized",
            payload={"invoice_id": invoice_id, "total_cents": total_cents},
        )
    except Exception:
        pass

    return _row_to_invoice(updated, tenant_id)


def send_invoice(invoice_id: int, tenant_id: int) -> Invoice:
    invoice_row = _get_invoice_row(invoice_id, tenant_id)
    if invoice_row is None:
        raise InvoiceError("invoice not found")
    if invoice_row["status"] != "finalized":
        raise InvoiceError("only finalized invoices can be sent")

    updated = update_entity_for_tenant(
        "invoices", invoice_id, {"status": "sent"}, tenant_id
    )

    try:
        EventPublisher.publish(
            tenant_id=tenant_id,
            event_type="invoice.sent",
            payload={"invoice_id": invoice_id},
        )
    except Exception:
        pass

    return _row_to_invoice(updated, tenant_id)


def mark_paid(
    invoice_id: int,
    tenant_id: int,
    amount_cents: int,
    method: str,
    reference: Optional[str] = None,
) -> InvoicePayment:
    invoice_row = _get_invoice_row(invoice_id, tenant_id)
    if invoice_row is None:
        raise InvoiceError("invoice not found")
    if invoice_row["status"] == "paid":
        raise InvoiceError("invoice is already paid")
    if invoice_row["status"] == "void":
        raise InvoiceError("cannot pay a voided invoice")
    if method not in PAYMENT_METHODS:
        raise InvoiceError(f"unsupported payment method: {method}")
    if not isinstance(amount_cents, int) or amount_cents <= 0:
        raise InvoiceError("amount_cents must be a positive integer")

    paid_at = datetime.utcnow().isoformat()
    update_entity_for_tenant(
        "invoices", invoice_id, {"status": "paid", "paid_at": paid_at}, tenant_id
    )
    payment_row = create_entity_for_tenant(
        "invoice_payments",
        {
            "invoice_id": invoice_id,
            "amount_cents": amount_cents,
            "method": method,
            "paid_at": paid_at,
            "reference": reference,
        },
        tenant_id,
    )

    try:
        EventPublisher.publish(
            tenant_id=tenant_id,
            event_type="invoice.paid",
            payload={"invoice_id": invoice_id, "amount_cents": amount_cents},
        )
    except Exception:
        pass

    return InvoicePayment(
        payment_id=payment_row["id"],
        invoice_id=invoice_id,
        amount_cents=payment_row["amount_cents"],
        method=payment_row["method"],
        paid_at=payment_row["paid_at"],
        reference=payment_row["reference"],
    )


def void_invoice(invoice_id: int, tenant_id: int, reason: str = "") -> Invoice:
    invoice_row = _get_invoice_row(invoice_id, tenant_id)
    if invoice_row is None:
        raise InvoiceError("invoice not found")
    if invoice_row["status"] == "paid":
        raise InvoiceError("cannot void a paid invoice")
    if invoice_row["status"] == "void":
        raise InvoiceError("invoice is already voided")

    voided_at = datetime.utcnow().isoformat()
    updated = update_entity_for_tenant(
        "invoices",
        invoice_id,
        {"status": "void", "voided_at": voided_at},
        tenant_id,
    )

    try:
        EventPublisher.publish(
            tenant_id=tenant_id,
            event_type="invoice.voided",
            payload={"invoice_id": invoice_id, "reason": reason},
        )
    except Exception:
        pass

    return _row_to_invoice(updated, tenant_id)


def list_invoices(
    tenant_id: int,
    status: Optional[str] = None,
) -> list[Invoice]:
    if status is not None and status not in INVOICE_STATUSES:
        raise InvoiceError(f"invalid status filter: {status}")

    rows = list_entities_for_tenant("invoices", tenant_id)
    results = []
    for row in rows:
        if status is not None and row["status"] != status:
            continue
        results.append(_row_to_invoice(row, tenant_id))
    return results


def get_invoice(invoice_id: int, tenant_id: int) -> Invoice:
    row = _get_invoice_row(invoice_id, tenant_id)
    if row is None:
        raise InvoiceError("invoice not found")
    return _row_to_invoice(row, tenant_id)
