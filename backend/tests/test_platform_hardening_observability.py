from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta, timezone

import pytest

from app.main import app
from app.modules.auth.token_service import create_access_token
from app.platform.events.publisher import EventPublisher
from app.platform.runtime_state import clear_runtime_state, record_scheduler_run, record_worker_heartbeat
from app.platform.uow import UnitOfWork
from app.platform.webhooks.service import webhook_service
from tests.conftest import ADMIN_HEADERS, client


class _RecordCollector(logging.Handler):
    def __init__(self) -> None:
        super().__init__()
        self.records: list[logging.LogRecord] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.records.append(record)


class _FakeRedisRuntimeClient:
    def __init__(self) -> None:
        self._store: dict[str, str] = {}

    def ping(self) -> bool:
        return True

    def set(self, key: str, value: str) -> None:
        self._store[key] = value

    def get(self, key: str) -> str | None:
        return self._store.get(key)

    def delete(self, key: str) -> None:
        self._store.pop(key, None)


def test_request_id_is_generated_and_echoed() -> None:
    response = client.get("/health", headers=ADMIN_HEADERS)

    assert response.status_code == 200
    request_id = response.headers.get("x-request-id")
    assert request_id is not None
    uuid.UUID(request_id)


def test_request_id_reuses_incoming_header() -> None:
    incoming_request_id = "req-integration-123"

    response = client.get("/health", headers={**ADMIN_HEADERS, "X-Request-ID": incoming_request_id})

    assert response.status_code == 200
    assert response.headers.get("x-request-id") == incoming_request_id


def test_health_endpoint_returns_ok_payload() -> None:
    response = client.get("/health", headers=ADMIN_HEADERS)

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "api"}


def test_health_db_returns_unreachable_when_session_factory_is_missing() -> None:
    original_factory = getattr(app.state, "admissions_session_factory", None)
    app.state.admissions_session_factory = None
    try:
        response = client.get("/health/db", headers=ADMIN_HEADERS)
    finally:
        app.state.admissions_session_factory = original_factory

    assert response.status_code == 503
    assert response.json() == {"status": "error", "database": "unreachable"}


def test_health_db_returns_ok_when_database_is_reachable() -> None:
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

    original_factory = getattr(app.state, "admissions_session_factory", None)
    app.state.admissions_session_factory = _FakeSessionFactory()
    try:
        response = client.get("/health/db", headers=ADMIN_HEADERS)
    finally:
        app.state.admissions_session_factory = original_factory

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "reachable"}


def test_metrics_endpoint_is_available_and_contains_http_metrics() -> None:
    # Make at least one request so counters are populated.
    health_response = client.get("/health", headers=ADMIN_HEADERS)
    assert health_response.status_code == 200

    response = client.get("/metrics", headers=ADMIN_HEADERS)

    assert response.status_code == 200
    assert "http_requests_total" in response.text
    assert "http_request_duration_seconds_bucket" in response.text
    assert "http_requests_status_class_total" in response.text


def test_ops_and_latency_metrics_are_normalized() -> None:
    tenant_id = 1

    with UnitOfWork() as uow:
        subscription = webhook_service.create_subscription(
            tenant_id=tenant_id,
            event_type="student.created",
            target_url="https://example.com/failing-webhook",
            signing_secret="metrics-signing-secret",
        )

        job = uow.job_repository.enqueue(tenant_id, "sync", {"batch": 1}, 1, conn=uow.conn)
        uow.job_repository.mark_running(int(job["id"]), conn=uow.conn)
        uow.job_repository.requeue_for_retry(int(job["id"]), "temporary", conn=uow.conn)
        uow.job_repository.mark_running(int(job["id"]), conn=uow.conn)
        uow.job_repository.mark_failed(int(job["id"]), "terminal", conn=uow.conn)

        execution = uow.automation_repository.create_execution(
            tenant_id=tenant_id,
            rule_id=101,
            event_id=501,
            status="pending",
            result_json={},
            conn=uow.conn,
        )
        uow.automation_repository.update_execution_status(
            int(execution.id),
            status="failed",
            result_json={"actions": []},
            error_message="boom",
            conn=uow.conn,
        )

        event = EventPublisher(uow=uow).publish_event(
            tenant_id=tenant_id,
            event_type="student.created",
            aggregate_type="student_profile",
            aggregate_id="1001",
            payload_json={"student_profile_id": 1001},
        )
        delivery = uow.webhook_repository.create_delivery_attempt(
            tenant_id=tenant_id,
            subscription_id=int(subscription["id"]),
            outbox_event_id=int(event["id"]),
            event_type="student.created",
            target_url="https://example.com/failing-webhook",
            request_payload_json={"payload": {"event_type": "student.created"}, "headers": {}},
            retry_count=1,
            conn=uow.conn,
        )
        uow.webhook_repository.finalize_delivery_attempt(
            int(delivery["id"]),
            delivery_status="failed",
            response_status_code=503,
            response_body="down",
            next_retry_at=datetime.now(timezone.utc) + timedelta(minutes=5),
            last_error="upstream unavailable",
            conn=uow.conn,
        )

        app_row = uow.developer_repository.create_app(
            tenant_id=tenant_id,
            name="metrics-check",
            app_key="app_metrics_check",
            app_secret_hash="secret-hash",
            description="",
            owner_email="ops@example.com",
            status="active",
            webhook_url=None,
            scopes=["students.read"],
            conn=uow.conn,
        )
        uow.developer_repository.log_api_call(
            app_id=int(app_row["id"]),
            tenant_id=tenant_id,
            endpoint="/api/dev/students",
            status_code=503,
            latency_ms=12.5,
            conn=uow.conn,
        )

    ops_response = client.get("/metrics/ops", headers=ADMIN_HEADERS)
    assert ops_response.status_code == 200
    ops_payload = ops_response.json()
    assert ops_payload["failed_webhooks"] >= 1
    assert ops_payload["dead_webhooks"] == 0
    assert ops_payload["failed_automation_executions"] >= 1
    assert ops_payload["dead_automation_executions"] >= 1
    assert ops_payload["failed_jobs"] >= 1
    assert ops_payload["dead_jobs"] >= 1
    assert ops_payload["retry_backlog"] >= 1
    assert "worker_last_heartbeat" in ops_payload
    assert "scheduler_last_run" in ops_payload

    latency_response = client.get("/metrics/latency", headers=ADMIN_HEADERS)
    assert latency_response.status_code == 200
    latency_payload = latency_response.json()
    assert "developer_api_error_count" in latency_payload
    assert latency_payload["developer_api_error_count"] >= 1


def test_request_log_contains_structured_fields() -> None:
    collector = _RecordCollector()
    request_logger = logging.getLogger("app.request")
    request_logger.addHandler(collector)
    superadmin_headers = {
        "Authorization": f"Bearer {create_access_token('platform.owner@example.com', ['superadmin'], 'test', tenant_id=1)}",
    }

    try:
        response = client.get(
            "/health",
            headers={
                **superadmin_headers,
                "X-Request-ID": "req-log-123",
                "X-Tenant-ID": "1",
                "X-Actor-ID": "actor-xyz",
            },
        )
    finally:
        request_logger.removeHandler(collector)

    assert response.status_code == 200

    http_records = [record for record in collector.records if record.getMessage() == "http_request"]
    assert http_records, "expected at least one app.request http_request log record"

    record = http_records[-1]
    assert getattr(record, "request_id", None) == "req-log-123"
    assert getattr(record, "tenant_id", None) == "1"
    assert getattr(record, "actor_id", None) == "platform.owner@example.com"
    assert getattr(record, "method", None) == "GET"
    assert getattr(record, "path", None) == "/health"
    assert getattr(record, "status_code", None) == 200
    assert isinstance(getattr(record, "duration_ms", None), float)


def test_health_comprehensive_reports_degraded_when_worker_and_scheduler_missing(monkeypatch: pytest.MonkeyPatch) -> None:
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

    fake_runtime_redis = _FakeRedisRuntimeClient()
    monkeypatch.setattr("app.platform.runtime_state._redis_client", lambda: fake_runtime_redis)
    monkeypatch.setattr(
        "app.modules.observability.health._redis_dependency",
        lambda: {"name": "redis", "status": "up", "healthy": True, "critical": True, "details": {}},
    )
    monkeypatch.setattr(
        "app.modules.observability.health._ldap_dependency",
        lambda _app: {"name": "ldap", "status": "up", "healthy": True, "critical": True, "details": {}},
    )

    original_factory = getattr(app.state, "admissions_session_factory", None)
    app.state.admissions_session_factory = _FakeSessionFactory()
    clear_runtime_state()
    try:
        response = client.get("/health/comprehensive", headers=ADMIN_HEADERS)
    finally:
        app.state.admissions_session_factory = original_factory
        clear_runtime_state()

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "degraded"
    assert payload["components"]["database"] == "reachable"
    assert payload["components"]["worker"] == "unreachable"
    assert payload["components"]["scheduler"] == "unreachable"
    assert "worker_not_running" in payload["issues"]
    assert "scheduler_not_running" in payload["issues"]


def test_health_comprehensive_reports_healthy_when_all_components_are_running(monkeypatch: pytest.MonkeyPatch) -> None:
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

    fake_runtime_redis = _FakeRedisRuntimeClient()
    monkeypatch.setattr("app.platform.runtime_state._redis_client", lambda: fake_runtime_redis)
    monkeypatch.setattr(
        "app.modules.observability.health._redis_dependency",
        lambda: {"name": "redis", "status": "up", "healthy": True, "critical": True, "details": {}},
    )
    monkeypatch.setattr(
        "app.modules.observability.health._ldap_dependency",
        lambda _app: {"name": "ldap", "status": "up", "healthy": True, "critical": True, "details": {}},
    )

    original_factory = getattr(app.state, "admissions_session_factory", None)
    app.state.admissions_session_factory = _FakeSessionFactory()
    clear_runtime_state()
    record_worker_heartbeat()
    record_scheduler_run("test")
    try:
        response = client.get("/health/comprehensive", headers=ADMIN_HEADERS)
    finally:
        app.state.admissions_session_factory = original_factory
        clear_runtime_state()

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "healthy"
    assert payload["components"]["database"] == "reachable"
    assert payload["components"]["worker"] == "reachable"
    assert payload["components"]["scheduler"] == "reachable"
    assert payload["issues"] == []
    assert "event_queue_size" in payload["metrics"] or "error" in payload["metrics"]
