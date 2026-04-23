from __future__ import annotations

from typing import Any

from app.modules.procurement.service import get_procurement_health_snapshot


def fetch_finance_context(*, tenant_id: int, subject: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    """Return finance context slice for Brain Core decisions."""
    return {
        "student_id": subject.get("student_id") or payload.get("student_id"),
        "balance_due": payload.get("balance_due"),
        "delinquency_days": payload.get("delinquency_days"),
        "budget_code": payload.get("budget_code"),
        "variance_amount": payload.get("variance_amount"),
        "variance_ratio": payload.get("variance_ratio"),
        "procurement_health_snapshot": get_procurement_health_snapshot(tenant_id).model_dump(),
        "tenant_id": tenant_id,
    }
