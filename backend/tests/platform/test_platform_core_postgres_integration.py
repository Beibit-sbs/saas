from __future__ import annotations

from uuid import uuid4

import pytest

from app.platform.billing import service as billing_service
from app.platform.jobs import service as jobs_service
from app.platform.jobs.worker import PlatformJobWorker
from app.platform.notifications import service as notifications_service
from app.platform.repository.db import db_available, db_url
from app.platform.tenant import service as tenant_service
from app.platform.uow import UnitOfWork


pytestmark = pytest.mark.integration


def _require_real_postgres() -> None:
    if not db_available() or not db_url():
        pytest.skip("DATABASE_URL is not configured for real PostgreSQL integration test")


def test_postgres_tenant_and_subscription_lifecycle() -> None:
    _require_real_postgres()

    suffix = uuid4().hex[:10]
    tenant = tenant_service.create_tenant(f"int-{suffix}", f"Integration {suffix}")
    tenant_id = int(tenant["tenant_id"])

    patched = tenant_service.patch_settings(tenant_id, {"region": "eu-central", "timezone": "UTC"})
    assert patched["settings"]["region"] == "eu-central"

    tenant_service.set_quotas(tenant_id, {"api_calls_per_day": 50000})
    tenant_service.set_limits(tenant_id, {"max_users": 400})

    plan_code = f"int-plan-{suffix}"
    with UnitOfWork() as uow:
        created_plan = uow.billing_repository.create_plan(
            code=plan_code,
            name=f"Integration {suffix}",
            price_cents=19900,
            features={"grades": True, "scheduling": True},
            limits={"max_users": 400},
            conn=uow.conn,
        )
        uow.billing_repository.assign_subscription(tenant_id, plan_code, conn=uow.conn)
    assert created_plan["code"] == plan_code

    sub_read = billing_service.get_subscription(tenant_id)
    assert sub_read is not None
    assert sub_read["plan_code"] == plan_code

    suspended = tenant_service.set_suspended(tenant_id, True)
    assert suspended["suspended"] is True

    reactivated = tenant_service.set_suspended(tenant_id, False)
    assert reactivated["suspended"] is False


def test_postgres_usage_jobs_and_notifications() -> None:
    _require_real_postgres()

    tenant_id = 1

    usage_1 = billing_service.increment_usage(tenant_id, "workflow.executions", 2)
    usage_2 = billing_service.increment_usage(tenant_id, "workflow.executions", 3)
    assert int(usage_2["value"]) >= int(usage_1["value"])

    queued = jobs_service.enqueue_job(tenant_id, "usage_rollup", {"window": "hour"}, max_retries=2)
    assert queued["status"] == "queued"

    worker = PlatformJobWorker(
        handlers={
            "usage_rollup": lambda payload: {"processed": True, "window": payload.get("window")},
        },
        batch_size=5,
    )
    outcome = worker.run_once()
    assert outcome["processed"] >= 1

    job = jobs_service.get_job(int(queued["id"]))
    assert job is not None
    assert job["status"] in {"succeeded", "queued", "running", "failed"}

    notification = notifications_service.dispatch_notification(
        tenant_id=tenant_id,
        channel="email",
        target="platform-ops@example.com",
        subject="Integration event",
        payload={"event": "usage_rollup.completed"},
    )
    assert notification["channel"] == "email"

    listed = notifications_service.list_notifications(tenant_id, limit=10)
    assert any(int(item["id"]) == int(notification["id"]) for item in listed)
