"""A-024.1 — Platform Health operational contract (L3 evidence).

Provides deterministic health severity evidence without claiming production
monitoring coverage, SLA guarantees, or external observability integrations.
"""
from __future__ import annotations

from app.modules.university_core.tenant_entity_api import (
    create_entity_for_tenant,
    list_entities_for_tenant,
)


HEALTH_STATES: frozenset[str] = frozenset({"HEALTHY", "DEGRADED", "OUTAGE"})
PLATFORM_COMPONENT_STATUSES: frozenset[str] = frozenset({"healthy", "degraded", "unhealthy", "unknown"})
PLATFORM_HEALTH_SEVERITIES: tuple[str, ...] = ("low", "medium", "high", "critical")
PLATFORM_HEALTH_EVENT_READINESS: dict[str, str] = {
    "low": "platform.health.healthy",
    "medium": "platform.health.degraded",
    "high": "platform.health.review_required",
    "critical": "platform.health.unhealthy",
}
PLATFORM_HEALTH_SAFETY_GUARDS: frozenset[str] = frozenset(
    {
        "NO_FAKE_UPTIME_CLAIMS",
        "NO_FAKE_SLA_CLAIMS",
        "NO_EXTERNAL_MONITORING_ASSERTIONS",
        "NO_SYNTHETIC_DASHBOARD_VALUES",
    }
)


def _validate_tenant(tenant_id: int) -> None:
    if not tenant_id or tenant_id <= 0:
        raise ValueError("tenant_id must be a positive integer")


def _severity_rank(severity: str) -> int:
    return PLATFORM_HEALTH_SEVERITIES.index(severity)


def _max_severity(current: str, candidate: str) -> str:
    return candidate if _severity_rank(candidate) > _severity_rank(current) else current


def _normalize_required(value: str, *, field: str) -> str:
    normalized = (value or "").strip()
    if not normalized:
        raise ValueError(f"{field} is required")
    return normalized


def build_platform_health_evidence(
    *,
    tenant_id: int,
    component: str,
    status: str,
    source_entity_type: str,
    source_entity_id: str,
    latency_ms: float | None = None,
    error_rate: float | None = None,
    dependency_available: bool | None = None,
) -> dict[str, object]:
    """Build deterministic health evidence from explicit module inputs."""
    _validate_tenant(tenant_id)
    component_name = _normalize_required(component, field="component").lower()
    status_name = _normalize_required(status, field="status").lower()
    source_type = _normalize_required(source_entity_type, field="source_entity_type")
    source_id = _normalize_required(source_entity_id, field="source_entity_id")

    if status_name not in PLATFORM_COMPONENT_STATUSES:
        raise ValueError(f"status must be one of {sorted(PLATFORM_COMPONENT_STATUSES)}")
    if latency_ms is not None and latency_ms < 0:
        raise ValueError("latency_ms must be >= 0")
    if error_rate is not None and (error_rate < 0 or error_rate > 1):
        raise ValueError("error_rate must be between 0 and 1")

    reasons: list[str] = []
    severity = "low"
    review_required = False

    if status_name == "healthy":
        severity = "low"
        reasons.append("COMPONENT_HEALTHY")
    elif status_name == "degraded":
        severity = "medium"
        reasons.append("COMPONENT_DEGRADED")
    elif status_name == "unhealthy":
        severity = "high"
        review_required = True
        reasons.append("COMPONENT_UNHEALTHY")
    else:
        severity = "high"
        review_required = True
        reasons.append("COMPONENT_STATUS_UNKNOWN")

    if latency_ms is not None and latency_ms >= 1200:
        severity = _max_severity(severity, "high")
        review_required = True
        reasons.append("HIGH_LATENCY")

    if error_rate is not None and error_rate >= 0.08:
        severity = _max_severity(severity, "high")
        review_required = True
        reasons.append("HIGH_ERROR_RATE")

    if dependency_available is False:
        severity = _max_severity(severity, "critical")
        review_required = True
        reasons.append("DEPENDENCY_UNAVAILABLE")

    audit_action = f"platform_health.{severity}"
    event_readiness = PLATFORM_HEALTH_EVENT_READINESS[severity]

    return {
        "tenant_id": tenant_id,
        "component": component_name,
        "status": status_name,
        "severity": severity,
        "review_required": review_required,
        "reasons": sorted(set(reasons)),
        "audit_action": audit_action,
        "event_readiness": event_readiness,
        "source_entity_type": source_type,
        "source_entity_id": source_id,
        "latency_ms": latency_ms,
        "error_rate": error_rate,
        "dependency_available": dependency_available,
        "no_fake_uptime": True,
        "no_fake_sla": True,
        "no_external_monitoring_integration": True,
    }


def register_health_signal(
    tenant_id: int,
    *,
    component: str,
    status: str,
    summary: str,
) -> dict[str, object]:
    """Register a platform health signal snapshot for a tenant."""
    _validate_tenant(tenant_id)
    if not component:
        raise ValueError("component is required")
    if status not in HEALTH_STATES:
        raise ValueError(f"status must be one of {sorted(HEALTH_STATES)}")
    if not summary:
        raise ValueError("summary is required")

    row = create_entity_for_tenant(
        "platform_health_signals",
        {
            "component": component,
            "status": status,
            "summary": summary,
            "tenant_id": tenant_id,
        },
        tenant_id,
    )
    return {"signal_id": row["id"], "status": status}


def list_health_signals(
    tenant_id: int,
    *,
    status: str | None = None,
    component: str | None = None,
) -> list[dict[str, object]]:
    """List tenant-scoped platform health signals with optional filters."""
    _validate_tenant(tenant_id)
    rows = list_entities_for_tenant("platform_health_signals", tenant_id)
    if status:
        rows = [row for row in rows if row.get("status") == status]
    if component:
        rows = [row for row in rows if row.get("component") == component]
    return rows
