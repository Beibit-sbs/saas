"""Phase LXVIII — Online Payments Router tests (20 tests)."""
from __future__ import annotations

from unittest.mock import patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.modules.online_payments.router import router

app = FastAPI()
app.include_router(router)
client = TestClient(app)

MODULE = "app.modules.online_payments.router"

# ─── helpers ──────────────────────────────────────────────────────────────────

def _payment(
    payment_id="p1",
    student_id="st1",
    amount=50000.0,
    method="KASPI",
    status="PENDING",
):
    return {
        "payment_id": payment_id,
        "student_id": student_id,
        "amount": amount,
        "method": method,
        "status": status,
    }


def _full_payment(
    id="p1",
    student_id="st1",
    amount=50000.0,
    status="PENDING",
    method="KASPI",
    currency="KZT",
):
    return {
        "id": id,
        "student_id": student_id,
        "amount": amount,
        "status": status,
        "method": method,
        "currency": currency,
        "tenant_id": 5,
    }


# ─── POST /api/payments ───────────────────────────────────────────────────────

def test_create_payment_success():
    with patch(f"{MODULE}.create_payment", return_value=_payment()) as mock:
        response = client.post("/api/payments", json={
            "tenant_id": 5,
            "student_id": "st1",
            "amount": 50000.0,
            "method": "KASPI",
        })
    assert response.status_code == 200
    data = response.json()
    assert data["payment_id"] == "p1"
    assert data["status"] == "PENDING"
    mock.assert_called_once()


def test_create_payment_invalid_method_returns_400():
    with patch(f"{MODULE}.create_payment", side_effect=ValueError("Invalid payment method")):
        response = client.post("/api/payments", json={
            "tenant_id": 5,
            "student_id": "st1",
            "amount": 50000.0,
            "method": "BITCOIN",
        })
    assert response.status_code == 400
    assert "Invalid payment method" in response.json()["detail"]


def test_create_payment_negative_amount_rejected_by_schema():
    response = client.post("/api/payments", json={
        "tenant_id": 5,
        "student_id": "st1",
        "amount": -1.0,
        "method": "KASPI",
    })
    assert response.status_code == 422


def test_create_payment_missing_student_rejected_by_schema():
    response = client.post("/api/payments", json={
        "tenant_id": 5,
        "amount": 50000.0,
        "method": "KASPI",
    })
    assert response.status_code == 422


# ─── GET /api/payments ────────────────────────────────────────────────────────

def test_list_payments_success():
    payments = [_full_payment("p1"), _full_payment("p2", status="COMPLETED")]
    with patch(f"{MODULE}.list_payments", return_value=payments) as mock:
        response = client.get("/api/payments?tenant_id=5")
    assert response.status_code == 200
    assert len(response.json()) == 2
    mock.assert_called_once_with(tenant_id=5, student_id=None, status=None)


def test_list_payments_with_status_filter():
    payments = [_full_payment("p3", status="COMPLETED")]
    with patch(f"{MODULE}.list_payments", return_value=payments) as mock:
        response = client.get("/api/payments?tenant_id=5&status=COMPLETED")
    assert response.status_code == 200
    assert response.json()[0]["status"] == "COMPLETED"
    mock.assert_called_once_with(tenant_id=5, student_id=None, status="COMPLETED")


def test_list_payments_with_student_filter():
    with patch(f"{MODULE}.list_payments", return_value=[_full_payment()]) as mock:
        response = client.get("/api/payments?tenant_id=5&student_id=st1")
    assert response.status_code == 200
    mock.assert_called_once_with(tenant_id=5, student_id="st1", status=None)


def test_list_payments_missing_tenant_rejected():
    response = client.get("/api/payments")
    assert response.status_code == 422


# ─── GET /api/payments/failure-pattern ───────────────────────────────────────

def test_failure_pattern_detected():
    result = {
        "student_id": "st1",
        "failure_count": 3,
        "pattern_detected": True,
        "event_fired": True,
    }
    with patch(f"{MODULE}.check_failure_pattern", return_value=result):
        response = client.get("/api/payments/failure-pattern?tenant_id=5&student_id=st1")
    assert response.status_code == 200
    assert response.json()["pattern_detected"] is True
    assert response.json()["failure_count"] == 3


def test_failure_pattern_not_detected():
    result = {
        "student_id": "st1",
        "failure_count": 1,
        "pattern_detected": False,
        "event_fired": False,
    }
    with patch(f"{MODULE}.check_failure_pattern", return_value=result):
        response = client.get("/api/payments/failure-pattern?tenant_id=5&student_id=st1")
    assert response.status_code == 200
    assert response.json()["pattern_detected"] is False


# ─── GET /api/payments/{payment_id} ──────────────────────────────────────────

def test_get_payment_success():
    with patch(f"{MODULE}.get_payment", return_value=_full_payment()) as mock:
        response = client.get("/api/payments/p1?tenant_id=5")
    assert response.status_code == 200
    assert response.json()["id"] == "p1"
    mock.assert_called_once_with(5, payment_id="p1")


def test_get_payment_not_found_returns_404():
    with patch(f"{MODULE}.get_payment", side_effect=LookupError("Payment p99 not found")):
        response = client.get("/api/payments/p99?tenant_id=5")
    assert response.status_code == 404
    assert "p99" in response.json()["detail"]


# ─── POST /api/payments/{payment_id}/process ─────────────────────────────────

def test_process_payment_success():
    result = {"payment_id": "p1", "status": "PROCESSING", "log_id": "log1"}
    with patch(f"{MODULE}.process_payment", return_value=result) as mock:
        response = client.post("/api/payments/p1/process?tenant_id=5")
    assert response.status_code == 200
    assert response.json()["status"] == "PROCESSING"
    mock.assert_called_once_with(5, payment_id="p1")


def test_process_payment_invalid_transition_returns_400():
    with patch(f"{MODULE}.process_payment", side_effect=ValueError("Cannot transition")):
        response = client.post("/api/payments/p1/process?tenant_id=5")
    assert response.status_code == 400


# ─── POST /api/payments/{payment_id}/complete ────────────────────────────────

def test_complete_payment_success():
    result = {"payment_id": "p1", "status": "COMPLETED", "transaction_id": "txn1"}
    with patch(f"{MODULE}.complete_payment", return_value=result) as mock:
        response = client.post("/api/payments/p1/complete", json={
            "tenant_id": 5,
            "transaction_ref": "TXN-KASPI-001",
        })
    assert response.status_code == 200
    assert response.json()["status"] == "COMPLETED"
    mock.assert_called_once_with(5, payment_id="p1", transaction_ref="TXN-KASPI-001")


def test_complete_payment_missing_ref_rejected_by_schema():
    response = client.post("/api/payments/p1/complete", json={"tenant_id": 5})
    assert response.status_code == 422


# ─── POST /api/payments/{payment_id}/fail ────────────────────────────────────

def test_fail_payment_success():
    result = {"payment_id": "p1", "status": "FAILED", "failure_id": "fail1"}
    with patch(f"{MODULE}.fail_payment", return_value=result) as mock:
        response = client.post("/api/payments/p1/fail", json={
            "tenant_id": 5,
            "reason": "Insufficient funds",
        })
    assert response.status_code == 200
    assert response.json()["status"] == "FAILED"
    mock.assert_called_once_with(5, payment_id="p1", reason="Insufficient funds")


def test_fail_payment_not_found_returns_400():
    with patch(f"{MODULE}.fail_payment", side_effect=LookupError("Payment not found")):
        response = client.post("/api/payments/p99/fail", json={
            "tenant_id": 5,
            "reason": "error",
        })
    assert response.status_code == 400


# ─── POST /api/payments/{payment_id}/refund ──────────────────────────────────

def test_refund_payment_success():
    result = {"payment_id": "p1", "status": "REFUNDED", "refund_id": "ref1"}
    with patch(f"{MODULE}.refund_payment", return_value=result) as mock:
        response = client.post("/api/payments/p1/refund", json={
            "tenant_id": 5,
            "reason": "Customer request",
        })
    assert response.status_code == 200
    assert response.json()["status"] == "REFUNDED"
    mock.assert_called_once_with(5, payment_id="p1", reason="Customer request")


def test_refund_payment_missing_reason_rejected_by_schema():
    response = client.post("/api/payments/p1/refund", json={"tenant_id": 5})
    assert response.status_code == 422
