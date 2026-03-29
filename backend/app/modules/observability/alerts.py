from __future__ import annotations

from collections import defaultdict, deque
from datetime import datetime, timezone
import json
import logging
import time
from threading import Lock
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen

from app.core.config import (
    get_ops_alert_cooldown_seconds,
    get_ops_alert_webhook_url,
    get_ops_jobs_failure_spike_threshold,
    get_ops_latency_p95_threshold_ms,
    get_ops_latency_p99_threshold_ms,
)


logger = logging.getLogger("app.ops.alerting")

_lock = Lock()
_last_alert_sent_at: dict[str, float] = {}
_dependency_state: dict[str, bool] = {}
_recent_event_windows: dict[str, deque[float]] = defaultdict(deque)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _send_webhook(payload: dict[str, Any]) -> None:
    webhook_url = get_ops_alert_webhook_url()
    if not webhook_url:
        return

    request = Request(
        webhook_url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(request, timeout=3) as response:
        response.read()


def emit_alert(
    *,
    alert_type: str,
    severity: str,
    summary: str,
    tenant_id: int | None = None,
    details: dict[str, Any] | None = None,
    dedupe_key: str | None = None,
) -> bool:
    key = str(dedupe_key or alert_type).strip().lower() or str(alert_type).strip().lower()
    now = time.time()
    cooldown_seconds = get_ops_alert_cooldown_seconds()

    with _lock:
        previous = _last_alert_sent_at.get(key)
        if previous is not None and now - previous < cooldown_seconds:
            return False
        _last_alert_sent_at[key] = now

    payload = {
        "timestamp": _now_iso(),
        "event": str(alert_type),
        "alert_type": str(alert_type),
        "severity": str(severity),
        "tenant_id": tenant_id,
        "summary": str(summary),
        "details": details or {},
    }

    logger.warning(
        "ops_alert_triggered",
        extra={
            "event_type": alert_type,
            "error_code": str((details or {}).get("error_code", alert_type)),
        },
    )

    try:
        _send_webhook(payload)
    except URLError as exc:
        logger.warning("ops_alert_delivery_failed", extra={"error_code": alert_type, "delivery_error": str(exc)})
    except Exception as exc:  # pragma: no cover - defensive network guard
        logger.warning("ops_alert_delivery_failed", extra={"error_code": alert_type, "delivery_error": str(exc)})
    return True


def observe_dependency_state(
    *,
    component: str,
    healthy: bool,
    details: dict[str, Any] | None = None,
    severity: str = "critical",
    tenant_id: int | None = None,
) -> None:
    normalized = str(component).strip().lower()
    with _lock:
        previous = _dependency_state.get(normalized)
        _dependency_state[normalized] = bool(healthy)

    if previous is None:
        if not healthy:
            emit_alert(
                alert_type=f"{normalized}.unavailable",
                severity=severity,
                summary=f"{normalized} is unavailable",
                tenant_id=tenant_id,
                details=details,
                dedupe_key=f"dependency:{normalized}:down",
            )
        return

    if previous and not healthy:
        emit_alert(
            alert_type=f"{normalized}.unavailable",
            severity=severity,
            summary=f"{normalized} is unavailable",
            tenant_id=tenant_id,
            details=details,
            dedupe_key=f"dependency:{normalized}:down",
        )
        return

    if not previous and healthy:
        logger.info(
            "dependency_recovered",
            extra={"event_type": "recovery", "error_code": f"{normalized}.recovered"},
        )
        emit_alert(
            alert_type=f"{normalized}.recovered",
            severity="info",
            summary=f"{normalized} recovered",
            tenant_id=tenant_id,
            details=details,
            dedupe_key=f"dependency:{normalized}:recovered",
        )


def observe_event_spike(
    *,
    event_name: str,
    threshold: int,
    window_seconds: int,
    severity: str,
    summary: str,
    tenant_id: int | None = None,
    details: dict[str, Any] | None = None,
) -> None:
    now = time.time()
    normalized = str(event_name).strip().lower()
    with _lock:
        bucket = _recent_event_windows[normalized]
        cutoff = now - int(window_seconds)
        while bucket and bucket[0] <= cutoff:
            bucket.popleft()
        bucket.append(now)
        current = len(bucket)

    if current >= int(threshold):
        emit_alert(
            alert_type=f"{normalized}.spike",
            severity=severity,
            summary=summary,
            tenant_id=tenant_id,
            details={**(details or {}), "count": current, "window_seconds": int(window_seconds)},
            dedupe_key=f"spike:{normalized}",
        )


def observe_latency_spike(p95_latency_ms: float, p99_latency_ms: float, requests_per_minute: int, tenant_id: int | None = None) -> None:
    if requests_per_minute <= 0:
        return
    threshold_p95 = get_ops_latency_p95_threshold_ms()
    threshold_p99 = get_ops_latency_p99_threshold_ms()
    if p95_latency_ms < threshold_p95 and p99_latency_ms < threshold_p99:
        return

    emit_alert(
        alert_type="http.latency.high",
        severity="warning",
        summary="HTTP latency exceeded SRE threshold",
        tenant_id=tenant_id,
        details={
            "p95_latency_ms": round(float(p95_latency_ms), 2),
            "p99_latency_ms": round(float(p99_latency_ms), 2),
            "requests_per_minute": int(requests_per_minute),
            "threshold_p95_ms": int(threshold_p95),
            "threshold_p99_ms": int(threshold_p99),
        },
        dedupe_key="latency:high",
    )


def observe_job_failure_spike(job_type: str | None = None, tenant_id: int | None = None) -> None:
    observe_event_spike(
        event_name="jobs.failures",
        threshold=get_ops_jobs_failure_spike_threshold(),
        window_seconds=10 * 60,
        severity="warning",
        summary="Background job failures exceeded threshold",
        tenant_id=tenant_id,
        details={"job_type": str(job_type or "unknown")},
    )


def clear_alert_state() -> None:
    with _lock:
        _last_alert_sent_at.clear()
        _dependency_state.clear()
        _recent_event_windows.clear()