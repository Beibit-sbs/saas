"""Tests for Phase XXXIX — Online Payments Module."""
from __future__ import annotations

from unittest.mock import patch

import pytest

from app.modules.online_payments.service import (
    FAILURE_PATTERN_THRESHOLD,
    PAYMENT_STATES,
    SUPPORTED_METHODS,
    check_failure_pattern,
    complete_payment,
    create_payment,
    fail_payment,
    list_payments,
    process_payment,
    refund_payment,
)

TENANT = 1

# ─── helpers ──────────────────────────────────────────────────────────────────

def _payment(id_="p1", student_id="st1", amount=50000.0, status="PENDING", method="KASPI"):
    return {"id": id_, "student_id": student_id, "amount": amount, "status": status,
            "method": method, "currency": "KZT"}


# ─── constants ────────────────────────────────────────────────────────────────

def test_payment_states():
    assert PAYMENT_STATES == {"PENDING", "PROCESSING", "COMPLETED", "FAILED", "REFUNDED"}


def test_supported_methods():
    assert "KASPI" in SUPPORTED_METHODS
    assert "HALYK" in SUPPORTED_METHODS
    assert "CARD" in SUPPORTED_METHODS


def test_failure_pattern_threshold():
    assert FAILURE_PATTERN_THRESHOLD == 3


# ─── create_payment ───────────────────────────────────────────────────────────

def test_create_payment_success_fires_event():
    with (
        patch("app.modules.online_payments.service.create_entity_for_tenant", return_value={"id": "p1"}),
        patch("app.modules.online_payments.service.EventPublisher") as mock_pub,
    ):
        result = create_payment(TENANT, student_id="st1", amount=50000.0, method="KASPI")
    assert result["payment_id"] == "p1"
    assert result["status"] == "PENDING"
    call_kwargs = mock_pub.return_value.publish_event.call_args[1]
    assert call_kwargs["event_type"] == "payment.initiated"


def test_create_payment_invalid_method():
    with pytest.raises(ValueError, match="Invalid payment method"):
        create_payment(TENANT, student_id="st1", amount=100.0, method="CRYPTO")


def test_create_payment_zero_amount():
    with pytest.raises(ValueError, match="amount must be positive"):
        create_payment(TENANT, student_id="st1", amount=0.0, method="CARD")


def test_create_payment_negative_amount():
    with pytest.raises(ValueError, match="amount must be positive"):
        create_payment(TENANT, student_id="st1", amount=-100.0, method="CARD")


def test_create_payment_missing_student():
    with pytest.raises(ValueError, match="student_id"):
        create_payment(TENANT, student_id="", amount=100.0, method="CARD")


def test_create_payment_invalid_tenant():
    with pytest.raises(ValueError, match="tenant_id"):
        create_payment(0, student_id="st1", amount=100.0, method="CARD")


# ─── process_payment ──────────────────────────────────────────────────────────

def test_process_payment_success():
    pay = _payment(status="PENDING")
    with (
        patch("app.modules.online_payments.service.list_entities_for_tenant", return_value=[pay]),
        patch("app.modules.online_payments.service.create_entity_for_tenant", return_value={"id": "log1"}),
    ):
        result = process_payment(TENANT, payment_id="p1")
    assert result["status"] == "PROCESSING"


def test_process_payment_wrong_status():
    pay = _payment(status="COMPLETED")
    with patch("app.modules.online_payments.service.list_entities_for_tenant", return_value=[pay]):
        with pytest.raises(ValueError, match="Cannot transition"):
            process_payment(TENANT, payment_id="p1")


def test_process_payment_not_found():
    with patch("app.modules.online_payments.service.list_entities_for_tenant", return_value=[]):
        with pytest.raises(LookupError):
            process_payment(TENANT, payment_id="nonexistent")


# ─── complete_payment ─────────────────────────────────────────────────────────

def test_complete_payment_success_fires_event():
    pay = _payment(status="PROCESSING")
    with (
        patch("app.modules.online_payments.service.list_entities_for_tenant", return_value=[pay]),
        patch("app.modules.online_payments.service.create_entity_for_tenant", return_value={"id": "txn1"}),
        patch("app.modules.online_payments.service.EventPublisher") as mock_pub,
    ):
        result = complete_payment(TENANT, payment_id="p1", transaction_ref="REF-001")
    assert result["status"] == "COMPLETED"
    assert result["transaction_id"] == "txn1"
    call_kwargs = mock_pub.return_value.publish_event.call_args[1]
    assert call_kwargs["event_type"] == "payment.completed"


def test_complete_payment_missing_ref():
    with pytest.raises(ValueError, match="transaction_ref"):
        complete_payment(TENANT, payment_id="p1", transaction_ref="")


def test_complete_payment_wrong_status():
    pay = _payment(status="PENDING")
    with patch("app.modules.online_payments.service.list_entities_for_tenant", return_value=[pay]):
        with pytest.raises(ValueError, match="Cannot transition"):
            complete_payment(TENANT, payment_id="p1", transaction_ref="REF-002")


# ─── fail_payment ─────────────────────────────────────────────────────────────

def test_fail_payment_success_fires_event():
    pay = _payment(status="PROCESSING")
    with (
        patch("app.modules.online_payments.service.list_entities_for_tenant", return_value=[pay]),
        patch("app.modules.online_payments.service.create_entity_for_tenant", return_value={"id": "fail1"}),
        patch("app.modules.online_payments.service.EventPublisher") as mock_pub,
    ):
        result = fail_payment(TENANT, payment_id="p1", reason="Insufficient funds")
    assert result["status"] == "FAILED"
    call_kwargs = mock_pub.return_value.publish_event.call_args[1]
    assert call_kwargs["event_type"] == "payment.failed"


def test_fail_payment_missing_reason():
    with pytest.raises(ValueError, match="reason"):
        fail_payment(TENANT, payment_id="p1", reason="")


def test_fail_payment_wrong_status():
    pay = _payment(status="COMPLETED")
    with patch("app.modules.online_payments.service.list_entities_for_tenant", return_value=[pay]):
        with pytest.raises(ValueError, match="Cannot transition"):
            fail_payment(TENANT, payment_id="p1", reason="Network error")


# ─── refund_payment ───────────────────────────────────────────────────────────

def test_refund_payment_success_fires_event():
    pay = _payment(status="COMPLETED")
    with (
        patch("app.modules.online_payments.service.list_entities_for_tenant", return_value=[pay]),
        patch("app.modules.online_payments.service.create_entity_for_tenant", return_value={"id": "ref1"}),
        patch("app.modules.online_payments.service.EventPublisher") as mock_pub,
    ):
        result = refund_payment(TENANT, payment_id="p1", reason="Student withdrawal")
    assert result["status"] == "REFUNDED"
    assert result["refund_id"] == "ref1"
    call_kwargs = mock_pub.return_value.publish_event.call_args[1]
    assert call_kwargs["event_type"] == "payment.refunded"


def test_refund_payment_wrong_status():
    pay = _payment(status="PENDING")
    with patch("app.modules.online_payments.service.list_entities_for_tenant", return_value=[pay]):
        with pytest.raises(ValueError, match="Cannot transition"):
            refund_payment(TENANT, payment_id="p1", reason="Cancellation")


# ─── check_failure_pattern ────────────────────────────────────────────────────

def test_check_failure_pattern_fires_event_when_threshold_reached():
    failures = [{"student_id": "st1"} for _ in range(3)]
    with (
        patch("app.modules.online_payments.service.list_entities_for_tenant", return_value=failures),
        patch("app.modules.online_payments.service.create_entity_for_tenant", return_value={"id": "alert1"}),
        patch("app.modules.online_payments.service.EventPublisher") as mock_pub,
    ):
        result = check_failure_pattern(TENANT, student_id="st1")
    assert result["pattern_detected"] is True
    assert result["event_fired"] is True
    call_kwargs = mock_pub.return_value.publish_event.call_args[1]
    assert call_kwargs["event_type"] == "payment.failure_pattern"


def test_check_failure_pattern_no_event_below_threshold():
    failures = [{"student_id": "st1"} for _ in range(2)]
    with (
        patch("app.modules.online_payments.service.list_entities_for_tenant", return_value=failures),
        patch("app.modules.online_payments.service.EventPublisher") as mock_pub,
    ):
        result = check_failure_pattern(TENANT, student_id="st1")
    assert result["pattern_detected"] is False
    assert result["event_fired"] is False
    mock_pub.return_value.publish_event.assert_not_called()


# ─── list_payments ────────────────────────────────────────────────────────────

def test_list_payments_unfiltered():
    payments = [_payment(id_="p1"), _payment(id_="p2", student_id="st2")]
    with patch("app.modules.online_payments.service.list_entities_for_tenant", return_value=payments):
        result = list_payments(TENANT)
    assert len(result) == 2


def test_list_payments_by_student():
    payments = [_payment(id_="p1", student_id="st1"), _payment(id_="p2", student_id="st2")]
    with patch("app.modules.online_payments.service.list_entities_for_tenant", return_value=payments):
        result = list_payments(TENANT, student_id="st1")
    assert len(result) == 1
    assert result[0]["id"] == "p1"


def test_list_payments_by_status():
    payments = [_payment(id_="p1", status="COMPLETED"), _payment(id_="p2", status="PENDING")]
    with patch("app.modules.online_payments.service.list_entities_for_tenant", return_value=payments):
        result = list_payments(TENANT, status="COMPLETED")
    assert len(result) == 1
    assert result[0]["id"] == "p1"
