from __future__ import annotations

from app.platform.jobs.scheduler import PlatformWorkerScheduler


def test_scheduler_runs_due_tasks_once() -> None:
    counter = {"calls": 0}

    def _task() -> dict[str, object]:
        counter["calls"] += 1
        return {"ok": True}

    scheduler = PlatformWorkerScheduler()
    scheduler.register_task("test-fast", interval_seconds=1, task=_task)

    first = scheduler.run_due_tasks_once()
    assert first["triggered"] >= 1

    second = scheduler.run_due_tasks_once()
    # Default tasks may or may not trigger immediately depending on state,
    # but our custom task must not run twice without interval.
    assert counter["calls"] == 1
    assert second["triggered"] >= 0


def test_scheduler_registers_application_service_tasks() -> None:
    scheduler = PlatformWorkerScheduler()
    task_names = set(scheduler._tasks.keys())  # noqa: SLF001 - acceptable for scheduler wiring validation

    assert "daily_usage_aggregation" in task_names
    assert "subscription_rollover" in task_names
    assert "notification_retry_dispatch" in task_names
