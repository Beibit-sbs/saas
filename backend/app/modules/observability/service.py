"""A-024.3 — Observability operational visibility contract (L4 evidence).

Deterministic, tenant-safe observability evidence only.
No fake uptime/SLA claims and no external monitoring provider integration.
"""
from __future__ import annotations

from typing import Any


OBSERVABILITY_COMPONENTS: frozenset[str] = frozenset(
    {
        "api",
        "database",
        "cache",
        "worker",
        "scheduler",
        "ai_routing",
        "ai_copilot",
        "platform_health",
    }
)
OBSERVABILITY_SIGNAL_STATUSES: frozenset[str] = frozenset({"healthy", "degraded", "unhealthy", "unknown"})
OBSERVABILITY_SEVERITIES: tuple[str, ...] = ("low", "medium", "high", "critical")
OBSERVABILITY_EVENT_READINESS: dict[str, str] = {
    "healthy": "platform.observability.signal_recorded",
    "degraded": "platform.observability.degraded",
    "unhealthy": "platform.observability.unhealthy",
    "unknown": "platform.observability.review_required",
}
OBSERVABILITY_INTEGRATION_COMPONENTS: frozenset[str] = frozenset(
    {"platform_health", "ai_routing", "ai_copilot"}
)


def _validate_tenant(tenant_id: int) -> None:
    if not tenant_id or tenant_id <= 0:
        raise ValueError("tenant_id must be a positive integer")


def _normalize_required(value: str, *, field: str) -> str:
    normalized = (value or "").strip()
    if not normalized:
        raise ValueError(f"{field} is required")
    return normalized


def _severity_rank(severity: str) -> int:
    return OBSERVABILITY_SEVERITIES.index(severity)


def _max_severity(current: str, candidate: str) -> str:
    return candidate if _severity_rank(candidate) > _severity_rank(current) else current


def _status_to_base_severity(status: str) -> str:
    if status == "healthy":
        return "low"
    if status == "degraded":
        return "medium"
    if status == "unhealthy":
        return "high"
    return "high"


def classify_observability_severity(
    *,
    status: str,
    latency_ms: float | None,
    error_rate: float | None,
    dependency_available: bool | None,
) -> tuple[str, bool, list[str], str | None]:
    """Classify signal severity with deterministic reasons and review policy."""
    severity = _status_to_base_severity(status)
    review_required = status in {"unhealthy", "unknown"}
    reasons: list[str] = []
    data_quality_note: str | None = None

    if status == "healthy":
        reasons.append("COMPONENT_HEALTHY")
    elif status == "degraded":
        reasons.append("COMPONENT_DEGRADED")
    elif status == "unhealthy":
        reasons.append("COMPONENT_UNHEALTHY")
    else:
        reasons.append("COMPONENT_STATUS_UNKNOWN")
        data_quality_note = "unknown component status requires operator review"

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

    return severity, review_required, sorted(set(reasons)), data_quality_note


def build_observability_signal(
    *,
    tenant_id: int,
    component: str,
    status: str,
    source: str,
    source_entity_type: str,
    source_entity_id: str,
    latency_ms: float | None = None,
    error_rate: float | None = None,
    dependency_available: bool | None = None,
) -> dict[str, Any]:
    """Build deterministic tenant-safe observability signal evidence."""
    _validate_tenant(tenant_id)
    component_name = _normalize_required(component, field="component").lower()
    status_name = _normalize_required(status, field="status").lower()
    source_name = _normalize_required(source, field="source")
    source_type = _normalize_required(source_entity_type, field="source_entity_type")
    source_id = _normalize_required(source_entity_id, field="source_entity_id")

    if component_name not in OBSERVABILITY_COMPONENTS:
        raise ValueError(f"component must be one of {sorted(OBSERVABILITY_COMPONENTS)}")
    if status_name not in OBSERVABILITY_SIGNAL_STATUSES:
        raise ValueError(f"status must be one of {sorted(OBSERVABILITY_SIGNAL_STATUSES)}")
    if latency_ms is not None and latency_ms < 0:
        raise ValueError("latency_ms must be >= 0")
    if error_rate is not None and (error_rate < 0 or error_rate > 1):
        raise ValueError("error_rate must be between 0 and 1")

    severity, review_required, reasons, data_quality_note = classify_observability_severity(
        status=status_name,
        latency_ms=latency_ms,
        error_rate=error_rate,
        dependency_available=dependency_available,
    )

    return {
        "tenant_id": tenant_id,
        "component": component_name,
        "status": status_name,
        "severity": severity,
        "review_required": review_required,
        "reasons": reasons,
        "latency_ms": latency_ms,
        "error_rate": error_rate,
        "dependency_available": dependency_available,
        "source": source_name,
        "source_entity_type": source_type,
        "source_entity_id": source_id,
        "event_readiness": OBSERVABILITY_EVENT_READINESS[status_name],
        "audit_action": f"observability.signal.{status_name}",
        "data_quality_note": data_quality_note,
        "no_fake_uptime": True,
        "no_fake_sla": True,
        "no_external_monitoring_provider": True,
        "no_fake_alert_execution": True,
    }


def build_observability_signal_from_platform_health(
    *,
    tenant_id: int,
    platform_health_evidence: dict[str, Any],
) -> dict[str, Any]:
    """Map platform_health evidence into observability signal contract."""
    _validate_tenant(tenant_id)
    source_tenant_id = int(platform_health_evidence.get("tenant_id", 0) or 0)
    if source_tenant_id != tenant_id:
        raise ValueError("platform_health_evidence tenant_id mismatch")

    severity = str(platform_health_evidence.get("severity", "high")).strip().lower()
    status = "healthy"
    if severity == "medium":
        status = "degraded"
    elif severity in {"high", "critical"}:
        status = "unhealthy"

    return build_observability_signal(
        tenant_id=tenant_id,
        component="platform_health",
        status=status,
        latency_ms=platform_health_evidence.get("latency_ms"),
        error_rate=platform_health_evidence.get("error_rate"),
        dependency_available=platform_health_evidence.get("dependency_available"),
        source="platform_health",
        source_entity_type=str(platform_health_evidence.get("source_entity_type", "service")),
        source_entity_id=str(platform_health_evidence.get("source_entity_id", "platform_health")),
    )


def summarize_observability_components(*, tenant_id: int, signals: list[dict[str, Any]]) -> dict[str, Any]:
    """Alias for summary builder to keep API explicit in tests/reports."""
    return build_observability_summary(tenant_id=tenant_id, signals=signals)


def build_observability_summary(*, tenant_id: int, signals: list[dict[str, Any]]) -> dict[str, Any]:
    """Build deterministic operational visibility summary for L4 evidence."""
    _validate_tenant(tenant_id)

    if not signals:
        return {
            "tenant_id": tenant_id,
            "overall_status": "unknown",
            "severity": "high",
            "component_count": 0,
            "degraded_count": 0,
            "unhealthy_count": 0,
            "unknown_count": 0,
            "review_required": True,
            "evidence_items": [],
            "integrated_components": [],
            "data_quality_note": "no observability signals available",
            "event_readiness_decision": "deferred_to_a0245",
            "no_fake_uptime": True,
            "no_fake_sla": True,
            "no_external_monitoring_provider": True,
            "no_fake_alert_execution": True,
        }

    normalized: list[dict[str, Any]] = []
    max_severity = "low"
    degraded_count = 0
    unhealthy_count = 0
    unknown_count = 0
    review_required = False

    for signal in signals:
        signal_tenant_id = int(signal.get("tenant_id", 0) or 0)
        if signal_tenant_id != tenant_id:
            raise ValueError("all observability signals must match tenant_id")

        component = str(signal.get("component", "")).strip().lower()
        status = str(signal.get("status", "")).strip().lower()
        severity = str(signal.get("severity", "")).strip().lower()

        if component not in OBSERVABILITY_COMPONENTS:
            raise ValueError(f"component must be one of {sorted(OBSERVABILITY_COMPONENTS)}")
        if status not in OBSERVABILITY_SIGNAL_STATUSES:
            raise ValueError(f"status must be one of {sorted(OBSERVABILITY_SIGNAL_STATUSES)}")
        if severity not in OBSERVABILITY_SEVERITIES:
            raise ValueError(f"severity must be one of {list(OBSERVABILITY_SEVERITIES)}")

        if status == "degraded":
            degraded_count += 1
        elif status == "unhealthy":
            unhealthy_count += 1
        elif status == "unknown":
            unknown_count += 1

        if bool(signal.get("review_required", False)):
            review_required = True

        max_severity = _max_severity(max_severity, severity)

        normalized.append(
            {
                "component": component,
                "status": status,
                "severity": severity,
                "audit_action": str(signal.get("audit_action", "observability.signal.unknown")),
                "source": str(signal.get("source", "unknown")),
                "source_entity_type": str(signal.get("source_entity_type", "unknown")),
                "source_entity_id": str(signal.get("source_entity_id", "unknown")),
                "event_readiness": str(
                    signal.get("event_readiness", OBSERVABILITY_EVENT_READINESS.get(status, "platform.observability.review_required"))
                ),
            }
        )

    overall_status = "healthy"
    if unhealthy_count > 0:
        overall_status = "unhealthy"
        review_required = True
    elif degraded_count > 0:
        overall_status = "degraded"
    elif unknown_count > 0:
        overall_status = "unknown"
        review_required = True

    data_quality_note: str | None = None
    if unknown_count > 0:
        data_quality_note = "some components reported unknown status"

    integrated_components = sorted(
        {
            item["component"]
            for item in normalized
            if item["component"] in OBSERVABILITY_INTEGRATION_COMPONENTS
        }
    )

    return {
        "tenant_id": tenant_id,
        "overall_status": overall_status,
        "severity": max_severity,
        "component_count": len(normalized),
        "degraded_count": degraded_count,
        "unhealthy_count": unhealthy_count,
        "unknown_count": unknown_count,
        "review_required": review_required,
        "evidence_items": sorted(normalized, key=lambda item: (item["component"], item["source_entity_id"])),
        "integrated_components": integrated_components,
        "data_quality_note": data_quality_note,
        "event_readiness_decision": "deferred_to_a0245",
        "no_fake_uptime": True,
        "no_fake_sla": True,
        "no_external_monitoring_provider": True,
        "no_fake_alert_execution": True,
    }
