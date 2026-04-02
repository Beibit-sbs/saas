"""In-process Prometheus-compatible metrics.

No external library required. Emits text/plain exposition format.
"""
from __future__ import annotations

from collections import defaultdict
from collections import deque
from datetime import datetime, timezone
from threading import Lock
import time

from app.platform.runtime_state import get_scheduler_last_run, get_worker_heartbeat
from app.modules.observability.security_signals import snapshot_security_metrics
from app.modules.observability.alerts import observe_latency_spike

_lock = Lock()

# http_requests_total{method, path, status, tenant_id}
_req_total: dict[tuple[str, str, str, str], int] = defaultdict(int)

# http_request_duration_seconds — stored as (count, sum_seconds)
_req_duration: dict[tuple[str, str, str], tuple[int, float]] = defaultdict(lambda: (0, 0.0))

# http_request_duration_seconds_bucket{method,path,tenant_id,le}
_req_duration_bucket: dict[tuple[str, str, str, str], int] = defaultdict(int)

# http_requests_status_class_total{method,path,status_class,tenant_id}
_req_status_class_total: dict[tuple[str, str, str, str], int] = defaultdict(int)

# Optional domain counters (safe defaults, increment only where integrated)
_workflow_executions_total = 0
_grade_submissions_total = 0
_scheduling_conflicts_total = 0
_recent_request_samples: deque[tuple[float, int, float]] = deque(maxlen=5000)
_auth_login_attempts_total: dict[tuple[str, str, str], int] = defaultdict(int)
_auth_login_failures_total: dict[tuple[str, str, str], int] = defaultdict(int)
_jobs_executed_total: int = 0
_jobs_failed_total: int = 0
_jobs_queue_size: int = 0
_invoices_created_total: int = 0
_billing_failures_total: int = 0
_db_connections_active: int | None = None
_redis_latency_seconds: float | None = None

_LATENCY_BUCKETS = (0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)


def _parse_iso(raw: str | None) -> datetime | None:
    if not raw:
        return None
    try:
        return datetime.fromisoformat(str(raw))
    except Exception:
        return None


def _age_seconds_from_iso(raw: str | None) -> float:
    parsed = _parse_iso(raw)
    if parsed is None:
        return -1.0
    return max(0.0, (datetime.now(timezone.utc) - parsed).total_seconds())


def _status_class(status: int) -> str:
    return f"{max(0, int(status)) // 100}xx"


def _bucket_label(value: float) -> str:
    if float(value).is_integer():
        return f"{int(value)}"
    return f"{value}"


def record_request(method: str, path: str, status: int, duration: float, tenant_id: str | int | None = None) -> None:
    tenant = str(tenant_id if tenant_id is not None else "-")
    key_total = (method.upper(), path, str(status), tenant)
    key_dur = (method.upper(), path, tenant)
    status_key = (method.upper(), path, _status_class(status), tenant)
    with _lock:
        _req_total[key_total] += 1
        old_count, old_sum = _req_duration[key_dur]
        _req_duration[key_dur] = (old_count + 1, old_sum + duration)
        _req_status_class_total[status_key] += 1
        _recent_request_samples.append((time.time(), int(status), float(duration)))
        for bound in _LATENCY_BUCKETS:
            if duration <= bound:
                _req_duration_bucket[(method.upper(), path, tenant, _bucket_label(bound))] += 1
            _req_duration_bucket[(method.upper(), path, tenant, "+Inf")] += 1
    latency = snapshot_latency_metrics()
    observe_latency_spike(
        float(latency.get("p95_latency_ms", 0.0) or 0.0),
        float(latency.get("p99_latency_ms", 0.0) or 0.0),
        int(latency.get("requests_per_minute", 0) or 0),
        None,
    )


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


def observe_auth_login_attempt(*, auth_source: str, outcome: str, tenant_id: str | int | None = None) -> None:
    key = (
        str(tenant_id if tenant_id is not None else "-").strip() or "-",
        str(auth_source).strip().lower() or "unknown",
        str(outcome).strip().lower() or "attempt",
    )
    with _lock:
        _auth_login_attempts_total[key] += 1
        if key[2] != "success":
            _auth_login_failures_total[(key[0], key[1], key[2])] += 1


def observe_job_execution(*, outcome: str) -> None:
    normalized = str(outcome).strip().lower()
    with _lock:
        global _jobs_executed_total, _jobs_failed_total
        if normalized == "success":
            _jobs_executed_total += 1
        elif normalized == "failed":
            _jobs_failed_total += 1


def set_jobs_queue_size(value: int) -> None:
    with _lock:
        global _jobs_queue_size
        _jobs_queue_size = max(0, int(value))


def observe_invoice_created() -> None:
    global _invoices_created_total
    with _lock:
        _invoices_created_total += 1


def observe_billing_failure() -> None:
    global _billing_failures_total
    with _lock:
        _billing_failures_total += 1


def set_db_connections_active(value: int | None) -> None:
    with _lock:
        global _db_connections_active
        _db_connections_active = None if value is None else int(value)


def set_redis_latency(value_seconds: float | None) -> None:
    with _lock:
        global _redis_latency_seconds
        _redis_latency_seconds = None if value_seconds is None else float(value_seconds)


def clear_metrics_state() -> None:
    with _lock:
        _req_total.clear()
        _req_duration.clear()
        _req_duration_bucket.clear()
        _req_status_class_total.clear()
        _recent_request_samples.clear()
        _auth_login_attempts_total.clear()
        _auth_login_failures_total.clear()
        global _workflow_executions_total, _grade_submissions_total, _scheduling_conflicts_total
        global _jobs_executed_total, _jobs_failed_total, _jobs_queue_size, _invoices_created_total, _billing_failures_total
        global _db_connections_active, _redis_latency_seconds
        _workflow_executions_total = 0
        _grade_submissions_total = 0
        _scheduling_conflicts_total = 0
        _jobs_executed_total = 0
        _jobs_failed_total = 0
        _jobs_queue_size = 0
        _invoices_created_total = 0
        _billing_failures_total = 0
        _db_connections_active = None
        _redis_latency_seconds = None


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
        auth_login_attempts_total = dict(_auth_login_attempts_total)
        auth_login_failures_total = dict(_auth_login_failures_total)
        jobs_executed_total = _jobs_executed_total
        jobs_failed_total = _jobs_failed_total
        jobs_queue_size = _jobs_queue_size
        invoices_created_total = _invoices_created_total
        billing_failures_total = _billing_failures_total
        db_connections_active = _db_connections_active
        redis_latency_seconds = _redis_latency_seconds

    for (method, path, status, tenant), count in sorted(total_snapshot.items()):
        labels = f'method="{_escape(method)}",path="{_escape(path)}",status="{_escape(status)}",tenant_id="{_escape(tenant)}"'
        lines.append(f"http_requests_total{{{labels}}} {count}")

    lines.append("# HELP http_requests_status_class_total Total HTTP requests grouped by status class.")
    lines.append("# TYPE http_requests_status_class_total counter")
    for (method, path, status_class, tenant), count in sorted(status_class_snapshot.items()):
        labels = f'method="{_escape(method)}",path="{_escape(path)}",status_class="{_escape(status_class)}",tenant_id="{_escape(tenant)}"'
        lines.append(f"http_requests_status_class_total{{{labels}}} {count}")

    lines.append("# HELP http_request_duration_seconds Request latency histogram buckets.")
    lines.append("# TYPE http_request_duration_seconds histogram")
    for (method, path, tenant, le), count in sorted(dur_bucket_snapshot.items()):
        labels = f'method="{_escape(method)}",path="{_escape(path)}",tenant_id="{_escape(tenant)}",le="{_escape(le)}"'
        lines.append(f"http_request_duration_seconds_bucket{{{labels}}} {count}")

    lines.append("# HELP http_request_duration_seconds_total Sum of request durations (seconds).")
    lines.append("# TYPE http_request_duration_seconds_total counter")
    for (method, path, tenant), (count, total_dur) in sorted(dur_snapshot.items()):
        labels = f'method="{_escape(method)}",path="{_escape(path)}",tenant_id="{_escape(tenant)}"'
        lines.append(f"http_request_duration_seconds_total{{{labels}}} {total_dur:.6f}")

    lines.append("# HELP http_request_duration_seconds_count Number of timed requests.")
    lines.append("# TYPE http_request_duration_seconds_count counter")
    for (method, path, tenant), (count, _) in sorted(dur_snapshot.items()):
        labels = f'method="{_escape(method)}",path="{_escape(path)}",tenant_id="{_escape(tenant)}"'
        lines.append(f"http_request_duration_seconds_count{{{labels}}} {count}")

    latency_snapshot = snapshot_latency_metrics()
    lines.append("# HELP http_request_duration_seconds_quantile Recent request latency quantiles.")
    lines.append("# TYPE http_request_duration_seconds_quantile gauge")
    lines.append(
        f'http_request_duration_seconds_quantile{{quantile="0.5"}} {float(latency_snapshot.get("p50_latency_ms", 0.0) or 0.0) / 1000:.6f}'
    )
    lines.append(
        f'http_request_duration_seconds_quantile{{quantile="0.95"}} {float(latency_snapshot.get("p95_latency_ms", 0.0) or 0.0) / 1000:.6f}'
    )
    lines.append(
        f'http_request_duration_seconds_quantile{{quantile="0.99"}} {float(latency_snapshot.get("p99_latency_ms", 0.0) or 0.0) / 1000:.6f}'
    )

    lines.append("# HELP workflow_executions_total Total successful workflow execution starts.")
    lines.append("# TYPE workflow_executions_total counter")
    lines.append(f"workflow_executions_total {workflow_executions_total}")

    lines.append("# HELP grade_submissions_total Total successful grade submissions.")
    lines.append("# TYPE grade_submissions_total counter")
    lines.append(f"grade_submissions_total {grade_submissions_total}")

    lines.append("# HELP scheduling_conflicts_total Total detected scheduling conflicts.")
    lines.append("# TYPE scheduling_conflicts_total counter")
    lines.append(f"scheduling_conflicts_total {scheduling_conflicts_total}")

    lines.append("# HELP auth_login_attempts_total Total authentication login attempts.")
    lines.append("# TYPE auth_login_attempts_total counter")
    for (tenant, auth_source, outcome), count in sorted(auth_login_attempts_total.items()):
        labels = f'tenant_id="{_escape(tenant)}",auth_source="{_escape(auth_source)}",outcome="{_escape(outcome)}"'
        lines.append(f"auth_login_attempts_total{{{labels}}} {count}")

    lines.append("# HELP auth_login_failures_total Total failed authentication login attempts.")
    lines.append("# TYPE auth_login_failures_total counter")
    for (tenant, auth_source, outcome), count in sorted(auth_login_failures_total.items()):
        labels = f'tenant_id="{_escape(tenant)}",auth_source="{_escape(auth_source)}",outcome="{_escape(outcome)}"'
        lines.append(f"auth_login_failures_total{{{labels}}} {count}")

    lines.append("# HELP jobs_executed_total Total successfully executed jobs.")
    lines.append("# TYPE jobs_executed_total counter")
    lines.append(f"jobs_executed_total {jobs_executed_total}")

    lines.append("# HELP jobs_failed_total Total permanently failed jobs.")
    lines.append("# TYPE jobs_failed_total counter")
    lines.append(f"jobs_failed_total {jobs_failed_total}")

    lines.append("# HELP jobs_queue_size Current number of queued (pending) jobs.")
    lines.append("# TYPE jobs_queue_size gauge")
    lines.append(f"jobs_queue_size {jobs_queue_size}")

    lines.append("# HELP invoices_created_total Total created invoices.")
    lines.append("# TYPE invoices_created_total counter")
    lines.append(f"invoices_created_total {invoices_created_total}")

    lines.append("# HELP billing_failures_total Total billing processing failures.")
    lines.append("# TYPE billing_failures_total counter")
    lines.append(f"billing_failures_total {billing_failures_total}")

    lines.append("# HELP db_connections_active Active checked-out DB connections.")
    lines.append("# TYPE db_connections_active gauge")
    lines.append(f"db_connections_active {db_connections_active if db_connections_active is not None else 'NaN'}")

    lines.append("# HELP redis_latency_seconds Most recent Redis probe latency in seconds.")
    lines.append("# TYPE redis_latency_seconds gauge")
    lines.append(f"redis_latency_seconds {redis_latency_seconds if redis_latency_seconds is not None else 'NaN'}")

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

    worker_age_seconds = _age_seconds_from_iso(get_worker_heartbeat())
    scheduler_last_run = get_scheduler_last_run()
    scheduler_age_seconds = _age_seconds_from_iso(
        str(scheduler_last_run.get("at")) if isinstance(scheduler_last_run, dict) and scheduler_last_run.get("at") else None
    )

    lines.append("# HELP worker_heartbeat_age_seconds Age of the last worker heartbeat in seconds (-1 if missing).")
    lines.append("# TYPE worker_heartbeat_age_seconds gauge")
    lines.append(f"worker_heartbeat_age_seconds {worker_age_seconds:.3f}")

    lines.append("# HELP scheduler_last_run_age_seconds Age of the last scheduler run in seconds (-1 if missing).")
    lines.append("# TYPE scheduler_last_run_age_seconds gauge")
    lines.append(f"scheduler_last_run_age_seconds {scheduler_age_seconds:.3f}")

    lines.append("")
    return "\n".join(lines)
