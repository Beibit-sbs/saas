from __future__ import annotations

from collections import defaultdict, deque
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from threading import Lock
import os
import time


def is_perf_profile_enabled() -> bool:
    return str(os.getenv("PERF_PROFILE_ENABLED", "false")).strip().lower() in {"1", "true", "yes", "on"}


@dataclass
class _RequestProfile:
    method: str
    path: str
    started_at: float
    segments_ms: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    counters: dict[str, int] = field(default_factory=lambda: defaultdict(int))


_request_profile_var: ContextVar[_RequestProfile | None] = ContextVar("perf_request_profile", default=None)
_lock = Lock()
_aggregate_segment_ms: dict[str, float] = defaultdict(float)
_aggregate_segment_count: dict[str, int] = defaultdict(int)
_aggregate_counters: dict[str, int] = defaultdict(int)
_request_latencies_ms: deque[float] = deque(maxlen=2000)
_request_errors = 0
_request_count = 0
_db_top_queries_ms: dict[str, float] = defaultdict(float)


def reset_perf_profile() -> None:
    with _lock:
        _aggregate_segment_ms.clear()
        _aggregate_segment_count.clear()
        _aggregate_counters.clear()
        _request_latencies_ms.clear()
        _db_top_queries_ms.clear()
        global _request_errors, _request_count
        _request_errors = 0
        _request_count = 0


def begin_request_profile(method: str, path: str) -> None:
    if not is_perf_profile_enabled():
        return
    _request_profile_var.set(_RequestProfile(method=method.upper(), path=path, started_at=time.perf_counter()))


def finish_request_profile(status_code: int, latency_ms: float) -> None:
    if not is_perf_profile_enabled():
        return
    profile = _request_profile_var.get()
    _request_profile_var.set(None)
    if profile is None:
        return

    with _lock:
        global _request_count, _request_errors
        _request_count += 1
        if int(status_code) >= 400:
            _request_errors += 1
        _request_latencies_ms.append(float(latency_ms))

        for name, duration_ms in profile.segments_ms.items():
            _aggregate_segment_ms[name] += float(duration_ms)
            _aggregate_segment_count[name] += 1

        for name, value in profile.counters.items():
            _aggregate_counters[name] += int(value)


@contextmanager
def perf_segment(name: str):
    if not is_perf_profile_enabled():
        yield
        return
    profile = _request_profile_var.get()
    if profile is None:
        yield
        return

    started = time.perf_counter()
    try:
        yield
    finally:
        elapsed_ms = (time.perf_counter() - started) * 1000.0
        profile.segments_ms[str(name)] += float(elapsed_ms)


def add_perf_counter(name: str, delta: int = 1) -> None:
    if not is_perf_profile_enabled():
        return
    profile = _request_profile_var.get()
    if profile is None:
        return
    profile.counters[str(name)] += int(delta)


def observe_db_query(statement: str, elapsed_ms: float) -> None:
    if not is_perf_profile_enabled():
        return
    add_perf_counter("db.query.count", 1)
    profile = _request_profile_var.get()
    if profile is not None:
        profile.segments_ms["db.query.total"] += float(elapsed_ms)

    normalized = " ".join(str(statement).strip().split())
    if len(normalized) > 140:
        normalized = normalized[:140]
    with _lock:
        _db_top_queries_ms[normalized] += float(elapsed_ms)


def observe_redis_call(elapsed_ms: float) -> None:
    if not is_perf_profile_enabled():
        return
    add_perf_counter("redis.call.count", 1)
    profile = _request_profile_var.get()
    if profile is not None:
        profile.segments_ms["redis.call.total"] += float(elapsed_ms)


def get_perf_profile_summary(top_n: int = 5) -> dict[str, object]:
    with _lock:
        segment_rows = []
        for name, total_ms in _aggregate_segment_ms.items():
            count = int(_aggregate_segment_count.get(name, 0))
            avg_ms = (total_ms / count) if count > 0 else 0.0
            segment_rows.append(
                {
                    "segment": name,
                    "total_ms": round(float(total_ms), 2),
                    "avg_ms": round(float(avg_ms), 3),
                    "count": count,
                }
            )
        segment_rows.sort(key=lambda item: item["total_ms"], reverse=True)

        top_queries = [
            {"query": query, "total_ms": round(float(total_ms), 2)}
            for query, total_ms in sorted(_db_top_queries_ms.items(), key=lambda item: item[1], reverse=True)[:top_n]
        ]

        request_count = int(_request_count)
        request_errors = int(_request_errors)
        error_rate = (request_errors / request_count) if request_count > 0 else 0.0
        latency = sorted(float(item) for item in _request_latencies_ms)
        p95_index = int(0.95 * (len(latency) - 1)) if latency else 0
        p99_index = int(0.99 * (len(latency) - 1)) if latency else 0

        return {
            "enabled": is_perf_profile_enabled(),
            "requests": request_count,
            "errors": request_errors,
            "error_rate": round(error_rate, 6),
            "latency_ms": {
                "p95": round(latency[p95_index], 2) if latency else 0.0,
                "p99": round(latency[p99_index], 2) if latency else 0.0,
            },
            "top_segments": segment_rows[:top_n],
            "counters": dict(_aggregate_counters),
            "top_queries": top_queries,
        }


def install_redis_profiler() -> None:
    if not is_perf_profile_enabled():
        return
    try:
        import redis
    except Exception:
        return

    redis_cls = getattr(redis, "Redis", None)
    if redis_cls is None:
        return
    if getattr(redis_cls, "_perf_profile_wrapped", False):
        return

    original_execute_command = redis_cls.execute_command

    def wrapped_execute_command(self, *args, **kwargs):
        started = time.perf_counter()
        try:
            return original_execute_command(self, *args, **kwargs)
        finally:
            observe_redis_call((time.perf_counter() - started) * 1000.0)

    redis_cls.execute_command = wrapped_execute_command
    setattr(redis_cls, "_perf_profile_wrapped", True)


def install_sqlalchemy_profiler(engine) -> None:
    if not is_perf_profile_enabled() or engine is None:
        return
    if getattr(engine, "_perf_profile_wrapped", False):
        return

    try:
        from sqlalchemy import event
    except Exception:
        return

    @event.listens_for(engine, "before_cursor_execute")
    def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        context._perf_started_at = time.perf_counter()

    @event.listens_for(engine, "after_cursor_execute")
    def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        started = getattr(context, "_perf_started_at", None)
        if started is None:
            return
        observe_db_query(str(statement), (time.perf_counter() - started) * 1000.0)

    setattr(engine, "_perf_profile_wrapped", True)