"""Library module service — XXXVI.

FSM для LibraryItem:
  AVAILABLE → RESERVED → CHECKED_OUT → OVERDUE → RETURNED → AVAILABLE

Операции:
  issue_book(tenant_id, item_id, borrower_id, due_days)
  return_book(tenant_id, item_id, borrower_id)
  reserve_book(tenant_id, item_id, borrower_id)
  cancel_reservation(tenant_id, item_id, borrower_id)
  mark_overdue(tenant_id, item_id)
  calculate_fine(tenant_id, loan_id)

События:
  library.book.issued
  library.book.returned
  library.book.reserved
  library.reservation.cancelled
  library.item.overdue
  library.fine.calculated
"""
from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app.modules.university_core.tenant_entity_api import (
    create_entity_for_tenant,
    list_entities_for_tenant,
    update_entity_for_tenant,
)
from app.platform.events.publisher import EventPublisher

# ─── constants ────────────────────────────────────────────────────────────────

ITEM_STATES = frozenset({"AVAILABLE", "RESERVED", "CHECKED_OUT", "OVERDUE", "RETURNED"})

# Fine per day overdue (in tenge)
FINE_RATE_PER_DAY: float = 50.0

_ITEM_FSM: dict[str, set[str]] = {
    "AVAILABLE":   {"RESERVED", "CHECKED_OUT"},
    "RESERVED":    {"CHECKED_OUT", "AVAILABLE"},   # cancel → AVAILABLE
    "CHECKED_OUT": {"OVERDUE", "RETURNED"},
    "OVERDUE":     {"RETURNED"},
    "RETURNED":    {"AVAILABLE"},
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


def _validate_fsm(current_state: str, target_state: str) -> None:
    allowed = _ITEM_FSM.get(current_state, set())
    if target_state not in allowed:
        raise ValueError(
            f"Invalid library item transition: {current_state} → {target_state}"
        )


# ─── issue_book ──────────────────────────────────────────────────────────────

def issue_book(
    tenant_id: int,
    *,
    item_id: str,
    borrower_id: str,
    due_days: int = 14,
) -> dict:
    """Check out a library item to a borrower."""
    _validate_tenant(tenant_id)
    if not item_id:
        raise ValueError("item_id is required")
    if not borrower_id:
        raise ValueError("borrower_id is required")

    # Load item
    items = list_entities_for_tenant("library_items", tenant_id=tenant_id)
    item = next((i for i in items if str(i.get("id", "")) == str(item_id)), None)
    if item is None:
        raise LookupError(f"Library item {item_id} not found for tenant {tenant_id}")

    current_state = item.get("status", "AVAILABLE")
    _validate_fsm(current_state, "CHECKED_OUT")

    due_date = (_utc_now() + timedelta(days=due_days)).isoformat()

    # Create loan record
    loan = create_entity_for_tenant(
        "library_loans",
        tenant_id=tenant_id,
        data={
            "item_id": item_id,
            "borrower_id": borrower_id,
            "issued_at": _utc_now().isoformat(),
            "due_date": due_date,
            "status": "ACTIVE",
            "tenant_id": tenant_id,
        },
    )

    _fire(tenant_id, "library.book.issued", {
        "item_id": item_id,
        "borrower_id": borrower_id,
        "due_date": due_date,
        "loan_id": loan.get("id"),
        "tenant_id": tenant_id,
    })

    return {"item_id": item_id, "borrower_id": borrower_id, "due_date": due_date, "loan_id": loan.get("id")}


# ─── return_book ─────────────────────────────────────────────────────────────

def return_book(
    tenant_id: int,
    *,
    item_id: str,
    borrower_id: str,
) -> dict:
    """Return a checked-out or overdue library item."""
    _validate_tenant(tenant_id)
    if not item_id:
        raise ValueError("item_id is required")

    # Find active loan
    loans = list_entities_for_tenant("library_loans", tenant_id=tenant_id)
    loan = next(
        (
            ln for ln in loans
            if str(ln.get("item_id", "")) == str(item_id)
            and str(ln.get("borrower_id", "")) == str(borrower_id)
            and ln.get("status") == "ACTIVE"
        ),
        None,
    )
    if loan is None:
        raise LookupError(f"No active loan for item {item_id} / borrower {borrower_id}")

    returned_at = _utc_now().isoformat()
    fine_amount = 0.0

    due_date_str = loan.get("due_date", "")
    if due_date_str:
        try:
            due_dt = datetime.fromisoformat(due_date_str)
            now = _utc_now()
            if due_dt.tzinfo is None:
                due_dt = due_dt.replace(tzinfo=UTC)
            if now > due_dt:
                overdue_days = (now - due_dt).days
                fine_amount = overdue_days * FINE_RATE_PER_DAY
        except ValueError:
            pass

    # Create return record
    ret = create_entity_for_tenant(
        "library_returns",
        tenant_id=tenant_id,
        data={
            "loan_id": loan.get("id"),
            "item_id": item_id,
            "borrower_id": borrower_id,
            "returned_at": returned_at,
            "fine_amount": fine_amount,
            "tenant_id": tenant_id,
        },
    )

    _fire(tenant_id, "library.book.returned", {
        "item_id": item_id,
        "borrower_id": borrower_id,
        "loan_id": loan.get("id"),
        "fine_amount": fine_amount,
        "tenant_id": tenant_id,
    })

    return {
        "item_id": item_id,
        "borrower_id": borrower_id,
        "returned_at": returned_at,
        "fine_amount": fine_amount,
        "return_id": ret.get("id"),
    }


# ─── reserve_book ────────────────────────────────────────────────────────────

def reserve_book(
    tenant_id: int,
    *,
    item_id: str,
    borrower_id: str,
) -> dict:
    """Reserve an available library item."""
    _validate_tenant(tenant_id)
    if not item_id:
        raise ValueError("item_id is required")
    if not borrower_id:
        raise ValueError("borrower_id is required")

    items = list_entities_for_tenant("library_items", tenant_id=tenant_id)
    item = next((i for i in items if str(i.get("id", "")) == str(item_id)), None)
    if item is None:
        raise LookupError(f"Library item {item_id} not found for tenant {tenant_id}")

    _validate_fsm(item.get("status", "AVAILABLE"), "RESERVED")

    reservation = create_entity_for_tenant(
        "library_reservations",
        tenant_id=tenant_id,
        data={
            "item_id": item_id,
            "borrower_id": borrower_id,
            "reserved_at": _utc_now().isoformat(),
            "status": "ACTIVE",
            "tenant_id": tenant_id,
        },
    )

    _fire(tenant_id, "library.book.reserved", {
        "item_id": item_id,
        "borrower_id": borrower_id,
        "reservation_id": reservation.get("id"),
        "tenant_id": tenant_id,
    })

    return {
        "item_id": item_id,
        "borrower_id": borrower_id,
        "reservation_id": reservation.get("id"),
    }


# ─── cancel_reservation ──────────────────────────────────────────────────────

def cancel_reservation(
    tenant_id: int,
    *,
    item_id: str,
    borrower_id: str,
) -> dict:
    """Cancel an active reservation."""
    _validate_tenant(tenant_id)
    if not item_id:
        raise ValueError("item_id is required")

    reservations = list_entities_for_tenant("library_reservations", tenant_id=tenant_id)
    reservation = next(
        (
            r for r in reservations
            if str(r.get("item_id", "")) == str(item_id)
            and str(r.get("borrower_id", "")) == str(borrower_id)
            and r.get("status") == "ACTIVE"
        ),
        None,
    )
    if reservation is None:
        raise LookupError(f"No active reservation for item {item_id} / borrower {borrower_id}")

    _fire(tenant_id, "library.reservation.cancelled", {
        "item_id": item_id,
        "borrower_id": borrower_id,
        "reservation_id": reservation.get("id"),
        "tenant_id": tenant_id,
    })

    return {"item_id": item_id, "reservation_id": reservation.get("id"), "status": "CANCELLED"}


# ─── mark_overdue ────────────────────────────────────────────────────────────

def mark_overdue(tenant_id: int, *, item_id: str) -> dict:
    """Mark a checked-out item as OVERDUE."""
    _validate_tenant(tenant_id)
    if not item_id:
        raise ValueError("item_id is required")

    items = list_entities_for_tenant("library_items", tenant_id=tenant_id)
    item = next((i for i in items if str(i.get("id", "")) == str(item_id)), None)
    if item is None:
        raise LookupError(f"Library item {item_id} not found for tenant {tenant_id}")

    current = item.get("status", "AVAILABLE")
    _validate_fsm(current, "OVERDUE")

    overdue_record = create_entity_for_tenant(
        "library_overdue_records",
        tenant_id=tenant_id,
        data={
            "item_id": item_id,
            "marked_at": _utc_now().isoformat(),
            "tenant_id": tenant_id,
        },
    )

    _fire(tenant_id, "library.item.overdue", {
        "item_id": item_id,
        "record_id": overdue_record.get("id"),
        "tenant_id": tenant_id,
    })

    return {"item_id": item_id, "status": "OVERDUE", "record_id": overdue_record.get("id")}


# ─── calculate_fine ──────────────────────────────────────────────────────────

def calculate_fine(tenant_id: int, *, loan_id: str) -> dict:
    """Calculate fine for an overdue loan."""
    _validate_tenant(tenant_id)
    if not loan_id:
        raise ValueError("loan_id is required")

    loans = list_entities_for_tenant("library_loans", tenant_id=tenant_id)
    loan = next((ln for ln in loans if str(ln.get("id", "")) == str(loan_id)), None)
    if loan is None:
        raise LookupError(f"Loan {loan_id} not found for tenant {tenant_id}")

    due_date_str = loan.get("due_date", "")
    fine_amount = 0.0
    overdue_days = 0

    if due_date_str:
        try:
            due_dt = datetime.fromisoformat(due_date_str)
            now = _utc_now()
            if due_dt.tzinfo is None:
                due_dt = due_dt.replace(tzinfo=UTC)
            if now > due_dt:
                overdue_days = (now - due_dt).days
                fine_amount = overdue_days * FINE_RATE_PER_DAY
        except ValueError:
            pass

    fine_record = create_entity_for_tenant(
        "library_fines",
        tenant_id=tenant_id,
        data={
            "loan_id": loan_id,
            "borrower_id": loan.get("borrower_id"),
            "fine_amount": fine_amount,
            "overdue_days": overdue_days,
            "calculated_at": _utc_now().isoformat(),
            "tenant_id": tenant_id,
        },
    )

    _fire(tenant_id, "library.fine.calculated", {
        "loan_id": loan_id,
        "fine_amount": fine_amount,
        "overdue_days": overdue_days,
        "fine_record_id": fine_record.get("id"),
        "tenant_id": tenant_id,
    })

    return {
        "loan_id": loan_id,
        "fine_amount": fine_amount,
        "overdue_days": overdue_days,
        "fine_record_id": fine_record.get("id"),
    }


# ─── list helpers ────────────────────────────────────────────────────────────

def list_loans(tenant_id: int, *, borrower_id: str | None = None) -> list[dict]:
    _validate_tenant(tenant_id)
    rows = list_entities_for_tenant("library_loans", tenant_id=tenant_id)
    if borrower_id:
        rows = [r for r in rows if str(r.get("borrower_id", "")) == str(borrower_id)]
    return rows


def list_reservations(tenant_id: int, *, item_id: str | None = None) -> list[dict]:
    _validate_tenant(tenant_id)
    rows = list_entities_for_tenant("library_reservations", tenant_id=tenant_id)
    if item_id:
        rows = [r for r in rows if str(r.get("item_id", "")) == str(item_id)]
    return rows
