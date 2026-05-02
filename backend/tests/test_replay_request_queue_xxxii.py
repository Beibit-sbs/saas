"""
Phase XXXII — Replay Escalation & Request Queue Management tests.

Tests for:
- XXXII1: Replay Request Queue API
- XXXII2: Replay Request Escalation
- XXXII3: Replay SLA & Queue Metrics
"""

import pytest
from datetime import datetime, timezone, timedelta
from app.modules.brain_core.service import brain_core_service


def _reset() -> None:
    """Reset brain_core_service state for test isolation."""
    brain_core_service._replay_request_queue = {}
    brain_core_service._replay_escalations = {}
    brain_core_service._replay_sla_metrics = {}


# ── XXXII1: Replay Request Queue API ──────────────────────────────────────


class TestReplayRequestQueueXXXII1:
    """XXXII1 tests: create_replay_request + get_replay_request_queue."""

    def setup_method(self):
        """Reset service state before each test."""
        _reset()

    def test_create_replay_request_basic(self):
        """Test creating a basic replay request."""
        request = brain_core_service.create_replay_request(
            tenant_id=1,
            signal_id="signal-123",
            decision_id="decision-456",
            requested_by="operator@example.com",
            priority="high",
            escalation_level=0,
        )

        assert request["tenant_id"] == 1
        assert request["signal_id"] == "signal-123"
        assert request["decision_id"] == "decision-456"
        assert request["requested_by"] == "operator@example.com"
        assert request["priority"] == "high"
        assert request["escalation_level"] == 0
        assert request["status"] == "pending"
        assert "request_id" in request
        assert "created_at" in request

    def test_create_replay_request_invalid_priority(self):
        """Test that invalid priority is rejected."""
        with pytest.raises(ValueError, match="priority must be"):
            brain_core_service.create_replay_request(
                tenant_id=1,
                signal_id="signal-123",
                decision_id="decision-456",
                requested_by="operator@example.com",
                priority="invalid",
            )

    def test_create_replay_request_invalid_escalation_level(self):
        """Test that negative escalation level is rejected."""
        with pytest.raises(ValueError, match="escalation_level must be >= 0"):
            brain_core_service.create_replay_request(
                tenant_id=1,
                signal_id="signal-123",
                decision_id="decision-456",
                requested_by="operator@example.com",
                escalation_level=-1,
            )

    def test_get_replay_request_queue_empty(self):
        """Test getting queue for tenant with no requests."""
        queue = brain_core_service.get_replay_request_queue(tenant_id=999)
        assert queue == []

    def test_get_replay_request_queue_filters_by_tenant(self):
        """Test that queue is filtered by tenant."""
        brain_core_service.create_replay_request(
            tenant_id=1,
            signal_id="signal-1",
            decision_id="decision-1",
            requested_by="op1@example.com",
        )
        brain_core_service.create_replay_request(
            tenant_id=2,
            signal_id="signal-2",
            decision_id="decision-2",
            requested_by="op2@example.com",
        )

        queue_t1 = brain_core_service.get_replay_request_queue(tenant_id=1)
        queue_t2 = brain_core_service.get_replay_request_queue(tenant_id=2)

        assert len(queue_t1) == 1
        assert len(queue_t2) == 1
        assert queue_t1[0]["tenant_id"] == 1
        assert queue_t2[0]["tenant_id"] == 2

    def test_get_replay_request_queue_filters_by_priority(self):
        """Test filtering by priority."""
        brain_core_service.create_replay_request(
            tenant_id=1,
            signal_id="s1",
            decision_id="d1",
            requested_by="op@example.com",
            priority="high",
        )
        brain_core_service.create_replay_request(
            tenant_id=1,
            signal_id="s2",
            decision_id="d2",
            requested_by="op@example.com",
            priority="low",
        )

        queue_high = brain_core_service.get_replay_request_queue(tenant_id=1, priority="high")
        queue_low = brain_core_service.get_replay_request_queue(tenant_id=1, priority="low")

        assert len(queue_high) == 1
        assert len(queue_low) == 1
        assert queue_high[0]["priority"] == "high"
        assert queue_low[0]["priority"] == "low"

    def test_get_replay_request_queue_sorts_by_priority(self):
        """Test that queue is sorted by priority (urgent > high > normal > low)."""
        # Create requests in reverse order
        brain_core_service.create_replay_request(
            tenant_id=1,
            signal_id="s1",
            decision_id="d1",
            requested_by="op@example.com",
            priority="low",
        )
        brain_core_service.create_replay_request(
            tenant_id=1,
            signal_id="s2",
            decision_id="d2",
            requested_by="op@example.com",
            priority="urgent",
        )
        brain_core_service.create_replay_request(
            tenant_id=1,
            signal_id="s3",
            decision_id="d3",
            requested_by="op@example.com",
            priority="high",
        )

        queue = brain_core_service.get_replay_request_queue(tenant_id=1)

        assert len(queue) == 3
        assert queue[0]["priority"] == "urgent"
        assert queue[1]["priority"] == "high"
        assert queue[2]["priority"] == "low"


# ── XXXII2: Replay Request Escalation ──────────────────────────────────────


class TestReplayRequestEscalationXXXII2:
    """XXXII2 tests: escalate_replay_request + get_escalation_history."""

    def setup_method(self):
        """Reset service state before each test."""
        _reset()

    def test_escalate_replay_request_basic(self):
        """Test escalating a replay request."""
        request = brain_core_service.create_replay_request(
            tenant_id=1,
            signal_id="signal-123",
            decision_id="decision-456",
            requested_by="operator@example.com",
            escalation_level=0,
        )

        result = brain_core_service.escalate_replay_request(
            request["request_id"],
            reason="requires_supervisor_approval",
            target_level=1,
        )

        assert result["request_id"] == request["request_id"]
        assert result["escalation"]["from_level"] == 0
        assert result["escalation"]["to_level"] == 1
        assert result["escalation"]["reason"] == "requires_supervisor_approval"
        assert result["updated_request"]["escalation_level"] == 1

    def test_escalate_replay_request_invalid_target_level(self):
        """Test that target_level must be greater than current level."""
        request = brain_core_service.create_replay_request(
            tenant_id=1,
            signal_id="signal-123",
            decision_id="decision-456",
            requested_by="operator@example.com",
            escalation_level=2,
        )

        # Should fail because 2 is not > 2
        with pytest.raises(ValueError, match="target_level.*must be"):
            brain_core_service.escalate_replay_request(
                request["request_id"],
                reason="test",
                target_level=2,
            )

    def test_escalate_replay_request_not_found(self):
        """Test escalating a non-existent request."""
        with pytest.raises(ValueError, match="replay request.*not found"):
            brain_core_service.escalate_replay_request(
                "invalid-request-id",
                reason="test",
                target_level=1,
            )

    def test_get_escalation_history_empty(self):
        """Test getting escalation history for request with no escalations."""
        request = brain_core_service.create_replay_request(
            tenant_id=1,
            signal_id="signal-123",
            decision_id="decision-456",
            requested_by="operator@example.com",
        )

        history = brain_core_service.get_escalation_history(request["request_id"])
        assert history == []

    def test_get_escalation_history_multiple_escalations(self):
        """Test getting history with multiple escalations."""
        request = brain_core_service.create_replay_request(
            tenant_id=1,
            signal_id="signal-123",
            decision_id="decision-456",
            requested_by="operator@example.com",
            escalation_level=0,
        )
        request_id = request["request_id"]

        # Escalate twice
        brain_core_service.escalate_replay_request(request_id, reason="level_1", target_level=1)
        brain_core_service.escalate_replay_request(request_id, reason="level_2", target_level=2)

        history = brain_core_service.get_escalation_history(request_id)

        assert len(history) == 2
        assert history[0]["reason"] == "level_1"
        assert history[0]["to_level"] == 1
        assert history[1]["reason"] == "level_2"
        assert history[1]["to_level"] == 2


# ── XXXII3: Replay SLA & Queue Metrics ────────────────────────────────────


class TestReplayQueueMetricsXXXII3:
    """XXXII3 tests: get_replay_queue_metrics."""

    def setup_method(self):
        """Reset service state before each test."""
        _reset()

    def test_get_replay_queue_metrics_empty_queue(self):
        """Test metrics for tenant with no requests."""
        metrics = brain_core_service.get_replay_queue_metrics(tenant_id=999)

        assert metrics["tenant_id"] == 999
        assert metrics["total_requests"] == 0
        assert metrics["pending_requests"] == 0
        assert metrics["resolved_requests"] == 0
        assert metrics["queue_by_priority"] == {"urgent": 0, "high": 0, "normal": 0, "low": 0}
        assert metrics["total_escalations"] == 0

    def test_get_replay_queue_metrics_with_requests(self):
        """Test metrics calculation with multiple requests."""
        brain_core_service.create_replay_request(
            tenant_id=1,
            signal_id="s1",
            decision_id="d1",
            requested_by="op@example.com",
            priority="high",
        )
        brain_core_service.create_replay_request(
            tenant_id=1,
            signal_id="s2",
            decision_id="d2",
            requested_by="op@example.com",
            priority="normal",
        )
        brain_core_service.create_replay_request(
            tenant_id=1,
            signal_id="s3",
            decision_id="d3",
            requested_by="op@example.com",
            priority="low",
        )

        metrics = brain_core_service.get_replay_queue_metrics(tenant_id=1)

        assert metrics["total_requests"] == 3
        assert metrics["pending_requests"] == 3
        assert metrics["queue_by_priority"]["high"] == 1
        assert metrics["queue_by_priority"]["normal"] == 1
        assert metrics["queue_by_priority"]["low"] == 1

    def test_get_replay_queue_metrics_with_escalations(self):
        """Test metrics with escalations."""
        request = brain_core_service.create_replay_request(
            tenant_id=1,
            signal_id="signal-123",
            decision_id="decision-456",
            requested_by="operator@example.com",
            escalation_level=0,
        )

        brain_core_service.escalate_replay_request(
            request["request_id"],
            reason="test",
            target_level=1,
        )

        metrics = brain_core_service.get_replay_queue_metrics(tenant_id=1)

        assert metrics["total_requests"] == 1
        assert metrics["total_escalations"] == 1

    def test_get_replay_queue_metrics_measured_at(self):
        """Test that metrics include measured_at timestamp."""
        brain_core_service.create_replay_request(
            tenant_id=1,
            signal_id="s1",
            decision_id="d1",
            requested_by="op@example.com",
        )

        metrics = brain_core_service.get_replay_queue_metrics(tenant_id=1)

        assert "measured_at" in metrics
        # Check that timestamp is recent (within last minute)
        measured = datetime.fromisoformat(metrics["measured_at"])
        now = datetime.now(timezone.utc)
        delta = (now - measured).total_seconds()
        assert 0 <= delta <= 60
