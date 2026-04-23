"""Phase VII-VII1: Research ethics service."""
from __future__ import annotations

from app.modules.university_core.tenant_entity_service import (
    create_entity_for_tenant,
    list_entities_for_tenant,
)


def list_ethics_reviews(
    tenant_id: int,
    status: str | None = None,
    risk_level: str | None = None,
) -> list[dict[str, object]]:
    rows = list_entities_for_tenant("ethics_reviews", tenant_id)
    status_filter = str(status or "").strip().lower()
    risk_filter = str(risk_level or "").strip().lower()

    result: list[dict[str, object]] = []
    for row in rows:
        if status_filter and str(row.get("status") or "").strip().lower() != status_filter:
            continue
        if risk_filter and str(row.get("risk_level") or "").strip().lower() != risk_filter:
            continue
        result.append(row)
    return result


def create_ethics_review(payload: dict[str, object], tenant_id: int) -> dict[str, object]:
    return create_entity_for_tenant("ethics_reviews", payload, tenant_id)


def get_research_ethics_brain_context(tenant_id: int) -> dict[str, object]:
    rows = list_entities_for_tenant("ethics_reviews", tenant_id)

    total = len(rows)
    pending = 0
    approved = 0
    rejected = 0
    high_risk = 0

    for row in rows:
        st = str(row.get("status") or "").strip().lower()
        if st == "pending":
            pending += 1
        elif st == "approved":
            approved += 1
        elif st in {"rejected", "denied"}:
            rejected += 1
        rl = str(row.get("risk_level") or "").strip().lower()
        if rl in {"high", "critical"}:
            high_risk += 1

    if high_risk > 0 or rejected > 0:
        compliance_status = "at_risk"
    elif pending > 0:
        compliance_status = "under_review"
    else:
        compliance_status = "compliant"

    return {
        "module": "research_ethics",
        "tenant_id": tenant_id,
        "total_reviews": total,
        "pending_reviews": pending,
        "approved_reviews": approved,
        "rejected_reviews": rejected,
        "high_risk_reviews": high_risk,
        "compliance_status": compliance_status,
    }
