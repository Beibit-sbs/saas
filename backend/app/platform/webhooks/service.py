from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
import logging
from typing import Any, Callable
from urllib import request as urllib_request
from urllib.error import HTTPError, URLError

from app.modules.audit.service import log_admin_action
from app.platform.events.schemas import OutboxEventRead
from app.platform.uow import UnitOfWork
from app.platform.webhooks.repository import SHARED_WEBHOOK_REPOSITORY, WebhookRepository
from app.platform.webhooks.signer import build_webhook_signature, canonical_json_bytes


logger = logging.getLogger("app.platform.webhooks")


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _utc_iso() -> str:
    return _utc_now().isoformat()


HttpSender = Callable[[str, dict[str, str], bytes, float], tuple[int, str]]


class WebhookService:
    def __init__(
        self,
        *,
        repository: WebhookRepository | None = None,
        sender: HttpSender | None = None,
        request_timeout_seconds: float = 5.0,
        max_retry_count: int = 5,
        base_retry_seconds: int = 30,
    ) -> None:
        self._repository = repository or SHARED_WEBHOOK_REPOSITORY
        self._sender: HttpSender = sender or self._default_sender
        self._request_timeout_seconds = max(0.1, float(request_timeout_seconds))
        self._max_retry_count = max(1, int(max_retry_count))
        self._base_retry_seconds = max(1, int(base_retry_seconds))

    @staticmethod
    def _default_sender(url: str, headers: dict[str, str], body: bytes, timeout_seconds: float) -> tuple[int, str]:
        req = urllib_request.Request(url=url, data=body, headers=headers, method="POST")
        try:
            with urllib_request.urlopen(req, timeout=timeout_seconds) as response:
                response_body = response.read().decode("utf-8", errors="replace")
                return int(getattr(response, "status", 200)), response_body
        except HTTPError as exc:
            body_text = exc.read().decode("utf-8", errors="replace") if hasattr(exc, "read") else str(exc)
            return int(exc.code), body_text
        except URLError as exc:
            raise RuntimeError(f"webhook dispatch network failure: {exc.reason}") from exc

    def clear_state(self) -> None:
        self._repository.clear_state()

    def _sanitize_subscription_read(self, row: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": int(row["id"]),
            "tenant_id": int(row["tenant_id"]),
            "event_type": str(row["event_type"]),
            "target_url": str(row["target_url"]),
            "is_active": bool(row["is_active"]),
            "created_at": str(row["created_at"]),
            "updated_at": str(row["updated_at"]),
            "version": int(row["version"]),
        }

    def create_subscription(
        self,
        *,
        tenant_id: int,
        event_type: str,
        target_url: str,
        signing_secret: str,
        actor: str = "platform-admin",
    ) -> dict[str, Any]:
        with UnitOfWork() as uow:
            row = self._repository.create_subscription(
                tenant_id=int(tenant_id),
                event_type=event_type,
                target_url=target_url,
                signing_secret=signing_secret,
                conn=uow.conn,
            )
        log_admin_action(
            actor=actor,
            tenant_id=int(tenant_id),
            action="platform_core.webhook.subscription.create",
            path="/api/v1/admin/webhooks/subscriptions",
            client_ip="application-service",
            correlation_id=None,
            entity="platform-webhook",
            result="success",
            metadata={"subscription_id": int(row["id"]), "event_type": str(row["event_type"])},
        )
        return self._sanitize_subscription_read(row)

    def list_subscriptions(self, *, tenant_id: int, event_type: str | None = None, active_only: bool = False, limit: int = 200) -> list[dict[str, Any]]:
        with UnitOfWork() as uow:
            rows = self._repository.list_subscriptions(
                tenant_id=int(tenant_id),
                event_type=event_type,
                active_only=active_only,
                limit=limit,
                conn=uow.conn,
            )
        return [self._sanitize_subscription_read(item) for item in rows]

    def deactivate_subscription(self, *, subscription_id: int, actor: str = "platform-admin") -> dict[str, Any]:
        with UnitOfWork() as uow:
            row = self._repository.deactivate_subscription(int(subscription_id), conn=uow.conn)
        if row is None:
            raise ValueError(f"webhook subscription {subscription_id} not found")
        log_admin_action(
            actor=actor,
            tenant_id=int(row["tenant_id"]),
            action="platform_core.webhook.subscription.deactivate",
            path=f"/api/v1/admin/webhooks/subscriptions/{int(subscription_id)}/deactivate",
            client_ip="application-service",
            correlation_id=None,
            entity="platform-webhook",
            result="success",
            metadata={"subscription_id": int(subscription_id)},
        )
        return self._sanitize_subscription_read(row)

    def list_deliveries(self, *, tenant_id: int, limit: int = 200) -> list[dict[str, Any]]:
        with UnitOfWork() as uow:
            return self._repository.list_deliveries(tenant_id=int(tenant_id), limit=limit, conn=uow.conn)

    def _build_outbox_payload(self, event: OutboxEventRead) -> dict[str, Any]:
        return {
            "id": int(event.id),
            "tenant_id": int(event.tenant_id),
            "event_type": str(event.event_type),
            "aggregate_type": str(event.aggregate_type),
            "aggregate_id": str(event.aggregate_id),
            "payload": dict(event.payload_json),
            "created_at": str(event.created_at),
            "correlation_id": event.correlation_id,
            "causation_id": event.causation_id,
        }

    def _retry_at_for(self, retry_count: int) -> datetime:
        exponent = min(max(0, int(retry_count)), 10)
        return _utc_now() + timedelta(seconds=self._base_retry_seconds * (2**exponent))

    def _dispatch_once(
        self,
        *,
        subscription: dict[str, Any],
        event: OutboxEventRead,
        retry_count: int,
        uow: UnitOfWork,
    ) -> dict[str, Any]:
        if self._repository.has_delivered_event(
            subscription_id=int(subscription["id"]),
            outbox_event_id=int(event.id),
            conn=uow.conn,
        ):
            return {
                "tenant_id": int(subscription["tenant_id"]),
                "subscription_id": int(subscription["id"]),
                "outbox_event_id": int(event.id),
                "delivery_status": "delivered",
                "response_status_code": 208,
                "response_body": "duplicate delivery suppressed",
                "retry_count": int(retry_count),
            }

        payload = self._build_outbox_payload(event)
        payload_bytes = canonical_json_bytes(payload)
        headers = build_webhook_signature(payload_bytes, signing_secret=str(subscription["signing_secret"]))
        headers["User-Agent"] = "ai-platform-webhook/1.0"

        delivery = self._repository.create_delivery_attempt(
            tenant_id=int(subscription["tenant_id"]),
            subscription_id=int(subscription["id"]),
            outbox_event_id=int(event.id),
            event_type=str(event.event_type),
            target_url=str(subscription["target_url"]),
            request_payload_json={"payload": payload, "headers": headers},
            retry_count=max(0, int(retry_count)),
            conn=uow.conn,
        )

        status_code: int | None = None
        response_body: str | None = None
        status = "failed"
        last_error: str | None = None
        next_retry_at: datetime | None = None

        try:
            status_code, response_body = self._sender(
                str(subscription["target_url"]),
                headers,
                payload_bytes,
                self._request_timeout_seconds,
            )
            if 200 <= int(status_code) < 300:
                status = "delivered"
            else:
                status = "failed"
                last_error = f"non-success status code: {status_code}"
                if int(retry_count) < self._max_retry_count:
                    next_retry_at = self._retry_at_for(int(retry_count))
        except Exception as exc:
            status = "failed"
            last_error = str(exc)
            response_body = str(exc)
            if int(retry_count) < self._max_retry_count:
                next_retry_at = self._retry_at_for(int(retry_count))

        finalized = self._repository.finalize_delivery_attempt(
            int(delivery["id"]),
            delivery_status=status,
            response_status_code=status_code,
            response_body=response_body,
            next_retry_at=next_retry_at,
            last_error=last_error,
            conn=uow.conn,
        )
        if finalized is None:
            raise RuntimeError("webhook delivery finalization failed")
        
        # Log retry exhaustion or success
        if str(status) == "delivered":
            logger.info(
                "webhook_delivery_succeeded",
                extra={
                    "subscription_id": subscription.get("id"),
                    "event_id": event.id,
                    "event_type": event.event_type,
                    "target_url": subscription.get("target_url"),
                    "retry_count": int(retry_count),
                },
            )
        elif next_retry_at is None and str(status) == "failed":
            logger.error(
                "webhook_delivery_exhausted",
                extra={
                    "subscription_id": subscription.get("id"),
                    "event_id": event.id,
                    "event_type": event.event_type,
                    "target_url": subscription.get("target_url"),
                    "retry_count": int(retry_count),
                    "max_retries": self._max_retry_count,
                    "last_error": last_error,
                    "last_status_code": status_code,
                },
            )
        
        return finalized

    def dispatch_event_to_subscriptions(
        self,
        *,
        event: OutboxEventRead,
        uow: UnitOfWork,
    ) -> dict[str, Any]:
        subscriptions = self._repository.list_subscriptions(
            tenant_id=int(event.tenant_id),
            event_type=str(event.event_type),
            active_only=True,
            conn=uow.conn,
        )

        attempted = 0
        delivered = 0
        failed = 0

        for subscription in subscriptions:
            attempted += 1
            result = self._dispatch_once(
                subscription=subscription,
                event=event,
                retry_count=0,
                uow=uow,
            )
            if str(result["delivery_status"]) == "delivered":
                delivered += 1
            else:
                failed += 1

        return {
            "attempted": attempted,
            "delivered": delivered,
            "failed": failed,
            "event_type": str(event.event_type),
            "tenant_id": int(event.tenant_id),
        }

    def retry_failed_deliveries(self, *, limit: int = 100, actor: str = "platform-system") -> dict[str, int]:
        attempted = 0
        delivered = 0
        failed = 0

        with UnitOfWork() as uow:
            rows = self._repository.fetch_retryable_deliveries(
                as_of=_utc_now(),
                limit=limit,
                max_retry_count=self._max_retry_count,
                conn=uow.conn,
            )
            for row in rows:
                attempted += 1
                subscription = self._repository.get_subscription(int(row["subscription_id"]), conn=uow.conn)
                if subscription is None or not bool(subscription.get("is_active")):
                    failed += 1
                    self._repository.finalize_delivery_attempt(
                        int(row["id"]),
                        delivery_status="failed",
                        response_status_code=row.get("response_status_code"),
                        response_body=row.get("response_body"),
                        next_retry_at=None,
                        last_error="subscription missing or inactive",
                        conn=uow.conn,
                    )
                    continue

                outbox_event = uow.outbox_event_repository.get(int(row["outbox_event_id"]), conn=uow.conn)
                if outbox_event is None:
                    failed += 1
                    self._repository.finalize_delivery_attempt(
                        int(row["id"]),
                        delivery_status="failed",
                        response_status_code=row.get("response_status_code"),
                        response_body=row.get("response_body"),
                        next_retry_at=None,
                        last_error="outbox event missing",
                        conn=uow.conn,
                    )
                    continue

                event = OutboxEventRead.model_validate(outbox_event)
                retry_result = self._dispatch_once(
                    subscription=subscription,
                    event=event,
                    retry_count=int(row.get("retry_count", 0)) + 1,
                    uow=uow,
                )
                if str(retry_result["delivery_status"]) == "delivered":
                    delivered += 1
                else:
                    failed += 1

        log_admin_action(
            actor=actor,
            tenant_id=1,
            action="platform_core.webhook.delivery.retry",
            path="/api/v1/internal/webhooks/retry-failed",
            client_ip="application-service",
            correlation_id=None,
            entity="platform-webhook",
            result="success",
            metadata={"attempted": attempted, "delivered": delivered, "failed": failed},
        )
        return {"attempted": attempted, "delivered": delivered, "failed": failed}


webhook_service = WebhookService()


def clear_webhook_state() -> None:
    webhook_service.clear_state()