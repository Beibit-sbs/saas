from __future__ import annotations

import json
from datetime import datetime, timezone
from threading import Lock
from typing import Any

from app.platform.repository.db import db_available, transaction

try:
    import psycopg
except ImportError:  # pragma: no cover
    psycopg = None


class AiRecommendationRepository:
    def __init__(self) -> None:
        self._lock = Lock()
        self._rows: dict[int, dict[str, Any]] = {}
        self._counter = 0

    def _now_iso(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def clear_state(self, *, conn: object | None = None) -> None:
        if conn is None:
            with transaction() as tx:
                self.clear_state(conn=tx)
                return

        if conn is not None and db_available() and psycopg is not None:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM app_platform_ai_copilot_recommendation_logs")
            return

        with self._lock:
            self._rows.clear()
            self._counter = 0

    def log_recommendation(
        self,
        *,
        tenant_id: int,
        actor_id: str,
        question: str,
        recommendation_type: str,
        context_json: dict[str, Any],
        recommendation_json: dict[str, Any],
        conn: object | None = None,
    ) -> int:
        if conn is None:
            with transaction() as tx:
                return self.log_recommendation(
                    tenant_id=tenant_id,
                    actor_id=actor_id,
                    question=question,
                    recommendation_type=recommendation_type,
                    context_json=context_json,
                    recommendation_json=recommendation_json,
                    conn=tx,
                )

        if conn is not None and db_available() and psycopg is not None:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO app_platform_ai_copilot_recommendation_logs
                        (tenant_id, actor_id, question, recommendation_type, context_json, recommendation_json)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (
                        tenant_id,
                        actor_id,
                        question,
                        recommendation_type,
                        json.dumps(context_json),
                        json.dumps(recommendation_json),
                    ),
                )
                row = cur.fetchone()
                return int(row[0])

        with self._lock:
            self._counter += 1
            row_id = self._counter
            self._rows[row_id] = {
                "id": row_id,
                "tenant_id": tenant_id,
                "actor_id": actor_id,
                "question": question,
                "recommendation_type": recommendation_type,
                "context_json": context_json,
                "recommendation_json": recommendation_json,
                "created_at": self._now_iso(),
            }
            return row_id

    def list_for_tenant(
        self,
        *,
        tenant_id: int,
        limit: int = 100,
        conn: object | None = None,
    ) -> list[dict[str, Any]]:
        if conn is None:
            with transaction() as tx:
                return self.list_for_tenant(tenant_id=tenant_id, limit=limit, conn=tx)

        if conn is not None and db_available() and psycopg is not None:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, tenant_id, actor_id, question, recommendation_type,
                           context_json, recommendation_json, created_at
                    FROM app_platform_ai_copilot_recommendation_logs
                    WHERE tenant_id = %s
                    ORDER BY created_at DESC
                    LIMIT %s
                    """,
                    (tenant_id, limit),
                )
                rows = cur.fetchall()
            return [
                {
                    "id": int(r[0]),
                    "tenant_id": int(r[1]),
                    "actor_id": str(r[2]),
                    "question": str(r[3]),
                    "recommendation_type": str(r[4]),
                    "context_json": dict(r[5] or {}),
                    "recommendation_json": dict(r[6] or {}),
                    "created_at": r[7].isoformat() if hasattr(r[7], "isoformat") else str(r[7]),
                }
                for r in rows
            ]

        with self._lock:
            rows = [
                r for r in self._rows.values()
                if r["tenant_id"] == tenant_id
            ]
        rows_sorted = sorted(rows, key=lambda r: r["created_at"], reverse=True)
        return rows_sorted[:limit]
