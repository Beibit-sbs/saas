from __future__ import annotations

from typing import Any

from app.platform.uow import UnitOfWork


def enqueue_job(tenant_id: int, job_type: str, payload: dict[str, Any], max_retries: int = 3) -> dict[str, Any]:
    with UnitOfWork() as uow:
        return uow.job_repository.enqueue(int(tenant_id), job_type, payload, int(max_retries), conn=uow.conn)


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
