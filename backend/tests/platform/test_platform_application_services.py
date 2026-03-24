from __future__ import annotations

from uuid import uuid4

import pytest

from app.platform.application.notification_dispatch_service import NotificationDispatchService
from app.platform.application.subscription_rollover_service import SubscriptionRolloverService
from app.platform.application.tenant_onboarding_service import TenantOnboardingService
from app.platform.repository.db import db_available, db_url
from app.platform.tenant import service as tenant_service
from app.platform.uow import UnitOfWork


def _require_real_postgres() -> None:
    if not db_available() or not db_url():
        pytest.skip("DATABASE_URL is not configured for real PostgreSQL integration test")


def test_tenant_onboarding_idempotent_replay() -> None:
    suffix = uuid4().hex[:8]
    plan_code = f"onboard-{suffix}"

    with UnitOfWork() as uow:
        uow.billing_repository.create_plan(
            code=plan_code,
            name=f"Onboarding {suffix}",
            price_cents=14900,
            features={"core": True},
            limits={"max_users": 100},
            conn=uow.conn,
        )

    service = TenantOnboardingService()
    idempotency_key = f"tenant-onboard:{suffix}"

    first = service.onboard_tenant(
        slug=f"tenant-{suffix}",
        name=f"Tenant {suffix}",
        default_plan_code=plan_code,
        actor="pytest",
        idempotency_key=idempotency_key,
    )
    second = service.onboard_tenant(
        slug=f"tenant-{suffix}",
        name=f"Tenant {suffix}",
        default_plan_code=plan_code,
        actor="pytest",
        idempotency_key=idempotency_key,
    )

    assert first["idempotent_replay"] is False
    assert second["idempotent_replay"] is True
    assert int(first["tenant"]["tenant_id"]) == int(second["tenant"]["tenant_id"])
    assert len(first["jobs"]) == 2

    profiles = tenant_service.list_tenant_profiles()
    matching = [item for item in profiles if str(item["slug"]) == f"tenant-{suffix}"]
    assert len(matching) == 1

    with UnitOfWork() as uow:
        idem = uow.idempotency_repository.get(1, idempotency_key, "tenant_onboarding", conn=uow.conn)
    assert idem is not None
    assert str(idem["status"]) == "completed"


@pytest.mark.integration
def test_tenant_onboarding_rolls_back_on_failure() -> None:
    _require_real_postgres()

    suffix = uuid4().hex[:8]
    plan_code = f"onboard-rb-{suffix}"

    with UnitOfWork() as uow:
        uow.billing_repository.create_plan(
            code=plan_code,
            name=f"Onboarding Rollback {suffix}",
            price_cents=9900,
            features={"core": True},
            limits={"max_users": 50},
            conn=uow.conn,
        )

    service = TenantOnboardingService()
    slug = f"rollback-{suffix}"

    with pytest.raises(RuntimeError):
        service.onboard_tenant(
            slug=slug,
            name=f"Rollback {suffix}",
            default_plan_code=plan_code,
            actor="pytest",
            idempotency_key=f"tenant-onboard-rb:{suffix}",
            fail_step="jobs",
        )

    profiles = tenant_service.list_tenant_profiles()
    assert all(str(item["slug"]) != slug for item in profiles)


def test_notification_dispatch_retry_flow() -> None:
    suffix = uuid4().hex[:8]
    service = NotificationDispatchService()

    dispatched = service.dispatch(
        tenant_id=1,
        channel="email",
        target="ops@example.com",
        subject="Retry test",
        payload={"event": "platform.test", "fail_once_token": f"tok-{suffix}"},
        actor="pytest",
        idempotency_key=f"notify:{suffix}",
    )
    assert dispatched["status"] == "failed"
    assert dispatched["idempotent_replay"] is False

    retried = service.retry_failed_deliveries(actor="pytest")
    assert retried["attempted"] >= 1
    assert retried["succeeded"] >= 1

    with UnitOfWork() as uow:
        row = uow.notification_repository.get(int(dispatched["notification_id"]), conn=uow.conn)
    assert row is not None
    assert str(row["status"]) == "sent"
    assert int(row["retry_count"]) >= 1


def test_subscription_rollover_is_idempotent_per_period() -> None:
    suffix = uuid4().hex[:8]
    plan_code = f"rollover-{suffix}"

    with UnitOfWork() as uow:
        tenant = uow.tenant_repository.create_tenant(f"roll-{suffix}", f"Rollover {suffix}", conn=uow.conn)
        tenant_id = int(tenant["tenant_id"])
        uow.billing_repository.create_plan(
            code=plan_code,
            name=f"Rollover {suffix}",
            price_cents=19900,
            features={"core": True},
            limits={"max_users": 120},
            conn=uow.conn,
        )
        uow.billing_repository.assign_subscription(tenant_id, plan_code, conn=uow.conn)
        before_jobs = [
            item
            for item in uow.job_repository.list_for_tenant(tenant_id, limit=200, conn=uow.conn)
            if str(item.get("job_type", "")).startswith("billing.")
        ]

    service = SubscriptionRolloverService()
    first = service.run_rollover_cycle(due_age_seconds=0, max_tenants=500, actor="pytest")
    second = service.run_rollover_cycle(due_age_seconds=0, max_tenants=500, actor="pytest")

    assert first["processed"] >= 1

    with UnitOfWork() as uow:
        after_first_second_jobs = [
            item
            for item in uow.job_repository.list_for_tenant(tenant_id, limit=300, conn=uow.conn)
            if str(item.get("job_type", "")).startswith("billing.")
        ]

    assert len(after_first_second_jobs) == len(before_jobs) + 2
    assert second["replayed"] >= 1
