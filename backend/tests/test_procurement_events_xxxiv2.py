"""Phase XXXIV.2 — procurement lifecycle event publication tests."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

from tests.conftest import ADMIN_HEADERS, client

BASE = "/api/admin/procurement"


def _create_vendor(vendor_code: str = "VEN-EVT-001") -> None:
    resp = client.post(
        f"{BASE}/vendors",
        headers=ADMIN_HEADERS,
        json={
            "vendor_code": vendor_code,
            "name": "Event Vendor",
            "category": "it",
            "sla_breach_rate": 0.02,
            "on_time_delivery_rate": 0.99,
            "status": "active",
        },
    )
    assert resp.status_code == 200, resp.text


def _create_contract(contract_code: str, vendor_code: str = "VEN-EVT-001") -> int:
    resp = client.post(
        f"{BASE}/contracts",
        headers=ADMIN_HEADERS,
        json={
            "contract_code": contract_code,
            "vendor_code": vendor_code,
            "title": "Procurement event flow",
            "risk_score": 0.15,
            "sla_target_met": True,
            "status": "DRAFT",
        },
    )
    assert resp.status_code == 200, resp.text
    return int(resp.json()["item"]["id"])


def _patch_status(contract_id: int, status: str):
    return client.patch(
        f"{BASE}/contracts/{contract_id}/status",
        headers=ADMIN_HEADERS,
        json={"status": status},
    )


def test_create_contract_publishes_request_created() -> None:
    _create_vendor("VEN-EVT-100")
    with patch("app.modules.procurement.service.EventPublisher") as mock_cls:
        mock_pub = MagicMock()
        mock_cls.return_value = mock_pub
        _create_contract("CON-EVT-100", "VEN-EVT-100")
        event_types = [c.kwargs["event_type"] for c in mock_pub.publish_event.call_args_list]
        assert "procurement.request_created" in event_types


def test_approve_transition_publishes_approved() -> None:
    _create_vendor("VEN-EVT-101")
    contract_id = _create_contract("CON-EVT-101", "VEN-EVT-101")
    _patch_status(contract_id, "SUBMITTED")

    with patch("app.modules.procurement.service.EventPublisher") as mock_cls:
        mock_pub = MagicMock()
        mock_cls.return_value = mock_pub
        resp = _patch_status(contract_id, "APPROVED")
        assert resp.status_code == 200, resp.text
        event_types = [c.kwargs["event_type"] for c in mock_pub.publish_event.call_args_list]
        assert "procurement.approved" in event_types


def test_reject_transition_publishes_rejected() -> None:
    _create_vendor("VEN-EVT-102")
    contract_id = _create_contract("CON-EVT-102", "VEN-EVT-102")
    _patch_status(contract_id, "SUBMITTED")

    with patch("app.modules.procurement.service.EventPublisher") as mock_cls:
        mock_pub = MagicMock()
        mock_cls.return_value = mock_pub
        resp = _patch_status(contract_id, "REJECTED")
        assert resp.status_code == 200, resp.text
        event_types = [c.kwargs["event_type"] for c in mock_pub.publish_event.call_args_list]
        assert "procurement.rejected" in event_types


def test_po_issued_transition_publishes_po_issued() -> None:
    _create_vendor("VEN-EVT-103")
    contract_id = _create_contract("CON-EVT-103", "VEN-EVT-103")
    _patch_status(contract_id, "SUBMITTED")
    _patch_status(contract_id, "APPROVED")

    with patch("app.modules.procurement.service.EventPublisher") as mock_cls:
        mock_pub = MagicMock()
        mock_cls.return_value = mock_pub
        resp = _patch_status(contract_id, "PO_ISSUED")
        assert resp.status_code == 200, resp.text
        event_types = [c.kwargs["event_type"] for c in mock_pub.publish_event.call_args_list]
        assert "procurement.po_issued" in event_types


def test_delivered_transition_publishes_delivered() -> None:
    _create_vendor("VEN-EVT-104")
    contract_id = _create_contract("CON-EVT-104", "VEN-EVT-104")
    _patch_status(contract_id, "SUBMITTED")
    _patch_status(contract_id, "APPROVED")
    _patch_status(contract_id, "PO_ISSUED")

    with patch("app.modules.procurement.service.EventPublisher") as mock_cls:
        mock_pub = MagicMock()
        mock_cls.return_value = mock_pub
        resp = _patch_status(contract_id, "DELIVERED")
        assert resp.status_code == 200, resp.text
        event_types = [c.kwargs["event_type"] for c in mock_pub.publish_event.call_args_list]
        assert "procurement.delivered" in event_types


def test_invalid_transition_emits_no_lifecycle_event() -> None:
    _create_vendor("VEN-EVT-105")
    contract_id = _create_contract("CON-EVT-105", "VEN-EVT-105")

    with patch("app.modules.procurement.service.EventPublisher") as mock_cls:
        mock_pub = MagicMock()
        mock_cls.return_value = mock_pub
        resp = _patch_status(contract_id, "APPROVED")
        assert resp.status_code == 400, resp.text
        mock_pub.publish_event.assert_not_called()


def test_create_contract_survives_event_publisher_failure() -> None:
    _create_vendor("VEN-EVT-106")
    with patch("app.modules.procurement.service.EventPublisher") as mock_cls:
        mock_pub = MagicMock()
        mock_pub.publish_event.side_effect = RuntimeError("broker down")
        mock_cls.return_value = mock_pub
        resp = client.post(
            f"{BASE}/contracts",
            headers=ADMIN_HEADERS,
            json={
                "contract_code": "CON-EVT-106",
                "vendor_code": "VEN-EVT-106",
                "title": "Publisher failure tolerance",
                "risk_score": 0.2,
                "sla_target_met": True,
                "status": "DRAFT",
            },
        )
        assert resp.status_code == 200, resp.text


def test_approved_event_payload_contains_expected_fields() -> None:
    _create_vendor("VEN-EVT-107")
    contract_id = _create_contract("CON-EVT-107", "VEN-EVT-107")
    _patch_status(contract_id, "SUBMITTED")

    with patch("app.modules.procurement.service.EventPublisher") as mock_cls:
        mock_pub = MagicMock()
        mock_cls.return_value = mock_pub
        resp = _patch_status(contract_id, "APPROVED")
        assert resp.status_code == 200, resp.text

        approved_call = next(
            c for c in mock_pub.publish_event.call_args_list
            if c.kwargs.get("event_type") == "procurement.approved"
        )
        payload = approved_call.kwargs["payload_json"]
        assert payload["contract_id"] == contract_id
        assert payload["old_status"] == "SUBMITTED"
        assert payload["new_status"] == "APPROVED"


def test_submitted_transition_does_not_emit_target_lifecycle_events() -> None:
    _create_vendor("VEN-EVT-108")
    contract_id = _create_contract("CON-EVT-108", "VEN-EVT-108")

    with patch("app.modules.procurement.service.EventPublisher") as mock_cls:
        mock_pub = MagicMock()
        mock_cls.return_value = mock_pub
        resp = _patch_status(contract_id, "SUBMITTED")
        assert resp.status_code == 200, resp.text
        event_types = [c.kwargs["event_type"] for c in mock_pub.publish_event.call_args_list]
        assert "procurement.approved" not in event_types
        assert "procurement.rejected" not in event_types
        assert "procurement.po_issued" not in event_types
        assert "procurement.delivered" not in event_types


def test_delivered_invalid_without_po_issued_emits_no_event() -> None:
    _create_vendor("VEN-EVT-109")
    contract_id = _create_contract("CON-EVT-109", "VEN-EVT-109")
    _patch_status(contract_id, "SUBMITTED")

    with patch("app.modules.procurement.service.EventPublisher") as mock_cls:
        mock_pub = MagicMock()
        mock_cls.return_value = mock_pub
        resp = _patch_status(contract_id, "DELIVERED")
        assert resp.status_code == 400, resp.text
        mock_pub.publish_event.assert_not_called()
