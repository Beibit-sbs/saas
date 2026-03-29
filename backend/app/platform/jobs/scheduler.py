from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import threading
import time
from typing import Callable

from app.modules.observability.metrics import observe_job_execution
from app.platform.application.notification_dispatch_service import NotificationDispatchService
from app.platform.application.subscription_rollover_service import SubscriptionRolloverService
from app.platform.context import service as context_service
from app.platform.events.worker import outbox_worker
from app.platform.jobs.worker import worker
from app.platform.kpi import service as kpi_service
from app.platform.runtime_state import record_scheduler_run, record_worker_heartbeat
from app.platform.uow import UnitOfWork
from app.platform.webhooks.dispatcher import webhook_dispatcher


SchedulerTask = Callable[[], dict[str, object] | None]


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(slots=True)
class _TaskDef:
    name: str
    interval_seconds: int
    task: SchedulerTask
    last_run_at: datetime | None = None


class PlatformWorkerScheduler:
    def __init__(self) -> None:
        self._tasks: dict[str, _TaskDef] = {}
        self._lock = threading.Lock()
        self._rollover_service = SubscriptionRolloverService()
        self._notification_dispatch_service = NotificationDispatchService()

        self.register_task("daily_usage_aggregation", interval_seconds=24 * 60 * 60, task=self._daily_usage_aggregation)
        self.register_task("subscription_rollover", interval_seconds=60 * 60, task=self._subscription_rollover)
        self.register_task("notification_retry_dispatch", interval_seconds=10 * 60, task=self._notification_retry_dispatch)
        self.register_task("outbox_event_dispatch", interval_seconds=60, task=self._outbox_event_dispatch)
        self.register_task("webhook_retry_dispatch", interval_seconds=2 * 60, task=self._webhook_retry_dispatch)
        self.register_task("kpi_metrics_refresh", interval_seconds=24 * 60 * 60, task=self._kpi_metrics_refresh)
        self.register_task("context_rebuild", interval_seconds=24 * 60 * 60, task=self._context_rebuild)

    def register_task(self, name: str, *, interval_seconds: int, task: SchedulerTask) -> None:
        normalized = name.strip().lower()
        if not normalized:
            raise ValueError("task name is required")
        if int(interval_seconds) <= 0:
            raise ValueError("interval_seconds must be positive")
        with self._lock:
            self._tasks[normalized] = _TaskDef(
                name=normalized,
                interval_seconds=int(interval_seconds),
                task=task,
            )

    def run_due_tasks_once(self) -> dict[str, int]:
        now = _now_utc()
        triggered = 0
        succeeded = 0
        failed = 0

        with self._lock:
            tasks = list(self._tasks.values())

        for item in tasks:
            due = item.last_run_at is None or (now - item.last_run_at).total_seconds() >= item.interval_seconds
            if not due:
                continue

            triggered += 1
            try:
                item.task()
                succeeded += 1
                observe_job_execution(outcome="success")
            except Exception:
                failed += 1
                observe_job_execution(outcome="failed")
            finally:
                item.last_run_at = now
                record_scheduler_run(item.name)
                record_worker_heartbeat()

        return {"triggered": triggered, "succeeded": succeeded, "failed": failed}

    def run_forever(self, poll_interval_seconds: float = 5.0, stop_event: threading.Event | None = None) -> None:
        event = stop_event or threading.Event()
        while not event.is_set():
            self.run_due_tasks_once()
            time.sleep(max(0.2, float(poll_interval_seconds)))

    def _daily_usage_aggregation(self) -> dict[str, object]:
        # Use worker queue processing as a generic periodic engine in Sprint C.
        return worker.run_once()

    def _subscription_rollover(self) -> dict[str, object]:
        return self._rollover_service.run_rollover_cycle(actor="platform-scheduler")

    def _notification_retry_dispatch(self) -> dict[str, object]:
        return self._notification_dispatch_service.retry_failed_deliveries(actor="platform-scheduler")

    def _outbox_event_dispatch(self) -> dict[str, object]:
        return outbox_worker.run_once()

    def _webhook_retry_dispatch(self) -> dict[str, object]:
        return webhook_dispatcher.retry_failed_deliveries(limit=100, actor="platform-scheduler")

    def _kpi_metrics_refresh(self) -> dict[str, int]:
        with UnitOfWork() as uow:
            return kpi_service.refresh_all_tenants(uow=uow)

    def _context_rebuild(self) -> dict[str, object]:
        tenants = []
        with UnitOfWork() as uow:
            try:
                tenants = list(uow.tenant_repository.list_tenants(conn=uow.conn) or [])
            except Exception:
                pass
        rebuilt = 0
        for tenant in tenants:
            tid = int(tenant.get("tenant_id") or tenant.get("id") or 0)
            if tid:
                context_service.rebuild_context_for_tenant(tenant_id=tid)
                rebuilt += 1
        return {"tenants_processed": rebuilt}


scheduler = PlatformWorkerScheduler()
