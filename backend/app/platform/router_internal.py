from __future__ import annotations

from app.platform.analytics import service as analytics_service
from app.platform.analytics.schemas import TenantKpiSnapshotRead
from app.platform.kpi import service as kpi_service
from app.platform.kpi.schemas import RectorDashboardReadSchema
from app.platform.automation import service as automation_service
from app.platform.context import service as context_service
from app.platform.context.schemas import StudentProfileRead
from app.platform.events.schemas import OutboxEventRead
import hmac

from fastapi import APIRouter, Header, HTTPException

from app.core.config import get_internal_api_token
from app.platform.jobs import service as jobs_service
from app.platform.jobs.scheduler import scheduler
from app.platform.jobs.worker import worker
from app.platform.notifications import service as notifications_service
from app.platform.schemas import JobRead, JobRunRequest, NotificationRead
from app.platform.uow import UnitOfWork
from app.platform.webhooks.dispatcher import webhook_dispatcher
from app.platform.webhooks.schemas import WebhookRetryResponseSchema

router = APIRouter(prefix="/api/v1/internal", tags=["platform-core-internal"])


def _legacy_job_read(row: dict[str, object]) -> JobRead:
    return JobRead.model_validate(
        {
            "id": int(row.get("id") or 0),
            "tenant_id": int(row.get("tenant_id") or 0),
            "job_type": str(row.get("job_type") or ""),
            "status": str(row.get("status") or ""),
            "retry_count": int(row.get("retry_count") or 0),
            "max_retries": int(row.get("max_retries") or 0),
            "payload": dict(row.get("payload") or row.get("payload_json") or {}),
            "result": row.get("result") or row.get("result_json"),
            "error": row.get("error") or row.get("error_message"),
            "created_at": str(row.get("created_at") or ""),
            "updated_at": str(row.get("updated_at") or row.get("finished_at") or row.get("started_at") or row.get("created_at") or ""),
        }
    )


def _require_internal_token(authorization: str | None) -> None:
    configured = get_internal_api_token()
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="internal token required")
    provided = authorization[len("Bearer ") :].strip()
    if not hmac.compare_digest(provided.encode(), configured.encode()):
        raise HTTPException(status_code=403, detail="invalid internal token")


@router.post("/jobs/{job_id}/run", response_model=JobRead)
def run_job(job_id: int, payload: JobRunRequest, authorization: str | None = Header(default=None)) -> JobRead:
    _require_internal_token(authorization)
    row = jobs_service.run_job(job_id, succeed=payload.succeed, result=payload.result, error=payload.error)
    return _legacy_job_read(row)


@router.post("/jobs/{job_id}/retry", response_model=JobRead)
def retry_job(job_id: int, authorization: str | None = Header(default=None)) -> JobRead:
    _require_internal_token(authorization)
    row = jobs_service.retry_job(job_id)
    return _legacy_job_read(row)


@router.post("/worker/run-once")
def run_worker_once(authorization: str | None = Header(default=None)) -> dict[str, int]:
    _require_internal_token(authorization)
    return worker.run_once()


@router.post("/scheduler/run-once")
def run_scheduler_once(authorization: str | None = Header(default=None)) -> dict[str, int]:
    _require_internal_token(authorization)
    return scheduler.run_due_tasks_once()


@router.get("/tenants/{tenant_id}/notifications", response_model=list[NotificationRead])
def list_notifications(tenant_id: int, authorization: str | None = Header(default=None)) -> list[NotificationRead]:
    _require_internal_token(authorization)
    rows = notifications_service.list_notifications(tenant_id)
    return [NotificationRead.model_validate(item) for item in rows]


@router.post("/webhooks/retry-failed", response_model=WebhookRetryResponseSchema)
def retry_failed_webhooks(limit: int = 100, authorization: str | None = Header(default=None)) -> WebhookRetryResponseSchema:
    _require_internal_token(authorization)
    result = webhook_dispatcher.retry_failed_deliveries(limit=max(1, min(int(limit), 500)), actor="platform-internal")
    return WebhookRetryResponseSchema.model_validate(result)


@router.get("/webhooks/failed-deliveries")
def list_failed_deliveries(
    limit: int = 50,
    tenant_id: int | None = None,
    authorization: str | None = Header(default=None),
) -> dict[str, object]:
    """List failed/stuck webhook deliveries for operational visibility."""
    _require_internal_token(authorization)
    from datetime import datetime, timezone
    with UnitOfWork() as uow:
        # Get failed deliveries from repository
        deliveries = uow.webhook_repository.fetch_retryable_deliveries(
            as_of=datetime.now(timezone.utc),
            limit=max(1, min(int(limit), 500)),
            max_retry_count=5,
            conn=uow.conn,
        )
        # Filter by tenant if specified
        if tenant_id:
            deliveries = [d for d in deliveries if d.get("tenant_id") == int(tenant_id)]
        return {
            "failed_deliveries_count": len(deliveries),
            "deliveries": [
                {
                    "id": d.get("id"),
                    "tenant_id": d.get("tenant_id"),
                    "subscription_id": d.get("subscription_id"),
                    "outbox_event_id": d.get("outbox_event_id"),
                    "target_url": d.get("target_url"),
                    "event_type": d.get("event_type"),
                    "retry_count": d.get("retry_count"),
                    "last_error": d.get("last_error"),
                    "next_retry_at": d.get("next_retry_at"),
                    "created_at": d.get("created_at"),
                }
                for d in deliveries
            ],
        }


@router.post("/analytics/tenants/{tenant_id}/kpis/refresh", response_model=TenantKpiSnapshotRead)
def refresh_tenant_kpis(
    tenant_id: int,
    authorization: str | None = Header(default=None),
) -> TenantKpiSnapshotRead:
    _require_internal_token(authorization)
    with UnitOfWork() as uow:
        snap = analytics_service.refresh_tenant_kpis(tenant_id=tenant_id, uow=uow)
    return TenantKpiSnapshotRead.model_validate(snap)


@router.post("/platform/kpi/refresh")
def refresh_all_tenant_kpi(authorization: str | None = Header(default=None)) -> dict[str, int]:
    _require_internal_token(authorization)
    with UnitOfWork() as uow:
        return kpi_service.refresh_all_tenants(uow=uow)


@router.post("/platform/kpi/refresh/{tenant_id}", response_model=RectorDashboardReadSchema)
def refresh_tenant_kpi(tenant_id: int, authorization: str | None = Header(default=None)) -> RectorDashboardReadSchema:
    _require_internal_token(authorization)
    with UnitOfWork() as uow:
        kpi_service.refresh_tenant_metrics(tenant_id=tenant_id, uow=uow)
        dashboard = kpi_service.refresh_tenant_dashboard_snapshot(tenant_id=tenant_id, uow=uow)
    return RectorDashboardReadSchema.model_validate(dashboard.get("snapshot_json") or {})


@router.post("/platform/automation/evaluate")
def evaluate_automation_event(
    body: OutboxEventRead,
    authorization: str | None = Header(default=None),
) -> dict[str, object]:
    """Manually trigger automation rule evaluation for a given event payload."""
    _require_internal_token(authorization)
    with UnitOfWork() as uow:
        return automation_service.evaluate_event(body, uow=uow)


# ------------------------------------------------------------------ #
#  Context Layer                                                        #
# ------------------------------------------------------------------ #

@router.get("/context/student/{student_id}", response_model=StudentProfileRead)
def get_student_context_internal(
    student_id: str,
    tenant_id: int,
    authorization: str | None = Header(default=None),
) -> StudentProfileRead:
    """Return the full semantic profile for a student (internal-scoped)."""
    _require_internal_token(authorization)
    with UnitOfWork() as uow:
        profile = context_service.build_student_profile(
            student_id=student_id,
            tenant_id=tenant_id,
            conn=uow.conn,
        )
    return StudentProfileRead.model_validate(profile)


@router.post("/platform/ai/copilot/rebuild-cache")
def rebuild_ai_copilot_cache(authorization: str | None = Header(default=None)) -> dict[str, object]:
    """Placeholder for future cache/materialization rebuild hooks."""
    _require_internal_token(authorization)
    return {"status": "noop", "component": "ai_copilot_foundation_v1", "read_only": True}
