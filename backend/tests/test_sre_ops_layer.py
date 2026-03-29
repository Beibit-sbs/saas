from __future__ import annotations

from pathlib import Path
import re
from typing import Any

import pytest

from app.main import app
from app.modules.observability.alerts import clear_alert_state
from app.modules.observability.metrics import (
    clear_metrics_state,
    observe_auth_login_attempt,
    observe_job_execution,
    set_db_connections_active,
    set_redis_latency,
)
from tests.conftest import ADMIN_HEADERS, client


def _healthy_dependency(name: str, *, critical: bool = True, details: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "name": name,
        "status": "up",
        "healthy": True,
        "critical": critical,
        "details": details or {},
    }


def _down_dependency(name: str, *, critical: bool = True, reason: str = "unavailable") -> dict[str, Any]:
    return {
        "name": name,
        "status": "down",
        "healthy": False,
        "critical": critical,
        "details": {"reason": reason},
    }


def test_health_live_returns_process_only_payload() -> None:
    response = client.get("/health/live")

    assert response.status_code == 200, response.text
    assert response.json()["live"] is True
    assert response.json()["service"] == "api"


def test_health_ready_db_down_returns_not_ready(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.modules.observability.health._redis_dependency", lambda: _healthy_dependency("redis"))
    monkeypatch.setattr("app.modules.observability.health._migrations_dependency", lambda _app: _healthy_dependency("migrations"))

    original_engine = getattr(app.state, "admissions_engine", None)
    original_factory = getattr(app.state, "admissions_session_factory", None)
    app.state.admissions_engine = None
    app.state.admissions_session_factory = None
    try:
        response = client.get("/health/ready")
    finally:
        app.state.admissions_engine = original_engine
        app.state.admissions_session_factory = original_factory

    assert response.status_code == 503, response.text
    payload = response.json()
    assert payload["ready"] is False
    assert payload["dependencies"]["postgresql"]["status"] == "down"


def test_health_ready_redis_down_returns_not_ready(monkeypatch: pytest.MonkeyPatch) -> None:
    class _FakePool:
        def checkedout(self) -> int:
            return 2

        def status(self) -> str:
            return "checked out connections: 2"

    class _FakeEngine:
        pool = _FakePool()

    class _FakeSession:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def execute(self, *_args, **_kwargs):
            return None

    class _FakeSessionFactory:
        def __call__(self):
            return _FakeSession()

    monkeypatch.setattr("app.modules.observability.health._migrations_dependency", lambda _app: _healthy_dependency("migrations"))
    monkeypatch.setattr("app.modules.observability.health._redis_dependency", lambda: _down_dependency("redis", reason="connection refused"))

    original_engine = getattr(app.state, "admissions_engine", None)
    original_factory = getattr(app.state, "admissions_session_factory", None)
    app.state.admissions_engine = _FakeEngine()
    app.state.admissions_session_factory = _FakeSessionFactory()
    try:
        response = client.get("/health/ready")
    finally:
        app.state.admissions_engine = original_engine
        app.state.admissions_session_factory = original_factory

    assert response.status_code == 503, response.text
    payload = response.json()
    assert payload["ready"] is False
    assert payload["dependencies"]["redis"]["status"] == "down"


def test_metrics_endpoint_contains_sre_metrics() -> None:
    clear_metrics_state()
    observe_auth_login_attempt(auth_source="ldap", outcome="success")
    observe_auth_login_attempt(auth_source="ldap", outcome="IDENTITY_INVALID_CREDENTIALS")
    observe_job_execution(outcome="success")
    observe_job_execution(outcome="failed")
    set_db_connections_active(3)
    set_redis_latency(0.012)

    response = client.get("/metrics", headers=ADMIN_HEADERS)

    assert response.status_code == 200, response.text
    assert "auth_login_attempts_total" in response.text
    assert "auth_login_failures_total" in response.text
    assert "jobs_executed_total" in response.text
    assert "jobs_failed_total" in response.text
    assert "db_connections_active 3" in response.text
    assert "redis_latency_seconds 0.012" in response.text


def test_metrics_include_tenant_id_labels() -> None:
    clear_metrics_state()
    observe_auth_login_attempt(auth_source="ldap", outcome="success", tenant_id=42)

    health_response = client.get("/health/live", headers={"X-Tenant-ID": "42"})
    assert health_response.status_code == 200, health_response.text

    response = client.get("/metrics", headers=ADMIN_HEADERS)

    assert response.status_code == 200, response.text
    assert 'http_requests_total{method="GET",path="/health/live",status="200",tenant_id="42"}' in response.text
    assert 'auth_login_attempts_total{tenant_id="42",auth_source="ldap",outcome="success"}' in response.text


def test_alert_trigger_is_emitted_for_dependency_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    sent_payloads: list[dict[str, Any]] = []
    clear_alert_state()

    monkeypatch.setattr("app.modules.observability.alerts._send_webhook", lambda payload: sent_payloads.append(payload))
    monkeypatch.setattr("app.modules.observability.health._postgres_dependency", lambda _app: _healthy_dependency("postgresql"))
    monkeypatch.setattr("app.modules.observability.health._migrations_dependency", lambda _app: _healthy_dependency("migrations"))
    monkeypatch.setattr("app.modules.observability.health._redis_dependency", lambda: _down_dependency("redis", reason="timeout"))

    response = client.get("/health/ready")

    assert response.status_code == 503, response.text
    assert sent_payloads, "expected ops alert payload"
    assert sent_payloads[-1]["event"] == "redis.unavailable"
    assert sent_payloads[-1]["severity"] == "critical"


def test_alert_severity_mapping_for_warning_and_info(monkeypatch: pytest.MonkeyPatch) -> None:
    sent_payloads: list[dict[str, Any]] = []
    clear_alert_state()

    monkeypatch.setattr("app.modules.observability.alerts._send_webhook", lambda payload: sent_payloads.append(payload))

    from app.modules.observability.alerts import observe_job_failure_spike, observe_dependency_state

    for _ in range(6):
        observe_job_failure_spike(job_type="sync")

    observe_dependency_state(component="redis", healthy=False, details={"reason": "timeout"})
    observe_dependency_state(component="redis", healthy=True, details={"reason": "restored"})

    severities = {item.get("event"): item.get("severity") for item in sent_payloads}
    assert severities.get("jobs.failures.spike") == "warning"
    assert severities.get("redis.unavailable") == "critical"
    assert severities.get("redis.recovered") == "info"


def test_legacy_health_endpoints_return_deprecated_header() -> None:
    for path in ("/health", "/health/db", "/health/comprehensive"):
        response = client.get(path, headers=ADMIN_HEADERS)
        assert response.headers.get("x-deprecated") == "true"


def test_alembic_revision_graph_has_no_missing_down_revision_links() -> None:
    versions_dir = Path(__file__).resolve().parents[1] / "alembic" / "versions"
    revision_pattern = re.compile(r"^revision\s*(?::\s*[^=]+)?\s*=\s*['\"]([^'\"]+)['\"]", flags=re.MULTILINE)
    down_pattern = re.compile(r"^down_revision\s*(?::\s*[^=]+)?\s*=\s*(.+)$", flags=re.MULTILINE)

    revisions: set[str] = set()
    down_refs: set[str] = set()

    for path in versions_dir.glob("*.py"):
        text = path.read_text(encoding="utf-8")
        revision_match = revision_pattern.search(text)
        if revision_match:
            revisions.add(revision_match.group(1))

        down_match = down_pattern.search(text)
        if not down_match:
            continue
        raw = down_match.group(1)
        down_refs.update(re.findall(r"['\"]([a-z0-9]+)['\"]", raw))

    missing = sorted(ref for ref in down_refs if ref not in revisions)
    assert missing == []