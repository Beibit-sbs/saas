"""Tests for pure utility functions in app.modules.auth.session_service.

These functions have no DB / Redis dependencies.
"""

from datetime import datetime, timezone, timedelta

from app.modules.auth.session_service import (
    _dt_to_iso,
    _ensure_session_table,
    _row_to_session,
)


# ---------------------------------------------------------------------------
# _ensure_session_table
# ---------------------------------------------------------------------------

class TestEnsureSessionTable:
    def test_none_conn_returns_false(self):
        assert _ensure_session_table(None) is False

    def test_non_none_conn_returns_db_ready_value(self):
        # conftest calls clear_sessions_state() before each test, which sets
        # _db_ready = False. So _ensure_session_table returns False for any conn.
        import app.modules.auth.session_service as _mod
        result = _ensure_session_table(object())
        assert result == _mod._db_ready

    def test_truthy_non_none_reflects_db_state(self):
        import app.modules.auth.session_service as _mod
        assert _ensure_session_table("any_string") == _mod._db_ready

    def test_false_is_bool(self):
        result = _ensure_session_table(None)
        assert result is False


# ---------------------------------------------------------------------------
# _dt_to_iso
# ---------------------------------------------------------------------------

class TestDtToIso:
    def test_none_returns_none(self):
        assert _dt_to_iso(None) is None

    def test_naive_datetime_adds_utc_tz(self):
        dt = datetime(2024, 6, 15, 12, 0, 0)  # naive, no tzinfo
        result = _dt_to_iso(dt)
        assert result is not None
        assert "2024-06-15" in result
        assert "+00:00" in result or "UTC" in result or "Z" in result.upper() or result.endswith("+00:00")

    def test_utc_aware_datetime_passes_through(self):
        dt = datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        result = _dt_to_iso(dt)
        assert result is not None
        assert "2024-01-01" in result

    def test_iso_string_returned_as_is(self):
        value = "2024-06-15T12:00:00+00:00"
        assert _dt_to_iso(value) == value

    def test_empty_string_returns_none(self):
        assert _dt_to_iso("") is None

    def test_whitespace_string_returns_none(self):
        assert _dt_to_iso("   ") is None

    def test_non_empty_non_datetime_string_returned(self):
        result = _dt_to_iso("some-date-string")
        assert result == "some-date-string"

    def test_non_utc_aware_datetime_converted_to_utc(self):
        tz_plus5 = timezone(timedelta(hours=5))
        dt = datetime(2024, 1, 1, 5, 0, 0, tzinfo=tz_plus5)  # noon UTC
        result = _dt_to_iso(dt)
        assert result is not None
        # After conversion, time should represent 00:00 UTC
        assert "2024-01-01" in result
        assert "+00:00" in result


# ---------------------------------------------------------------------------
# _row_to_session
# ---------------------------------------------------------------------------

# Match order of columns in the session table:
# session_id, user_id, tenant_id, auth_source, client_ip, user_agent,
# device_id, device_name, created_at, last_seen_at, expires_at,
# revoked_at, revoked
_SAMPLE_ROW = (
    "sess-uuid-001",         # 0  session_id
    "user-001",              # 1  user_id
    7,                       # 2  tenant_id
    "local",                 # 3  auth_source
    "127.0.0.1",             # 4  client_ip
    "Mozilla/5.0",           # 5  user_agent
    "dev-001",               # 6  device_id
    "Laptop",                # 7  device_name
    datetime(2024, 1, 1, tzinfo=timezone.utc),   # 8  created_at
    datetime(2024, 6, 1, tzinfo=timezone.utc),   # 9  last_seen_at
    datetime(2025, 1, 1, tzinfo=timezone.utc),   # 10 expires_at
    None,                    # 11 revoked_at
    False,                   # 12 revoked flag
)


class TestRowToSession:
    def test_session_id_converted_to_str(self):
        result = _row_to_session(_SAMPLE_ROW)
        assert result["session_id"] == "sess-uuid-001"

    def test_user_id_converted_to_str(self):
        result = _row_to_session(_SAMPLE_ROW)
        assert result["user_id"] == "user-001"

    def test_tenant_id_converted_to_int(self):
        result = _row_to_session(_SAMPLE_ROW)
        assert result["tenant_id"] == 7

    def test_auth_source_value(self):
        result = _row_to_session(_SAMPLE_ROW)
        assert result["auth_source"] == "local"

    def test_active_when_not_revoked(self):
        result = _row_to_session(_SAMPLE_ROW)
        assert result["active"] is True
        assert result["is_revoked"] is False

    def test_inactive_when_revoked(self):
        row = list(_SAMPLE_ROW)
        row[12] = True
        result = _row_to_session(tuple(row))
        assert result["active"] is False
        assert result["is_revoked"] is True

    def test_revoked_at_none_preserved(self):
        result = _row_to_session(_SAMPLE_ROW)
        assert result["revoked_at"] is None

    def test_revoked_at_datetime_converted(self):
        row = list(_SAMPLE_ROW)
        row[11] = datetime(2024, 7, 1, tzinfo=timezone.utc)
        result = _row_to_session(tuple(row))
        assert result["revoked_at"] is not None
        assert "2024-07-01" in result["revoked_at"]

    def test_expires_at_converted(self):
        result = _row_to_session(_SAMPLE_ROW)
        assert result["expires_at"] is not None
        assert "2025-01-01" in result["expires_at"]

    def test_created_at_converted(self):
        result = _row_to_session(_SAMPLE_ROW)
        assert result["created_at"] is not None
        assert "2024-01-01" in result["created_at"]

    def test_device_info_fields(self):
        result = _row_to_session(_SAMPLE_ROW)
        assert result["device_id"] == "dev-001"
        assert result["device_name"] == "Laptop"
        assert result["client_ip"] == "127.0.0.1"
        assert result["user_agent"] == "Mozilla/5.0"
