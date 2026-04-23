from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4


class JobActionDispatcher:
    """Minimal in-memory job sink for deferred Brain Core actions."""

    def __init__(self) -> None:
        self._jobs: list[dict] = []

    def enqueue(self, *, tenant_id: int, decision_id: str, job_type: str, payload: dict) -> dict:
        job = {
            "job_id": str(uuid4()),
            "tenant_id": int(tenant_id),
            "decision_id": decision_id,
            "job_type": str(job_type),
            "payload": dict(payload or {}),
            "status": "queued",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self._jobs.append(job)
        return {"status": "queued", "item": job}

    def snapshot(self) -> list[dict]:
        return list(self._jobs)
