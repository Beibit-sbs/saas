"""L.2 — Kcell SMS gateway adapter (stub)."""
from __future__ import annotations

import httpx

KCELL_BASE_URL = "https://sms.kcell.kz/api/v1"
DEFAULT_TIMEOUT = 10


class KcellSmsError(Exception):
    pass


def send_sms(phone: str, message: str, *, sender: str = "INFO") -> str:
    """Send SMS via Kcell. Returns delivery_status: SENT / FAILED / QUEUED."""
    if not phone:
        raise ValueError("phone is required")
    if not message:
        raise ValueError("message is required")
    if len(message) > 1024:
        raise ValueError("message too long (max 1024 chars)")

    payload = {
        "msisdn": phone,
        "text": message,
        "sourceAddress": sender,
    }
    try:
        resp = httpx.post(f"{KCELL_BASE_URL}/message/send", json=payload, timeout=DEFAULT_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        return data.get("deliveryStatus", "QUEUED")
    except httpx.RequestError as exc:
        raise KcellSmsError(f"Kcell send_sms failed: {exc}") from exc


def check_delivery(message_id: str) -> str:
    """Check SMS delivery status by message_id."""
    if not message_id:
        raise ValueError("message_id is required")
    try:
        resp = httpx.get(f"{KCELL_BASE_URL}/message/{message_id}", timeout=DEFAULT_TIMEOUT)
        resp.raise_for_status()
        return resp.json().get("deliveryStatus", "UNKNOWN")
    except httpx.RequestError as exc:
        raise KcellSmsError(f"Kcell check_delivery failed: {exc}") from exc
