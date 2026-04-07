from __future__ import annotations

from fastapi import HTTPException

from app.platform.feature_flags import service as feature_flags_service
from app.platform.tenant import service as tenant_service


ANALYTICS_READ_FEATURE_MODULE = "analytics"
ANALYTICS_READ_FEATURE_KEY = "developer_read"
ANALYTICS_READ_REQUIRED_FEATURE_KEY = "developer_read_required"
ANALYTICS_READ_DENY_DETAIL = "analytics entitlement required"
ANALYTICS_READ_DENY_REASON_HEADER = "x-analytics-entitlement-reason"
ANALYTICS_READ_DENY_REASON_EXPLICIT_DISABLED = "explicit_disabled"
ANALYTICS_READ_DENY_REASON_MISSING_ENTITLEMENT_DENIED = "missing_entitlement_denied"
ANALYTICS_READ_EFFECTIVE_LEGACY_COMPATIBLE_ALLOW = "legacy_compatible_allow"
ANALYTICS_READ_EFFECTIVE_STRICT_REQUIRED_MISSING = "strict_required_missing"
ANALYTICS_READ_EFFECTIVE_EXPLICITLY_ENABLED = "explicitly_enabled"
ANALYTICS_READ_EFFECTIVE_EXPLICITLY_DISABLED = "explicitly_disabled"


def _feature_enabled_state(*, rows: list[dict[str, object]], module: str, key: str) -> bool | None:
    state: bool | None = None
    normalized_module = str(module).strip().lower()
    normalized_key = str(key).strip().lower()
    for item in rows:
        if (
            str(item.get("module", "")).strip().lower() == normalized_module
            and str(item.get("key", "")).strip().lower() == normalized_key
        ):
            state = bool(item.get("enabled", False))
    return state


def inspect_analytics_read_policy_state(tenant_id: int) -> dict[str, object]:
    rows = feature_flags_service.list_tenant_features(int(tenant_id))
    enabled = _feature_enabled_state(
        rows=rows,
        module=ANALYTICS_READ_FEATURE_MODULE,
        key=ANALYTICS_READ_FEATURE_KEY,
    )
    entitlement_required = _feature_enabled_state(
        rows=rows,
        module=ANALYTICS_READ_FEATURE_MODULE,
        key=ANALYTICS_READ_REQUIRED_FEATURE_KEY,
    )

    effective_state = ANALYTICS_READ_EFFECTIVE_LEGACY_COMPATIBLE_ALLOW
    is_entitled = True

    if enabled is True:
        effective_state = ANALYTICS_READ_EFFECTIVE_EXPLICITLY_ENABLED
        is_entitled = True
    elif enabled is False:
        effective_state = ANALYTICS_READ_EFFECTIVE_EXPLICITLY_DISABLED
        is_entitled = False
    elif entitlement_required is True:
        # Rollout marker enabled and no explicit entitlement: strict deny.
        effective_state = ANALYTICS_READ_EFFECTIVE_STRICT_REQUIRED_MISSING
        is_entitled = False

    return {
        "tenant_id": int(tenant_id),
        "analytics_read_feature_enabled": enabled,
        "analytics_read_required_marker_enabled": entitlement_required,
        "effective_state": effective_state,
        "is_entitled": is_entitled,
    }


def build_analytics_read_policy_state_read(tenant_id: int) -> dict[str, object]:
    policy_state = inspect_analytics_read_policy_state(int(tenant_id))
    return {
        "tenant_id": int(tenant_id),
        "module": ANALYTICS_READ_FEATURE_MODULE,
        "marker_enabled": policy_state.get("analytics_read_required_marker_enabled"),
        "feature_enabled": policy_state.get("analytics_read_feature_enabled"),
        "marker_key": ANALYTICS_READ_REQUIRED_FEATURE_KEY,
        "feature_key": ANALYTICS_READ_FEATURE_KEY,
        "effective_state": policy_state.get("effective_state"),
        "is_entitled": policy_state.get("is_entitled"),
    }


def list_analytics_read_policy_state_reads(*, limit: int) -> list[dict[str, object]]:
    normalized_limit = max(1, int(limit))
    tenant_rows = tenant_service.list_tenant_profiles()
    return [
        build_analytics_read_policy_state_read(int(item["tenant_id"]))
        for item in tenant_rows[:normalized_limit]
    ]


def analytics_entitlement_deny_reason(exc: HTTPException) -> str | None:
    if int(getattr(exc, "status_code", 0)) != 403:
        return None
    if str(getattr(exc, "detail", "") or "").strip().lower() != ANALYTICS_READ_DENY_DETAIL:
        return None
    reason = str((getattr(exc, "headers", None) or {}).get(ANALYTICS_READ_DENY_REASON_HEADER, "")).strip().lower()
    if reason in {
        ANALYTICS_READ_DENY_REASON_EXPLICIT_DISABLED,
        ANALYTICS_READ_DENY_REASON_MISSING_ENTITLEMENT_DENIED,
    }:
        return reason
    return "entitlement_denied"


def assert_analytics_read_entitled(tenant_id: int) -> None:
    deny_reason = ANALYTICS_READ_DENY_REASON_EXPLICIT_DISABLED
    try:
        policy_state = inspect_analytics_read_policy_state(int(tenant_id))
    except ValueError as exc:
        raise HTTPException(
            status_code=403,
            detail=ANALYTICS_READ_DENY_DETAIL,
            headers={ANALYTICS_READ_DENY_REASON_HEADER: deny_reason},
        ) from exc

    if str(policy_state.get("effective_state")) == ANALYTICS_READ_EFFECTIVE_STRICT_REQUIRED_MISSING:
        deny_reason = ANALYTICS_READ_DENY_REASON_MISSING_ENTITLEMENT_DENIED

    if not bool(policy_state.get("is_entitled", False)):
        raise HTTPException(
            status_code=403,
            detail=ANALYTICS_READ_DENY_DETAIL,
            headers={ANALYTICS_READ_DENY_REASON_HEADER: deny_reason},
        )