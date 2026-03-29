from __future__ import annotations

import logging
import threading
import time
from typing import Any, Callable

from app.modules.audit.service import log_admin_action
from app.modules.observability.alerts import observe_job_failure_spike
from app.modules.observability.metrics import observe_billing_failure, observe_invoice_created, observe_job_execution
from app.platform.idempotency.service import IdempotencyService
from app.platform.runtime_state import record_worker_heartbeat
from app.platform.jobs import service as jobs_service
from app.platform.uow import UnitOfWork

logger = logging.getLogger("app.platform.worker")


class PlatformJobWorker:
    def __init__(
        self,
        handlers: dict[str, Callable[[dict], dict]] | None = None,
        poll_interval_seconds: float = 1.0,
        batch_size: int = 20,
    ) -> None:
        self._handlers = {str(k).strip().lower(): v for k, v in (handlers or {}).items()}
        self._poll_interval_seconds = max(0.05, float(poll_interval_seconds))
        self._batch_size = max(1, int(batch_size))
        self._idempotency = IdempotencyService()

        self._default_handlers: dict[str, Callable[[dict[str, Any]], dict[str, Any]]] = {
            "billing.generate_invoice": self._handle_billing_generate_invoice,
            "billing.rollover_event": self._handle_billing_rollover_event,
        }

    @staticmethod
    def _metric_token(metric: str) -> str:
        return str(metric or "").strip().lower().replace(".", "_")

    @classmethod
    def _limit_value(cls, limits: dict[str, Any], metric: str, kind: str, default: int = 0) -> int:
        token = cls._metric_token(metric)
        candidates = (
            f"{kind}.{metric}",
            f"{kind}_{token}",
            f"{token}_{kind}",
        )
        for key in candidates:
            if key in limits:
                value = int(limits[key])
                if value < 0:
                    raise ValueError(f"plan limit '{key}' must be non-negative")
                return value
        return int(default)

    @classmethod
    def _compute_usage_amount_cents(cls, plan: dict[str, Any], breakdown: dict[str, int]) -> int:
        limits = dict(plan.get("limits") or {})
        usage_amount_cents = 0
        for metric, value in breakdown.items():
            used = int(value)
            included = cls._limit_value(limits, metric, "included", default=0)
            overage_rate_cents = cls._limit_value(limits, metric, "overage_cents", default=0)
            overage_units = max(0, used - included)
            usage_amount_cents += overage_units * overage_rate_cents
        return usage_amount_cents

    def _handler_for(self, job_type: str) -> Callable[[dict[str, Any]], dict[str, Any]]:
        normalized_job_type = str(job_type or "").strip().lower()
        if normalized_job_type in self._handlers:
            return self._handlers[normalized_job_type]
        if normalized_job_type in self._default_handlers:
            return self._default_handlers[normalized_job_type]
        raise ValueError(f"unsupported job_type: {normalized_job_type}")

    def _handle_billing_rollover_event(self, payload: dict[str, Any]) -> dict[str, Any]:
        tenant_id = int(payload.get("tenant_id") or 0)
        period_key = str(payload.get("period_key") or "").strip().lower()
        plan_code = str(payload.get("plan_code") or "").strip().lower()

        if tenant_id <= 0:
            raise ValueError("billing.rollover_event requires positive tenant_id")
        if not period_key:
            raise ValueError("billing.rollover_event requires period_key")
        if not plan_code:
            raise ValueError("billing.rollover_event requires plan_code")

        idem_key = f"billing-rollover-event:{period_key}:{plan_code}"

        def _execute(uow: UnitOfWork) -> dict[str, Any]:
            event = uow.outbox_event_repository.enqueue(
                tenant_id=tenant_id,
                event_type="billing.rollover.completed",
                aggregate_type="billing",
                aggregate_id=f"{tenant_id}:{period_key}",
                payload_json={
                    "tenant_id": tenant_id,
                    "period_key": period_key,
                    "plan_code": plan_code,
                },
                conn=uow.conn,
            )
            return {
                "tenant_id": tenant_id,
                "period_key": period_key,
                "plan_code": plan_code,
                "outbox_event_id": int(event["id"]),
            }

        result = self._idempotency.execute(
            tenant_id=tenant_id,
            key=idem_key,
            operation="billing_rollover_event",
            request_payload={"tenant_id": tenant_id, "period_key": period_key, "plan_code": plan_code},
            executor=_execute,
        )

        logger.info(
            "billing_rollover_event_recorded",
            extra={
                "tenant_id": tenant_id,
                "period_key": period_key,
                "plan_code": plan_code,
                "replayed": bool(result.replayed),
            },
        )
        response = dict(result.response)
        response["replayed"] = bool(result.replayed)
        return response

    def _handle_billing_generate_invoice(self, payload: dict[str, Any]) -> dict[str, Any]:
        tenant_id = int(payload.get("tenant_id") or 0)
        period_key = str(payload.get("period_key") or "").strip().lower()

        if tenant_id <= 0:
            raise ValueError("billing.generate_invoice requires positive tenant_id")
        if not period_key:
            raise ValueError("billing.generate_invoice requires period_key")

        with UnitOfWork() as uow:
            subscription = uow.billing_repository.get_subscription(tenant_id, conn=uow.conn)
            if subscription is None:
                raise ValueError(f"active subscription not found for tenant {tenant_id}")

            plan_code = str(subscription.get("plan_code") or "").strip().lower()
            plan = uow.billing_repository.get_plan(plan_code, conn=uow.conn)
            if plan is None:
                raise ValueError(f"plan '{plan_code}' not found for tenant {tenant_id}")

            usage_rows = uow.usage_repository.list_for_tenant_period(tenant_id, period_key=period_key, conn=uow.conn)
            breakdown = {str(item.get("metric", "")): int(item.get("value", 0)) for item in usage_rows}

            base_amount_cents = int(plan.get("price_cents", 0))
            usage_amount_cents = self._compute_usage_amount_cents(plan, breakdown)

            invoice, created = uow.invoice_repository.create_or_get(
                tenant_id=tenant_id,
                period_key=period_key,
                plan_code=plan_code,
                base_amount_cents=base_amount_cents,
                usage_amount_cents=usage_amount_cents,
                breakdown=breakdown,
                conn=uow.conn,
            )

        if created:
            observe_invoice_created()

        logger.info(
            "billing_invoice_generated",
            extra={
                "tenant_id": tenant_id,
                "invoice_id": int(invoice["id"]),
                "amount_cents": int(invoice["total_amount_cents"]),
                "period_key": period_key,
                "invoice_created": bool(created),
            },
        )

        return {
            "tenant_id": tenant_id,
            "invoice_id": int(invoice["id"]),
            "period_key": period_key,
            "amount_cents": int(invoice["total_amount_cents"]),
            "created": bool(created),
        }

    def run_once(self) -> dict[str, int]:
        record_worker_heartbeat()
        queued = jobs_service.fetch_queued_jobs(limit=self._batch_size)
        processed = 0
        succeeded = 0
        retried = 0
        failed = 0

        for job in queued:
            processed += 1
            job_id = int(job["id"])
            tenant_id = int(job["tenant_id"])
            job_type = str(job["job_type"]).strip().lower()

            started = jobs_service.mark_job_running(job_id)
            if started is None:
                # Another worker or manual operation might have moved state.
                continue

            try:
                handler = self._handler_for(job_type)
                result = handler(dict(job.get("payload") or {}))
                completed = jobs_service.mark_job_succeeded(job_id, result)
                if completed is None:
                    raise RuntimeError("job transition to succeeded failed")
                logger.info("platform_job_succeeded", extra={"job_id": job_id, "job_type": job_type})
                log_admin_action(
                    actor="platform-worker",
                    tenant_id=tenant_id,
                    action="platform_core.jobs.succeeded",
                    path="/api/v1/internal/worker/run-once",
                    client_ip="worker",
                    correlation_id=None,
                    entity="platform-core",
                    result="success",
                    metadata={"job_id": job_id, "job_type": job_type, "status": completed["status"]},
                )
                observe_job_execution(outcome="success")
                succeeded += 1
            except Exception as exc:
                current = jobs_service.get_job(job_id)
                retry_count = int(current.get("retry_count", 0)) if current else 0
                max_retries = int(current.get("max_retries", 0)) if current else 0
                if retry_count < max_retries:
                    jobs_service.requeue_job(job_id, str(exc))
                    retried += 1
                    outcome = "retry"
                else:
                    jobs_service.mark_job_failed(job_id, str(exc))
                    failed += 1
                    outcome = "failed"

                logger.exception("platform_job_failed", extra={"job_id": job_id, "job_type": job_type, "outcome": outcome})
                log_admin_action(
                    actor="platform-worker",
                    tenant_id=tenant_id,
                    action="platform_core.jobs.failed",
                    path="/api/v1/internal/worker/run-once",
                    client_ip="worker",
                    correlation_id=None,
                    entity="platform-core",
                    result=outcome,
                    metadata={"job_id": job_id, "job_type": job_type, "error": str(exc)},
                )
                if outcome == "failed":
                    observe_job_execution(outcome="failed")
                    observe_job_failure_spike(job_type=job_type)
                    if job_type.startswith("billing."):
                        observe_billing_failure()

        return {"processed": processed, "succeeded": succeeded, "retried": retried, "failed": failed}

    def run_forever(self, stop_event: threading.Event | None = None) -> None:
        event = stop_event or threading.Event()
        while not event.is_set():
            record_worker_heartbeat()
            self.run_once()
            time.sleep(self._poll_interval_seconds)


worker = PlatformJobWorker()
