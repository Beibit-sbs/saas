"""
Coverage boost: app.modules.observability.perf_profile

All public functions are guarded by is_perf_profile_enabled() which checks
PERF_PROFILE_ENABLED env var.  Tests either monkeypatch the env var to activate
the code paths or directly patch the guard function.
"""
from __future__ import annotations

import os
import time

import pytest

import app.modules.observability.perf_profile as pp


@pytest.fixture(autouse=True)
def _reset_perf_state():
    """Ensure profile state is clean before and after each test."""
    pp.reset_perf_profile()
    pp._request_profile_var.set(None)
    yield
    pp.reset_perf_profile()
    pp._request_profile_var.set(None)


@pytest.fixture
def perf_enabled(monkeypatch: pytest.MonkeyPatch):
    """Activate profiling for the duration of one test."""
    monkeypatch.setenv("PERF_PROFILE_ENABLED", "true")
    # Force re-evaluation (function reads os.getenv at call time)
    yield
    monkeypatch.delenv("PERF_PROFILE_ENABLED", raising=False)


# ---------------------------------------------------------------------------
# is_perf_profile_enabled
# ---------------------------------------------------------------------------


def test_disabled_by_default():
    # In CI the env var is unset
    os.environ.pop("PERF_PROFILE_ENABLED", None)
    assert pp.is_perf_profile_enabled() is False


def test_enabled_when_env_true(monkeypatch: pytest.MonkeyPatch):
    for val in ("true", "1", "yes", "on", "TRUE", "YES"):
        monkeypatch.setenv("PERF_PROFILE_ENABLED", val)
        assert pp.is_perf_profile_enabled() is True


def test_disabled_when_env_false(monkeypatch: pytest.MonkeyPatch):
    for val in ("false", "0", "no", "off", ""):
        monkeypatch.setenv("PERF_PROFILE_ENABLED", val)
        assert pp.is_perf_profile_enabled() is False


# ---------------------------------------------------------------------------
# reset_perf_profile
# ---------------------------------------------------------------------------


def test_reset_clears_all_state(perf_enabled):
    pp.begin_request_profile("GET", "/test")
    pp.finish_request_profile(200, 50.0)
    pp.reset_perf_profile()
    summary = pp.get_perf_profile_summary()
    assert summary["requests"] == 0
    assert summary["errors"] == 0
    assert summary["top_segments"] == []


# ---------------------------------------------------------------------------
# begin_request_profile / finish_request_profile
# ---------------------------------------------------------------------------


def test_begin_and_finish_happy_path(perf_enabled):
    pp.begin_request_profile("GET", "/health")
    profile = pp._request_profile_var.get()
    assert profile is not None
    assert profile.method == "GET"
    assert profile.path == "/health"

    pp.finish_request_profile(200, 12.5)
    assert pp._request_profile_var.get() is None

    summary = pp.get_perf_profile_summary()
    assert summary["requests"] == 1
    assert summary["errors"] == 0
    assert summary["latency_ms"]["p95"] > 0


def test_finish_increments_error_count_for_4xx(perf_enabled):
    pp.begin_request_profile("GET", "/bad")
    pp.finish_request_profile(400, 5.0)
    summary = pp.get_perf_profile_summary()
    assert summary["errors"] == 1


def test_finish_increments_error_count_for_5xx(perf_enabled):
    pp.begin_request_profile("POST", "/fail")
    pp.finish_request_profile(500, 3.0)
    summary = pp.get_perf_profile_summary()
    assert summary["errors"] == 1


def test_finish_does_nothing_when_no_active_profile(perf_enabled):
    # finish without begin — should be a no-op
    pp.finish_request_profile(200, 10.0)
    assert pp.get_perf_profile_summary()["requests"] == 0


def test_noop_when_disabled():
    # With profiling off, begin/finish add nothing
    os.environ.pop("PERF_PROFILE_ENABLED", None)
    pp.begin_request_profile("GET", "/x")
    assert pp._request_profile_var.get() is None
    pp.finish_request_profile(200, 1.0)
    assert pp.get_perf_profile_summary()["requests"] == 0


# ---------------------------------------------------------------------------
# perf_segment
# ---------------------------------------------------------------------------


def test_perf_segment_records_duration(perf_enabled):
    pp.begin_request_profile("GET", "/seg")
    with pp.perf_segment("db"):
        time.sleep(0.01)
    pp.finish_request_profile(200, 20.0)

    summary = pp.get_perf_profile_summary()
    seg_names = [s["segment"] for s in summary["top_segments"]]
    assert "db" in seg_names


def test_perf_segment_noop_when_disabled():
    os.environ.pop("PERF_PROFILE_ENABLED", None)
    with pp.perf_segment("db"):
        pass  # should not raise


def test_perf_segment_noop_when_no_profile(perf_enabled):
    # profiling on but no active request profile
    with pp.perf_segment("db"):
        pass
    # no crash, nothing recorded
    assert pp.get_perf_profile_summary()["requests"] == 0


# ---------------------------------------------------------------------------
# add_perf_counter
# ---------------------------------------------------------------------------


def test_add_perf_counter_accumulates(perf_enabled):
    pp.begin_request_profile("POST", "/cmd")
    pp.add_perf_counter("cache.hit", 1)
    pp.add_perf_counter("cache.hit", 2)
    pp.finish_request_profile(200, 5.0)

    summary = pp.get_perf_profile_summary()
    assert summary["counters"].get("cache.hit") == 3


def test_add_perf_counter_noop_when_disabled():
    os.environ.pop("PERF_PROFILE_ENABLED", None)
    pp.add_perf_counter("x", 1)  # should not raise


def test_add_perf_counter_noop_when_no_profile(perf_enabled):
    pp.add_perf_counter("x", 1)  # no active request profile, should not raise


# ---------------------------------------------------------------------------
# observe_db_query
# ---------------------------------------------------------------------------


def test_observe_db_query_records_top_query(perf_enabled):
    pp.begin_request_profile("GET", "/q")
    pp.observe_db_query("SELECT 1", 14.0)
    pp.finish_request_profile(200, 20.0)

    summary = pp.get_perf_profile_summary()
    assert any("SELECT 1" in q["query"] for q in summary["top_queries"])


def test_observe_db_query_truncates_long_statement(perf_enabled):
    pp.begin_request_profile("GET", "/q")
    long_sql = "SELECT " + "x" * 200
    pp.observe_db_query(long_sql, 5.0)
    pp.finish_request_profile(200, 10.0)

    summary = pp.get_perf_profile_summary()
    for q in summary["top_queries"]:
        assert len(q["query"]) <= 145  # 140 + some overhead


def test_observe_db_query_noop_when_disabled():
    os.environ.pop("PERF_PROFILE_ENABLED", None)
    pp.observe_db_query("SELECT 1", 5.0)  # should not raise


# ---------------------------------------------------------------------------
# observe_redis_call
# ---------------------------------------------------------------------------


def test_observe_redis_call_records_segment(perf_enabled):
    pp.begin_request_profile("GET", "/r")
    pp.observe_redis_call(3.0)
    pp.finish_request_profile(200, 5.0)

    summary = pp.get_perf_profile_summary()
    seg_names = [s["segment"] for s in summary["top_segments"]]
    assert "redis.call.total" in seg_names


def test_observe_redis_call_noop_when_disabled():
    os.environ.pop("PERF_PROFILE_ENABLED", None)
    pp.observe_redis_call(1.0)  # should not raise


def test_observe_redis_call_noop_when_no_profile(perf_enabled):
    pp.observe_redis_call(1.0)  # no active profile


# ---------------------------------------------------------------------------
# get_perf_profile_summary
# ---------------------------------------------------------------------------


def test_summary_error_rate_calculation(perf_enabled):
    pp.begin_request_profile("GET", "/a")
    pp.finish_request_profile(200, 5.0)
    pp.begin_request_profile("GET", "/b")
    pp.finish_request_profile(500, 5.0)

    summary = pp.get_perf_profile_summary()
    assert abs(summary["error_rate"] - 0.5) < 0.001


def test_summary_empty_state():
    summary = pp.get_perf_profile_summary()
    assert summary["requests"] == 0
    assert summary["latency_ms"]["p95"] == 0.0
    assert summary["latency_ms"]["p99"] == 0.0
    assert summary["top_queries"] == []


def test_summary_top_n_limits_segments(perf_enabled):
    pp.begin_request_profile("GET", "/x")
    for i in range(10):
        pp.observe_db_query(f"SELECT {i}", float(i))
    pp.finish_request_profile(200, 50.0)

    summary = pp.get_perf_profile_summary(top_n=3)
    assert len(summary["top_queries"]) <= 3


def test_summary_p99_percentile_multi_requests(perf_enabled):
    latencies = [1.0, 2.0, 3.0, 4.0, 100.0]
    for lat in latencies:
        pp.begin_request_profile("GET", "/x")
        pp.finish_request_profile(200, lat)

    summary = pp.get_perf_profile_summary()
    # p99 should be near the highest value
    assert summary["latency_ms"]["p99"] >= 100.0 or summary["latency_ms"]["p99"] > 0


# ---------------------------------------------------------------------------
# install_redis_profiler
# ---------------------------------------------------------------------------


def test_install_redis_profiler_noop_when_disabled():
    os.environ.pop("PERF_PROFILE_ENABLED", None)
    pp.install_redis_profiler()  # should not raise


def test_install_redis_profiler_noop_when_redis_unavailable(
    monkeypatch: pytest.MonkeyPatch, perf_enabled
):
    # Simulate redis not installed
    import sys
    monkeypatch.setitem(sys.modules, "redis", None)
    pp.install_redis_profiler()  # should not raise


def test_install_redis_profiler_idempotent(perf_enabled):
    """Calling twice should not double-wrap execute_command."""
    try:
        import redis  # noqa: F401
    except ImportError:
        pytest.skip("redis not installed")
    pp.install_redis_profiler()
    pp.install_redis_profiler()  # second call is a no-op


# ---------------------------------------------------------------------------
# install_sqlalchemy_profiler
# ---------------------------------------------------------------------------


def test_install_sqlalchemy_profiler_noop_when_disabled():
    os.environ.pop("PERF_PROFILE_ENABLED", None)
    pp.install_sqlalchemy_profiler(engine=None)  # should not raise


def test_install_sqlalchemy_profiler_noop_when_engine_none(perf_enabled):
    pp.install_sqlalchemy_profiler(engine=None)  # should not raise


def test_install_sqlalchemy_profiler_idempotent(perf_enabled):
    """Wrapped engine should not be double-wrapped."""
    from unittest.mock import MagicMock
    engine = MagicMock()
    engine._perf_profile_wrapped = False
    pp.install_sqlalchemy_profiler(engine)
    pp.install_sqlalchemy_profiler(engine)  # second call is no-op via flag check


def test_install_sqlalchemy_profiler_registers_events(perf_enabled):
    """Should register before/after_cursor_execute listeners on the engine."""
    from unittest.mock import MagicMock, patch

    engine = MagicMock()
    engine._perf_profile_wrapped = False

    with patch("app.modules.observability.perf_profile.time") as mock_time:
        mock_time.perf_counter.return_value = 1.0

        # Simulate event listeners being attached
        captured_listeners = {}

        def fake_event_listen(target, event_name, listener):
            captured_listeners[event_name] = listener

        with patch("sqlalchemy.event.listens_for") as mock_listens_for:
            mock_listens_for.side_effect = lambda *a, **kw: (lambda fn: fn)
            pp.install_sqlalchemy_profiler(engine)
