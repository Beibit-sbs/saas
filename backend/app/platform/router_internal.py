from __future__ import annotations

from app.platform.analytics import service as analytics_service
from app.platform.analytics.schemas import TenantKpiSnapshotRead
from app.platform.kpi import service as kpi_service
from app.platform.kpi.schemas import RectorDashboardReadSchema
import os

from fastapi import APIRouter, Header, HTTPException

from app.platform.jobs import service as jobs_service
from app.platform.jobs.scheduler import scheduler
from app.platform.jobs.worker import worker
from app.platform.notifications import service as notifications_service
from app.platform.schemas import JobRead, JobRunRequest, NotificationRead
from app.platform.uow import UnitOfWork
from app.platform.webhooks.dispatcher import webhook_dispatcher
from app.platform.webhooks.schemas import WebhookRetryResponseSchema

router = APIRouter(prefix="/api/v1/internal", tags=["platform-core-internal"])


def _require_internal_token(authorization: str | None) -> None:
    configured = os.getenv("PLATFORM_INTERNAL_TOKEN", "").strip()
    if not configured:
        return
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="internal token required")
    provided = authorization[len("Bearer ") :].strip()
    if provided != configured:
        raise HTTPException(status_code=403, detail="invalid internal token")


@router.post("/jobs/{job_id}/run", response_model=JobRead)
def run_job(job_id: int, payload: JobRunRequest, authorization: str | None = Header(default=None)) -> JobRead:
    _require_internal_token(authorization)
    row = jobs_service.run_job(job_id, succeed=payload.succeed, result=payload.result, error=payload.error)
    return JobRead.model_validate(row)


@router.post("/jobs/{job_id}/retry", response_model=JobRead)
def retry_job(job_id: int, authorization: str | None = Header(default=None)) -> JobRead:
    _require_internal_token(authorization)
    row = jobs_service.retry_job(job_id)
    return JobRead.model_validate(row)


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
