from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
import secrets
from threading import Lock
from typing import Any

from app.modules.integrations.service import get_global_setting, save_global_setting


_SESSIONS_SETTINGS_KEY = "auth.sessions_json"


@dataclass
class SessionState:
    rows: dict[str, dict[str, Any]]


_state_lock = Lock()
_state = SessionState(rows={})
_loaded = False


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_once() -> None:
    global _loaded
    if _loaded:
        return
    _loaded = True
    raw = get_global_setting(_SESSIONS_SETTINGS_KEY)
    if raw is None or not raw.value:
        return
    try:
        payload = json.loads(raw.value)
    except json.JSONDecodeError:
        return
    if not isinstance(payload, dict):
        return
    rows = payload.get("rows")
    if not isinstance(rows, dict):
        return
    for key, value in rows.items():
        if not isinstance(key, str) or not isinstance(value, dict):
            continue
        _state.rows[key] = value


def _persist() -> None:
    payload = {"rows": _state.rows}
    save_global_setting(_SESSIONS_SETTINGS_KEY, json.dumps(payload), is_secret=True)


def create_session(
    *,
    user_id: str,
    tenant_id: int,
    auth_source: str,
    client_ip: str,
    user_agent: str,
) -> dict[str, Any]:
    _load_once()
    session_id = secrets.token_urlsafe(24)
    row = {
        "session_id": session_id,
        "user_id": str(user_id),
        "tenant_id": int(tenant_id),
        "auth_source": str(auth_source),
        "client_ip": str(client_ip),
        "user_agent": str(user_agent),
        "created_at": _now_iso(),
        "last_seen_at": _now_iso(),
        "revoked_at": None,
        "active": True,
    }
    with _state_lock:
        _state.rows[session_id] = row
        _persist()
    return dict(row)


def touch_session(session_id: str) -> None:
    _load_once()
    normalized = str(session_id).strip()
    if not normalized:
        return
    with _state_lock:
        row = _state.rows.get(normalized)
        if row is None or not bool(row.get("active", False)):
            return
        row["last_seen_at"] = _now_iso()
        _persist()


def is_session_active(session_id: str) -> bool:
    _load_once()
    normalized = str(session_id).strip()
    if not normalized:
        return False
    with _state_lock:
        row = _state.rows.get(normalized)
        if row is None:
            return False
        return bool(row.get("active", False))


def list_sessions_for_user(*, user_id: str, tenant_id: int) -> list[dict[str, Any]]:
    _load_once()
    normalized_user = str(user_id).strip()
    normalized_tenant = int(tenant_id)
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
    _load_once()
    normalized = str(session_id).strip()
    if not normalized:
        return False
    with _state_lock:
        row = _state.rows.get(normalized)
        if row is None:
            return False
        if not bool(row.get("active", False)):
            return False
        row["active"] = False
        row["revoked_at"] = _now_iso()
        row["last_seen_at"] = _now_iso()
        _persist()
        return True


def revoke_all_sessions_for_user(*, user_id: str, tenant_id: int) -> int:
    _load_once()
    normalized_user = str(user_id).strip()
    normalized_tenant = int(tenant_id)
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
            row["revoked_at"] = _now_iso()
            row["last_seen_at"] = _now_iso()
            revoked += 1
        if revoked:
            _persist()
    return revoked


def clear_sessions_state() -> None:
    global _loaded
    with _state_lock:
        _state.rows.clear()
        _loaded = False
        save_global_setting(_SESSIONS_SETTINGS_KEY, json.dumps({"rows": {}}), is_secret=True)
