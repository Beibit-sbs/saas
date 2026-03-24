from __future__ import annotations

from datetime import datetime, timedelta, timezone
import logging
import uuid
from typing import Sequence

from app.modules.audit.service import log_admin_action
from app.modules.observability.logging import bind_log_context, reset_log_context
from app.platform.events.handlers import AnalyticsEventHandler, AutomationEventHandler, ContextProjectionHandler, EventHandler, NotificationEventHandler, WebhookEventHandler
from app.platform.events.schemas import OutboxEventRead
from app.platform.uow import UnitOfWork


logger = logging.getLogger("app.platform.outbox")


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class OutboxEventWorker:
    def __init__(
        self,
        handlers: Sequence[EventHandler] | None = None,
        *,
        batch_size: int = 20,
        max_retry_count: int = 5,
        retry_delay_seconds: float = 30.0,
    ) -> None:
        self._handlers = list(handlers or [
            NotificationEventHandler(),
            WebhookEventHandler(),
            AnalyticsEventHandler(),
            AutomationEventHandler(),
            ContextProjectionHandler(),
        ])
        self._batch_size = max(1, int(batch_size))
        self._max_retry_count = max(1, int(max_retry_count))
        self._retry_delay_seconds = max(0.0, float(retry_delay_seconds))

    def run_once(self) -> dict[str, int]:
        with UnitOfWork() as uow:
            candidates = uow.outbox_event_repository.fetch_processible(
                limit=self._batch_size,
                max_retry_count=self._max_retry_count,
                as_of=_utc_now(),
                conn=uow.conn,
            )

        processed = 0
        succeeded = 0
        retried = 0
        failed = 0

        for candidate in candidates:
            processed += 1
            event_id = int(candidate["id"])
            tenant_id = int(candidate["tenant_id"])

            with UnitOfWork() as uow:
                started = uow.outbox_event_repository.mark_processing(event_id, conn=uow.conn)
                if started is None:
                    continue

                event = OutboxEventRead.model_validate(started)
                # Extract trace_id from event payload (injected by EventPublisher)
                trace_id_from_event = event.payload_json.get("trace_id") if event.payload_json else None
                log_tokens = bind_log_context(
                    request_id=event.correlation_id or f"outbox-{event.id}-{uuid.uuid4().hex[:8]}",
                    trace_id=trace_id_from_event,
                    tenant_id=event.tenant_id,
                    actor_id="platform-outbox-worker",
                )
                try:
                    for handler in self._handlers:
                        idempotency_key = f"event:{event.id}:handler:{handler.name}"
                        existing = uow.idempotency_repository.get(
                            int(event.tenant_id),
                            idempotency_key,
                            "event_processing",
                            conn=uow.conn,
                        )
                        if existing is not None and str(existing.get("status", "")).lower() == "completed":
                            continue
                        uow.idempotency_repository.create_pending(
                            int(event.tenant_id),
                            idempotency_key,
                            "event_processing",
                            request_hash=str(event.id),
                            conn=uow.conn,
                        )
                        try:
                            handler_result = handler.handle(event, uow=uow)
                            uow.idempotency_repository.complete(
                                int(event.tenant_id),
                                idempotency_key,
                                "event_processing",
                                {"handler": handler.name, "result": handler_result},
                                conn=uow.conn,
                            )
                        except Exception as handler_exc:
                            uow.idempotency_repository.fail(
                                int(event.tenant_id),
                                idempotency_key,
                                "event_processing",
                                {"handler": handler.name, "error": str(handler_exc)},
                                conn=uow.conn,
                            )
                            raise
                    completed = uow.outbox_event_repository.mark_processed(event_id, conn=uow.conn)
                    if completed is None:
                        raise RuntimeError("outbox event transition to processed failed")
                    logger.info("outbox_event_processed", extra={"event_id": event_id, "event_type": event.event_type})
                    log_admin_action(
                        actor="platform-outbox-worker",
                        tenant_id=tenant_id,
                        action="platform_core.events.processed",
                        path="/api/v1/internal/events/outbox/run-once",
                        client_ip="worker",
                        correlation_id=event.correlation_id,
                        entity="platform-outbox",
                        result="success",
                        metadata={"event_id": event_id, "event_type": event.event_type},
                    )
                    succeeded += 1
                except Exception as exc:
                    next_available_at = _utc_now() + timedelta(seconds=self._retry_delay_seconds * (2 ** int(event.retry_count)))
                    failed_row = uow.outbox_event_repository.mark_failed(
                        event_id,
                        error=str(exc),
                        next_available_at=next_available_at,
                        conn=uow.conn,
                    )
                    terminal = int(event.retry_count) + 1 >= self._max_retry_count or failed_row is None
                    if terminal:
                        failed += 1
                        logger.error(
                            "outbox_event_dead_lettered",
                            extra={
                                "event_id": event_id,
                                "event_type": event.event_type,
                                "retry_count": int(event.retry_count),
                                "max_retries": self._max_retry_count,
                                "error": str(exc),
                            },
                        )
                    else:
                        retried += 1
                    logger.exception(
                        "outbox_event_failed",
                        extra={"event_id": event_id, "event_type": event.event_type, "terminal": terminal},
                    )
                    log_admin_action(
                        actor="platform-outbox-worker",
                        tenant_id=tenant_id,
                        action="platform_core.events.failed",
                        path="/api/v1/internal/events/outbox/run-once",
                        client_ip="worker",
                        correlation_id=event.correlation_id,
                        entity="platform-outbox",
                        result="failed" if terminal else "retry",
                        metadata={"event_id": event_id, "event_type": event.event_type, "error": str(exc)},
                    )
                finally:
                    reset_log_context(log_tokens)

        return {"processed": processed, "succeeded": succeeded, "retried": retried, "failed": failed}


outbox_worker = OutboxEventWorker()