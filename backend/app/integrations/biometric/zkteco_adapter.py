"""L.4 — ZKTeco Biometric Access Control adapter (stub)."""
from __future__ import annotations

from datetime import datetime

import httpx

ZKTECO_BASE_URL = "http://zkteco-controller/api"
DEFAULT_TIMEOUT = 10


class ZKTecoError(Exception):
    pass


class AccessEvent:
    def __init__(self, event_id: str, user_id: str, door: str, direction: str, timestamp: str, granted: bool):
        self.event_id = event_id
        self.user_id = user_id
        self.door = door
        self.direction = direction
        self.timestamp = timestamp
        self.granted = granted

    def to_dict(self) -> dict:
        return {
            "event_id": self.event_id,
            "user_id": self.user_id,
            "door": self.door,
            "direction": self.direction,
            "timestamp": self.timestamp,
            "granted": self.granted,
        }


def get_events(from_dt: datetime, *, to_dt: datetime | None = None) -> list[AccessEvent]:
    """Fetch access events from ZKTeco controller since from_dt."""
    if from_dt is None:
        raise ValueError("from_dt is required")

    params: dict = {"from": from_dt.isoformat()}
    if to_dt:
        params["to"] = to_dt.isoformat()

    try:
        resp = httpx.get(f"{ZKTECO_BASE_URL}/events", params=params, timeout=DEFAULT_TIMEOUT)
        resp.raise_for_status()
        items = resp.json().get("events", [])
    except httpx.RequestError as exc:
        raise ZKTecoError(f"ZKTeco get_events failed: {exc}") from exc

    return [
        AccessEvent(
            event_id=e.get("id", ""),
            user_id=e.get("userId", ""),
            door=e.get("door", ""),
            direction=e.get("direction", "IN"),
            timestamp=e.get("timestamp", ""),
            granted=e.get("granted", False),
        )
        for e in items
    ]


def enroll_user(user_id: str, biometric_data: bytes, *, door_groups: list[str] | None = None) -> bool:
    """Enroll a user with biometric template. Returns True on success."""
    if not user_id:
        raise ValueError("user_id is required")
    if not biometric_data:
        raise ValueError("biometric_data is required")

    import base64
    payload = {
        "userId": user_id,
        "biometricTemplate": base64.b64encode(biometric_data).decode(),
        "doorGroups": door_groups or [],
    }
    try:
        resp = httpx.post(f"{ZKTECO_BASE_URL}/enroll", json=payload, timeout=DEFAULT_TIMEOUT)
        resp.raise_for_status()
        return resp.json().get("success", False)
    except httpx.RequestError as exc:
        raise ZKTecoError(f"ZKTeco enroll_user failed: {exc}") from exc


def delete_user(user_id: str) -> bool:
    """Remove a user from the ZKTeco controller."""
    if not user_id:
        raise ValueError("user_id is required")
    try:
        resp = httpx.delete(f"{ZKTECO_BASE_URL}/users/{user_id}", timeout=DEFAULT_TIMEOUT)
        resp.raise_for_status()
        return resp.json().get("success", False)
    except httpx.RequestError as exc:
        raise ZKTecoError(f"ZKTeco delete_user failed: {exc}") from exc
