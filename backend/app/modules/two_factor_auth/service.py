"""Phase LIV — 2FA SMS + TOTP service."""
from __future__ import annotations

import hashlib
import hmac
import secrets
import struct
import time
from dataclasses import dataclass

from app.modules.university_core.tenant_entity_api import (
    create_entity_for_tenant,
    list_entities_for_tenant,
    update_entity_for_tenant,
)
from app.platform.events.publisher import EventPublisher

METHOD_TYPES = {"sms", "totp", "backup_code"}
CHALLENGE_STATES = {"pending", "verified", "expired", "failed"}
TOTP_DIGITS = 6
TOTP_PERIOD = 30  # seconds
SMS_CODE_LENGTH = 6
MAX_BACKUP_CODES = 10


class TwoFactorError(Exception):
    """Raised on invalid 2FA service input."""


@dataclass
class TwoFactorEnrollment:
    enrollment_id: int
    user_id: int
    method: str
    is_active: bool
    tenant_id: int


@dataclass
class TwoFactorChallenge:
    challenge_id: int
    user_id: int
    method: str
    status: str
    tenant_id: int


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _generate_sms_code() -> str:
    """Generate a random 6-digit SMS OTP."""
    return str(secrets.randbelow(10 ** SMS_CODE_LENGTH)).zfill(SMS_CODE_LENGTH)


def _generate_totp_secret() -> str:
    """Generate a random TOTP secret (hex)."""
    return secrets.token_hex(20)


def _compute_totp(secret_hex: str, timestamp: int | None = None) -> str:
    """Compute TOTP value for the given secret (RFC 6238 simplified)."""
    if timestamp is None:
        timestamp = int(time.time())
    counter = timestamp // TOTP_PERIOD
    secret_bytes = bytes.fromhex(secret_hex)
    counter_bytes = struct.pack(">Q", counter)
    hmac_digest = hmac.new(secret_bytes, counter_bytes, hashlib.sha1).digest()
    offset = hmac_digest[-1] & 0x0F
    truncated = struct.unpack(">I", hmac_digest[offset : offset + 4])[0] & 0x7FFFFFFF
    code = truncated % (10 ** TOTP_DIGITS)
    return str(code).zfill(TOTP_DIGITS)


def _generate_backup_codes(count: int = 8) -> list[str]:
    """Generate a list of one-time backup codes."""
    return [secrets.token_hex(4).upper() for _ in range(count)]


# ---------------------------------------------------------------------------
# Enrollment
# ---------------------------------------------------------------------------


def enroll_2fa(
    *,
    user_id: int,
    method: str,
    tenant_id: int,
) -> TwoFactorEnrollment:
    """Enroll a user for 2FA using SMS or TOTP."""
    if not user_id or user_id <= 0:
        raise TwoFactorError("user_id is required")
    if method not in METHOD_TYPES:
        raise TwoFactorError(f"invalid method: {method!r}; must be one of {METHOD_TYPES}")

    secret = _generate_totp_secret() if method == "totp" else ""

    record = create_entity_for_tenant(
        "twofa_enrollments",
        {
            "user_id": user_id,
            "method": method,
            "secret": secret,
            "is_active": False,
            "status": "pending_verification",
        },
        tenant_id,
    )

    try:
        EventPublisher.publish(
            tenant_id=tenant_id,
            event_type="twofa.enrollment_started",
            payload={"user_id": user_id, "method": method},
        )
    except Exception:
        pass

    return TwoFactorEnrollment(
        enrollment_id=record["id"],
        user_id=user_id,
        method=method,
        is_active=False,
        tenant_id=tenant_id,
    )


def activate_enrollment(*, enrollment_id: int, tenant_id: int) -> TwoFactorEnrollment:
    """Activate a 2FA enrollment after initial verification."""
    enrollments = list_entities_for_tenant("twofa_enrollments", tenant_id)
    matched = [e for e in enrollments if e["id"] == enrollment_id]
    if not matched:
        raise TwoFactorError(f"enrollment {enrollment_id} not found")

    enrollment = matched[0]
    if enrollment.get("is_active"):
        raise TwoFactorError("enrollment is already active")

    update_entity_for_tenant(
        "twofa_enrollments", enrollment_id, {"is_active": True, "status": "active"}, tenant_id
    )

    try:
        EventPublisher.publish(
            tenant_id=tenant_id,
            event_type="twofa.enrollment_activated",
            payload={"user_id": enrollment["user_id"], "method": enrollment["method"]},
        )
    except Exception:
        pass

    return TwoFactorEnrollment(
        enrollment_id=enrollment_id,
        user_id=enrollment["user_id"],
        method=enrollment["method"],
        is_active=True,
        tenant_id=tenant_id,
    )


def revoke_enrollment(*, enrollment_id: int, tenant_id: int) -> TwoFactorEnrollment:
    """Revoke/deactivate a 2FA enrollment."""
    enrollments = list_entities_for_tenant("twofa_enrollments", tenant_id)
    matched = [e for e in enrollments if e["id"] == enrollment_id]
    if not matched:
        raise TwoFactorError(f"enrollment {enrollment_id} not found")

    enrollment = matched[0]
    if not enrollment.get("is_active"):
        raise TwoFactorError("enrollment is not active; cannot revoke")

    update_entity_for_tenant(
        "twofa_enrollments", enrollment_id, {"is_active": False, "status": "revoked"}, tenant_id
    )

    return TwoFactorEnrollment(
        enrollment_id=enrollment_id,
        user_id=enrollment["user_id"],
        method=enrollment["method"],
        is_active=False,
        tenant_id=tenant_id,
    )


# ---------------------------------------------------------------------------
# Challenges (SMS / TOTP verification)
# ---------------------------------------------------------------------------


def create_challenge(
    *,
    user_id: int,
    method: str,
    tenant_id: int,
) -> TwoFactorChallenge:
    """Issue a 2FA challenge for a login attempt."""
    if not user_id or user_id <= 0:
        raise TwoFactorError("user_id is required")
    if method not in ("sms", "totp"):
        raise TwoFactorError(f"invalid method: {method!r}")

    code = _generate_sms_code() if method == "sms" else ""

    record = create_entity_for_tenant(
        "twofa_challenges",
        {
            "user_id": user_id,
            "method": method,
            "code": code,
            "status": "pending",
        },
        tenant_id,
    )

    return TwoFactorChallenge(
        challenge_id=record["id"],
        user_id=user_id,
        method=method,
        status="pending",
        tenant_id=tenant_id,
    )


def verify_sms_challenge(
    *,
    challenge_id: int,
    code: str,
    tenant_id: int,
) -> TwoFactorChallenge:
    """Verify a SMS OTP challenge."""
    if not code or not code.strip():
        raise TwoFactorError("code is required")

    challenges = list_entities_for_tenant("twofa_challenges", tenant_id)
    matched = [c for c in challenges if c["id"] == challenge_id]
    if not matched:
        raise TwoFactorError(f"challenge {challenge_id} not found")

    challenge = matched[0]
    if challenge["status"] != "pending":
        raise TwoFactorError(
            f"challenge is already in status {challenge['status']!r}; cannot verify"
        )
    if challenge["method"] != "sms":
        raise TwoFactorError("challenge is not an SMS challenge")

    # Constant-time comparison
    expected = challenge.get("code", "")
    is_valid = hmac.compare_digest(expected, code.strip())
    new_status = "verified" if is_valid else "failed"

    update_entity_for_tenant(
        "twofa_challenges", challenge_id, {"status": new_status}, tenant_id
    )

    if not is_valid:
        try:
            EventPublisher.publish(
                tenant_id=tenant_id,
                event_type="twofa.verification_failed",
                payload={"user_id": challenge["user_id"], "method": "sms"},
            )
        except Exception:
            pass
        raise TwoFactorError("invalid SMS code")

    try:
        EventPublisher.publish(
            tenant_id=tenant_id,
            event_type="twofa.verified",
            payload={"user_id": challenge["user_id"], "method": "sms"},
        )
    except Exception:
        pass

    return TwoFactorChallenge(
        challenge_id=challenge_id,
        user_id=challenge["user_id"],
        method="sms",
        status="verified",
        tenant_id=tenant_id,
    )


def verify_totp_challenge(
    *,
    challenge_id: int,
    totp_code: str,
    secret_hex: str,
    tenant_id: int,
) -> TwoFactorChallenge:
    """Verify a TOTP challenge (checks current and previous window)."""
    if not totp_code or not totp_code.strip():
        raise TwoFactorError("totp_code is required")
    if not secret_hex or not secret_hex.strip():
        raise TwoFactorError("secret_hex is required")

    challenges = list_entities_for_tenant("twofa_challenges", tenant_id)
    matched = [c for c in challenges if c["id"] == challenge_id]
    if not matched:
        raise TwoFactorError(f"challenge {challenge_id} not found")

    challenge = matched[0]
    if challenge["status"] != "pending":
        raise TwoFactorError(
            f"challenge is already in status {challenge['status']!r}; cannot verify"
        )
    if challenge["method"] != "totp":
        raise TwoFactorError("challenge is not a TOTP challenge")

    now = int(time.time())
    valid_codes = {
        _compute_totp(secret_hex.strip(), now),
        _compute_totp(secret_hex.strip(), now - TOTP_PERIOD),
    }
    is_valid = totp_code.strip() in valid_codes
    new_status = "verified" if is_valid else "failed"

    update_entity_for_tenant(
        "twofa_challenges", challenge_id, {"status": new_status}, tenant_id
    )

    if not is_valid:
        try:
            EventPublisher.publish(
                tenant_id=tenant_id,
                event_type="twofa.verification_failed",
                payload={"user_id": challenge["user_id"], "method": "totp"},
            )
        except Exception:
            pass
        raise TwoFactorError("invalid TOTP code")

    try:
        EventPublisher.publish(
            tenant_id=tenant_id,
            event_type="twofa.verified",
            payload={"user_id": challenge["user_id"], "method": "totp"},
        )
    except Exception:
        pass

    return TwoFactorChallenge(
        challenge_id=challenge_id,
        user_id=challenge["user_id"],
        method="totp",
        status="verified",
        tenant_id=tenant_id,
    )


def expire_challenge(*, challenge_id: int, tenant_id: int) -> TwoFactorChallenge:
    """Expire a pending challenge (TTL enforcement)."""
    challenges = list_entities_for_tenant("twofa_challenges", tenant_id)
    matched = [c for c in challenges if c["id"] == challenge_id]
    if not matched:
        raise TwoFactorError(f"challenge {challenge_id} not found")

    challenge = matched[0]
    if challenge["status"] != "pending":
        raise TwoFactorError(
            f"only pending challenges can be expired; current status: {challenge['status']!r}"
        )

    update_entity_for_tenant(
        "twofa_challenges", challenge_id, {"status": "expired"}, tenant_id
    )

    return TwoFactorChallenge(
        challenge_id=challenge_id,
        user_id=challenge["user_id"],
        method=challenge["method"],
        status="expired",
        tenant_id=tenant_id,
    )


def list_enrollments(*, user_id: int, tenant_id: int) -> list[TwoFactorEnrollment]:
    """List all 2FA enrollments for a user."""
    rows = list_entities_for_tenant("twofa_enrollments", tenant_id)
    return [
        TwoFactorEnrollment(
            enrollment_id=r["id"],
            user_id=r["user_id"],
            method=r["method"],
            is_active=bool(r.get("is_active")),
            tenant_id=tenant_id,
        )
        for r in rows
        if r.get("user_id") == user_id
    ]
