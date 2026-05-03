"""Phase LXV — Invoice Management Service tests (22 tests)."""
from __future__ import annotations

from unittest.mock import patch

import pytest

MODULE = "app.modules.invoices.service"


def _invoice(
    id: int = 1,
    invoice_number: str = "INV-5-ABCD1234",
    status: str = "draft",
    currency_code: str = "KZT",
    total_cents: int = 0,
    due_date: str = "2026-06-30",
    issued_at=None,
    paid_at=None,
    voided_at=None,
):
    return {
        "id": id,
        "invoice_number": invoice_number,
        "status": status,
        "currency_code": currency_code,
        "total_cents": total_cents,
        "due_date": due_date,
        "notes": "",
        "issued_at": issued_at,
        "paid_at": paid_at,
        "voided_at": voided_at,
    }


def _item(
    id: int = 10,
    invoice_id: int = 1,
    description: str = "Tuition Fee",
    quantity: int = 1,
    unit_price_cents: int = 50000,
    total_cents: int = 50000,
):
    return {
        "id": id,
        "invoice_id": invoice_id,
        "description": description,
        "quantity": quantity,
        "unit_price_cents": unit_price_cents,
        "total_cents": total_cents,
    }


def _payment(
    id: int = 20,
    invoice_id: int = 1,
    amount_cents: int = 50000,
    method: str = "kaspi",
    paid_at: str = "2026-05-03T10:00:00",
    reference: str = "TXN-001",
):
    return {
        "id": id,
        "invoice_id": invoice_id,
        "amount_cents": amount_cents,
        "method": method,
        "paid_at": paid_at,
        "reference": reference,
    }


# ─── create_invoice ─────────────────────────────────────────────────────────

def test_create_invoice_success():
    with (
        patch(f"{MODULE}.create_entity_for_tenant", return_value=_invoice()) as mock_create,
        patch(f"{MODULE}.EventPublisher"),
    ):
        from app.modules.invoices import service

        result = service.create_invoice(5, "KZT", "2026-06-30")

    assert result.invoice_id == 1
    assert result.status == "draft"
    assert result.currency_code == "KZT"
    mock_create.assert_called_once()


def test_create_invoice_invalid_tenant_id():
    from app.modules.invoices.service import InvoiceError, create_invoice

    with pytest.raises(InvoiceError, match="tenant_id"):
        create_invoice(0, "KZT", "2026-06-30")


def test_create_invoice_invalid_currency_code():
    from app.modules.invoices.service import InvoiceError, create_invoice

    with pytest.raises(InvoiceError, match="currency_code"):
        create_invoice(5, "XYZ", "2026-06-30")


def test_create_invoice_invalid_due_date():
    from app.modules.invoices.service import InvoiceError, create_invoice

    with pytest.raises(InvoiceError, match="due_date"):
        create_invoice(5, "KZT", "not-a-date")


# ─── add_item ───────────────────────────────────────────────────────────────

def test_add_item_to_invoice():
    draft = _invoice(status="draft")
    with (
        patch(f"{MODULE}.list_entities_for_tenant", return_value=[draft]),
        patch(f"{MODULE}.create_entity_for_tenant", return_value=_item()),
    ):
        from app.modules.invoices import service

        result = service.add_item(1, 5, "Tuition Fee", 1, 50000)

    assert result.total_cents == 50000
    assert result.description == "Tuition Fee"


def test_add_item_invalid_quantity():
    draft = _invoice(status="draft")
    with patch(f"{MODULE}.list_entities_for_tenant", return_value=[draft]):
        from app.modules.invoices.service import InvoiceError, add_item

        with pytest.raises(InvoiceError, match="quantity"):
            add_item(1, 5, "Fee", 0, 1000)


def test_add_item_invalid_unit_price():
    draft = _invoice(status="draft")
    with patch(f"{MODULE}.list_entities_for_tenant", return_value=[draft]):
        from app.modules.invoices.service import InvoiceError, add_item

        with pytest.raises(InvoiceError, match="unit_price_cents"):
            add_item(1, 5, "Fee", 1, -1)


def test_add_item_to_finalized_raises():
    finalized = _invoice(status="finalized")
    with patch(f"{MODULE}.list_entities_for_tenant", return_value=[finalized]):
        from app.modules.invoices.service import InvoiceError, add_item

        with pytest.raises(InvoiceError, match="draft"):
            add_item(1, 5, "Fee", 1, 1000)


# ─── finalize_invoice ────────────────────────────────────────────────────────

def test_finalize_invoice_computes_total():
    draft = _invoice(id=1, status="draft")
    items = [_item(invoice_id=1, total_cents=50000), _item(id=11, invoice_id=1, total_cents=30000)]
    updated = _invoice(id=1, status="finalized", total_cents=80000, issued_at="2026-05-03T00:00:00")
    with (
        patch(f"{MODULE}.list_entities_for_tenant", side_effect=[[draft], items]),
        patch(f"{MODULE}.update_entity_for_tenant", return_value=updated),
        patch(f"{MODULE}.EventPublisher") as mock_pub,
    ):
        from app.modules.invoices import service

        result = service.finalize_invoice(1, 5)

    assert result.status == "finalized"
    assert result.total_cents == 80000
    mock_pub.publish.assert_called_once()


def test_finalize_invoice_no_items_raises():
    draft = _invoice(id=1, status="draft")
    with (
        patch(f"{MODULE}.list_entities_for_tenant", side_effect=[[draft], []]),
    ):
        from app.modules.invoices.service import InvoiceError, finalize_invoice

        with pytest.raises(InvoiceError, match="no items"):
            finalize_invoice(1, 5)


def test_finalize_already_finalized_raises():
    finalized = _invoice(id=1, status="finalized")
    with patch(f"{MODULE}.list_entities_for_tenant", return_value=[finalized]):
        from app.modules.invoices.service import InvoiceError, finalize_invoice

        with pytest.raises(InvoiceError, match="draft"):
            finalize_invoice(1, 5)


# ─── send_invoice ─────────────────────────────────────────────────────────────

def test_send_invoice_sets_status():
    fin = _invoice(id=1, status="finalized")
    sent = _invoice(id=1, status="sent")
    with (
        patch(f"{MODULE}.list_entities_for_tenant", return_value=[fin]),
        patch(f"{MODULE}.update_entity_for_tenant", return_value=sent),
        patch(f"{MODULE}.EventPublisher"),
    ):
        from app.modules.invoices import service

        result = service.send_invoice(1, 5)

    assert result.status == "sent"


def test_send_non_finalized_raises():
    draft = _invoice(id=1, status="draft")
    with patch(f"{MODULE}.list_entities_for_tenant", return_value=[draft]):
        from app.modules.invoices.service import InvoiceError, send_invoice

        with pytest.raises(InvoiceError, match="finalized"):
            send_invoice(1, 5)


# ─── mark_paid ───────────────────────────────────────────────────────────────

def test_mark_paid_creates_payment():
    sent = _invoice(id=1, status="sent")
    with (
        patch(f"{MODULE}.list_entities_for_tenant", return_value=[sent]),
        patch(f"{MODULE}.update_entity_for_tenant", return_value=_invoice(id=1, status="paid")),
        patch(f"{MODULE}.create_entity_for_tenant", return_value=_payment()) as mock_pay,
        patch(f"{MODULE}.EventPublisher"),
    ):
        from app.modules.invoices import service

        result = service.mark_paid(1, 5, 50000, "kaspi", "TXN-001")

    assert result.amount_cents == 50000
    assert result.method == "kaspi"
    mock_pay.assert_called_once()


def test_mark_paid_invalid_method():
    sent = _invoice(id=1, status="sent")
    with patch(f"{MODULE}.list_entities_for_tenant", return_value=[sent]):
        from app.modules.invoices.service import InvoiceError, mark_paid

        with pytest.raises(InvoiceError, match="payment method"):
            mark_paid(1, 5, 50000, "bitcoin")


def test_mark_paid_already_paid_raises():
    paid = _invoice(id=1, status="paid")
    with patch(f"{MODULE}.list_entities_for_tenant", return_value=[paid]):
        from app.modules.invoices.service import InvoiceError, mark_paid

        with pytest.raises(InvoiceError, match="already paid"):
            mark_paid(1, 5, 50000, "card")


# ─── void_invoice ────────────────────────────────────────────────────────────

def test_void_invoice_success():
    sent = _invoice(id=1, status="sent")
    voided = _invoice(id=1, status="void", voided_at="2026-05-03T00:00:00")
    with (
        patch(f"{MODULE}.list_entities_for_tenant", return_value=[sent]),
        patch(f"{MODULE}.update_entity_for_tenant", return_value=voided),
        patch(f"{MODULE}.EventPublisher"),
    ):
        from app.modules.invoices import service

        result = service.void_invoice(1, 5, "Duplicate")

    assert result.status == "void"


def test_void_paid_invoice_raises():
    paid = _invoice(id=1, status="paid")
    with patch(f"{MODULE}.list_entities_for_tenant", return_value=[paid]):
        from app.modules.invoices.service import InvoiceError, void_invoice

        with pytest.raises(InvoiceError, match="paid"):
            void_invoice(1, 5)


# ─── list_invoices ───────────────────────────────────────────────────────────

def test_list_invoices_filters_by_tenant():
    invoices = [_invoice(id=1), _invoice(id=2, status="paid")]
    with patch(f"{MODULE}.list_entities_for_tenant", return_value=invoices):
        from app.modules.invoices import service

        result = service.list_invoices(5)

    assert len(result) == 2


def test_list_invoices_filters_by_status():
    invoices = [_invoice(id=1, status="draft"), _invoice(id=2, status="paid")]
    with patch(f"{MODULE}.list_entities_for_tenant", return_value=invoices):
        from app.modules.invoices import service

        result = service.list_invoices(5, status="paid")

    assert len(result) == 1
    assert result[0].status == "paid"


def test_get_invoice_not_found():
    with patch(f"{MODULE}.list_entities_for_tenant", return_value=[]):
        from app.modules.invoices.service import InvoiceError, get_invoice

        with pytest.raises(InvoiceError, match="not found"):
            get_invoice(999, 5)


def test_invoice_event_published_on_finalize():
    draft = _invoice(id=1, status="draft")
    items = [_item(invoice_id=1, total_cents=20000)]
    updated = _invoice(id=1, status="finalized", total_cents=20000, issued_at="2026-05-03")
    with (
        patch(f"{MODULE}.list_entities_for_tenant", side_effect=[[draft], items]),
        patch(f"{MODULE}.update_entity_for_tenant", return_value=updated),
        patch(f"{MODULE}.EventPublisher") as mock_pub,
    ):
        from app.modules.invoices import service

        service.finalize_invoice(1, 5)

    mock_pub.publish.assert_called_once_with(
        tenant_id=5,
        event_type="invoice.finalized",
        payload={"invoice_id": 1, "total_cents": 20000},
    )
