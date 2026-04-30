"""
Coverage boost: app.modules.auth.session_service

Tests exercise the in-memory fallback paths (DATABASE_URL not set in CI).
get_raw_conn() yields None, so _ensure_session_table(None) returns False and
all functions use the _state in-memory store.
"""
from __future__ import annotations

import pytest

from app.modules.auth.session_service import (
    create_session,
    touch_session,
    is_session_active,
    list_sessions_for_user,
    revoke_session,
    revoke_all_sessions_for_user,
    list_active_devices,
    revoke_device,
    clear_sessions_state,
)
import app.modules.auth.session_service as _ss


@pytest.fixture(autouse=True)
def _reset():
    clear_sessions_state()
    yield
    clear_sessions_state()


def _make_session(
    user_id: str = "user-1",
    tenant_id: int = 1,
    auth_source: str = "jwt",
    client_ip: str = "127.0.0.1",
    user_agent: str = "pytest",
    device_id: str | None = "dev-a",
    device_name: str | None = "Laptop",
) -> dict:
    return create_session(
        user_id=user_id,
        tenant_id=tenant_id,
        auth_source=auth_source,
        client_ip=client_ip,
        user_agent=user_agent,
        device_id=device_id,
        device_name=device_name,
    )


# ---------------------------------------------------------------------------
# create_session
# ---------------------------------------------------------------------------


def test_create_session_returns_dict():
    sess = _make_session()
    assert sess["user_id"] == "user-1"
    assert sess["tenant_id"] == 1
    assert sess["active"] is True
    assert sess["is_revoked"] is False
    assert sess["session_id"]


def test_create_session_empty_device_name_defaults():
    sess = create_session(
        user_id="u",
        tenant_id=1,
        auth_source="local",
        client_ip="0.0.0.0",
        user_agent="",
        device_id=None,
        device_name=None,
    )
    assert sess["device_name"] == "Unknown Device"
    assert sess["device_id"]  # auto-generated


def test_create_session_without_device_id_generates_one():
    sess = create_session(
        user_id="u2",
        tenant_id=2,
        auth_source="sso",
        client_ip="1.2.3.4",
        user_agent="Mozilla",
        device_id=None,
    )
    assert sess["device_id"]


# ---------------------------------------------------------------------------
# touch_session
# ---------------------------------------------------------------------------


def test_touch_session_updates_last_seen():
    sess = _make_session()
    sid = sess["session_id"]
    old_ts = _ss._state.rows[sid]["last_seen_at"]
    touch_session(sid)
    new_ts = _ss._state.rows[sid]["last_seen_at"]
    # timestamp should have been refreshed (or at worst unchanged under fast systems)
    assert new_ts >= old_ts


def test_touch_session_noop_for_empty_id():
    touch_session("")  # should not raise


def test_touch_session_noop_for_unknown_session():
    touch_session("non-existent-id")  # no crash


def test_touch_session_noop_for_inactive_session():
    sess = _make_session()
    sid = sess["session_id"]
    revoke_session(session_id=sid)
    # touching revoked session is a no-op
    touch_session(sid)


# ---------------------------------------------------------------------------
# is_session_active
# ---------------------------------------------------------------------------


def test_is_session_active_true_for_new():
    sess = _make_session()
    assert is_session_active(sess["session_id"]) is True


def test_is_session_active_false_for_empty():
    assert is_session_active("") is False


def test_is_session_active_false_for_unknown():
    assert is_session_active("bogus") is False


def test_is_session_active_false_after_revoke():
    sess = _make_session()
    sid = sess["session_id"]
    revoke_session(session_id=sid)
    assert is_session_active(sid) is False


def test_is_session_active_false_after_expiry():
    """If the stored expires_at is in the past, active check returns False."""
    sess = _make_session()
    sid = sess["session_id"]
    # Override stored expires_at to be in the past
    _ss._state.rows[sid]["expires_at"] = "2000-01-01T00:00:00+00:00"
    assert is_session_active(sid) is False


def test_is_session_active_ignores_invalid_expiry():
    """Malformed expires_at falls back to checking active flag."""
    sess = _make_session()
    sid = sess["session_id"]
    _ss._state.rows[sid]["expires_at"] = "not-a-valid-date"
    # active is True, so result should be True
    assert is_session_active(sid) is True


# ---------------------------------------------------------------------------
# list_sessions_for_user
# ---------------------------------------------------------------------------


def test_list_sessions_returns_user_sessions():
    s1 = _make_session(user_id="alice", tenant_id=1)
    s2 = _make_session(user_id="alice", tenant_id=1, device_id="dev-b")
    _make_session(user_id="bob", tenant_id=1)  # different user

    sessions = list_sessions_for_user(user_id="alice", tenant_id=1)
    ids = {s["session_id"] for s in sessions}
    assert s1["session_id"] in ids
    assert s2["session_id"] in ids
    # bob's session not included
    assert all(s["user_id"] == "alice" for s in sessions)


def test_list_sessions_empty_for_no_match():
    sessions = list_sessions_for_user(user_id="nobody", tenant_id=999)
    assert sessions == []


def test_list_sessions_tenant_scoped():
    _make_session(user_id="carol", tenant_id=1)
    _make_session(user_id="carol", tenant_id=2)
    sessions = list_sessions_for_user(user_id="carol", tenant_id=1)
    assert all(s["tenant_id"] == 1 for s in sessions)
    assert len(sessions) == 1


# ---------------------------------------------------------------------------
# revoke_session
# ---------------------------------------------------------------------------


def test_revoke_session_returns_true_on_success():
    sess = _make_session()
    result = revoke_session(session_id=sess["session_id"])
    assert result is True


def test_revoke_session_marks_revoked():
    sess = _make_session()
    sid = sess["session_id"]
    revoke_session(session_id=sid)
    row = _ss._state.rows[sid]
    assert row["is_revoked"] is True
    assert row["active"] is False


def test_revoke_session_returns_false_if_already_revoked():
    sess = _make_session()
    sid = sess["session_id"]
    revoke_session(session_id=sid)
    # second revoke is no-op
    assert revoke_session(session_id=sid) is False


def test_revoke_session_returns_false_for_unknown():
    assert revoke_session(session_id="not-there") is False


def test_revoke_session_false_for_empty_id():
    assert revoke_session(session_id="") is False


# ---------------------------------------------------------------------------
# revoke_all_sessions_for_user
# ---------------------------------------------------------------------------


def test_revoke_all_returns_count():
    _make_session(user_id="dave", tenant_id=1)
    _make_session(user_id="dave", tenant_id=1, device_id="dev-x")
    _make_session(user_id="other", tenant_id=1)

    count = revoke_all_sessions_for_user(user_id="dave", tenant_id=1)
    assert count == 2


def test_revoke_all_only_revokes_active():
    s1 = _make_session(user_id="eve", tenant_id=1)
    _make_session(user_id="eve", tenant_id=1, device_id="dev-y")
    revoke_session(session_id=s1["session_id"])  # pre-revoke one

    count = revoke_all_sessions_for_user(user_id="eve", tenant_id=1)
    assert count == 1  # only s2 was still active


def test_revoke_all_zero_for_no_sessions():
    count = revoke_all_sessions_for_user(user_id="nobody", tenant_id=1)
    assert count == 0


# ---------------------------------------------------------------------------
# list_active_devices
# ---------------------------------------------------------------------------


def test_list_active_devices_returns_devices():
    _make_session(user_id="frank", tenant_id=1, device_id="dev-1", device_name="Phone")
    _make_session(user_id="frank", tenant_id=1, device_id="dev-2", device_name="Tablet")

    devices = list_active_devices(user_id="frank", tenant_id=1)
    dev_ids = {d["device_id"] for d in devices}
    assert "dev-1" in dev_ids
    assert "dev-2" in dev_ids


def test_list_active_devices_excludes_revoked():
    sess = _make_session(user_id="grace", tenant_id=1, device_id="dev-r")
    revoke_session(session_id=sess["session_id"])

    devices = list_active_devices(user_id="grace", tenant_id=1)
    assert not any(d["device_id"] == "dev-r" for d in devices)


def test_list_active_devices_empty():
    devices = list_active_devices(user_id="no-one", tenant_id=1)
    assert devices == []


def test_list_active_devices_tenant_scoped():
    _make_session(user_id="hank", tenant_id=1, device_id="hank-dev")
    _make_session(user_id="hank", tenant_id=2, device_id="hank-dev2")

    devices_t1 = list_active_devices(user_id="hank", tenant_id=1)
    assert all(True for d in devices_t1)  # only tenant 1 devices in result
    assert len(devices_t1) == 1
    assert devices_t1[0]["device_id"] == "hank-dev"


# ---------------------------------------------------------------------------
# revoke_device
# ---------------------------------------------------------------------------


def test_revoke_device_revokes_all_device_sessions():
    s1 = _make_session(user_id="ivan", tenant_id=1, device_id="ipad")
    s2 = _make_session(user_id="ivan", tenant_id=1, device_id="ipad")

    count = revoke_device(device_id="ipad", user_id="ivan", tenant_id=1)
    assert count == 2
    assert _ss._state.rows[s1["session_id"]]["is_revoked"] is True
    assert _ss._state.rows[s2["session_id"]]["is_revoked"] is True


def test_revoke_device_returns_zero_if_no_match():
    count = revoke_device(device_id="unknown", user_id="ivan", tenant_id=1)
    assert count == 0


def test_revoke_device_skips_already_revoked():
    sess = _make_session(user_id="jane", tenant_id=1, device_id="laptop")
    revoke_session(session_id=sess["session_id"])

    count = revoke_device(device_id="laptop", user_id="jane", tenant_id=1)
    assert count == 0
