from __future__ import annotations

from datetime import datetime, timezone
from threading import Lock
from typing import Any

from app.platform.repository.db import db_available, transaction

try:
    import psycopg
except ImportError:  # pragma: no cover
    psycopg = None


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class DeveloperRepository:
    def __init__(self) -> None:
        self._lock = Lock()
        self._app_seq = 0
        self._installation_seq = 0
        self._log_seq = 0
        self._subscription_seq = 0
        self._apps: dict[int, dict[str, Any]] = {}
        self._scopes: dict[int, list[str]] = {}
        self._installations: dict[int, dict[str, Any]] = {}
        self._api_logs: dict[int, dict[str, Any]] = {}
        self._event_subscriptions: dict[int, dict[str, Any]] = {}

    def clear_state(self) -> None:
        with self._lock:
            self._app_seq = 0
            self._installation_seq = 0
            self._log_seq = 0
            self._subscription_seq = 0
            self._apps.clear()
            self._scopes.clear()
            self._installations.clear()
            self._api_logs.clear()
            self._event_subscriptions.clear()

    def _hydrate_app(self, row: dict[str, Any]) -> dict[str, Any]:
        payload = dict(row)
        payload["scopes"] = list(self._scopes.get(int(row["id"]), []))
        return payload

    def create_app(
        self,
        *,
        tenant_id: int,
        name: str,
        app_key: str,
        app_secret_hash: str,
        description: str,
        owner_email: str,
        status: str,
        webhook_url: str | None,
        scopes: list[str],
        conn: object | None = None,
    ) -> dict[str, Any]:
        if conn is None:
            with transaction() as tx:
                return self.create_app(
                    tenant_id=tenant_id,
                    name=name,
                    app_key=app_key,
                    app_secret_hash=app_secret_hash,
                    description=description,
                    owner_email=owner_email,
                    status=status,
                    webhook_url=webhook_url,
                    scopes=scopes,
                    conn=tx,
                )

        if conn is not None and db_available() and psycopg is not None:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO app_platform_developer_apps
                        (tenant_id, name, app_key, app_secret_hash, description, owner_email, status, webhook_url, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                    RETURNING id, tenant_id, name, app_key, app_secret_hash, description, owner_email, status, webhook_url, created_at, updated_at
                    """,
                    (int(tenant_id), name, app_key, app_secret_hash, description, owner_email, status, webhook_url),
                )
                row = cur.fetchone()
                app_id = int(row[0])
                for scope in scopes:
                    cur.execute(
                        """
                        INSERT INTO app_platform_developer_app_scopes (app_id, scope, created_at)
                        VALUES (%s, %s, NOW())
                        ON CONFLICT (app_id, scope) DO NOTHING
                        """,
                        (app_id, scope),
                    )
            return self.get_app(app_id, conn=conn)  # type: ignore[return-value]

        with self._lock:
            self._app_seq += 1
            row = {
                "id": self._app_seq,
                "tenant_id": int(tenant_id),
                "name": name,
                "app_key": app_key,
                "app_secret_hash": app_secret_hash,
                "description": description,
                "owner_email": owner_email,
                "status": status,
                "webhook_url": webhook_url,
                "created_at": _utc_now_iso(),
                "updated_at": _utc_now_iso(),
            }
            self._apps[self._app_seq] = row
            self._scopes[self._app_seq] = sorted({scope for scope in scopes if scope})
            return self._hydrate_app(row)

    def get_app(self, app_id: int, *, conn: object | None = None) -> dict[str, Any] | None:
        normalized_app_id = int(app_id)
        if conn is None:
            with transaction() as tx:
                return self.get_app(normalized_app_id, conn=tx)

        if conn is not None and db_available() and psycopg is not None:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, tenant_id, name, app_key, app_secret_hash, description, owner_email, status, webhook_url, created_at, updated_at
                    FROM app_platform_developer_apps
                    WHERE id = %s
                    LIMIT 1
                    """,
                    (normalized_app_id,),
                )
                row = cur.fetchone()
                if row is None:
                    return None
                cur.execute(
                    "SELECT scope FROM app_platform_developer_app_scopes WHERE app_id = %s ORDER BY scope ASC",
                    (normalized_app_id,),
                )
                scopes = [str(item[0]) for item in cur.fetchall()]
            return {
                "id": int(row[0]),
                "tenant_id": int(row[1]) if row[1] is not None else None,
                "name": str(row[2]),
                "app_key": str(row[3]),
                "app_secret_hash": str(row[4]),
                "description": str(row[5] or ""),
                "owner_email": str(row[6]),
                "status": str(row[7]),
                "webhook_url": row[8],
                "created_at": row[9].isoformat() if hasattr(row[9], "isoformat") else str(row[9]),
                "updated_at": row[10].isoformat() if hasattr(row[10], "isoformat") else str(row[10]),
                "scopes": scopes,
            }

        with self._lock:
            row = self._apps.get(normalized_app_id)
            return self._hydrate_app(row) if row else None

    def get_app_by_key(self, app_key: str, *, conn: object | None = None) -> dict[str, Any] | None:
        normalized_app_key = str(app_key or "").strip()
        if conn is None:
            with transaction() as tx:
                return self.get_app_by_key(normalized_app_key, conn=tx)

        if conn is not None and db_available() and psycopg is not None:
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM app_platform_developer_apps WHERE app_key = %s LIMIT 1", (normalized_app_key,))
                row = cur.fetchone()
            return self.get_app(int(row[0]), conn=conn) if row else None

        with self._lock:
            for row in self._apps.values():
                if str(row.get("app_key", "")) == normalized_app_key:
                    return self._hydrate_app(row)
        return None

    def list_apps(self, *, tenant_id: int | None = None, conn: object | None = None) -> list[dict[str, Any]]:
        if conn is None:
            with transaction() as tx:
                return self.list_apps(tenant_id=tenant_id, conn=tx)

        if conn is not None and db_available() and psycopg is not None:
            with conn.cursor() as cur:
                if tenant_id is not None:
                    cur.execute("SELECT id FROM app_platform_developer_apps WHERE tenant_id = %s ORDER BY created_at DESC, id DESC", (int(tenant_id),))
                else:
                    cur.execute("SELECT id FROM app_platform_developer_apps ORDER BY created_at DESC, id DESC")
                rows = cur.fetchall()
            return [self.get_app(int(row[0]), conn=conn) for row in rows if row]

        with self._lock:
            rows = [self._hydrate_app(row) for row in self._apps.values()]
            if tenant_id is not None:
                rows = [row for row in rows if int(row.get("tenant_id", -1)) == int(tenant_id)]
        rows.sort(key=lambda item: (str(item["created_at"]), int(item["id"])), reverse=True)
        return rows

    def update_app_secret_hash(self, app_id: int, app_secret_hash: str, *, conn: object | None = None) -> dict[str, Any] | None:
        normalized_app_id = int(app_id)
        if conn is None:
            with transaction() as tx:
                return self.update_app_secret_hash(normalized_app_id, app_secret_hash, conn=tx)

        if conn is not None and db_available() and psycopg is not None:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE app_platform_developer_apps SET app_secret_hash = %s, updated_at = NOW() WHERE id = %s",
                    (app_secret_hash, normalized_app_id),
                )
            return self.get_app(normalized_app_id, conn=conn)

        with self._lock:
            row = self._apps.get(normalized_app_id)
            if row is None:
                return None
            row["app_secret_hash"] = app_secret_hash
            row["updated_at"] = _utc_now_iso()
            return self._hydrate_app(row)

    def create_installation(
        self,
        *,
        app_id: int,
        tenant_id: int,
        status: str,
        installed_by: str,
        conn: object | None = None,
    ) -> dict[str, Any]:
        if conn is None:
            with transaction() as tx:
                return self.create_installation(
                    app_id=app_id,
                    tenant_id=tenant_id,
                    status=status,
                    installed_by=installed_by,
                    conn=tx,
                )

        if conn is not None and db_available() and psycopg is not None:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO app_platform_developer_app_installations (app_id, tenant_id, status, installed_by, created_at)
                    VALUES (%s, %s, %s, %s, NOW())
                    ON CONFLICT (app_id, tenant_id) DO UPDATE SET status = EXCLUDED.status, installed_by = EXCLUDED.installed_by
                    RETURNING id, app_id, tenant_id, status, installed_by, created_at
                    """,
                    (int(app_id), int(tenant_id), status, installed_by),
                )
                row = cur.fetchone()
            return {
                "id": int(row[0]),
                "app_id": int(row[1]),
                "tenant_id": int(row[2]),
                "status": str(row[3]),
                "installed_by": str(row[4]),
                "created_at": row[5].isoformat() if hasattr(row[5], "isoformat") else str(row[5]),
            }

        with self._lock:
            existing = None
            for row in self._installations.values():
                if int(row["app_id"]) == int(app_id) and int(row["tenant_id"]) == int(tenant_id):
                    existing = row
                    break
            if existing is not None:
                existing["status"] = status
                existing["installed_by"] = installed_by
                return dict(existing)
            self._installation_seq += 1
            row = {
                "id": self._installation_seq,
                "app_id": int(app_id),
                "tenant_id": int(tenant_id),
                "status": status,
                "installed_by": installed_by,
                "created_at": _utc_now_iso(),
            }
            self._installations[self._installation_seq] = row
            return dict(row)

    def get_installation(self, *, app_id: int, tenant_id: int, conn: object | None = None) -> dict[str, Any] | None:
        if conn is None:
            with transaction() as tx:
                return self.get_installation(app_id=app_id, tenant_id=tenant_id, conn=tx)

        if conn is not None and db_available() and psycopg is not None:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, app_id, tenant_id, status, installed_by, created_at
                    FROM app_platform_developer_app_installations
                    WHERE app_id = %s AND tenant_id = %s
                    LIMIT 1
                    """,
                    (int(app_id), int(tenant_id)),
                )
                row = cur.fetchone()
            if row is None:
                return None
            return {
                "id": int(row[0]),
                "app_id": int(row[1]),
                "tenant_id": int(row[2]),
                "status": str(row[3]),
                "installed_by": str(row[4]),
                "created_at": row[5].isoformat() if hasattr(row[5], "isoformat") else str(row[5]),
            }

        with self._lock:
            for row in self._installations.values():
                if int(row["app_id"]) == int(app_id) and int(row["tenant_id"]) == int(tenant_id):
                    return dict(row)
        return None

    def list_installations(self, app_id: int, *, conn: object | None = None) -> list[dict[str, Any]]:
        normalized_app_id = int(app_id)
        if conn is None:
            with transaction() as tx:
                return self.list_installations(normalized_app_id, conn=tx)

        if conn is not None and db_available() and psycopg is not None:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, app_id, tenant_id, status, installed_by, created_at
                    FROM app_platform_developer_app_installations
                    WHERE app_id = %s
                    ORDER BY created_at DESC, id DESC
                    """,
                    (normalized_app_id,),
                )
                rows = cur.fetchall()
            return [
                {
                    "id": int(row[0]),
                    "app_id": int(row[1]),
                    "tenant_id": int(row[2]),
                    "status": str(row[3]),
                    "installed_by": str(row[4]),
                    "created_at": row[5].isoformat() if hasattr(row[5], "isoformat") else str(row[5]),
                }
                for row in rows
            ]

        with self._lock:
            rows = [dict(row) for row in self._installations.values() if int(row["app_id"]) == normalized_app_id]
        rows.sort(key=lambda item: (str(item["created_at"]), int(item["id"])), reverse=True)
        return rows

    def log_api_call(
        self,
        *,
        app_id: int,
        tenant_id: int,
        endpoint: str,
        status_code: int,
        latency_ms: float,
        conn: object | None = None,
    ) -> dict[str, Any]:
        if conn is None:
            with transaction() as tx:
                return self.log_api_call(
                    app_id=app_id,
                    tenant_id=tenant_id,
                    endpoint=endpoint,
                    status_code=status_code,
                    latency_ms=latency_ms,
                    conn=tx,
                )

        if conn is not None and db_available() and psycopg is not None:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO app_platform_developer_api_logs (app_id, tenant_id, endpoint, status_code, latency_ms, created_at)
                    VALUES (%s, %s, %s, %s, %s, NOW())
                    RETURNING id, app_id, tenant_id, endpoint, status_code, latency_ms, created_at
                    """,
                    (int(app_id), int(tenant_id), endpoint, int(status_code), float(latency_ms)),
                )
                row = cur.fetchone()
            return {
                "id": int(row[0]),
                "app_id": int(row[1]),
                "tenant_id": int(row[2]),
                "endpoint": str(row[3]),
                "status_code": int(row[4]),
                "latency_ms": float(row[5]),
                "created_at": row[6].isoformat() if hasattr(row[6], "isoformat") else str(row[6]),
            }

        with self._lock:
            self._log_seq += 1
            row = {
                "id": self._log_seq,
                "app_id": int(app_id),
                "tenant_id": int(tenant_id),
                "endpoint": endpoint,
                "status_code": int(status_code),
                "latency_ms": float(latency_ms),
                "created_at": _utc_now_iso(),
            }
            self._api_logs[self._log_seq] = row
            return dict(row)

    def list_api_logs(self, app_id: int, *, limit: int = 100, conn: object | None = None) -> list[dict[str, Any]]:
        normalized_app_id = int(app_id)
        normalized_limit = max(1, min(int(limit), 500))
        if conn is None:
            with transaction() as tx:
                return self.list_api_logs(normalized_app_id, limit=normalized_limit, conn=tx)

        if conn is not None and db_available() and psycopg is not None:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, app_id, tenant_id, endpoint, status_code, latency_ms, created_at
                    FROM app_platform_developer_api_logs
                    WHERE app_id = %s
                    ORDER BY created_at DESC, id DESC
                    LIMIT %s
                    """,
                    (normalized_app_id, normalized_limit),
                )
                rows = cur.fetchall()
            return [
                {
                    "id": int(row[0]),
                    "app_id": int(row[1]),
                    "tenant_id": int(row[2]),
                    "endpoint": str(row[3]),
                    "status_code": int(row[4]),
                    "latency_ms": float(row[5]),
                    "created_at": row[6].isoformat() if hasattr(row[6], "isoformat") else str(row[6]),
                }
                for row in rows
            ]

        with self._lock:
            rows = [dict(row) for row in self._api_logs.values() if int(row["app_id"]) == normalized_app_id]
        rows.sort(key=lambda item: (str(item["created_at"]), int(item["id"])), reverse=True)
        return rows[:normalized_limit]

    def count_error_logs(self, *, conn: object | None = None) -> int:
        if conn is None:
            with transaction() as tx:
                return self.count_error_logs(conn=tx)

        if conn is not None and db_available() and psycopg is not None:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT COUNT(*) FROM app_platform_developer_api_logs WHERE status_code >= 400"
                )
                row = cur.fetchone()
            return int(row[0]) if row else 0

        with self._lock:
            return sum(1 for row in self._api_logs.values() if int(row.get("status_code", 0)) >= 400)

    def create_event_subscription(self, *, app_id: int, event_type: str, conn: object | None = None) -> dict[str, Any]:
        normalized_event_type = str(event_type or "").strip().lower()
        if conn is None:
            with transaction() as tx:
                return self.create_event_subscription(app_id=app_id, event_type=normalized_event_type, conn=tx)

        if conn is not None and db_available() and psycopg is not None:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO app_platform_app_event_subscriptions (app_id, event_type, created_at)
                    VALUES (%s, %s, NOW())
                    RETURNING id, app_id, event_type, created_at
                    """,
                    (int(app_id), normalized_event_type),
                )
                row = cur.fetchone()
            return {
                "id": int(row[0]),
                "app_id": int(row[1]),
                "event_type": str(row[2]),
                "created_at": row[3].isoformat() if hasattr(row[3], "isoformat") else str(row[3]),
            }

        with self._lock:
            self._subscription_seq += 1
            row = {
                "id": self._subscription_seq,
                "app_id": int(app_id),
                "event_type": normalized_event_type,
                "created_at": _utc_now_iso(),
            }
            self._event_subscriptions[self._subscription_seq] = row
            return dict(row)

    def list_event_subscriptions(self, app_id: int, *, conn: object | None = None) -> list[dict[str, Any]]:
        normalized_app_id = int(app_id)
        if conn is None:
            with transaction() as tx:
                return self.list_event_subscriptions(normalized_app_id, conn=tx)

        if conn is not None and db_available() and psycopg is not None:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, app_id, event_type, created_at FROM app_platform_app_event_subscriptions WHERE app_id = %s ORDER BY id DESC",
                    (normalized_app_id,),
                )
                rows = cur.fetchall()
            return [
                {
                    "id": int(row[0]),
                    "app_id": int(row[1]),
                    "event_type": str(row[2]),
                    "created_at": row[3].isoformat() if hasattr(row[3], "isoformat") else str(row[3]),
                }
                for row in rows
            ]

        with self._lock:
            rows = [dict(row) for row in self._event_subscriptions.values() if int(row["app_id"]) == normalized_app_id]
        rows.sort(key=lambda item: int(item["id"]), reverse=True)
        return rows

    def list_subscribed_apps_for_event(self, event_type: str, *, conn: object | None = None) -> list[dict[str, Any]]:
        normalized_event_type = str(event_type or "").strip().lower()
        if conn is None:
            with transaction() as tx:
                return self.list_subscribed_apps_for_event(normalized_event_type, conn=tx)

        if conn is not None and db_available() and psycopg is not None:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT DISTINCT app_id FROM app_platform_app_event_subscriptions WHERE event_type = %s",
                    (normalized_event_type,),
                )
                rows = cur.fetchall()
            result: list[dict[str, Any]] = []
            for row in rows:
                app = self.get_app(int(row[0]), conn=conn)
                if app is not None:
                    result.append(app)
            return result

        with self._lock:
            app_ids = {int(row["app_id"]) for row in self._event_subscriptions.values() if str(row["event_type"]) == normalized_event_type}
            return [self._hydrate_app(self._apps[app_id]) for app_id in app_ids if app_id in self._apps]