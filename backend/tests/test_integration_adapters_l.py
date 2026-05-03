"""Phase L — Integration Adapters tests (35 tests, 5 per adapter)."""
from __future__ import annotations

import json
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
import httpx

# ─────────────────────────────────────────────────────────────────────────────
# L.1a — KaspiPay adapter (5 tests)
# ─────────────────────────────────────────────────────────────────────────────

from app.integrations.payments.kaspi_adapter import (
    KaspiPayError,
    create_order as kaspi_create_order,
    check_status as kaspi_check_status,
    refund as kaspi_refund,
)


def test_kaspi_create_order_returns_order_id_and_qr():
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"orderId": "k-001", "qrCode": "QR_DATA"}
    mock_resp.raise_for_status.return_value = None
    with patch("app.integrations.payments.kaspi_adapter.httpx.post", return_value=mock_resp):
        result = kaspi_create_order("merch-1", 5000.0, "https://cb.example.com/kaspi")
    assert result["order_id"] == "k-001"
    assert result["qr_code"] == "QR_DATA"
    assert result["status"] == "PENDING"


def test_kaspi_create_order_validates_amount():
    with pytest.raises(ValueError, match="amount must be positive"):
        kaspi_create_order("merch-1", -100.0, "https://cb.example.com")


def test_kaspi_create_order_validates_merchant_id():
    with pytest.raises(ValueError, match="merchant_id is required"):
        kaspi_create_order("", 100.0, "https://cb.example.com")


def test_kaspi_check_status_returns_status():
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"status": "PAID"}
    mock_resp.raise_for_status.return_value = None
    with patch("app.integrations.payments.kaspi_adapter.httpx.get", return_value=mock_resp):
        status = kaspi_check_status("k-001")
    assert status == "PAID"


def test_kaspi_refund_raises_on_network_error():
    with patch(
        "app.integrations.payments.kaspi_adapter.httpx.post",
        side_effect=httpx.ConnectError("timeout"),
    ):
        with pytest.raises(KaspiPayError, match="KaspiPay refund failed"):
            kaspi_refund("k-001", 5000.0)


# ─────────────────────────────────────────────────────────────────────────────
# L.1b — HalykBank adapter (5 tests)
# ─────────────────────────────────────────────────────────────────────────────

from app.integrations.payments.halyk_adapter import (
    HalykBankError,
    create_order as halyk_create_order,
    check_status as halyk_check_status,
    refund as halyk_refund,
)


def test_halyk_create_order_returns_order_id_and_redirect():
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"invoiceId": "h-999", "hpUrl": "https://epay.homebank.kz/pay/h-999"}
    mock_resp.raise_for_status.return_value = None
    with patch("app.integrations.payments.halyk_adapter.httpx.post", return_value=mock_resp):
        result = halyk_create_order("halyk-merch", 10000.0, "https://cb.example.com/halyk")
    assert result["order_id"] == "h-999"
    assert "epay" in result["redirect_url"]
    assert result["status"] == "PENDING"


def test_halyk_create_order_validates_amount_zero():
    with pytest.raises(ValueError, match="amount must be positive"):
        halyk_create_order("merch", 0.0, "https://cb.example.com")


def test_halyk_create_order_validates_callback_url():
    with pytest.raises(ValueError, match="callback_url is required"):
        halyk_create_order("merch", 100.0, "")


def test_halyk_check_status_returns_failed():
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"status": "FAILED"}
    mock_resp.raise_for_status.return_value = None
    with patch("app.integrations.payments.halyk_adapter.httpx.get", return_value=mock_resp):
        status = halyk_check_status("h-999")
    assert status == "FAILED"


def test_halyk_refund_raises_on_network_error():
    with patch(
        "app.integrations.payments.halyk_adapter.httpx.post",
        side_effect=httpx.ConnectError("conn refused"),
    ):
        with pytest.raises(HalykBankError, match="HalykBank refund failed"):
            halyk_refund("h-999", 500.0)


# ─────────────────────────────────────────────────────────────────────────────
# L.2a — Beeline SMS adapter (5 tests)
# ─────────────────────────────────────────────────────────────────────────────

from app.integrations.sms.beeline_adapter import (
    BeelineSmsError,
    send_sms as beeline_send,
    check_delivery as beeline_check,
)


def test_beeline_send_sms_returns_sent():
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"status": "SENT", "messageId": "bln-1"}
    mock_resp.raise_for_status.return_value = None
    with patch("app.integrations.sms.beeline_adapter.httpx.post", return_value=mock_resp):
        result = beeline_send("+77011234567", "OTP: 1234")
    assert result == "SENT"


def test_beeline_send_sms_validates_empty_phone():
    with pytest.raises(ValueError, match="phone is required"):
        beeline_send("", "Hello")


def test_beeline_send_sms_validates_empty_message():
    with pytest.raises(ValueError, match="message is required"):
        beeline_send("+77011234567", "")


def test_beeline_send_sms_rejects_too_long_message():
    with pytest.raises(ValueError, match="message too long"):
        beeline_send("+77011234567", "A" * 1025)


def test_beeline_send_sms_raises_on_network_error():
    with patch(
        "app.integrations.sms.beeline_adapter.httpx.post",
        side_effect=httpx.ConnectError("SMS gateway down"),
    ):
        with pytest.raises(BeelineSmsError, match="Beeline send_sms failed"):
            beeline_send("+77011234567", "Test")


# ─────────────────────────────────────────────────────────────────────────────
# L.2b — Kcell SMS adapter (5 tests)
# ─────────────────────────────────────────────────────────────────────────────

from app.integrations.sms.kcell_adapter import (
    KcellSmsError,
    send_sms as kcell_send,
    check_delivery as kcell_check,
)


def test_kcell_send_sms_returns_queued():
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"deliveryStatus": "QUEUED", "messageId": "kc-55"}
    mock_resp.raise_for_status.return_value = None
    with patch("app.integrations.sms.kcell_adapter.httpx.post", return_value=mock_resp):
        result = kcell_send("+77071234567", "Your code: 5678")
    assert result == "QUEUED"


def test_kcell_send_sms_validates_empty_phone():
    with pytest.raises(ValueError, match="phone is required"):
        kcell_send("", "Hello")


def test_kcell_send_sms_validates_empty_message():
    with pytest.raises(ValueError, match="message is required"):
        kcell_send("+77071234567", "")


def test_kcell_check_delivery_returns_status():
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"deliveryStatus": "DELIVERED"}
    mock_resp.raise_for_status.return_value = None
    with patch("app.integrations.sms.kcell_adapter.httpx.get", return_value=mock_resp):
        status = kcell_check("kc-55")
    assert status == "DELIVERED"


def test_kcell_send_sms_raises_on_http_error():
    with patch(
        "app.integrations.sms.kcell_adapter.httpx.post",
        side_effect=httpx.ConnectError("timeout"),
    ):
        with pytest.raises(KcellSmsError, match="Kcell send_sms failed"):
            kcell_send("+77071234567", "Test")


# ─────────────────────────────────────────────────────────────────────────────
# L.3 — NCA ЭЦП adapter (5 tests)
# ─────────────────────────────────────────────────────────────────────────────

import base64

from app.integrations.crypto.nca_adapter import (
    NcaError,
    SignerInfo,
    sign as nca_sign,
    verify_signature as nca_verify,
)


def test_nca_sign_returns_bytes():
    signed_data = base64.b64encode(b"SIGNED_DOC").decode()
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"cms": signed_data}
    mock_resp.raise_for_status.return_value = None
    with patch("app.integrations.crypto.nca_adapter.httpx.post", return_value=mock_resp):
        result = nca_sign(b"document content", b"p12-cert-bytes")
    assert isinstance(result, bytes)
    assert result == b"SIGNED_DOC"


def test_nca_sign_validates_empty_doc():
    with pytest.raises(ValueError, match="doc_bytes is required"):
        nca_sign(b"", b"cert")


def test_nca_sign_validates_empty_cert():
    with pytest.raises(ValueError, match="p12_cert is required"):
        nca_sign(b"doc", b"")


def test_nca_verify_returns_signer_info():
    mock_resp = MagicMock()
    mock_resp.json.return_value = {
        "iin": "123456789012",
        "cn": "Иванов Иван",
        "valid": True,
        "serial": "ABC123",
        "notAfter": "2026-01-01",
    }
    mock_resp.raise_for_status.return_value = None
    with patch("app.integrations.crypto.nca_adapter.httpx.post", return_value=mock_resp):
        info = nca_verify(b"signed-doc-bytes")
    assert isinstance(info, SignerInfo)
    assert info.valid is True
    assert info.iin == "123456789012"
    assert info.to_dict()["cn"] == "Иванов Иван"


def test_nca_sign_raises_on_network_error():
    with patch(
        "app.integrations.crypto.nca_adapter.httpx.post",
        side_effect=httpx.ConnectError("NCA unavailable"),
    ):
        with pytest.raises(NcaError, match="NCA sign failed"):
            nca_sign(b"doc", b"cert")


# ─────────────────────────────────────────────────────────────────────────────
# L.4 — ZKTeco Biometric adapter (5 tests)
# ─────────────────────────────────────────────────────────────────────────────

from app.integrations.biometric.zkteco_adapter import (
    AccessEvent,
    ZKTecoError,
    get_events,
    enroll_user,
    delete_user,
)


def test_zkteco_get_events_returns_access_event_list():
    mock_resp = MagicMock()
    mock_resp.json.return_value = {
        "events": [
            {
                "id": "ev-1",
                "userId": "u-100",
                "door": "MAIN",
                "direction": "IN",
                "timestamp": "2025-01-01T09:00:00",
                "granted": True,
            }
        ]
    }
    mock_resp.raise_for_status.return_value = None
    with patch("app.integrations.biometric.zkteco_adapter.httpx.get", return_value=mock_resp):
        events = get_events(datetime(2025, 1, 1))
    assert len(events) == 1
    assert isinstance(events[0], AccessEvent)
    assert events[0].granted is True
    assert events[0].to_dict()["door"] == "MAIN"


def test_zkteco_get_events_validates_from_dt():
    with pytest.raises((ValueError, TypeError)):
        get_events(None)  # type: ignore[arg-type]


def test_zkteco_enroll_user_returns_true():
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"success": True}
    mock_resp.raise_for_status.return_value = None
    with patch("app.integrations.biometric.zkteco_adapter.httpx.post", return_value=mock_resp):
        result = enroll_user("u-100", b"\x01\x02\x03biometric")
    assert result is True


def test_zkteco_enroll_user_validates_empty_user_id():
    with pytest.raises(ValueError, match="user_id is required"):
        enroll_user("", b"bio")


def test_zkteco_get_events_raises_on_network_error():
    with patch(
        "app.integrations.biometric.zkteco_adapter.httpx.get",
        side_effect=httpx.ConnectError("controller offline"),
    ):
        with pytest.raises(ZKTecoError, match="ZKTeco get_events failed"):
            get_events(datetime(2025, 1, 1))


# ─────────────────────────────────────────────────────────────────────────────
# L.5 — Ministry of Education NIS adapter (5 tests)
# ─────────────────────────────────────────────────────────────────────────────

from app.integrations.ministry.nis_adapter import (
    NisAdapterError,
    push_student_data,
    push_grades,
    push_enrollment_stats,
)


def test_nis_push_student_data_returns_sync_result():
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"accepted": 10, "rejected": 0, "errors": [], "syncId": "sync-42"}
    mock_resp.raise_for_status.return_value = None
    students = [{"iin": "111111111111", "name": "Тест"}]
    with patch("app.integrations.ministry.nis_adapter.httpx.post", return_value=mock_resp):
        result = push_student_data("tenant-1", students)
    assert result["accepted"] == 10
    assert result["sync_id"] == "sync-42"
    assert result["errors"] == []


def test_nis_push_student_data_validates_tenant_id():
    with pytest.raises(ValueError, match="tenant_id is required"):
        push_student_data("", [])


def test_nis_push_grades_returns_result():
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"accepted": 5, "rejected": 1, "errors": ["bad grade"], "syncId": "sg-7"}
    mock_resp.raise_for_status.return_value = None
    with patch("app.integrations.ministry.nis_adapter.httpx.post", return_value=mock_resp):
        result = push_grades("tenant-1", [{"student_id": "s1", "course": "Math", "grade": "A"}])
    assert result["rejected"] == 1
    assert len(result["errors"]) == 1


def test_nis_push_enrollment_stats_returns_status():
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"status": "ACCEPTED", "reportId": "rpt-99"}
    mock_resp.raise_for_status.return_value = None
    stats = {"total": 1200, "active": 1150, "graduated": 50}
    with patch("app.integrations.ministry.nis_adapter.httpx.post", return_value=mock_resp):
        result = push_enrollment_stats("tenant-1", stats)
    assert result["status"] == "ACCEPTED"
    assert result["report_id"] == "rpt-99"


def test_nis_push_student_data_raises_on_network_error():
    with patch(
        "app.integrations.ministry.nis_adapter.httpx.post",
        side_effect=httpx.ConnectError("NIS unreachable"),
    ):
        with pytest.raises(NisAdapterError, match="NIS push_student_data failed"):
            push_student_data("tenant-1", [])


# ─────────────────────────────────────────────────────────────────────────────
# L.6 — Moodle LTI 1.3 adapter (5 tests)
# ─────────────────────────────────────────────────────────────────────────────

from app.integrations.lms.moodle_lti_adapter import (
    MoodleLtiError,
    launch as lti_launch,
    submit_grade as lti_submit_grade,
    deep_link_selection,
)


def test_lti_launch_returns_launch_data():
    result = lti_launch("client-1", "deploy-1", "user-42", "resource-link-1")
    assert "id_token" in result
    assert "launch_url" in result
    assert "nonce" in result
    claims = json.loads(result["id_token"])
    assert claims["sub"] == "user-42"
    assert claims["iss"] == "client-1"


def test_lti_launch_validates_client_id():
    with pytest.raises(ValueError, match="client_id is required"):
        lti_launch("", "deploy-1", "user-1", "rl-1")


def test_lti_submit_grade_returns_true():
    mock_resp = MagicMock()
    mock_resp.raise_for_status.return_value = None
    with patch("app.integrations.lms.moodle_lti_adapter.httpx.post", return_value=mock_resp):
        result = lti_submit_grade("https://moodle.example.com/grade", 0.85, "user-42")
    assert result is True


def test_lti_submit_grade_validates_score_range():
    with pytest.raises(ValueError, match="score must be between"):
        lti_submit_grade("https://moodle.example.com/grade", 1.5, "user-42")


def test_deep_link_selection_returns_json_string():
    items = [{"type": "ltiResourceLink", "url": "https://content.example.com/1"}]
    result = deep_link_selection(items)
    assert isinstance(result, str)
    data = json.loads(result)
    assert data["type"] == "LtiDeepLinkingResponse"
    assert data["content_items"] == items


# ─────────────────────────────────────────────────────────────────────────────
# L.7 — 1C / SAP ERP adapter (5 tests)
# ─────────────────────────────────────────────────────────────────────────────

from app.integrations.erp.onec_adapter import (
    OneCAdapterError,
    sync_payroll,
    sync_budget,
    sync_assets,
)


def test_onec_sync_payroll_returns_summary():
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"synced": 42, "errors": [], "period": "2025-01", "status": "OK"}
    mock_resp.raise_for_status.return_value = None
    with patch("app.integrations.erp.onec_adapter.httpx.get", return_value=mock_resp):
        result = sync_payroll("tenant-1", period="2025-01")
    assert result["synced"] == 42
    assert result["status"] == "OK"
    assert result["period"] == "2025-01"


def test_onec_sync_payroll_validates_tenant_id():
    with pytest.raises(ValueError, match="tenant_id is required"):
        sync_payroll("")


def test_onec_sync_budget_returns_lines_synced():
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"linesSynced": 200, "errors": [], "fiscalYear": 2025, "status": "OK"}
    mock_resp.raise_for_status.return_value = None
    with patch("app.integrations.erp.onec_adapter.httpx.post", return_value=mock_resp):
        result = sync_budget("tenant-1", fiscal_year=2025)
    assert result["lines_synced"] == 200
    assert result["fiscal_year"] == 2025


def test_onec_sync_assets_returns_assets_count():
    mock_resp = MagicMock()
    mock_resp.json.return_value = {
        "assetsSynced": 150,
        "depreciationUpdated": 30,
        "errors": [],
        "status": "OK",
    }
    mock_resp.raise_for_status.return_value = None
    with patch("app.integrations.erp.onec_adapter.httpx.get", return_value=mock_resp):
        result = sync_assets("tenant-1")
    assert result["assets_synced"] == 150
    assert result["depreciation_updated"] == 30


def test_onec_sync_payroll_raises_on_network_error():
    with patch(
        "app.integrations.erp.onec_adapter.httpx.get",
        side_effect=httpx.ConnectError("1C offline"),
    ):
        with pytest.raises(OneCAdapterError, match="1C sync_payroll failed"):
            sync_payroll("tenant-1")
