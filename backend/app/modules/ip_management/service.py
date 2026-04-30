"""Phase VII-VII1: IP management service."""
from __future__ import annotations

from app.core.module_helpers.service_validation import DomainValidationError
from app.modules.university_core.tenant_entity_service import (
    create_entity_for_tenant,
    list_entities_for_tenant,
)

# --- W31: active-asset cap by IP type ---
_IP_TYPE_MAX_ACTIVE_ASSETS: dict[str, int] = {
    "patent": 50,
    "trademark": 30,
    "copyright": 100,
    "trade_secret": 20,
}

_ACTIVE_ASSET_STATUSES: frozenset[str] = frozenset({"filed", "granted", "active"})

# statuses that trigger a licensing record side effect
_COMMERCIAL_STATUSES: frozenset[str] = frozenset({"licensed", "commercialized", "sold"})

# W31 upgrade: cross-entity faculty contract eligibility guard for non-draft assets
_INVENTOR_REQUIRED_ASSET_STATUSES: frozenset[str] = frozenset({"filed", "granted", "active"})
_INVENTOR_ACTIVE_CONTRACT_STATUSES: frozenset[str] = frozenset({"active"})


def _parse_inventor_ids(raw: object) -> list[str]:
    if raw is None:
        return []

    if isinstance(raw, str):
        parts = [p.strip() for p in raw.split(",")]
    elif isinstance(raw, (list, tuple, set)):
        parts = [str(p).strip() for p in raw]
    else:
        parts = [str(raw).strip()]

    result: list[str] = []
    seen: set[str] = set()
    for part in parts:
        if not part:
            continue
        if part in seen:
            continue
        seen.add(part)
        result.append(part)
    return result


def _check_inventors_have_active_contracts_for_ip_asset(
    *,
    tenant_id: int,
    ip_type: str,
    status: str,
    commercialization_status: str,
    inventor_ids_raw: object,
) -> None:
    """W31 upgrade: Cross-entity guard for IP asset validity.

    Non-draft IP assets and commercially transitioned assets influence portfolio
    and revenue decisions. We must block ghost assets attributed to inventors
    without active faculty contracts.

    FAIL-CLOSED: when faculty_contracts lookup fails, block creation.
    """
    requires_contract_validation = (
        status in _INVENTOR_REQUIRED_ASSET_STATUSES
        or commercialization_status in _COMMERCIAL_STATUSES
    )
    if not requires_contract_validation:
        return

    inventor_ids = _parse_inventor_ids(inventor_ids_raw)
    if not inventor_ids:
        raise DomainValidationError(
            "IP asset creation blocked: inventor_ids is required for filed/granted/active "
            "or commercially transitioned assets."
        )

    try:
        all_contracts = list_entities_for_tenant("faculty_contracts", tenant_id)
    except Exception as exc:
        raise DomainValidationError(
            "IP asset creation blocked: faculty_contracts lookup failed; "
            "cannot verify inventor employment eligibility."
        ) from exc

    active_inventor_ids = {
        str(row.get("faculty_id") or "").strip()
        for row in all_contracts
        if str(row.get("status") or "").strip().lower() in _INVENTOR_ACTIVE_CONTRACT_STATUSES
    }

    missing_or_inactive = [i for i in inventor_ids if i not in active_inventor_ids]
    if missing_or_inactive:
        raise DomainValidationError(
            "IP asset creation blocked: inventor(s) without active faculty contract: "
            f"{missing_or_inactive}."
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
    ip_type = str(payload.get("ip_type") or "patent").strip().lower()
    status = str(payload.get("status") or "draft").strip().lower()
    commercialization_status = str(
        payload.get("commercialization_status") or "none"
    ).strip().lower()

    # W31 upgrade: cross-entity validation BEFORE any persist operation.
    _check_inventors_have_active_contracts_for_ip_asset(
        tenant_id=tenant_id,
        ip_type=ip_type,
        status=status,
        commercialization_status=commercialization_status,
        inventor_ids_raw=payload.get("inventor_ids"),
    )

    cap = _IP_TYPE_MAX_ACTIVE_ASSETS.get(ip_type, 30)

    # cap guard: count existing active assets of the same ip_type
    if status in _ACTIVE_ASSET_STATUSES:
        all_assets = list_entities_for_tenant("ip_assets", tenant_id)
        active_count = sum(
            1 for r in all_assets
            if str(r.get("ip_type") or "").strip().lower() == ip_type
            and str(r.get("status") or "").strip().lower() in _ACTIVE_ASSET_STATUSES
        )
        if active_count >= cap:
            raise ValueError(
                f"Active {ip_type} asset cap ({cap}) reached for this tenant."
            )

    record = create_entity_for_tenant("ip_assets", payload, tenant_id)

    # side effect: create licensing record for commercial transitions
    if commercialization_status in _COMMERCIAL_STATUSES:
        _ensure_ip_licensing_record(record, tenant_id)

    return record


def _ensure_ip_licensing_record(asset: dict[str, object], tenant_id: int) -> None:
    """Idempotent side-effect: ensure a licensing record exists for a commercialized IP asset."""
    asset_id = str(asset.get("id") or asset.get("asset_code") or "unknown")
    existing = list_entities_for_tenant("ip_licensing_records", tenant_id)
    for rec in existing:
        if str(rec.get("source_entity_id") or "") == asset_id and str(
            rec.get("integration_source") or ""
        ) == "ip_commercialization":
            return  # already created

    create_entity_for_tenant(
        "ip_licensing_records",
        {
            "asset_id": asset_id,
            "asset_code": asset.get("asset_code"),
            "commercialization_status": asset.get("commercialization_status"),
            "integration_source": "ip_commercialization",
            "source_entity_id": asset_id,
            "tenant_id": tenant_id,
        },
        tenant_id,
    )


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
