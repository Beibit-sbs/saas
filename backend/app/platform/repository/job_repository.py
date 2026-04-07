from __future__ import annotations

from datetime import datetime, timezone
from threading import Lock
from typing import Any

from app.platform.repository.db import db_available, transaction

try:
    import psycopg
except ImportError:  # pragma: no cover
    psycopg = None


class JobRepository:
    def __init__(self) -> None:
        self._lock = Lock()
        self._rows: dict[int, dict[str, Any]] = {}
        self._counter = 0

    def _now_iso(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _row_to_api(self, row: tuple[Any, ...]) -> dict[str, Any]:
        return {
            "id": int(row[0]),
            "tenant_id": int(row[1]),
            "job_type": str(row[2]),
            "status": str(row[3]),
            "retry_count": int(row[4]),
            "max_retries": int(row[5]),
            "payload": dict(row[6] or {}),
            "result": dict(row[7]) if isinstance(row[7], dict) else row[7],
            "error": row[8],
            "created_at": row[9].isoformat() if hasattr(row[9], "isoformat") else str(row[9]),
            "updated_at": row[10].isoformat() if hasattr(row[10], "isoformat") else str(row[10]),
        }

    def clear_state(self, *, conn: object | None = None) -> None:
        if conn is None:
            with transaction() as tx:
                self.clear_state(conn=tx)
                return

        if conn is not None and db_available() and psycopg is not None:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM app_platform_jobs")
            return

        with self._lock:
            self._rows.clear()
            self._counter = 0

    def enqueue(self, tenant_id: int, job_type: str, payload: dict[str, Any], max_retries: int, *, conn: object | None = None) -> dict[str, Any]:
        normalized_tenant_id = int(tenant_id)
        normalized_job_type = job_type.strip().lower()

        if conn is None:
            with transaction() as tx:
                return self.enqueue(normalized_tenant_id, normalized_job_type, payload, max_retries, conn=tx)

        if conn is not None and db_available() and psycopg is not None:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO app_platform_jobs (tenant_id, job_type, status, retry_count, max_retries, payload_json, created_at, updated_at)
                    VALUES (%s, %s, 'queued', 0, %s, %s::jsonb, NOW(), NOW())
                    RETURNING id, tenant_id, job_type, status, retry_count, max_retries, payload_json, result_json, last_error, created_at, updated_at
                    """,
                    (normalized_tenant_id, normalized_job_type, int(max_retries), psycopg.types.json.Jsonb(dict(payload))),
                )
                row = cur.fetchone()
            return self._row_to_api(row)

        with self._lock:
            self._counter += 1
            row = {
                "id": self._counter,
                "tenant_id": normalized_tenant_id,
                "job_type": normalized_job_type,
                "status": "queued",
                "retry_count": 0,
                "max_retries": int(max_retries),
                "payload": dict(payload),
                "result": None,
                "error": None,
                "created_at": self._now_iso(),
                "updated_at": self._now_iso(),
            }
            self._rows[self._counter] = row
            return dict(row)

    def get(self, job_id: int, *, conn: object | None = None) -> dict[str, Any] | None:
        normalized_job_id = int(job_id)
        if conn is None:
            with transaction() as tx:
                return self.get(normalized_job_id, conn=tx)

        if conn is not None and db_available() and psycopg is not None:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, tenant_id, job_type, status, retry_count, max_retries, payload_json, result_json, last_error, created_at, updated_at
                    FROM app_platform_jobs
                    WHERE id = %s
                    """,
                    (normalized_job_id,),
                )
                row = cur.fetchone()
            return self._row_to_api(row) if row else None

        with self._lock:
            row = self._rows.get(normalized_job_id)
            return dict(row) if row else None

    def list_for_tenant(self, tenant_id: int, *, status: str | None = None, limit: int = 100, conn: object | None = None) -> list[dict[str, Any]]:
        normalized_tenant_id = int(tenant_id)
        normalized_limit = max(1, min(int(limit), 500))
        normalized_status = status.strip().lower() if isinstance(status, str) and status.strip() else None

        if conn is None:
            with transaction() as tx:
                return self.list_for_tenant(normalized_tenant_id, status=normalized_status, limit=normalized_limit, conn=tx)

        if conn is not None and db_available() and psycopg is not None:
            with conn.cursor() as cur:
                if normalized_status:
                    cur.execute(
                        """
                        SELECT id, tenant_id, job_type, status, retry_count, max_retries, payload_json, result_json, last_error, created_at, updated_at
                        FROM app_platform_jobs
                        WHERE tenant_id = %s AND status = %s
                        ORDER BY created_at DESC
                        LIMIT %s
                        """,
                        (normalized_tenant_id, normalized_status, normalized_limit),
                    )
                else:
                    cur.execute(
                        """
                        SELECT id, tenant_id, job_type, status, retry_count, max_retries, payload_json, result_json, last_error, created_at, updated_at
                        FROM app_platform_jobs
                        WHERE tenant_id = %s
                        ORDER BY created_at DESC
                        LIMIT %s
                        """,
                        (normalized_tenant_id, normalized_limit),
                    )
                rows = cur.fetchall()
            return [self._row_to_api(row) for row in rows]

        with self._lock:
            rows = [dict(row) for row in self._rows.values() if int(row["tenant_id"]) == normalized_tenant_id]
        if normalized_status:
            rows = [row for row in rows if str(row["status"]) == normalized_status]
        rows.sort(key=lambda item: str(item["created_at"]), reverse=True)
        return rows[:normalized_limit]

    def fetch_queued(self, limit: int = 50, *, conn: object | None = None) -> list[dict[str, Any]]:
        normalized_limit = max(1, min(int(limit), 500))
        if conn is None:
            with transaction() as tx:
                return self.fetch_queued(limit=normalized_limit, conn=tx)

        if conn is not None and db_available() and psycopg is not None:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, tenant_id, job_type, status, retry_count, max_retries, payload_json, result_json, last_error, created_at, updated_at
                    FROM app_platform_jobs
                    WHERE status = 'queued'
                    ORDER BY created_at ASC
                    LIMIT %s
                    """,
                    (normalized_limit,),
                )
                rows = cur.fetchall()
            return [self._row_to_api(row) for row in rows]

        with self._lock:
            rows = [dict(row) for row in self._rows.values() if str(row["status"]) == "queued"]
        rows.sort(key=lambda item: str(item["created_at"]))
        return rows[:normalized_limit]

    def count_by_status(self, status: str, *, conn: object | None = None) -> int:
        normalized_status = str(status or "").strip().lower()
        if conn is None:
            with transaction() as tx:
                return self.count_by_status(normalized_status, conn=tx)

        if conn is not None and db_available() and psycopg is not None:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT COUNT(*) FROM app_platform_jobs WHERE status = %s",
                    (normalized_status,),
                )
                row = cur.fetchone()
            return int(row[0]) if row else 0

        with self._lock:
            return sum(1 for row in self._rows.values() if str(row.get("status", "")).lower() == normalized_status)

    def count_dead_jobs(self, *, conn: object | None = None) -> int:
        if conn is None:
            with transaction() as tx:
                return self.count_dead_jobs(conn=tx)

        if conn is not None and db_available() and psycopg is not None:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT COUNT(*) FROM app_platform_jobs WHERE status = 'failed' AND retry_count >= max_retries"
                )
                row = cur.fetchone()
            return int(row[0]) if row else 0

        with self._lock:
            return sum(
                1
                for row in self._rows.values()
                if str(row.get("status", "")).lower() == "failed"
                and int(row.get("retry_count", 0)) >= int(row.get("max_retries", 0))
            )

    def mark_running(self, job_id: int, *, conn: object | None = None) -> dict[str, Any] | None:
        return self._transition(job_id, from_statuses=["queued"], to_status="running", conn=conn)

    def mark_succeeded(self, job_id: int, result: dict[str, Any], *, conn: object | None = None) -> dict[str, Any] | None:
        if conn is None:
            with transaction() as tx:
                return self.mark_succeeded(job_id, result, conn=tx)

        normalized_job_id = int(job_id)
        if conn is not None and db_available() and psycopg is not None:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE app_platform_jobs
                    SET status = 'succeeded', result_json = %s::jsonb, last_error = NULL, updated_at = NOW()
                    WHERE id = %s AND status = 'running'
                    RETURNING id, tenant_id, job_type, status, retry_count, max_retries, payload_json, result_json, last_error, created_at, updated_at
                    """,
                    (psycopg.types.json.Jsonb(dict(result)), normalized_job_id),
                )
                row = cur.fetchone()
            return self._row_to_api(row) if row else None

        with self._lock:
            row = self._rows.get(normalized_job_id)
            if row is None or str(row["status"]) != "running":
                return None
            row["status"] = "succeeded"
            row["result"] = dict(result)
            row["error"] = None
            row["updated_at"] = self._now_iso()
            return dict(row)

    def mark_failed(self, job_id: int, error: str, *, conn: object | None = None) -> dict[str, Any] | None:
        if conn is None:
            with transaction() as tx:
                return self.mark_failed(job_id, error, conn=tx)

        normalized_job_id = int(job_id)
        normalized_error = error.strip() or "job failed"
        if conn is not None and db_available() and psycopg is not None:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE app_platform_jobs
                    SET status = 'failed', last_error = %s, updated_at = NOW()
                    WHERE id = %s AND status = 'running'
                    RETURNING id, tenant_id, job_type, status, retry_count, max_retries, payload_json, result_json, last_error, created_at, updated_at
                    """,
                    (normalized_error, normalized_job_id),
                )
                row = cur.fetchone()
            return self._row_to_api(row) if row else None

        with self._lock:
            row = self._rows.get(normalized_job_id)
            if row is None or str(row["status"]) != "running":
                return None
            row["status"] = "failed"
            row["error"] = normalized_error
            row["updated_at"] = self._now_iso()
            return dict(row)

    def requeue_for_retry(self, job_id: int, error: str, *, conn: object | None = None) -> dict[str, Any] | None:
        if conn is None:
            with transaction() as tx:
                return self.requeue_for_retry(job_id, error, conn=tx)

        normalized_job_id = int(job_id)
        normalized_error = error.strip() or "retryable failure"
        if conn is not None and db_available() and psycopg is not None:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE app_platform_jobs
                    SET status = 'queued',
                        retry_count = retry_count + 1,
                        last_error = %s,
                        updated_at = NOW()
                    WHERE id = %s AND status = 'running'
                    RETURNING id, tenant_id, job_type, status, retry_count, max_retries, payload_json, result_json, last_error, created_at, updated_at
                    """,
                    (normalized_error, normalized_job_id),
                )
                row = cur.fetchone()
            return self._row_to_api(row) if row else None

        with self._lock:
            row = self._rows.get(normalized_job_id)
            if row is None or str(row["status"]) != "running":
                return None
            row["status"] = "queued"
            row["retry_count"] = int(row["retry_count"]) + 1
            row["error"] = normalized_error
            row["updated_at"] = self._now_iso()
            return dict(row)

    def cancel(self, job_id: int, *, conn: object | None = None) -> dict[str, Any] | None:
        return self._transition(job_id, from_statuses=["queued", "running"], to_status="cancelled", conn=conn)

    def _transition(
        self,
        job_id: int,
        *,
        from_statuses: list[str],
        to_status: str,
        conn: object | None = None,
    ) -> dict[str, Any] | None:
        normalized_job_id = int(job_id)
        normalized_to_status = to_status.strip().lower()
        normalized_from = [item.strip().lower() for item in from_statuses]

        if conn is None:
            with transaction() as tx:
                return self._transition(
                    normalized_job_id,
                    from_statuses=normalized_from,
                    to_status=normalized_to_status,
                    conn=tx,
                )

        if conn is not None and db_available() and psycopg is not None:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE app_platform_jobs
                    SET status = %s,
                        updated_at = NOW()
                    WHERE id = %s AND status = ANY(%s)
                    RETURNING id, tenant_id, job_type, status, retry_count, max_retries, payload_json, result_json, last_error, created_at, updated_at
                    """,
                    (normalized_to_status, normalized_job_id, normalized_from),
                )
                row = cur.fetchone()
            return self._row_to_api(row) if row else None

        with self._lock:
            row = self._rows.get(normalized_job_id)
            if row is None:
                return None
            if str(row["status"]).lower() not in set(normalized_from):
                return None
            row["status"] = normalized_to_status
            row["updated_at"] = self._now_iso()
            return dict(row)
