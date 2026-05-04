"""Phase LXVI — Invoice Management Router tests (20 tests)."""
from __future__ import annotations

from dataclasses import asdict
from unittest.mock import patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.modules.invoices.router import router
from app.modules.invoices.service import Invoice, InvoiceError, InvoiceItem, InvoicePayment

app = FastAPI()
app.include_router(router)
# A-009 added router-level permission_dependency — override in unit tests.
app.dependency_overrides = {dep.dependency: lambda: None for dep in router.dependencies}
client = TestClient(app)

MODULE = "app.modules.invoices.router"


def _invoice(
    id: int = 1,
    tenant_id: int = 5,
    invoice_number: str = "INV-5-ABCD1234",
    status: str = "draft",
    currency_code: str = "KZT",
    total_cents: int = 0,
    due_date: str = "2026-06-30",
    issued_at=None,
    paid_at=None,
    voided_at=None,
) -> Invoice:
    return Invoice(
        invoice_id=id,
        tenant_id=tenant_id,
        invoice_number=invoice_number,
        status=status,
        currency_code=currency_code,
        total_cents=total_cents,
        due_date=due_date,
        issued_at=issued_at,
        paid_at=paid_at,
        voided_at=voided_at,
    )


def _item(id: int = 10, invoice_id: int = 1) -> InvoiceItem:
    return InvoiceItem(
        id=id,
        invoice_id=invoice_id,
        description="Tuition Fee",
        quantity=1,
        unit_price_cents=50000,
        total_cents=50000,
    )


def _payment(id: int = 20, invoice_id: int = 1) -> InvoicePayment:
    return InvoicePayment(
        payment_id=id,
        invoice_id=invoice_id,
        amount_cents=50000,
        method="kaspi",
        paid_at="2026-05-03T10:00:00",
        reference="TXN-001",
    )


# ─── POST /api/invoices ───────────────────────────────────────────────────────

def test_create_invoice_success():
    with patch(f"{MODULE}.create_invoice", return_value=_invoice()) as mock:
        response = client.post("/api/invoices", json={
            "tenant_id": 5, "currency_code": "KZT", "due_date": "2026-06-30"
        })
    assert response.status_code == 200
    assert response.json()["invoice_id"] == 1
    assert response.json()["status"] == "draft"
    mock.assert_called_once()


def test_create_invoice_invalid_tenant_id():
    response = client.post("/api/invoices", json={
        "tenant_id": 0, "currency_code": "KZT", "due_date": "2026-06-30"
    })
    assert response.status_code == 422


def test_create_invoice_service_error():
    with patch(f"{MODULE}.create_invoice", side_effect=InvoiceError("invalid currency_code")):
        response = client.post("/api/invoices", json={
            "tenant_id": 5, "currency_code": "XYZ", "due_date": "2026-06-30"
        })
    assert response.status_code == 400
    assert "currency_code" in response.json()["detail"]


# ─── GET /api/invoices ────────────────────────────────────────────────────────

def test_list_invoices_returns_all():
    invoices = [_invoice(id=1), _invoice(id=2, status="paid")]
    with patch(f"{MODULE}.list_invoices", return_value=invoices):
        response = client.get("/api/invoices?tenant_id=5")
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_list_invoices_with_status_filter():
    invoices = [_invoice(id=1, status="draft")]
    with patch(f"{MODULE}.list_invoices", return_value=invoices) as mock:
        response = client.get("/api/invoices?tenant_id=5&status=draft")
    assert response.status_code == 200
    mock.assert_called_once_with(tenant_id=5, status="draft")


def test_list_invoices_bad_status_returns_400():
    with patch(f"{MODULE}.list_invoices", side_effect=InvoiceError("invalid status")):
        response = client.get("/api/invoices?tenant_id=5&status=garbage")
    assert response.status_code == 400


# ─── GET /api/invoices/{id} ───────────────────────────────────────────────────

def test_get_invoice_found():
    with patch(f"{MODULE}.get_invoice", return_value=_invoice(id=7)):
        response = client.get("/api/invoices/7?tenant_id=5")
    assert response.status_code == 200
    assert response.json()["invoice_id"] == 7


def test_get_invoice_not_found():
    with patch(f"{MODULE}.get_invoice", side_effect=InvoiceError("invoice not found")):
        response = client.get("/api/invoices/999?tenant_id=5")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


# ─── POST /api/invoices/{id}/items ───────────────────────────────────────────

def test_add_item_success():
    with patch(f"{MODULE}.add_item", return_value=_item()) as mock:
        response = client.post("/api/invoices/1/items", json={
            "tenant_id": 5, "description": "Tuition Fee", "quantity": 1, "unit_price_cents": 50000
        })
    assert response.status_code == 200
    assert response.json()["total_cents"] == 50000
    mock.assert_called_once()


def test_add_item_to_finalized_returns_400():
    with patch(f"{MODULE}.add_item", side_effect=InvoiceError("only draft invoices")):
        response = client.post("/api/invoices/1/items", json={
            "tenant_id": 5, "description": "Fee", "quantity": 1, "unit_price_cents": 1000
        })
    assert response.status_code == 400


# ─── POST /api/invoices/{id}/finalize ────────────────────────────────────────

def test_finalize_invoice_success():
    finalized = _invoice(id=1, status="finalized", total_cents=50000)
    with patch(f"{MODULE}.finalize_invoice", return_value=finalized):
        response = client.post("/api/invoices/1/finalize?tenant_id=5")
    assert response.status_code == 200
    assert response.json()["status"] == "finalized"


def test_finalize_invoice_no_items_400():
    with patch(f"{MODULE}.finalize_invoice", side_effect=InvoiceError("no items")):
        response = client.post("/api/invoices/1/finalize?tenant_id=5")
    assert response.status_code == 400
    assert "no items" in response.json()["detail"]


# ─── POST /api/invoices/{id}/send ────────────────────────────────────────────

def test_send_invoice_success():
    sent = _invoice(id=1, status="sent")
    with patch(f"{MODULE}.send_invoice", return_value=sent):
        response = client.post("/api/invoices/1/send?tenant_id=5")
    assert response.status_code == 200
    assert response.json()["status"] == "sent"


def test_send_non_finalized_400():
    with patch(f"{MODULE}.send_invoice", side_effect=InvoiceError("only finalized")):
        response = client.post("/api/invoices/1/send?tenant_id=5")
    assert response.status_code == 400


# ─── POST /api/invoices/{id}/pay ─────────────────────────────────────────────

def test_mark_paid_success():
    with patch(f"{MODULE}.mark_paid", return_value=_payment()) as mock:
        response = client.post("/api/invoices/1/pay", json={
            "tenant_id": 5, "amount_cents": 50000, "method": "kaspi", "reference": "TXN-001"
        })
    assert response.status_code == 200
    assert response.json()["method"] == "kaspi"
    mock.assert_called_once()


def test_mark_paid_invalid_method_400():
    with patch(f"{MODULE}.mark_paid", side_effect=InvoiceError("payment method")):
        response = client.post("/api/invoices/1/pay", json={
            "tenant_id": 5, "amount_cents": 50000, "method": "bitcoin"
        })
    assert response.status_code == 400


def test_mark_paid_zero_amount_unprocessable():
    response = client.post("/api/invoices/1/pay", json={
        "tenant_id": 5, "amount_cents": 0, "method": "card"
    })
    assert response.status_code == 422


# ─── POST /api/invoices/{id}/void ────────────────────────────────────────────

def test_void_invoice_success():
    voided = _invoice(id=1, status="void")
    with patch(f"{MODULE}.void_invoice", return_value=voided):
        response = client.post("/api/invoices/1/void", json={"tenant_id": 5, "reason": "Duplicate"})
    assert response.status_code == 200
    assert response.json()["status"] == "void"


def test_void_paid_invoice_400():
    with patch(f"{MODULE}.void_invoice", side_effect=InvoiceError("cannot void paid")):
        response = client.post("/api/invoices/1/void", json={"tenant_id": 5})
    assert response.status_code == 400
