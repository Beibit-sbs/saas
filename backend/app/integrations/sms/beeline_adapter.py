"""L.2 — Beeline KZ SMS gateway adapter (stub)."""
from __future__ import annotations

import httpx

BEELINE_BASE_URL = "https://smspro.beeline.kz/api"
DEFAULT_TIMEOUT = 10


class BeelineSmsError(Exception):
    pass


def send_sms(phone: str, message: str, *, sender: str = "INFO") -> str:
    """Send SMS via Beeline KZ. Returns delivery_status: SENT / FAILED / QUEUED."""
    if not phone:
        raise ValueError("phone is required")
    if not message:
        raise ValueError("message is required")
    if len(message) > 1024:
        raise ValueError("message too long (max 1024 chars)")

    payload = {
        "phone": phone,
        "message": message,
        "sender": sender,
    }
    try:
        resp = httpx.post(f"{BEELINE_BASE_URL}/send", json=payload, timeout=DEFAULT_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        return data.get("status", "QUEUED")
    except httpx.RequestError as exc:
        raise BeelineSmsError(f"Beeline send_sms failed: {exc}") from exc


def check_delivery(message_id: str) -> str:
    """Check SMS delivery status by message_id."""
    if not message_id:
        raise ValueError("message_id is required")
    try:
        resp = httpx.get(f"{BEELINE_BASE_URL}/status/{message_id}", timeout=DEFAULT_TIMEOUT)
        resp.raise_for_status()
        return resp.json().get("status", "UNKNOWN")
    except httpx.RequestError as exc:
        raise BeelineSmsError(f"Beeline check_delivery failed: {exc}") from exc
