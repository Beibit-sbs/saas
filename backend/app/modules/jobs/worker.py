from __future__ import annotations

from typing import Any, Callable

from app.modules.audit.service import list_admin_actions
from app.modules.backup.service import run_backup_now
from app.modules.jobs import service as jobs_service


def _execute_backup_run(job: dict[str, Any]) -> dict[str, Any]:
    actor = str(job.get("created_by") or "system")
    result = run_backup_now(actor=actor, tenant_id=int(job["tenant_id"]))
    return {
        "job_type": "backup.run",
        "backup_job": result,
    }


def _execute_audit_export(job: dict[str, Any]) -> dict[str, Any]:
    payload = job.get("payload_json") or {}
    tenant_id = int(job["tenant_id"])
    export_format = str(payload.get("format") or "json").lower()
    events = list_admin_actions(
        tenant_id=tenant_id,
        actor=payload.get("actor"),
        action=payload.get("action"),
        entity=payload.get("entity"),
        result=payload.get("result"),
        correlation_id=payload.get("correlation_id"),
        since=payload.get("since"),
        limit=min(int(payload.get("limit") or 500), 500),
    )
    return {
        "job_type": "audit.export",
        "format": export_format,
        "rows": len(events),
        "tenant_id": tenant_id,
    }


def _execute_placeholder(job: dict[str, Any]) -> dict[str, Any]:
    return {
        "job_type": job["job_type"],
        "status": "accepted",
        "note": "handler placeholder; implement concrete flow in subsequent phase",
    }


_JOB_HANDLERS: dict[str, Callable[[dict[str, Any]], dict[str, Any]]] = {
    "backup.run": _execute_backup_run,
    "audit.export": _execute_audit_export,
    "ldap.sync": _execute_placeholder,
    "ai.generate": _execute_placeholder,
    "report.generate": _execute_placeholder,
}


def execute_job(job: dict[str, Any]) -> dict[str, Any]:
    job_type = str(job.get("job_type") or "").strip().lower()
    handler = _JOB_HANDLERS.get(job_type)
    if handler is None:
        raise ValueError(f"unsupported job_type: {job_type}")
    return handler(job)


def execute_next_queued_job() -> dict[str, Any] | None:
    job = jobs_service.acquire_next_queued_job()
    if job is None:
        return None

    try:
        result = execute_job(job)
        updated = jobs_service.mark_job_succeeded(int(job["id"]), result)
        return updated
    except Exception as exc:
        updated = jobs_service.mark_job_failed(int(job["id"]), str(exc))
        return updated


def run_worker_loop(iterations: int = 0) -> int:
    processed = 0
    while True:
        row = execute_next_queued_job()
        if row is None:
            break
        processed += 1
        if iterations > 0 and processed >= iterations:
            break
    return processed
