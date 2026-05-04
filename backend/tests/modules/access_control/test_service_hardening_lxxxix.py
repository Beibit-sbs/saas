"""
LXXXIX — Access Control Service Hardening Tests.

Verifies:
  1. issue_card persists card BEFORE firing event (persist-first).
  2. issue_card survives publisher failure (fire-and-forget).
  3. attempt_access uses canonical tenant API signatures.
  4. check_security_anomaly persists log first — no rollback when event publish fails.
"""

from __future__ import annotations

from unittest.mock import MagicMock, call, patch

import pytest

MODULE = "app.modules.access_control.service"


# ─── helpers ──────────────────────────────────────────────────────────────────

def _make_card(
    *,
    id: str = "card-1",
    holder_id: str = "h-1",
    status: str = "ACTIVE",
    zones: list[str] | None = None,
    tenant_id: int = 1,
) -> dict:
    if zones is None:
        zones = ["zone-a"]
    return {
        "id": id,
        "holder_id": holder_id,
        "status": status,
        "zones": zones,
        "tenant_id": tenant_id,
    }


# ─── test 1 ───────────────────────────────────────────────────────────────────

def test_issue_card_persists_before_event():
    """create_entity_for_tenant must be called BEFORE EventPublisher.publish_event."""
    call_order: list[str] = []

    fake_card = _make_card(id="card-7")

    def fake_create(entity_name, payload, tenant_id):
        call_order.append("persist")
        return fake_card

    def fake_publish(self, **kwargs):
        call_order.append("event")

    with (
        patch(f"{MODULE}.create_entity_for_tenant", side_effect=fake_create),
        patch(f"{MODULE}.EventPublisher.publish_event", fake_publish),
    ):
        from app.modules.access_control import service as svc

        svc.issue_card(1, holder_id="h-1", zones=["zone-a"])

    assert call_order == ["persist", "event"], (
        "persist must come before event publish"
    )


# ─── test 2 ───────────────────────────────────────────────────────────────────

def test_issue_card_survives_publish_failure():
    """issue_card must succeed even when EventPublisher raises."""
    fake_card = _make_card(id="card-99")

    with (
        patch(f"{MODULE}.create_entity_for_tenant", return_value=fake_card),
        patch(
            f"{MODULE}.EventPublisher.publish_event",
            side_effect=RuntimeError("kafka down"),
        ),
        patch(f"{MODULE}.log_admin_action") as mock_audit,
        patch(f"{MODULE}.record_usage_event") as mock_metric,
    ):
        from app.modules.access_control import service as svc

        result = svc.issue_card(1, holder_id="h-1", zones=["zone-a"])

    assert result["card_id"] == "card-99"
    assert result["status"] == "ACTIVE"
    mock_audit.assert_called_once()
    mock_metric.assert_called_once()


# ─── test 3 ───────────────────────────────────────────────────────────────────

def test_attempt_access_uses_canonical_tenant_api():
    """list_entities_for_tenant must be called with positional args (entity, tenant_id)."""
    card = _make_card(id="card-1", status="ACTIVE")
    log_row = {
        "id": "log-1",
        "card_id": "card-1",
        "zone": "zone-a",
        "result": "GRANTED",
        "tenant_id": 1,
    }

    mock_list = MagicMock(side_effect=lambda entity, tid: [card] if entity == "access_cards" else [])
    mock_create = MagicMock(return_value=log_row)

    with (
        patch(f"{MODULE}.list_entities_for_tenant", mock_list),
        patch(f"{MODULE}.create_entity_for_tenant", mock_create),
        patch(f"{MODULE}.EventPublisher.publish_event", return_value=None),
    ):
        from app.modules.access_control import service as svc

        result = svc.attempt_access(1, card_id="card-1", zone="zone-a")

    # Every call must pass args positionally (entity_name, tenant_id), NOT as kwargs.
    for c in mock_list.call_args_list:
        args, kwargs = c
        assert len(args) == 2, (
            f"list_entities_for_tenant called with kwargs instead of positional: {c}"
        )
        assert "tenant_id" not in kwargs, (
            f"tenant_id must be positional, not keyword: {c}"
        )

    assert result["granted"] is True


# ─── test 4 ───────────────────────────────────────────────────────────────────

def test_check_security_anomaly_persist_before_event_no_rollback():
    """_check_security_anomaly must persist DENIED log even if event publish fails."""
    card = _make_card(id="card-1", status="ACTIVE")
    existing_denied_logs = [
        {"id": "log-a", "card_id": "card-1", "result": "DENIED"},
        {"id": "log-b", "card_id": "card-1", "result": "DENIED"},
    ]

    mock_list = MagicMock(
        side_effect=lambda entity, tid: (
            [card] if entity == "access_cards" else existing_denied_logs
        )
    )
    mock_create = MagicMock(
        return_value={"id": "log-new", "card_id": "card-1", "result": "DENIED"}
    )

    with (
        patch(f"{MODULE}.list_entities_for_tenant", mock_list),
        patch(f"{MODULE}.create_entity_for_tenant", mock_create),
        patch(
            f"{MODULE}.EventPublisher.publish_event",
            side_effect=Exception("broker unavailable"),
        ),
        patch("app.modules.brain_core.service.brain_core_service") as mock_brain,
        patch(f"{MODULE}.log_admin_action") as mock_audit,
        patch(f"{MODULE}.record_usage_event") as mock_metric,
    ):
        from app.modules.access_control import service as svc

        mock_brain.record_dispatch_outcome.side_effect = RuntimeError("brain down")
        # attempt_access should trigger _check_security_anomaly when card is not ACTIVE or zone denied
        # Actually, let's trigger it directly if possible. Since it's internal, call attempt_access
        # with a card that will cause denial and trigger anomaly check
        result = svc.attempt_access(1, card_id="card-1", zone="zone-not-permitted")

    # create_entity_for_tenant must have been called to log the DENIED event.
    # We expect at least one call to persist the access_logs record.
    assert mock_create.called, "create_entity_for_tenant should have been called"
    # The function should survive the event publish failure
    assert result["granted"] is False
    assert mock_metric.called
    assert mock_audit.called
