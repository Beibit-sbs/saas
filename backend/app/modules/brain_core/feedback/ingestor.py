from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


class FeedbackIngestor:
    """Normalizes raw execution feedback to Brain outcome payload."""

    def ingest(self, *, decision_id: str, tenant_id: int, payload: dict[str, Any]) -> dict[str, Any]:
        return {
            "outcome_id": str(uuid4()),
            "decision_id": decision_id,
            "tenant_id": int(tenant_id),
            "outcome_type": str(payload.get("outcome_type") or "completed"),
            "effectiveness": str(payload.get("effectiveness") or "neutral"),
            "outcome_payload": dict(payload),
            "recorded_at": datetime.now(timezone.utc).isoformat(),
        }
