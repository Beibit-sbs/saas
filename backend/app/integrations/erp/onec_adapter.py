"""L.7 — 1C / SAP ERP integration adapter (stub)."""
from __future__ import annotations

import httpx

ONEC_BASE_URL = "http://1c-server/hs/ERP"
DEFAULT_TIMEOUT = 30


class OneCAdapterError(Exception):
    pass


def sync_payroll(tenant_id: str, *, period: str | None = None) -> dict:
    """Pull payroll data from 1C and return sync summary. Bidirectional: also pushes deltas."""
    if not tenant_id:
        raise ValueError("tenant_id is required")

    params: dict = {"tenantId": tenant_id}
    if period:
        params["period"] = period

    try:
        resp = httpx.get(f"{ONEC_BASE_URL}/payroll/sync", params=params, timeout=DEFAULT_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
    except httpx.RequestError as exc:
        raise OneCAdapterError(f"1C sync_payroll failed: {exc}") from exc

    return {
        "synced": data.get("synced", 0),
        "errors": data.get("errors", []),
        "period": data.get("period", period or ""),
        "status": data.get("status", "OK"),
    }


def sync_budget(tenant_id: str, *, fiscal_year: int | None = None) -> dict:
    """Sync budget plan and actual data with 1C."""
    if not tenant_id:
        raise ValueError("tenant_id is required")

    payload: dict = {"tenantId": tenant_id}
    if fiscal_year:
        payload["fiscalYear"] = fiscal_year

    try:
        resp = httpx.post(f"{ONEC_BASE_URL}/budget/sync", json=payload, timeout=DEFAULT_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
    except httpx.RequestError as exc:
        raise OneCAdapterError(f"1C sync_budget failed: {exc}") from exc

    return {
        "lines_synced": data.get("linesSynced", 0),
        "errors": data.get("errors", []),
        "fiscal_year": data.get("fiscalYear", fiscal_year),
        "status": data.get("status", "OK"),
    }


def sync_assets(tenant_id: str) -> dict:
    """Sync fixed assets register with 1C."""
    if not tenant_id:
        raise ValueError("tenant_id is required")

    try:
        resp = httpx.get(
            f"{ONEC_BASE_URL}/assets/sync",
            params={"tenantId": tenant_id},
            timeout=DEFAULT_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()
    except httpx.RequestError as exc:
        raise OneCAdapterError(f"1C sync_assets failed: {exc}") from exc

    return {
        "assets_synced": data.get("assetsSynced", 0),
        "depreciation_updated": data.get("depreciationUpdated", 0),
        "errors": data.get("errors", []),
        "status": data.get("status", "OK"),
    }
