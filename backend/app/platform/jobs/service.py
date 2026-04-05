from __future__ import annotations

from typing import Any

from fastapi import HTTPException

from app.platform.jobs import legacy_billing_compat
from app.platform.tenant import service as tenant_service
from app.platform.uow import UnitOfWork


def _ensure_platform_tenant_exists(tenant_id: int) -> bool:
    normalized_tenant_id = int(tenant_id)
    try:
        tenant_service.get_tenant_profile(normalized_tenant_id)
        return True
    except ValueError:
        # Transitional compatibility for legacy self-service lifecycle state.
        if legacy_billing_compat.has_legacy_subscription(normalized_tenant_id):
            return False
        raise


def _assert_platform_billing_write_allowed(tenant_id: int, *, action: str, platform_managed: bool) -> None:
    normalized_tenant_id = int(tenant_id)
    if not platform_managed:
        legacy_subscription = legacy_billing_compat.get_legacy_subscription(normalized_tenant_id)
        if legacy_subscription is not None:
            legacy_billing_compat.assert_legacy_billing_write_allowed(
                normalized_tenant_id,
                action=action,
                subscription=legacy_subscription,
            )
        return

    with UnitOfWork() as uow:
        subscription = uow.billing_repository.get_subscription(normalized_tenant_id, conn=uow.conn)
    if subscription is None:
        legacy_subscription = legacy_billing_compat.get_legacy_subscription(normalized_tenant_id)
        if legacy_subscription is not None:
            legacy_billing_compat.assert_legacy_billing_write_allowed(
                normalized_tenant_id,
                action=action,
                subscription=legacy_subscription,
            )
        return

    status = str(subscription.get("status", "trial")).strip().lower()
    if status not in {"trial", "active"}:
        raise HTTPException(
            status_code=403,
            detail=f"billing_required: tenant subscription is '{status}' (read-only mode)",
        )


def enqueue_job(tenant_id: int, job_type: str, payload: dict[str, Any], max_retries: int = 3) -> dict[str, Any]:
    normalized_tenant_id = int(tenant_id)
    platform_managed = _ensure_platform_tenant_exists(normalized_tenant_id)
    _assert_platform_billing_write_allowed(normalized_tenant_id, action="jobs.enqueue", platform_managed=platform_managed)
    with UnitOfWork() as uow:
        return uow.job_repository.enqueue(
            normalized_tenant_id,
            str(job_type),
            dict(payload),
            max_retries=int(max_retries),
            conn=uow.conn,
        )


def get_job(job_id: int) -> dict[str, Any] | None:
    with UnitOfWork() as uow:
        return uow.job_repository.get(int(job_id), conn=uow.conn)


def list_tenant_jobs(tenant_id: int, status: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
    with UnitOfWork() as uow:
        return uow.job_repository.list_for_tenant(int(tenant_id), status=status, limit=limit, conn=uow.conn)


def run_job(job_id: int, succeed: bool, result: dict[str, Any] | None = None, error: str | None = None) -> dict[str, Any]:
    with UnitOfWork() as uow:
        running = uow.job_repository.mark_running(int(job_id), conn=uow.conn)
    if running is None:
        raise ValueError(f"Job {job_id} not found or not runnable")

    if succeed:
        with UnitOfWork() as uow:
            completed = uow.job_repository.mark_succeeded(int(job_id), result or {"status": "ok"}, conn=uow.conn)
        if completed is None:
            raise ValueError(f"Job {job_id} could not be completed")
        return completed

    with UnitOfWork() as uow:
        failed = uow.job_repository.mark_failed(int(job_id), error or "job execution failed", conn=uow.conn)
    if failed is None:
        raise ValueError(f"Job {job_id} could not be failed")
    return failed


def mark_job_running(job_id: int) -> dict[str, Any] | None:
    with UnitOfWork() as uow:
        return uow.job_repository.mark_running(int(job_id), conn=uow.conn)


def mark_job_succeeded(job_id: int, result: dict[str, Any]) -> dict[str, Any] | None:
    with UnitOfWork() as uow:
        return uow.job_repository.mark_succeeded(int(job_id), result, conn=uow.conn)


def mark_job_failed(job_id: int, error: str) -> dict[str, Any] | None:
    with UnitOfWork() as uow:
        return uow.job_repository.mark_failed(int(job_id), error, conn=uow.conn)


def retry_job(job_id: int) -> dict[str, Any]:
    with UnitOfWork() as uow:
        retried = uow.job_repository.requeue_for_retry(int(job_id), "manual retry", conn=uow.conn)
    if retried is None:
        raise ValueError(f"Job {job_id} cannot be retried")
    return retried


def cancel_job(job_id: int) -> dict[str, Any]:
    with UnitOfWork() as uow:
        cancelled = uow.job_repository.cancel(int(job_id), conn=uow.conn)
    if cancelled is None:
        raise ValueError(f"Job {job_id} cannot be cancelled")
    return cancelled


def fetch_queued_jobs(limit: int = 50) -> list[dict[str, Any]]:
    with UnitOfWork() as uow:
        return uow.job_repository.fetch_queued(limit=limit, conn=uow.conn)


def requeue_job(job_id: int, error: str) -> dict[str, Any] | None:
    with UnitOfWork() as uow:
        return uow.job_repository.requeue_for_retry(int(job_id), error, conn=uow.conn)


def clear_jobs_state() -> None:
    with UnitOfWork() as uow:
        uow.job_repository.clear_state(conn=uow.conn)
