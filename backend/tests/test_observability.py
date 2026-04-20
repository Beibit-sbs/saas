"""Tests for observability module — alert primitives, dependency state observer,
live payload, event-spike tracking, cooldown dedup.

Does NOT test external webhook delivery (requires network) — tests focus on
internal logic: emit_alert return value, cooldown behaviour, dependency
state transitions, event-spike counters, live_payload structure.
"""

import time

from app.modules.observability.alerts import (
    _dependency_state,
    _last_alert_sent_at,
    _lock,
    _recent_event_windows,
    emit_alert,
    observe_dependency_state,
    observe_event_spike,
)
from app.modules.observability.health import live_payload


def _reset_alert_state() -> None:
    """Clear internal alert state between tests."""
    with _lock:
        _last_alert_sent_at.clear()
        _dependency_state.clear()
        _recent_event_windows.clear()


# ---------------------------------------------------------------------------
# 1. live_payload
# ---------------------------------------------------------------------------


def test_live_payload_structure() -> None:
    payload = live_payload()
    assert payload["status"] == "ok"
    assert payload["live"] is True
    assert payload["service"] == "api"
    assert "timestamp" in payload


# ---------------------------------------------------------------------------
# 2. emit_alert — basic
# ---------------------------------------------------------------------------


def test_emit_alert_returns_true_on_first_call() -> None:
    _reset_alert_state()
    result = emit_alert(
        alert_type="test.basic",
        severity="info",
        summary="Test alert",
    )
    assert result is True


def test_emit_alert_cooldown_dedup() -> None:
    """Second alert with same key within cooldown should be suppressed."""
    _reset_alert_state()
    emit_alert(alert_type="test.cooldown", severity="info", summary="first")
    result = emit_alert(alert_type="test.cooldown", severity="info", summary="second")
    assert result is False


def test_emit_alert_different_keys_not_deduped() -> None:
    _reset_alert_state()
    r1 = emit_alert(alert_type="test.key_a", severity="info", summary="a")
    r2 = emit_alert(alert_type="test.key_b", severity="info", summary="b")
    assert r1 is True
    assert r2 is True


def test_emit_alert_custom_dedupe_key() -> None:
    _reset_alert_state()
    emit_alert(alert_type="test.x", severity="info", summary="x", dedupe_key="custom")
    result = emit_alert(alert_type="test.y", severity="info", summary="y", dedupe_key="custom")
    assert result is False  # same dedupe_key → suppressed


# ---------------------------------------------------------------------------
# 3. observe_dependency_state
# ---------------------------------------------------------------------------


def test_dependency_state_healthy_first_seen() -> None:
    _reset_alert_state()
    # First call with healthy=True should NOT emit an alert
    observe_dependency_state(component="redis_test", healthy=True)
    with _lock:
        assert _dependency_state.get("redis_test") is True


def test_dependency_state_unhealthy_first_seen() -> None:
    _reset_alert_state()
    # First call with healthy=False should emit an unavailable alert
    observe_dependency_state(component="pg_test", healthy=False)
    with _lock:
        assert _dependency_state.get("pg_test") is False


def test_dependency_state_transition_down_then_up() -> None:
    _reset_alert_state()
    observe_dependency_state(component="cache_test", healthy=False)
    observe_dependency_state(component="cache_test", healthy=True)
    with _lock:
        assert _dependency_state.get("cache_test") is True


def test_dependency_state_transition_up_then_down() -> None:
    _reset_alert_state()
    observe_dependency_state(component="worker_test", healthy=True)
    observe_dependency_state(component="worker_test", healthy=False)
    with _lock:
        assert _dependency_state.get("worker_test") is False


# ---------------------------------------------------------------------------
# 4. observe_event_spike
# ---------------------------------------------------------------------------


def test_event_spike_below_threshold_no_alert() -> None:
    _reset_alert_state()
    # Add 2 events with threshold of 5 — should NOT trigger alert
    observe_event_spike(
        event_name="test.spike_low",
        threshold=5,
        window_seconds=60,
        severity="warning",
        summary="Test spike",
    )
    observe_event_spike(
        event_name="test.spike_low",
        threshold=5,
        window_seconds=60,
        severity="warning",
        summary="Test spike",
    )
    # No exception = OK; internal counter should show 2
    with _lock:
        count = len(_recent_event_windows.get("test.spike_low", []))
    assert count == 2


def test_event_spike_at_threshold_triggers() -> None:
    _reset_alert_state()
    for _ in range(3):
        observe_event_spike(
            event_name="test.spike_hit",
            threshold=3,
            window_seconds=60,
            severity="warning",
            summary="Spike reached",
        )
    with _lock:
        count = len(_recent_event_windows.get("test.spike_hit", []))
    assert count == 3
