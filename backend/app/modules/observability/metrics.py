"""In-process Prometheus-compatible metrics.

No external library required. Emits text/plain exposition format.
"""
from __future__ import annotations

from collections import defaultdict
from collections import deque
from threading import Lock
import time

from app.modules.observability.security_signals import snapshot_security_metrics

_lock = Lock()

# http_requests_total{method, path, status}
_req_total: dict[tuple[str, str, str], int] = defaultdict(int)

# http_request_duration_seconds — stored as (count, sum_seconds)
_req_duration: dict[tuple[str, str], tuple[int, float]] = defaultdict(lambda: (0, 0.0))

# http_request_duration_seconds_bucket{method,path,le}
_req_duration_bucket: dict[tuple[str, str, str], int] = defaultdict(int)

# http_requests_status_class_total{method,path,status_class}
_req_status_class_total: dict[tuple[str, str, str], int] = defaultdict(int)

# Optional domain counters (safe defaults, increment only where integrated)
_workflow_executions_total = 0
_grade_submissions_total = 0
_scheduling_conflicts_total = 0
_recent_request_samples: deque[tuple[float, int, float]] = deque(maxlen=5000)

_LATENCY_BUCKETS = (0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)


def _status_class(status: int) -> str:
    return f"{max(0, int(status)) // 100}xx"


def _bucket_label(value: float) -> str:
    if float(value).is_integer():
        return f"{int(value)}"
    return f"{value}"


def record_request(method: str, path: str, status: int, duration: float) -> None:
    key_total = (method.upper(), path, str(status))
    key_dur = (method.upper(), path)
    status_key = (method.upper(), path, _status_class(status))
    with _lock:
        _req_total[key_total] += 1
        old_count, old_sum = _req_duration[key_dur]
        _req_duration[key_dur] = (old_count + 1, old_sum + duration)
        _req_status_class_total[status_key] += 1
        _recent_request_samples.append((time.time(), int(status), float(duration)))
        for bound in _LATENCY_BUCKETS:
            if duration <= bound:
                _req_duration_bucket[(method.upper(), path, _bucket_label(bound))] += 1
        _req_duration_bucket[(method.upper(), path, "+Inf")] += 1


def _percentile(sorted_values: list[float], percentile: float) -> float:
    if not sorted_values:
        return 0.0
    if len(sorted_values) == 1:
        return sorted_values[0]
    index = max(0, min(len(sorted_values) - 1, round((len(sorted_values) - 1) * percentile)))
    return sorted_values[index]


def snapshot_latency_metrics() -> dict[str, float | int]:
    now = time.time()
    with _lock:
        samples = list(_recent_request_samples)
    recent_minute = [item for item in samples if now - item[0] <= 60]
    durations_ms = sorted(round(item[2] * 1000, 2) for item in recent_minute)
    count_4xx = sum(1 for _, status, _ in recent_minute if 400 <= status < 500)
    count_5xx = sum(1 for _, status, _ in recent_minute if 500 <= status < 600)
    return {
        "p50_latency_ms": round(_percentile(durations_ms, 0.50), 2),
        "p95_latency_ms": round(_percentile(durations_ms, 0.95), 2),
        "p99_latency_ms": round(_percentile(durations_ms, 0.99), 2),
        "requests_per_minute": len(recent_minute),
        "http_4xx_count": count_4xx,
        "http_5xx_count": count_5xx,
    }


def observe_workflow_execution() -> None:
    global _workflow_executions_total
    with _lock:
        _workflow_executions_total += 1


def observe_grade_submission() -> None:
    global _grade_submissions_total
    with _lock:
        _grade_submissions_total += 1


def observe_scheduling_conflict() -> None:
    global _scheduling_conflicts_total
    with _lock:
        _scheduling_conflicts_total += 1


def _escape(s: str) -> str:
    return s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


def render_metrics() -> str:
    """Return metrics in Prometheus text exposition format."""
    lines: list[str] = []

    lines.append("# HELP http_requests_total Total HTTP requests.")
    lines.append("# TYPE http_requests_total counter")
    with _lock:
        total_snapshot = dict(_req_total)
        dur_snapshot = dict(_req_duration)
        dur_bucket_snapshot = dict(_req_duration_bucket)
        status_class_snapshot = dict(_req_status_class_total)
        workflow_executions_total = _workflow_executions_total
        grade_submissions_total = _grade_submissions_total
        scheduling_conflicts_total = _scheduling_conflicts_total

    for (method, path, status), count in sorted(total_snapshot.items()):
        labels = f'method="{_escape(method)}",path="{_escape(path)}",status="{_escape(status)}"'
        lines.append(f"http_requests_total{{{labels}}} {count}")

    lines.append("# HELP http_requests_status_class_total Total HTTP requests grouped by status class.")
    lines.append("# TYPE http_requests_status_class_total counter")
    for (method, path, status_class), count in sorted(status_class_snapshot.items()):
        labels = f'method="{_escape(method)}",path="{_escape(path)}",status_class="{_escape(status_class)}"'
        lines.append(f"http_requests_status_class_total{{{labels}}} {count}")

    lines.append("# HELP http_request_duration_seconds Request latency histogram buckets.")
    lines.append("# TYPE http_request_duration_seconds histogram")
    for (method, path, le), count in sorted(dur_bucket_snapshot.items()):
        labels = f'method="{_escape(method)}",path="{_escape(path)}",le="{_escape(le)}"'
        lines.append(f"http_request_duration_seconds_bucket{{{labels}}} {count}")

    lines.append("# HELP http_request_duration_seconds_total Sum of request durations (seconds).")
    lines.append("# TYPE http_request_duration_seconds_total counter")
    for (method, path), (count, total_dur) in sorted(dur_snapshot.items()):
        labels = f'method="{_escape(method)}",path="{_escape(path)}"'
        lines.append(f"http_request_duration_seconds_total{{{labels}}} {total_dur:.6f}")

    lines.append("# HELP http_request_duration_seconds_count Number of timed requests.")
    lines.append("# TYPE http_request_duration_seconds_count counter")
    for (method, path), (count, _) in sorted(dur_snapshot.items()):
        labels = f'method="{_escape(method)}",path="{_escape(path)}"'
        lines.append(f"http_request_duration_seconds_count{{{labels}}} {count}")

    lines.append("# HELP workflow_executions_total Total successful workflow execution starts.")
    lines.append("# TYPE workflow_executions_total counter")
    lines.append(f"workflow_executions_total {workflow_executions_total}")

    lines.append("# HELP grade_submissions_total Total successful grade submissions.")
    lines.append("# TYPE grade_submissions_total counter")
    lines.append(f"grade_submissions_total {grade_submissions_total}")

    lines.append("# HELP scheduling_conflicts_total Total detected scheduling conflicts.")
    lines.append("# TYPE scheduling_conflicts_total counter")
    lines.append(f"scheduling_conflicts_total {scheduling_conflicts_total}")

    security_events, security_anomalies = snapshot_security_metrics()
    lines.append("# HELP security_events_total Total number of security-relevant events.")
    lines.append("# TYPE security_events_total counter")
    for (signal, outcome), count in sorted(security_events.items()):
        labels = f'signal="{_escape(signal)}",outcome="{_escape(outcome)}"'
        lines.append(f"security_events_total{{{labels}}} {count}")

    lines.append("# HELP security_anomalies_total Total number of detected security anomalies.")
    lines.append("# TYPE security_anomalies_total counter")
    for signal, count in sorted(security_anomalies.items()):
        labels = f'signal="{_escape(signal)}"'
        lines.append(f"security_anomalies_total{{{labels}}} {count}")

    lines.append("")
    return "\n".join(lines)
