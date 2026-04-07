from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.modules.audit.service import log_admin_action
from app.platform.idempotency.service import IdempotencyService
from app.platform.uow import UnitOfWork


class SubscriptionRolloverService:
    def __init__(self) -> None:
        self._idempotency = IdempotencyService()

    def run_rollover_cycle(
        self,
        *,
        due_age_seconds: int = 30 * 24 * 60 * 60,
        max_tenants: int = 100,
        actor: str = "platform-scheduler",
    ) -> dict[str, int]:
        with UnitOfWork() as uow:
            due = uow.billing_repository.list_due_subscriptions(
                due_age_seconds=due_age_seconds,
                limit=max_tenants,
                conn=uow.conn,
            )

        processed = 0
        replayed = 0
        failed = 0

        period_key = datetime.now(timezone.utc).strftime("%Y-%m")
        for item in due:
            tenant_id = int(item["tenant_id"])
            plan_code = str(item["plan_code"])
            idem_key = f"subscription-rollover:{tenant_id}:{period_key}:{plan_code}"
            request_payload = {
                "tenant_id": tenant_id,
                "plan_code": plan_code,
                "period_key": period_key,
            }

            def _execute(uow: UnitOfWork) -> dict[str, Any]:
                next_subscription = uow.billing_repository.assign_subscription(tenant_id, plan_code, conn=uow.conn)

                # New billing period and usage reset by opening period-specific counters.
                metrics = ["api.requests", "workflow.executions", "notification.dispatch"]
                for metric in metrics:
                    uow.usage_repository.initialize(tenant_id, metric, period_key=period_key, conn=uow.conn)

                billing_event_job = uow.job_repository.enqueue(
                    tenant_id=tenant_id,
                    job_type="billing.rollover_event",
                    payload={"tenant_id": tenant_id, "period_key": period_key, "plan_code": plan_code},
                    max_retries=3,
                    conn=uow.conn,
                )
                invoice_job = uow.job_repository.enqueue(
                    tenant_id=tenant_id,
                    job_type="billing.generate_invoice",
                    payload={"tenant_id": tenant_id, "period_key": period_key},
                    max_retries=3,
                    conn=uow.conn,
                )

                log_admin_action(
                    actor=actor,
                    tenant_id=tenant_id,
                    action="platform_core.billing.rollover",
                    path="/api/v1/internal/scheduler/run-once",
                    client_ip="application-service",
                    correlation_id=None,
                    entity="platform-core",
                    result="success",
                    metadata={
                        "period_key": period_key,
                        "plan_code": plan_code,
                        "billing_event_job_id": int(billing_event_job["id"]),
                        "invoice_job_id": int(invoice_job["id"]),
                    },
                )

                return {
                    "tenant_id": tenant_id,
                    "period_key": period_key,
                    "subscription": next_subscription,
                    "jobs": [int(billing_event_job["id"]), int(invoice_job["id"])],
                }

            try:
                result = self._idempotency.execute(
                    tenant_id=tenant_id,
                    key=idem_key,
                    operation="subscription_rollover",
                    request_payload=request_payload,
                    executor=_execute,
                )
                if result.replayed:
                    replayed += 1
                else:
                    processed += 1
            except Exception:
                failed += 1

        return {"processed": processed, "replayed": replayed, "failed": failed}
