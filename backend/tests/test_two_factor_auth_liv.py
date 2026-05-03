"""Phase LIV — 2FA SMS + TOTP tests (22 tests)."""
from __future__ import annotations

from unittest.mock import MagicMock, call, patch

import pytest

MODULE = "app.modules.two_factor_auth.service"


# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------


def _make_enrollment(
    id_=1, user_id=100, method="totp", is_active=True, status="active", secret="aabb"
):
    return {
        "id": id_,
        "user_id": user_id,
        "method": method,
        "is_active": is_active,
        "status": status,
        "secret": secret,
    }


def _make_challenge(id_=10, user_id=100, method="sms", code="123456", status="pending"):
    return {
        "id": id_,
        "user_id": user_id,
        "method": method,
        "code": code,
        "status": status,
    }


# ---------------------------------------------------------------------------
# 1. enroll_2fa — happy path TOTP
# ---------------------------------------------------------------------------


def test_enroll_totp_creates_entity():
    with (
        patch(f"{MODULE}.create_entity_for_tenant") as mock_create,
        patch(f"{MODULE}.EventPublisher") as mock_pub,
    ):
        mock_create.return_value = {"id": 5}
        from app.modules.two_factor_auth.service import enroll_2fa

        result = enroll_2fa(user_id=1, method="totp", tenant_id=42)

        assert result.enrollment_id == 5
        assert result.method == "totp"
        assert not result.is_active
        mock_create.assert_called_once()
        args = mock_create.call_args[0]
        assert args[0] == "twofa_enrollments"
        assert args[2] == 42
        assert args[1]["method"] == "totp"
        assert len(args[1]["secret"]) > 0  # TOTP secret generated
        mock_pub.publish.assert_called_once()
        assert mock_pub.publish.call_args[1]["event_type"] == "twofa.enrollment_started"


# ---------------------------------------------------------------------------
# 2. enroll_2fa — happy path SMS
# ---------------------------------------------------------------------------


def test_enroll_sms_creates_entity_no_secret():
    with (
        patch(f"{MODULE}.create_entity_for_tenant") as mock_create,
        patch(f"{MODULE}.EventPublisher"),
    ):
        mock_create.return_value = {"id": 6}
        from app.modules.two_factor_auth.service import enroll_2fa

        result = enroll_2fa(user_id=2, method="sms", tenant_id=10)

        assert result.enrollment_id == 6
        assert result.method == "sms"
        payload = mock_create.call_args[0][1]
        assert payload["secret"] == ""  # SMS has no TOTP secret


# ---------------------------------------------------------------------------
# 3. enroll_2fa — invalid method
# ---------------------------------------------------------------------------


def test_enroll_invalid_method():
    from app.modules.two_factor_auth.service import TwoFactorError, enroll_2fa

    with pytest.raises(TwoFactorError, match="invalid method"):
        enroll_2fa(user_id=1, method="carrier_pigeon", tenant_id=1)


# ---------------------------------------------------------------------------
# 4. enroll_2fa — invalid user_id
# ---------------------------------------------------------------------------


def test_enroll_invalid_user_id():
    from app.modules.two_factor_auth.service import TwoFactorError, enroll_2fa

    with pytest.raises(TwoFactorError, match="user_id"):
        enroll_2fa(user_id=0, method="sms", tenant_id=1)


# ---------------------------------------------------------------------------
# 5. activate_enrollment — happy path
# ---------------------------------------------------------------------------


def test_activate_enrollment_sets_active():
    inactive = _make_enrollment(is_active=False, status="pending_verification")
    with (
        patch(f"{MODULE}.list_entities_for_tenant", return_value=[inactive]),
        patch(f"{MODULE}.update_entity_for_tenant") as mock_update,
        patch(f"{MODULE}.EventPublisher") as mock_pub,
    ):
        from app.modules.two_factor_auth.service import activate_enrollment

        result = activate_enrollment(enrollment_id=1, tenant_id=42)

        assert result.is_active is True
        mock_update.assert_called_once()
        update_payload = mock_update.call_args[0][2]
        assert update_payload["is_active"] is True
        mock_pub.publish.assert_called_once()
        assert mock_pub.publish.call_args[1]["event_type"] == "twofa.enrollment_activated"


# ---------------------------------------------------------------------------
# 6. activate_enrollment — already active
# ---------------------------------------------------------------------------


def test_activate_enrollment_already_active_raises():
    active = _make_enrollment(is_active=True)
    with patch(f"{MODULE}.list_entities_for_tenant", return_value=[active]):
        from app.modules.two_factor_auth.service import TwoFactorError, activate_enrollment

        with pytest.raises(TwoFactorError, match="already active"):
            activate_enrollment(enrollment_id=1, tenant_id=42)


# ---------------------------------------------------------------------------
# 7. activate_enrollment — not found
# ---------------------------------------------------------------------------


def test_activate_enrollment_not_found():
    with patch(f"{MODULE}.list_entities_for_tenant", return_value=[]):
        from app.modules.two_factor_auth.service import TwoFactorError, activate_enrollment

        with pytest.raises(TwoFactorError, match="not found"):
            activate_enrollment(enrollment_id=99, tenant_id=42)


# ---------------------------------------------------------------------------
# 8. revoke_enrollment — happy path
# ---------------------------------------------------------------------------


def test_revoke_enrollment_deactivates():
    active = _make_enrollment(is_active=True)
    with (
        patch(f"{MODULE}.list_entities_for_tenant", return_value=[active]),
        patch(f"{MODULE}.update_entity_for_tenant") as mock_update,
    ):
        from app.modules.two_factor_auth.service import revoke_enrollment

        result = revoke_enrollment(enrollment_id=1, tenant_id=42)

        assert result.is_active is False
        update_payload = mock_update.call_args[0][2]
        assert update_payload["is_active"] is False
        assert update_payload["status"] == "revoked"


# ---------------------------------------------------------------------------
# 9. revoke_enrollment — not active
# ---------------------------------------------------------------------------


def test_revoke_enrollment_not_active_raises():
    inactive = _make_enrollment(is_active=False)
    with patch(f"{MODULE}.list_entities_for_tenant", return_value=[inactive]):
        from app.modules.two_factor_auth.service import TwoFactorError, revoke_enrollment

        with pytest.raises(TwoFactorError, match="not active"):
            revoke_enrollment(enrollment_id=1, tenant_id=42)


# ---------------------------------------------------------------------------
# 10. create_challenge — SMS
# ---------------------------------------------------------------------------


def test_create_challenge_sms():
    with (
        patch(f"{MODULE}.create_entity_for_tenant") as mock_create,
    ):
        mock_create.return_value = {"id": 10}
        from app.modules.two_factor_auth.service import create_challenge

        result = create_challenge(user_id=1, method="sms", tenant_id=5)

        assert result.challenge_id == 10
        assert result.method == "sms"
        assert result.status == "pending"
        payload = mock_create.call_args[0][1]
        # SMS code generated automatically — 6 digits
        assert len(payload["code"]) == 6
        assert payload["code"].isdigit()


# ---------------------------------------------------------------------------
# 11. create_challenge — TOTP (no code stored)
# ---------------------------------------------------------------------------


def test_create_challenge_totp_no_code():
    with patch(f"{MODULE}.create_entity_for_tenant") as mock_create:
        mock_create.return_value = {"id": 11}
        from app.modules.two_factor_auth.service import create_challenge

        result = create_challenge(user_id=2, method="totp", tenant_id=5)

        assert result.method == "totp"
        payload = mock_create.call_args[0][1]
        assert payload["code"] == ""  # no stored code for TOTP


# ---------------------------------------------------------------------------
# 12. create_challenge — invalid method
# ---------------------------------------------------------------------------


def test_create_challenge_invalid_method():
    from app.modules.two_factor_auth.service import TwoFactorError, create_challenge

    with pytest.raises(TwoFactorError, match="invalid method"):
        create_challenge(user_id=1, method="email", tenant_id=5)


# ---------------------------------------------------------------------------
# 13. verify_sms_challenge — correct code
# ---------------------------------------------------------------------------


def test_verify_sms_correct_code():
    challenge = _make_challenge(code="654321")
    with (
        patch(f"{MODULE}.list_entities_for_tenant", return_value=[challenge]),
        patch(f"{MODULE}.update_entity_for_tenant") as mock_update,
        patch(f"{MODULE}.EventPublisher") as mock_pub,
    ):
        from app.modules.two_factor_auth.service import verify_sms_challenge

        result = verify_sms_challenge(challenge_id=10, code="654321", tenant_id=5)

        assert result.status == "verified"
        update_payload = mock_update.call_args[0][2]
        assert update_payload["status"] == "verified"
        mock_pub.publish.assert_called_once()
        assert mock_pub.publish.call_args[1]["event_type"] == "twofa.verified"


# ---------------------------------------------------------------------------
# 14. verify_sms_challenge — wrong code
# ---------------------------------------------------------------------------


def test_verify_sms_wrong_code_raises():
    challenge = _make_challenge(code="111111")
    with (
        patch(f"{MODULE}.list_entities_for_tenant", return_value=[challenge]),
        patch(f"{MODULE}.update_entity_for_tenant"),
        patch(f"{MODULE}.EventPublisher") as mock_pub,
    ):
        from app.modules.two_factor_auth.service import TwoFactorError, verify_sms_challenge

        with pytest.raises(TwoFactorError, match="invalid SMS code"):
            verify_sms_challenge(challenge_id=10, code="999999", tenant_id=5)

        mock_pub.publish.assert_called_once()
        assert mock_pub.publish.call_args[1]["event_type"] == "twofa.verification_failed"


# ---------------------------------------------------------------------------
# 15. verify_sms_challenge — already verified
# ---------------------------------------------------------------------------


def test_verify_sms_already_verified_raises():
    challenge = _make_challenge(status="verified")
    with patch(f"{MODULE}.list_entities_for_tenant", return_value=[challenge]):
        from app.modules.two_factor_auth.service import TwoFactorError, verify_sms_challenge

        with pytest.raises(TwoFactorError, match="already in status"):
            verify_sms_challenge(challenge_id=10, code="123456", tenant_id=5)


# ---------------------------------------------------------------------------
# 16. verify_totp_challenge — correct code (uses real _compute_totp)
# ---------------------------------------------------------------------------


def test_verify_totp_correct_code():
    import time

    from app.modules.two_factor_auth.service import _compute_totp

    secret = "deadbeefdeadbeefdeadbeefdeadbeefdeadbeef"
    code = _compute_totp(secret)
    challenge = _make_challenge(id_=20, method="totp", code="", status="pending")
    with (
        patch(f"{MODULE}.list_entities_for_tenant", return_value=[challenge]),
        patch(f"{MODULE}.update_entity_for_tenant") as mock_update,
        patch(f"{MODULE}.EventPublisher") as mock_pub,
    ):
        from app.modules.two_factor_auth.service import verify_totp_challenge

        result = verify_totp_challenge(
            challenge_id=20, totp_code=code, secret_hex=secret, tenant_id=5
        )

        assert result.status == "verified"
        mock_pub.publish.assert_called_once()
        assert mock_pub.publish.call_args[1]["event_type"] == "twofa.verified"


# ---------------------------------------------------------------------------
# 17. verify_totp_challenge — wrong code
# ---------------------------------------------------------------------------


def test_verify_totp_wrong_code_raises():
    challenge = _make_challenge(id_=21, method="totp", code="", status="pending")
    with (
        patch(f"{MODULE}.list_entities_for_tenant", return_value=[challenge]),
        patch(f"{MODULE}.update_entity_for_tenant"),
        patch(f"{MODULE}.EventPublisher") as mock_pub,
    ):
        from app.modules.two_factor_auth.service import TwoFactorError, verify_totp_challenge

        with pytest.raises(TwoFactorError, match="invalid TOTP code"):
            verify_totp_challenge(
                challenge_id=21,
                totp_code="000000",
                secret_hex="deadbeefdeadbeefdeadbeefdeadbeefdeadbeef",
                tenant_id=5,
            )

        assert mock_pub.publish.call_args[1]["event_type"] == "twofa.verification_failed"


# ---------------------------------------------------------------------------
# 18. verify_totp_challenge — missing secret
# ---------------------------------------------------------------------------


def test_verify_totp_missing_secret_raises():
    from app.modules.two_factor_auth.service import TwoFactorError, verify_totp_challenge

    with pytest.raises(TwoFactorError, match="secret_hex"):
        verify_totp_challenge(challenge_id=1, totp_code="123456", secret_hex="", tenant_id=5)


# ---------------------------------------------------------------------------
# 19. expire_challenge
# ---------------------------------------------------------------------------


def test_expire_challenge_sets_status():
    challenge = _make_challenge(status="pending")
    with (
        patch(f"{MODULE}.list_entities_for_tenant", return_value=[challenge]),
        patch(f"{MODULE}.update_entity_for_tenant") as mock_update,
    ):
        from app.modules.two_factor_auth.service import expire_challenge

        result = expire_challenge(challenge_id=10, tenant_id=5)

        assert result.status == "expired"
        update_payload = mock_update.call_args[0][2]
        assert update_payload["status"] == "expired"


# ---------------------------------------------------------------------------
# 20. expire_challenge — not pending
# ---------------------------------------------------------------------------


def test_expire_non_pending_raises():
    challenge = _make_challenge(status="verified")
    with patch(f"{MODULE}.list_entities_for_tenant", return_value=[challenge]):
        from app.modules.two_factor_auth.service import TwoFactorError, expire_challenge

        with pytest.raises(TwoFactorError, match="only pending"):
            expire_challenge(challenge_id=10, tenant_id=5)


# ---------------------------------------------------------------------------
# 21. list_enrollments — filters by user_id
# ---------------------------------------------------------------------------


def test_list_enrollments_filters_by_user():
    enrollments = [
        _make_enrollment(id_=1, user_id=10),
        _make_enrollment(id_=2, user_id=20),
        _make_enrollment(id_=3, user_id=10),
    ]
    with patch(f"{MODULE}.list_entities_for_tenant", return_value=enrollments):
        from app.modules.two_factor_auth.service import list_enrollments

        result = list_enrollments(user_id=10, tenant_id=42)

        assert len(result) == 2
        assert all(r.user_id == 10 for r in result)


# ---------------------------------------------------------------------------
# 22. backup_code generation produces distinct codes
# ---------------------------------------------------------------------------


def test_generate_backup_codes_distinct():
    from app.modules.two_factor_auth.service import _generate_backup_codes

    codes = _generate_backup_codes(8)
    assert len(codes) == 8
    assert len(set(codes)) == 8  # all unique
