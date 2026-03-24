from __future__ import annotations

from datetime import datetime, timezone
from threading import Lock
from typing import Any

from app.platform.repository.db import db_available, transaction

try:
    import psycopg
except ImportError:  # pragma: no cover
    psycopg = None


class AiCopilotRepository:
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
            "actor_id": str(row[2]),
            "question": str(row[3]),
            "query_type": str(row[4]),
            "retrieved_sources_json": list(row[5] or []),
            "answer_json": dict(row[6] or {}),
            "created_at": row[7].isoformat() if hasattr(row[7], "isoformat") else str(row[7]),
        }

    def clear_state(self, *, conn: object | None = None) -> None:
        if conn is None:
            with transaction() as tx:
                self.clear_state(conn=tx)
                return

        if conn is not None and db_available() and psycopg is not None:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM app_platform_ai_copilot_query_logs")
            return

        with self._lock:
            self._rows.clear()
            self._counter = 0

    def log_query(
        self,
        *,
        tenant_id: int,
        actor_id: str,
        question: str,
        query_type: str,
        retrieved_sources_json: list[dict[str, Any]],
        answer_json: dict[str, Any],
        conn: object | None = None,
    ) -> dict[str, Any]:
        normalized_tenant_id = int(tenant_id)
        normalized_actor_id = str(actor_id or "unknown").strip() or "unknown"
        normalized_question = str(question or "").strip()
        normalized_query_type = str(query_type or "unsupported").strip()

        if conn is None:
            with transaction() as tx:
                return self.log_query(
                    tenant_id=normalized_tenant_id,
                    actor_id=normalized_actor_id,
                    question=normalized_question,
                    query_type=normalized_query_type,
                    retrieved_sources_json=retrieved_sources_json,
                    answer_json=answer_json,
                    conn=tx,
                )

        if conn is not None and db_available() and psycopg is not None:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO app_platform_ai_copilot_query_logs
                        (tenant_id, actor_id, question, query_type, retrieved_sources_json, answer_json, created_at)
                    VALUES (%s, %s, %s, %s, %s::jsonb, %s::jsonb, NOW())
                    RETURNING id, tenant_id, actor_id, question, query_type, retrieved_sources_json, answer_json, created_at
                    """,
                    (
                        normalized_tenant_id,
                        normalized_actor_id,
                        normalized_question,
                        normalized_query_type,
                        psycopg.types.json.Jsonb(list(retrieved_sources_json)),
                        psycopg.types.json.Jsonb(dict(answer_json)),
                    ),
                )
                row = cur.fetchone()
            return self._row_to_api(row)

        with self._lock:
            self._counter += 1
            row = {
                "id": self._counter,
                "tenant_id": normalized_tenant_id,
                "actor_id": normalized_actor_id,
                "question": normalized_question,
                "query_type": normalized_query_type,
                "retrieved_sources_json": list(retrieved_sources_json),
                "answer_json": dict(answer_json),
                "created_at": self._now_iso(),
            }
            self._rows[self._counter] = row
            return dict(row)

    def list_queries_for_tenant(
        self,
        tenant_id: int,
        *,
        limit: int = 100,
        conn: object | None = None,
    ) -> list[dict[str, Any]]:
        normalized_tenant_id = int(tenant_id)
        normalized_limit = max(1, min(int(limit), 500))

        if conn is None:
            with transaction() as tx:
                return self.list_queries_for_tenant(normalized_tenant_id, limit=normalized_limit, conn=tx)

        if conn is not None and db_available() and psycopg is not None:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, tenant_id, actor_id, question, query_type, retrieved_sources_json, answer_json, created_at
                    FROM app_platform_ai_copilot_query_logs
                    WHERE tenant_id = %s
                    ORDER BY created_at DESC, id DESC
                    LIMIT %s
                    """,
                    (normalized_tenant_id, normalized_limit),
                )
                rows = cur.fetchall()
            return [self._row_to_api(row) for row in rows]

        with self._lock:
            rows = [dict(item) for item in self._rows.values() if int(item["tenant_id"]) == normalized_tenant_id]
        rows.sort(key=lambda item: (str(item["created_at"]), int(item["id"])), reverse=True)
        return rows[:normalized_limit]

    def get_query(self, query_id: int, *, conn: object | None = None) -> dict[str, Any] | None:
        normalized_query_id = int(query_id)

        if conn is None:
            with transaction() as tx:
                return self.get_query(normalized_query_id, conn=tx)

        if conn is not None and db_available() and psycopg is not None:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, tenant_id, actor_id, question, query_type, retrieved_sources_json, answer_json, created_at
                    FROM app_platform_ai_copilot_query_logs
                    WHERE id = %s
                    LIMIT 1
                    """,
                    (normalized_query_id,),
                )
                row = cur.fetchone()
            return self._row_to_api(row) if row else None

        with self._lock:
            row = self._rows.get(normalized_query_id)
            return dict(row) if row else None
