from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import struct
import time
from datetime import datetime, timezone
from threading import Lock
from typing import Any

from app.modules.integrations.service import get_global_setting, save_global_setting


_MFA_SETTINGS_KEY = "auth.mfa_state_json"

_state_lock = Lock()
_loaded = False
_state: dict[str, dict[str, Any]] = {}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _state_key(user_id: str, tenant_id: int) -> str:
    return f"{int(tenant_id)}:{str(user_id).strip()}"


def _load_once() -> None:
    global _loaded
    if _loaded:
        return
    _loaded = True
    raw = get_global_setting(_MFA_SETTINGS_KEY)
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
        if isinstance(key, str) and isinstance(value, dict):
            _state[key] = value


def _persist() -> None:
    save_global_setting(_MFA_SETTINGS_KEY, json.dumps({"rows": _state}), is_secret=True)


def _generate_secret() -> str:
    return base64.b32encode(secrets.token_bytes(20)).decode("ascii").rstrip("=")


def _normalize_base32_secret(secret: str) -> bytes:
    normalized = str(secret).strip().upper().replace(" ", "")
    padding = "=" * ((8 - len(normalized) % 8) % 8)
    return base64.b32decode(normalized + padding, casefold=True)


def _totp(secret: str, for_time: int, step_seconds: int = 30, digits: int = 6) -> str:
    key = _normalize_base32_secret(secret)
    counter = int(for_time // step_seconds)
    msg = struct.pack(">Q", counter)
    digest = hmac.new(key, msg, hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    code_int = struct.unpack(">I", digest[offset : offset + 4])[0] & 0x7FFFFFFF
    code = code_int % (10 ** digits)
    return str(code).zfill(digits)


def verify_totp_code(secret: str, code: str, *, allowed_drift_steps: int = 1) -> bool:
    normalized_code = str(code).strip()
    if len(normalized_code) != 6 or not normalized_code.isdigit():
        return False
    now = int(time.time())
    for shift in range(-allowed_drift_steps, allowed_drift_steps + 1):
        ts = now + (shift * 30)
        if hmac.compare_digest(_totp(secret, ts), normalized_code):
            return True
    return False


def _hash_recovery_code(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _generate_recovery_codes(count: int = 8) -> list[str]:
    return [secrets.token_hex(4) for _ in range(max(1, count))]


def initiate_mfa_enrollment(*, user_id: str, tenant_id: int, issuer: str = "ai-saas") -> dict[str, Any]:
    _load_once()
    key = _state_key(user_id, tenant_id)
    secret = _generate_secret()
    recovery_codes = _generate_recovery_codes()
    row = {
        "user_id": str(user_id),
        "tenant_id": int(tenant_id),
        "enabled": False,
        "secret": None,
        "pending_secret": secret,
        "recovery_code_hashes": [_hash_recovery_code(item) for item in recovery_codes],
        "updated_at": _now_iso(),
        "created_at": _now_iso(),
    }
    with _state_lock:
        _state[key] = row
        _persist()
    return {
        "status": "pending",
        "secret": secret,
        "otpauth_uri": f"otpauth://totp/{issuer}:{user_id}?secret={secret}&issuer={issuer}",
        "recovery_codes": recovery_codes,
    }


def enable_mfa(*, user_id: str, tenant_id: int, code: str) -> bool:
    _load_once()
    key = _state_key(user_id, tenant_id)
    with _state_lock:
        row = _state.get(key)
        if row is None:
            return False
        pending = str(row.get("pending_secret") or "").strip()
        if not pending:
            return False
        if not verify_totp_code(pending, code):
            return False
        row["enabled"] = True
        row["secret"] = pending
        row["pending_secret"] = None
        row["updated_at"] = _now_iso()
        _persist()
        return True


def is_mfa_enabled(*, user_id: str, tenant_id: int) -> bool:
    _load_once()
    key = _state_key(user_id, tenant_id)
    with _state_lock:
        row = _state.get(key)
        return bool(row and row.get("enabled", False))


def verify_mfa(*, user_id: str, tenant_id: int, code: str | None = None, recovery_code: str | None = None) -> bool:
    _load_once()
    key = _state_key(user_id, tenant_id)
    with _state_lock:
        row = _state.get(key)
        if row is None:
            return False
        if not bool(row.get("enabled", False)):
            return False
        secret = str(row.get("secret") or "").strip()
        if code is not None and secret and verify_totp_code(secret, code):
            return True
        if recovery_code is not None:
            candidate = _hash_recovery_code(str(recovery_code).strip())
            hashes = list(row.get("recovery_code_hashes") or [])
            if candidate in hashes:
                hashes.remove(candidate)
                row["recovery_code_hashes"] = hashes
                row["updated_at"] = _now_iso()
                _persist()
                return True
    return False


def disable_mfa(*, user_id: str, tenant_id: int) -> bool:
    _load_once()
    key = _state_key(user_id, tenant_id)
    with _state_lock:
        row = _state.get(key)
        if row is None:
            return False
        if not bool(row.get("enabled", False)) and not row.get("pending_secret"):
            return False
        row["enabled"] = False
        row["secret"] = None
        row["pending_secret"] = None
        row["recovery_code_hashes"] = []
        row["updated_at"] = _now_iso()
        _persist()
        return True


def clear_mfa_state() -> None:
    global _loaded
    with _state_lock:
        _state.clear()
        _loaded = False
        save_global_setting(_MFA_SETTINGS_KEY, json.dumps({"rows": {}}), is_secret=True)
