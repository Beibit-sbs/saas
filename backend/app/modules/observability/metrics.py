"""In-process Prometheus-compatible metrics.

No external library required. Emits text/plain exposition format.
"""
from __future__ import annotations

from collections import defaultdict
from threading import Lock

_lock = Lock()

# http_requests_total{method, path, status}
_req_total: dict[tuple[str, str, str], int] = defaultdict(int)

# http_request_duration_seconds — stored as (count, sum_seconds)
_req_duration: dict[tuple[str, str], tuple[int, float]] = defaultdict(lambda: (0, 0.0))


def record_request(method: str, path: str, status: int, duration: float) -> None:
    key_total = (method.upper(), path, str(status))
    key_dur = (method.upper(), path)
    with _lock:
        _req_total[key_total] += 1
        old_count, old_sum = _req_duration[key_dur]
        _req_duration[key_dur] = (old_count + 1, old_sum + duration)


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

    for (method, path, status), count in sorted(total_snapshot.items()):
        labels = f'method="{_escape(method)}",path="{_escape(path)}",status="{_escape(status)}"'
        lines.append(f"http_requests_total{{{labels}}} {count}")

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

    lines.append("")
    return "\n".join(lines)
