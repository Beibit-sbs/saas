"""Phase LXXI — Payment Reconciliation Router tests (20 tests)."""
from __future__ import annotations

from unittest.mock import patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.modules.payment_reconciliation.router import router

app = FastAPI()
app.include_router(router)
client = TestClient(app)

MODULE = "app.modules.payment_reconciliation.router"

# ─── helpers ──────────────────────────────────────────────────────────────────

def _rec(
    rec_id="rec1",
    payment_id="pay1",
    invoice_id="inv1",
    status="active",
    notes="",
):
    return {
        "id": rec_id,
        "tenant_id": 1,
        "payment_id": payment_id,
        "invoice_id": invoice_id,
        "status": status,
        "notes": notes,
        "created_at": "2025-01-01T00:00:00+00:00",
        "cancelled_at": None,
        "cancel_reason": None,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# POST /api/reconciliations — reconcile_endpoint
# ═══════════════════════════════════════════════════════════════════════════════

def test_post_reconcile_success():
    with patch(f"{MODULE}.reconcile_payment", return_value=_rec()) as mock:
        resp = client.post("/api/reconciliations", json={
            "tenant_id": 1,
            "payment_id": "pay1",
            "invoice_id": "inv1",
        })
    assert resp.status_code == 200
    assert resp.json()["status"] == "active"
    mock.assert_called_once()


def test_post_reconcile_stores_notes():
    with patch(f"{MODULE}.reconcile_payment", return_value=_rec(notes="manual")):
        resp = client.post("/api/reconciliations", json={
            "tenant_id": 1,
            "payment_id": "pay1",
            "invoice_id": "inv1",
            "notes": "manual",
        })
    assert resp.status_code == 200
    assert resp.json()["notes"] == "manual"


def test_post_reconcile_payment_not_found_returns_404():
    with patch(f"{MODULE}.reconcile_payment", side_effect=LookupError("Payment pay1 not found")):
        resp = client.post("/api/reconciliations", json={
            "tenant_id": 1,
            "payment_id": "pay1",
            "invoice_id": "inv1",
        })
    assert resp.status_code == 404
    assert "pay1" in resp.json()["detail"]


def test_post_reconcile_not_completed_returns_400():
    with patch(f"{MODULE}.reconcile_payment", side_effect=ValueError("must be in COMPLETED")):
        resp = client.post("/api/reconciliations", json={
            "tenant_id": 1,
            "payment_id": "pay1",
            "invoice_id": "inv1",
        })
    assert resp.status_code == 400
    assert "COMPLETED" in resp.json()["detail"]


def test_post_reconcile_duplicate_returns_400():
    with patch(f"{MODULE}.reconcile_payment", side_effect=ValueError("already reconciled")):
        resp = client.post("/api/reconciliations", json={
            "tenant_id": 1,
            "payment_id": "pay1",
            "invoice_id": "inv1",
        })
    assert resp.status_code == 400


def test_post_reconcile_missing_tenant_rejected():
    resp = client.post("/api/reconciliations", json={
        "payment_id": "pay1",
        "invoice_id": "inv1",
    })
    assert resp.status_code == 422


def test_post_reconcile_missing_payment_id_rejected():
    resp = client.post("/api/reconciliations", json={
        "tenant_id": 1,
        "invoice_id": "inv1",
    })
    assert resp.status_code == 422


# ═══════════════════════════════════════════════════════════════════════════════
# GET /api/reconciliations — list_reconciliations_endpoint
# ═══════════════════════════════════════════════════════════════════════════════

def test_get_list_returns_all():
    recs = [_rec("r1"), _rec("r2", payment_id="pay2")]
    with patch(f"{MODULE}.list_reconciliations", return_value=recs):
        resp = client.get("/api/reconciliations", params={"tenant_id": 1})
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_get_list_filters_by_invoice_id():
    recs = [_rec("r1", invoice_id="inv1")]
    with patch(f"{MODULE}.list_reconciliations", return_value=recs) as mock:
        resp = client.get("/api/reconciliations", params={"tenant_id": 1, "invoice_id": "inv1"})
    assert resp.status_code == 200
    mock.assert_called_once_with(1, invoice_id="inv1", payment_id=None)


def test_get_list_filters_by_payment_id():
    recs = [_rec("r1", payment_id="pay1")]
    with patch(f"{MODULE}.list_reconciliations", return_value=recs) as mock:
        resp = client.get("/api/reconciliations", params={"tenant_id": 1, "payment_id": "pay1"})
    assert resp.status_code == 200
    mock.assert_called_once_with(1, invoice_id=None, payment_id="pay1")


def test_get_list_missing_tenant_rejected():
    resp = client.get("/api/reconciliations")
    assert resp.status_code == 422


# ═══════════════════════════════════════════════════════════════════════════════
# GET /api/reconciliations/{reconciliation_id}
# ═══════════════════════════════════════════════════════════════════════════════

def test_get_by_id_success():
    with patch(f"{MODULE}.get_reconciliation", return_value=_rec()) as mock:
        resp = client.get("/api/reconciliations/rec1", params={"tenant_id": 1})
    assert resp.status_code == 200
    assert resp.json()["id"] == "rec1"
    mock.assert_called_once_with(1, reconciliation_id="rec1")


def test_get_by_id_not_found_returns_404():
    with patch(f"{MODULE}.get_reconciliation", side_effect=LookupError("rec999 not found")):
        resp = client.get("/api/reconciliations/rec999", params={"tenant_id": 1})
    assert resp.status_code == 404
    assert "rec999" in resp.json()["detail"]


# ═══════════════════════════════════════════════════════════════════════════════
# POST /api/reconciliations/{reconciliation_id}/cancel
# ═══════════════════════════════════════════════════════════════════════════════

def test_cancel_success():
    cancelled = _rec(status="cancelled")
    with patch(f"{MODULE}.unreconcile", return_value=cancelled) as mock:
        resp = client.post("/api/reconciliations/rec1/cancel", json={
            "tenant_id": 1,
            "reason": "wrong invoice",
        })
    assert resp.status_code == 200
    assert resp.json()["status"] == "cancelled"
    mock.assert_called_once_with(1, reconciliation_id="rec1", reason="wrong invoice")


def test_cancel_not_found_returns_404():
    with patch(f"{MODULE}.unreconcile", side_effect=LookupError("rec999 not found")):
        resp = client.post("/api/reconciliations/rec999/cancel", json={"tenant_id": 1})
    assert resp.status_code == 404


def test_cancel_already_cancelled_returns_400():
    with patch(f"{MODULE}.unreconcile", side_effect=ValueError("already cancelled")):
        resp = client.post("/api/reconciliations/rec1/cancel", json={"tenant_id": 1})
    assert resp.status_code == 400
    assert "already cancelled" in resp.json()["detail"]


def test_cancel_missing_tenant_rejected():
    resp = client.post("/api/reconciliations/rec1/cancel", json={})
    assert resp.status_code == 422


# ═══════════════════════════════════════════════════════════════════════════════
# POST /api/reconciliations/auto
# ═══════════════════════════════════════════════════════════════════════════════

def test_auto_reconcile_success():
    rec = _rec(notes="auto-reconciled")
    with patch(f"{MODULE}.auto_reconcile", return_value=rec) as mock:
        resp = client.post("/api/reconciliations/auto", json={
            "tenant_id": 1,
            "invoice_id": "inv1",
        })
    assert resp.status_code == 200
    assert resp.json()["notes"] == "auto-reconciled"
    mock.assert_called_once_with(1, invoice_id="inv1")


def test_auto_reconcile_invoice_not_found_returns_404():
    with patch(f"{MODULE}.auto_reconcile", side_effect=LookupError("inv1 not found")):
        resp = client.post("/api/reconciliations/auto", json={
            "tenant_id": 1,
            "invoice_id": "inv1",
        })
    assert resp.status_code == 404


def test_auto_reconcile_no_eligible_payment_returns_400():
    with patch(f"{MODULE}.auto_reconcile", side_effect=ValueError("No eligible")):
        resp = client.post("/api/reconciliations/auto", json={
            "tenant_id": 1,
            "invoice_id": "inv1",
        })
    assert resp.status_code == 400
    assert "No eligible" in resp.json()["detail"]
