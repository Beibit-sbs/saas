"""Online Payments module service — XXXIX.

FSM платежа:
  PENDING → PROCESSING → COMPLETED
                       → FAILED
  COMPLETED → REFUNDED

Операции:
  create_payment(tenant_id, *, student_id, amount, currency, method, description)
  process_payment(tenant_id, *, payment_id)
  complete_payment(tenant_id, *, payment_id, transaction_ref)
  fail_payment(tenant_id, *, payment_id, reason)
  refund_payment(tenant_id, *, payment_id, reason)
  get_payment(tenant_id, *, payment_id)
  list_payments(tenant_id, *, student_id=None, status=None)
  check_failure_pattern(tenant_id, *, student_id)

Константы:
  FAILURE_PATTERN_THRESHOLD = 3  (повторные отказы)
  SUPPORTED_METHODS = {"KASPI", "HALYK", "CARD", "BANK_TRANSFER"}

События:
  payment.initiated
  payment.completed
  payment.failed
  payment.refunded
  payment.failure_pattern
"""
from __future__ import annotations

from datetime import UTC, datetime

from app.modules.university_core.tenant_entity_api import (
    create_entity_for_tenant,
    list_entities_for_tenant,
)
from app.platform.events.publisher import EventPublisher

# ─── constants ────────────────────────────────────────────────────────────────

PAYMENT_STATES = frozenset({"PENDING", "PROCESSING", "COMPLETED", "FAILED", "REFUNDED"})
SUPPORTED_METHODS = frozenset({"KASPI", "HALYK", "CARD", "BANK_TRANSFER"})
FAILURE_PATTERN_THRESHOLD: int = 3

_PAYMENT_FSM: dict[str, list[str]] = {
    "PENDING": ["PROCESSING"],
    "PROCESSING": ["COMPLETED", "FAILED"],
    "COMPLETED": ["REFUNDED"],
}


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


def _get_payment(tenant_id: int, payment_id: str) -> dict:
    payments = list_entities_for_tenant("payment_orders", tenant_id=tenant_id)
    payment = next((p for p in payments if str(p.get("id", "")) == str(payment_id)), None)
    if payment is None:
        raise LookupError(f"Payment {payment_id} not found for tenant {tenant_id}")
    return payment


def _assert_transition(payment: dict, target: str) -> None:
    current = payment.get("status", "")
    allowed = _PAYMENT_FSM.get(current, [])
    if target not in allowed:
        raise ValueError(
            f"Cannot transition payment from '{current}' to '{target}'. "
            f"Allowed transitions: {allowed}"
        )


# ─── create_payment ───────────────────────────────────────────────────────────

def create_payment(
    tenant_id: int,
    *,
    student_id: str,
    amount: float,
    currency: str = "KZT",
    method: str,
    description: str = "",
) -> dict:
    _validate_tenant(tenant_id)
    if not student_id:
        raise ValueError("student_id is required")
    if amount <= 0:
        raise ValueError("amount must be positive")
    if method not in SUPPORTED_METHODS:
        raise ValueError(f"Invalid payment method '{method}'. Supported: {sorted(SUPPORTED_METHODS)}")

    payment = create_entity_for_tenant(
        "payment_orders",
        tenant_id=tenant_id,
        data={
            "student_id": student_id,
            "amount": amount,
            "currency": currency,
            "method": method,
            "description": description,
            "status": "PENDING",
            "created_at": _utc_now().isoformat(),
            "tenant_id": tenant_id,
        },
    )

    _fire(tenant_id, "payment.initiated", {
        "payment_id": payment.get("id"),
        "student_id": student_id,
        "amount": amount,
        "currency": currency,
        "method": method,
        "tenant_id": tenant_id,
    })

    return {"payment_id": payment.get("id"), "status": "PENDING", "amount": amount, "method": method}


# ─── process_payment ──────────────────────────────────────────────────────────

def process_payment(tenant_id: int, *, payment_id: str) -> dict:
    _validate_tenant(tenant_id)
    payment = _get_payment(tenant_id, payment_id)
    _assert_transition(payment, "PROCESSING")

    proc = create_entity_for_tenant(
        "payment_processing_log",
        tenant_id=tenant_id,
        data={
            "payment_id": payment_id,
            "started_at": _utc_now().isoformat(),
            "tenant_id": tenant_id,
        },
    )

    return {"payment_id": payment_id, "status": "PROCESSING", "log_id": proc.get("id")}


# ─── complete_payment ─────────────────────────────────────────────────────────

def complete_payment(
    tenant_id: int,
    *,
    payment_id: str,
    transaction_ref: str,
) -> dict:
    _validate_tenant(tenant_id)
    if not transaction_ref:
        raise ValueError("transaction_ref is required")
    payment = _get_payment(tenant_id, payment_id)
    _assert_transition(payment, "COMPLETED")

    txn = create_entity_for_tenant(
        "payment_transactions",
        tenant_id=tenant_id,
        data={
            "payment_id": payment_id,
            "student_id": payment.get("student_id"),
            "amount": payment.get("amount"),
            "currency": payment.get("currency"),
            "transaction_ref": transaction_ref,
            "completed_at": _utc_now().isoformat(),
            "tenant_id": tenant_id,
        },
    )

    _fire(tenant_id, "payment.completed", {
        "payment_id": payment_id,
        "student_id": payment.get("student_id"),
        "amount": payment.get("amount"),
        "transaction_id": txn.get("id"),
        "transaction_ref": transaction_ref,
        "tenant_id": tenant_id,
    })

    return {"payment_id": payment_id, "status": "COMPLETED", "transaction_id": txn.get("id")}


# ─── fail_payment ─────────────────────────────────────────────────────────────

def fail_payment(
    tenant_id: int,
    *,
    payment_id: str,
    reason: str,
) -> dict:
    _validate_tenant(tenant_id)
    if not reason:
        raise ValueError("reason is required")
    payment = _get_payment(tenant_id, payment_id)
    _assert_transition(payment, "FAILED")

    failure = create_entity_for_tenant(
        "payment_failures",
        tenant_id=tenant_id,
        data={
            "payment_id": payment_id,
            "student_id": payment.get("student_id"),
            "reason": reason,
            "failed_at": _utc_now().isoformat(),
            "tenant_id": tenant_id,
        },
    )

    _fire(tenant_id, "payment.failed", {
        "payment_id": payment_id,
        "student_id": payment.get("student_id"),
        "reason": reason,
        "failure_id": failure.get("id"),
        "tenant_id": tenant_id,
    })

    return {"payment_id": payment_id, "status": "FAILED", "failure_id": failure.get("id")}


# ─── refund_payment ───────────────────────────────────────────────────────────

def refund_payment(
    tenant_id: int,
    *,
    payment_id: str,
    reason: str,
) -> dict:
    _validate_tenant(tenant_id)
    if not reason:
        raise ValueError("reason is required")
    payment = _get_payment(tenant_id, payment_id)
    _assert_transition(payment, "REFUNDED")

    refund = create_entity_for_tenant(
        "payment_refunds",
        tenant_id=tenant_id,
        data={
            "payment_id": payment_id,
            "student_id": payment.get("student_id"),
            "amount": payment.get("amount"),
            "reason": reason,
            "refunded_at": _utc_now().isoformat(),
            "tenant_id": tenant_id,
        },
    )

    _fire(tenant_id, "payment.refunded", {
        "payment_id": payment_id,
        "student_id": payment.get("student_id"),
        "amount": payment.get("amount"),
        "refund_id": refund.get("id"),
        "tenant_id": tenant_id,
    })

    return {"payment_id": payment_id, "status": "REFUNDED", "refund_id": refund.get("id")}


# ─── check_failure_pattern ────────────────────────────────────────────────────

def check_failure_pattern(
    tenant_id: int,
    *,
    student_id: str,
) -> dict:
    _validate_tenant(tenant_id)
    if not student_id:
        raise ValueError("student_id is required")

    failures = list_entities_for_tenant("payment_failures", tenant_id=tenant_id)
    student_failures = [f for f in failures if str(f.get("student_id", "")) == str(student_id)]
    failure_count = len(student_failures)

    if failure_count >= FAILURE_PATTERN_THRESHOLD:
        alert = create_entity_for_tenant(
            "payment_failure_alerts",
            tenant_id=tenant_id,
            data={
                "student_id": student_id,
                "failure_count": failure_count,
                "threshold": FAILURE_PATTERN_THRESHOLD,
                "detected_at": _utc_now().isoformat(),
                "tenant_id": tenant_id,
            },
        )

        _fire(tenant_id, "payment.failure_pattern", {
            "student_id": student_id,
            "failure_count": failure_count,
            "threshold": FAILURE_PATTERN_THRESHOLD,
            "alert_id": alert.get("id"),
            "tenant_id": tenant_id,
        })

        return {
            "student_id": student_id,
            "failure_count": failure_count,
            "pattern_detected": True,
            "alert_id": alert.get("id"),
            "event_fired": True,
        }

    return {
        "student_id": student_id,
        "failure_count": failure_count,
        "pattern_detected": False,
        "event_fired": False,
    }


# ─── list helpers ─────────────────────────────────────────────────────────────

def get_payment(tenant_id: int, *, payment_id: str) -> dict:
    _validate_tenant(tenant_id)
    return _get_payment(tenant_id, payment_id)


def list_payments(
    tenant_id: int,
    *,
    student_id: str | None = None,
    status: str | None = None,
) -> list[dict]:
    _validate_tenant(tenant_id)
    rows = list_entities_for_tenant("payment_orders", tenant_id=tenant_id)
    if student_id:
        rows = [r for r in rows if str(r.get("student_id", "")) == str(student_id)]
    if status:
        rows = [r for r in rows if r.get("status") == status]
    return rows
