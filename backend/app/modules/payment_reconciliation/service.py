"""Phase LXX — Payment Reconciliation Service.

Сервис сверки онлайн-платежей с инвойсами.

Операции:
  reconcile_payment(tenant_id, *, payment_id, invoice_id, notes="")
      Привязывает COMPLETED платёж к инвойсу.
      Возвращает dict (reconciliation record).

  get_reconciliation(tenant_id, *, reconciliation_id)
      Возвращает запись сверки по ID.
      Raises LookupError если не найдено.

  list_reconciliations(tenant_id, *, invoice_id=None, payment_id=None)
      Список сверок. Фильтрация по invoice_id или payment_id.

  unreconcile(tenant_id, *, reconciliation_id, reason="")
      Отменяет сверку (помечает cancelled).
      Raises LookupError если не найдено.
      Raises ValueError если уже cancelled.

  auto_reconcile(tenant_id, *, invoice_id)
      Автоматически ищет подходящий COMPLETED несвязанный платёж
      по student_id инвойса и выполняет сверку.
      Raises LookupError если инвойс не найден.
      Raises ValueError если нет подходящего платежа.

События:
  reconciliation.created
  reconciliation.cancelled
  reconciliation.auto_completed
"""
from __future__ import annotations

from datetime import UTC, datetime
from typing import Optional
import uuid

from app.modules.university_core.tenant_entity_api import (
    create_entity_for_tenant,
    list_entities_for_tenant,
    update_entity_for_tenant,
)
from app.platform.events.publisher import EventPublisher

# ─── constants ────────────────────────────────────────────────────────────────

RECONCILIATION_STATUSES = frozenset({"active", "cancelled"})


def _utc_now() -> datetime:
    return datetime.now(UTC)


# ─── helpers ──────────────────────────────────────────────────────────────────

def _fire(tenant_id: int, event_type: str, payload: dict) -> None:
    try:
        pub = EventPublisher(tenant_id=tenant_id)
        pub.publish_event(event_type=event_type, payload=payload)
    except Exception:
        pass


def _validate_tenant(tenant_id: int) -> None:
    if not tenant_id or tenant_id <= 0:
        raise ValueError("tenant_id must be a positive integer")


def _get_rec(tenant_id: int, reconciliation_id: str) -> dict:
    records = list_entities_for_tenant("payment_reconciliations", tenant_id=tenant_id)
    rec = next(
        (r for r in records if str(r.get("id", "")) == str(reconciliation_id)),
        None,
    )
    if rec is None:
        raise LookupError(
            f"Reconciliation {reconciliation_id} not found for tenant {tenant_id}"
        )
    return rec


def _get_payment_rows(tenant_id: int) -> list[dict]:
    return list_entities_for_tenant("payment_orders", tenant_id=tenant_id)


def _get_invoice_rows(tenant_id: int) -> list[dict]:
    return list_entities_for_tenant("invoices", tenant_id=tenant_id)


# ─── public API ───────────────────────────────────────────────────────────────

def reconcile_payment(
    tenant_id: int,
    *,
    payment_id: str,
    invoice_id: str,
    notes: str = "",
) -> dict:
    """Привязать COMPLETED платёж к инвойсу."""
    _validate_tenant(tenant_id)

    # Validate payment exists and is COMPLETED
    payments = _get_payment_rows(tenant_id)
    payment = next(
        (p for p in payments if str(p.get("id", "")) == str(payment_id)),
        None,
    )
    if payment is None:
        raise LookupError(f"Payment {payment_id} not found")
    if payment.get("status") != "COMPLETED":
        raise ValueError(
            f"Payment {payment_id} must be in COMPLETED status to reconcile "
            f"(current: {payment.get('status')})"
        )

    # Validate invoice exists
    invoices = _get_invoice_rows(tenant_id)
    invoice = next(
        (i for i in invoices if str(i.get("id", "")) == str(invoice_id)),
        None,
    )
    if invoice is None:
        raise LookupError(f"Invoice {invoice_id} not found")

    # Check no active reconciliation already exists for this payment
    existing = list_entities_for_tenant("payment_reconciliations", tenant_id=tenant_id)
    duplicate = next(
        (r for r in existing
         if str(r.get("payment_id", "")) == str(payment_id)
         and r.get("status") == "active"),
        None,
    )
    if duplicate is not None:
        raise ValueError(
            f"Payment {payment_id} is already reconciled (reconciliation {duplicate.get('id')})"
        )

    rec_id = str(uuid.uuid4())
    now = _utc_now().isoformat()
    record = {
        "id": rec_id,
        "tenant_id": tenant_id,
        "payment_id": str(payment_id),
        "invoice_id": str(invoice_id),
        "status": "active",
        "notes": notes,
        "created_at": now,
        "cancelled_at": None,
        "cancel_reason": None,
    }
    create_entity_for_tenant("payment_reconciliations", tenant_id=tenant_id, data=record)
    _fire(tenant_id, "reconciliation.created", {"reconciliation_id": rec_id, **record})
    return record


def get_reconciliation(tenant_id: int, *, reconciliation_id: str) -> dict:
    """Получить запись сверки."""
    _validate_tenant(tenant_id)
    return _get_rec(tenant_id, reconciliation_id)


def list_reconciliations(
    tenant_id: int,
    *,
    invoice_id: Optional[str] = None,
    payment_id: Optional[str] = None,
) -> list[dict]:
    """Список сверок с опциональной фильтрацией."""
    _validate_tenant(tenant_id)
    records = list_entities_for_tenant("payment_reconciliations", tenant_id=tenant_id)
    if invoice_id is not None:
        records = [r for r in records if str(r.get("invoice_id", "")) == str(invoice_id)]
    if payment_id is not None:
        records = [r for r in records if str(r.get("payment_id", "")) == str(payment_id)]
    return records


def unreconcile(tenant_id: int, *, reconciliation_id: str, reason: str = "") -> dict:
    """Отменить сверку."""
    _validate_tenant(tenant_id)
    rec = _get_rec(tenant_id, reconciliation_id)
    if rec.get("status") == "cancelled":
        raise ValueError(f"Reconciliation {reconciliation_id} is already cancelled")

    now = _utc_now().isoformat()
    updated = {
        **rec,
        "status": "cancelled",
        "cancelled_at": now,
        "cancel_reason": reason,
    }
    update_entity_for_tenant(
        "payment_reconciliations",
        tenant_id=tenant_id,
        entity_id=reconciliation_id,
        data=updated,
    )
    _fire(
        tenant_id,
        "reconciliation.cancelled",
        {"reconciliation_id": reconciliation_id, "reason": reason},
    )
    return updated


def auto_reconcile(tenant_id: int, *, invoice_id: str) -> dict:
    """Автоматически подобрать и привязать подходящий платёж к инвойсу."""
    _validate_tenant(tenant_id)

    # Find invoice
    invoices = _get_invoice_rows(tenant_id)
    invoice = next(
        (i for i in invoices if str(i.get("id", "")) == str(invoice_id)),
        None,
    )
    if invoice is None:
        raise LookupError(f"Invoice {invoice_id} not found")

    student_id = invoice.get("student_id") or invoice.get("payer_id")

    # Find already-reconciled payment IDs (active)
    existing_recs = list_entities_for_tenant("payment_reconciliations", tenant_id=tenant_id)
    reconciled_payment_ids = {
        str(r.get("payment_id", ""))
        for r in existing_recs
        if r.get("status") == "active"
    }

    # Find COMPLETED payment for the same student_id not yet reconciled
    payments = _get_payment_rows(tenant_id)
    candidate = next(
        (
            p
            for p in payments
            if p.get("status") == "COMPLETED"
            and str(p.get("id", "")) not in reconciled_payment_ids
            and (student_id is None or str(p.get("student_id", "")) == str(student_id))
        ),
        None,
    )
    if candidate is None:
        raise ValueError(
            f"No eligible COMPLETED payment found for invoice {invoice_id}"
        )

    rec = reconcile_payment(
        tenant_id,
        payment_id=str(candidate["id"]),
        invoice_id=str(invoice_id),
        notes="auto-reconciled",
    )
    _fire(
        tenant_id,
        "reconciliation.auto_completed",
        {"reconciliation_id": rec["id"], "invoice_id": invoice_id},
    )
    return rec
