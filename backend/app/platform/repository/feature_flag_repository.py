from __future__ import annotations

from datetime import datetime, timezone
from threading import Lock

from app.platform.repository.db import db_available, transaction

try:
    import psycopg
except ImportError:  # pragma: no cover
    psycopg = None


_PLATFORM_TENANT_ID = 1


def _normalize_tenant_for_scope(*, scope: str, tenant_id: int | None) -> int:
    normalized_scope = str(scope).strip().lower()
    if normalized_scope == "platform":
        return _PLATFORM_TENANT_ID
    if tenant_id is None:
        raise ValueError("tenant_id is required for tenant-scoped feature flags")
    normalized_tenant = int(tenant_id)
    if normalized_tenant <= 0:
        raise ValueError("tenant_id must be positive for feature flags")
    return normalized_tenant


class FeatureFlagRepository:
    def __init__(self) -> None:
        self._lock = Lock()
        self._memory: dict[tuple[str, int, str, str], dict[str, object]] = {}

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
        rollout_percentage: int = 100,
        conn: object | None = None,
    ) -> dict[str, object]:
        normalized_scope = scope.strip().lower()
        normalized_module = module.strip().lower()
        normalized_key = key.strip().lower()
        normalized_tenant = _normalize_tenant_for_scope(scope=normalized_scope, tenant_id=tenant_id)
        normalized_rollout = max(0, min(100, int(rollout_percentage)))

        if conn is None:
            with transaction() as tx:
                return self.set_flag(
                    scope=normalized_scope,
                    module=normalized_module,
                    key=normalized_key,
                    enabled=enabled,
                    tenant_id=normalized_tenant,
                    rollout_percentage=normalized_rollout,
                    conn=tx,
                )

        if conn is not None and db_available() and psycopg is not None:
            with conn.cursor() as cur:
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
                        INSERT INTO app_platform_feature_flags
                            (tenant_id, scope, module, key, enabled, rollout_percentage, updated_at)
                        VALUES (%s, %s, %s, %s, %s, %s, NOW())
                        RETURNING updated_at
                        """,
                        (normalized_tenant, normalized_scope, normalized_module, normalized_key, bool(enabled), normalized_rollout),
                    )
                    updated_at = cur.fetchone()[0]
                else:
                    cur.execute(
                        """
                        UPDATE app_platform_feature_flags
                        SET enabled = %s,
                            rollout_percentage = %s,
                            updated_at = NOW()
                        WHERE id = %s
                        RETURNING updated_at
                        """,
                        (bool(enabled), normalized_rollout, int(existing[0])),
                    )
                    updated_at = cur.fetchone()[0]

            return {
                "scope": normalized_scope,
                "tenant_id": normalized_tenant,
                "module": normalized_module,
                "key": normalized_key,
                "enabled": bool(enabled),
                "rollout_percentage": normalized_rollout,
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
                "rollout_percentage": normalized_rollout,
                "updated_at": self._now_iso(),
            }
            self._memory[store_key] = row
            return dict(row)

    def list_tenant_flags(self, tenant_id: int, *, conn: object | None = None) -> list[dict[str, object]]:
        normalized_tenant_id = int(tenant_id)
        if normalized_tenant_id <= 0:
            raise ValueError("tenant_id must be positive for feature flags")

        if conn is None:
            with transaction() as tx:
                return self.list_tenant_flags(normalized_tenant_id, conn=tx)

        if conn is not None and db_available() and psycopg is not None:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT scope, tenant_id, module, key, enabled, rollout_percentage, updated_at
                    FROM app_platform_feature_flags
                    WHERE (scope = 'platform' AND tenant_id = %s)
                       OR (scope = 'tenant' AND tenant_id = %s)
                    ORDER BY scope, module, key
                    """,
                    (_PLATFORM_TENANT_ID, normalized_tenant_id),
                )
                rows = cur.fetchall()
            return [
                {
                    "scope": str(row[0]),
                    "tenant_id": int(row[1]),
                    "module": str(row[2]),
                    "key": str(row[3]),
                    "enabled": bool(row[4]),
                    "rollout_percentage": int(row[5]),
                    "updated_at": row[6].isoformat() if hasattr(row[6], "isoformat") else str(row[6]),
                }
                for row in rows
            ]

        with self._lock:
            rows = [
                dict(item)
                for item in self._memory.values()
                if (str(item["scope"]) == "platform" and int(item.get("tenant_id") or 0) == _PLATFORM_TENANT_ID)
                or (str(item["scope"]) == "tenant" and int(item.get("tenant_id") or 0) == normalized_tenant_id)
            ]
        rows.sort(key=lambda item: (str(item["scope"]), str(item["module"]), str(item["key"])))
        return rows

    def clear_state(self, *, conn: object | None = None) -> None:
        if conn is None:
            with transaction() as tx:
                self.clear_state(conn=tx)
                return

        if conn is not None and db_available() and psycopg is not None:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM app_platform_feature_flags")
            return

        with self._lock:
            self._memory.clear()

    def get_flag(self, tenant_id: int, module: str, key: str, *, conn: object | None = None) -> dict[str, object] | None:
        normalized_tenant_id = int(tenant_id)
        normalized_module = module.strip().lower()
        normalized_key = key.strip().lower()

        if conn is None:
            with transaction() as tx:
                return self.get_flag(normalized_tenant_id, normalized_module, normalized_key, conn=tx)

        if conn is not None and db_available() and psycopg is not None:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT scope, tenant_id, module, key, enabled, rollout_percentage, updated_at
                    FROM app_platform_feature_flags
                    WHERE tenant_id = %s AND module = %s AND key = %s
                    LIMIT 1
                    """,
                    (normalized_tenant_id, normalized_module, normalized_key),
                )
                row = cur.fetchone()
            if row is None:
                return None
            return {
                "scope": str(row[0]),
                "tenant_id": int(row[1]),
                "module": str(row[2]),
                "key": str(row[3]),
                "enabled": bool(row[4]),
                "rollout_percentage": int(row[5]),
                "updated_at": row[6].isoformat() if hasattr(row[6], "isoformat") else str(row[6]),
            }

        with self._lock:
            store_key_tenant = ("tenant", normalized_tenant_id, normalized_module, normalized_key)
            store_key_platform = ("platform", _PLATFORM_TENANT_ID, normalized_module, normalized_key)
            row = self._memory.get(store_key_tenant) or self._memory.get(store_key_platform)
            return dict(row) if row else None

    def delete_flag(self, tenant_id: int, module: str, key: str, *, conn: object | None = None) -> bool:
        normalized_tenant_id = int(tenant_id)
        normalized_module = module.strip().lower()
        normalized_key = key.strip().lower()

        if conn is None:
            with transaction() as tx:
                return self.delete_flag(normalized_tenant_id, normalized_module, normalized_key, conn=tx)

        if conn is not None and db_available() and psycopg is not None:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    DELETE FROM app_platform_feature_flags
                    WHERE tenant_id = %s AND module = %s AND key = %s
                    """,
                    (normalized_tenant_id, normalized_module, normalized_key),
                )
                deleted = cur.rowcount > 0
            return deleted

        with self._lock:
            store_key = ("tenant", normalized_tenant_id, normalized_module, normalized_key)
            if store_key in self._memory:
                del self._memory[store_key]
                return True
            return False

