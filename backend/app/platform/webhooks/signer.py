from __future__ import annotations

import hashlib
import hmac
import json
import time
from typing import Any


def canonical_json_bytes(payload: dict[str, Any]) -> bytes:
    # Stable encoding ensures reproducible signatures across retries.
    return json.dumps(payload, separators=(",", ":"), sort_keys=True, ensure_ascii=True).encode("utf-8")


def build_webhook_signature(payload_bytes: bytes, *, signing_secret: str, timestamp: int | None = None) -> dict[str, str]:
    normalized_secret = signing_secret.strip()
    if not normalized_secret:
        raise ValueError("webhook signing secret is required")

    signed_timestamp = int(time.time()) if timestamp is None else int(timestamp)
    signed_payload = f"{signed_timestamp}.".encode("utf-8") + payload_bytes
    digest = hmac.new(normalized_secret.encode("utf-8"), signed_payload, hashlib.sha256).hexdigest()
    return {
        "X-Webhook-Timestamp": str(signed_timestamp),
        "X-Webhook-Signature": f"t={signed_timestamp},v1={digest}",
        "Content-Type": "application/json",
    }