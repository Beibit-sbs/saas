"""Phase LII — Student ID Card (NFC/QR) tests (20 tests)."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

BASE_MODULE = "app.modules.student_id_card.service"


def _make_create(return_id: int = 1) -> MagicMock:
    m = MagicMock(return_value={"id": return_id})
    return m


def _card_row(
    card_id: int = 1,
    student_id: int = 10,
    card_type: str = "hybrid",
    card_number: str = "ABCD12345678EF90",
    qr_code: str = "UNIV-1-ABCD12345678EF90",
    nfc_uid: str = "NFC001",
    status: str = "active",
) -> dict:
    return {
        "id": card_id,
        "student_id": student_id,
        "card_type": card_type,
        "card_number": card_number,
        "qr_code": qr_code,
        "nfc_uid": nfc_uid,
        "status": status,
    }


# ── issue_card ──────────────────────────────────────────────────────────────

@pytest.mark.parametrize("card_type,nfc_uid", [
    ("hybrid", "NFC001"),
    ("nfc", "NFC002"),
    ("qr", None),
])
def test_issue_card_valid_types(card_type, nfc_uid):
    with patch(f"{BASE_MODULE}.create_entity_for_tenant", _make_create(1)) as mc, \
         patch(f"{BASE_MODULE}.EventPublisher") as ep:
        from app.modules.student_id_card.service import issue_card
        card = issue_card(student_id=5, card_type=card_type, nfc_uid=nfc_uid, tenant_id=1)
    assert card.card_id == 1
    assert card.status == "active"
    assert card.card_type == card_type


def test_issue_card_invalid_type():
    from app.modules.student_id_card.service import issue_card, StudentIdCardError
    with pytest.raises(StudentIdCardError, match="invalid card_type"):
        issue_card(student_id=5, card_type="rfid", tenant_id=1)


def test_issue_card_nfc_requires_uid():
    from app.modules.student_id_card.service import issue_card, StudentIdCardError
    with pytest.raises(StudentIdCardError, match="nfc_uid"):
        issue_card(student_id=5, card_type="nfc", nfc_uid=None, tenant_id=1)


def test_issue_card_invalid_student_id():
    from app.modules.student_id_card.service import issue_card, StudentIdCardError
    with pytest.raises(StudentIdCardError, match="student_id"):
        issue_card(student_id=0, card_type="qr", tenant_id=1)


def test_issue_card_publishes_event():
    with patch(f"{BASE_MODULE}.create_entity_for_tenant", _make_create(3)), \
         patch(f"{BASE_MODULE}.EventPublisher") as ep:
        from app.modules.student_id_card.service import issue_card
        issue_card(student_id=7, card_type="qr", tenant_id=2)
    ep.publish.assert_called_once()
    call_kwargs = ep.publish.call_args.kwargs
    assert call_kwargs["event_type"] == "id_card.issued"
    assert call_kwargs["tenant_id"] == 2


# ── suspend_card ─────────────────────────────────────────────────────────────

def test_suspend_card_active():
    with patch(f"{BASE_MODULE}.list_entities_for_tenant", return_value=[_card_row()]), \
         patch(f"{BASE_MODULE}.update_entity_for_tenant") as upd, \
         patch(f"{BASE_MODULE}.EventPublisher"):
        from app.modules.student_id_card.service import suspend_card
        result = suspend_card(card_id=1, tenant_id=1)
    assert result.status == "suspended"
    upd.assert_called_once_with("student_id_cards", 1, {"status": "suspended"}, 1)


def test_suspend_card_not_found():
    with patch(f"{BASE_MODULE}.list_entities_for_tenant", return_value=[]):
        from app.modules.student_id_card.service import suspend_card, StudentIdCardError
        with pytest.raises(StudentIdCardError, match="not found"):
            suspend_card(card_id=99, tenant_id=1)


def test_suspend_card_already_suspended():
    row = _card_row(status="suspended")
    with patch(f"{BASE_MODULE}.list_entities_for_tenant", return_value=[row]):
        from app.modules.student_id_card.service import suspend_card, StudentIdCardError
        with pytest.raises(StudentIdCardError, match="active"):
            suspend_card(card_id=1, tenant_id=1)


# ── reactivate_card ──────────────────────────────────────────────────────────

def test_reactivate_card_suspended():
    row = _card_row(status="suspended")
    with patch(f"{BASE_MODULE}.list_entities_for_tenant", return_value=[row]), \
         patch(f"{BASE_MODULE}.update_entity_for_tenant") as upd:
        from app.modules.student_id_card.service import reactivate_card
        result = reactivate_card(card_id=1, tenant_id=1)
    assert result.status == "active"


def test_reactivate_card_active_fails():
    with patch(f"{BASE_MODULE}.list_entities_for_tenant", return_value=[_card_row(status="active")]):
        from app.modules.student_id_card.service import reactivate_card, StudentIdCardError
        with pytest.raises(StudentIdCardError, match="suspended"):
            reactivate_card(card_id=1, tenant_id=1)


# ── revoke_card ──────────────────────────────────────────────────────────────

def test_revoke_card_active():
    with patch(f"{BASE_MODULE}.list_entities_for_tenant", return_value=[_card_row()]), \
         patch(f"{BASE_MODULE}.update_entity_for_tenant"), \
         patch(f"{BASE_MODULE}.EventPublisher") as ep:
        from app.modules.student_id_card.service import revoke_card
        result = revoke_card(card_id=1, tenant_id=1)
    assert result.status == "revoked"
    ep.publish.assert_called_once()
    assert ep.publish.call_args.kwargs["event_type"] == "id_card.revoked"


def test_revoke_card_already_revoked():
    row = _card_row(status="revoked")
    with patch(f"{BASE_MODULE}.list_entities_for_tenant", return_value=[row]):
        from app.modules.student_id_card.service import revoke_card, StudentIdCardError
        with pytest.raises(StudentIdCardError, match="already revoked"):
            revoke_card(card_id=1, tenant_id=1)


# ── scan_card ─────────────────────────────────────────────────────────────────

def test_scan_card_granted():
    row = _card_row(card_number="TESTCARD1234")
    with patch(f"{BASE_MODULE}.list_entities_for_tenant", return_value=[row]), \
         patch(f"{BASE_MODULE}.create_entity_for_tenant", _make_create(10)), \
         patch(f"{BASE_MODULE}.EventPublisher") as ep:
        from app.modules.student_id_card.service import scan_card
        result = scan_card(card_number="TESTCARD1234", location="Main Gate", tenant_id=1)
    assert result.result == "granted"
    ep.publish.assert_not_called()


def test_scan_card_denied_unknown_card():
    with patch(f"{BASE_MODULE}.list_entities_for_tenant", return_value=[]), \
         patch(f"{BASE_MODULE}.create_entity_for_tenant", _make_create(20)), \
         patch(f"{BASE_MODULE}.EventPublisher") as ep:
        from app.modules.student_id_card.service import scan_card
        result = scan_card(card_number="UNKNOWNCARD", location="Library", tenant_id=1)
    assert result.result == "denied"
    ep.publish.assert_called_once()
    assert ep.publish.call_args.kwargs["event_type"] == "id_card.access_denied"


def test_scan_card_denied_suspended():
    row = _card_row(card_number="SUSP001", status="suspended")
    with patch(f"{BASE_MODULE}.list_entities_for_tenant", return_value=[row]), \
         patch(f"{BASE_MODULE}.create_entity_for_tenant", _make_create(5)), \
         patch(f"{BASE_MODULE}.EventPublisher"):
        from app.modules.student_id_card.service import scan_card
        result = scan_card(card_number="SUSP001", location="Dorm", tenant_id=1)
    assert result.result == "denied"


def test_scan_card_empty_card_number():
    from app.modules.student_id_card.service import scan_card, StudentIdCardError
    with pytest.raises(StudentIdCardError, match="card_number"):
        scan_card(card_number="   ", location="Gate", tenant_id=1)


def test_scan_card_empty_location():
    from app.modules.student_id_card.service import scan_card, StudentIdCardError
    with pytest.raises(StudentIdCardError, match="location"):
        scan_card(card_number="ABCD1234", location="", tenant_id=1)


# ── list_cards ───────────────────────────────────────────────────────────────

def test_list_cards_returns_matching():
    rows = [_card_row(student_id=5), _card_row(card_id=2, student_id=9)]
    with patch(f"{BASE_MODULE}.list_entities_for_tenant", return_value=rows):
        from app.modules.student_id_card.service import list_cards
        result = list_cards(student_id=5, tenant_id=1)
    assert len(result) == 1
    assert result[0].student_id == 5


def test_list_cards_empty():
    with patch(f"{BASE_MODULE}.list_entities_for_tenant", return_value=[]):
        from app.modules.student_id_card.service import list_cards
        result = list_cards(student_id=1, tenant_id=1)
    assert result == []
