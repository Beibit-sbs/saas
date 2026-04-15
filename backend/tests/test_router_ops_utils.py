"""Unit tests for pure utility functions in app.platform.router_ops.

Functions tested:
  _safe_metric_int(loader)  — wraps any callable; returns int or None on error
  _parse_iso(raw)           — ISO-8601 string → aware datetime, None on failure
  _age_seconds(raw)         — ISO-8601 string → float seconds from now, or None

All are pure (no I/O, no DB, no HTTP) and tested in isolation.
"""
from __future__ import annotations

from datetime import datetime, timezone, timedelta

from app.platform.router_ops import _age_seconds, _parse_iso, _safe_metric_int


# ---------------------------------------------------------------------------
# _safe_metric_int
# ---------------------------------------------------------------------------

class TestSafeMetricInt:
    def test_returns_int_from_callable(self):
        assert _safe_metric_int(lambda: 42) == 42

    def test_coerces_to_int(self):
        result = _safe_metric_int(lambda: "7")
        assert result == 7

    def test_returns_none_on_exception_in_loader(self):
        def boom():
            raise ValueError("no db")
        assert _safe_metric_int(boom) is None

    def test_returns_none_on_runtime_error(self):
        def also_boom():
            raise RuntimeError("fail")
        assert _safe_metric_int(also_boom) is None

    def test_zero_is_valid(self):
        assert _safe_metric_int(lambda: 0) == 0

    def test_large_value(self):
        assert _safe_metric_int(lambda: 10_000_000) == 10_000_000


# ---------------------------------------------------------------------------
# _parse_iso
# ---------------------------------------------------------------------------

class TestParseIso:
    def test_parses_valid_utc_string(self):
        result = _parse_iso("2026-01-15T12:00:00+00:00")
        assert isinstance(result, datetime)
        assert result.tzinfo is not None

    def test_parses_naive_datetime_string(self):
        result = _parse_iso("2026-01-15T12:00:00")
        assert isinstance(result, datetime)

    def test_returns_none_for_none(self):
        assert _parse_iso(None) is None

    def test_returns_none_for_empty_string(self):
        assert _parse_iso("") is None

    def test_returns_none_for_invalid_format(self):
        assert _parse_iso("not-a-date") is None

    def test_returns_none_for_garbage(self):
        assert _parse_iso("9999-99-99T99:99:99") is None


# ---------------------------------------------------------------------------
# _age_seconds
# ---------------------------------------------------------------------------

class TestAgeSeconds:
    def test_returns_none_for_none(self):
        assert _age_seconds(None) is None

    def test_returns_none_for_invalid_string(self):
        assert _age_seconds("not-a-date") is None

    def test_returns_non_negative_float_for_past_timestamp(self):
        # A timestamp 60 seconds in the past
        past = datetime.now(timezone.utc) - timedelta(seconds=60)
        raw = past.isoformat()
        result = _age_seconds(raw)
        assert result is not None
        assert isinstance(result, float)
        # Should be approximately 60 seconds, allow generous margin for test latency
        assert 0.0 <= result < 120.0

    def test_clamps_to_zero_for_future_timestamp(self):
        # A timestamp 10 seconds in the future
        future = datetime.now(timezone.utc) + timedelta(seconds=10)
        result = _age_seconds(future.isoformat())
        assert result == 0.0

    def test_recent_timestamp_is_near_zero(self):
        now_str = datetime.now(timezone.utc).isoformat()
        result = _age_seconds(now_str)
        assert result is not None
        assert 0.0 <= result < 5.0  # ample margin for CI
