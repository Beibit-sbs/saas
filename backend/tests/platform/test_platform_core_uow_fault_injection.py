from __future__ import annotations

from uuid import uuid4

import pytest

from app.platform.uow import UnitOfWork
from app.platform.tenant import service as tenant_service


pytestmark = pytest.mark.integration


def _require_real_postgres() -> None:
    # Rollback semantics are validated only against real PostgreSQL.
    from app.platform.repository.db import db_available, db_url

    if not db_available() or not db_url():
        pytest.skip("DATABASE_URL is not configured for real PostgreSQL fault-injection test")


def test_rollback_tenant_created_but_billing_fails() -> None:
    _require_real_postgres()

    suffix = uuid4().hex[:8]
    slug = f"rb-{suffix}"

    with pytest.raises(ValueError):
        with UnitOfWork() as uow:
            tenant = uow.tenant_repository.create_tenant(slug, f"Rollback {suffix}", conn=uow.conn)
            # Inject billing failure: missing plan code.
            uow.billing_repository.assign_subscription(int(tenant["tenant_id"]), "__missing_plan__", conn=uow.conn)

    rows = tenant_service.list_tenant_profiles()
    assert all(str(item["slug"]) != slug for item in rows)


def test_rollback_subscription_update_but_usage_fails() -> None:
    _require_real_postgres()

    suffix = uuid4().hex[:8]
    plan_code = f"plan-{suffix}"

    with UnitOfWork() as uow:
        tenant = uow.tenant_repository.create_tenant(f"sub-{suffix}", f"Sub {suffix}", conn=uow.conn)
        tenant_id = int(tenant["tenant_id"])
        uow.billing_repository.create_plan(
            code=plan_code,
            name=f"Plan {suffix}",
            price_cents=1000,
            features={"x": True},
            limits={"max_users": 10},
            conn=uow.conn,
        )

    with pytest.raises(ValueError):
        with UnitOfWork() as uow:
            uow.billing_repository.assign_subscription(tenant_id, plan_code, conn=uow.conn)
            # Inject usage failure.
            uow.usage_repository.increment(tenant_id, "", 1, conn=uow.conn)

    with UnitOfWork() as uow:
        sub = uow.billing_repository.get_subscription(tenant_id, conn=uow.conn)
    assert sub is None


def test_rollback_job_enqueue_but_notification_fails() -> None:
    _require_real_postgres()

    with pytest.raises(ValueError):
        with UnitOfWork() as uow:
            job = uow.job_repository.enqueue(tenant_id=1, job_type="notification_dispatch", payload={"scope": "x"}, max_retries=2, conn=uow.conn)
            # Inject notification failure via invalid channel.
            uow.notification_repository.dispatch(
                tenant_id=1,
                channel="invalid-channel",
                target="ops@example.com",
                payload={"event": "test"},
                subject="Fault",
                conn=uow.conn,
            )

    with UnitOfWork() as uow:
        read_back = uow.job_repository.get(int(job["id"]), conn=uow.conn) if "job" in locals() else None
    assert read_back is None
