from __future__ import annotations

import logging
import time
from collections import defaultdict, deque
from threading import Lock

from app.core.config import get_ops_login_failure_spike_threshold
from app.modules.observability.alerts import emit_alert


logger = logging.getLogger("app.security")

_lock = Lock()

# security_events_total{name,outcome}
_security_events_total: dict[tuple[str, str], int] = defaultdict(int)

# security_anomalies_total{name}
_security_anomalies_total: dict[str, int] = defaultdict(int)

# Recent event timestamps by (signal, bucket) for thresholding.
_recent_events: dict[tuple[str, str], deque[float]] = defaultdict(deque)

_ANOMALY_WINDOW_SECONDS = 10 * 60
_ANOMALY_THRESHOLDS: dict[str, int] = {
    "tenant.override.denied": 3,
    "auth.login.failed": get_ops_login_failure_spike_threshold(),
    "auth.refresh.failed": 4,
    "auth.csrf.failed": 5,
    "auth.token.revoked_reuse": 2,
    "platform.access.denied": 3,
    "metrics.access.denied": 3,
    "rate_limit.blocked": 5,
}


def _prune_bucket(bucket: deque[float], now: float) -> None:
    cutoff = now - _ANOMALY_WINDOW_SECONDS
    while bucket and bucket[0] <= cutoff:
        bucket.popleft()


def _bucket_id(actor: str | None, client_ip: str | None) -> str:
    actor_value = (actor or "").strip().lower()
    if actor_value:
        return f"actor:{actor_value}"
    ip_value = (client_ip or "").strip().lower()
    if ip_value:
        return f"ip:{ip_value}"
    return "unknown"


def record_security_signal(
    *,
    signal: str,
    outcome: str,
    actor: str | None = None,
    client_ip: str | None = None,
    path: str | None = None,
    tenant_id: int | None = None,
) -> None:
    normalized_signal = str(signal).strip().lower()
    normalized_outcome = str(outcome).strip().lower() or "observed"
    if not normalized_signal:
        return

    now = time.time()
    bucket_id = _bucket_id(actor, client_ip)

    with _lock:
        _security_events_total[(normalized_signal, normalized_outcome)] += 1

        threshold = _ANOMALY_THRESHOLDS.get(normalized_signal)
        if threshold is None:
            return

        bucket = _recent_events[(normalized_signal, bucket_id)]
        _prune_bucket(bucket, now)
        bucket.append(now)
        if len(bucket) < threshold:
            return

        _security_anomalies_total[normalized_signal] += 1

    if normalized_signal == "auth.login.failed":
        emit_alert(
            alert_type="auth.login.failed.spike",
            severity="warning",
            summary="Login failure spike detected",
            details={
                "signal": normalized_signal,
                "threshold": threshold,
                "bucket": bucket_id,
                "path": path or "",
                "tenant_id": tenant_id,
            },
            dedupe_key="security:auth.login.failed",
        )

    logger.warning(
        "security_anomaly signal=%s bucket=%s count=%s window_seconds=%s path=%s tenant_id=%s",
        normalized_signal,
        bucket_id,
        threshold,
        _ANOMALY_WINDOW_SECONDS,
        path or "",
        tenant_id,
    )


def snapshot_security_metrics() -> tuple[dict[tuple[str, str], int], dict[str, int]]:
    with _lock:
        return dict(_security_events_total), dict(_security_anomalies_total)


def clear_security_signal_state() -> None:
    with _lock:
        _security_events_total.clear()
        _security_anomalies_total.clear()
        _recent_events.clear()
