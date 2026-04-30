from __future__ import annotations

from tests.conftest import ADMIN_HEADERS, client


def _reset_brain_state() -> None:
    from app.modules.brain_core.service import brain_core_service

    brain_core_service.__init__()


def test_admin_request_emits_platform_module_activity_signal() -> None:
    from app.modules.brain_core.service import brain_core_service

    _reset_brain_state()

    response = client.get(
        "/api/admin/org/faculty/consistency",
        headers=ADMIN_HEADERS,
    )

    assert response.status_code == 200

    emitted = [
        signal
        for signal in brain_core_service._signals
        if signal.get("event_type") == "platform.module.activity.logged"
    ]
    assert emitted, "expected at least one platform.module.activity.logged signal"

    last_signal = emitted[-1]
    assert last_signal.get("source_module") == "faculty"
    assert last_signal.get("payload", {}).get("path") == "/api/admin/org/faculty/consistency"
    assert last_signal.get("payload", {}).get("method") == "GET"
    assert last_signal.get("payload", {}).get("status_code") == 200
