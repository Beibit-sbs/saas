from __future__ import annotations

import hashlib
import hmac
import json
import time
from dataclasses import dataclass


@dataclass(frozen=True)
class WebhookSubscription:
    tenant_id: int
    event_type: str
    endpoint_url: str
    secret: str
    active: bool = True


def sign_webhook_payload(*, secret: str, payload: dict[str, object], timestamp: int | None = None) -> str:
    ts = int(time.time()) if timestamp is None else int(timestamp)
    body = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    signed = f"{ts}.".encode("ascii") + body
    signature = hmac.new(secret.encode("utf-8"), signed, hashlib.sha256).hexdigest()
    return f"t={ts},v1={signature}"


def verify_webhook_signature(*, secret: str, payload: dict[str, object], header_value: str, tolerance_seconds: int = 300) -> bool:
    parts = dict(item.split("=", 1) for item in header_value.split(",") if "=" in item)
    if "t" not in parts or "v1" not in parts:
        return False
    try:
        ts = int(parts["t"])
    except ValueError:
        return False
    now = int(time.time())
    if abs(now - ts) > max(30, int(tolerance_seconds)):
        return False
    expected = sign_webhook_payload(secret=secret, payload=payload, timestamp=ts)
    expected_sig = dict(item.split("=", 1) for item in expected.split(",")).get("v1", "")
    return hmac.compare_digest(parts.get("v1", ""), expected_sig)
