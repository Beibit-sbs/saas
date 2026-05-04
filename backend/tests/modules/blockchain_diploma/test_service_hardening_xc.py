"""
XC — Blockchain Diploma Service Hardening Tests.

Verifies:
  1. issue_diploma persists diploma BEFORE firing event (persist-first).
  2. issue_diploma survives publisher failure (fire-and-forget).
  3. verify_diploma uses canonical tenant API signatures.
  4. revoke_diploma persists first — no rollback when event publish fails.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

MODULE = "app.modules.blockchain_diploma.service"


# ─── test 1 ───────────────────────────────────────────────────────────────────

def test_issue_diploma_persists_before_event():
    """create_entity_for_tenant must be called BEFORE EventPublisher.publish_event."""
    call_order: list[str] = []

    fake_diploma = {
        "id": 42,
        "student_id": 1,
        "degree": "BS",
        "issued_year": 2024,
        "status": "issued",
        "tx_hash": "0x123",
        "certificate_hash": "abc123",
    }

    def fake_create(entity_name, payload, tenant_id):
        call_order.append("persist")
        return fake_diploma

    def fake_publish(self, **kwargs):
        call_order.append("event")

    with (
        patch(f"{MODULE}.create_entity_for_tenant", side_effect=fake_create),
        patch(f"{MODULE}.EventPublisher.publish_event", fake_publish),
    ):
        from app.modules.blockchain_diploma import service as svc

        svc.issue_diploma(
            student_id=1,
            degree="BS",
            specialization="AI",
            issued_year=2024,
            gpa=3.8,
            tenant_id=1,
        )

    assert call_order == ["persist", "event"], (
        "persist must come before event publish"
    )


# ─── test 2 ───────────────────────────────────────────────────────────────────

def test_issue_diploma_survives_publish_failure():
    """issue_diploma must succeed even when EventPublisher raises."""
    fake_diploma = {
        "id": 99,
        "student_id": 1,
        "degree": "MS",
        "issued_year": 2024,
        "status": "issued",
        "tx_hash": "0x456",
        "certificate_hash": "def456",
    }

    with (
        patch(f"{MODULE}.create_entity_for_tenant", return_value=fake_diploma),
        patch(
            f"{MODULE}.EventPublisher.publish_event",
            side_effect=RuntimeError("kafka down"),
        ),
        patch("app.modules.brain_core.service.brain_core_service") as mock_brain,
        patch(f"{MODULE}.log_admin_action") as mock_audit,
        patch(f"{MODULE}.record_usage_event") as mock_metric,
    ):
        from app.modules.blockchain_diploma import service as svc

        mock_brain.record_dispatch_outcome.side_effect = RuntimeError("brain down")
        result = svc.issue_diploma(
            student_id=1,
            degree="MS",
            specialization="AI",
            issued_year=2024,
            gpa=3.8,
            tenant_id=1,
        )

    assert result.diploma_id == 99
    assert result.status == "issued"
    mock_audit.assert_called_once()
    mock_metric.assert_called_once()


# ─── test 3 ───────────────────────────────────────────────────────────────────

def test_verify_diploma_uses_canonical_tenant_api():
    """list_entities_for_tenant must be called with positional args (entity, tenant_id)."""
    diploma = {
        "id": 1,
        "student_id": 1,
        "degree": "BS",
        "issued_year": 2024,
        "status": "issued",
        "certificate_hash": "abc123",
        "tx_hash": "0x123",
    }
    verification_record = {
        "id": 77,
        "certificate_hash": "abc123",
        "diploma_id": 1,
        "result": "valid",
        "verifier_id": 2,
    }

    mock_list = MagicMock(return_value=[diploma])
    mock_create = MagicMock(return_value=verification_record)

    with (
        patch(f"{MODULE}.list_entities_for_tenant", mock_list),
        patch(f"{MODULE}.create_entity_for_tenant", mock_create),
        patch(f"{MODULE}.EventPublisher.publish_event", return_value=None),
    ):
        from app.modules.blockchain_diploma import service as svc

        result = svc.verify_diploma(
            certificate_hash="abc123", verifier_id=2, tenant_id=1
        )

    # Every call must pass args positionally (entity_name, tenant_id), NOT as kwargs.
    for c in mock_list.call_args_list:
        args, kwargs = c
        assert len(args) == 2, (
            f"list_entities_for_tenant called with kwargs instead of positional: {c}"
        )
        assert "tenant_id" not in kwargs, (
            f"tenant_id must be positional, not keyword: {c}"
        )

    assert result.result == "valid"


# ─── test 4 ───────────────────────────────────────────────────────────────────

def test_revoke_diploma_persist_before_event_no_rollback():
    """revoke_diploma must persist updates even if event publish fails."""
    existing_diploma = {
        "id": 5,
        "student_id": 1,
        "degree": "BS",
        "issued_year": 2024,
        "status": "issued",
        "certificate_hash": "abc123",
        "tx_hash": "0x789",
    }

    mock_list = MagicMock(return_value=[existing_diploma])
    mock_update = MagicMock()
    mock_create = MagicMock(
        return_value={"id": 11, "diploma_id": 5, "reason": "policy change"}
    )

    with (
        patch(f"{MODULE}.list_entities_for_tenant", mock_list),
        patch(f"{MODULE}.update_entity_for_tenant", mock_update),
        patch(f"{MODULE}.create_entity_for_tenant", mock_create),
        patch(
            f"{MODULE}.EventPublisher.publish_event",
            side_effect=Exception("broker unavailable"),
        ),
        patch(f"{MODULE}.log_admin_action") as mock_audit,
        patch(f"{MODULE}.record_usage_event") as mock_metric,
    ):
        from app.modules.blockchain_diploma import service as svc

        result = svc.revoke_diploma(diploma_id=5, reason="policy change", tenant_id=1)

    # update_entity_for_tenant must have been called with positional args.
    mock_update.assert_called_once()
    args, kwargs = mock_update.call_args
    assert len(args) == 4, "update_entity_for_tenant must use positional args"
    # Result must reflect the revocation.
    assert result.status == "revoked"
    mock_audit.assert_called_once()
    mock_metric.assert_called_once()
