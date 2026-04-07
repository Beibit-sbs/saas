from __future__ import annotations

from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.modules.observability.metrics import render_metrics
from app.platform.billing import service as billing_service
from app.platform.jobs import service as jobs_service
from app.platform.jobs.worker import PlatformJobWorker
from app.platform.repository.billing_repository import BillingRepository
from app.platform.uow import UnitOfWork


def _seed_tenant_with_plan(*, suffix: str, price_cents: int = 9900) -> tuple[int, str]:
    with UnitOfWork() as uow:
        tenant = uow.tenant_repository.create_tenant(f"bill-{suffix}", f"Billing {suffix}", conn=uow.conn)
        tenant_id = int(tenant["tenant_id"])
        plan_code = f"plan-{suffix}"
        uow.billing_repository.create_plan(
            code=plan_code,
            name=f"Plan {suffix}",
            price_cents=price_cents,
            features={"core": True},
            limits={
                "max_users": 100,
                "included_api_requests": 0,
                "overage_cents_api_requests": 0,
                "included_workflow_executions": 0,
                "overage_cents_workflow_executions": 0,
                "included_notification_dispatch": 0,
                "overage_cents_notification_dispatch": 0,
            },
            conn=uow.conn,
        )
        uow.billing_repository.assign_subscription(tenant_id, plan_code, conn=uow.conn)
    return tenant_id, plan_code


def test_usage_to_invoice_flow_persists_real_invoice() -> None:
    suffix = uuid4().hex[:8]
    tenant_id, _ = _seed_tenant_with_plan(suffix=suffix, price_cents=12345)
    period_key = "2026-03"

    billing_service.increment_usage(tenant_id, "api.requests", 7, period_key=period_key)
    queued = jobs_service.enqueue_job(
        tenant_id,
        "billing.generate_invoice",
        {"tenant_id": tenant_id, "period_key": period_key},
        max_retries=0,
    )

    outcome = PlatformJobWorker(batch_size=5).run_once()
    assert outcome["succeeded"] == 1

    job = jobs_service.get_job(int(queued["id"]))
    assert job is not None
    assert str(job["status"]) == "succeeded"
    assert int(job["result"]["invoice_id"]) > 0

    with UnitOfWork() as uow:
        invoices = uow.invoice_repository.list_for_tenant(tenant_id, conn=uow.conn)

    assert len(invoices) == 1
    invoice = invoices[0]
    assert int(invoice["total_amount_cents"]) == 12345
    assert int(invoice["breakdown"]["api.requests"]) == 7



def test_missing_subscription_makes_billing_job_fail() -> None:
    suffix = uuid4().hex[:8]
    with UnitOfWork() as uow:
        tenant = uow.tenant_repository.create_tenant(f"nosub-{suffix}", f"NoSub {suffix}", conn=uow.conn)
        tenant_id = int(tenant["tenant_id"])

    queued = jobs_service.enqueue_job(
        tenant_id,
        "billing.generate_invoice",
        {"tenant_id": tenant_id, "period_key": "2026-03"},
        max_retries=0,
    )

    outcome = PlatformJobWorker(batch_size=5).run_once()
    assert outcome["failed"] == 1

    job = jobs_service.get_job(int(queued["id"]))
    assert job is not None
    assert str(job["status"]) == "failed"
    assert "subscription" in str(job.get("error", "")).lower()

    metrics = render_metrics()
    assert "billing_failures_total 1" in metrics



def test_unknown_platform_job_type_fails_fast() -> None:
    suffix = uuid4().hex[:8]
    tenant_id, _ = _seed_tenant_with_plan(suffix=suffix)

    queued = jobs_service.enqueue_job(tenant_id, "billing.unknown_action", {}, max_retries=0)
    result = PlatformJobWorker(batch_size=5).run_once()

    assert result["failed"] == 1
    job = jobs_service.get_job(int(queued["id"]))
    assert job is not None
    assert str(job["status"]) == "failed"
    assert "unsupported job_type" in str(job.get("error", "")).lower()



def test_invoice_generation_is_idempotent_per_tenant_period() -> None:
    suffix = uuid4().hex[:8]
    tenant_id, _ = _seed_tenant_with_plan(suffix=suffix, price_cents=5555)
    period_key = "2026-03"

    billing_service.increment_usage(tenant_id, "workflow.executions", 3, period_key=period_key)
    job_a = jobs_service.enqueue_job(
        tenant_id,
        "billing.generate_invoice",
        {"tenant_id": tenant_id, "period_key": period_key},
        max_retries=0,
    )
    job_b = jobs_service.enqueue_job(
        tenant_id,
        "billing.generate_invoice",
        {"tenant_id": tenant_id, "period_key": period_key},
        max_retries=0,
    )

    outcome = PlatformJobWorker(batch_size=10).run_once()
    assert outcome["processed"] == 2
    assert outcome["succeeded"] == 2

    first = jobs_service.get_job(int(job_a["id"]))
    second = jobs_service.get_job(int(job_b["id"]))
    assert first is not None and second is not None
    assert int(first["result"]["invoice_id"]) == int(second["result"]["invoice_id"])

    with UnitOfWork() as uow:
        invoices = uow.invoice_repository.list_for_tenant(tenant_id, conn=uow.conn)

    assert len(invoices) == 1



def test_invoice_generation_preserves_tenant_isolation() -> None:
    suffix_a = uuid4().hex[:8]
    suffix_b = uuid4().hex[:8]
    tenant_a, _ = _seed_tenant_with_plan(suffix=suffix_a, price_cents=1000)
    tenant_b, _ = _seed_tenant_with_plan(suffix=suffix_b, price_cents=2000)
    period_key = "2026-03"

    billing_service.increment_usage(tenant_a, "api.requests", 2, period_key=period_key)
    billing_service.increment_usage(tenant_b, "workflow.executions", 4, period_key=period_key)

    jobs_service.enqueue_job(
        tenant_a,
        "billing.generate_invoice",
        {"tenant_id": tenant_a, "period_key": period_key},
        max_retries=0,
    )
    jobs_service.enqueue_job(
        tenant_b,
        "billing.generate_invoice",
        {"tenant_id": tenant_b, "period_key": period_key},
        max_retries=0,
    )

    outcome = PlatformJobWorker(batch_size=10).run_once()
    assert outcome["succeeded"] == 2

    with UnitOfWork() as uow:
        invoices_a = uow.invoice_repository.list_for_tenant(tenant_a, conn=uow.conn)
        invoices_b = uow.invoice_repository.list_for_tenant(tenant_b, conn=uow.conn)

    assert len(invoices_a) == 1
    assert len(invoices_b) == 1
    assert int(invoices_a[0]["tenant_id"]) == tenant_a
    assert int(invoices_b[0]["tenant_id"]) == tenant_b
    assert "api.requests" in invoices_a[0]["breakdown"]
    assert "workflow.executions" not in invoices_a[0]["breakdown"]
    assert "workflow.executions" in invoices_b[0]["breakdown"]
    assert "api.requests" not in invoices_b[0]["breakdown"]


def test_usage_overage_is_applied_to_invoice_total() -> None:
    suffix = uuid4().hex[:8]
    with UnitOfWork() as uow:
        tenant = uow.tenant_repository.create_tenant(f"bill-overage-{suffix}", f"Billing Overage {suffix}", conn=uow.conn)
        tenant_id = int(tenant["tenant_id"])
        plan_code = f"plan-overage-{suffix}"
        uow.billing_repository.create_plan(
            code=plan_code,
            name=f"Plan Overage {suffix}",
            price_cents=5000,
            features={"core": True},
            limits={
                "included_api_requests": 5,
                "overage_cents_api_requests": 2,
                "included_workflow_executions": 0,
                "overage_cents_workflow_executions": 0,
                "included_notification_dispatch": 0,
                "overage_cents_notification_dispatch": 0,
            },
            conn=uow.conn,
        )
        uow.billing_repository.assign_subscription(tenant_id, plan_code, conn=uow.conn)

    period_key = "2026-03"
    billing_service.increment_usage(tenant_id, "api.requests", 9, period_key=period_key)
    jobs_service.enqueue_job(
        tenant_id,
        "billing.generate_invoice",
        {"tenant_id": tenant_id, "period_key": period_key},
        max_retries=0,
    )

    outcome = PlatformJobWorker(batch_size=5).run_once()
    assert outcome["succeeded"] == 1

    with UnitOfWork() as uow:
        invoices = uow.invoice_repository.list_for_tenant(tenant_id, conn=uow.conn)

    assert len(invoices) == 1
    invoice = invoices[0]
    assert int(invoice["usage_amount_cents"]) == 8
    assert int(invoice["total_amount_cents"]) == 5008


def test_billing_pipeline_keeps_analytics_usage_metrics_in_invoice_breakdown() -> None:
    suffix = uuid4().hex[:8]
    tenant_id, _ = _seed_tenant_with_plan(suffix=suffix, price_cents=4200)
    period_key = "2026-04"

    billing_service.increment_usage(tenant_id, "analytics.events.read", 3, period_key=period_key)
    billing_service.increment_usage(tenant_id, "analytics.kpi.read", 2, period_key=period_key)

    jobs_service.enqueue_job(
        tenant_id,
        "billing.generate_invoice",
        {"tenant_id": tenant_id, "period_key": period_key},
        max_retries=0,
    )

    outcome = PlatformJobWorker(batch_size=5).run_once()
    assert outcome["succeeded"] == 1

    with UnitOfWork() as uow:
        invoices = uow.invoice_repository.list_for_tenant(tenant_id, conn=uow.conn)

    assert len(invoices) == 1
    invoice = invoices[0]
    breakdown = dict(invoice["breakdown"])
    assert int(invoice["base_amount_cents"]) == 4200
    assert int(invoice["usage_amount_cents"]) == 0
    assert int(invoice["total_amount_cents"]) == 4200
    assert int(breakdown["analytics.events.read"]) == 3
    assert int(breakdown["analytics.kpi.read"]) == 2


def test_rollover_event_writes_single_outbox_event_under_idempotency() -> None:
    suffix = uuid4().hex[:8]
    tenant_id, plan_code = _seed_tenant_with_plan(suffix=suffix)
    payload = {"tenant_id": tenant_id, "period_key": "2026-03", "plan_code": plan_code}

    first = jobs_service.enqueue_job(tenant_id, "billing.rollover_event", payload, max_retries=0)
    second = jobs_service.enqueue_job(tenant_id, "billing.rollover_event", payload, max_retries=0)

    outcome = PlatformJobWorker(batch_size=10).run_once()
    assert outcome["succeeded"] == 2

    first_job = jobs_service.get_job(int(first["id"]))
    second_job = jobs_service.get_job(int(second["id"]))
    assert first_job is not None and second_job is not None
    assert int(first_job["result"]["outbox_event_id"]) == int(second_job["result"]["outbox_event_id"])

    with UnitOfWork() as uow:
        outbox_events = uow.outbox_event_repository.list_for_tenant(tenant_id=tenant_id, limit=10, conn=uow.conn)

    assert len(outbox_events) == 1
    assert str(outbox_events[0]["event_type"]) == "billing.rollover.completed"


def test_invoice_created_metric_counts_only_new_invoice() -> None:
    suffix = uuid4().hex[:8]
    tenant_id, _ = _seed_tenant_with_plan(suffix=suffix, price_cents=3000)
    period_key = "2026-03"

    jobs_service.enqueue_job(
        tenant_id,
        "billing.generate_invoice",
        {"tenant_id": tenant_id, "period_key": period_key},
        max_retries=0,
    )
    jobs_service.enqueue_job(
        tenant_id,
        "billing.generate_invoice",
        {"tenant_id": tenant_id, "period_key": period_key},
        max_retries=0,
    )

    outcome = PlatformJobWorker(batch_size=10).run_once()
    assert outcome["succeeded"] == 2

    metrics = render_metrics()
    assert "invoices_created_total 1" in metrics


def test_platform_jobs_enqueue_does_not_depend_on_module_tenant_lookup(monkeypatch) -> None:
    suffix = uuid4().hex[:8]
    tenant_id, _ = _seed_tenant_with_plan(suffix=suffix, price_cents=3000)

    # Simulate module tenant lookup being unavailable; platform jobs path must stay operational.
    monkeypatch.setattr("app.modules.tenants.service.get_tenant", lambda _tenant_id: None)

    queued = jobs_service.enqueue_job(
        tenant_id,
        "billing.generate_invoice",
        {"tenant_id": tenant_id, "period_key": "2026-03"},
        max_retries=0,
    )
    assert int(queued["tenant_id"]) == tenant_id
    assert str(queued["job_type"]) == "billing.generate_invoice"


def test_platform_jobs_enqueue_uses_platform_subscription_without_legacy_fallback(monkeypatch) -> None:
    suffix = uuid4().hex[:8]
    tenant_id, _ = _seed_tenant_with_plan(suffix=suffix, price_cents=3000)

    def _legacy_should_not_run(_tenant_id: int, *, action: str) -> None:
        raise AssertionError(f"unexpected legacy compatibility path for action={action}")

    monkeypatch.setattr(
        "app.platform.jobs.legacy_billing_compat.assert_legacy_billing_write_allowed",
        _legacy_should_not_run,
    )

    queued = jobs_service.enqueue_job(
        tenant_id,
        "billing.generate_invoice",
        {"tenant_id": tenant_id, "period_key": "2026-03"},
        max_retries=0,
    )
    assert int(queued["tenant_id"]) == tenant_id


def test_platform_subscription_suspended_blocks_jobs_without_legacy_path(monkeypatch) -> None:
    suffix = uuid4().hex[:8]
    tenant_id, _ = _seed_tenant_with_plan(suffix=suffix, price_cents=3000)

    original_get_subscription = BillingRepository.get_subscription

    def _fake_get_subscription(self, requested_tenant_id: int, *, conn=None):
        row = original_get_subscription(self, requested_tenant_id, conn=conn)
        if row is None:
            return None
        return {
            **row,
            "status": "suspended",
        }

    def _legacy_should_not_run(_tenant_id: int, *, action: str) -> None:
        raise AssertionError(f"unexpected legacy compatibility path for action={action}")

    monkeypatch.setattr(BillingRepository, "get_subscription", _fake_get_subscription)
    monkeypatch.setattr(
        "app.platform.jobs.legacy_billing_compat.assert_legacy_billing_write_allowed",
        _legacy_should_not_run,
    )

    with pytest.raises(HTTPException) as exc_info:
        jobs_service.enqueue_job(
            tenant_id,
            "billing.generate_invoice",
            {"tenant_id": tenant_id, "period_key": "2026-03"},
            max_retries=0,
        )

    assert exc_info.value.status_code == 403
    assert "billing_required" in str(exc_info.value.detail)


def test_platform_billing_service_get_subscription_reads_platform_repository_state() -> None:
    suffix = uuid4().hex[:8]
    tenant_id, plan_code = _seed_tenant_with_plan(suffix=suffix, price_cents=3000)

    subscription = billing_service.get_subscription(tenant_id)

    assert subscription is not None
    assert int(subscription["tenant_id"]) == tenant_id
    assert str(subscription["plan_code"]) == plan_code
    assert str(subscription["status"]) == "active"


def test_platform_billing_service_assign_plan_uses_platform_repository_only() -> None:
    suffix = uuid4().hex[:8]
    with UnitOfWork() as uow:
        tenant = uow.tenant_repository.create_tenant(f"assign-{suffix}", f"Assign {suffix}", conn=uow.conn)
        tenant_id = int(tenant["tenant_id"])
        plan_code = f"assign-plan-{suffix}"
        uow.billing_repository.create_plan(
            code=plan_code,
            name=f"Assign Plan {suffix}",
            price_cents=4500,
            features={"core": True},
            limits={"max_users": 50},
            conn=uow.conn,
        )

    assigned = billing_service.assign_plan(tenant_id, plan_code)

    assert int(assigned["tenant_id"]) == tenant_id
    assert str(assigned["plan_code"]) == plan_code
    assert str(assigned["status"]) == "active"

    with UnitOfWork() as uow:
        persisted = uow.billing_repository.get_subscription(tenant_id, conn=uow.conn)

    assert persisted is not None
    assert str(persisted["plan_code"]) == plan_code


def test_billing_repository_clear_state_removes_plans_subscriptions_and_usage() -> None:
    suffix = uuid4().hex[:8]
    with UnitOfWork() as uow:
        tenant = uow.tenant_repository.create_tenant(f"clear-{suffix}", f"Clear {suffix}", conn=uow.conn)
        tenant_id = int(tenant["tenant_id"])
        plan_code = f"clear-plan-{suffix}"
        uow.billing_repository.create_plan(
            code=plan_code,
            name=f"Clear Plan {suffix}",
            price_cents=5000,
            features={"core": True},
            limits={"max_users": 10},
            conn=uow.conn,
        )
        uow.billing_repository.assign_subscription(tenant_id, plan_code, conn=uow.conn)
        uow.billing_repository.increment_usage(tenant_id, "api.requests", 2, conn=uow.conn)
        uow.billing_repository.clear_state(conn=uow.conn)

        plan = uow.billing_repository.get_plan(plan_code, conn=uow.conn)
        subscription = uow.billing_repository.get_subscription(tenant_id, conn=uow.conn)

    assert plan is None
    assert subscription is None
