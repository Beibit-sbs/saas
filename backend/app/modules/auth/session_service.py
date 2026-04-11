from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import secrets
from threading import Lock
from typing import Any

from app.core.db import get_raw_conn


DEFAULT_SESSION_TTL_DAYS = 30


@dataclass
class SessionState:
    rows: dict[str, dict[str, Any]]


_state_lock = Lock()
_state = SessionState(rows={})
# Table is guaranteed by Alembic migration f3e4d5c6b7a9_add_auth_session_and_mfa_tables.
# In-memory fallback (_state) is used only when DB is unavailable (e.g. tests without DATABASE_URL).
_db_ready = True


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure_session_table(conn) -> bool:
    """Return True if DB is available; False causes caller to use in-memory fallback."""
    if conn is None:
        return False
    return _db_ready


def _dt_to_iso(value: object | None) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc).isoformat()
        return value.astimezone(timezone.utc).isoformat()
    text = str(value).strip()
    if not text:
        return None
    return text


def _row_to_session(row: tuple[object, ...]) -> dict[str, Any]:
    return {
        "session_id": str(row[0]),
        "user_id": str(row[1]),
        "tenant_id": int(row[2]),
        "auth_source": str(row[3]),
        "client_ip": str(row[4]),
        "user_agent": str(row[5]),
        "device_id": str(row[6]),
        "device_name": str(row[7]),
        "created_at": _dt_to_iso(row[8]) or _now_iso(),
        "last_seen_at": _dt_to_iso(row[9]) or _now_iso(),
        "expires_at": _dt_to_iso(row[10]),
        "revoked_at": _dt_to_iso(row[11]),
        "active": not bool(row[12]),
        "is_revoked": bool(row[12]),
    }


def _default_expires_at() -> datetime:
    return datetime.now(timezone.utc) + timedelta(days=DEFAULT_SESSION_TTL_DAYS)


def create_session(
    *,
    user_id: str,
    tenant_id: int,
    auth_source: str,
    client_ip: str,
    user_agent: str,
    device_id: str | None = None,
    device_name: str | None = None,
) -> dict[str, Any]:
    session_id = secrets.token_urlsafe(24)
    normalized_device_id = str(device_id).strip() if device_id else secrets.token_urlsafe(16)
    now_iso = _now_iso()
    expires_at = _default_expires_at()

    with get_raw_conn() as conn:
        if _ensure_session_table(conn):
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO app_auth_sessions (
                        session_id,
                        user_id,
                        tenant_id,
                        auth_source,
                        client_ip,
                        user_agent,
                        device_id,
                        device_name,
                        created_at,
                        last_seen_at,
                        expires_at,
                        is_revoked,
                        revoked_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW(), %s, FALSE, NULL)
                    RETURNING
                        session_id,
                        user_id,
                        tenant_id,
                        auth_source,
                        client_ip,
                        user_agent,
                        device_id,
                        device_name,
                        created_at,
                        last_seen_at,
                        expires_at,
                        revoked_at,
                        is_revoked
                    """,
                    (
                        session_id,
                        str(user_id),
                        int(tenant_id),
                        str(auth_source),
                        str(client_ip),
                        str(user_agent),
                        normalized_device_id,
                        str(device_name or "").strip() or "Unknown Device",
                        expires_at,
                    ),
                )
                row = cur.fetchone()
            conn.commit()
            return _row_to_session(row)

    # Fallback for test/runtime without DATABASE_URL.
    row = {
        "session_id": session_id,
        "user_id": str(user_id),
        "tenant_id": int(tenant_id),
        "auth_source": str(auth_source),
        "client_ip": str(client_ip),
        "user_agent": str(user_agent),
        "device_id": normalized_device_id,
        "device_name": str(device_name or "").strip() or "Unknown Device",
        "created_at": now_iso,
        "last_seen_at": now_iso,
        "expires_at": expires_at.isoformat(),
        "revoked_at": None,
        "active": True,
        "is_revoked": False,
    }
    with _state_lock:
        _state.rows[session_id] = row
    return dict(row)


def touch_session(session_id: str) -> None:
    normalized = str(session_id).strip()
    if not normalized:
        return

    with get_raw_conn() as conn:
        if _ensure_session_table(conn):
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE app_auth_sessions
                    SET last_seen_at = NOW()
                    WHERE session_id = %s
                      AND is_revoked = FALSE
                      AND (expires_at IS NULL OR expires_at > NOW())
                    """,
                    (normalized,),
                )
            conn.commit()
            return

    with _state_lock:
        row = _state.rows.get(normalized)
        if row is None or not bool(row.get("active", False)):
            return
        row["last_seen_at"] = _now_iso()


def is_session_active(session_id: str) -> bool:
    normalized = str(session_id).strip()
    if not normalized:
        return False

    with get_raw_conn() as conn:
        if _ensure_session_table(conn):
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT is_revoked, expires_at
                    FROM app_auth_sessions
                    WHERE session_id = %s
                    LIMIT 1
                    """,
                    (normalized,),
                )
                row = cur.fetchone()
            if row is None:
                return False
            is_revoked = bool(row[0])
            expires_at = row[1]
            if is_revoked:
                return False
            if isinstance(expires_at, datetime):
                now = datetime.now(timezone.utc)
                return expires_at.astimezone(timezone.utc) > now
            return True

    with _state_lock:
        row = _state.rows.get(normalized)
        if row is None:
            return False
        expires_at = row.get("expires_at")
        if expires_at:
            try:
                expiry = datetime.fromisoformat(str(expires_at).replace("Z", "+00:00"))
                if expiry.tzinfo is None:
                    expiry = expiry.replace(tzinfo=timezone.utc)
                if expiry.astimezone(timezone.utc) <= datetime.now(timezone.utc):
                    return False
            except ValueError:
                pass
        return bool(row.get("active", False))


def list_sessions_for_user(*, user_id: str, tenant_id: int) -> list[dict[str, Any]]:
    normalized_user = str(user_id).strip()
    normalized_tenant = int(tenant_id)

    with get_raw_conn() as conn:
        if _ensure_session_table(conn):
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT
                        session_id,
                        user_id,
                        tenant_id,
                        auth_source,
                        client_ip,
                        user_agent,
                        device_id,
                        device_name,
                        created_at,
                        last_seen_at,
                        expires_at,
                        revoked_at,
                        is_revoked
                    FROM app_auth_sessions
                    WHERE user_id = %s
                      AND tenant_id = %s
                    ORDER BY created_at DESC
                    """,
                    (normalized_user, normalized_tenant),
                )
                rows = cur.fetchall()
            return [_row_to_session(item) for item in rows]

    with _state_lock:
        rows = [
            dict(item)
            for item in _state.rows.values()
            if str(item.get("user_id", "")).strip() == normalized_user
            and int(item.get("tenant_id", 0)) == normalized_tenant
        ]
    rows.sort(key=lambda item: str(item.get("created_at", "")), reverse=True)
    return rows


def revoke_session(*, session_id: str) -> bool:
    normalized = str(session_id).strip()
    if not normalized:
        return False

    with get_raw_conn() as conn:
        if _ensure_session_table(conn):
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE app_auth_sessions
                    SET is_revoked = TRUE,
                        revoked_at = NOW(),
                        last_seen_at = NOW()
                    WHERE session_id = %s
                      AND is_revoked = FALSE
                    """,
                    (normalized,),
                )
                updated = int(cur.rowcount)
            conn.commit()
            return updated > 0

    with _state_lock:
        row = _state.rows.get(normalized)
        if row is None:
            return False
        if not bool(row.get("active", False)):
            return False
        row["active"] = False
        row["is_revoked"] = True
        row["revoked_at"] = _now_iso()
        row["last_seen_at"] = _now_iso()
        return True


def revoke_all_sessions_for_user(*, user_id: str, tenant_id: int) -> int:
    normalized_user = str(user_id).strip()
    normalized_tenant = int(tenant_id)

    with get_raw_conn() as conn:
        if _ensure_session_table(conn):
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE app_auth_sessions
                    SET is_revoked = TRUE,
                        revoked_at = NOW(),
                        last_seen_at = NOW()
                    WHERE user_id = %s
                      AND tenant_id = %s
                      AND is_revoked = FALSE
                    """,
                    (normalized_user, normalized_tenant),
                )
                updated = int(cur.rowcount)
            conn.commit()
            return updated

    revoked = 0
    with _state_lock:
        for row in _state.rows.values():
            if str(row.get("user_id", "")).strip() != normalized_user:
                continue
            if int(row.get("tenant_id", 0)) != normalized_tenant:
                continue
            if not bool(row.get("active", False)):
                continue
            row["active"] = False
            row["is_revoked"] = True
            row["revoked_at"] = _now_iso()
            row["last_seen_at"] = _now_iso()
            revoked += 1
    return revoked


def list_active_devices(*, user_id: str, tenant_id: int) -> list[dict[str, Any]]:
    """List all active devices (unique device_id) for a user in a tenant."""
    normalized_user = str(user_id).strip()
    normalized_tenant = int(tenant_id)

    with get_raw_conn() as conn:
        if _ensure_session_table(conn):
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT
                        device_id,
                        MAX(device_name) AS device_name,
                        MAX(client_ip) AS client_ip,
                        MAX(user_agent) AS user_agent,
                        MAX(auth_source) AS auth_source,
                        MIN(created_at) AS created_at,
                        MAX(last_seen_at) AS last_seen_at,
                        COUNT(*) AS session_count
                    FROM app_auth_sessions
                    WHERE user_id = %s
                      AND tenant_id = %s
                      AND is_revoked = FALSE
                      AND (expires_at IS NULL OR expires_at > NOW())
                    GROUP BY device_id
                    ORDER BY MAX(last_seen_at) DESC
                    """,
                    (normalized_user, normalized_tenant),
                )
                rows = cur.fetchall()
            return [
                {
                    "device_id": str(item[0]),
                    "device_name": str(item[1] or "Unknown"),
                    "client_ip": str(item[2] or ""),
                    "user_agent": str(item[3] or "")[:100],
                    "auth_source": str(item[4] or ""),
                    "created_at": _dt_to_iso(item[5]) or "",
                    "last_seen_at": _dt_to_iso(item[6]) or "",
                    "session_count": int(item[7] or 0),
                }
                for item in rows
            ]

    devices: dict[str, dict[str, Any]] = {}
    with _state_lock:
        for row in _state.rows.values():
            if str(row.get("user_id", "")).strip() != normalized_user:
                continue
            if int(row.get("tenant_id", 0)) != normalized_tenant:
                continue
            if not bool(row.get("active", False)):
                continue
            device_id = str(row.get("device_id", "unknown"))
            # Keep the most recently updated device record
            if device_id not in devices or str(row.get("last_seen_at", "")) > str(devices[device_id].get("last_seen_at", "")):
                devices[device_id] = {
                    "device_id": device_id,
                    "device_name": str(row.get("device_name", "Unknown")),
                    "client_ip": str(row.get("client_ip", "")),
                    "user_agent": str(row.get("user_agent", ""))[:100],  # truncate UA
                    "auth_source": str(row.get("auth_source", "")),
                    "created_at": str(row.get("created_at", "")),
                    "last_seen_at": str(row.get("last_seen_at", "")),
                    "session_count": len([s for s in _state.rows.values() 
                                        if str(s.get("device_id", "")) == device_id 
                                        and bool(s.get("active", False))]),
                }
    
    result = list(devices.values())
    result.sort(key=lambda x: x["last_seen_at"], reverse=True)
    return result


def revoke_device(*, device_id: str, user_id: str, tenant_id: int) -> int:
    """Revoke all sessions for a specific device."""
    normalized_device_id = str(device_id).strip()
    normalized_user = str(user_id).strip()
    normalized_tenant = int(tenant_id)

    with get_raw_conn() as conn:
        if _ensure_session_table(conn):
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE app_auth_sessions
                    SET is_revoked = TRUE,
                        revoked_at = NOW(),
                        last_seen_at = NOW()
                    WHERE device_id = %s
                      AND user_id = %s
                      AND tenant_id = %s
                      AND is_revoked = FALSE
                    """,
                    (normalized_device_id, normalized_user, normalized_tenant),
                )
                updated = int(cur.rowcount)
            conn.commit()
            return updated

    revoked = 0
    with _state_lock:
        for row in _state.rows.values():
            if str(row.get("device_id", "")) != normalized_device_id:
                continue
            if str(row.get("user_id", "")).strip() != normalized_user:
                continue
            if int(row.get("tenant_id", 0)) != normalized_tenant:
                continue
            if not bool(row.get("active", False)):
                continue
            row["active"] = False
            row["is_revoked"] = True
            row["revoked_at"] = _now_iso()
            revoked += 1
    return revoked


def clear_sessions_state() -> None:
    global _db_ready

    with get_raw_conn() as conn:
        if _ensure_session_table(conn):
            with conn.cursor() as cur:
                cur.execute("DELETE FROM app_auth_sessions")
            conn.commit()

    with _state_lock:
        _state.rows.clear()
        _db_ready = False
