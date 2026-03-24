from __future__ import annotations

from datetime import datetime, timezone
from threading import Lock

from app.platform.repository.db import db_available, transaction

try:
    import psycopg
except ImportError:  # pragma: no cover
    psycopg = None


class FeatureFlagRepository:
    def __init__(self) -> None:
        self._lock = Lock()
        self._memory: dict[tuple[str, int | None, str, str], dict[str, object]] = {}

    def _now_iso(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def set_flag(
        self,
        *,
        scope: str,
        module: str,
        key: str,
        enabled: bool,
        tenant_id: int | None,
        conn: object | None = None,
    ) -> dict[str, object]:
        normalized_scope = scope.strip().lower()
        normalized_module = module.strip().lower()
        normalized_key = key.strip().lower()
        normalized_tenant = int(tenant_id) if tenant_id is not None else None

        if conn is None:
            with transaction() as tx:
                return self.set_flag(
                    scope=normalized_scope,
                    module=normalized_module,
                    key=normalized_key,
                    enabled=enabled,
                    tenant_id=normalized_tenant,
                    conn=tx,
                )

        if conn is not None and db_available() and psycopg is not None:
            with conn.cursor() as cur:
                if normalized_tenant is None:
                    cur.execute(
                        """
                        SELECT id FROM app_platform_feature_flags
                        WHERE scope = %s AND module = %s AND key = %s
                          AND tenant_id IS NULL
                        LIMIT 1
                        """,
                        (normalized_scope, normalized_module, normalized_key),
                    )
                else:
                    cur.execute(
                        """
                        SELECT id FROM app_platform_feature_flags
                        WHERE scope = %s AND module = %s AND key = %s
                          AND tenant_id = %s
                        LIMIT 1
                        """,
                        (normalized_scope, normalized_module, normalized_key, normalized_tenant),
                    )
                existing = cur.fetchone()
                if existing is None:
                    cur.execute(
                        """
                        INSERT INTO app_platform_feature_flags (tenant_id, scope, module, key, enabled, updated_at)
                        VALUES (%s, %s, %s, %s, %s, NOW())
                        RETURNING updated_at
                        """,
                        (normalized_tenant, normalized_scope, normalized_module, normalized_key, bool(enabled)),
                    )
                    updated_at = cur.fetchone()[0]
                else:
                    cur.execute(
                        """
                        UPDATE app_platform_feature_flags
                        SET enabled = %s,
                            updated_at = NOW()
                        WHERE id = %s
                        RETURNING updated_at
                        """,
                        (bool(enabled), int(existing[0])),
                    )
                    updated_at = cur.fetchone()[0]

            return {
                "scope": normalized_scope,
                "tenant_id": normalized_tenant,
                "module": normalized_module,
                "key": normalized_key,
                "enabled": bool(enabled),
                "updated_at": updated_at.isoformat() if hasattr(updated_at, "isoformat") else str(updated_at),
            }

        with self._lock:
            store_key = (normalized_scope, normalized_tenant, normalized_module, normalized_key)
            row = {
                "scope": normalized_scope,
                "tenant_id": normalized_tenant,
                "module": normalized_module,
                "key": normalized_key,
                "enabled": bool(enabled),
                "updated_at": self._now_iso(),
            }
            self._memory[store_key] = row
            return dict(row)

    def list_tenant_flags(self, tenant_id: int, *, conn: object | None = None) -> list[dict[str, object]]:
        normalized_tenant_id = int(tenant_id)
        if conn is None:
            with transaction() as tx:
                return self.list_tenant_flags(normalized_tenant_id, conn=tx)

        if conn is not None and db_available() and psycopg is not None:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT scope, tenant_id, module, key, enabled, updated_at
                    FROM app_platform_feature_flags
                    WHERE (scope = 'platform' AND tenant_id IS NULL)
                       OR (scope = 'tenant' AND tenant_id = %s)
                    ORDER BY scope, module, key
                    """,
                    (normalized_tenant_id,),
                )
                rows = cur.fetchall()
            return [
                {
                    "scope": str(row[0]),
                    "tenant_id": int(row[1]) if row[1] is not None else None,
                    "module": str(row[2]),
                    "key": str(row[3]),
                    "enabled": bool(row[4]),
                    "updated_at": row[5].isoformat() if hasattr(row[5], "isoformat") else str(row[5]),
                }
                for row in rows
            ]

        with self._lock:
            rows = [
                dict(item)
                for item in self._memory.values()
                if (str(item["scope"]) == "platform" and item.get("tenant_id") is None)
                or (str(item["scope"]) == "tenant" and int(item.get("tenant_id") or 0) == normalized_tenant_id)
            ]
        rows.sort(key=lambda item: (str(item["scope"]), str(item["module"]), str(item["key"])))
        return rows
