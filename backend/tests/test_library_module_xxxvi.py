"""Tests for Phase XXXVI — Library Module service.

14 tests covering:
- issue_book
- return_book (with and without fine)
- reserve_book
- cancel_reservation
- mark_overdue
- calculate_fine
- list helpers
- validation errors
"""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch

# ─── Helpers ──────────────────────────────────────────────────────────────────

TENANT = 42
ITEM_ID = "item-1"
BORROWER_ID = "student-99"
LOAN_ID = "loan-77"


def _item(status: str = "AVAILABLE") -> dict:
    return {"id": ITEM_ID, "title": "Clean Code", "status": status, "tenant_id": TENANT}


def _loan(status: str = "ACTIVE", due_date: str = "2099-12-31T00:00:00+00:00") -> dict:
    return {
        "id": LOAN_ID,
        "item_id": ITEM_ID,
        "borrower_id": BORROWER_ID,
        "issued_at": "2024-01-01T00:00:00+00:00",
        "due_date": due_date,
        "status": status,
        "tenant_id": TENANT,
    }


def _reservation(status: str = "ACTIVE") -> dict:
    return {
        "id": "res-5",
        "item_id": ITEM_ID,
        "borrower_id": BORROWER_ID,
        "reserved_at": "2024-01-01T00:00:00+00:00",
        "status": status,
        "tenant_id": TENANT,
    }


# ─── 1. issue_book — success ──────────────────────────────────────────────────

def test_issue_book_success():
    new_loan = {"id": "loan-new"}
    with (
        patch("app.modules.library.service.list_entities_for_tenant", return_value=[_item("AVAILABLE")]),
        patch("app.modules.library.service.create_entity_for_tenant", return_value=new_loan),
        patch("app.modules.library.service.EventPublisher") as mock_pub,
    ):
        from app.modules.library.service import issue_book
        result = issue_book(TENANT, item_id=ITEM_ID, borrower_id=BORROWER_ID, due_days=14)

    assert result["item_id"] == ITEM_ID
    assert result["borrower_id"] == BORROWER_ID
    assert result["loan_id"] == "loan-new"
    assert "due_date" in result
    mock_pub.return_value.publish_event.assert_called_once()


# ─── 2. issue_book — invalid FSM state ───────────────────────────────────────

def test_issue_book_invalid_state():
    with (
        patch("app.modules.library.service.list_entities_for_tenant", return_value=[_item("OVERDUE")]),
        patch("app.modules.library.service.EventPublisher"),
    ):
        from app.modules.library.service import issue_book
        with pytest.raises(ValueError, match="Invalid library item transition"):
            issue_book(TENANT, item_id=ITEM_ID, borrower_id=BORROWER_ID)


# ─── 3. issue_book — item not found ──────────────────────────────────────────

def test_issue_book_item_not_found():
    with (
        patch("app.modules.library.service.list_entities_for_tenant", return_value=[]),
        patch("app.modules.library.service.EventPublisher"),
    ):
        from app.modules.library.service import issue_book
        with pytest.raises(LookupError, match="not found"):
            issue_book(TENANT, item_id=ITEM_ID, borrower_id=BORROWER_ID)


# ─── 4. issue_book — bad tenant ──────────────────────────────────────────────

def test_issue_book_bad_tenant():
    from app.modules.library.service import issue_book
    with pytest.raises(ValueError, match="tenant_id must be a positive integer"):
        issue_book(0, item_id=ITEM_ID, borrower_id=BORROWER_ID)


# ─── 5. return_book — success no fine ────────────────────────────────────────

def test_return_book_no_fine():
    new_return = {"id": "ret-1"}
    with (
        patch("app.modules.library.service.list_entities_for_tenant", return_value=[_loan()]),
        patch("app.modules.library.service.create_entity_for_tenant", return_value=new_return),
        patch("app.modules.library.service.EventPublisher") as mock_pub,
    ):
        from app.modules.library.service import return_book
        result = return_book(TENANT, item_id=ITEM_ID, borrower_id=BORROWER_ID)

    assert result["item_id"] == ITEM_ID
    assert result["fine_amount"] == 0.0
    mock_pub.return_value.publish_event.assert_called_once()


# ─── 6. return_book — fine applied for overdue ───────────────────────────────

def test_return_book_with_fine():
    past_due = "2020-01-01T00:00:00+00:00"
    new_return = {"id": "ret-2"}
    with (
        patch("app.modules.library.service.list_entities_for_tenant", return_value=[_loan(due_date=past_due)]),
        patch("app.modules.library.service.create_entity_for_tenant", return_value=new_return),
        patch("app.modules.library.service.EventPublisher"),
    ):
        from app.modules.library.service import return_book
        result = return_book(TENANT, item_id=ITEM_ID, borrower_id=BORROWER_ID)

    assert result["fine_amount"] > 0


# ─── 7. return_book — no active loan ─────────────────────────────────────────

def test_return_book_no_loan():
    with (
        patch("app.modules.library.service.list_entities_for_tenant", return_value=[]),
        patch("app.modules.library.service.EventPublisher"),
    ):
        from app.modules.library.service import return_book
        with pytest.raises(LookupError, match="No active loan"):
            return_book(TENANT, item_id=ITEM_ID, borrower_id=BORROWER_ID)


# ─── 8. reserve_book — success ───────────────────────────────────────────────

def test_reserve_book_success():
    new_res = {"id": "res-new"}
    with (
        patch("app.modules.library.service.list_entities_for_tenant", return_value=[_item("AVAILABLE")]),
        patch("app.modules.library.service.create_entity_for_tenant", return_value=new_res),
        patch("app.modules.library.service.EventPublisher") as mock_pub,
    ):
        from app.modules.library.service import reserve_book
        result = reserve_book(TENANT, item_id=ITEM_ID, borrower_id=BORROWER_ID)

    assert result["item_id"] == ITEM_ID
    assert result["reservation_id"] == "res-new"
    mock_pub.return_value.publish_event.assert_called_once()


# ─── 9. reserve_book — item already checked out ──────────────────────────────

def test_reserve_book_invalid_state():
    with (
        patch("app.modules.library.service.list_entities_for_tenant", return_value=[_item("CHECKED_OUT")]),
        patch("app.modules.library.service.EventPublisher"),
    ):
        from app.modules.library.service import reserve_book
        with pytest.raises(ValueError, match="Invalid library item transition"):
            reserve_book(TENANT, item_id=ITEM_ID, borrower_id=BORROWER_ID)


# ─── 10. cancel_reservation — success ────────────────────────────────────────

def test_cancel_reservation_success():
    with (
        patch("app.modules.library.service.list_entities_for_tenant", return_value=[_reservation()]),
        patch("app.modules.library.service.EventPublisher") as mock_pub,
    ):
        from app.modules.library.service import cancel_reservation
        result = cancel_reservation(TENANT, item_id=ITEM_ID, borrower_id=BORROWER_ID)

    assert result["status"] == "CANCELLED"
    mock_pub.return_value.publish_event.assert_called_once()


# ─── 11. mark_overdue — success ──────────────────────────────────────────────

def test_mark_overdue_success():
    new_rec = {"id": "od-1"}
    with (
        patch("app.modules.library.service.list_entities_for_tenant", return_value=[_item("CHECKED_OUT")]),
        patch("app.modules.library.service.create_entity_for_tenant", return_value=new_rec),
        patch("app.modules.library.service.EventPublisher") as mock_pub,
    ):
        from app.modules.library.service import mark_overdue
        result = mark_overdue(TENANT, item_id=ITEM_ID)

    assert result["status"] == "OVERDUE"
    mock_pub.return_value.publish_event.assert_called_once()


# ─── 12. mark_overdue — invalid transition ───────────────────────────────────

def test_mark_overdue_invalid_state():
    with (
        patch("app.modules.library.service.list_entities_for_tenant", return_value=[_item("AVAILABLE")]),
        patch("app.modules.library.service.EventPublisher"),
    ):
        from app.modules.library.service import mark_overdue
        with pytest.raises(ValueError, match="Invalid library item transition"):
            mark_overdue(TENANT, item_id=ITEM_ID)


# ─── 13. calculate_fine — no overdue ─────────────────────────────────────────

def test_calculate_fine_no_overdue():
    fine_rec = {"id": "fine-1"}
    loan = _loan(due_date="2099-12-31T00:00:00+00:00")
    with (
        patch("app.modules.library.service.list_entities_for_tenant", return_value=[loan]),
        patch("app.modules.library.service.create_entity_for_tenant", return_value=fine_rec),
        patch("app.modules.library.service.EventPublisher"),
    ):
        from app.modules.library.service import calculate_fine
        result = calculate_fine(TENANT, loan_id=LOAN_ID)

    assert result["fine_amount"] == 0.0
    assert result["overdue_days"] == 0


# ─── 14. calculate_fine — overdue ────────────────────────────────────────────

def test_calculate_fine_overdue():
    fine_rec = {"id": "fine-2"}
    loan = _loan(due_date="2020-01-01T00:00:00+00:00")
    with (
        patch("app.modules.library.service.list_entities_for_tenant", return_value=[loan]),
        patch("app.modules.library.service.create_entity_for_tenant", return_value=fine_rec),
        patch("app.modules.library.service.EventPublisher"),
    ):
        from app.modules.library.service import calculate_fine
        result = calculate_fine(TENANT, loan_id=LOAN_ID)

    assert result["fine_amount"] > 0
    assert result["overdue_days"] > 0
    assert result["fine_record_id"] == "fine-2"
