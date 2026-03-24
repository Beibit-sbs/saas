from __future__ import annotations

import logging
import threading
import time
from typing import Callable

from app.modules.audit.service import log_admin_action
from app.platform.jobs import service as jobs_service

logger = logging.getLogger("app.platform.worker")


class PlatformJobWorker:
    def __init__(
        self,
        handlers: dict[str, Callable[[dict], dict]] | None = None,
        poll_interval_seconds: float = 1.0,
        batch_size: int = 20,
    ) -> None:
        self._handlers = handlers or {}
        self._poll_interval_seconds = max(0.05, float(poll_interval_seconds))
        self._batch_size = max(1, int(batch_size))

    def _handler_for(self, job_type: str) -> Callable[[dict], dict]:
        return self._handlers.get(job_type, lambda payload: {"ok": True, "echo": payload})

    def run_once(self) -> dict[str, int]:
        queued = jobs_service.fetch_queued_jobs(limit=self._batch_size)
        processed = 0
        succeeded = 0
        retried = 0
        failed = 0

        for job in queued:
            processed += 1
            job_id = int(job["id"])
            tenant_id = int(job["tenant_id"])
            job_type = str(job["job_type"])

            started = jobs_service.mark_job_running(job_id)
            if started is None:
                # Another worker or manual operation might have moved state.
                continue

            try:
                handler = self._handler_for(job_type)
                result = handler(dict(job.get("payload") or {}))
                completed = jobs_service.mark_job_succeeded(job_id, result)
                if completed is None:
                    raise RuntimeError("job transition to succeeded failed")
                logger.info("platform_job_succeeded", extra={"job_id": job_id, "job_type": job_type})
                log_admin_action(
                    actor="platform-worker",
                    tenant_id=tenant_id,
                    action="platform_core.jobs.succeeded",
                    path="/api/v1/internal/worker/run-once",
                    client_ip="worker",
                    correlation_id=None,
                    entity="platform-core",
                    result="success",
                    metadata={"job_id": job_id, "job_type": job_type, "status": completed["status"]},
                )
                succeeded += 1
            except Exception as exc:
                current = jobs_service.get_job(job_id)
                retry_count = int(current.get("retry_count", 0)) if current else 0
                max_retries = int(current.get("max_retries", 0)) if current else 0
                if retry_count < max_retries:
                    jobs_service.requeue_job(job_id, str(exc))
                    retried += 1
                    outcome = "retry"
                else:
                    jobs_service.mark_job_failed(job_id, str(exc))
                    failed += 1
                    outcome = "failed"

                logger.exception("platform_job_failed", extra={"job_id": job_id, "job_type": job_type, "outcome": outcome})
                log_admin_action(
                    actor="platform-worker",
                    tenant_id=tenant_id,
                    action="platform_core.jobs.failed",
                    path="/api/v1/internal/worker/run-once",
                    client_ip="worker",
                    correlation_id=None,
                    entity="platform-core",
                    result=outcome,
                    metadata={"job_id": job_id, "job_type": job_type, "error": str(exc)},
                )

        return {"processed": processed, "succeeded": succeeded, "retried": retried, "failed": failed}

    def run_forever(self, stop_event: threading.Event | None = None) -> None:
        event = stop_event or threading.Event()
        while not event.is_set():
            self.run_once()
            time.sleep(self._poll_interval_seconds)


worker = PlatformJobWorker()
