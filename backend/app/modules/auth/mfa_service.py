from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
import struct
import time
from datetime import datetime, timezone
import json
from threading import Lock
from typing import Any

from app.core.db import get_raw_conn


_state_lock = Lock()
# Table is guaranteed by Alembic migration f3e4d5c6b7a9_add_auth_session_and_mfa_tables.
# In-memory fallback (_state) is used only when DB is unavailable (e.g. tests without DATABASE_URL).
_db_ready = True
_state: dict[str, dict[str, Any]] = {}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _state_key(user_id: str, tenant_id: int) -> str:
    return f"{int(tenant_id)}:{str(user_id).strip()}"


def _ensure_mfa_table(conn) -> bool:
    """Return True if DB is available; False causes caller to use in-memory fallback."""
    if conn is None:
        return False
    return _db_ready


def _parse_recovery_codes(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value]
    if isinstance(value, tuple):
        return [str(item) for item in value]
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return []
        try:
            parsed = json.loads(text)
            if isinstance(parsed, list):
                return [str(item) for item in parsed]
        except json.JSONDecodeError:
            return []
    return []


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
    normalized_user_id = str(user_id).strip()
    normalized_tenant_id = int(tenant_id)
    secret = _generate_secret()
    recovery_codes = _generate_recovery_codes()
    hashes = [_hash_recovery_code(item) for item in recovery_codes]

    with get_raw_conn() as conn:
        if _ensure_mfa_table(conn):
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO app_mfa_state (
                        user_id,
                        tenant_id,
                        secret_encrypted,
                        pending_secret_encrypted,
                        recovery_codes,
                        enabled,
                        created_at,
                        updated_at
                    )
                    VALUES (%s, %s, NULL, %s, %s::jsonb, FALSE, NOW(), NOW())
                    ON CONFLICT (user_id, tenant_id)
                    DO UPDATE SET
                        secret_encrypted = NULL,
                        pending_secret_encrypted = EXCLUDED.pending_secret_encrypted,
                        recovery_codes = EXCLUDED.recovery_codes,
                        enabled = FALSE,
                        updated_at = NOW()
                    """,
                    (
                        normalized_user_id,
                        normalized_tenant_id,
                        secret,
                        json.dumps(hashes),
                    ),
                )
            conn.commit()
            return {
                "status": "pending",
                "secret": secret,
                "otpauth_uri": f"otpauth://totp/{issuer}:{normalized_user_id}?secret={secret}&issuer={issuer}",
                "recovery_codes": recovery_codes,
            }

    key = _state_key(normalized_user_id, normalized_tenant_id)
    row = {
        "user_id": normalized_user_id,
        "tenant_id": normalized_tenant_id,
        "enabled": False,
        "secret": None,
        "pending_secret": secret,
        "recovery_code_hashes": hashes,
        "updated_at": _now_iso(),
        "created_at": _now_iso(),
    }
    with _state_lock:
        _state[key] = row
    return {
        "status": "pending",
        "secret": secret,
        "otpauth_uri": f"otpauth://totp/{issuer}:{normalized_user_id}?secret={secret}&issuer={issuer}",
        "recovery_codes": recovery_codes,
    }


def enable_mfa(*, user_id: str, tenant_id: int, code: str) -> bool:
    normalized_user_id = str(user_id).strip()
    normalized_tenant_id = int(tenant_id)

    with get_raw_conn() as conn:
        if _ensure_mfa_table(conn):
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT pending_secret_encrypted
                    FROM app_mfa_state
                    WHERE user_id = %s AND tenant_id = %s
                    FOR UPDATE
                    """,
                    (normalized_user_id, normalized_tenant_id),
                )
                row = cur.fetchone()
                if row is None:
                    conn.rollback()
                    return False
                pending = str(row[0] or "").strip()
                if not pending or not verify_totp_code(pending, code):
                    conn.rollback()
                    return False
                cur.execute(
                    """
                    UPDATE app_mfa_state
                    SET enabled = TRUE,
                        secret_encrypted = %s,
                        pending_secret_encrypted = NULL,
                        updated_at = NOW()
                    WHERE user_id = %s AND tenant_id = %s
                    """,
                    (pending, normalized_user_id, normalized_tenant_id),
                )
            conn.commit()
            return True

    key = _state_key(normalized_user_id, normalized_tenant_id)
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
        return True


def is_mfa_enabled(*, user_id: str, tenant_id: int) -> bool:
    normalized_user_id = str(user_id).strip()
    normalized_tenant_id = int(tenant_id)

    with get_raw_conn() as conn:
        if _ensure_mfa_table(conn):
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT enabled
                    FROM app_mfa_state
                    WHERE user_id = %s AND tenant_id = %s
                    LIMIT 1
                    """,
                    (normalized_user_id, normalized_tenant_id),
                )
                row = cur.fetchone()
            return bool(row and row[0])

    key = _state_key(normalized_user_id, normalized_tenant_id)
    with _state_lock:
        row = _state.get(key)
        return bool(row and row.get("enabled", False))


def verify_mfa(*, user_id: str, tenant_id: int, code: str | None = None, recovery_code: str | None = None) -> bool:
    normalized_user_id = str(user_id).strip()
    normalized_tenant_id = int(tenant_id)

    with get_raw_conn() as conn:
        if _ensure_mfa_table(conn):
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT enabled, secret_encrypted, recovery_codes
                    FROM app_mfa_state
                    WHERE user_id = %s AND tenant_id = %s
                    FOR UPDATE
                    """,
                    (normalized_user_id, normalized_tenant_id),
                )
                row = cur.fetchone()
                if row is None or not bool(row[0]):
                    conn.rollback()
                    return False

                secret = str(row[1] or "").strip()
                if code is not None and secret and verify_totp_code(secret, code):
                    conn.rollback()
                    return True

                if recovery_code is not None:
                    candidate = _hash_recovery_code(str(recovery_code).strip())
                    hashes = _parse_recovery_codes(row[2])
                    if candidate in hashes:
                        hashes.remove(candidate)
                        cur.execute(
                            """
                            UPDATE app_mfa_state
                            SET recovery_codes = %s::jsonb,
                                updated_at = NOW()
                            WHERE user_id = %s AND tenant_id = %s
                            """,
                            (json.dumps(hashes), normalized_user_id, normalized_tenant_id),
                        )
                        conn.commit()
                        return True

                conn.rollback()
                return False

    key = _state_key(normalized_user_id, normalized_tenant_id)
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
                return True
    return False


def disable_mfa(*, user_id: str, tenant_id: int) -> bool:
    normalized_user_id = str(user_id).strip()
    normalized_tenant_id = int(tenant_id)

    with get_raw_conn() as conn:
        if _ensure_mfa_table(conn):
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE app_mfa_state
                    SET enabled = FALSE,
                        secret_encrypted = NULL,
                        pending_secret_encrypted = NULL,
                        recovery_codes = '[]'::jsonb,
                        updated_at = NOW()
                    WHERE user_id = %s
                      AND tenant_id = %s
                      AND (enabled = TRUE OR pending_secret_encrypted IS NOT NULL)
                    """,
                    (normalized_user_id, normalized_tenant_id),
                )
                updated = int(cur.rowcount)
            conn.commit()
            return updated > 0

    key = _state_key(normalized_user_id, normalized_tenant_id)
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
        return True


def clear_mfa_state() -> None:
    global _db_ready

    with get_raw_conn() as conn:
        if _ensure_mfa_table(conn):
            with conn.cursor() as cur:
                cur.execute("DELETE FROM app_mfa_state")
            conn.commit()

    with _state_lock:
        _state.clear()
        _db_ready = False
