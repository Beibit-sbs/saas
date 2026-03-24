from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from threading import Lock
from typing import Any


try:
    import redis
except ImportError:  # pragma: no cover
    redis = None


_lock = Lock()
_state: dict[str, Any] = {
    "worker_heartbeat_at": None,
    "scheduler_last_run_at": None,
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _redis_client():
    url = os.getenv("REDIS_URL", "").strip()
    if not url or redis is None:
        return None
    try:
        return redis.Redis.from_url(url, decode_responses=True, socket_timeout=1)
    except Exception:
        return None


def _write_state(key: str, value: Any) -> None:
    client = _redis_client()
    if client is not None:
        try:
            client.set(f"platform:runtime:{key}", json.dumps(value))
            return
        except Exception:
            pass
    with _lock:
        _state[key] = value


def _read_state(key: str) -> Any:
    client = _redis_client()
    if client is not None:
        try:
            raw = client.get(f"platform:runtime:{key}")
            if raw:
                return json.loads(raw)
        except Exception:
            pass
    with _lock:
        return _state.get(key)


def record_worker_heartbeat() -> str:
    heartbeat = _now_iso()
    _write_state("worker_heartbeat_at", heartbeat)
    return heartbeat


def get_worker_heartbeat() -> str | None:
    value = _read_state("worker_heartbeat_at")
    return str(value) if value else None


def record_scheduler_run(task_name: str | None = None) -> str:
    payload = {
        "at": _now_iso(),
        "task_name": str(task_name or "scheduler"),
    }
    _write_state("scheduler_last_run_at", payload)
    return str(payload["at"])


def get_scheduler_last_run() -> dict[str, Any] | None:
    value = _read_state("scheduler_last_run_at")
    return dict(value) if isinstance(value, dict) else None


def clear_runtime_state() -> None:
    with _lock:
        _state["worker_heartbeat_at"] = None
        _state["scheduler_last_run_at"] = None