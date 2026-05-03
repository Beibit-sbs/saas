"""Phase LXX — Payment Reconciliation Service tests (20 tests)."""
from __future__ import annotations

from unittest.mock import MagicMock, patch, call

import pytest

SVC = "app.modules.payment_reconciliation.service"

# ─── helpers ──────────────────────────────────────────────────────────────────

def _payment(id="pay1", status="COMPLETED", student_id="st1"):
    return {"id": id, "status": status, "student_id": student_id, "tenant_id": 1}


def _invoice(id="inv1", student_id="st1"):
    return {"id": id, "student_id": student_id, "tenant_id": 1}


def _reconciliation(
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


def _patch_lists(payments=None, invoices=None, recs=None):
    """Return list of patches for the three list calls."""
    payments = payments if payments is not None else []
    invoices = invoices if invoices is not None else []
    recs = recs if recs is not None else []

    def _list_side_effect(entity_type, *, tenant_id):
        if entity_type == "payment_orders":
            return payments
        if entity_type == "invoices":
            return invoices
        if entity_type == "payment_reconciliations":
            return recs
        return []

    return _list_side_effect


# ═══════════════════════════════════════════════════════════════════════════════
# reconcile_payment — happy path
# ═══════════════════════════════════════════════════════════════════════════════

def test_reconcile_payment_returns_active_record():
    from app.modules.payment_reconciliation.service import reconcile_payment

    side = _patch_lists(
        payments=[_payment()],
        invoices=[_invoice()],
        recs=[],
    )
    with (
        patch(f"{SVC}.list_entities_for_tenant", side_effect=side),
        patch(f"{SVC}.create_entity_for_tenant") as mock_create,
        patch(f"{SVC}.EventPublisher"),
    ):
        result = reconcile_payment(1, payment_id="pay1", invoice_id="inv1")

    assert result["status"] == "active"
    assert result["payment_id"] == "pay1"
    assert result["invoice_id"] == "inv1"
    assert "id" in result
    mock_create.assert_called_once()


def test_reconcile_payment_stores_notes():
    from app.modules.payment_reconciliation.service import reconcile_payment

    side = _patch_lists(payments=[_payment()], invoices=[_invoice()], recs=[])
    with (
        patch(f"{SVC}.list_entities_for_tenant", side_effect=side),
        patch(f"{SVC}.create_entity_for_tenant"),
        patch(f"{SVC}.EventPublisher"),
    ):
        result = reconcile_payment(1, payment_id="pay1", invoice_id="inv1", notes="manual")

    assert result["notes"] == "manual"


def test_reconcile_payment_fires_created_event():
    from app.modules.payment_reconciliation.service import reconcile_payment

    pub_instance = MagicMock()
    side = _patch_lists(payments=[_payment()], invoices=[_invoice()], recs=[])
    with (
        patch(f"{SVC}.list_entities_for_tenant", side_effect=side),
        patch(f"{SVC}.create_entity_for_tenant"),
        patch(f"{SVC}.EventPublisher", return_value=pub_instance),
    ):
        reconcile_payment(1, payment_id="pay1", invoice_id="inv1")

    pub_instance.publish_event.assert_called_once()
    args = pub_instance.publish_event.call_args
    assert args.kwargs["event_type"] == "reconciliation.created"


# ═══════════════════════════════════════════════════════════════════════════════
# reconcile_payment — error paths
# ═══════════════════════════════════════════════════════════════════════════════

def test_reconcile_payment_raises_if_payment_not_found():
    from app.modules.payment_reconciliation.service import reconcile_payment

    side = _patch_lists(payments=[], invoices=[_invoice()], recs=[])
    with (
        patch(f"{SVC}.list_entities_for_tenant", side_effect=side),
        patch(f"{SVC}.create_entity_for_tenant"),
        patch(f"{SVC}.EventPublisher"),
        pytest.raises(LookupError, match="pay1"),
    ):
        reconcile_payment(1, payment_id="pay1", invoice_id="inv1")


def test_reconcile_payment_raises_if_not_completed():
    from app.modules.payment_reconciliation.service import reconcile_payment

    side = _patch_lists(
        payments=[_payment(status="PENDING")],
        invoices=[_invoice()],
        recs=[],
    )
    with (
        patch(f"{SVC}.list_entities_for_tenant", side_effect=side),
        patch(f"{SVC}.create_entity_for_tenant"),
        patch(f"{SVC}.EventPublisher"),
        pytest.raises(ValueError, match="COMPLETED"),
    ):
        reconcile_payment(1, payment_id="pay1", invoice_id="inv1")


def test_reconcile_payment_raises_if_invoice_not_found():
    from app.modules.payment_reconciliation.service import reconcile_payment

    side = _patch_lists(payments=[_payment()], invoices=[], recs=[])
    with (
        patch(f"{SVC}.list_entities_for_tenant", side_effect=side),
        patch(f"{SVC}.create_entity_for_tenant"),
        patch(f"{SVC}.EventPublisher"),
        pytest.raises(LookupError, match="inv1"),
    ):
        reconcile_payment(1, payment_id="pay1", invoice_id="inv1")


def test_reconcile_payment_raises_if_duplicate_active():
    from app.modules.payment_reconciliation.service import reconcile_payment

    existing_rec = _reconciliation(status="active")
    side = _patch_lists(
        payments=[_payment()],
        invoices=[_invoice()],
        recs=[existing_rec],
    )
    with (
        patch(f"{SVC}.list_entities_for_tenant", side_effect=side),
        patch(f"{SVC}.create_entity_for_tenant"),
        patch(f"{SVC}.EventPublisher"),
        pytest.raises(ValueError, match="already reconciled"),
    ):
        reconcile_payment(1, payment_id="pay1", invoice_id="inv1")


def test_reconcile_payment_allows_cancelled_duplicate():
    """Повторная сверка разрешена, если предыдущая отменена."""
    from app.modules.payment_reconciliation.service import reconcile_payment

    cancelled_rec = _reconciliation(status="cancelled")
    side = _patch_lists(
        payments=[_payment()],
        invoices=[_invoice()],
        recs=[cancelled_rec],
    )
    with (
        patch(f"{SVC}.list_entities_for_tenant", side_effect=side),
        patch(f"{SVC}.create_entity_for_tenant"),
        patch(f"{SVC}.EventPublisher"),
    ):
        result = reconcile_payment(1, payment_id="pay1", invoice_id="inv1")

    assert result["status"] == "active"


def test_reconcile_payment_raises_on_invalid_tenant():
    from app.modules.payment_reconciliation.service import reconcile_payment

    with pytest.raises(ValueError, match="tenant_id"):
        reconcile_payment(0, payment_id="pay1", invoice_id="inv1")


# ═══════════════════════════════════════════════════════════════════════════════
# get_reconciliation
# ═══════════════════════════════════════════════════════════════════════════════

def test_get_reconciliation_returns_record():
    from app.modules.payment_reconciliation.service import get_reconciliation

    rec = _reconciliation()
    with patch(f"{SVC}.list_entities_for_tenant", return_value=[rec]):
        result = get_reconciliation(1, reconciliation_id="rec1")

    assert result["id"] == "rec1"
    assert result["status"] == "active"


def test_get_reconciliation_raises_if_not_found():
    from app.modules.payment_reconciliation.service import get_reconciliation

    with (
        patch(f"{SVC}.list_entities_for_tenant", return_value=[]),
        pytest.raises(LookupError, match="rec999"),
    ):
        get_reconciliation(1, reconciliation_id="rec999")


# ═══════════════════════════════════════════════════════════════════════════════
# list_reconciliations
# ═══════════════════════════════════════════════════════════════════════════════

def test_list_reconciliations_returns_all():
    from app.modules.payment_reconciliation.service import list_reconciliations

    recs = [_reconciliation("r1"), _reconciliation("r2", payment_id="pay2")]
    with patch(f"{SVC}.list_entities_for_tenant", return_value=recs):
        result = list_reconciliations(1)

    assert len(result) == 2


def test_list_reconciliations_filters_by_invoice_id():
    from app.modules.payment_reconciliation.service import list_reconciliations

    recs = [
        _reconciliation("r1", invoice_id="inv1"),
        _reconciliation("r2", invoice_id="inv2"),
    ]
    with patch(f"{SVC}.list_entities_for_tenant", return_value=recs):
        result = list_reconciliations(1, invoice_id="inv1")

    assert len(result) == 1
    assert result[0]["invoice_id"] == "inv1"


def test_list_reconciliations_filters_by_payment_id():
    from app.modules.payment_reconciliation.service import list_reconciliations

    recs = [
        _reconciliation("r1", payment_id="pay1"),
        _reconciliation("r2", payment_id="pay2"),
    ]
    with patch(f"{SVC}.list_entities_for_tenant", return_value=recs):
        result = list_reconciliations(1, payment_id="pay2")

    assert len(result) == 1
    assert result[0]["payment_id"] == "pay2"


# ═══════════════════════════════════════════════════════════════════════════════
# unreconcile
# ═══════════════════════════════════════════════════════════════════════════════

def test_unreconcile_sets_cancelled():
    from app.modules.payment_reconciliation.service import unreconcile

    rec = _reconciliation()
    with (
        patch(f"{SVC}.list_entities_for_tenant", return_value=[rec]),
        patch(f"{SVC}.update_entity_for_tenant") as mock_upd,
        patch(f"{SVC}.EventPublisher"),
    ):
        result = unreconcile(1, reconciliation_id="rec1", reason="mistake")

    assert result["status"] == "cancelled"
    assert result["cancel_reason"] == "mistake"
    assert result["cancelled_at"] is not None
    mock_upd.assert_called_once()


def test_unreconcile_fires_cancelled_event():
    from app.modules.payment_reconciliation.service import unreconcile

    rec = _reconciliation()
    pub_instance = MagicMock()
    with (
        patch(f"{SVC}.list_entities_for_tenant", return_value=[rec]),
        patch(f"{SVC}.update_entity_for_tenant"),
        patch(f"{SVC}.EventPublisher", return_value=pub_instance),
    ):
        unreconcile(1, reconciliation_id="rec1")

    pub_instance.publish_event.assert_called_once()
    assert pub_instance.publish_event.call_args.kwargs["event_type"] == "reconciliation.cancelled"


def test_unreconcile_raises_if_already_cancelled():
    from app.modules.payment_reconciliation.service import unreconcile

    rec = _reconciliation(status="cancelled")
    with (
        patch(f"{SVC}.list_entities_for_tenant", return_value=[rec]),
        pytest.raises(ValueError, match="already cancelled"),
    ):
        unreconcile(1, reconciliation_id="rec1")


def test_unreconcile_raises_if_not_found():
    from app.modules.payment_reconciliation.service import unreconcile

    with (
        patch(f"{SVC}.list_entities_for_tenant", return_value=[]),
        pytest.raises(LookupError, match="rec999"),
    ):
        unreconcile(1, reconciliation_id="rec999")


# ═══════════════════════════════════════════════════════════════════════════════
# auto_reconcile
# ═══════════════════════════════════════════════════════════════════════════════

def test_auto_reconcile_matches_student_id():
    from app.modules.payment_reconciliation.service import auto_reconcile

    def side(entity_type, *, tenant_id):
        if entity_type == "invoices":
            return [_invoice()]
        if entity_type == "payment_orders":
            return [_payment(student_id="st1")]
        return []  # payment_reconciliations — пусто

    with (
        patch(f"{SVC}.list_entities_for_tenant", side_effect=side),
        patch(f"{SVC}.create_entity_for_tenant"),
        patch(f"{SVC}.EventPublisher"),
    ):
        result = auto_reconcile(1, invoice_id="inv1")

    assert result["status"] == "active"
    assert result["notes"] == "auto-reconciled"


def test_auto_reconcile_raises_if_invoice_not_found():
    from app.modules.payment_reconciliation.service import auto_reconcile

    with (
        patch(f"{SVC}.list_entities_for_tenant", return_value=[]),
        pytest.raises(LookupError, match="inv1"),
    ):
        auto_reconcile(1, invoice_id="inv1")


def test_auto_reconcile_raises_if_no_eligible_payment():
    from app.modules.payment_reconciliation.service import auto_reconcile

    def side(entity_type, *, tenant_id):
        if entity_type == "invoices":
            return [_invoice()]
        if entity_type == "payment_orders":
            return [_payment(status="PENDING")]  # не COMPLETED
        return []

    with (
        patch(f"{SVC}.list_entities_for_tenant", side_effect=side),
        patch(f"{SVC}.EventPublisher"),
        pytest.raises(ValueError, match="No eligible"),
    ):
        auto_reconcile(1, invoice_id="inv1")


def test_auto_reconcile_skips_already_reconciled_payments():
    from app.modules.payment_reconciliation.service import auto_reconcile

    def side(entity_type, *, tenant_id):
        if entity_type == "invoices":
            return [_invoice()]
        if entity_type == "payment_orders":
            return [_payment(id="pay1"), _payment(id="pay2", student_id="st1")]
        if entity_type == "payment_reconciliations":
            return [_reconciliation(payment_id="pay1", status="active")]
        return []

    with (
        patch(f"{SVC}.list_entities_for_tenant", side_effect=side),
        patch(f"{SVC}.create_entity_for_tenant"),
        patch(f"{SVC}.EventPublisher"),
    ):
        result = auto_reconcile(1, invoice_id="inv1")

    # pay1 уже привязан → должен выбрать pay2
    assert result["payment_id"] == "pay2"
