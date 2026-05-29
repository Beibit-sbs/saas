from __future__ import annotations

from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from starlette.requests import Request

from app.platform import router_ops


def _request() -> Request:
    return Request({"type": "http", "method": "GET", "path": "/api/v1/platform/ops/summary", "headers": []})


def test_resolve_request_tenant_id_rejects_non_positive_claim(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        router_ops,
        "resolve_current_user_claims",
        lambda *_args, **_kwargs: SimpleNamespace(tenant_id=0),
    )

    with pytest.raises(HTTPException) as exc:
        router_ops._resolve_request_tenant_id(_request())

    assert exc.value.status_code == 403
    assert exc.value.detail == "tenant context missing"


def test_resolve_request_tenant_id_accepts_positive_claim(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        router_ops,
        "resolve_current_user_claims",
        lambda *_args, **_kwargs: SimpleNamespace(tenant_id=7),
    )

    assert router_ops._resolve_request_tenant_id(_request()) == 7


def test_ops_summary_bff_router_exposes_summary_path() -> None:
    paths = {route.path for route in router_ops.bff_router.routes}
    assert "/api/bff/v1/platform/ops/summary" in paths


def test_build_ops_summary_payload_marks_computed_non_fake(monkeypatch: pytest.MonkeyPatch) -> None:
    class _StubUow:
        conn = None

        class outbox_event_repository:
            @staticmethod
            def count_backlog(conn=None):
                return 4

        class webhook_repository:
            @staticmethod
            def count_failed_deliveries(conn=None):
                return 1

            @staticmethod
            def count_dead_deliveries(conn=None):
                return 0

            @staticmethod
            def count_retry_backlog(conn=None):
                return 2

        class job_repository:
            @staticmethod
            def count_by_status(_status, conn=None):
                return 1

            @staticmethod
            def count_dead_jobs(conn=None):
                return 0

        class automation_repository:
            @staticmethod
            def count_failed_executions(conn=None):
                return 0

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

    monkeypatch.setattr(router_ops, "UnitOfWork", _StubUow)
    monkeypatch.setattr(
        router_ops,
        "snapshot_latency_metrics",
        lambda: {
            "p50_latency_ms": 10,
            "p95_latency_ms": 15,
            "p99_latency_ms": 20,
            "requests_per_minute": 100,
            "http_4xx_count": 2,
            "http_5xx_count": 1,
        },
    )
    monkeypatch.setattr(router_ops, "get_worker_heartbeat", lambda: None)
    monkeypatch.setattr(router_ops, "get_scheduler_last_run", lambda: {})
    monkeypatch.setattr(router_ops, "list_backup_history", lambda tenant_id: [{"status": "ok"}] if tenant_id == 1 else [])

    payload = router_ops._build_ops_summary_payload(1)

    assert payload["data_source"] == "computed_from_runtime_health"
    assert payload["fake_metrics"] is False
    assert payload["queues"]["event_queue_size"] == 6
