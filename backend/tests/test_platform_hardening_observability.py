from __future__ import annotations

import logging
import uuid

from app.main import app
from tests.conftest import client


class _RecordCollector(logging.Handler):
    def __init__(self) -> None:
        super().__init__()
        self.records: list[logging.LogRecord] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.records.append(record)


def test_request_id_is_generated_and_echoed() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    request_id = response.headers.get("x-request-id")
    assert request_id is not None
    uuid.UUID(request_id)


def test_request_id_reuses_incoming_header() -> None:
    incoming_request_id = "req-integration-123"

    response = client.get("/health", headers={"X-Request-ID": incoming_request_id})

    assert response.status_code == 200
    assert response.headers.get("x-request-id") == incoming_request_id


def test_health_endpoint_returns_ok_payload() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_health_db_returns_unreachable_when_session_factory_is_missing() -> None:
    original_factory = getattr(app.state, "admissions_session_factory", None)
    app.state.admissions_session_factory = None
    try:
        response = client.get("/health/db")
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
        response = client.get("/health/db")
    finally:
        app.state.admissions_session_factory = original_factory

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "reachable"}


def test_metrics_endpoint_is_available_and_contains_http_metrics() -> None:
    # Make at least one request so counters are populated.
    health_response = client.get("/health")
    assert health_response.status_code == 200

    response = client.get("/metrics")

    assert response.status_code == 200
    assert "http_requests_total" in response.text
    assert "http_request_duration_seconds_bucket" in response.text
    assert "http_requests_status_class_total" in response.text


def test_request_log_contains_structured_fields() -> None:
    collector = _RecordCollector()
    request_logger = logging.getLogger("app.request")
    request_logger.addHandler(collector)

    try:
        response = client.get(
            "/health",
            headers={
                "X-Request-ID": "req-log-123",
                "X-Tenant-ID": "42",
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
    assert getattr(record, "tenant_id", None) == "42"
    assert getattr(record, "actor_id", None) == "actor-xyz"
    assert getattr(record, "method", None) == "GET"
    assert getattr(record, "path", None) == "/health"
    assert getattr(record, "status_code", None) == 200
    assert isinstance(getattr(record, "duration_ms", None), float)
