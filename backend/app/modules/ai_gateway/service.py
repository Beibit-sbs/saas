from __future__ import annotations
from app.core.db import get_raw_conn
from app.core.config import is_runtime_schema_bootstrap_enabled

import json
import os
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime, timezone
from threading import Lock
from typing import Any, Protocol
import math

import httpx
from fastapi import HTTPException

from app.modules.integrations.service import get_ai_provider_runtime_config
from app.modules.integrations.service import get_global_runtime_value
from app.modules.integrations.service import get_runtime_value
from app.modules.observability.metrics import (
    observe_ai_budget_status,
    observe_ai_cost_summary,
    observe_ai_slo_compliance,
    observe_ai_guardrail_evaluation,
    observe_ai_guardrail_blocked,
    observe_ai_routing_selection,
)
from app.modules.ai_guardrails import GuardrailEngine, GuardrailResult
from app.modules.ai_guardrails.schemas import GuardrailPolicy
from app.modules.security.db_tenant_context import set_db_tenant_context
from app.modules.security.url_validation import validate_external_https_url

try:
    import psycopg
except ImportError:  # pragma: no cover
    psycopg = None


_limit_lock = Lock()
_limit_events: dict[tuple[str, str], deque[float]] = defaultdict(deque)

_registry_lock = Lock()
_model_registry: dict[str, dict[str, object]] = {}

_usage_lock = Lock()
_usage_logs: deque[dict[str, object]] = deque(maxlen=2000)

_routing_lock = Lock()
_routing_policies: dict[int, dict[int, dict[str, object]]] = {}
_routing_policy_counters: dict[int, int] = {}
_routing_log_lock = Lock()
_routing_selection_log: deque[dict[str, object]] = deque(maxlen=200)

_budget_lock = Lock()
_usage_budgets: dict[int, dict[str, dict[str, object]]] = {}

_price_lock = Lock()
_usage_token_prices: dict[int, dict[str, dict[str, object]]] = {}

_slo_lock = Lock()
_usage_slo_policies: dict[int, dict[str, dict[str, object]]] = {}

_daily_cost_lock = Lock()
_usage_cost_daily_aggregates: dict[int, dict[str, dict[str, object]]] = {}

_safety_lock = Lock()
_ai_safety_policies: dict[int, dict[str, object]] = {}

SUPPORTED_PROVIDERS = ("openai", "gemini", "anthropic", "custom")


DEFAULT_MODELS: tuple[dict[str, object], ...] = (
    {
        "model_key": "openai.default.chat",
        "provider": "openai",
        "provider_model_id": "gpt-4o-mini",
        "display_name": "OpenAI Default Chat",
        "enabled": True,
        "priority": 100,
        "metadata": {},
    },
    {
        "model_key": "gemini.default.chat",
        "provider": "gemini",
        "provider_model_id": "gemini-1.5-flash",
        "display_name": "Gemini Default Chat",
        "enabled": True,
        "priority": 200,
        "metadata": {},
    },
    {
        "model_key": "anthropic.default.chat",
        "provider": "anthropic",
        "provider_model_id": "claude-3-5-haiku-latest",
        "display_name": "Anthropic Default Chat",
        "enabled": True,
        "priority": 300,
        "metadata": {},
    },
    {
        "model_key": "custom.default.chat",
        "provider": "custom",
        "provider_model_id": "default-chat",
        "display_name": "Custom Default Chat",
        "enabled": False,
        "priority": 400,
        "metadata": {},
    },
)


class AIGatewayError(Exception):
    def __init__(
        self,
        *,
        status_code: int,
        detail: str,
        audit_reason: str,
        provider: str | None = None,
        model: str | None = None,
    ) -> None:
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail
        self.audit_reason = audit_reason
        self.provider = provider
        self.model = model


class AIProviderTimeoutError(Exception):
    pass


class AIProviderExecutionError(Exception):
    def __init__(self, message: str, *, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


@dataclass
class NormalizedChatResult:
    provider: str
    output_text: str
    finish_reason: str | None
    provider_response_id: str | None
    usage: dict[str, int | None]


class AIProviderAdapter(Protocol):
    provider: str

    def execute_chat(
        self,
        *,
        provider_model_id: str,
        messages: list[dict[str, str]],
        temperature: float | None,
        max_tokens: int | None,
        runtime_config: dict[str, str],
    ) -> NormalizedChatResult:
        ...


def _db_url() -> str | None:
    return os.getenv("DATABASE_URL")


def _use_database() -> bool:
    return bool(_db_url()) and psycopg is not None


def _should_fallback_to_memory(exc: Exception) -> bool:
    if isinstance(exc, RuntimeError) and str(exc) == "database unavailable":
        return True
    if isinstance(exc, (ConnectionError, TimeoutError, OSError, ValueError)):
        return True
    if psycopg is not None and isinstance(exc, (psycopg.OperationalError, psycopg.InterfaceError)):
        return True
    return False


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _timeout() -> float:
    raw = os.getenv("AI_PROVIDER_TIMEOUT_SECONDS", "8").strip()
    try:
        return max(1.0, float(raw))
    except ValueError:
        return 8.0


def _runtime_int(setting_key: str, env_name: str, default: int) -> int:
    raw = get_global_runtime_value(setting_key, env_name, str(default)).strip()
    try:
        return int(raw)
    except ValueError:
        return default


def _rate_limit_window_seconds() -> int:
    return max(1, _runtime_int("ai.rate_limit.window_seconds", "AI_RATE_LIMIT_WINDOW_SECONDS", 60))


def _provider_limit(provider: str) -> int:
    env_name = f"AI_RATE_LIMIT_PROVIDER_{provider.upper()}_LIMIT"
    return max(0, _runtime_int(f"ai.rate_limit.provider.{provider}", env_name, 30))


def _user_limit(actor: str) -> int:
    normalized_actor = actor.strip().lower().replace("@", "_").replace(".", "_")
    env_name = f"AI_RATE_LIMIT_USER_{normalized_actor.upper()}_LIMIT"
    specific = _runtime_int(f"ai.rate_limit.user.{normalized_actor}", env_name, -1)
    if specific >= 0:
        return specific
    return max(0, _runtime_int("ai.rate_limit.user.default", "AI_RATE_LIMIT_USER_LIMIT", 10))


def _role_limit(role: str) -> int:
    normalized_role = role.strip().lower()
    env_name = f"AI_RATE_LIMIT_ROLE_{normalized_role.upper()}_LIMIT"
    specific = _runtime_int(f"ai.rate_limit.role.{normalized_role}", env_name, -1)
    if specific >= 0:
        return specific
    return max(0, _runtime_int("ai.rate_limit.role.default", "AI_RATE_LIMIT_ROLE_LIMIT", 50))


def clear_rate_limit_state() -> None:
    with _limit_lock:
        _limit_events.clear()


def clear_ai_gateway_state() -> None:
    clear_rate_limit_state()
    with _registry_lock:
        _model_registry.clear()
    with _usage_lock:
        _usage_logs.clear()
    with _routing_lock:
        _routing_policies.clear()
        _routing_policy_counters.clear()
    with _routing_log_lock:
        _routing_selection_log.clear()
    with _budget_lock:
        _usage_budgets.clear()
    with _price_lock:
        _usage_token_prices.clear()
    with _slo_lock:
        _usage_slo_policies.clear()
    with _daily_cost_lock:
        _usage_cost_daily_aggregates.clear()

    with _safety_lock:
        _ai_safety_policies.clear()


def list_usage_token_prices(*, tenant_id: int) -> list[dict[str, object]]:
    normalized_tenant_id = _normalize_tenant_id(tenant_id)
    with _price_lock:
        rows = [dict(item) for item in _usage_token_prices.get(normalized_tenant_id, {}).values()]
    return sorted(rows, key=lambda item: (str(item.get("provider") or ""), str(item.get("model_key") or "")))


def upsert_usage_token_price(
    provider: str,
    model_key: str,
    payload: dict[str, object],
    *,
    tenant_id: int,
) -> dict[str, object]:
    normalized_tenant_id = _normalize_tenant_id(tenant_id)
    normalized_provider = str(provider or "").strip().lower()
    if normalized_provider not in SUPPORTED_PROVIDERS:
        raise ValueError("unsupported provider")

    normalized_model_key = _normalize_model_key(model_key)
    if not normalized_model_key:
        raise ValueError("model_key is required")

    input_price_per_1k = max(0.0, float(payload.get("input_price_per_1k") or 0.0))
    output_price_per_1k = max(0.0, float(payload.get("output_price_per_1k") or 0.0))

    row = {
        "tenant_id": normalized_tenant_id,
        "provider": normalized_provider,
        "model_key": normalized_model_key,
        "input_price_per_1k": round(input_price_per_1k, 6),
        "output_price_per_1k": round(output_price_per_1k, 6),
        "updated_at": _now_iso(),
    }

    key = f"{normalized_provider}:{normalized_model_key}"
    with _price_lock:
        tenant_rows = _usage_token_prices.setdefault(normalized_tenant_id, {})
        tenant_rows[key] = dict(row)

    return dict(row)


def list_slo_policies(*, tenant_id: int) -> list[dict[str, object]]:
    normalized_tenant_id = _normalize_tenant_id(tenant_id)
    with _slo_lock:
        rows = [dict(item) for item in _usage_slo_policies.get(normalized_tenant_id, {}).values()]
    return sorted(rows, key=lambda item: str(item.get("model_key") or ""))


def upsert_slo_policy(model_key: str, payload: dict[str, object], *, tenant_id: int) -> dict[str, object]:
    normalized_tenant_id = _normalize_tenant_id(tenant_id)
    normalized_model_key = _normalize_model_key(model_key)
    if not normalized_model_key:
        raise ValueError("model_key is required")

    p95_latency_ms = max(1, int(payload.get("p95_latency_ms") or 1000))
    max_error_rate_pct = float(payload.get("max_error_rate_pct") or 5.0)
    if max_error_rate_pct < 0.0 or max_error_rate_pct > 100.0:
        raise ValueError("max_error_rate_pct must be between 0 and 100")

    row = {
        "tenant_id": normalized_tenant_id,
        "model_key": normalized_model_key,
        "p95_latency_ms": p95_latency_ms,
        "max_error_rate_pct": round(max_error_rate_pct, 2),
        "updated_at": _now_iso(),
    }

    with _slo_lock:
        tenant_rows = _usage_slo_policies.setdefault(normalized_tenant_id, {})
        tenant_rows[normalized_model_key] = dict(row)
    return dict(row)


def list_slo_compliance(*, tenant_id: int, limit: int = 5000) -> list[dict[str, object]]:
    normalized_tenant_id = _normalize_tenant_id(tenant_id)
    rows = list_usage_logs(limit=max(1, min(limit, 5000)), tenant_id=normalized_tenant_id)

    with _slo_lock:
        policies = {key: dict(value) for key, value in _usage_slo_policies.get(normalized_tenant_id, {}).items()}

    grouped: dict[str, list[dict[str, object]]] = {}
    for row in rows:
        model_key = str(row.get("model_key") or "unknown")
        grouped.setdefault(model_key, []).append(row)

    result: list[dict[str, object]] = []
    for model_key, model_rows in grouped.items():
        latencies = sorted(max(0, int(item.get("latency_ms") or 0)) for item in model_rows)
        requests_total = len(model_rows)
        if requests_total == 0:
            continue
        failed_count = sum(1 for item in model_rows if str(item.get("outcome") or "").strip().lower() == "failed")
        p95_index = max(0, int(math.ceil(requests_total * 0.95)) - 1)
        p95_observed = int(latencies[p95_index])
        error_rate_observed = round(float((failed_count / requests_total) * 100.0), 2)

        policy = policies.get(model_key)
        if policy is None:
            policy = {
                "p95_latency_ms": 1000,
                "max_error_rate_pct": 5.0,
            }

        p95_target = int(policy.get("p95_latency_ms") or 1000)
        error_rate_target = float(policy.get("max_error_rate_pct") or 5.0)
        latency_compliant = p95_observed <= p95_target
        error_rate_compliant = error_rate_observed <= error_rate_target

        result.append(
            {
                "tenant_id": normalized_tenant_id,
                "model_key": model_key,
                "requests_total": requests_total,
                "p95_latency_ms_observed": p95_observed,
                "error_rate_pct_observed": error_rate_observed,
                "p95_latency_ms_target": p95_target,
                "max_error_rate_pct_target": round(error_rate_target, 2),
                "latency_compliant": latency_compliant,
                "error_rate_compliant": error_rate_compliant,
                "compliant": latency_compliant and error_rate_compliant,
            }
        )

    sorted_result = sorted(result, key=lambda item: str(item.get("model_key") or ""))
    observe_ai_slo_compliance(sorted_result)
    return sorted_result


def list_slo_violations(*, tenant_id: int, limit: int = 5000) -> list[dict[str, object]]:
    rows = list_slo_compliance(tenant_id=tenant_id, limit=limit)
    result: list[dict[str, object]] = []
    for row in rows:
        if bool(row.get("compliant", True)):
            continue
        violation_types: list[str] = []
        if not bool(row.get("latency_compliant", True)):
            violation_types.append("latency")
        if not bool(row.get("error_rate_compliant", True)):
            violation_types.append("error_rate")
        result.append({**row, "violation_types": violation_types})
    return sorted(result, key=lambda item: str(item.get("model_key") or ""))


# ---------------------------------------------------------------------------
# Tenant AI Safety Policy override
# ---------------------------------------------------------------------------

_DEFAULT_SAFETY_POLICY: dict[str, object] = {
    "injection_detection": True,
    "content_moderation": True,
    "pii_detection": True,
    "audit_only": False,
    "blocked_patterns": [],
}


def get_ai_safety_policy(*, tenant_id: int) -> dict[str, object]:
    normalized = _normalize_tenant_id(tenant_id)
    with _safety_lock:
        override = _ai_safety_policies.get(normalized)
    if override is None:
        return dict(_DEFAULT_SAFETY_POLICY)
    merged = dict(_DEFAULT_SAFETY_POLICY)
    merged.update(override)
    return merged


def upsert_ai_safety_policy(payload: dict[str, object], *, tenant_id: int) -> dict[str, object]:
    normalized = _normalize_tenant_id(tenant_id)
    allowed = {"injection_detection", "content_moderation", "pii_detection", "audit_only", "blocked_patterns"}
    cleaned: dict[str, object] = {}
    for k in allowed:
        if k in payload:
            cleaned[k] = payload[k]
    with _safety_lock:
        existing = dict(_ai_safety_policies.get(normalized, {}))
        existing.update(cleaned)
        existing["tenant_id"] = normalized
        _ai_safety_policies[normalized] = existing
    return get_ai_safety_policy(tenant_id=normalized)


def list_ai_safety_policies() -> list[dict[str, object]]:
    with _safety_lock:
        rows = [dict(v) for v in _ai_safety_policies.values()]
    return sorted(rows, key=lambda r: int(r.get("tenant_id") or 0))


def _build_guardrail_policy_for_tenant(tenant_id: int) -> GuardrailPolicy:
    data = get_ai_safety_policy(tenant_id=tenant_id)
    return GuardrailPolicy(
        injection_detection=bool(data.get("injection_detection", True)),
        content_moderation=bool(data.get("content_moderation", True)),
        pii_detection=bool(data.get("pii_detection", True)),
        audit_only=bool(data.get("audit_only", False)),
        blocked_patterns=list(data.get("blocked_patterns") or []),
    )


def refresh_usage_cost_daily_aggregation(
    *,
    tenant_id: int,
    days: int = 30,
    limit: int = 5000,
) -> list[dict[str, object]]:
    normalized_tenant_id = _normalize_tenant_id(tenant_id)
    normalized_days = max(1, min(int(days), 365))
    rows = list_usage_logs(limit=max(1, min(limit, 5000)), tenant_id=normalized_tenant_id)
    now_date = datetime.now(timezone.utc).date()
    usd_per_token = 0.80 / 1_000_000.0

    grouped: dict[str, dict[str, object]] = {}
    for row in rows:
        day_key = _usage_row_date(row)
        if day_key is None:
            continue
        day_delta = (now_date - datetime.fromisoformat(day_key).date()).days
        if day_delta < 0 or day_delta >= normalized_days:
            continue

        provider = str(row.get("provider") or "unknown").strip().lower() or "unknown"
        model_key = str(row.get("model_key") or "unknown").strip() or "unknown"
        aggregate_key = f"{day_key}:{provider}:{model_key}"
        item = grouped.get(aggregate_key)
        if item is None:
            item = {
                "tenant_id": normalized_tenant_id,
                "date": day_key,
                "provider": provider,
                "model_key": model_key,
                "requests_total": 0,
                "total_tokens": 0,
                "estimated_cost_usd": 0.0,
                "updated_at": _now_iso(),
            }
            grouped[aggregate_key] = item

        tokens = max(0, int(row.get("total_tokens") or 0))
        item["requests_total"] = int(item["requests_total"]) + 1
        item["total_tokens"] = int(item["total_tokens"]) + tokens
        item["estimated_cost_usd"] = round(float(int(item["total_tokens"]) * usd_per_token), 6)
        item["updated_at"] = _now_iso()

    with _daily_cost_lock:
        tenant_rows = _usage_cost_daily_aggregates.setdefault(normalized_tenant_id, {})
        tenant_rows.clear()
        for key, value in grouped.items():
            tenant_rows[key] = dict(value)

    return list_usage_cost_daily_aggregation(tenant_id=normalized_tenant_id, days=normalized_days)


def list_usage_cost_daily_aggregation(*, tenant_id: int, days: int = 30) -> list[dict[str, object]]:
    normalized_tenant_id = _normalize_tenant_id(tenant_id)
    normalized_days = max(1, min(int(days), 365))
    now_date = datetime.now(timezone.utc).date()

    with _daily_cost_lock:
        tenant_rows = list(_usage_cost_daily_aggregates.get(normalized_tenant_id, {}).values())

    if not tenant_rows:
        return refresh_usage_cost_daily_aggregation(tenant_id=normalized_tenant_id, days=normalized_days)

    result: list[dict[str, object]] = []
    for row in tenant_rows:
        day_key = str(row.get("date") or "").strip()
        if not day_key:
            continue
        try:
            day_delta = (now_date - datetime.fromisoformat(day_key).date()).days
        except ValueError:
            continue
        if day_delta < 0 or day_delta >= normalized_days:
            continue
        result.append(dict(row))

    return sorted(
        result,
        key=lambda item: (
            str(item.get("date") or ""),
            str(item.get("provider") or ""),
            str(item.get("model_key") or ""),
        ),
        reverse=True,
    )


def get_usage_budget(*, tenant_id: int) -> dict[str, object]:
    normalized_tenant_id = _normalize_tenant_id(tenant_id)
    scope_key = _budget_scope_key("tenant", None)
    with _budget_lock:
        tenant_budgets = _usage_budgets.setdefault(normalized_tenant_id, {})
        current = tenant_budgets.get(scope_key)
        if current is None:
            current = _default_budget_row(normalized_tenant_id, scope="tenant", scope_id=None)
            tenant_budgets[scope_key] = dict(current)
        return dict(current)


def update_usage_budget(payload: dict[str, object], *, tenant_id: int) -> dict[str, object]:
    normalized_tenant_id = _normalize_tenant_id(tenant_id)
    budget_limit = max(0.0, float(payload.get("budget_limit_usd") or 0.0))
    alert_threshold = int(payload.get("alert_threshold_pct") or 80)
    if alert_threshold < 1 or alert_threshold > 100:
        raise ValueError("alert_threshold_pct must be between 1 and 100")

    next_row = {
        "tenant_id": normalized_tenant_id,
        "scope": "tenant",
        "scope_id": None,
        "budget_limit_usd": round(budget_limit, 6),
        "alert_threshold_pct": alert_threshold,
        "hard_cap": bool(payload.get("hard_cap", False)),
        "updated_at": _now_iso(),
    }
    with _budget_lock:
        tenant_budgets = _usage_budgets.setdefault(normalized_tenant_id, {})
        tenant_budgets[_budget_scope_key("tenant", None)] = dict(next_row)
    return dict(next_row)


def _budget_scope_key(scope: str, scope_id: str | None) -> str:
    normalized_scope = str(scope or "tenant").strip().lower()
    normalized_scope_id = str(scope_id or "").strip().lower()
    return f"{normalized_scope}:{normalized_scope_id}"


def _default_budget_row(tenant_id: int, *, scope: str, scope_id: str | None) -> dict[str, object]:
    return {
        "tenant_id": int(tenant_id),
        "scope": str(scope),
        "scope_id": str(scope_id).strip() if scope_id is not None else None,
        "budget_limit_usd": 0.0,
        "alert_threshold_pct": 80,
        "hard_cap": False,
        "updated_at": _now_iso(),
    }


def upsert_usage_budget_scoped(payload: dict[str, object], *, tenant_id: int) -> dict[str, object]:
    normalized_tenant_id = _normalize_tenant_id(tenant_id)
    scope = str(payload.get("scope") or "tenant").strip().lower()
    if scope not in {"tenant", "department", "user"}:
        raise ValueError("scope must be one of: tenant, department, user")

    raw_scope_id = payload.get("scope_id")
    scope_id = str(raw_scope_id).strip() if raw_scope_id is not None else None
    if scope in {"department", "user"} and not scope_id:
        raise ValueError("scope_id is required for non-tenant scope")
    if scope == "tenant":
        scope_id = None

    budget_limit = max(0.0, float(payload.get("budget_limit_usd") or 0.0))
    alert_threshold = int(payload.get("alert_threshold_pct") or 80)
    if alert_threshold < 1 or alert_threshold > 100:
        raise ValueError("alert_threshold_pct must be between 1 and 100")

    next_row = {
        "tenant_id": normalized_tenant_id,
        "scope": scope,
        "scope_id": scope_id,
        "budget_limit_usd": round(budget_limit, 6),
        "alert_threshold_pct": alert_threshold,
        "hard_cap": bool(payload.get("hard_cap", False)),
        "updated_at": _now_iso(),
    }

    with _budget_lock:
        tenant_budgets = _usage_budgets.setdefault(normalized_tenant_id, {})
        tenant_budgets[_budget_scope_key(scope, scope_id)] = dict(next_row)
    return dict(next_row)


def list_usage_budgets(*, tenant_id: int) -> list[dict[str, object]]:
    normalized_tenant_id = _normalize_tenant_id(tenant_id)
    with _budget_lock:
        tenant_budgets = _usage_budgets.setdefault(normalized_tenant_id, {})
        tenant_scope_key = _budget_scope_key("tenant", None)
        if tenant_scope_key not in tenant_budgets:
            tenant_budgets[tenant_scope_key] = _default_budget_row(normalized_tenant_id, scope="tenant", scope_id=None)
        rows = [dict(item) for item in tenant_budgets.values()]
    return sorted(rows, key=lambda item: (str(item.get("scope") or ""), str(item.get("scope_id") or "")))


def delete_usage_budget_scoped(*, tenant_id: int, scope: str, scope_id: str | None) -> dict[str, object]:
    normalized_tenant_id = _normalize_tenant_id(tenant_id)
    normalized_scope = str(scope or "tenant").strip().lower()
    if normalized_scope not in {"tenant", "department", "user"}:
        raise ValueError("scope must be one of: tenant, department, user")

    normalized_scope_id = str(scope_id or "").strip() if scope_id is not None else None
    if normalized_scope in {"department", "user"} and not normalized_scope_id:
        raise ValueError("scope_id is required for non-tenant scope")
    if normalized_scope == "tenant":
        normalized_scope_id = None

    key = _budget_scope_key(normalized_scope, normalized_scope_id)
    with _budget_lock:
        tenant_budgets = _usage_budgets.setdefault(normalized_tenant_id, {})
        current = tenant_budgets.get(key)
        if current is None:
            raise ValueError("usage budget scope not found")
        deleted = dict(current)
        del tenant_budgets[key]

        tenant_scope_key = _budget_scope_key("tenant", None)
        if tenant_scope_key not in tenant_budgets:
            tenant_budgets[tenant_scope_key] = _default_budget_row(normalized_tenant_id, scope="tenant", scope_id=None)

    return deleted


def list_usage_budget_status(*, tenant_id: int) -> list[dict[str, object]]:
    normalized_tenant_id = _normalize_tenant_id(tenant_id)
    with _budget_lock:
        tenant_budgets = _usage_budgets.setdefault(normalized_tenant_id, {})
        tenant_scope_key = _budget_scope_key("tenant", None)
        if tenant_scope_key not in tenant_budgets:
            tenant_budgets[tenant_scope_key] = _default_budget_row(normalized_tenant_id, scope="tenant", scope_id=None)
        rows = [dict(item) for item in tenant_budgets.values()]

    usd_per_token = 0.80 / 1_000_000.0
    usage_rows = list_usage_logs(limit=5000, tenant_id=normalized_tenant_id)

    result: list[dict[str, object]] = []
    for row in rows:
        scope = str(row.get("scope") or "tenant").strip().lower()
        scope_id = row.get("scope_id")
        current_cost = _usage_cost_for_scope(
            usage_rows,
            scope=scope,
            scope_id=str(scope_id).strip() if scope_id is not None else None,
            usd_per_token=usd_per_token,
        )
        budget_limit_usd = float(row.get("budget_limit_usd") or 0.0)
        utilization_pct = float((current_cost / budget_limit_usd) * 100.0) if budget_limit_usd > 0 else 0.0
        alert_threshold = int(row.get("alert_threshold_pct") or 80)
        hard_cap = bool(row.get("hard_cap", False))
        hard_cap_exceeded = hard_cap and budget_limit_usd > 0 and current_cost > budget_limit_usd

        result.append(
            {
                "tenant_id": normalized_tenant_id,
                "scope": scope,
                "scope_id": scope_id,
                "budget_limit_usd": round(budget_limit_usd, 6),
                "current_cost_usd": round(current_cost, 6),
                "utilization_pct": round(utilization_pct, 2),
                "alert_threshold_pct": alert_threshold,
                "budget_alert": utilization_pct >= float(alert_threshold),
                "hard_cap": hard_cap,
                "hard_cap_exceeded": hard_cap_exceeded,
                "updated_at": str(row.get("updated_at") or _now_iso()),
            }
        )

    sorted_result = sorted(result, key=lambda item: (str(item.get("scope") or ""), str(item.get("scope_id") or "")))
    observe_ai_budget_status(tenant_id=normalized_tenant_id, rows=sorted_result)
    return sorted_result


def _usage_cost_for_scope(
    rows: list[dict[str, object]],
    *,
    scope: str,
    scope_id: str | None,
    usd_per_token: float,
) -> float:
    normalized_scope = str(scope or "tenant").strip().lower()
    normalized_scope_id = str(scope_id or "").strip().lower()

    if normalized_scope == "tenant":
        tokens = sum(max(0, int(item.get("total_tokens") or 0)) for item in rows)
        return float(tokens * usd_per_token)

    if normalized_scope == "user":
        tokens = sum(
            max(0, int(item.get("total_tokens") or 0))
            for item in rows
            if str(item.get("actor") or "").strip().lower() == normalized_scope_id
        )
        return float(tokens * usd_per_token)

    if normalized_scope == "department":
        rows_with_department = [item for item in rows if str(item.get("department") or "").strip()]
        if rows_with_department:
            tokens = sum(
                max(0, int(item.get("total_tokens") or 0))
                for item in rows_with_department
                if str(item.get("department") or "").strip().lower() == normalized_scope_id
            )
            return float(tokens * usd_per_token)

        # Legacy fallback for existing logs that do not yet contain department attribution.
        tokens = sum(max(0, int(item.get("total_tokens") or 0)) for item in rows)
        return float(tokens * usd_per_token)

    tokens = sum(max(0, int(item.get("total_tokens") or 0)) for item in rows)
    return float(tokens * usd_per_token)


def _detect_cost_anomaly(rows: list[dict[str, object]], *, usd_per_token: float) -> tuple[bool, float, str | None]:
    if not rows:
        return False, 0.0, None

    costs = [float(max(0, int(item.get("total_tokens") or 0)) * usd_per_token) for item in rows]
    if len(costs) < 6:
        return False, 0.0, None

    latest = costs[0]
    baseline = costs[1:]
    mean = sum(baseline) / len(baseline)
    variance = sum((value - mean) ** 2 for value in baseline) / len(baseline)
    std = math.sqrt(max(0.0, variance))
    if std <= 0.0:
        # Flat baseline: if latest sample is significantly larger than baseline mean,
        # treat it as a spike even without variance history.
        if latest > mean * 2.0 and latest > 0:
            return True, 99.0, "flat_baseline_spike"
        return False, 0.0, None

    z_score = (latest - mean) / std
    detected = z_score > 2.0
    reason = "z_score_spike" if detected else None
    return detected, round(float(z_score), 3), reason


def _evaluate_budget_guardrail(*, tenant_id: int, estimated_increment_tokens: int) -> dict[str, object]:
    budget = get_usage_budget(tenant_id=tenant_id)
    budget_limit_usd = float(budget.get("budget_limit_usd") or 0.0)
    alert_threshold_pct = int(budget.get("alert_threshold_pct") or 80)
    hard_cap = bool(budget.get("hard_cap", False))

    if budget_limit_usd <= 0:
        return {
            "budget_limit_usd": 0.0,
            "current_cost_usd": 0.0,
            "projected_cost_usd": 0.0,
            "projected_utilization_pct": 0.0,
            "alert": False,
            "blocked": False,
            "hard_cap": hard_cap,
        }

    usd_per_token = 0.80 / 1_000_000.0
    rows = list_usage_logs(limit=5000, tenant_id=tenant_id)
    total_tokens = sum(max(0, int(item.get("total_tokens") or 0)) for item in rows)
    current_cost = float(total_tokens * usd_per_token)
    projected_cost = current_cost + float(max(0, int(estimated_increment_tokens)) * usd_per_token)
    projected_utilization_pct = float((projected_cost / budget_limit_usd) * 100.0)

    alert = projected_utilization_pct >= float(alert_threshold_pct)
    blocked = hard_cap and projected_cost > budget_limit_usd

    return {
        "budget_limit_usd": round(budget_limit_usd, 6),
        "current_cost_usd": round(current_cost, 6),
        "projected_cost_usd": round(projected_cost, 6),
        "projected_utilization_pct": round(projected_utilization_pct, 2),
        "alert": bool(alert),
        "blocked": bool(blocked),
        "hard_cap": hard_cap,
    }


def list_routing_policies(*, tenant_id: int) -> list[dict[str, object]]:
    normalized_tenant_id = _normalize_tenant_id(tenant_id)
    with _routing_lock:
        tenant_policies = _routing_policies.get(normalized_tenant_id, {})
        rows = [dict(item) for item in tenant_policies.values()]
    return sorted(rows, key=lambda item: int(item.get("id", 0)))


def create_routing_policy(payload: dict[str, Any], *, tenant_id: int) -> dict[str, object]:
    normalized_tenant_id = _normalize_tenant_id(tenant_id)
    name = str(payload.get("name") or "").strip()
    if not name:
        raise ValueError("policy name is required")
    strategy = str(payload.get("strategy") or "priority").strip().lower()
    if strategy != "priority":
        raise ValueError("unsupported strategy")
    rules = list(payload.get("rules") or [])
    fallback_chain = [str(item).strip() for item in list(payload.get("fallback_chain") or []) if str(item).strip()]

    now = _now_iso()
    with _routing_lock:
        next_id = _routing_policy_counters.get(normalized_tenant_id, 0) + 1
        _routing_policy_counters[normalized_tenant_id] = next_id
        tenant_policies = _routing_policies.setdefault(normalized_tenant_id, {})
        row = {
            "id": next_id,
            "tenant_id": normalized_tenant_id,
            "name": name,
            "strategy": strategy,
            "enabled": bool(payload.get("enabled", True)),
            "rules": rules,
            "fallback_chain": fallback_chain,
            "created_at": now,
            "updated_at": now,
        }
        tenant_policies[next_id] = row
        return dict(row)


def update_routing_policy(policy_id: int, payload: dict[str, Any], *, tenant_id: int) -> dict[str, object]:
    normalized_tenant_id = _normalize_tenant_id(tenant_id)
    normalized_policy_id = int(policy_id)
    with _routing_lock:
        tenant_policies = _routing_policies.get(normalized_tenant_id, {})
        current = tenant_policies.get(normalized_policy_id)
        if current is None:
            raise ValueError("routing policy not found")

        name = str(payload.get("name") or current.get("name") or "").strip()
        if not name:
            raise ValueError("policy name is required")
        strategy = str(payload.get("strategy") or current.get("strategy") or "priority").strip().lower()
        if strategy != "priority":
            raise ValueError("unsupported strategy")

        updated = {
            **current,
            "name": name,
            "strategy": strategy,
            "enabled": bool(payload.get("enabled", current.get("enabled", True))),
            "rules": list(payload.get("rules") if "rules" in payload else current.get("rules") or []),
            "fallback_chain": [
                str(item).strip()
                for item in list(payload.get("fallback_chain") if "fallback_chain" in payload else current.get("fallback_chain") or [])
                if str(item).strip()
            ],
            "updated_at": _now_iso(),
        }
        tenant_policies[normalized_policy_id] = updated
        return dict(updated)


def delete_routing_policy(policy_id: int, *, tenant_id: int) -> None:
    normalized_tenant_id = _normalize_tenant_id(tenant_id)
    normalized_policy_id = int(policy_id)
    with _routing_lock:
        tenant_policies = _routing_policies.get(normalized_tenant_id, {})
        if normalized_policy_id not in tenant_policies:
            raise ValueError("routing policy not found")
        del tenant_policies[normalized_policy_id]


def _record_routing_selection(model_key: str, meta: dict[str, object], *, tenant_id: int) -> None:
    entry: dict[str, object] = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "tenant_id": tenant_id,
        "model_key": model_key,
        **meta,
    }
    with _routing_log_lock:
        _routing_selection_log.appendleft(entry)
    observe_ai_routing_selection(
        tenant_id=tenant_id,
        mode=str(meta.get("mode") or "auto"),
        selection=str(meta.get("selection") or "unknown"),
    )


def list_routing_selection_log(*, tenant_id: int | None = None, limit: int = 50) -> list[dict[str, object]]:
    with _routing_log_lock:
        rows = list(_routing_selection_log)
    if tenant_id is not None:
        rows = [r for r in rows if int(r.get("tenant_id", -1)) == int(tenant_id)]
    return rows[:max(1, min(limit, 200))]


def _select_auto_model(payload: dict[str, Any], *, tenant_id: int) -> tuple[str, dict[str, object]]:
    models = list_models(include_disabled=False, tenant_id=tenant_id)
    if not models:
        raise ValueError("no enabled models configured for auto routing")

    enabled_keys = {str(item.get("model_key") or "").strip() for item in models}
    task_type = str(payload.get("task_type") or "").strip().lower()

    with _routing_lock:
        tenant_policies = list((_routing_policies.get(tenant_id) or {}).values())
    tenant_policies.sort(key=lambda item: int(item.get("id", 0)))

    for policy in tenant_policies:
        if not bool(policy.get("enabled", True)):
            continue
        rules = list(policy.get("rules") or [])
        rules.sort(key=lambda item: int((item or {}).get("priority", 100)))
        for rule in rules:
            if not isinstance(rule, dict):
                continue
            rule_task = str(rule.get("task_type") or "").strip().lower()
            target_model = str(rule.get("target_model") or "").strip()
            if task_type and rule_task == task_type and target_model in enabled_keys:
                meta: dict[str, object] = {
                    "mode": "auto",
                    "selection": "policy_rule",
                    "policy_id": int(policy.get("id", 0)),
                    "task_type": task_type,
                }
                _record_routing_selection(target_model, meta, tenant_id=tenant_id)
                return target_model, meta

    selected = str(models[0].get("model_key") or "").strip()
    if not selected:
        raise ValueError("no enabled models configured for auto routing")
    meta = {
        "mode": "auto",
        "selection": "priority_default",
        "task_type": task_type or None,
    }
    _record_routing_selection(selected, meta, tenant_id=tenant_id)
    return selected, meta


def _prune(bucket: deque[float], now: float, window_seconds: int) -> None:
    cutoff = now - window_seconds
    while bucket and bucket[0] <= cutoff:
        bucket.popleft()


def enforce_rate_limit(provider: str, actor: str, roles: list[str]) -> dict[str, Any]:
    window_seconds = _rate_limit_window_seconds()
    normalized_provider = provider.strip().lower()
    normalized_actor = actor.strip().lower()
    normalized_roles = [role.strip().lower() for role in roles if role.strip()]
    now = time.time()

    checks: list[tuple[tuple[str, str], int, str]] = [
        (("provider", normalized_provider), _provider_limit(normalized_provider), f"provider:{normalized_provider}"),
        (("user", normalized_actor), _user_limit(normalized_actor), f"user:{normalized_actor}"),
    ]
    for role in normalized_roles:
        checks.append((("role", role), _role_limit(role), f"role:{role}"))

    with _limit_lock:
        for key, limit, label in checks:
            bucket = _limit_events[key]
            _prune(bucket, now, window_seconds)
            if limit > 0 and len(bucket) >= limit:
                retry_after = max(1, int(window_seconds - (now - bucket[0]))) if bucket else window_seconds
                raise ValueError(f"AI Gateway rate limit exceeded for {label}; retry in {retry_after}s")

        for key, _, _ in checks:
            _limit_events[key].append(now)

        provider_bucket = _limit_events[("provider", normalized_provider)]
        user_bucket = _limit_events[("user", normalized_actor)]

    return {
        "window_seconds": window_seconds,
        "provider_limit": _provider_limit(normalized_provider),
        "provider_used": len(provider_bucket),
        "user_limit": _user_limit(normalized_actor),
        "user_used": len(user_bucket),
    }


def _ensure_ai_gateway_tables(conn) -> None:
    if not is_runtime_schema_bootstrap_enabled():
        return
    with conn.cursor() as cur:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS app_ai_models (
                tenant_id BIGINT NOT NULL,
                model_key TEXT NOT NULL,
                provider TEXT NOT NULL,
                provider_model_id TEXT NOT NULL,
                display_name TEXT NOT NULL,
                enabled BOOLEAN NOT NULL DEFAULT TRUE,
                priority INTEGER NOT NULL DEFAULT 100,
                metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                CONSTRAINT pk_app_ai_models_tenant_model PRIMARY KEY (tenant_id, model_key)
            )
            """
        )
        cur.execute("ALTER TABLE app_ai_models ADD COLUMN IF NOT EXISTS tenant_id BIGINT")
        cur.execute("ALTER TABLE app_ai_models ALTER COLUMN tenant_id DROP DEFAULT")
        cur.execute(
            """
            DO $$
            BEGIN
                IF EXISTS (SELECT 1 FROM app_ai_models WHERE tenant_id IS NULL) THEN
                    RAISE EXCEPTION 'ai gateway remediation required: app_ai_models has NULL tenant_id rows';
                END IF;
            END
            $$;
            """
        )
        cur.execute("ALTER TABLE app_ai_models ALTER COLUMN tenant_id SET NOT NULL")
        cur.execute(
            """
            DO $$
            BEGIN
                IF EXISTS (
                    SELECT 1 FROM pg_constraint
                    WHERE conname = 'app_ai_models_pkey'
                      AND conrelid = 'app_ai_models'::regclass
                ) THEN
                    ALTER TABLE app_ai_models DROP CONSTRAINT app_ai_models_pkey;
                END IF;
            END
            $$;
            """
        )
        cur.execute(
            """
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_constraint
                    WHERE conname = 'pk_app_ai_models_tenant_model'
                      AND conrelid = 'app_ai_models'::regclass
                ) THEN
                    ALTER TABLE app_ai_models
                    ADD CONSTRAINT pk_app_ai_models_tenant_model PRIMARY KEY (tenant_id, model_key);
                END IF;
            END
            $$;
            """
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS ix_app_ai_models_tenant_provider_enabled ON app_ai_models (tenant_id, provider, enabled)"
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS app_ai_usage_logs (
                id BIGSERIAL PRIMARY KEY,
                tenant_id BIGINT NOT NULL,
                timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                actor TEXT NOT NULL,
                provider TEXT NOT NULL,
                model_key TEXT NOT NULL,
                provider_model_id TEXT NOT NULL,
                outcome TEXT NOT NULL,
                latency_ms INTEGER NOT NULL,
                input_tokens INTEGER,
                output_tokens INTEGER,
                total_tokens INTEGER,
                failure_reason TEXT,
                correlation_id TEXT
            )
            """
        )
        cur.execute("ALTER TABLE app_ai_usage_logs ADD COLUMN IF NOT EXISTS tenant_id BIGINT")
        cur.execute("ALTER TABLE app_ai_usage_logs ALTER COLUMN tenant_id DROP DEFAULT")
        cur.execute(
            """
            DO $$
            BEGIN
                IF EXISTS (SELECT 1 FROM app_ai_usage_logs WHERE tenant_id IS NULL) THEN
                    RAISE EXCEPTION 'ai gateway remediation required: app_ai_usage_logs has NULL tenant_id rows';
                END IF;
            END
            $$;
            """
        )
        cur.execute("ALTER TABLE app_ai_usage_logs ALTER COLUMN tenant_id SET NOT NULL")
        cur.execute(
            "CREATE INDEX IF NOT EXISTS ix_app_ai_usage_logs_tenant_timestamp ON app_ai_usage_logs (tenant_id, timestamp DESC)"
        )
    conn.commit()


def _seed_default_models_db(conn, tenant_id: int) -> None:
    with conn.cursor() as cur:
        cur.executemany(
            """
            INSERT INTO app_ai_models (tenant_id, model_key, provider, provider_model_id, display_name, enabled, priority, metadata)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s::jsonb)
            ON CONFLICT (tenant_id, model_key) DO NOTHING
            """,
            [
                (
                    tenant_id,
                    item["model_key"],
                    item["provider"],
                    item["provider_model_id"],
                    item["display_name"],
                    item["enabled"],
                    item["priority"],
                    json.dumps(item.get("metadata") or {}, ensure_ascii=False),
                )
                for item in DEFAULT_MODELS
            ],
        )
    conn.commit()


def _tenant_registry_key(tenant_id: int, model_key: str) -> str:
    return f"{tenant_id}:{model_key}"


def _seed_default_models_memory(tenant_id: int) -> None:
    with _registry_lock:
        has_tenant_seed = any(key.startswith(f"{tenant_id}:") for key in _model_registry)
        if has_tenant_seed:
            return
        for item in DEFAULT_MODELS:
            storage_key = _tenant_registry_key(tenant_id, str(item["model_key"]))
            _model_registry[storage_key] = {
                **item,
                "tenant_id": tenant_id,
                "created_at": _now_iso(),
                "updated_at": _now_iso(),
            }


def _normalize_model_key(value: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError("model_key is required")
    if len(normalized) > 120:
        raise ValueError("model_key must be at most 120 characters")
    return normalized


def _normalize_provider(value: str) -> str:
    normalized = value.strip().lower()
    if normalized not in SUPPORTED_PROVIDERS:
        raise ValueError("unknown provider")
    return normalized


def _normalize_tenant_id(value: int | None) -> int:
    if value is None:
        raise ValueError("tenant_id is required")
    tenant_id = int(value)
    if tenant_id <= 0:
        raise ValueError("tenant_id must be positive")
    return tenant_id


def _normalize_model_payload(
    model_key: str,
    provider: str,
    provider_model_id: str,
    display_name: str,
    enabled: bool,
    priority: int,
    metadata: dict[str, Any] | None,
) -> dict[str, object]:
    normalized_provider_model_id = provider_model_id.strip()
    normalized_display_name = display_name.strip()
    if not normalized_provider_model_id:
        raise ValueError("provider_model_id is required")
    if not normalized_display_name:
        raise ValueError("display_name is required")
    if len(normalized_provider_model_id) > 200:
        raise ValueError("provider_model_id must be at most 200 characters")
    if len(normalized_display_name) > 200:
        raise ValueError("display_name must be at most 200 characters")
    if priority < 0 or priority > 10_000:
        raise ValueError("priority must be between 0 and 10000")

    return {
        "model_key": _normalize_model_key(model_key),
        "provider": _normalize_provider(provider),
        "provider_model_id": normalized_provider_model_id,
        "display_name": normalized_display_name,
        "enabled": bool(enabled),
        "priority": int(priority),
        "metadata": metadata or {},
    }


def _model_row_to_dict(row: tuple[Any, ...]) -> dict[str, object]:
    metadata = row[7]
    if isinstance(metadata, str):
        try:
            metadata = json.loads(metadata)
        except json.JSONDecodeError:
            metadata = {}
    if not isinstance(metadata, dict):
        metadata = {}

    created_at = row[8].isoformat() if hasattr(row[8], "isoformat") else str(row[8])
    updated_at = row[9].isoformat() if hasattr(row[9], "isoformat") else str(row[9])

    return {
        "tenant_id": int(row[0]),
        "model_key": row[1],
        "provider": row[2],
        "provider_model_id": row[3],
        "display_name": row[4],
        "enabled": bool(row[5]),
        "priority": int(row[6]),
        "metadata": metadata,
        "created_at": created_at,
        "updated_at": updated_at,
    }


def _list_models_db(*, include_disabled: bool = True, tenant_id: int) -> list[dict[str, object]]:
    if not _db_url() or psycopg is None:
        raise RuntimeError("database unavailable")

    with get_raw_conn() as conn:
        _ensure_ai_gateway_tables(conn)
        set_db_tenant_context(conn, tenant_id=tenant_id)
        _seed_default_models_db(conn, tenant_id)
        with conn.cursor() as cur:
            if include_disabled:
                cur.execute(
                    """
                    SELECT tenant_id, model_key, provider, provider_model_id, display_name, enabled, priority, metadata, created_at, updated_at
                    FROM app_ai_models
                    WHERE tenant_id = %s
                    ORDER BY priority ASC, model_key ASC
                    """,
                    (tenant_id,),
                )
            else:
                cur.execute(
                    """
                    SELECT tenant_id, model_key, provider, provider_model_id, display_name, enabled, priority, metadata, created_at, updated_at
                    FROM app_ai_models
                    WHERE tenant_id = %s AND enabled = TRUE
                    ORDER BY priority ASC, model_key ASC
                    """,
                    (tenant_id,),
                )
            return [_model_row_to_dict(row) for row in cur.fetchall()]


def _upsert_model_db(entry: dict[str, object], *, tenant_id: int) -> dict[str, object]:
    if not _db_url() or psycopg is None:
        raise RuntimeError("database unavailable")

    with get_raw_conn() as conn:
        _ensure_ai_gateway_tables(conn)
        set_db_tenant_context(conn, tenant_id=tenant_id)
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO app_ai_models (tenant_id, model_key, provider, provider_model_id, display_name, enabled, priority, metadata)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s::jsonb)
                ON CONFLICT (tenant_id, model_key)
                DO UPDATE SET
                    provider = EXCLUDED.provider,
                    provider_model_id = EXCLUDED.provider_model_id,
                    display_name = EXCLUDED.display_name,
                    enabled = EXCLUDED.enabled,
                    priority = EXCLUDED.priority,
                    metadata = EXCLUDED.metadata,
                    updated_at = NOW()
                RETURNING tenant_id, model_key, provider, provider_model_id, display_name, enabled, priority, metadata, created_at, updated_at
                """,
                (
                    tenant_id,
                    entry["model_key"],
                    entry["provider"],
                    entry["provider_model_id"],
                    entry["display_name"],
                    entry["enabled"],
                    entry["priority"],
                    json.dumps(entry.get("metadata") or {}, ensure_ascii=False),
                ),
            )
            row = cur.fetchone()
        conn.commit()

    if row is None:
        raise RuntimeError("failed to save model")
    return _model_row_to_dict(row)


def _set_model_enabled_db(model_key: str, enabled: bool, *, tenant_id: int) -> dict[str, object]:
    if not _db_url() or psycopg is None:
        raise RuntimeError("database unavailable")

    with get_raw_conn() as conn:
        _ensure_ai_gateway_tables(conn)
        set_db_tenant_context(conn, tenant_id=tenant_id)
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE app_ai_models
                SET enabled = %s,
                    updated_at = NOW()
                WHERE tenant_id = %s AND model_key = %s
                RETURNING tenant_id, model_key, provider, provider_model_id, display_name, enabled, priority, metadata, created_at, updated_at
                """,
                (bool(enabled), tenant_id, model_key),
            )
            row = cur.fetchone()
        conn.commit()

    if row is None:
        raise ValueError("model not found")
    return _model_row_to_dict(row)


def _resolve_model_db(model_key: str, *, tenant_id: int) -> dict[str, object] | None:
    if not _db_url() or psycopg is None:
        raise RuntimeError("database unavailable")

    with get_raw_conn() as conn:
        _ensure_ai_gateway_tables(conn)
        set_db_tenant_context(conn, tenant_id=tenant_id)
        _seed_default_models_db(conn, tenant_id)
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT tenant_id, model_key, provider, provider_model_id, display_name, enabled, priority, metadata, created_at, updated_at
                FROM app_ai_models
                WHERE tenant_id = %s AND model_key = %s
                """,
                (tenant_id, model_key),
            )
            row = cur.fetchone()

    if row is None:
        return None
    return _model_row_to_dict(row)


def _insert_usage_log_db(entry: dict[str, object]) -> None:
    if not _db_url() or psycopg is None:
        raise RuntimeError("database unavailable")

    with get_raw_conn() as conn:
        _ensure_ai_gateway_tables(conn)
        set_db_tenant_context(conn, tenant_id=int(entry["tenant_id"]))
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO app_ai_usage_logs (
                    tenant_id,
                    timestamp,
                    actor,
                    provider,
                    model_key,
                    provider_model_id,
                    outcome,
                    latency_ms,
                    input_tokens,
                    output_tokens,
                    total_tokens,
                    failure_reason,
                    correlation_id
                )
                VALUES (
                    %s, NOW(), %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
                """,
                (
                    entry["tenant_id"],
                    entry["actor"],
                    entry["provider"],
                    entry["model_key"],
                    entry["provider_model_id"],
                    entry["outcome"],
                    entry["latency_ms"],
                    entry.get("input_tokens"),
                    entry.get("output_tokens"),
                    entry.get("total_tokens"),
                    entry.get("failure_reason"),
                    entry.get("correlation_id"),
                ),
            )
        conn.commit()


def _list_usage_logs_db(limit: int, *, tenant_id: int) -> list[dict[str, object]]:
    if not _db_url() or psycopg is None:
        raise RuntimeError("database unavailable")

    with get_raw_conn() as conn:
        _ensure_ai_gateway_tables(conn)
        set_db_tenant_context(conn, tenant_id=tenant_id)
        with conn.cursor() as cur:
            cur.execute(
                """
                  SELECT tenant_id, actor, provider, model_key, provider_model_id, outcome, latency_ms,
                       input_tokens, output_tokens, total_tokens, failure_reason, correlation_id,
                       timestamp
                FROM app_ai_usage_logs
                  WHERE tenant_id = %s
                ORDER BY timestamp DESC
                LIMIT %s
                """,
                  (tenant_id, max(1, min(limit, 500))),
            )
            rows = cur.fetchall()

    result: list[dict[str, object]] = []
    for row in rows:
        ts = row[12].isoformat() if hasattr(row[12], "isoformat") else str(row[12])
        result.append(
            {
                "tenant_id": int(row[0]),
                "actor": row[1],
                "provider": row[2],
                "model_key": row[3],
                "provider_model_id": row[4],
                "outcome": row[5],
                "latency_ms": int(row[6]),
                "input_tokens": row[7],
                "output_tokens": row[8],
                "total_tokens": row[9],
                "failure_reason": row[10],
                "correlation_id": row[11],
                "timestamp": ts,
            }
        )
    return result


def list_models(*, include_disabled: bool = True, tenant_id: int) -> list[dict[str, object]]:
    normalized_tenant_id = _normalize_tenant_id(tenant_id)
    if _use_database():
        try:
            return _list_models_db(include_disabled=include_disabled, tenant_id=normalized_tenant_id)
        except Exception as exc:
            if not _should_fallback_to_memory(exc):
                raise

    _seed_default_models_memory(normalized_tenant_id)
    with _registry_lock:
        prefix = f"{normalized_tenant_id}:"
        rows = [item for key, item in _model_registry.items() if key.startswith(prefix)]

    if not include_disabled:
        rows = [item for item in rows if bool(item.get("enabled"))]
    return sorted(rows, key=lambda item: (int(item.get("priority", 100)), str(item.get("model_key", ""))))


def upsert_model(
    *,
    model_key: str,
    provider: str,
    provider_model_id: str,
    display_name: str,
    enabled: bool,
    priority: int,
    metadata: dict[str, Any] | None,
    tenant_id: int,
) -> dict[str, object]:
    normalized_tenant_id = _normalize_tenant_id(tenant_id)
    entry = _normalize_model_payload(
        model_key=model_key,
        provider=provider,
        provider_model_id=provider_model_id,
        display_name=display_name,
        enabled=enabled,
        priority=priority,
        metadata=metadata,
    )

    if _use_database():
        try:
            return _upsert_model_db(entry, tenant_id=normalized_tenant_id)
        except Exception as exc:
            if not _should_fallback_to_memory(exc):
                raise

    _seed_default_models_memory(normalized_tenant_id)
    now = _now_iso()
    with _registry_lock:
        storage_key = _tenant_registry_key(normalized_tenant_id, str(entry["model_key"]))
        previous = _model_registry.get(storage_key)
        merged = {
            **entry,
            "tenant_id": normalized_tenant_id,
            "created_at": previous.get("created_at") if previous else now,
            "updated_at": now,
        }
        _model_registry[storage_key] = merged
        return merged


def set_model_enabled(model_key: str, enabled: bool, *, tenant_id: int) -> dict[str, object]:
    normalized_tenant_id = _normalize_tenant_id(tenant_id)
    normalized_key = _normalize_model_key(model_key)
    if _use_database():
        try:
            return _set_model_enabled_db(normalized_key, enabled, tenant_id=normalized_tenant_id)
        except Exception as exc:
            if not _should_fallback_to_memory(exc):
                raise

    _seed_default_models_memory(normalized_tenant_id)
    with _registry_lock:
        storage_key = _tenant_registry_key(normalized_tenant_id, normalized_key)
        current = _model_registry.get(storage_key)
        if current is None:
            raise ValueError("model not found")
        current["enabled"] = bool(enabled)
        current["updated_at"] = _now_iso()
        return current


def _resolve_model(model_key: str, *, tenant_id: int) -> dict[str, object] | None:
    normalized_tenant_id = _normalize_tenant_id(tenant_id)
    normalized_key = _normalize_model_key(model_key)
    if _use_database():
        try:
            return _resolve_model_db(normalized_key, tenant_id=normalized_tenant_id)
        except Exception as exc:
            if not _should_fallback_to_memory(exc):
                raise

    _seed_default_models_memory(normalized_tenant_id)
    with _registry_lock:
        return _model_registry.get(_tenant_registry_key(normalized_tenant_id, normalized_key))


def _record_usage_log(
    *,
    tenant_id: int,
    actor: str,
    provider: str,
    model_key: str,
    provider_model_id: str,
    outcome: str,
    latency_ms: int,
    input_tokens: int | None,
    output_tokens: int | None,
    total_tokens: int | None,
    failure_reason: str | None,
    correlation_id: str | None,
) -> None:
    normalized_tenant_id = _normalize_tenant_id(tenant_id)
    entry = {
        "tenant_id": normalized_tenant_id,
        "actor": actor,
        "provider": provider,
        "model_key": model_key,
        "provider_model_id": provider_model_id,
        "outcome": outcome,
        "latency_ms": latency_ms,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": total_tokens,
        "failure_reason": failure_reason,
        "correlation_id": correlation_id,
        "timestamp": _now_iso(),
    }

    if _use_database():
        try:
            _insert_usage_log_db(entry)
        except Exception as exc:
            if not _should_fallback_to_memory(exc):
                raise

    with _usage_lock:
        _usage_logs.appendleft(entry)


def list_usage_logs(limit: int = 100, *, tenant_id: int) -> list[dict[str, object]]:
    normalized_tenant_id = _normalize_tenant_id(tenant_id)
    if _use_database():
        try:
            return _list_usage_logs_db(limit, tenant_id=normalized_tenant_id)
        except Exception as exc:
            if not _should_fallback_to_memory(exc):
                raise

    with _usage_lock:
        rows = [item for item in _usage_logs if int(item.get("tenant_id", 0)) == normalized_tenant_id]
        return rows[: max(1, min(limit, 500))]


def summarize_usage_cost(*, tenant_id: int, limit: int = 500) -> dict[str, object]:
    normalized_tenant_id = _normalize_tenant_id(tenant_id)
    rows = list_usage_logs(limit=max(1, min(limit, 5000)), tenant_id=normalized_tenant_id)

    # Conservative blended estimate for pilot reporting: $0.80 per 1M tokens.
    usd_per_token = 0.80 / 1_000_000.0

    budget = get_usage_budget(tenant_id=normalized_tenant_id)

    total_requests = len(rows)
    success_count = 0
    degraded_count = 0
    failed_count = 0
    total_tokens = 0
    total_latency_ms = 0

    per_model: dict[tuple[str, str], dict[str, object]] = {}

    for row in rows:
        model_key = str(row.get("model_key") or "unknown")
        provider = str(row.get("provider") or "unknown")
        outcome = str(row.get("outcome") or "failed").strip().lower()
        tokens = max(0, int(row.get("total_tokens") or 0))
        latency_ms = max(0, int(row.get("latency_ms") or 0))

        total_tokens += tokens
        total_latency_ms += latency_ms

        if outcome == "success":
            success_count += 1
        elif outcome == "degraded":
            degraded_count += 1
        else:
            failed_count += 1

        key = (model_key, provider)
        item = per_model.get(key)
        if item is None:
            item = {
                "model_key": model_key,
                "provider": provider,
                "requests_total": 0,
                "success_count": 0,
                "degraded_count": 0,
                "failed_count": 0,
                "total_tokens": 0,
                "latency_sum_ms": 0,
            }
            per_model[key] = item

        item["requests_total"] = int(item["requests_total"]) + 1
        item["total_tokens"] = int(item["total_tokens"]) + tokens
        item["latency_sum_ms"] = int(item["latency_sum_ms"]) + latency_ms
        if outcome == "success":
            item["success_count"] = int(item["success_count"]) + 1
        elif outcome == "degraded":
            item["degraded_count"] = int(item["degraded_count"]) + 1
        else:
            item["failed_count"] = int(item["failed_count"]) + 1

    models: list[dict[str, object]] = []
    for item in per_model.values():
        requests_total = max(1, int(item["requests_total"]))
        item_total_tokens = int(item["total_tokens"])
        models.append(
            {
                "model_key": str(item["model_key"]),
                "provider": str(item["provider"]),
                "requests_total": int(item["requests_total"]),
                "success_count": int(item["success_count"]),
                "degraded_count": int(item["degraded_count"]),
                "failed_count": int(item["failed_count"]),
                "total_tokens": item_total_tokens,
                "avg_latency_ms": round(float(int(item["latency_sum_ms"]) / requests_total), 2),
                "estimated_cost_usd": round(float(item_total_tokens * usd_per_token), 6),
            }
        )

    models.sort(key=lambda item: int(item["requests_total"]), reverse=True)

    avg_latency_ms = round(float(total_latency_ms / total_requests), 2) if total_requests > 0 else 0.0
    estimated_cost_usd = round(float(total_tokens * usd_per_token), 6)
    budget_limit_usd = float(budget.get("budget_limit_usd") or 0.0)
    budget_utilization_pct = round(float((estimated_cost_usd / budget_limit_usd) * 100.0), 2) if budget_limit_usd > 0 else 0.0
    budget_alert = budget_limit_usd > 0 and budget_utilization_pct >= float(int(budget.get("alert_threshold_pct") or 80))
    anomaly_detected, anomaly_score_z, anomaly_reason = _detect_cost_anomaly(rows, usd_per_token=usd_per_token)

    summary = {
        "tenant_id": normalized_tenant_id,
        "requests_total": total_requests,
        "success_count": success_count,
        "degraded_count": degraded_count,
        "failed_count": failed_count,
        "total_tokens": total_tokens,
        "avg_latency_ms": avg_latency_ms,
        "estimated_cost_usd": estimated_cost_usd,
        "budget_limit_usd": round(budget_limit_usd, 6),
        "budget_utilization_pct": budget_utilization_pct,
        "budget_alert": bool(budget_alert),
        "budget_hard_cap": bool(budget.get("hard_cap", False)),
        "anomaly_detected": bool(anomaly_detected),
        "anomaly_score_z": float(anomaly_score_z),
        "anomaly_reason": anomaly_reason,
        "models": models,
    }
    observe_ai_cost_summary(tenant_id=normalized_tenant_id, summary=summary)
    return summary


def summarize_usage_cost_by_user(*, tenant_id: int, limit: int = 500) -> list[dict[str, object]]:
    normalized_tenant_id = _normalize_tenant_id(tenant_id)
    rows = list_usage_logs(limit=max(1, min(limit, 5000)), tenant_id=normalized_tenant_id)
    return _summarize_usage_cost_grouped(
        rows,
        tenant_id=normalized_tenant_id,
        dimension_name="actor",
        key_resolver=lambda row: str(row.get("actor") or "unknown"),
    )


def summarize_usage_cost_by_department(*, tenant_id: int, limit: int = 500) -> list[dict[str, object]]:
    normalized_tenant_id = _normalize_tenant_id(tenant_id)
    rows = list_usage_logs(limit=max(1, min(limit, 5000)), tenant_id=normalized_tenant_id)
    return _summarize_usage_cost_grouped(
        rows,
        tenant_id=normalized_tenant_id,
        dimension_name="department",
        key_resolver=lambda row: str(row.get("department") or "unattributed"),
    )


def summarize_usage_cost_trend(*, tenant_id: int, days: int = 30, limit: int = 5000) -> list[dict[str, object]]:
    normalized_tenant_id = _normalize_tenant_id(tenant_id)
    normalized_days = max(1, min(int(days), 365))
    rows = list_usage_logs(limit=max(1, min(limit, 5000)), tenant_id=normalized_tenant_id)
    usd_per_token = 0.80 / 1_000_000.0
    now_date = datetime.now(timezone.utc).date()

    per_day: dict[str, dict[str, object]] = {}
    for row in rows:
        day_key = _usage_row_date(row)
        if day_key is None:
            continue
        day_delta = (now_date - datetime.fromisoformat(day_key).date()).days
        if day_delta < 0 or day_delta >= normalized_days:
            continue

        item = per_day.get(day_key)
        if item is None:
            item = {
                "tenant_id": normalized_tenant_id,
                "date": day_key,
                "requests_total": 0,
                "total_tokens": 0,
            }
            per_day[day_key] = item

        item["requests_total"] = int(item["requests_total"]) + 1
        item["total_tokens"] = int(item["total_tokens"]) + max(0, int(row.get("total_tokens") or 0))

    result: list[dict[str, object]] = []
    for item in per_day.values():
        total_tokens = int(item["total_tokens"])
        result.append(
            {
                "tenant_id": int(item["tenant_id"]),
                "date": str(item["date"]),
                "requests_total": int(item["requests_total"]),
                "total_tokens": total_tokens,
                "estimated_cost_usd": round(float(total_tokens * usd_per_token), 6),
            }
        )

    return sorted(result, key=lambda entry: str(entry["date"]))


def summarize_usage_cost_projection(*, tenant_id: int, limit: int = 5000) -> dict[str, object]:
    normalized_tenant_id = _normalize_tenant_id(tenant_id)
    rows = list_usage_logs(limit=max(1, min(limit, 5000)), tenant_id=normalized_tenant_id)
    usd_per_token = 0.80 / 1_000_000.0

    current_tokens = sum(max(0, int(item.get("total_tokens") or 0)) for item in rows)
    current_cost = float(current_tokens * usd_per_token)
    elapsed_requests = max(0, len(rows))

    if elapsed_requests == 0:
        projected_cost = 0.0
    else:
        # Heuristic for pilot: project the remaining daily volume as 2x observed sample.
        projected_cost = current_cost * 2.0

    return {
        "tenant_id": normalized_tenant_id,
        "period": "daily",
        "elapsed_requests": elapsed_requests,
        "current_cost_usd": round(current_cost, 6),
        "projected_cost_usd": round(projected_cost, 6),
        "projection_basis": "daily_linear_samplex2",
    }


def list_usage_cost_anomalies(*, tenant_id: int, limit: int = 20) -> list[dict[str, object]]:
    normalized_tenant_id = _normalize_tenant_id(tenant_id)
    normalized_limit = max(1, min(int(limit), 200))
    sample_size = 6
    rows = list_usage_logs(limit=max(500, normalized_limit * sample_size), tenant_id=normalized_tenant_id)
    if len(rows) < sample_size:
        return []

    usd_per_token = 0.80 / 1_000_000.0
    anomalies: list[dict[str, object]] = []

    for idx in range(0, len(rows) - sample_size + 1):
        window = rows[idx : idx + sample_size]
        detected, z_score, reason = _detect_cost_anomaly(window, usd_per_token=usd_per_token)
        if not detected or reason is None:
            continue

        latest = window[0]
        tokens = max(0, int(latest.get("total_tokens") or 0))
        anomalies.append(
            {
                "tenant_id": normalized_tenant_id,
                "timestamp": str(latest.get("timestamp") or _now_iso()),
                "model_key": str(latest.get("model_key") or "unknown"),
                "provider": str(latest.get("provider") or "unknown"),
                "total_tokens": tokens,
                "estimated_cost_usd": round(float(tokens * usd_per_token), 6),
                "anomaly_score_z": float(z_score),
                "anomaly_reason": str(reason),
            }
        )
        if len(anomalies) >= normalized_limit:
            break

    return anomalies


def _usage_row_date(row: dict[str, object]) -> str | None:
    raw = str(row.get("timestamp") or "").strip()
    if not raw:
        return None
    normalized = raw.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    return parsed.date().isoformat()


def _summarize_usage_cost_grouped(
    rows: list[dict[str, object]],
    *,
    tenant_id: int,
    dimension_name: str,
    key_resolver,
) -> list[dict[str, object]]:
    usd_per_token = 0.80 / 1_000_000.0
    grouped: dict[str, dict[str, object]] = {}

    for row in rows:
        key = str(key_resolver(row) or "unknown").strip() or "unknown"
        outcome = str(row.get("outcome") or "failed").strip().lower()
        tokens = max(0, int(row.get("total_tokens") or 0))
        latency_ms = max(0, int(row.get("latency_ms") or 0))

        item = grouped.get(key)
        if item is None:
            item = {
                "tenant_id": int(tenant_id),
                dimension_name: key,
                "requests_total": 0,
                "success_count": 0,
                "degraded_count": 0,
                "failed_count": 0,
                "total_tokens": 0,
                "latency_sum_ms": 0,
            }
            grouped[key] = item

        item["requests_total"] = int(item["requests_total"]) + 1
        item["total_tokens"] = int(item["total_tokens"]) + tokens
        item["latency_sum_ms"] = int(item["latency_sum_ms"]) + latency_ms
        if outcome == "success":
            item["success_count"] = int(item["success_count"]) + 1
        elif outcome == "degraded":
            item["degraded_count"] = int(item["degraded_count"]) + 1
        else:
            item["failed_count"] = int(item["failed_count"]) + 1

    result: list[dict[str, object]] = []
    for item in grouped.values():
        requests_total = max(1, int(item["requests_total"]))
        total_tokens = int(item["total_tokens"])
        result.append(
            {
                "tenant_id": int(item["tenant_id"]),
                dimension_name: str(item[dimension_name]),
                "requests_total": int(item["requests_total"]),
                "success_count": int(item["success_count"]),
                "degraded_count": int(item["degraded_count"]),
                "failed_count": int(item["failed_count"]),
                "total_tokens": total_tokens,
                "avg_latency_ms": round(float(int(item["latency_sum_ms"]) / requests_total), 2),
                "estimated_cost_usd": round(float(total_tokens * usd_per_token), 6),
            }
        )

    return sorted(result, key=lambda item: (float(item["estimated_cost_usd"]), int(item["requests_total"])), reverse=True)


def _provider_config(tenant_id: int | None = None) -> dict[str, dict[str, Any]]:
    openai_cfg = get_ai_provider_runtime_config("openai", tenant_id=tenant_id)
    gemini_cfg = get_ai_provider_runtime_config("gemini", tenant_id=tenant_id)
    anthropic_cfg = get_ai_provider_runtime_config("anthropic", tenant_id=tenant_id)
    custom_cfg = get_ai_provider_runtime_config("custom", tenant_id=tenant_id)

    return {
        "openai": {
            "configured": bool(openai_cfg["api_key"]),
            "validation_url": openai_cfg["validation_url"] or "https://api.openai.com/v1/models",
            "headers": lambda: {"Authorization": f"Bearer {openai_cfg['api_key']}"},
            "params": lambda: None,
        },
        "gemini": {
            "configured": bool(gemini_cfg["api_key"]),
            "validation_url": gemini_cfg["validation_url"] or "https://generativelanguage.googleapis.com/v1beta/models",
            "headers": lambda: {},
            "params": lambda: {"key": gemini_cfg["api_key"]},
        },
        "anthropic": {
            "configured": bool(anthropic_cfg["api_key"]),
            "validation_url": anthropic_cfg["validation_url"] or "https://api.anthropic.com/v1/models",
            "headers": lambda: {
                "x-api-key": anthropic_cfg["api_key"],
                "anthropic-version": "2023-06-01",
            },
            "params": lambda: None,
        },
        "custom": {
            "configured": bool(custom_cfg["validation_url"]),
            "validation_url": custom_cfg["validation_url"],
            "headers": lambda: (
                {"Authorization": f"Bearer {custom_cfg['api_key']}"}
                if custom_cfg["api_key"]
                else {}
            ),
            "params": lambda: None,
        },
    }


def _provider_runtime_config(provider: str, tenant_id: int | None = None) -> dict[str, str]:
    provider = provider.strip().lower()
    runtime = get_ai_provider_runtime_config(provider, tenant_id=tenant_id)

    if provider == "openai":
        runtime["chat_url"] = get_runtime_value(
            "ai.openai.chat_url",
            "AI_OPENAI_CHAT_URL",
            "https://api.openai.com/v1/chat/completions",
            tenant_id=tenant_id,
        )
    elif provider == "gemini":
        runtime["chat_url"] = get_runtime_value(
            "ai.gemini.chat_url",
            "AI_GEMINI_CHAT_URL",
            "https://generativelanguage.googleapis.com/v1beta/models",
            tenant_id=tenant_id,
        )
    elif provider == "anthropic":
        runtime["chat_url"] = get_runtime_value(
            "ai.anthropic.chat_url",
            "AI_ANTHROPIC_CHAT_URL",
            "https://api.anthropic.com/v1/messages",
            tenant_id=tenant_id,
        )
    elif provider == "custom":
        runtime["chat_url"] = get_runtime_value(
            "ai.custom.chat_url",
            "AI_CUSTOM_PROVIDER_CHAT_URL",
            runtime.get("validation_url", ""),
            tenant_id=tenant_id,
        )

    return runtime


def list_provider_status(tenant_id: int | None = None) -> list[dict[str, Any]]:
    providers = []
    for name, config in _provider_config(tenant_id=tenant_id).items():
        providers.append(
            {
                "provider": name,
                "configured": bool(config["configured"]),
                "validation_url": config["validation_url"],
            }
        )
    return providers


def _request(method: str, url: str, headers: dict[str, str], params: dict[str, str] | None) -> httpx.Response:
    safe_url = validate_external_https_url(url)
    with httpx.Client(timeout=_timeout(), follow_redirects=True) as client:
        return client.request(method, safe_url, headers=headers, params=params)


def _request_json(
    method: str,
    url: str,
    *,
    headers: dict[str, str],
    params: dict[str, str] | None = None,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    safe_url = validate_external_https_url(url)
    try:
        with httpx.Client(timeout=_timeout(), follow_redirects=True) as client:
            response = client.request(method, safe_url, headers=headers, params=params, json=payload)
    except httpx.TimeoutException as exc:
        raise AIProviderTimeoutError("provider timeout") from exc
    except httpx.HTTPError as exc:
        raise AIProviderExecutionError("provider request failed") from exc

    if response.status_code >= 400:
        detail = "provider request failed"
        try:
            data = response.json()
            if isinstance(data, dict):
                maybe_message = data.get("error") or data.get("message") or data.get("detail")
                if isinstance(maybe_message, dict):
                    maybe_message = maybe_message.get("message")
                if maybe_message:
                    detail = str(maybe_message)
        except Exception:
            if response.text:
                detail = response.text[:250]
        raise AIProviderExecutionError(detail, status_code=response.status_code)

    try:
        data = response.json()
    except Exception as exc:
        raise AIProviderExecutionError("provider returned non-JSON response") from exc

    if not isinstance(data, dict):
        raise AIProviderExecutionError("provider returned invalid response body")
    return data


def _coerce_message_content(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        parts = []
        for item in value:
            if isinstance(item, dict) and item.get("type") == "text":
                text = item.get("text")
                if isinstance(text, str):
                    parts.append(text)
        return "\n".join(parts).strip()
    return ""


class OpenAIAdapter:
    provider = "openai"

    def execute_chat(
        self,
        *,
        provider_model_id: str,
        messages: list[dict[str, str]],
        temperature: float | None,
        max_tokens: int | None,
        runtime_config: dict[str, str],
    ) -> NormalizedChatResult:
        if not runtime_config.get("api_key"):
            raise AIProviderExecutionError("openai is not configured")

        payload: dict[str, Any] = {
            "model": provider_model_id,
            "messages": messages,
        }
        if temperature is not None:
            payload["temperature"] = temperature
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens

        data = _request_json(
            "POST",
            runtime_config["chat_url"],
            headers={
                "Authorization": f"Bearer {runtime_config['api_key']}",
                "Content-Type": "application/json",
            },
            payload=payload,
        )

        choices = data.get("choices") or []
        first = choices[0] if choices else {}
        message = first.get("message") if isinstance(first, dict) else {}
        output_text = _coerce_message_content(message.get("content") if isinstance(message, dict) else "")
        usage = data.get("usage") or {}
        return NormalizedChatResult(
            provider=self.provider,
            output_text=output_text,
            finish_reason=first.get("finish_reason") if isinstance(first, dict) else None,
            provider_response_id=str(data.get("id")) if data.get("id") else None,
            usage={
                "input_tokens": usage.get("prompt_tokens"),
                "output_tokens": usage.get("completion_tokens"),
                "total_tokens": usage.get("total_tokens"),
            },
        )


class GeminiAdapter:
    provider = "gemini"

    def execute_chat(
        self,
        *,
        provider_model_id: str,
        messages: list[dict[str, str]],
        temperature: float | None,
        max_tokens: int | None,
        runtime_config: dict[str, str],
    ) -> NormalizedChatResult:
        if not runtime_config.get("api_key"):
            raise AIProviderExecutionError("gemini is not configured")

        contents: list[dict[str, Any]] = []
        for item in messages:
            role = "model" if item.get("role") == "assistant" else "user"
            contents.append({"role": role, "parts": [{"text": item.get("content", "")}]})

        payload: dict[str, Any] = {"contents": contents}
        generation_config: dict[str, Any] = {}
        if temperature is not None:
            generation_config["temperature"] = temperature
        if max_tokens is not None:
            generation_config["maxOutputTokens"] = max_tokens
        if generation_config:
            payload["generationConfig"] = generation_config

        base_url = runtime_config["chat_url"].rstrip("/")
        url = f"{base_url}/{provider_model_id}:generateContent"
        data = _request_json(
            "POST",
            url,
            headers={"Content-Type": "application/json"},
            params={"key": runtime_config["api_key"]},
            payload=payload,
        )

        candidates = data.get("candidates") or []
        first = candidates[0] if candidates else {}
        content = first.get("content") if isinstance(first, dict) else {}
        parts = content.get("parts") if isinstance(content, dict) else []
        output_text = "\n".join(
            item.get("text", "")
            for item in parts
            if isinstance(item, dict) and isinstance(item.get("text"), str)
        ).strip()

        usage = data.get("usageMetadata") or {}
        return NormalizedChatResult(
            provider=self.provider,
            output_text=output_text,
            finish_reason=first.get("finishReason") if isinstance(first, dict) else None,
            provider_response_id=None,
            usage={
                "input_tokens": usage.get("promptTokenCount"),
                "output_tokens": usage.get("candidatesTokenCount"),
                "total_tokens": usage.get("totalTokenCount"),
            },
        )


class AnthropicAdapter:
    provider = "anthropic"

    def execute_chat(
        self,
        *,
        provider_model_id: str,
        messages: list[dict[str, str]],
        temperature: float | None,
        max_tokens: int | None,
        runtime_config: dict[str, str],
    ) -> NormalizedChatResult:
        if not runtime_config.get("api_key"):
            raise AIProviderExecutionError("anthropic is not configured")

        payload: dict[str, Any] = {
            "model": provider_model_id,
            "messages": [
                {"role": item.get("role"), "content": item.get("content", "")}
                for item in messages
                if item.get("role") in {"user", "assistant"}
            ],
            "max_tokens": max_tokens or 1024,
        }

        system_messages = [item.get("content", "") for item in messages if item.get("role") == "system"]
        if system_messages:
            payload["system"] = "\n".join(system_messages)
        if temperature is not None:
            payload["temperature"] = temperature

        data = _request_json(
            "POST",
            runtime_config["chat_url"],
            headers={
                "x-api-key": runtime_config["api_key"],
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            payload=payload,
        )

        content = data.get("content") or []
        output_text = "\n".join(
            item.get("text", "")
            for item in content
            if isinstance(item, dict) and item.get("type") == "text"
        ).strip()

        usage = data.get("usage") or {}
        return NormalizedChatResult(
            provider=self.provider,
            output_text=output_text,
            finish_reason=data.get("stop_reason"),
            provider_response_id=str(data.get("id")) if data.get("id") else None,
            usage={
                "input_tokens": usage.get("input_tokens"),
                "output_tokens": usage.get("output_tokens"),
                "total_tokens": (
                    (usage.get("input_tokens") or 0) + (usage.get("output_tokens") or 0)
                    if usage.get("input_tokens") is not None or usage.get("output_tokens") is not None
                    else None
                ),
            },
        )


class CustomAdapter:
    provider = "custom"

    def execute_chat(
        self,
        *,
        provider_model_id: str,
        messages: list[dict[str, str]],
        temperature: float | None,
        max_tokens: int | None,
        runtime_config: dict[str, str],
    ) -> NormalizedChatResult:
        chat_url = (runtime_config.get("chat_url") or "").strip()
        if not chat_url:
            raise AIProviderExecutionError("custom provider chat URL is not configured")

        headers: dict[str, str] = {"Content-Type": "application/json"}
        if runtime_config.get("api_key"):
            headers["Authorization"] = f"Bearer {runtime_config['api_key']}"

        payload: dict[str, Any] = {
            "model": provider_model_id,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        data = _request_json(
            "POST",
            chat_url,
            headers=headers,
            payload=payload,
        )

        output_text = ""
        if isinstance(data.get("output_text"), str):
            output_text = data["output_text"]
        elif isinstance(data.get("choices"), list) and data["choices"]:
            first = data["choices"][0]
            if isinstance(first, dict):
                msg = first.get("message")
                if isinstance(msg, dict):
                    output_text = _coerce_message_content(msg.get("content"))

        usage = data.get("usage") if isinstance(data.get("usage"), dict) else {}
        return NormalizedChatResult(
            provider=self.provider,
            output_text=output_text,
            finish_reason=data.get("finish_reason") if isinstance(data.get("finish_reason"), str) else None,
            provider_response_id=str(data.get("id")) if data.get("id") else None,
            usage={
                "input_tokens": usage.get("input_tokens") or usage.get("prompt_tokens"),
                "output_tokens": usage.get("output_tokens") or usage.get("completion_tokens"),
                "total_tokens": usage.get("total_tokens"),
            },
        )


_ADAPTERS: dict[str, AIProviderAdapter] = {
    "openai": OpenAIAdapter(),
    "gemini": GeminiAdapter(),
    "anthropic": AnthropicAdapter(),
    "custom": CustomAdapter(),
}


def _adapter_for_provider(provider: str) -> AIProviderAdapter:
    adapter = _ADAPTERS.get(provider)
    if adapter is None:
        raise AIGatewayError(
            status_code=400,
            detail="unsupported provider",
            audit_reason="unsupported_provider",
            provider=provider,
        )
    return adapter


def validate_provider_runtime(
    provider: str,
    actor: str | None = None,
    roles: list[str] | None = None,
    tenant_id: int | None = None,
) -> dict[str, Any]:
    config = _provider_config(tenant_id=tenant_id).get(provider)
    if config is None:
        raise ValueError("unknown provider")
    if not config["configured"]:
        raise ValueError(f"{provider} is not configured")

    url = str(config["validation_url"] or "").strip()
    if not url:
        raise ValueError(f"{provider} validation URL is not configured")

    limit_state = None
    if actor:
        limit_state = enforce_rate_limit(provider, actor=actor, roles=roles or [])

    response = _request("GET", url, config["headers"](), config["params"]())
    if response.status_code >= 400:
        detail = response.text[:300] if response.text else str(response.status_code)
        raise ValueError(f"{provider} validation failed: {detail}")

    result = {
        "provider": provider,
        "status": "validated",
        "http_status": response.status_code,
        "validation_url": url,
    }
    if limit_state is not None:
        result["rate_limit"] = limit_state
    return result


def _degraded_fallback_result(
    *,
    model_key: str,
    provider: str,
    provider_model_id: str,
    latency_ms: int,
    degraded_reason: str,
) -> dict[str, object]:
    return {
        "model": model_key,
        "provider": provider,
        "provider_model_id": provider_model_id,
        "output_text": "AI provider is temporarily unavailable. Returned deterministic degraded fallback.",
        "finish_reason": "degraded_fallback",
        "usage": {
            "input_tokens": None,
            "output_tokens": None,
            "total_tokens": None,
        },
        "latency_ms": latency_ms,
        "degraded": True,
        "degraded_reason": degraded_reason,
    }


def execute_chat(
    payload: dict[str, Any],
    *,
    actor: str,
    roles: list[str],
    tenant_id: int | None = None,
    correlation_id: str | None = None,
) -> dict[str, object]:
    try:
        normalized_tenant_id = _normalize_tenant_id(tenant_id)
    except ValueError as exc:
        raise AIGatewayError(status_code=400, detail=str(exc), audit_reason="invalid_payload") from exc

    from app.modules.billing.service import (
        assert_billing_write_allowed,
        assert_quota_with_increment,
    )

    try:
        assert_billing_write_allowed(normalized_tenant_id, action="ai_gateway.execute_chat")
        assert_quota_with_increment(normalized_tenant_id, "ai_requests_per_day", increment=1)
    except HTTPException as exc:
        raise AIGatewayError(status_code=exc.status_code, detail=str(exc.detail), audit_reason="quota_exceeded") from exc

    try:
        from app.modules.usage.service import record_usage_event

        record_usage_event(normalized_tenant_id, "ai_requests", 1)
    except Exception:
        pass

    requested_model = str(payload.get("model", "")).strip()
    model_key = requested_model
    routing_meta: dict[str, object] = {"mode": "explicit", "selection": "requested"}
    if not model_key:
        raise AIGatewayError(status_code=400, detail="model is required", audit_reason="invalid_payload")
    if model_key.lower() == "auto":
        try:
            model_key, routing_meta = _select_auto_model(payload, tenant_id=normalized_tenant_id)
        except ValueError as exc:
            raise AIGatewayError(status_code=400, detail=str(exc), audit_reason="unknown_model") from exc

    messages = payload.get("messages")
    if not isinstance(messages, list) or not messages:
        raise AIGatewayError(status_code=400, detail="messages are required", audit_reason="invalid_payload", model=model_key)

    model_entry = _resolve_model(model_key, tenant_id=normalized_tenant_id)
    if model_entry is None:
        raise AIGatewayError(status_code=400, detail="unknown model", audit_reason="unknown_model", model=model_key)
    if not bool(model_entry.get("enabled")):
        raise AIGatewayError(status_code=400, detail="model is disabled", audit_reason="disabled_model", model=model_key)

    provider = str(model_entry["provider"])
    provider_model_id = str(model_entry["provider_model_id"])

    budget_guardrail = _evaluate_budget_guardrail(
        tenant_id=normalized_tenant_id,
        estimated_increment_tokens=max(1, int(payload.get("max_tokens") or 1024)),
    )
    if bool(budget_guardrail.get("blocked")):
        _record_usage_log(
            tenant_id=normalized_tenant_id,
            actor=actor,
            provider=provider,
            model_key=model_key,
            provider_model_id=provider_model_id,
            outcome="budget_blocked",
            latency_ms=1,
            input_tokens=None,
            output_tokens=None,
            total_tokens=None,
            failure_reason="budget_hard_cap_exceeded",
            correlation_id=correlation_id,
        )
        raise AIGatewayError(
            status_code=403,
            detail="ai_budget_hard_cap_exceeded",
            audit_reason="budget_hard_cap",
            provider=provider,
            model=model_key,
        )

    started = time.monotonic()
    try:
        enforce_rate_limit(provider, actor=actor, roles=roles)
    except ValueError as exc:
        latency_ms = max(1, int((time.monotonic() - started) * 1000))
        _record_usage_log(
            tenant_id=normalized_tenant_id,
            actor=actor,
            provider=provider,
            model_key=model_key,
            provider_model_id=provider_model_id,
            outcome="rate_limited",
            latency_ms=latency_ms,
            input_tokens=None,
            output_tokens=None,
            total_tokens=None,
            failure_reason=str(exc),
            correlation_id=correlation_id,
        )
        raise AIGatewayError(
            status_code=429,
            detail=str(exc),
            audit_reason="rate_limit",
            provider=provider,
            model=model_key,
        ) from exc

    adapter = _adapter_for_provider(provider)
    runtime_config = _provider_runtime_config(provider, tenant_id=normalized_tenant_id)
    normalized_messages = [
        {
            "role": str(item.get("role", "")),
            "content": str(item.get("content", "")),
        }
        for item in messages
        if isinstance(item, dict)
    ]

    # --- Pre-call guardrails ---
    _tenant_guardrail_policy = _build_guardrail_policy_for_tenant(normalized_tenant_id)
    _guardrail_engine = GuardrailEngine(_tenant_guardrail_policy)
    _combined_input = " ".join(
        str(m.get("content", "")) for m in normalized_messages
    )
    pre_guardrail = _guardrail_engine.evaluate_pre(_combined_input)
    for _det in pre_guardrail.detectors:
        observe_ai_guardrail_evaluation(
            tenant_id=normalized_tenant_id,
            stage="pre",
            detector=_det.detector,
            decision=_det.decision.value,
            duration_seconds=pre_guardrail.latency_ms / 1000.0,
        )
    if pre_guardrail.blocked:
        for _det in pre_guardrail.detectors:
            if _det.decision.value == "block":
                observe_ai_guardrail_blocked(
                    tenant_id=normalized_tenant_id,
                    detector=_det.detector,
                    reason=_det.reason or "guardrail_pre_block",
                )
        _record_usage_log(
            tenant_id=normalized_tenant_id,
            actor=actor,
            provider=provider,
            model_key=model_key,
            provider_model_id=provider_model_id,
            outcome="blocked_by_guardrail",
            latency_ms=max(1, int(pre_guardrail.latency_ms)),
            input_tokens=None,
            output_tokens=None,
            total_tokens=None,
            failure_reason=f"pre_guardrail:{pre_guardrail.decision}",
            correlation_id=correlation_id,
        )
        raise AIGatewayError(
            status_code=422,
            detail="request_blocked_by_guardrail",
            audit_reason="guardrail_pre_block",
            provider=provider,
            model=model_key,
        )

    try:
        result = adapter.execute_chat(
            provider_model_id=provider_model_id,
            messages=normalized_messages,
            temperature=payload.get("temperature"),
            max_tokens=payload.get("max_tokens"),
            runtime_config=runtime_config,
        )
    except AIProviderTimeoutError:
        latency_ms = max(1, int((time.monotonic() - started) * 1000))
        _record_usage_log(
            tenant_id=normalized_tenant_id,
            actor=actor,
            provider=provider,
            model_key=model_key,
            provider_model_id=provider_model_id,
            outcome="degraded",
            latency_ms=latency_ms,
            input_tokens=None,
            output_tokens=None,
            total_tokens=None,
            failure_reason="provider_timeout",
            correlation_id=correlation_id,
        )
        degraded = _degraded_fallback_result(
            model_key=model_key,
            provider=provider,
            provider_model_id=provider_model_id,
            latency_ms=latency_ms,
            degraded_reason="provider_timeout",
        )
        degraded["routing"] = routing_meta
        degraded["budget"] = budget_guardrail
        return degraded
    except AIProviderExecutionError as exc:
        latency_ms = max(1, int((time.monotonic() - started) * 1000))
        # If error has a status_code, it's a remote provider error → degrade gracefully (200)
        # If error has no status_code, it's an internal error → surface as 502 failure
        if exc.status_code is not None:
            # Remote provider error: return degraded result
            _record_usage_log(
                tenant_id=normalized_tenant_id,
                actor=actor,
                provider=provider,
                model_key=model_key,
                provider_model_id=provider_model_id,
                outcome="degraded",
                latency_ms=latency_ms,
                input_tokens=None,
                output_tokens=None,
                total_tokens=None,
                failure_reason="provider_error",
                correlation_id=correlation_id,
            )
            degraded = _degraded_fallback_result(
                model_key=model_key,
                provider=provider,
                provider_model_id=provider_model_id,
                latency_ms=latency_ms,
                degraded_reason="provider_error",
            )
            degraded["routing"] = routing_meta
            degraded["budget"] = budget_guardrail
            return degraded
        else:
            # Internal error: record as failure and raise 502
            _record_usage_log(
                tenant_id=normalized_tenant_id,
                actor=actor,
                provider=provider,
                model_key=model_key,
                provider_model_id=provider_model_id,
                outcome="failed",
                latency_ms=latency_ms,
                input_tokens=None,
                output_tokens=None,
                total_tokens=None,
                failure_reason=str(exc),
                correlation_id=correlation_id,
            )
            raise AIGatewayError(
                status_code=502,
                detail=str(exc) or "provider error",
                audit_reason="provider_error",
                provider=provider,
                model=model_key,
            ) from exc

    latency_ms = max(1, int((time.monotonic() - started) * 1000))

    # --- Post-call guardrails ---
    post_guardrail = _guardrail_engine.evaluate_post(result.output_text or "")
    for _det in post_guardrail.detectors:
        observe_ai_guardrail_evaluation(
            tenant_id=normalized_tenant_id,
            stage="post",
            detector=_det.detector,
            decision=_det.decision.value,
            duration_seconds=post_guardrail.latency_ms / 1000.0,
        )
    if post_guardrail.blocked:
        for _det in post_guardrail.detectors:
            if _det.decision.value == "block":
                observe_ai_guardrail_blocked(
                    tenant_id=normalized_tenant_id,
                    detector=_det.detector,
                    reason=_det.reason or "guardrail_post_block",
                )
        _record_usage_log(
            tenant_id=normalized_tenant_id,
            actor=actor,
            provider=provider,
            model_key=model_key,
            provider_model_id=provider_model_id,
            outcome="blocked_by_guardrail",
            latency_ms=latency_ms,
            input_tokens=result.usage.get("input_tokens") if isinstance(result.usage, dict) else None,
            output_tokens=result.usage.get("output_tokens") if isinstance(result.usage, dict) else None,
            total_tokens=result.usage.get("total_tokens") if isinstance(result.usage, dict) else None,
            failure_reason=f"post_guardrail:{post_guardrail.decision}",
            correlation_id=correlation_id,
        )
        raise AIGatewayError(
            status_code=422,
            detail="response_blocked_by_guardrail",
            audit_reason="guardrail_post_block",
            provider=provider,
            model=model_key,
        )

    _record_usage_log(
        tenant_id=normalized_tenant_id,
        actor=actor,
        provider=provider,
        model_key=model_key,
        provider_model_id=provider_model_id,
        outcome="success",
        latency_ms=latency_ms,
        input_tokens=result.usage.get("input_tokens") if isinstance(result.usage, dict) else None,
        output_tokens=result.usage.get("output_tokens") if isinstance(result.usage, dict) else None,
        total_tokens=result.usage.get("total_tokens") if isinstance(result.usage, dict) else None,
        failure_reason=None,
        correlation_id=correlation_id,
    )

    return {
        "model": model_key,
        "provider": provider,
        "provider_model_id": provider_model_id,
        "output_text": result.output_text,
        "finish_reason": result.finish_reason,
        "usage": {
            "input_tokens": result.usage.get("input_tokens") if isinstance(result.usage, dict) else None,
            "output_tokens": result.usage.get("output_tokens") if isinstance(result.usage, dict) else None,
            "total_tokens": result.usage.get("total_tokens") if isinstance(result.usage, dict) else None,
        },
        "latency_ms": latency_ms,
        "routing": routing_meta,
        "budget": budget_guardrail,
        "guardrail": {
            "pre": {
                "decision": pre_guardrail.decision.value,
                "blocked": pre_guardrail.blocked,
                "latency_ms": pre_guardrail.latency_ms,
                "detectors": [
                    {"detector": d.detector, "decision": d.decision.value, "score": d.score}
                    for d in pre_guardrail.detectors
                ],
            },
            "post": {
                "decision": post_guardrail.decision.value,
                "blocked": post_guardrail.blocked,
                "latency_ms": post_guardrail.latency_ms,
                "detectors": [
                    {"detector": d.detector, "decision": d.decision.value, "score": d.score}
                    for d in post_guardrail.detectors
                ],
            },
        },
    }