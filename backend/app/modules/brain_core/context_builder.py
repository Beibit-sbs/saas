from __future__ import annotations

from typing import Any

from app.modules.brain_core.context_sources.academic import fetch_academic_context
from app.modules.brain_core.context_sources.faculty import fetch_faculty_context
from app.modules.brain_core.context_sources.finance import fetch_finance_context
from app.modules.brain_core.context_sources.operations import fetch_operations_context
from app.modules.brain_core.context_sources.platform import fetch_platform_context
from app.modules.brain_core.context_sources.student_success import fetch_student_success_context


class ContextBuilder:
    """Builds a tenant-scoped context snapshot from multiple domain sources."""

    def build_context(self, signal: dict[str, Any]) -> dict[str, Any]:
        tenant_id = int(signal.get("tenant_id") or 0)
        if tenant_id <= 0:
            raise ValueError("tenant_id is required for context build")

        subject = dict(signal.get("subject") or {})
        payload = dict(signal.get("payload") or {})

        return {
            "tenant_id": tenant_id,
            "signal_id": signal.get("signal_id"),
            "correlation_id": signal.get("correlation_id"),
            "event_type": signal.get("event_type"),
            "academic": fetch_academic_context(tenant_id=tenant_id, subject=subject, payload=payload),
            "student_success": fetch_student_success_context(tenant_id=tenant_id, subject=subject, payload=payload),
            "faculty": fetch_faculty_context(tenant_id=tenant_id, subject=subject, payload=payload),
            "finance": fetch_finance_context(tenant_id=tenant_id, subject=subject, payload=payload),
            "operations": fetch_operations_context(tenant_id=tenant_id, subject=subject, payload=payload),
            "platform": fetch_platform_context(tenant_id=tenant_id, subject=subject, payload=payload),
        }
