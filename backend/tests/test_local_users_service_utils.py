"""Tests for pure utility functions in app.modules.auth.local_users_service.

These functions have no DB / Redis dependencies and are always reachable in the
unit-test environment (DATABASE_URL is absent → in-memory mode is active).
"""

import pytest
from fastapi import HTTPException

from app.modules.auth.local_users_service import (
    _hash_password,
    _require_tenant_id,
    _row_to_dict,
    _verify_password,
    LocalUserStore,
)


# ---------------------------------------------------------------------------
# _require_tenant_id
# ---------------------------------------------------------------------------

class TestRequireTenantId:
    def test_valid_int(self):
        assert _require_tenant_id(1, operation="test") == 1

    def test_valid_string_int(self):
        assert _require_tenant_id("42", operation="test") == 42

    def test_large_value(self):
        assert _require_tenant_id(99999, operation="test") == 99999

    def test_none_raises_400(self):
        with pytest.raises(HTTPException) as exc_info:
            _require_tenant_id(None, operation="test_op")
        assert exc_info.value.status_code == 400

    def test_non_numeric_string_raises_400(self):
        with pytest.raises(HTTPException) as exc_info:
            _require_tenant_id("abc", operation="test_op")
        assert exc_info.value.status_code == 400

    def test_zero_raises_400(self):
        with pytest.raises(HTTPException) as exc_info:
            _require_tenant_id(0, operation="test_op")
        assert exc_info.value.status_code == 400

    def test_negative_raises_400(self):
        with pytest.raises(HTTPException) as exc_info:
            _require_tenant_id(-5, operation="test_op")
        assert exc_info.value.status_code == 400

    def test_negative_string_raises_400(self):
        with pytest.raises(HTTPException) as exc_info:
            _require_tenant_id("-1", operation="op")
        assert exc_info.value.status_code == 400

    def test_empty_string_raises_400(self):
        with pytest.raises(HTTPException) as exc_info:
            _require_tenant_id("", operation="op")
        assert exc_info.value.status_code == 400

    def test_operation_in_detail(self):
        with pytest.raises(HTTPException) as exc_info:
            _require_tenant_id(None, operation="my_operation")
        assert "my_operation" in exc_info.value.detail


# ---------------------------------------------------------------------------
# _hash_password / _verify_password
# ---------------------------------------------------------------------------

class TestPasswordHashing:
    def test_round_trip(self):
        h = _hash_password("SuperSecret123!")
        assert _verify_password("SuperSecret123!", h) is True

    def test_wrong_password_fails(self):
        h = _hash_password("correct_password")
        assert _verify_password("wrong_password", h) is False

    def test_hash_format(self):
        h = _hash_password("test")
        parts = h.split("$")
        assert len(parts) == 4
        assert parts[0] == "pbkdf2_sha256"

    def test_unique_hashes(self):
        h1 = _hash_password("password")
        h2 = _hash_password("password")
        # Different salts → different hashes
        assert h1 != h2

    def test_verify_malformed_encoded_returns_false(self):
        assert _verify_password("pw", "malformed") is False

    def test_verify_wrong_algorithm_returns_false(self):
        assert _verify_password("pw", "sha256$1000$salt$digest") is False

    def test_verify_non_numeric_iterations_returns_false(self):
        # 4 parts, correct algorithm, but iterations is not a number
        assert _verify_password("pw", "pbkdf2_sha256$NaN$somesalt$somedigest") is False

    def test_empty_password_round_trip(self):
        h = _hash_password("")
        assert _verify_password("", h) is True

    def test_unicode_password_round_trip(self):
        h = _hash_password("пароль_テスト_🔐")
        assert _verify_password("пароль_テスト_🔐", h) is True


# ---------------------------------------------------------------------------
# _row_to_dict
# ---------------------------------------------------------------------------

# Columns: user_id, tenant_id, login, password_hash, display_name, roles,
#          default_language, email, account_scope, is_platform_user,
#          force_password_change, auth_source, status
_BASE_ROW = (
    "u-1",   # 0  user_id
    1,       # 1  tenant_id
    "alice", # 2  login
    "hash",  # 3  password_hash
    "Alice", # 4  display_name
    ["admin", "teacher"],  # 5  roles (list)
    "en",    # 6  default_language
    "a@b.com",  # 7  email
    None,    # 8  account_scope
    False,   # 9  is_platform_user
    False,   # 10 force_password_change
    "local", # 11 auth_source
    "active",# 12 status
)


class TestRowToDict:
    def test_roles_as_list(self):
        result = _row_to_dict(_BASE_ROW)
        assert result["roles"] == ["admin", "teacher"]

    def test_roles_as_json_string(self):
        row = list(_BASE_ROW)
        row[5] = '["student", "tutor"]'
        result = _row_to_dict(tuple(row))
        assert result["roles"] == ["student", "tutor"]

    def test_roles_as_invalid_json_string(self):
        row = list(_BASE_ROW)
        row[5] = "not-valid-json"
        result = _row_to_dict(tuple(row))
        assert result["roles"] == ["student"]

    def test_roles_as_none(self):
        row = list(_BASE_ROW)
        row[5] = None
        result = _row_to_dict(tuple(row))
        assert result["roles"] == ["student"]

    def test_basic_fields_mapped(self):
        result = _row_to_dict(_BASE_ROW)
        assert result["user_id"] == "u-1"
        assert result["tenant_id"] == 1
        assert result["login"] == "alice"
        assert result["display_name"] == "Alice"
        assert result["email"] == "a@b.com"
        assert result["auth_source"] == "local"
        assert result["status"] == "active"

    def test_null_password_hash_defaults_empty_string(self):
        row = list(_BASE_ROW)
        row[3] = None
        result = _row_to_dict(tuple(row))
        assert result["password_hash"] == ""

    def test_null_display_name_defaults_empty_string(self):
        row = list(_BASE_ROW)
        row[4] = None
        result = _row_to_dict(tuple(row))
        assert result["display_name"] == ""

    def test_null_language_defaults_ru(self):
        row = list(_BASE_ROW)
        row[6] = None
        result = _row_to_dict(tuple(row))
        assert result["default_language"] == "ru"

    def test_null_auth_source_defaults_local(self):
        row = list(_BASE_ROW)
        row[11] = None
        result = _row_to_dict(tuple(row))
        assert result["auth_source"] == "local"

    def test_null_status_defaults_active(self):
        row = list(_BASE_ROW)
        row[12] = None
        result = _row_to_dict(tuple(row))
        assert result["status"] == "active"

    def test_is_platform_user_cast_to_bool(self):
        row = list(_BASE_ROW)
        row[9] = 1  # truthy int
        result = _row_to_dict(tuple(row))
        assert result["is_platform_user"] is True


# ---------------------------------------------------------------------------
# LocalUserStore._normalize_roles
# ---------------------------------------------------------------------------

class TestNormalizeRoles:
    def setup_method(self):
        self.store = LocalUserStore()

    def test_returns_stripped_roles(self):
        assert self.store._normalize_roles(["admin ", " teacher"]) == ["admin", "teacher"]

    def test_empty_list_returns_student(self):
        assert self.store._normalize_roles([]) == ["student"]

    def test_all_blank_roles_returns_student(self):
        assert self.store._normalize_roles(["  ", ""]) == ["student"]

    def test_filters_empty_strings(self):
        result = self.store._normalize_roles(["admin", "", "teacher"])
        assert result == ["admin", "teacher"]


# ---------------------------------------------------------------------------
# LocalUserStore._public_user
# ---------------------------------------------------------------------------

class TestPublicUser:
    def setup_method(self):
        self.store = LocalUserStore()

    def _base_item(self, **overrides):
        item = {
            "user_id": "u-1",
            "login": "alice",
            "display_name": "Alice",
            "roles": ["student"],
            "default_language": "en",
            "tenant_id": 1,
            "auth_source": "local",
            "email": None,
            "account_scope": None,
            "is_platform_user": False,
            "force_password_change": False,
        }
        item.update(overrides)
        return item

    def test_basic_projection(self):
        result = self.store._public_user(self._base_item())
        assert result["user_id"] == "u-1"
        assert result["login"] == "alice"
        assert result["sync_with_ad"] is False

    def test_email_included_when_present(self):
        result = self.store._public_user(self._base_item(email="a@b.com"))
        assert result["email"] == "a@b.com"

    def test_email_excluded_when_empty(self):
        result = self.store._public_user(self._base_item(email=""))
        assert "email" not in result

    def test_account_scope_included_when_present(self):
        result = self.store._public_user(self._base_item(account_scope="premium"))
        assert result["account_scope"] == "premium"

    def test_account_scope_excluded_when_none(self):
        result = self.store._public_user(self._base_item(account_scope=None))
        assert "account_scope" not in result

    def test_is_platform_user_included_when_true(self):
        result = self.store._public_user(self._base_item(is_platform_user=True))
        assert result["is_platform_user"] is True

    def test_is_platform_user_excluded_when_false(self):
        result = self.store._public_user(self._base_item(is_platform_user=False))
        assert "is_platform_user" not in result

    def test_force_password_change_included_when_true(self):
        result = self.store._public_user(self._base_item(force_password_change=True))
        assert result["force_password_change"] is True
