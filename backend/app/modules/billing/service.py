from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
import os
from threading import Lock

from fastapi import HTTPException

from app.core.config import is_runtime_schema_bootstrap_enabled
from app.core.db import get_raw_conn
from app.modules.audit.service import log_admin_action
from app.modules.plans.service import get_plan_by_code, get_plan_by_id
from app.modules.quotas.service import check_quota, resolve_tenant_quotas
from app.modules.tenants.service import get_tenant
from app.modules.usage.service import get_usage_sum

try:
    import psycopg
except ImportError:  # pragma: no cover
    psycopg = None


SUBSCRIPTION_STATUSES = {"trial", "active", "suspended", "cancelled"}
WRITE_ALLOWED_STATUSES = {"trial", "active"}
DEFAULT_TRIAL_DAYS = 14
DEFAULT_BILLING_PERIOD_DAYS = 30

# Cancelled is terminal. Reactivation requires explicit new subscription start, not status flip.
TRANSITIONS: dict[str, set[str]] = {
    "trial": {"active", "suspended", "cancelled"},
    "active": {"suspended", "cancelled"},
    "suspended": {"active", "cancelled"},
    "cancelled": set(),
}

PLAN_RANK: dict[str, int] = {
    "free": 0,
    "basic": 1,
    "pro": 2,
    "enterprise": 3,
}


@dataclass
class BillingState:
    subscriptions: dict[int, dict[str, object]] = field(default_factory=dict)


_state = BillingState()
_state_lock = Lock()


def _db_url() -> str | None:
    return os.getenv("DATABASE_URL")


def _use_database() -> bool:
    return bool(_db_url()) and psycopg is not None


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _now_iso() -> str:
    return _now().isoformat()


def _period_end_from_start(start: datetime) -> datetime:
    return start + timedelta(days=DEFAULT_BILLING_PERIOD_DAYS)


def _parse_dt(value: object | None) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    raw = str(value).strip()
    if not raw:
        return None
    raw = raw.replace("Z", "+00:00")
    dt = datetime.fromisoformat(raw)
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _dt_to_iso(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.astimezone(timezone.utc).isoformat()


def _period_window(
    *,
    current_start: object | None,
    current_end: object | None,
    requested_start: str | None,
    requested_end: str | None,
) -> tuple[datetime, datetime]:
    now = _now()
    start = _parse_dt(requested_start) or _parse_dt(current_start) or now
    end = _parse_dt(requested_end) or _parse_dt(current_end) or _period_end_from_start(start)
    if end <= start:
        raise ValueError("current_period_end must be later than current_period_start")
    return start, end


def _plan_rank(plan_code: str) -> int:
    return PLAN_RANK.get(str(plan_code or "").strip().lower(), -1)


def _trial_auto_activate_enabled() -> bool:
    value = str(os.getenv("BILLING_TRIAL_AUTO_ACTIVATE", "false")).strip().lower()
    return value in {"1", "true", "yes", "on"}


def _audit_billing(
    *,
    tenant_id: int,
    action: str,
    result: str,
    metadata: dict[str, object],
    actor: str = "system.billing",
) -> None:
    log_admin_action(
        actor=actor,
        tenant_id=tenant_id,
        action=action,
        path="billing:lifecycle",
        client_ip="internal",
        entity="billing",
        result=result,
        metadata=metadata,
    )


def _ensure_db(conn) -> None:
    if not is_runtime_schema_bootstrap_enabled():
        return
    with conn.cursor() as cur:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS app_tenant_subscriptions (
                tenant_id BIGINT PRIMARY KEY REFERENCES app_tenants(id) ON DELETE CASCADE,
                plan_id BIGINT NOT NULL REFERENCES app_plans(id) ON DELETE RESTRICT,
                status TEXT NOT NULL,
                started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                trial_ends_at TIMESTAMPTZ,
                current_period_start TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                current_period_end TIMESTAMPTZ,
                next_plan_id BIGINT REFERENCES app_plans(id) ON DELETE SET NULL,
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                CHECK (status IN ('trial', 'active', 'suspended', 'cancelled'))
            )
            """
        )
        cur.execute(
            "ALTER TABLE app_tenant_subscriptions ADD COLUMN IF NOT EXISTS next_plan_id BIGINT REFERENCES app_plans(id) ON DELETE SET NULL"
        )
    conn.commit()


def _row_to_subscription(row: tuple[object, ...]) -> dict[str, object]:
    plan = get_plan_by_id(int(row[1]))
    next_plan = get_plan_by_id(int(row[7])) if row[7] is not None else None
    return {
        "tenant_id": int(row[0]),
        "plan_id": int(row[1]),
        "plan_code": str(plan["code"]) if plan else "",
        "status": str(row[2]),
        "started_at": _dt_to_iso(_parse_dt(row[3])) or _now_iso(),
        "trial_ends_at": _dt_to_iso(_parse_dt(row[4])),
        "current_period_start": _dt_to_iso(_parse_dt(row[5])) or _now_iso(),
        "current_period_end": _dt_to_iso(_parse_dt(row[6])) or _now_iso(),
        "next_plan_id": int(row[7]) if row[7] is not None else None,
        "next_plan_code": str(next_plan["code"]) if next_plan else None,
        "updated_at": _dt_to_iso(_parse_dt(row[8])) or _now_iso(),
    }


def _get_subscription_db(tenant_id: int) -> dict[str, object] | None:
    with get_raw_conn() as conn:
        _ensure_db(conn)
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT tenant_id, plan_id, status, started_at, trial_ends_at,
                       current_period_start, current_period_end, next_plan_id, updated_at
                FROM app_tenant_subscriptions
                WHERE tenant_id = %s
                LIMIT 1
                """,
                (tenant_id,),
            )
            row = cur.fetchone()
    if row is None:
        return None
    return _row_to_subscription(row)


def ensure_tenant_subscription(
    tenant_id: int,
    *,
    plan_code: str,
    status: str = "trial",
    trial_days: int = DEFAULT_TRIAL_DAYS,
    trial_ends_at: str | None = None,
    current_period_start: str | None = None,
    current_period_end: str | None = None,
    next_plan_code: str | None = None,
    preserve_existing_trial_end: bool = True,
) -> dict[str, object]:
    normalized_tenant_id = int(tenant_id)
    if normalized_tenant_id <= 0:
        raise ValueError("tenant_id must be positive")

    tenant = get_tenant(normalized_tenant_id)
    if tenant is None:
        raise ValueError("tenant not found")

    normalized_status = str(status or "trial").strip().lower()
    if normalized_status not in SUBSCRIPTION_STATUSES:
        raise ValueError("invalid subscription status")

    plan = get_plan_by_code(plan_code)
    if plan is None:
        raise ValueError("plan not found")

    next_plan_id: int | None = None
    if next_plan_code:
        next_plan = get_plan_by_code(next_plan_code)
        if next_plan is None:
            raise ValueError("next plan not found")
        next_plan_id = int(next_plan["id"])

    if _use_database():
        try:
            existing = _get_subscription_db(normalized_tenant_id)

            start_dt, end_dt = _period_window(
                current_start=existing.get("current_period_start") if existing else None,
                current_end=existing.get("current_period_end") if existing else None,
                requested_start=current_period_start,
                requested_end=current_period_end,
            )

            existing_trial_end = _parse_dt(existing.get("trial_ends_at") if existing else None)
            requested_trial_end = _parse_dt(trial_ends_at)
            trial_end: datetime | None = None
            if normalized_status == "trial":
                if requested_trial_end is not None:
                    trial_end = requested_trial_end
                elif preserve_existing_trial_end and existing_trial_end is not None:
                    trial_end = existing_trial_end
                else:
                    trial_end = _now() + timedelta(days=max(1, int(trial_days)))
                if trial_end <= _now():
                    # Allow explicit past value only for deterministic tests/recovery jobs.
                    pass
            elif requested_trial_end is not None:
                trial_end = requested_trial_end

            started_at = _parse_dt(existing.get("started_at") if existing else None) or _now()

            with get_raw_conn() as conn:
                _ensure_db(conn)
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO app_tenant_subscriptions (
                            tenant_id,
                            plan_id,
                            status,
                            started_at,
                            trial_ends_at,
                            current_period_start,
                            current_period_end,
                            next_plan_id,
                            updated_at
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
                        ON CONFLICT (tenant_id)
                        DO UPDATE SET
                            plan_id = EXCLUDED.plan_id,
                            status = EXCLUDED.status,
                            trial_ends_at = EXCLUDED.trial_ends_at,
                            current_period_start = EXCLUDED.current_period_start,
                            current_period_end = EXCLUDED.current_period_end,
                            next_plan_id = EXCLUDED.next_plan_id,
                            updated_at = NOW()
                        RETURNING tenant_id, plan_id, status, started_at, trial_ends_at,
                                  current_period_start, current_period_end, next_plan_id, updated_at
                        """,
                        (
                            normalized_tenant_id,
                            int(plan["id"]),
                            normalized_status,
                            started_at,
                            trial_end,
                            start_dt,
                            end_dt,
                            next_plan_id,
                        ),
                    )
                    row = cur.fetchone()
                conn.commit()
            return _row_to_subscription(row)
        except Exception:
            pass

    with _state_lock:
        existing = _state.subscriptions.get(normalized_tenant_id)

        start_dt, end_dt = _period_window(
            current_start=existing.get("current_period_start") if existing else None,
            current_end=existing.get("current_period_end") if existing else None,
            requested_start=current_period_start,
            requested_end=current_period_end,
        )

        existing_trial_end = _parse_dt(existing.get("trial_ends_at") if existing else None)
        requested_trial_end = _parse_dt(trial_ends_at)
        trial_end: datetime | None = None
        if normalized_status == "trial":
            if requested_trial_end is not None:
                trial_end = requested_trial_end
            elif preserve_existing_trial_end and existing_trial_end is not None:
                trial_end = existing_trial_end
            else:
                trial_end = _now() + timedelta(days=max(1, int(trial_days)))
        elif requested_trial_end is not None:
            trial_end = requested_trial_end

        started_at = _parse_dt(existing.get("started_at") if existing else None) or _now()
        record = {
            "tenant_id": normalized_tenant_id,
            "plan_id": int(plan["id"]),
            "plan_code": str(plan["code"]),
            "status": normalized_status,
            "started_at": _dt_to_iso(started_at) or _now_iso(),
            "trial_ends_at": _dt_to_iso(trial_end),
            "current_period_start": _dt_to_iso(start_dt) or _now_iso(),
            "current_period_end": _dt_to_iso(end_dt) or _now_iso(),
            "next_plan_id": next_plan_id,
            "next_plan_code": next_plan_code.strip().lower() if next_plan_code else None,
            "updated_at": _now_iso(),
        }
        _state.subscriptions[normalized_tenant_id] = record
        return dict(record)


def _transition_allowed(current_status: str, target_status: str) -> bool:
    if current_status == target_status:
        return True
    return target_status in TRANSITIONS.get(current_status, set())


def _apply_period_rollover(subscription: dict[str, object]) -> dict[str, object]:
    status = str(subscription.get("status", "")).lower()
    if status not in {"active", "suspended", "cancelled"}:
        return subscription

    period_end = _parse_dt(subscription.get("current_period_end"))
    period_start = _parse_dt(subscription.get("current_period_start"))
    if period_end is None or period_start is None:
        return subscription
    if _now() < period_end:
        return subscription

    next_plan_code = str(subscription.get("next_plan_code") or "").strip().lower() or str(subscription.get("plan_code") or "free")
    new_start = period_end
    new_end = _period_end_from_start(new_start)

    updated = ensure_tenant_subscription(
        int(subscription["tenant_id"]),
        plan_code=next_plan_code,
        status=status,
        current_period_start=_dt_to_iso(new_start),
        current_period_end=_dt_to_iso(new_end),
        trial_ends_at=_dt_to_iso(_parse_dt(subscription.get("trial_ends_at"))),
        next_plan_code=None,
    )

    previous_plan = str(subscription.get("plan_code") or "")
    if next_plan_code and next_plan_code != previous_plan:
        _audit_billing(
            tenant_id=int(subscription["tenant_id"]),
            action="billing.subscription.plan.changed",
            result="success",
            metadata={
                "old_plan": previous_plan,
                "new_plan": next_plan_code,
                "effective": "period_rollover",
                "period_start": updated.get("current_period_start"),
                "period_end": updated.get("current_period_end"),
            },
        )
    return updated


def _apply_trial_expiry(subscription: dict[str, object]) -> dict[str, object]:
    status = str(subscription.get("status", "")).lower()
    if status != "trial":
        return subscription

    trial_end = _parse_dt(subscription.get("trial_ends_at"))
    if trial_end is None:
        # Fail-safe: no infinite trial allowed.
        updated = ensure_tenant_subscription(
            int(subscription["tenant_id"]),
            plan_code=str(subscription.get("plan_code") or "free"),
            status="suspended",
            trial_ends_at=_now_iso(),
            current_period_start=str(subscription.get("current_period_start") or _now_iso()),
            current_period_end=str(subscription.get("current_period_end") or _period_end_from_start(_now()).isoformat()),
            next_plan_code=str(subscription.get("next_plan_code") or "") or None,
        )
        _audit_billing(
            tenant_id=int(subscription["tenant_id"]),
            action="billing.subscription.trial.expired",
            result="success",
            metadata={
                "from_status": "trial",
                "to_status": "suspended",
                "reason": "missing_trial_end",
            },
        )
        _audit_billing(
            tenant_id=int(subscription["tenant_id"]),
            action="billing.subscription.suspended",
            result="success",
            metadata={"reason": "trial_missing_end"},
        )
        return updated

    if _now() < trial_end:
        return subscription

    target = "active" if _trial_auto_activate_enabled() else "suspended"
    updated = ensure_tenant_subscription(
        int(subscription["tenant_id"]),
        plan_code=str(subscription.get("plan_code") or "free"),
        status=target,
        trial_ends_at=_dt_to_iso(trial_end),
        current_period_start=str(subscription.get("current_period_start") or _now_iso()),
        current_period_end=str(subscription.get("current_period_end") or _period_end_from_start(_now()).isoformat()),
        next_plan_code=str(subscription.get("next_plan_code") or "") or None,
    )
    _audit_billing(
        tenant_id=int(subscription["tenant_id"]),
        action="billing.subscription.trial.expired",
        result="success",
        metadata={
            "from_status": "trial",
            "to_status": target,
            "trial_ends_at": _dt_to_iso(trial_end),
            "auto_activate": _trial_auto_activate_enabled(),
        },
    )
    if target == "suspended":
        _audit_billing(
            tenant_id=int(subscription["tenant_id"]),
            action="billing.subscription.suspended",
            result="success",
            metadata={"reason": "trial_expired"},
        )
    return updated


def _effective_subscription(subscription: dict[str, object]) -> dict[str, object]:
    current = _apply_trial_expiry(subscription)
    current = _apply_period_rollover(current)
    return current


def get_tenant_subscription(tenant_id: int) -> dict[str, object] | None:
    normalized_tenant_id = int(tenant_id)
    if normalized_tenant_id <= 0:
        return None

    if _use_database():
        try:
            row = _get_subscription_db(normalized_tenant_id)
            if row is None:
                return None
            return _effective_subscription(row)
        except Exception:
            pass

    with _state_lock:
        row = _state.subscriptions.get(normalized_tenant_id)
        row_copy = dict(row) if row is not None else None
    if row_copy is None:
        return None
    return _effective_subscription(row_copy)


def _get_or_create_subscription(tenant_id: int) -> dict[str, object]:
    subscription = get_tenant_subscription(tenant_id)
    if subscription is not None:
        return subscription

    tenant = get_tenant(int(tenant_id))
    if tenant is None:
        raise ValueError("tenant not found")

    plan = get_plan_by_id(int(tenant.get("plan_id") or 0))
    if plan is None:
        plan = get_plan_by_code("free")
    if plan is None:
        raise ValueError("default plan not found")

    return ensure_tenant_subscription(int(tenant_id), plan_code=str(plan["code"]), status="trial")


def transition_subscription_status(
    tenant_id: int,
    target_status: str,
    *,
    actor: str = "system.billing",
    reason: str | None = None,
) -> dict[str, object]:
    normalized_tenant_id = int(tenant_id)
    normalized_target = str(target_status or "").strip().lower()
    if normalized_target not in SUBSCRIPTION_STATUSES:
        raise ValueError("invalid subscription status")

    current = _get_or_create_subscription(normalized_tenant_id)
    current_status = str(current.get("status", "trial")).lower()

    if not _transition_allowed(current_status, normalized_target):
        raise ValueError(f"invalid transition: {current_status} -> {normalized_target}")

    if current_status == "cancelled" and normalized_target == "active":
        raise ValueError("cancelled subscriptions cannot be reactivated; create a new subscription cycle")

    updated = ensure_tenant_subscription(
        normalized_tenant_id,
        plan_code=str(current.get("plan_code", "free")),
        status=normalized_target,
        trial_ends_at=str(current.get("trial_ends_at") or "") or None,
        current_period_start=str(current.get("current_period_start") or "") or None,
        current_period_end=str(current.get("current_period_end") or "") or None,
        next_plan_code=str(current.get("next_plan_code") or "") or None,
    )

    _audit_billing(
        tenant_id=normalized_tenant_id,
        action="billing.subscription.status.changed",
        result="success",
        actor=actor,
        metadata={
            "from_status": current_status,
            "to_status": normalized_target,
            "reason": reason,
        },
    )
    if normalized_target == "suspended":
        _audit_billing(
            tenant_id=normalized_tenant_id,
            action="billing.subscription.suspended",
            result="success",
            actor=actor,
            metadata={"reason": reason or "manual_transition"},
        )

    return updated


def change_subscription_plan(
    tenant_id: int,
    target_plan_code: str,
    *,
    effective: str = "auto",
    actor: str = "system.billing",
    reason: str | None = None,
) -> dict[str, object]:
    normalized_tenant_id = int(tenant_id)
    target_plan = get_plan_by_code(target_plan_code)
    if target_plan is None:
        raise ValueError("plan not found")

    current = _get_or_create_subscription(normalized_tenant_id)
    current_plan_code = str(current.get("plan_code") or "")
    current_status = str(current.get("status") or "trial").lower()

    mode = str(effective or "auto").strip().lower()
    if mode not in {"auto", "immediate", "next_period"}:
        raise ValueError("effective must be one of: auto, immediate, next_period")

    if mode == "auto":
        mode = "immediate" if _plan_rank(str(target_plan["code"])) >= _plan_rank(current_plan_code) else "next_period"

    if mode == "immediate":
        updated = ensure_tenant_subscription(
            normalized_tenant_id,
            plan_code=str(target_plan["code"]),
            status=current_status,
            trial_ends_at=str(current.get("trial_ends_at") or "") or None,
            current_period_start=str(current.get("current_period_start") or "") or None,
            current_period_end=str(current.get("current_period_end") or "") or None,
            next_plan_code=None,
        )
    else:
        updated = ensure_tenant_subscription(
            normalized_tenant_id,
            plan_code=current_plan_code,
            status=current_status,
            trial_ends_at=str(current.get("trial_ends_at") or "") or None,
            current_period_start=str(current.get("current_period_start") or "") or None,
            current_period_end=str(current.get("current_period_end") or "") or None,
            next_plan_code=str(target_plan["code"]),
        )

    _audit_billing(
        tenant_id=normalized_tenant_id,
        action="billing.subscription.plan.changed",
        result="success",
        actor=actor,
        metadata={
            "old_plan": current_plan_code,
            "new_plan": str(target_plan["code"]),
            "effective": mode,
            "reason": reason,
        },
    )

    return {
        "subscription": updated,
        "effective": mode,
        "old_plan": current_plan_code,
        "new_plan": str(target_plan["code"]),
    }


def assert_billing_write_allowed(tenant_id: int, *, action: str) -> None:
    normalized_tenant_id = int(tenant_id)
    if normalized_tenant_id <= 0:
        raise HTTPException(status_code=400, detail="invalid tenant_id")

    try:
        subscription = _get_or_create_subscription(normalized_tenant_id)
    except ValueError as exc:
        if "not found" in str(exc):
            raise HTTPException(status_code=404, detail="tenant not found") from exc
        raise

    status = str(subscription.get("status", "trial")).lower()
    if status not in WRITE_ALLOWED_STATUSES:
        _audit_billing(
            actor="system.billing",
            tenant_id=normalized_tenant_id,
            action="billing.enforcement.blocked",
            result="blocked",
            metadata={
                "reason": "subscription_inactive",
                "subscription_status": status,
                "action": action,
            },
        )
        raise HTTPException(
            status_code=403,
            detail=f"billing_required: tenant subscription is '{status}' (read-only mode)",
        )


def assert_quota_with_increment(tenant_id: int, quota_key: str, *, increment: int = 1) -> dict[str, object]:
    info = check_quota(tenant_id=int(tenant_id), quota_key=quota_key)
    limit_value = int(info.get("limit_value") or 0)
    current_value = int(info.get("current_value") or 0)
    projected = current_value + max(0, int(increment))

    if limit_value > 0 and projected > limit_value:
        normalized_tenant_id = int(tenant_id)
        normalized_key = str(quota_key).strip().lower()
        _audit_billing(
            actor="system.billing",
            tenant_id=normalized_tenant_id,
            action="billing.limit.exceeded",
            result="blocked",
            metadata={
                "quota_key": normalized_key,
                "limit_value": limit_value,
                "current_value": current_value,
                "projected_value": projected,
            },
        )
        raise HTTPException(
            status_code=403,
            detail=(
                f"billing_required: quota exceeded for '{normalized_key}' "
                f"(limit={limit_value}, current={current_value}, projected={projected})"
            ),
        )

    return {
        "tenant_id": int(tenant_id),
        "quota_key": str(quota_key).strip().lower(),
        "limit_value": limit_value,
        "current_value": current_value,
        "projected_value": projected,
        "within_limit": True,
    }


def get_usage_snapshot(tenant_id: int, *, since_iso: str | None = None) -> dict[str, int]:
    normalized_tenant_id = int(tenant_id)

    since = since_iso
    if since is None:
        subscription = get_tenant_subscription(normalized_tenant_id)
        since = str(subscription.get("current_period_start") or "").strip() if subscription else ""
        if not since:
            now = _now()
            since = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()

    api_calls = get_usage_sum(normalized_tenant_id, metric="api_calls", since_iso=since)
    ai_usage = get_usage_sum(normalized_tenant_id, metric="ai_requests", since_iso=since)

    try:
        from app.modules.auth.local_users_service import local_user_store

        active_users = len(local_user_store.list_users(tenant_id=normalized_tenant_id))
    except Exception:
        active_users = 0

    try:
        from app.modules.backup.service import list_backup_history

        rows = list_backup_history(tenant_id=normalized_tenant_id)
        total_bytes = sum(max(0, int(item.get("size_bytes") or 0)) for item in rows)
        storage_mb = int(total_bytes / (1024 * 1024))
    except Exception:
        storage_mb = 0

    return {
        "api_calls": int(api_calls),
        "ai_usage": int(ai_usage),
        "active_users": int(active_users),
        "storage_mb": int(storage_mb),
    }


def get_tenant_billing_state(tenant_id: int) -> dict[str, object]:
    normalized_tenant_id = int(tenant_id)
    tenant = get_tenant(normalized_tenant_id)
    if tenant is None:
        raise ValueError("tenant not found")

    subscription = _get_or_create_subscription(normalized_tenant_id)

    quotas = resolve_tenant_quotas(normalized_tenant_id)
    usage = get_usage_snapshot(
        normalized_tenant_id,
        since_iso=str(subscription.get("current_period_start") or "") or None,
    )
    status = str(subscription.get("status", "trial")).lower()
    billing_state = "read_write" if status in WRITE_ALLOWED_STATUSES else "read_only"

    return {
        "tenant_id": normalized_tenant_id,
        "plan_code": str(subscription.get("plan_code", "")),
        "plan_id": int(subscription.get("plan_id") or 0),
        "next_plan_code": subscription.get("next_plan_code"),
        "subscription_status": status,
        "billing_state": billing_state,
        "period_start": subscription.get("current_period_start"),
        "period_end": subscription.get("current_period_end"),
        "limits": quotas,
        "usage": usage,
        "subscription": subscription,
    }


def clear_billing_state() -> None:
    with _state_lock:
        _state.subscriptions.clear()
