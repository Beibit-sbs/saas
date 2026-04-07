from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Callable

from app.platform.uow import UnitOfWork


@dataclass
class IdempotencyResult:
    replayed: bool
    response: dict[str, Any]


def _hash_request(payload: dict[str, Any]) -> str:
    serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


class IdempotencyService:
    def execute(
        self,
        *,
        tenant_id: int,
        key: str,
        operation: str,
        request_payload: dict[str, Any],
        executor: Callable[[UnitOfWork], dict[str, Any]],
    ) -> IdempotencyResult:
        normalized_tenant_id = int(tenant_id)
        normalized_key = str(key or "").strip()
        normalized_operation = str(operation or "").strip().lower()
        if not normalized_key:
            raise ValueError("idempotency key is required")
        if not normalized_operation:
            raise ValueError("idempotency operation is required")

        request_hash = _hash_request(request_payload)

        with UnitOfWork() as uow:
            existing = uow.idempotency_repository.get(normalized_tenant_id, normalized_key, normalized_operation, conn=uow.conn)
            if existing is not None:
                if str(existing.get("request_hash", "")) != request_hash:
                    raise ValueError("idempotency key reuse with different payload")
                if str(existing.get("status", "")).lower() == "completed":
                    snapshot = dict(existing.get("response_snapshot") or {})
                    return IdempotencyResult(replayed=True, response=snapshot)

            uow.idempotency_repository.create_pending(
                normalized_tenant_id,
                normalized_key,
                normalized_operation,
                request_hash,
                conn=uow.conn,
            )

            try:
                response = executor(uow)
                uow.idempotency_repository.complete(
                    normalized_tenant_id,
                    normalized_key,
                    normalized_operation,
                    response,
                    conn=uow.conn,
                )
                return IdempotencyResult(replayed=False, response=response)
            except Exception as exc:
                uow.idempotency_repository.fail(
                    normalized_tenant_id,
                    normalized_key,
                    normalized_operation,
                    {"error": str(exc)},
                    conn=uow.conn,
                )
                raise
