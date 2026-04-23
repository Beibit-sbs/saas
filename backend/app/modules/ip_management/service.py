"""Phase VII-VII1: IP management service."""
from __future__ import annotations

from app.modules.university_core.tenant_entity_service import (
    create_entity_for_tenant,
    list_entities_for_tenant,
)


def list_ip_assets(
    tenant_id: int,
    ip_type: str | None = None,
    status: str | None = None,
) -> list[dict[str, object]]:
    rows = list_entities_for_tenant("ip_assets", tenant_id)
    type_filter = str(ip_type or "").strip().lower()
    status_filter = str(status or "").strip().lower()

    result: list[dict[str, object]] = []
    for row in rows:
        if type_filter and str(row.get("ip_type") or "").strip().lower() != type_filter:
            continue
        if status_filter and str(row.get("status") or "").strip().lower() != status_filter:
            continue
        result.append(row)
    return result


def create_ip_asset(payload: dict[str, object], tenant_id: int) -> dict[str, object]:
    return create_entity_for_tenant("ip_assets", payload, tenant_id)


def get_ip_management_brain_context(tenant_id: int) -> dict[str, object]:
    rows = list_entities_for_tenant("ip_assets", tenant_id)

    total = len(rows)
    active_patents = 0
    commercialized = 0
    total_revenue = 0.0

    for row in rows:
        ip_type = str(row.get("ip_type") or "").strip().lower()
        st = str(row.get("status") or "").strip().lower()
        comm_st = str(row.get("commercialization_status") or "").strip().lower()

        if ip_type == "patent" and st in {"granted", "active", "filed"}:
            active_patents += 1
        if comm_st in {"licensed", "commercialized", "sold"}:
            commercialized += 1
        try:
            rev = float(row.get("licensing_revenue") or 0)
            total_revenue += rev
        except (TypeError, ValueError):
            pass

    commercialization_rate = round(commercialized / total, 3) if total > 0 else 0.0

    if commercialization_rate >= 0.3 and total_revenue > 0:
        portfolio_health = "strong"
    elif commercialization_rate >= 0.1 or active_patents > 0:
        portfolio_health = "developing"
    else:
        portfolio_health = "early_stage"

    return {
        "module": "ip_management",
        "tenant_id": tenant_id,
        "total_assets": total,
        "active_patents": active_patents,
        "commercialized_assets": commercialized,
        "total_licensing_revenue": round(total_revenue, 2),
        "commercialization_rate": commercialization_rate,
        "portfolio_health": portfolio_health,
    }
