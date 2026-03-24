from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.platform.events.models import OutboxEventModel
from app.platform.events.repository import OutboxEventRepository
from app.platform.uow import UnitOfWork


def _normalize_datetime(value: datetime | None) -> datetime:
    if value is None:
        return datetime.now(timezone.utc)
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _model_to_api(model: OutboxEventModel) -> dict[str, Any]:
    return {
        "id": int(model.id),
        "tenant_id": int(model.tenant_id),
        "event_type": str(model.event_type),
        "aggregate_type": str(model.aggregate_type),
        "aggregate_id": str(model.aggregate_id),
        "payload_json": dict(model.payload_json or {}),
        "status": str(model.status),
        "retry_count": int(model.retry_count),
        "available_at": model.available_at.isoformat(),
        "created_at": model.created_at.isoformat(),
        "processed_at": model.processed_at.isoformat() if model.processed_at else None,
        "last_error": model.last_error,
        "correlation_id": model.correlation_id,
        "causation_id": model.causation_id,
    }


class EventPublisher:
    def __init__(
        self,
        *,
        uow: UnitOfWork | None = None,
        db_session: Session | None = None,
        repository: OutboxEventRepository | None = None,
    ) -> None:
        self._uow = uow
        self._db_session = db_session
        self._repository = repository or (uow.outbox_event_repository if uow is not None else OutboxEventRepository())

    def publish_event(
        self,
        *,
        tenant_id: int,
        event_type: str,
        aggregate_type: str,
        aggregate_id: int | str,
        payload_json: dict[str, Any],
        available_at: datetime | None = None,
        correlation_id: str | None = None,
        causation_id: str | None = None,
    ) -> dict[str, Any]:
        normalized_tenant_id = int(tenant_id)
        normalized_available_at = _normalize_datetime(available_at)

        if self._uow is not None:
            return self._repository.enqueue(
                tenant_id=normalized_tenant_id,
                event_type=event_type,
                aggregate_type=aggregate_type,
                aggregate_id=str(aggregate_id),
                payload_json=payload_json,
                available_at=normalized_available_at,
                correlation_id=correlation_id,
                causation_id=causation_id,
                conn=self._uow.conn,
            )

        if self._db_session is not None:
            event = OutboxEventModel(
                tenant_id=normalized_tenant_id,
                event_type=event_type.strip().lower(),
                aggregate_type=aggregate_type.strip().lower(),
                aggregate_id=str(aggregate_id).strip(),
                payload_json=dict(payload_json),
                status="pending",
                retry_count=0,
                available_at=normalized_available_at,
                correlation_id=correlation_id,
                causation_id=causation_id,
            )
            self._db_session.add(event)
            self._db_session.flush()
            self._db_session.refresh(event)
            return _model_to_api(event)

        with UnitOfWork() as uow:
            return self._repository.enqueue(
                tenant_id=normalized_tenant_id,
                event_type=event_type,
                aggregate_type=aggregate_type,
                aggregate_id=str(aggregate_id),
                payload_json=payload_json,
                available_at=normalized_available_at,
                correlation_id=correlation_id,
                causation_id=causation_id,
                conn=uow.conn,
            )