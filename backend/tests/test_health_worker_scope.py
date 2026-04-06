from app.modules.observability import health as health_module
from app.platform.runtime_state import clear_runtime_state
from tests.conftest import ADMIN_HEADERS, client


def test_health_worker_returns_skipped_when_worker_scope_is_optional(monkeypatch) -> None:
    monkeypatch.setenv("OPS_REQUIRE_WORKER_HEALTH", "false")
    monkeypatch.setattr(health_module, "get_worker_heartbeat", lambda: None)
    clear_runtime_state()

    response = client.get("/health/worker", headers=ADMIN_HEADERS)

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "skipped"
    assert body["worker"] == "out_of_scope"


def test_health_worker_returns_503_when_worker_scope_is_required(monkeypatch) -> None:
    monkeypatch.setenv("OPS_REQUIRE_WORKER_HEALTH", "true")
    monkeypatch.setattr(health_module, "get_worker_heartbeat", lambda: None)
    clear_runtime_state()

    response = client.get("/health/worker", headers=ADMIN_HEADERS)

    assert response.status_code == 503
    body = response.json()
    assert body["status"] == "error"
    assert body["worker"] == "unreachable"
