#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE=(docker compose --env-file .env)

bash "${ROOT_DIR}/scripts/docker_only_guard.sh"

export ROOT_DIR
export BACKEND_DIR="${ROOT_DIR}/backend"
export REDIS_URL="${REDIS_URL:-redis://redis:6379/0}"
: "${JWT_SECRET:?set JWT_SECRET explicitly for smoke check}"
export JWT_SECRET
export API_BASE_URL="${API_BASE_URL:-http://backend:8000}"
export ADMIN_PANEL_URL="${ADMIN_PANEL_URL:-http://nginx}"
export AUTH_DEV_DEMO_COMPATIBILITY="${AUTH_DEV_DEMO_COMPATIBILITY:-false}"
export RBAC_ALLOW_DEV_FALLBACK="${RBAC_ALLOW_DEV_FALLBACK:-false}"

pushd "${ROOT_DIR}/infra" >/dev/null
"${COMPOSE[@]}" up -d --build
"${COMPOSE[@]}" exec -T backend python - <<'PY'
from __future__ import annotations

import os
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT_DIR = Path(os.environ["ROOT_DIR"])
BACKEND_DIR = Path(os.environ["BACKEND_DIR"])

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from fastapi.testclient import TestClient

from app.main import app
from app.modules.auth.token_service import create_access_token
from app.modules.rbac import service as rbac_service
from app.modules.students import service as students_service
from app.platform.ai import service as ai_service
from app.platform.analytics import service as analytics_service
from app.platform.automation import service as automation_service
from app.platform.context import service as context_service
from app.platform.developer import service as developer_service
from app.platform.events.handlers.analytics_handler import AnalyticsEventHandler
from app.platform.events.handlers.context_projection_handler import ContextProjectionHandler
from app.platform.events.handlers.webhook_handler import WebhookEventHandler
from app.platform.events.publisher import EventPublisher
from app.platform.events.schemas import OutboxEventRead
from app.platform.events.worker import OutboxEventWorker
from app.platform.kpi import service as kpi_service
from app.platform.runtime_state import clear_runtime_state
from app.platform.tenant import service as tenant_service
from app.platform.uow import UnitOfWork
import app.platform.webhooks.service as webhook_service_module


client = TestClient(app)
results: list[tuple[str, bool, str]] = []


def ensure(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def record(name: str, ok: bool, detail: str) -> None:
    status = "PASS" if ok else "FAIL"
    print(f"[{status}] {name}: {detail}")
    results.append((name, ok, detail))


def run_check(name: str, callback) -> None:
    try:
        detail = str(callback())
    except Exception as exc:  # pragma: no cover - exercised by smoke failures
        record(name, False, str(exc))
        return
    record(name, True, detail)


def auth_headers(user_id: str, roles: list[str], tenant_id: int) -> dict[str, str]:
    for role in roles:
        try:
            rbac_service.assign_role_to_user(tenant_id=tenant_id, user_id=user_id, role=role)
        except ValueError as exc:
            if "unknown role" not in str(exc):
                raise
    token = create_access_token(user_id=user_id, roles=roles, auth_source="smoke")
    return {
        "Authorization": f"Bearer {token}",
        "X-Tenant-ID": str(tenant_id),
    }


def internal_headers() -> dict[str, str]:
    token = os.getenv("PLATFORM_INTERNAL_TOKEN", "").strip()
    return {"Authorization": f"Bearer {token}"} if token else {}


def reset_state() -> None:
    clear_runtime_state()
    analytics_service.clear_analytics_state()
    ai_service.clear_ai_state()
    developer_service.clear_developer_state()
    kpi_service.clear_kpi_state()
    automation_service.clear_automation_state()
    context_service.clear_context_state()
    webhook_service_module.clear_webhook_state()
    with UnitOfWork() as uow:
        uow.outbox_event_repository.clear_state(conn=uow.conn)
        uow.analytics_repository.clear_state()


reset_state()

suffix = uuid.uuid4().hex[:8]
tenant = tenant_service.create_tenant(f"pilot-smoke-{suffix}", f"Pilot Smoke {suffix}")
tenant_id = int(tenant["tenant_id"])
admin_headers = auth_headers("pilot.ops@example.com", ["admin"], tenant_id)
internal_auth_headers = internal_headers()

with UnitOfWork() as uow:
    uow.outbox_event_repository.clear_state(conn=uow.conn)

students_service.create_student(
    {
        "student_id": f"SMOKE-{suffix.upper()}",
        "first_name": "Pilot",
        "last_name": "Student",
        "email": f"pilot-smoke-{suffix}@example.edu",
        "status": "active",
    },
    tenant_id,
)


def health_check() -> str:
    ready = client.get("/health")
    ensure(ready.status_code == 200, f"/health returned {ready.status_code}")
    ensure(ready.json() == {"status": "ok", "service": "api"}, "unexpected /health payload")

    worker_run = client.post("/api/v1/internal/worker/run-once", headers=internal_auth_headers)
    ensure(worker_run.status_code == 200, f"worker run-once returned {worker_run.status_code}")

    scheduler_run = client.post("/api/v1/internal/scheduler/run-once", headers=internal_auth_headers)
    ensure(scheduler_run.status_code == 200, f"scheduler run-once returned {scheduler_run.status_code}")

    db = client.get("/health/db")
    ensure(db.status_code in {200, 503}, f"/health/db returned {db.status_code}")
    db_payload = db.json()
    ensure(db_payload.get("database") in {"reachable", "unreachable"}, "unexpected /health/db payload")

    worker = client.get("/health/worker")
    ensure(worker.status_code == 200, f"/health/worker returned {worker.status_code}")
    ensure(worker.json().get("worker") == "reachable", "worker heartbeat missing")
    return f"api=ok db={db_payload['database']} worker=reachable scheduler=ran"


def outbox_processing_check() -> str:
    with UnitOfWork() as uow:
        event = EventPublisher(uow=uow).publish_event(
            tenant_id=tenant_id,
            event_type="student.created",
            aggregate_type="student_profile",
            aggregate_id=f"smoke-event-{suffix}",
            payload_json={"student_id": f"smoke-event-{suffix}", "name": "Pilot Student"},
        )

    worker = OutboxEventWorker(
        handlers=[AnalyticsEventHandler(), ContextProjectionHandler()],
        retry_delay_seconds=0.0,
    )
    result = worker.run_once()
    ensure(result["processed"] >= 1, "outbox worker did not process events")

    with UnitOfWork() as uow:
        backlog = uow.outbox_event_repository.count_backlog(conn=uow.conn)
    ensure(backlog == 0, f"outbox backlog not drained: {backlog}")
    return f"event_id={event['id']} processed={result['processed']} backlog={backlog}"


def automation_check() -> str:
    with UnitOfWork() as uow:
        automation_service.create_rule(
            tenant_id=tenant_id,
            name=f"Smoke Automation {suffix}",
            description="pilot smoke automation rule",
            event_type="student.created",
            condition_json={},
            actions_json=[{"type": "create_task", "job_type": "smoke_review", "max_retries": 1}],
            is_active=True,
            uow=uow,
        )

    now = datetime.now(timezone.utc).isoformat()
    response = client.post(
        "/api/v1/internal/platform/automation/evaluate",
        headers=internal_auth_headers,
        json={
            "id": 9001,
            "tenant_id": tenant_id,
            "event_type": "student.created",
            "aggregate_type": "student_profile",
            "aggregate_id": f"automation-{suffix}",
            "payload_json": {"student_id": f"automation-{suffix}"},
            "status": "pending",
            "retry_count": 0,
            "available_at": now,
            "created_at": now,
        },
    )
    ensure(response.status_code == 200, f"automation evaluate returned {response.status_code}")
    payload = response.json()
    ensure(payload["rules_matched"] >= 1, "automation rule did not match")
    ensure(any(item.get("status") == "completed" for item in payload.get("executions", [])), "automation did not complete")
    return f"matched={payload['rules_matched']} executions={len(payload['executions'])}"


def webhook_retry_check() -> str:
    create_resp = client.post(
        "/api/v1/admin/webhooks/subscriptions",
        headers=admin_headers,
        json={
            "tenant_id": tenant_id,
            "event_type": "grade.submitted",
            "target_url": "https://example.com/pilot-smoke-webhook",
            "signing_secret": "pilot-smoke-signing-secret",
        },
    )
    ensure(create_resp.status_code == 201, f"webhook subscription returned {create_resp.status_code}")

    original_sender = webhook_service_module.webhook_service._sender
    original_now = webhook_service_module._utc_now
    try:
        webhook_service_module.webhook_service._sender = lambda *_args, **_kwargs: (503, "upstream unavailable")
        with UnitOfWork() as uow:
            published = EventPublisher(uow=uow).publish_event(
                tenant_id=tenant_id,
                event_type="grade.submitted",
                aggregate_type="grade_submission",
                aggregate_id=f"grade-{suffix}",
                payload_json={"submission_id": f"grade-{suffix}"},
            )
            event_row = uow.outbox_event_repository.get(int(published["id"]), conn=uow.conn)
            ensure(event_row is not None, "published webhook outbox event not found")
            dispatch_result = webhook_service_module.webhook_service.dispatch_event_to_subscriptions(
                event=OutboxEventRead.model_validate(event_row),
                uow=uow,
            )
        ensure(dispatch_result["failed"] >= 1, "webhook dispatch did not fail as expected")

        failed = client.get("/api/v1/internal/webhooks/failed-deliveries", headers=internal_auth_headers)
        ensure(failed.status_code == 200, f"failed-deliveries returned {failed.status_code}")
        failed_payload = failed.json()
        ensure("failed_deliveries_count" in failed_payload, "failed-deliveries payload incomplete")

        with UnitOfWork() as uow:
            retry_backlog = uow.webhook_repository.count_retry_backlog(conn=uow.conn)
            failed_deliveries = uow.webhook_repository.count_failed_deliveries(conn=uow.conn)
        ensure(retry_backlog >= 1, "expected webhook retry backlog")
        ensure(failed_deliveries >= 1, "expected failed webhook delivery")

        webhook_service_module.webhook_service._sender = lambda *_args, **_kwargs: (200, "ok")
        webhook_service_module._utc_now = lambda: datetime.now(timezone.utc) + timedelta(days=1)
        retried = client.post("/api/v1/internal/webhooks/retry-failed", headers=internal_auth_headers)
        ensure(retried.status_code == 200, f"retry-failed returned {retried.status_code}")
        retried_payload = retried.json()
        ensure(retried_payload["delivered"] >= 1, "webhook retry did not recover")
        return f"failed={failed_deliveries} backlog={retry_backlog} recovered={retried_payload['delivered']}"
    finally:
        webhook_service_module.webhook_service._sender = original_sender
        webhook_service_module._utc_now = original_now


def kpi_refresh_check() -> str:
    response = client.post(f"/api/v1/internal/platform/kpi/refresh/{tenant_id}", headers=internal_auth_headers)
    ensure(response.status_code == 200, f"kpi refresh returned {response.status_code}")
    payload = response.json()
    ensure(isinstance(payload.get("cards"), list), "kpi dashboard cards missing")
    return f"cards={len(payload['cards'])} snapshot_date={payload['snapshot_date']}"


def ai_copilot_check() -> str:
    response = client.post(
        "/api/v1/admin/platform/ai/copilot/ask",
        headers=admin_headers,
        json={
            "tenant_id": tenant_id,
            "question": "Show me the latest KPI summary",
            "context": {},
        },
    )
    ensure(response.status_code == 200, f"copilot ask returned {response.status_code}")
    payload = response.json()
    required = {"question", "summary", "insights", "sources", "warnings", "recommendations"}
    ensure(required.issubset(payload.keys()), "copilot response shape incomplete")
    return f"summary={payload['summary']}"


def developer_auth_flow_check() -> str:
    create_resp = client.post(
        "/api/v1/admin/platform/developer/apps",
        headers=admin_headers,
        json={
            "name": f"Pilot Smoke App {suffix}",
            "description": "pilot smoke developer app",
            "owner_email": "pilot-smoke@example.com",
            "scopes": ["students.read", "analytics.read"],
        },
    )
    ensure(create_resp.status_code == 201, f"developer app create returned {create_resp.status_code}")
    app_payload = create_resp.json()

    install_resp = client.post(
        f"/api/v1/admin/platform/developer/apps/{app_payload['id']}/installations",
        headers=admin_headers,
        json={"tenant_id": tenant_id},
    )
    ensure(install_resp.status_code == 201, f"developer install returned {install_resp.status_code}")

    unauthorized = client.get("/api/v1/public/students")
    ensure(unauthorized.status_code == 401, f"unauthorized public request returned {unauthorized.status_code}")

    authorized = client.get(
        "/api/v1/public/students",
        headers={
            "X-App-Key": app_payload["app_key"],
            "X-App-Secret": app_payload["app_secret"],
            "X-Tenant-Id": str(tenant_id),
        },
    )
    ensure(authorized.status_code == 200, f"authorized public request returned {authorized.status_code}")
    ensure(len(authorized.json()) >= 1, "public students returned no records")

    logs_resp = client.get(
        f"/api/v1/admin/platform/developer/apps/{app_payload['id']}/logs",
        headers=admin_headers,
    )
    ensure(logs_resp.status_code == 200, f"developer logs returned {logs_resp.status_code}")
    ensure(any(item.get("status_code") == 200 for item in logs_resp.json()), "developer success log missing")
    return f"app_id={app_payload['id']} public_students={len(authorized.json())}"


def metrics_check() -> str:
    ops = client.get("/metrics/ops")
    ensure(ops.status_code == 200, f"/metrics/ops returned {ops.status_code}")
    ops_payload = ops.json()
    for key in (
        "event_queue_size",
        "failed_webhooks",
        "dead_webhooks",
        "failed_automation_executions",
        "dead_automation_executions",
        "failed_jobs",
        "dead_jobs",
        "retry_backlog",
    ):
        ensure(key in ops_payload, f"missing ops metric: {key}")

    latency = client.get("/metrics/latency")
    ensure(latency.status_code == 200, f"/metrics/latency returned {latency.status_code}")
    latency_payload = latency.json()
    ensure("developer_api_error_count" in latency_payload, "missing developer_api_error_count")
    return (
        f"failed_webhooks={ops_payload['failed_webhooks']} "
        f"retry_backlog={ops_payload['retry_backlog']} "
        f"developer_api_error_count={latency_payload['developer_api_error_count']}"
    )


run_check("Health Surfaces", health_check)
run_check("Outbox Event Processing", outbox_processing_check)
run_check("Automation Execution", automation_check)
run_check("Webhook Retry Behavior", webhook_retry_check)
run_check("KPI Refresh", kpi_refresh_check)
run_check("AI Copilot Response", ai_copilot_check)
run_check("Developer Platform Auth Flow", developer_auth_flow_check)
run_check("Metrics Surfaces", metrics_check)

passed = sum(1 for _, ok, _ in results if ok)
failed = len(results) - passed
print(f"\n[SUMMARY] passed={passed} failed={failed}")

if failed:
    sys.exit(1)
PY
popd >/dev/null