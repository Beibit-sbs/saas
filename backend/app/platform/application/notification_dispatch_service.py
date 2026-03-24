from __future__ import annotations

from threading import Lock
from typing import Any

from app.modules.audit.service import log_admin_action
from app.platform.idempotency.service import IdempotencyService
from app.platform.uow import UnitOfWork


class NotificationDispatchService:
    def __init__(self) -> None:
        self._idempotency = IdempotencyService()
        self._fail_once_lock = Lock()
        self._failed_once_tokens: set[str] = set()

    def _send(self, *, channel: str, target: str, payload: dict[str, Any]) -> dict[str, Any]:
        normalized_channel = channel.strip().lower()
        if normalized_channel not in {"email", "in_app", "webhook"}:
            raise ValueError("unsupported notification channel")

        fail_once_token = str(payload.get("fail_once_token", "")).strip()
        if fail_once_token:
            with self._fail_once_lock:
                if fail_once_token not in self._failed_once_tokens:
                    self._failed_once_tokens.add(fail_once_token)
                    raise RuntimeError("simulated transient delivery failure")

        if bool(payload.get("force_fail")):
            raise RuntimeError("simulated delivery failure")

        if "fail" in target.lower():
            raise RuntimeError("delivery target refused")

        return {"delivered": True, "channel": normalized_channel, "target": target}

    def dispatch(
        self,
        *,
        tenant_id: int,
        channel: str,
        target: str,
        payload: dict[str, Any],
        subject: str | None = None,
        actor: str = "platform-system",
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        normalized_tenant_id = int(tenant_id)
        normalized_channel = channel.strip().lower()
        normalized_target = target.strip()

        request_payload = {
            "tenant_id": normalized_tenant_id,
            "channel": normalized_channel,
            "target": normalized_target,
            "subject": subject,
            "payload": payload,
        }

        def _execute(uow: UnitOfWork) -> dict[str, Any]:
            row = uow.notification_repository.dispatch(
                tenant_id=normalized_tenant_id,
                channel=normalized_channel,
                target=normalized_target,
                payload=payload,
                subject=subject,
                conn=uow.conn,
            )

            try:
                delivery = self._send(channel=normalized_channel, target=normalized_target, payload=payload)
                final = uow.notification_repository.mark_status(
                    int(row["id"]),
                    status="sent",
                    last_error=None,
                    increment_retry=False,
                    conn=uow.conn,
                )
                response = {
                    "notification_id": int(row["id"]),
                    "status": "sent",
                    "delivery": delivery,
                    "record": final or row,
                }
                log_admin_action(
                    actor=actor,
                    tenant_id=normalized_tenant_id,
                    action="platform_core.notification.dispatch",
                    path="/api/v1/admin/notifications",
                    client_ip="application-service",
                    correlation_id=None,
                    entity="platform-core",
                    result="success",
                    metadata={"notification_id": int(row["id"]), "channel": normalized_channel},
                )
                return response
            except Exception as exc:
                failed = uow.notification_repository.mark_status(
                    int(row["id"]),
                    status="failed",
                    last_error=str(exc),
                    increment_retry=True,
                    conn=uow.conn,
                )
                response = {
                    "notification_id": int(row["id"]),
                    "status": "failed",
                    "error": str(exc),
                    "record": failed or row,
                }
                log_admin_action(
                    actor=actor,
                    tenant_id=normalized_tenant_id,
                    action="platform_core.notification.dispatch",
                    path="/api/v1/admin/notifications",
                    client_ip="application-service",
                    correlation_id=None,
                    entity="platform-core",
                    result="failed",
                    metadata={"notification_id": int(row["id"]), "channel": normalized_channel, "error": str(exc)},
                )
                return response

        if idempotency_key:
            result = self._idempotency.execute(
                tenant_id=normalized_tenant_id,
                key=idempotency_key,
                operation="notification_dispatch",
                request_payload=request_payload,
                executor=_execute,
            )
            return {**result.response, "idempotent_replay": result.replayed}

        with UnitOfWork() as uow:
            return _execute(uow)

    def retry_failed_deliveries(self, *, limit: int = 100, actor: str = "platform-system") -> dict[str, int]:
        attempted = 0
        succeeded = 0
        failed = 0

        with UnitOfWork() as uow:
            rows = uow.notification_repository.list_by_status("failed", limit=limit, conn=uow.conn)
            for row in rows:
                attempted += 1
                try:
                    self._send(
                        channel=str(row["channel"]),
                        target=str(row["target"]),
                        payload=dict(row.get("payload") or {}),
                    )
                    uow.notification_repository.mark_status(
                        int(row["id"]),
                        status="sent",
                        last_error=None,
                        increment_retry=False,
                        conn=uow.conn,
                    )
                    succeeded += 1
                except Exception as exc:
                    uow.notification_repository.mark_status(
                        int(row["id"]),
                        status="failed",
                        last_error=str(exc),
                        increment_retry=True,
                        conn=uow.conn,
                    )
                    failed += 1

        log_admin_action(
            actor=actor,
            tenant_id=1,
            action="platform_core.notification.retry",
            path="/api/v1/internal/scheduler/run-once",
            client_ip="application-service",
            correlation_id=None,
            entity="platform-core",
            result="success",
            metadata={"attempted": attempted, "succeeded": succeeded, "failed": failed},
        )
        return {"attempted": attempted, "succeeded": succeeded, "failed": failed}
