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
_developer_analytics_contract_total: dict[tuple[str, str, str], int] = defaultdict(int)
_playbook_executions_total: dict[tuple[str, str, str], int] = defaultdict(int)
_playbook_execution_duration: dict[tuple[str, str], tuple[int, float]] = defaultdict(lambda: (0, 0.0))
_playbook_step_actions_total: dict[tuple[str, str], int] = defaultdict(int)
_risk_scoring_jobs_total: dict[tuple[str, str], int] = defaultdict(int)
_risk_scoring_duration: dict[tuple[str, str], tuple[int, float]] = defaultdict(lambda: (0, 0.0))
_risk_recommendation_ack_total: dict[tuple[str, str], int] = defaultdict(int)
_risk_high_band_students_total: dict[str, int] = defaultdict(int)
_risk_latest_snapshot_age_seconds: dict[str, float] = defaultdict(float)
_f3_cohort_operations_total: dict[tuple[str, str, str], int] = defaultdict(int)
_f3_cohort_operation_duration: dict[tuple[str, str, str], tuple[int, float]] = defaultdict(lambda: (0, 0.0))
_f3_guardrails_evaluated_total: dict[tuple[str, str, str], int] = defaultdict(int)
_f3_active_cohort_analysis_queue_depth: dict[tuple[str, str, str], int] = defaultdict(int)
_ai_cost_total_usd: dict[tuple[str, str, str, str], float] = defaultdict(float)
_ai_budget_utilization_pct: dict[tuple[str, str, str], float] = defaultdict(float)
_ai_budget_exceeded_total: dict[tuple[str, str], int] = defaultdict(int)
_ai_cost_anomaly_detected_total: dict[str, int] = defaultdict(int)
_ai_slo_compliance_pct: dict[tuple[str, str], float] = defaultdict(float)
_ai_slo_breach_total: dict[tuple[str, str], int] = defaultdict(int)
_ai_guardrail_evaluations_total: dict[tuple[str, str, str, str], int] = defaultdict(int)
_ai_guardrail_blocked_total: dict[tuple[str, str, str], int] = defaultdict(int)
_ai_guardrail_evaluation_duration_seconds: dict[tuple[str, str], tuple[int, float]] = defaultdict(lambda: (0, 0.0))
_ai_routing_selection_total: dict[tuple[str, str, str], int] = defaultdict(int)
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


def observe_developer_analytics_contract(*, endpoint: str, outcome: str, reason: str) -> None:
    key = (
        str(endpoint).strip() or "unknown",
        str(outcome).strip().lower() or "observed",
        str(reason).strip().lower() or "unspecified",
    )
    with _lock:
        _developer_analytics_contract_total[key] += 1


def observe_playbook_execution_started(*, tenant_id: str | int | None, triggered_by: str) -> None:
    key = (
        str(tenant_id if tenant_id is not None else "-").strip() or "-",
        "started",
        str(triggered_by).strip().lower() or "-",
    )
    with _lock:
        _playbook_executions_total[key] += 1


def observe_playbook_execution_finished(
    *, tenant_id: str | int | None, status: str, duration_seconds: float
) -> None:
    tenant = str(tenant_id if tenant_id is not None else "-").strip() or "-"
    normalized_status = str(status).strip().lower() or "unknown"
    with _lock:
        _playbook_executions_total[(tenant, normalized_status, "-")] += 1
        count, total_duration = _playbook_execution_duration[(tenant, normalized_status)]
        _playbook_execution_duration[(tenant, normalized_status)] = (
            count + 1,
            total_duration + max(0.0, float(duration_seconds)),
        )


def observe_playbook_step_action(*, tenant_id: str | int | None, action: str) -> None:
    key = (
        str(tenant_id if tenant_id is not None else "-").strip() or "-",
        str(action).strip().lower() or "unknown",
    )
    with _lock:
        _playbook_step_actions_total[key] += 1


def observe_risk_scoring_job(*, tenant_id: str | int | None, status: str) -> None:
    key = (
        str(tenant_id if tenant_id is not None else "-").strip() or "-",
        str(status).strip().lower() or "unknown",
    )
    with _lock:
        _risk_scoring_jobs_total[key] += 1


def observe_risk_scoring_duration(*, tenant_id: str | int | None, status: str, duration_seconds: float) -> None:
    key = (
        str(tenant_id if tenant_id is not None else "-").strip() or "-",
        str(status).strip().lower() or "unknown",
    )
    with _lock:
        count, total_duration = _risk_scoring_duration[key]
        _risk_scoring_duration[key] = (count + 1, total_duration + max(0.0, float(duration_seconds)))


def observe_risk_recommendation_ack(*, tenant_id: str | int | None, status: str) -> None:
    key = (
        str(tenant_id if tenant_id is not None else "-").strip() or "-",
        str(status).strip().lower() or "unknown",
    )
    with _lock:
        _risk_recommendation_ack_total[key] += 1


def observe_f3_cohort_operation(
    *,
    tenant_id: str | int | None,
    operation: str,
    status: str,
    duration_seconds: float,
) -> None:
    key = (
        str(tenant_id if tenant_id is not None else "-").strip() or "-",
        str(operation).strip().lower() or "unknown",
        str(status).strip().lower() or "unknown",
    )
    with _lock:
        _f3_cohort_operations_total[key] += 1
        count, total_duration = _f3_cohort_operation_duration[key]
        _f3_cohort_operation_duration[key] = (count + 1, total_duration + max(0.0, float(duration_seconds)))


def observe_f3_guardrail_evaluation(
    *,
    tenant_id: str | int | None,
    guardrail: str,
    result: str,
) -> None:
    key = (
        str(tenant_id if tenant_id is not None else "-").strip() or "-",
        str(guardrail).strip().lower() or "unknown",
        str(result).strip().lower() or "unknown",
    )
    with _lock:
        _f3_guardrails_evaluated_total[key] += 1


def observe_f3_analysis_queue_enqueued(*, tenant_id: str | int | None, queue_name: str = "analyze_queue") -> None:
    key = (
        str(tenant_id if tenant_id is not None else "-").strip() or "-",
        str(queue_name).strip().lower() or "analyze_queue",
        "pending",
    )
    with _lock:
        _f3_active_cohort_analysis_queue_depth[key] += 1


def set_risk_high_band_students_total(*, tenant_id: str | int | None, total: int) -> None:
    key = str(tenant_id if tenant_id is not None else "-").strip() or "-"
    with _lock:
        _risk_high_band_students_total[key] = max(0, int(total))


def set_risk_latest_snapshot_age_seconds(*, tenant_id: str | int | None, age_seconds: float) -> None:
    key = str(tenant_id if tenant_id is not None else "-").strip() or "-"
    with _lock:
        _risk_latest_snapshot_age_seconds[key] = max(0.0, float(age_seconds))


def snapshot_developer_analytics_contract_metrics() -> dict[tuple[str, str, str], int]:
    with _lock:
        return dict(_developer_analytics_contract_total)


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


def observe_ai_cost_summary(*, tenant_id: int, summary: dict[str, object]) -> None:
    tenant = str(int(tenant_id))
    models = list(summary.get("models") or [])
    with _lock:
        for item in models:
            if not isinstance(item, dict):
                continue
            provider = str(item.get("provider") or "unknown").strip().lower() or "unknown"
            model = str(item.get("model_key") or "unknown").strip() or "unknown"
            cost_usd = max(0.0, float(item.get("estimated_cost_usd") or 0.0))
            _ai_cost_total_usd[(tenant, provider, model, "daily")] = round(cost_usd, 6)

        if bool(summary.get("anomaly_detected", False)):
            _ai_cost_anomaly_detected_total[tenant] += 1


def observe_ai_budget_status(*, tenant_id: int, rows: list[dict[str, object]]) -> None:
    tenant = str(int(tenant_id))
    with _lock:
        for item in rows:
            scope = str(item.get("scope") or "tenant").strip().lower() or "tenant"
            raw_scope_id = item.get("scope_id")
            scope_id = str(raw_scope_id).strip() if raw_scope_id is not None else "-"
            utilization_pct = max(0.0, float(item.get("utilization_pct") or 0.0))
            _ai_budget_utilization_pct[(tenant, scope, scope_id)] = round(utilization_pct, 2)

            exceeded = bool(item.get("hard_cap_exceeded", False)) or utilization_pct >= 100.0
            if exceeded:
                _ai_budget_exceeded_total[(tenant, scope)] += 1


def observe_ai_slo_compliance(rows: list[dict[str, object]]) -> None:
    with _lock:
        for item in rows:
            model = str(item.get("model_key") or "unknown").strip() or "unknown"

            latency_compliant = bool(item.get("latency_compliant", False))
            latency_pct = 100.0 if latency_compliant else 0.0
            _ai_slo_compliance_pct[(model, "p95_latency")] = latency_pct
            if not latency_compliant:
                _ai_slo_breach_total[(model, "p95_latency")] += 1

            error_rate_compliant = bool(item.get("error_rate_compliant", False))
            error_rate_pct = 100.0 if error_rate_compliant else 0.0
            _ai_slo_compliance_pct[(model, "error_rate")] = error_rate_pct
            if not error_rate_compliant:
                _ai_slo_breach_total[(model, "error_rate")] += 1


def observe_ai_routing_selection(
    *,
    tenant_id: int | str,
    mode: str,
    selection: str,
) -> None:
    t = str(tenant_id)
    m = str(mode).strip().lower() or "unknown"
    s = str(selection).strip().lower() or "unknown"
    with _lock:
        _ai_routing_selection_total[(t, m, s)] += 1


def observe_ai_guardrail_evaluation(
    *,
    tenant_id: str | int | None,
    stage: str,
    detector: str,
    decision: str,
    duration_seconds: float = 0.0,
) -> None:
    t = str(tenant_id if tenant_id is not None else "-").strip() or "-"
    s = str(stage).strip().lower() or "unknown"
    d = str(detector).strip().lower() or "unknown"
    dec = str(decision).strip().lower() or "unknown"
    with _lock:
        _ai_guardrail_evaluations_total[(t, s, d, dec)] += 1
        count, total = _ai_guardrail_evaluation_duration_seconds[(t, s)]
        _ai_guardrail_evaluation_duration_seconds[(t, s)] = (count + 1, total + max(0.0, float(duration_seconds)))


def observe_ai_guardrail_blocked(
    *,
    tenant_id: str | int | None,
    detector: str,
    reason: str,
) -> None:
    t = str(tenant_id if tenant_id is not None else "-").strip() or "-"
    d = str(detector).strip().lower() or "unknown"
    r = str(reason).strip().lower() or "unknown"
    with _lock:
        _ai_guardrail_blocked_total[(t, d, r)] += 1


def clear_metrics_state() -> None:
    with _lock:
        _req_total.clear()
        _req_duration.clear()
        _req_duration_bucket.clear()
        _req_status_class_total.clear()
        _recent_request_samples.clear()
        _auth_login_attempts_total.clear()
        _auth_login_failures_total.clear()
        _developer_analytics_contract_total.clear()
        _playbook_executions_total.clear()
        _playbook_execution_duration.clear()
        _playbook_step_actions_total.clear()
        _risk_scoring_jobs_total.clear()
        _risk_scoring_duration.clear()
        _risk_recommendation_ack_total.clear()
        _risk_high_band_students_total.clear()
        _risk_latest_snapshot_age_seconds.clear()
        _f3_cohort_operations_total.clear()
        _f3_cohort_operation_duration.clear()
        _f3_guardrails_evaluated_total.clear()
        _f3_active_cohort_analysis_queue_depth.clear()
        _ai_cost_total_usd.clear()
        _ai_budget_utilization_pct.clear()
        _ai_budget_exceeded_total.clear()
        _ai_cost_anomaly_detected_total.clear()
        _ai_slo_compliance_pct.clear()
        _ai_slo_breach_total.clear()
        _ai_guardrail_evaluations_total.clear()
        _ai_guardrail_blocked_total.clear()
        _ai_guardrail_evaluation_duration_seconds.clear()
        _ai_routing_selection_total.clear()
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
        developer_analytics_contract_total = dict(_developer_analytics_contract_total)
        playbook_executions_total = dict(_playbook_executions_total)
        playbook_execution_duration = dict(_playbook_execution_duration)
        playbook_step_actions_total = dict(_playbook_step_actions_total)
        risk_scoring_jobs_total = dict(_risk_scoring_jobs_total)
        risk_scoring_duration = dict(_risk_scoring_duration)
        risk_recommendation_ack_total = dict(_risk_recommendation_ack_total)
        risk_high_band_students_total = dict(_risk_high_band_students_total)
        risk_latest_snapshot_age_seconds = dict(_risk_latest_snapshot_age_seconds)
        f3_cohort_operations_total = dict(_f3_cohort_operations_total)
        f3_cohort_operation_duration = dict(_f3_cohort_operation_duration)
        f3_guardrails_evaluated_total = dict(_f3_guardrails_evaluated_total)
        f3_active_cohort_analysis_queue_depth = dict(_f3_active_cohort_analysis_queue_depth)
        ai_cost_total_usd = dict(_ai_cost_total_usd)
        ai_budget_utilization_pct = dict(_ai_budget_utilization_pct)
        ai_budget_exceeded_total = dict(_ai_budget_exceeded_total)
        ai_cost_anomaly_detected_total = dict(_ai_cost_anomaly_detected_total)
        ai_slo_compliance_pct = dict(_ai_slo_compliance_pct)
        ai_slo_breach_total = dict(_ai_slo_breach_total)
        ai_routing_selection_total = dict(_ai_routing_selection_total)
        ai_guardrail_evaluations_total = dict(_ai_guardrail_evaluations_total)
        ai_guardrail_blocked_total = dict(_ai_guardrail_blocked_total)
        ai_guardrail_evaluation_duration_seconds = dict(_ai_guardrail_evaluation_duration_seconds)
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

    lines.append("# HELP developer_analytics_contract_total Developer analytics contract outcomes.")
    lines.append("# TYPE developer_analytics_contract_total counter")
    for (endpoint, outcome, reason), count in sorted(developer_analytics_contract_total.items()):
        labels = f'endpoint="{_escape(endpoint)}",outcome="{_escape(outcome)}",reason="{_escape(reason)}"'
        lines.append(f"developer_analytics_contract_total{{{labels}}} {count}")

    lines.append("# HELP playbook_executions_total Total playbook execution lifecycle events.")
    lines.append("# TYPE playbook_executions_total counter")
    for (tenant, status, triggered_by), count in sorted(playbook_executions_total.items()):
        labels = f'tenant_id="{_escape(tenant)}",status="{_escape(status)}",triggered_by="{_escape(triggered_by)}"'
        lines.append(f"playbook_executions_total{{{labels}}} {count}")

    lines.append("# HELP playbook_execution_duration_seconds_total Sum of playbook execution durations.")
    lines.append("# TYPE playbook_execution_duration_seconds_total counter")
    for (tenant, status), (_, total_duration) in sorted(playbook_execution_duration.items()):
        labels = f'tenant_id="{_escape(tenant)}",status="{_escape(status)}"'
        lines.append(f"playbook_execution_duration_seconds_total{{{labels}}} {total_duration:.6f}")

    lines.append("# HELP playbook_execution_duration_seconds_count Number of finished playbook executions.")
    lines.append("# TYPE playbook_execution_duration_seconds_count counter")
    for (tenant, status), (count, _) in sorted(playbook_execution_duration.items()):
        labels = f'tenant_id="{_escape(tenant)}",status="{_escape(status)}"'
        lines.append(f"playbook_execution_duration_seconds_count{{{labels}}} {count}")

    lines.append("# HELP playbook_step_actions_total Total playbook step actions.")
    lines.append("# TYPE playbook_step_actions_total counter")
    for (tenant, action), count in sorted(playbook_step_actions_total.items()):
        labels = f'tenant_id="{_escape(tenant)}",action="{_escape(action)}"'
        lines.append(f"playbook_step_actions_total{{{labels}}} {count}")

    lines.append("# HELP risk_scoring_jobs_total Total risk scoring recompute jobs.")
    lines.append("# TYPE risk_scoring_jobs_total counter")
    for (tenant, status), count in sorted(risk_scoring_jobs_total.items()):
        labels = f'tenant_id="{_escape(tenant)}",status="{_escape(status)}"'
        lines.append(f"risk_scoring_jobs_total{{{labels}}} {count}")

    lines.append("# HELP risk_scoring_duration_seconds_total Sum of risk scoring durations.")
    lines.append("# TYPE risk_scoring_duration_seconds_total counter")
    for (tenant, status), (_, total_duration) in sorted(risk_scoring_duration.items()):
        labels = f'tenant_id="{_escape(tenant)}",status="{_escape(status)}"'
        lines.append(f"risk_scoring_duration_seconds_total{{{labels}}} {total_duration:.6f}")

    lines.append("# HELP risk_scoring_duration_seconds_count Number of risk scoring runs.")
    lines.append("# TYPE risk_scoring_duration_seconds_count counter")
    for (tenant, status), (count, _) in sorted(risk_scoring_duration.items()):
        labels = f'tenant_id="{_escape(tenant)}",status="{_escape(status)}"'
        lines.append(f"risk_scoring_duration_seconds_count{{{labels}}} {count}")

    lines.append("# HELP risk_recommendation_ack_total Total risk recommendation acknowledgements.")
    lines.append("# TYPE risk_recommendation_ack_total counter")
    for (tenant, status), count in sorted(risk_recommendation_ack_total.items()):
        labels = f'tenant_id="{_escape(tenant)}",status="{_escape(status)}"'
        lines.append(f"risk_recommendation_ack_total{{{labels}}} {count}")

    lines.append("# HELP risk_high_band_students_total Total students currently in the highest risk band.")
    lines.append("# TYPE risk_high_band_students_total gauge")
    for tenant, total in sorted(risk_high_band_students_total.items()):
        labels = f'tenant_id="{_escape(tenant)}"'
        lines.append(f"risk_high_band_students_total{{{labels}}} {total}")

    lines.append("# HELP risk_latest_snapshot_age_seconds Age of the latest risk snapshot in seconds.")
    lines.append("# TYPE risk_latest_snapshot_age_seconds gauge")
    for tenant, age_seconds in sorted(risk_latest_snapshot_age_seconds.items()):
        labels = f'tenant_id="{_escape(tenant)}"'
        lines.append(f"risk_latest_snapshot_age_seconds{{{labels}}} {age_seconds:.3f}")

    lines.append("# HELP f3_cohort_operations_total Total F3 cohort operations.")
    lines.append("# TYPE f3_cohort_operations_total counter")
    for (tenant, operation, status), count in sorted(f3_cohort_operations_total.items()):
        labels = f'tenant_id="{_escape(tenant)}",operation="{_escape(operation)}",status="{_escape(status)}"'
        lines.append(f"f3_cohort_operations_total{{{labels}}} {count}")

    lines.append("# HELP f3_cohort_operation_duration_seconds_total Sum of F3 cohort operation durations.")
    lines.append("# TYPE f3_cohort_operation_duration_seconds_total counter")
    for (tenant, operation, status), (_, total_duration) in sorted(f3_cohort_operation_duration.items()):
        labels = f'tenant_id="{_escape(tenant)}",operation="{_escape(operation)}",status="{_escape(status)}"'
        lines.append(f"f3_cohort_operation_duration_seconds_total{{{labels}}} {total_duration:.6f}")

    lines.append("# HELP f3_cohort_operation_duration_seconds_count Number of finished F3 cohort operations.")
    lines.append("# TYPE f3_cohort_operation_duration_seconds_count counter")
    for (tenant, operation, status), (count, _) in sorted(f3_cohort_operation_duration.items()):
        labels = f'tenant_id="{_escape(tenant)}",operation="{_escape(operation)}",status="{_escape(status)}"'
        lines.append(f"f3_cohort_operation_duration_seconds_count{{{labels}}} {count}")

    lines.append("# HELP f3_guardrails_evaluated_total Total F3 guardrail evaluations.")
    lines.append("# TYPE f3_guardrails_evaluated_total counter")
    for (tenant, guardrail, result), count in sorted(f3_guardrails_evaluated_total.items()):
        labels = f'tenant_id="{_escape(tenant)}",guardrail="{_escape(guardrail)}",result="{_escape(result)}"'
        lines.append(f"f3_guardrails_evaluated_total{{{labels}}} {count}")

    lines.append("# HELP f3_active_cohort_analysis_queue_depth Current queued F3 analysis depth.")
    lines.append("# TYPE f3_active_cohort_analysis_queue_depth gauge")
    for (tenant, queue_name, status), value in sorted(f3_active_cohort_analysis_queue_depth.items()):
        labels = f'tenant_id="{_escape(tenant)}",queue_name="{_escape(queue_name)}",status="{_escape(status)}"'
        lines.append(f"f3_active_cohort_analysis_queue_depth{{{labels}}} {value}")

    lines.append("# HELP ai_cost_total_usd Total AI cost per tenant/provider/model/period.")
    lines.append("# TYPE ai_cost_total_usd gauge")
    for (tenant, provider, model, period), value in sorted(ai_cost_total_usd.items()):
        labels = (
            f'tenant_id="{_escape(tenant)}",provider="{_escape(provider)}",'
            f'model="{_escape(model)}",period="{_escape(period)}"'
        )
        lines.append(f"ai_cost_total_usd{{{labels}}} {value:.6f}")

    lines.append("# HELP ai_budget_utilization_pct AI budget utilization percentage.")
    lines.append("# TYPE ai_budget_utilization_pct gauge")
    for (tenant, scope, scope_id), value in sorted(ai_budget_utilization_pct.items()):
        labels = f'tenant_id="{_escape(tenant)}",scope="{_escape(scope)}",scope_id="{_escape(scope_id)}"'
        lines.append(f"ai_budget_utilization_pct{{{labels}}} {value:.2f}")

    lines.append("# HELP ai_budget_exceeded_total Total AI budget exceeded events.")
    lines.append("# TYPE ai_budget_exceeded_total counter")
    for (tenant, scope), count in sorted(ai_budget_exceeded_total.items()):
        labels = f'tenant_id="{_escape(tenant)}",scope="{_escape(scope)}"'
        lines.append(f"ai_budget_exceeded_total{{{labels}}} {count}")

    lines.append("# HELP ai_cost_anomaly_detected_total Total detected AI cost anomalies.")
    lines.append("# TYPE ai_cost_anomaly_detected_total counter")
    for tenant, count in sorted(ai_cost_anomaly_detected_total.items()):
        labels = f'tenant_id="{_escape(tenant)}"'
        lines.append(f"ai_cost_anomaly_detected_total{{{labels}}} {count}")

    lines.append("# HELP ai_slo_compliance_pct AI SLO compliance percentage by model and metric.")
    lines.append("# TYPE ai_slo_compliance_pct gauge")
    for (model, metric), value in sorted(ai_slo_compliance_pct.items()):
        labels = f'model="{_escape(model)}",metric="{_escape(metric)}"'
        lines.append(f"ai_slo_compliance_pct{{{labels}}} {value:.2f}")

    lines.append("# HELP ai_slo_breach_total Total AI SLO breach events by model and metric.")
    lines.append("# TYPE ai_slo_breach_total counter")
    for (model, metric), count in sorted(ai_slo_breach_total.items()):
        labels = f'model="{_escape(model)}",metric="{_escape(metric)}"'
        lines.append(f"ai_slo_breach_total{{{labels}}} {count}")

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
    lines.append("# HELP ai_routing_selection_total Total AI routing selections by mode and selection type.")
    lines.append("# TYPE ai_routing_selection_total counter")
    for (tenant, mode, selection), count in sorted(ai_routing_selection_total.items()):
        labels = f'tenant_id="{_escape(tenant)}",mode="{_escape(mode)}",selection="{_escape(selection)}"'
        lines.append(f"ai_routing_selection_total{{{labels}}} {count}")

    lines.append("# HELP ai_guardrail_evaluations_total Total AI guardrail evaluations per stage/detector/decision.")
    lines.append("# TYPE ai_guardrail_evaluations_total counter")
    for (tenant, stage, detector, decision), count in sorted(ai_guardrail_evaluations_total.items()):
        labels = f'tenant_id="{_escape(tenant)}",stage="{_escape(stage)}",detector="{_escape(detector)}",decision="{_escape(decision)}"'
        lines.append(f"ai_guardrail_evaluations_total{{{labels}}} {count}")

    lines.append("# HELP ai_guardrail_blocked_total Total AI guardrail blocks per detector/reason.")
    lines.append("# TYPE ai_guardrail_blocked_total counter")
    for (tenant, detector, reason), count in sorted(ai_guardrail_blocked_total.items()):
        labels = f'tenant_id="{_escape(tenant)}",detector="{_escape(detector)}",reason="{_escape(reason)}"'
        lines.append(f"ai_guardrail_blocked_total{{{labels}}} {count}")

    lines.append("# HELP ai_guardrail_evaluation_duration_seconds_total Sum of AI guardrail evaluation durations.")
    lines.append("# TYPE ai_guardrail_evaluation_duration_seconds_total counter")
    for (tenant, stage), (_, total_duration) in sorted(ai_guardrail_evaluation_duration_seconds.items()):
        labels = f'tenant_id="{_escape(tenant)}",stage="{_escape(stage)}"'
        lines.append(f"ai_guardrail_evaluation_duration_seconds_total{{{labels}}} {total_duration:.6f}")

    lines.append("# HELP ai_guardrail_evaluation_duration_seconds_count Number of AI guardrail evaluations timed.")
    lines.append("# TYPE ai_guardrail_evaluation_duration_seconds_count counter")
    for (tenant, stage), (count, _) in sorted(ai_guardrail_evaluation_duration_seconds.items()):
        labels = f'tenant_id="{_escape(tenant)}",stage="{_escape(stage)}"'
        lines.append(f"ai_guardrail_evaluation_duration_seconds_count{{{labels}}} {count}")

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
