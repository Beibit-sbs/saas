from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
import os
from threading import Lock
from typing import Any

from app.modules.tenants.service import get_tenant

try:
    import psycopg
except ImportError:  # pragma: no cover
    psycopg = None


VALID_JOB_STATUSES = {"queued", "running", "succeeded", "failed", "cancelled"}
DEFAULT_MAX_RETRIES = 3


@dataclass
class JobsMemoryState:
    rows: dict[int, dict[str, Any]] = field(default_factory=dict)
    counter: int = 0


_jobs_lock = Lock()
_jobs_state = JobsMemoryState()


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


def _enqueue_job_db(
    tenant_id: int,
    job_type: str,
    payload: dict[str, Any],
    created_by: str | None,
    max_retries: int,
) -> dict[str, Any]:
    assert _db_url() and psycopg is not None
    with psycopg.connect(_db_url(), connect_timeout=5) as conn:
        _ensure_schema(conn)
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO app_jobs (tenant_id, job_type, status, payload_json, retry_count, max_retries, created_by)
                VALUES (%s, %s, 'queued', %s::jsonb, 0, %s, %s)
                RETURNING id, tenant_id, job_type, status, payload_json, result_json, error_message,
                          retry_count, max_retries, created_at, started_at, finished_at, created_by
                """,
                (tenant_id, job_type, json.dumps(payload, ensure_ascii=False), max_retries, created_by),
            )
            row = cur.fetchone()
        conn.commit()
    return _row_to_job(row)


def _list_jobs_for_tenant_db(tenant_id: int, status: str | None, limit: int) -> list[dict[str, Any]]:
    assert _db_url() and psycopg is not None
    clauses = ["tenant_id = %s"]
    params: list[Any] = [tenant_id]

    if status:
        clauses.append("status = %s")
        params.append(status)

    where_sql = " AND ".join(clauses)
    with psycopg.connect(_db_url(), connect_timeout=5) as conn:
        _ensure_schema(conn)
        with conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT id, tenant_id, job_type, status, payload_json, result_json, error_message,
                       retry_count, max_retries, created_at, started_at, finished_at, created_by
                FROM app_jobs
                WHERE {where_sql}
                ORDER BY created_at DESC
                LIMIT %s
                """,
                [*params, limit],
            )
            rows = cur.fetchall()
    return [_row_to_job(row) for row in rows]


def _get_job_for_tenant_db(tenant_id: int, job_id: int) -> dict[str, Any] | None:
    assert _db_url() and psycopg is not None
    with psycopg.connect(_db_url(), connect_timeout=5) as conn:
        _ensure_schema(conn)
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
    with psycopg.connect(_db_url(), connect_timeout=5) as conn:
        _ensure_schema(conn)
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
    with psycopg.connect(_db_url(), connect_timeout=5) as conn:
        _ensure_schema(conn)
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
    with psycopg.connect(_db_url(), connect_timeout=5) as conn:
        _ensure_schema(conn)
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
    with psycopg.connect(_db_url(), connect_timeout=5) as conn:
        _ensure_schema(conn)
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
    with psycopg.connect(_db_url(), connect_timeout=5) as conn:
        _ensure_schema(conn)
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
    with psycopg.connect(_db_url(), connect_timeout=5) as conn:
        _ensure_schema(conn)
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
    with psycopg.connect(_db_url(), connect_timeout=5) as conn:
        _ensure_schema(conn)
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
            with psycopg.connect(_db_url(), connect_timeout=5) as conn:
                _ensure_schema(conn)
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
    normalized_job_type = _normalize_job_type(job_type)
    safe_payload = _to_json_safe(payload)
    normalized_max_retries = max(0, min(int(max_retries), 20))

    if _use_database():
        try:
            return _enqueue_job_db(normalized_tenant_id, normalized_job_type, safe_payload, created_by, normalized_max_retries)
        except Exception:
            pass

    with _jobs_lock:
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
        return dict(row)


def list_jobs_for_tenant(tenant_id: int, status: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
    normalized_tenant_id = _normalize_tenant_id(tenant_id)
    _ensure_tenant_exists(normalized_tenant_id)
    normalized_limit = max(1, min(int(limit), 500))
    normalized_status = _normalize_status(status) if status else None

    if _use_database():
        try:
            return _list_jobs_for_tenant_db(normalized_tenant_id, normalized_status, normalized_limit)
        except Exception:
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
        try:
            return _get_job_for_tenant_db(normalized_tenant_id, normalized_job_id)
        except Exception:
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
        try:
            return _count_jobs_for_tenant_db(normalized_tenant_id)
        except Exception:
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
        try:
            return _acquire_next_queued_job_db()
        except Exception:
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
