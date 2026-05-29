from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request

from app.modules.backup.service import list_backup_history
from app.modules.observability.metrics import snapshot_latency_metrics
from app.modules.rbac.security import permission_dependency, resolve_current_user_claims
from app.platform.runtime_state import get_scheduler_last_run, get_worker_heartbeat
from app.platform.uow import UnitOfWork

router = APIRouter(prefix="/api/v1/platform/ops", tags=["platform-ops"])
bff_router = APIRouter(prefix="/api/bff/v1/platform/ops", tags=["platform-ops-bff"])


def _safe_metric_int(loader) -> int | None:
    try:
        value = loader()
    except Exception:
        return None
    return int(value)


def _parse_iso(raw: str | None) -> datetime | None:
    if not raw:
        return None
    try:
        return datetime.fromisoformat(str(raw))
    except Exception:
        return None


def _age_seconds(raw: str | None) -> float | None:
    value = _parse_iso(raw)
    if value is None:
        return None
    return max(0.0, (datetime.now(timezone.utc) - value).total_seconds())


def _resolve_request_tenant_id(request: Request) -> int:
    claims = resolve_current_user_claims(request, request.headers.get("authorization"))
    tenant_id = int(claims.tenant_id)
    if tenant_id <= 0:
        raise HTTPException(status_code=403, detail="tenant context missing")
    return tenant_id


def _build_ops_summary_payload(tenant_id: int) -> dict[str, Any]:
    latency = dict(snapshot_latency_metrics())

    with UnitOfWork() as uow:
        outbox_backlog = _safe_metric_int(lambda: uow.outbox_event_repository.count_backlog(conn=uow.conn))
        failed_webhooks = _safe_metric_int(lambda: uow.webhook_repository.count_failed_deliveries(conn=uow.conn))
        dead_webhooks = _safe_metric_int(lambda: uow.webhook_repository.count_dead_deliveries(conn=uow.conn))
        retry_backlog = _safe_metric_int(lambda: uow.webhook_repository.count_retry_backlog(conn=uow.conn))
        failed_jobs = _safe_metric_int(lambda: uow.job_repository.count_by_status("failed", conn=uow.conn))
        dead_jobs = _safe_metric_int(lambda: uow.job_repository.count_dead_jobs(conn=uow.conn))
        failed_automation = _safe_metric_int(lambda: uow.automation_repository.count_failed_executions(conn=uow.conn))
        dead_automation = _safe_metric_int(lambda: uow.automation_repository.count_failed_executions(conn=uow.conn))

    # Keep `event_queue_size` for backward compatibility, but derive it from
    # queue components so it is no longer a direct duplicate of `outbox_backlog`.
    if outbox_backlog is not None and retry_backlog is not None:
        event_queue_size = int(outbox_backlog) + int(retry_backlog)
    else:
        event_queue_size = outbox_backlog if outbox_backlog is not None else retry_backlog

    worker_heartbeat = get_worker_heartbeat()
    scheduler_state = get_scheduler_last_run() or {}
    scheduler_heartbeat = str(scheduler_state.get("at")) if scheduler_state.get("at") else None

    total_errors = int(latency.get("http_4xx_count", 0) or 0) + int(latency.get("http_5xx_count", 0) or 0)
    rpm = int(latency.get("requests_per_minute", 0) or 0)
    error_rate = float(total_errors / rpm) if rpm > 0 else 0.0

    backup_history = list_backup_history(tenant_id=tenant_id)
    last_backup = backup_history[0] if backup_history else None

    return {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "tenant_id": tenant_id,
        "data_source": "computed_from_runtime_health",
        "fake_metrics": False,
        "latency": {
            "p50_ms": float(latency.get("p50_latency_ms", 0.0) or 0.0),
            "p95_ms": float(latency.get("p95_latency_ms", 0.0) or 0.0),
            "p99_ms": float(latency.get("p99_latency_ms", 0.0) or 0.0),
        },
        "traffic": {
            "requests_per_minute": rpm,
            "http_4xx_count": int(latency.get("http_4xx_count", 0) or 0),
            "http_5xx_count": int(latency.get("http_5xx_count", 0) or 0),
            "error_rate": round(error_rate, 4),
        },
        "runtime": {
            "worker_heartbeat": worker_heartbeat,
            "worker_heartbeat_age_seconds": _age_seconds(worker_heartbeat),
            "scheduler_heartbeat": scheduler_heartbeat,
            "scheduler_heartbeat_age_seconds": _age_seconds(scheduler_heartbeat),
        },
        "queues": {
            "event_queue_size": event_queue_size,
            "outbox_backlog": outbox_backlog,
            "retry_backlog": retry_backlog,
            "failed_webhooks": failed_webhooks,
            "dead_webhooks": dead_webhooks,
            "failed_jobs": failed_jobs,
            "dead_jobs": dead_jobs,
            "failed_automation_executions": failed_automation,
            "dead_automation_executions": dead_automation,
            "dead_count": int(dead_webhooks or 0) + int(dead_jobs or 0) + int(dead_automation or 0),
        },
        "backup": {
            "last_status": str(last_backup.get("status")) if isinstance(last_backup, dict) and last_backup.get("status") else "unknown",
            "last_started_at": str(last_backup.get("started_at")) if isinstance(last_backup, dict) and last_backup.get("started_at") else None,
            "last_finished_at": str(last_backup.get("finished_at")) if isinstance(last_backup, dict) and last_backup.get("finished_at") else None,
            "last_error": str(last_backup.get("error")) if isinstance(last_backup, dict) and last_backup.get("error") else None,
        },
    }


@router.get("/summary")
@bff_router.get("/summary")
def get_ops_summary(
    request: Request,
    __: None = Depends(permission_dependency("ops.read")),
) -> dict[str, Any]:
    tenant_id = _resolve_request_tenant_id(request)
    return _build_ops_summary_payload(tenant_id)
