from __future__ import annotations
from app.core.db import get_raw_conn
from app.core.config import is_runtime_schema_bootstrap_enabled

from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
import json
import logging
import os
import time
from threading import Lock

_jobs_schema_ready = False
_jobs_schema_lock = Lock()
from typing import Any

from app.modules.tenants.service import get_tenant

try:
    import psycopg
except ImportError:  # pragma: no cover
    psycopg = None


VALID_JOB_STATUSES = {"queued", "running", "succeeded", "failed", "cancelled"}
ACTIVE_JOB_STATUSES = ("queued", "running")
DEFAULT_MAX_RETRIES = 3


@dataclass
class JobsMemoryState:
    rows: dict[int, dict[str, Any]] = field(default_factory=dict)
    counter: int = 0


_jobs_lock = Lock()
_jobs_state = JobsMemoryState()
_logger = logging.getLogger("app.dependency")


def _log_jobs_db_fallback(operation: str, started_at: float, exc: Exception) -> None:
    _logger.warning(
        "dependency_fallback",
        extra={
            "dependency": "jobs_db",
            "operation": operation,
            "reason": str(exc),
            "timing_ms": round((time.perf_counter() - started_at) * 1000.0, 2),
        },
    )


def _db_url() -> str | None:
    return os.getenv("DATABASE_URL")


def _use_database() -> bool:
    return bool(_db_url()) and psycopg is not None


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _now_iso() -> str:
    return _now().isoformat()


def _normalize_tenant_id(value: int | str) -> int:
    tenant_id = int(value)
    if tenant_id <= 0:
        raise ValueError("tenant_id must be positive")
    return tenant_id


def _normalize_job_type(value: str) -> str:
    job_type = str(value or "").strip().lower()
    if not job_type:
        raise ValueError("job_type is required")
    return job_type


def _normalize_status(value: str) -> str:
    status = str(value or "").strip().lower()
    if status not in VALID_JOB_STATUSES:
        raise ValueError("invalid job status")
    return status


def _to_json_safe(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        data = value
    else:
        data = {"value": value}
    serialized = json.dumps(data, ensure_ascii=False, default=str)
    parsed = json.loads(serialized)
    if not isinstance(parsed, dict):
        return {"value": parsed}
    return parsed


def _payload_hash(payload: dict[str, Any]) -> str:
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _build_dedup_key(tenant_id: int, job_type: str, payload_hash: str) -> str:
    return f"{tenant_id}:{job_type}:{payload_hash}:active"


def _mark_deduplicated(row: dict[str, Any], dedup_key: str) -> dict[str, Any]:
    payload = dict(row)
    payload["deduplicated"] = True
    payload["dedup_key"] = dedup_key
    return payload


def _ensure_tenant_exists(tenant_id: int) -> None:
    tenant = get_tenant(tenant_id)
    if tenant is None:
        raise ValueError(f"Tenant {tenant_id} not found")


def _row_to_job(row: tuple[Any, ...]) -> dict[str, Any]:
    payload_json = row[4]
    result_json = row[5]

    if isinstance(payload_json, str):
        payload_json = json.loads(payload_json)
    if isinstance(result_json, str):
        result_json = json.loads(result_json)

    return {
        "id": int(row[0]),
        "tenant_id": int(row[1]),
        "job_type": str(row[2]),
        "status": str(row[3]),
        "payload_json": payload_json if isinstance(payload_json, dict) else {},
        "result_json": result_json if isinstance(result_json, dict) else None,
        "error_message": row[6],
        "retry_count": int(row[7]),
        "max_retries": int(row[8]),
        "created_at": row[9].isoformat() if hasattr(row[9], "isoformat") else str(row[9]),
        "started_at": row[10].isoformat() if row[10] is not None and hasattr(row[10], "isoformat") else None,
        "finished_at": row[11].isoformat() if row[11] is not None and hasattr(row[11], "isoformat") else None,
        "created_by": row[12],
    }


def _ensure_schema(conn) -> None:
    if not is_runtime_schema_bootstrap_enabled():
        return
    with conn.cursor() as cur:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS app_jobs (
                id BIGSERIAL PRIMARY KEY,
                tenant_id BIGINT NOT NULL REFERENCES app_tenants(id),
                job_type TEXT NOT NULL,
                status TEXT NOT NULL,
                payload_json JSONB NOT NULL,
                result_json JSONB,
                error_message TEXT,
                retry_count INTEGER NOT NULL DEFAULT 0,
                max_retries INTEGER NOT NULL DEFAULT 3,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                started_at TIMESTAMPTZ,
                finished_at TIMESTAMPTZ,
                created_by TEXT
            )
            """
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS ix_app_jobs_tenant_status_created ON app_jobs (tenant_id, status, created_at DESC)"
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS ix_app_jobs_status_created ON app_jobs (status, created_at DESC)"
        )
    conn.commit()



def _ensure_schema_once(conn) -> None:
    global _jobs_schema_ready
    if _jobs_schema_ready:
        return
    with _jobs_schema_lock:
        if _jobs_schema_ready:
            return
        _ensure_schema(conn)
        _jobs_schema_ready = True


def _enqueue_job_db(
    tenant_id: int,
    job_type: str,
    payload: dict[str, Any],
    created_by: str | None,
    max_retries: int,
) -> dict[str, Any]:
    assert _db_url() and psycopg is not None
    payload_json = json.dumps(payload, ensure_ascii=False)
    payload_hash = _payload_hash(payload)
    dedup_key = _build_dedup_key(tenant_id, job_type, payload_hash)

    with get_raw_conn() as conn:
        _ensure_schema_once(conn)
        with conn.cursor() as cur:
            # Serialize same-key enqueues to avoid race duplicates without schema changes.
            cur.execute("SELECT pg_advisory_xact_lock(hashtext(%s))", (dedup_key,))
            cur.execute(
                """
                SELECT id, tenant_id, job_type, status, payload_json, result_json, error_message,
                       retry_count, max_retries, created_at, started_at, finished_at, created_by
                FROM app_jobs
                WHERE tenant_id = %s
                  AND job_type = %s
                  AND status = ANY(%s)
                                    AND payload_json::jsonb = %s::jsonb
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (tenant_id, job_type, list(ACTIVE_JOB_STATUSES), payload_json),
            )
            duplicate = cur.fetchone()
            if duplicate:
                conn.commit()
                return _mark_deduplicated(_row_to_job(duplicate), dedup_key)

            cur.execute(
                """
                INSERT INTO app_jobs (tenant_id, job_type, status, payload_json, retry_count, max_retries, created_by)
                VALUES (%s, %s, 'queued', %s::jsonb, 0, %s, %s)
                RETURNING id, tenant_id, job_type, status, payload_json, result_json, error_message,
                          retry_count, max_retries, created_at, started_at, finished_at, created_by
                """,
                (tenant_id, job_type, payload_json, max_retries, created_by),
            )
            row = cur.fetchone()
        conn.commit()
    return _row_to_job(row)


def _list_jobs_for_tenant_db(tenant_id: int, status: str | None, limit: int) -> list[dict[str, Any]]:
    assert _db_url() and psycopg is not None
    with get_raw_conn() as conn:
        _ensure_schema_once(conn)
        with conn.cursor() as cur:
            if status:
                cur.execute(
                    """
                    SELECT id, tenant_id, job_type, status, payload_json, result_json, error_message,
                           retry_count, max_retries, created_at, started_at, finished_at, created_by
                    FROM app_jobs
                    WHERE tenant_id = %s AND status = %s
                    ORDER BY created_at DESC
                    LIMIT %s
                    """,
                    (tenant_id, status, limit),
                )
            else:
                cur.execute(
                    """
                    SELECT id, tenant_id, job_type, status, payload_json, result_json, error_message,
                           retry_count, max_retries, created_at, started_at, finished_at, created_by
                    FROM app_jobs
                    WHERE tenant_id = %s
                    ORDER BY created_at DESC
                    LIMIT %s
                    """,
                    (tenant_id, limit),
                )
            rows = cur.fetchall()
    return [_row_to_job(row) for row in rows]


def _get_job_for_tenant_db(tenant_id: int, job_id: int) -> dict[str, Any] | None:
    assert _db_url() and psycopg is not None
    with get_raw_conn() as conn:
        _ensure_schema_once(conn)
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, tenant_id, job_type, status, payload_json, result_json, error_message,
                       retry_count, max_retries, created_at, started_at, finished_at, created_by
                FROM app_jobs
                WHERE tenant_id = %s AND id = %s
                """,
                (tenant_id, job_id),
            )
            row = cur.fetchone()
    return _row_to_job(row) if row else None


def _get_job_by_id_db(job_id: int) -> dict[str, Any] | None:
    assert _db_url() and psycopg is not None
    with get_raw_conn() as conn:
        _ensure_schema_once(conn)
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, tenant_id, job_type, status, payload_json, result_json, error_message,
                       retry_count, max_retries, created_at, started_at, finished_at, created_by
                FROM app_jobs
                WHERE id = %s
                """,
                (job_id,),
            )
            row = cur.fetchone()
    return _row_to_job(row) if row else None


def _update_status_db(job_id: int, from_statuses: list[str], to_status: str) -> dict[str, Any] | None:
    assert _db_url() and psycopg is not None
    with get_raw_conn() as conn:
        _ensure_schema_once(conn)
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE app_jobs
                SET status = %s,
                    started_at = CASE WHEN %s = 'running' THEN NOW() ELSE started_at END,
                    finished_at = CASE WHEN %s IN ('succeeded', 'failed', 'cancelled') THEN NOW() ELSE finished_at END
                WHERE id = %s
                  AND status = ANY(%s)
                RETURNING id, tenant_id, job_type, status, payload_json, result_json, error_message,
                          retry_count, max_retries, created_at, started_at, finished_at, created_by
                """,
                (to_status, to_status, to_status, job_id, from_statuses),
            )
            row = cur.fetchone()
        conn.commit()
    return _row_to_job(row) if row else None


def _mark_succeeded_db(job_id: int, result_json: dict[str, Any]) -> dict[str, Any] | None:
    assert _db_url() and psycopg is not None
    with get_raw_conn() as conn:
        _ensure_schema_once(conn)
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE app_jobs
                SET status = 'succeeded', result_json = %s::jsonb, error_message = NULL, finished_at = NOW()
                WHERE id = %s
                RETURNING id, tenant_id, job_type, status, payload_json, result_json, error_message,
                          retry_count, max_retries, created_at, started_at, finished_at, created_by
                """,
                (json.dumps(result_json, ensure_ascii=False), job_id),
            )
            row = cur.fetchone()
        conn.commit()
    return _row_to_job(row) if row else None


def _mark_failed_db(job_id: int, error_message: str) -> dict[str, Any] | None:
    assert _db_url() and psycopg is not None
    with get_raw_conn() as conn:
        _ensure_schema_once(conn)
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE app_jobs
                SET status = 'failed', error_message = %s, finished_at = NOW()
                WHERE id = %s
                RETURNING id, tenant_id, job_type, status, payload_json, result_json, error_message,
                          retry_count, max_retries, created_at, started_at, finished_at, created_by
                """,
                (error_message, job_id),
            )
            row = cur.fetchone()
        conn.commit()
    return _row_to_job(row) if row else None


def _retry_job_db(job_id: int) -> dict[str, Any] | None:
    assert _db_url() and psycopg is not None
    with get_raw_conn() as conn:
        _ensure_schema_once(conn)
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE app_jobs
                SET status = 'queued',
                    retry_count = retry_count + 1,
                    error_message = NULL,
                    result_json = NULL,
                    started_at = NULL,
                    finished_at = NULL
                WHERE id = %s
                  AND status = 'failed'
                  AND retry_count < max_retries
                RETURNING id, tenant_id, job_type, status, payload_json, result_json, error_message,
                          retry_count, max_retries, created_at, started_at, finished_at, created_by
                """,
                (job_id,),
            )
            row = cur.fetchone()
        conn.commit()
    return _row_to_job(row) if row else None


def _count_jobs_for_tenant_db(tenant_id: int) -> dict[str, int]:
    assert _db_url() and psycopg is not None
    with get_raw_conn() as conn:
        _ensure_schema_once(conn)
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT status, COUNT(*)
                FROM app_jobs
                WHERE tenant_id = %s
                GROUP BY status
                """,
                (tenant_id,),
            )
            rows = cur.fetchall()

    summary = {"queued": 0, "running": 0, "failed": 0}
    for status, count in rows:
        status_value = str(status)
        if status_value in summary:
            summary[status_value] = int(count)
    return summary


def _acquire_next_queued_job_db() -> dict[str, Any] | None:
    assert _db_url() and psycopg is not None
    with get_raw_conn() as conn:
        _ensure_schema_once(conn)
        with conn.cursor() as cur:
            cur.execute(
                """
                WITH next_job AS (
                    SELECT id
                    FROM app_jobs
                    WHERE status = 'queued'
                    ORDER BY created_at ASC
                    FOR UPDATE SKIP LOCKED
                    LIMIT 1
                )
                UPDATE app_jobs j
                SET status = 'running', started_at = NOW()
                FROM next_job
                WHERE j.id = next_job.id
                RETURNING j.id, j.tenant_id, j.job_type, j.status, j.payload_json, j.result_json,
                          j.error_message, j.retry_count, j.max_retries, j.created_at, j.started_at,
                          j.finished_at, j.created_by
                """
            )
            row = cur.fetchone()
        conn.commit()
    return _row_to_job(row) if row else None


def clear_jobs_state() -> None:
    if _use_database():
        try:
            assert _db_url() and psycopg is not None
            with get_raw_conn() as conn:
                _ensure_schema_once(conn)
                with conn.cursor() as cur:
                    cur.execute("DELETE FROM app_jobs")
                conn.commit()
        except Exception:
            pass

    with _jobs_lock:
        _jobs_state.rows.clear()
        _jobs_state.counter = 0


def enqueue_job(
    tenant_id: int,
    job_type: str,
    payload: dict[str, Any],
    created_by: str | None = None,
    max_retries: int = DEFAULT_MAX_RETRIES,
) -> dict[str, Any]:
    normalized_tenant_id = _normalize_tenant_id(tenant_id)
    _ensure_tenant_exists(normalized_tenant_id)

    from app.modules.billing.service import assert_billing_write_allowed, assert_quota_with_increment

    assert_billing_write_allowed(normalized_tenant_id, action="jobs.enqueue")
    assert_quota_with_increment(normalized_tenant_id, "jobs_per_day", increment=1)

    normalized_job_type = _normalize_job_type(job_type)
    safe_payload = _to_json_safe(payload)
    normalized_max_retries = max(0, min(int(max_retries), 20))
    dedup_key = _build_dedup_key(normalized_tenant_id, normalized_job_type, _payload_hash(safe_payload))

    if _use_database():
        db_started = time.perf_counter()
        try:
            return _enqueue_job_db(normalized_tenant_id, normalized_job_type, safe_payload, created_by, normalized_max_retries)
        except Exception as exc:
            _log_jobs_db_fallback("enqueue", db_started, exc)
            pass

    with _jobs_lock:
        for existing in _jobs_state.rows.values():
            if int(existing["tenant_id"]) != normalized_tenant_id:
                continue
            if str(existing["job_type"]) != normalized_job_type:
                continue
            if str(existing["status"]) not in ACTIVE_JOB_STATUSES:
                continue
            if _payload_hash(_to_json_safe(existing.get("payload_json") or {})) != _payload_hash(safe_payload):
                continue
            return _mark_deduplicated(dict(existing), dedup_key)

        _jobs_state.counter += 1
        job_id = _jobs_state.counter
        row = {
            "id": job_id,
            "tenant_id": normalized_tenant_id,
            "job_type": normalized_job_type,
            "status": "queued",
            "payload_json": safe_payload,
            "result_json": None,
            "error_message": None,
            "retry_count": 0,
            "max_retries": normalized_max_retries,
            "created_at": _now_iso(),
            "started_at": None,
            "finished_at": None,
            "created_by": created_by,
        }
        _jobs_state.rows[job_id] = row
        created = dict(row)

    try:
        from app.modules.usage.service import record_usage_event

        record_usage_event(normalized_tenant_id, "jobs_executed", 1)
    except Exception:
        pass

    return created


def list_jobs_for_tenant(tenant_id: int, status: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
    normalized_tenant_id = _normalize_tenant_id(tenant_id)
    _ensure_tenant_exists(normalized_tenant_id)
    normalized_limit = max(1, min(int(limit), 500))
    normalized_status = _normalize_status(status) if status else None

    if _use_database():
        db_started = time.perf_counter()
        try:
            return _list_jobs_for_tenant_db(normalized_tenant_id, normalized_status, normalized_limit)
        except Exception as exc:
            _log_jobs_db_fallback("list", db_started, exc)
            pass

    with _jobs_lock:
        rows = [dict(item) for item in _jobs_state.rows.values() if int(item["tenant_id"]) == normalized_tenant_id]

    if normalized_status:
        rows = [item for item in rows if str(item["status"]) == normalized_status]
    rows.sort(key=lambda item: str(item.get("created_at", "")), reverse=True)
    return rows[:normalized_limit]


def get_job_for_tenant(tenant_id: int, job_id: int) -> dict[str, Any] | None:
    normalized_tenant_id = _normalize_tenant_id(tenant_id)
    normalized_job_id = int(job_id)

    if _use_database():
        db_started = time.perf_counter()
        try:
            return _get_job_for_tenant_db(normalized_tenant_id, normalized_job_id)
        except Exception as exc:
            _log_jobs_db_fallback("get", db_started, exc)
            pass

    with _jobs_lock:
        row = _jobs_state.rows.get(normalized_job_id)
        if row is None or int(row["tenant_id"]) != normalized_tenant_id:
            return None
        return dict(row)


def get_job_by_id(job_id: int) -> dict[str, Any] | None:
    normalized_job_id = int(job_id)

    if _use_database():
        try:
            return _get_job_by_id_db(normalized_job_id)
        except Exception:
            pass

    with _jobs_lock:
        row = _jobs_state.rows.get(normalized_job_id)
        return dict(row) if row is not None else None


def mark_job_running(job_id: int) -> dict[str, Any] | None:
    normalized_job_id = int(job_id)

    if _use_database():
        try:
            return _update_status_db(normalized_job_id, ["queued"], "running")
        except Exception:
            pass

    with _jobs_lock:
        row = _jobs_state.rows.get(normalized_job_id)
        if row is None or row["status"] != "queued":
            return None
        row["status"] = "running"
        row["started_at"] = _now_iso()
        return dict(row)


def mark_job_succeeded(job_id: int, result: dict[str, Any]) -> dict[str, Any] | None:
    normalized_job_id = int(job_id)
    safe_result = _to_json_safe(result)

    if _use_database():
        try:
            return _mark_succeeded_db(normalized_job_id, safe_result)
        except Exception:
            pass

    with _jobs_lock:
        row = _jobs_state.rows.get(normalized_job_id)
        if row is None:
            return None
        row["status"] = "succeeded"
        row["result_json"] = safe_result
        row["error_message"] = None
        if not row.get("started_at"):
            row["started_at"] = _now_iso()
        row["finished_at"] = _now_iso()
        return dict(row)


def mark_job_failed(job_id: int, error: str) -> dict[str, Any] | None:
    normalized_job_id = int(job_id)

    if _use_database():
        try:
            return _mark_failed_db(normalized_job_id, str(error)[:2000])
        except Exception:
            pass

    with _jobs_lock:
        row = _jobs_state.rows.get(normalized_job_id)
        if row is None:
            return None
        row["status"] = "failed"
        row["error_message"] = str(error)[:2000]
        if not row.get("started_at"):
            row["started_at"] = _now_iso()
        row["finished_at"] = _now_iso()
        return dict(row)


def retry_job(job_id: int) -> dict[str, Any] | None:
    normalized_job_id = int(job_id)

    if _use_database():
        try:
            return _retry_job_db(normalized_job_id)
        except Exception:
            pass

    with _jobs_lock:
        row = _jobs_state.rows.get(normalized_job_id)
        if row is None:
            return None
        if row["status"] != "failed":
            return None
        if int(row["retry_count"]) >= int(row["max_retries"]):
            return None
        row["status"] = "queued"
        row["retry_count"] = int(row["retry_count"]) + 1
        row["error_message"] = None
        row["result_json"] = None
        row["started_at"] = None
        row["finished_at"] = None
        return dict(row)


def cancel_job(job_id: int) -> dict[str, Any] | None:
    normalized_job_id = int(job_id)

    if _use_database():
        try:
            return _update_status_db(normalized_job_id, ["queued", "running"], "cancelled")
        except Exception:
            pass

    with _jobs_lock:
        row = _jobs_state.rows.get(normalized_job_id)
        if row is None:
            return None
        if row["status"] not in {"queued", "running"}:
            return None
        row["status"] = "cancelled"
        if not row.get("started_at"):
            row["started_at"] = _now_iso()
        row["finished_at"] = _now_iso()
        return dict(row)


def count_jobs_for_tenant(tenant_id: int) -> dict[str, int]:
    normalized_tenant_id = _normalize_tenant_id(tenant_id)

    if _use_database():
        db_started = time.perf_counter()
        try:
            return _count_jobs_for_tenant_db(normalized_tenant_id)
        except Exception as exc:
            _log_jobs_db_fallback("count", db_started, exc)
            pass

    summary = {"queued": 0, "running": 0, "failed": 0}
    with _jobs_lock:
        for row in _jobs_state.rows.values():
            if int(row["tenant_id"]) != normalized_tenant_id:
                continue
            status = str(row["status"])
            if status in summary:
                summary[status] += 1
    return summary


def acquire_next_queued_job() -> dict[str, Any] | None:
    if _use_database():
        db_started = time.perf_counter()
        try:
            return _acquire_next_queued_job_db()
        except Exception as exc:
            _log_jobs_db_fallback("acquire", db_started, exc)
            pass

    with _jobs_lock:
        queued = [row for row in _jobs_state.rows.values() if row["status"] == "queued"]
        queued.sort(key=lambda item: str(item.get("created_at", "")))
        if not queued:
            return None
        row = queued[0]
        row["status"] = "running"
        row["started_at"] = _now_iso()
        return dict(row)
