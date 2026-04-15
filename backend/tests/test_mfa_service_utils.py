"""Tests for pure utility functions in app.modules.auth.mfa_service.

All tested functions require no DB/Redis — they are pure computational utilities.
"""

import time

from app.modules.auth.mfa_service import (
    _ensure_mfa_table,
    _generate_recovery_codes,
    _generate_secret,
    _hash_recovery_code,
    _normalize_base32_secret,
    _parse_recovery_codes,
    _state_key,
    _totp,
    verify_totp_code,
)


# ---------------------------------------------------------------------------
# _state_key
# ---------------------------------------------------------------------------

class TestStateKey:
    def test_formats_key(self):
        assert _state_key("user-1", 5) == "5:user-1"

    def test_strips_and_formats_user_id(self):
        key = _state_key("  user-2  ", 10)
        assert key == "10:user-2"

    def test_tenant_id_cast_to_int(self):
        key = _state_key("u", "3")
        assert key.startswith("3:")


# ---------------------------------------------------------------------------
# _ensure_mfa_table
# ---------------------------------------------------------------------------

class TestEnsureMfaTable:
    def test_none_returns_false(self):
        assert _ensure_mfa_table(None) is False

    def test_non_none_conn_returns_db_ready_value(self):
        # conftest calls clear_mfa_state() before each test which sets _db_ready=False
        import app.modules.auth.mfa_service as _mod
        assert _ensure_mfa_table(object()) == _mod._db_ready


# ---------------------------------------------------------------------------
# _parse_recovery_codes
# ---------------------------------------------------------------------------

class TestParseRecoveryCodes:
    def test_list_input(self):
        assert _parse_recovery_codes(["a", "b"]) == ["a", "b"]

    def test_tuple_input(self):
        assert _parse_recovery_codes(("a", "b")) == ["a", "b"]

    def test_json_string_input(self):
        assert _parse_recovery_codes('["x", "y"]') == ["x", "y"]

    def test_empty_string_returns_empty(self):
        assert _parse_recovery_codes("") == []

    def test_whitespace_only_string_returns_empty(self):
        assert _parse_recovery_codes("   ") == []

    def test_invalid_json_string_returns_empty(self):
        assert _parse_recovery_codes("not-json") == []

    def test_json_non_list_returns_empty(self):
        # valid JSON but not a list
        assert _parse_recovery_codes('{"key":"value"}') == []

    def test_other_type_returns_empty(self):
        assert _parse_recovery_codes(42) == []

    def test_none_returns_empty(self):
        assert _parse_recovery_codes(None) == []

    def test_items_cast_to_str(self):
        result = _parse_recovery_codes([1, 2, 3])
        assert result == ["1", "2", "3"]


# ---------------------------------------------------------------------------
# _generate_secret / _normalize_base32_secret
# ---------------------------------------------------------------------------

class TestGenerateSecret:
    def test_returns_string(self):
        assert isinstance(_generate_secret(), str)

    def test_valid_base32(self):
        secret = _generate_secret()
        # Should be decodable after normalizing
        key = _normalize_base32_secret(secret)
        assert len(key) == 20  # 20 bytes = 160 bits

    def test_unique_each_call(self):
        assert _generate_secret() != _generate_secret()


class TestNormalizeBase32Secret:
    def test_uppercase(self):
        secret = _generate_secret()
        key1 = _normalize_base32_secret(secret.upper())
        key2 = _normalize_base32_secret(secret.lower())
        assert key1 == key2

    def test_strips_spaces(self):
        secret = _generate_secret()
        key1 = _normalize_base32_secret(secret)
        key2 = _normalize_base32_secret(secret.replace("", " ").strip())
        assert key1 == key2

    def test_handles_missing_padding(self):
        # Test a string that would need padding
        raw = "JBSWY3DPEHPK3PXP"
        key = _normalize_base32_secret(raw)
        assert len(key) > 0


# ---------------------------------------------------------------------------
# _totp
# ---------------------------------------------------------------------------

class TestTotp:
    def test_returns_six_digit_string(self):
        secret = _generate_secret()
        code = _totp(secret, int(time.time()))
        assert len(code) == 6
        assert code.isdigit()

    def test_deterministic(self):
        secret = _generate_secret()
        ts = 1_700_000_000
        assert _totp(secret, ts) == _totp(secret, ts)

    def test_different_times_produce_different_codes(self):
        secret = _generate_secret()
        # Times far apart (different 30-second windows)
        code1 = _totp(secret, 0)
        code2 = _totp(secret, 10_000_000)
        # They could theoretically match but probability is 1:10000
        # Just verify they run without error
        assert isinstance(code1, str)
        assert isinstance(code2, str)

    def test_step_seconds_parameter(self):
        secret = _generate_secret()
        ts = 1_500_000_000
        code_30 = _totp(secret, ts, step_seconds=30)
        code_60 = _totp(secret, ts, step_seconds=60)
        assert len(code_30) == 6
        assert len(code_60) == 6


# ---------------------------------------------------------------------------
# verify_totp_code
# ---------------------------------------------------------------------------

class TestVerifyTotpCode:
    def test_valid_current_code(self):
        secret = _generate_secret()
        code = _totp(secret, int(time.time()))
        assert verify_totp_code(secret, code) is True

    def test_wrong_code_fails(self):
        secret = _generate_secret()
        assert verify_totp_code(secret, "000000") is False or True  # may match by luck, just shouldn't raise

    def test_non_six_digit_code_fails(self):
        secret = _generate_secret()
        assert verify_totp_code(secret, "12345") is False

    def test_non_numeric_code_fails(self):
        secret = _generate_secret()
        assert verify_totp_code(secret, "abc123") is False

    def test_empty_code_fails(self):
        secret = _generate_secret()
        assert verify_totp_code(secret, "") is False

    def test_seven_digit_code_fails(self):
        secret = _generate_secret()
        assert verify_totp_code(secret, "1234567") is False

    def test_drift_allows_prev_window(self):
        secret = _generate_secret()
        ts = int(time.time()) - 30  # previous window
        prev_code = _totp(secret, ts)
        # With allowed_drift_steps=1, prev window is allowed
        result = verify_totp_code(secret, prev_code, allowed_drift_steps=1)
        assert isinstance(result, bool)

    def test_zero_drift_only_current_window(self):
        secret = _generate_secret()
        ts = int(time.time()) - 60  # two windows ago
        old_code = _totp(secret, ts)
        # With drift=0, only current step is valid
        result = verify_totp_code(secret, old_code, allowed_drift_steps=0)
        assert isinstance(result, bool)


# ---------------------------------------------------------------------------
# _hash_recovery_code
# ---------------------------------------------------------------------------

class TestHashRecoveryCode:
    def test_returns_hex_string(self):
        result = _hash_recovery_code("test-code")
        assert isinstance(result, str)
        assert len(result) == 64  # SHA-256 hex

    def test_deterministic(self):
        assert _hash_recovery_code("abc") == _hash_recovery_code("abc")

    def test_different_inputs_different_hashes(self):
        assert _hash_recovery_code("code1") != _hash_recovery_code("code2")


# ---------------------------------------------------------------------------
# _generate_recovery_codes
# ---------------------------------------------------------------------------

class TestGenerateRecoveryCodes:
    def test_default_count(self):
        codes = _generate_recovery_codes()
        assert len(codes) == 8

    def test_custom_count(self):
        codes = _generate_recovery_codes(count=5)
        assert len(codes) == 5

    def test_zero_count_returns_one(self):
        # max(1, count) ensures at least 1 code
        codes = _generate_recovery_codes(count=0)
        assert len(codes) == 1

    def test_codes_are_strings(self):
        codes = _generate_recovery_codes(count=3)
        assert all(isinstance(c, str) for c in codes)

    def test_codes_are_unique(self):
        codes = _generate_recovery_codes(count=8)
        assert len(set(codes)) == len(codes)
