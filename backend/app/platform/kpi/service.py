from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any

from app.platform.event_ingestion import service as event_ingestion_service
from app.platform.event_ingestion.types import (
    ANALYTICS_EVENT_READ,
    ANALYTICS_KPI_READ,
    BILLING_USAGE_RECORDED,
    KPI_REFRESH_EXECUTED,
)
from app.platform.kpi.repository import KpiRepository

_SHARED_KPI_REPOSITORY = KpiRepository()
_kpi_repository = _SHARED_KPI_REPOSITORY


METRIC_TITLES: dict[str, str] = {
    "total_students": "Total Students",
    "total_enrollments": "Total Enrollments",
    "total_grades_submitted": "Total Grades Submitted",
    "total_active_subscriptions": "Active Subscriptions",
    "total_failed_jobs": "Failed Jobs",
    "total_failed_notifications": "Failed Notifications",
    "analytics_events_ingested_total": "Analytics Events Ingested Total",
    "analytics_events_reads_total": "Analytics Events Reads Total",
    "analytics_kpi_reads_total": "Analytics KPI Reads Total",
    "analytics_reads_total": "Analytics Total Reads",
    "analytics_kpi_reads_share_pct": "Analytics KPI Reads Share (%)",
    "analytics_events_reads_from_events_total": "Analytics Events Reads (Event-Derived) Total",
    "analytics_kpi_reads_from_events_total": "Analytics KPI Reads (Event-Derived) Total",
    "billing_usage_recorded_from_events_total": "Billing Usage Recorded (Event-Derived) Total",
}


EVENT_METRIC_MAP: dict[str, str] = {
    "student.created": "total_students",
    "enrollment.created": "total_enrollments",
    "grade.submitted": "total_grades_submitted",
}


EVENT_DERIVED_METRIC_LINEAGE: dict[str, list[str]] = {
    "analytics_events_reads_from_events_total": [ANALYTICS_EVENT_READ],
    "analytics_kpi_reads_from_events_total": [ANALYTICS_KPI_READ],
    "billing_usage_recorded_from_events_total": [BILLING_USAGE_RECORDED],
}


USAGE_DERIVED_METRICS: set[str] = {
    "analytics_events_reads_total",
    "analytics_kpi_reads_total",
    "analytics_reads_total",
    "analytics_kpi_reads_share_pct",
}

KPI_SURFACE_ID = "tenant_analytics_kpis"
KPI_CONTRACT_VERSION = "v1"
KPI_SURFACE_CAPABILITIES: dict[str, bool] = {
    "supports_cards": True,
    "supports_trends": True,
    "supports_insights": True,
    "supports_recommendations": True,
    "supports_refresh": True,
    "supports_refresh_history": True,
    "supports_change_digest": True,
    "supports_source_mix": True,
    "supports_lineage": True,
    "supports_source_breakdown": True,
    "supports_thresholds": True,
    "supports_actionability": True,
}

KPI_SURFACE_PROFILE: dict[str, Any] = {
    "audience_profiles": [
        "human_dashboard",
        "machine_client",
        "support_traceable",
    ],
    "primary_audience": "human_dashboard",
    "consumption_mode": "structured_read_model",
}

KPI_FIELD_SEMANTICS: dict[str, str] = {
    "capabilities": "supported surface features",
    "sections": "current response section presence and state",
    "contract_invariants": "guaranteed structural compatibility markers",
    "contract_fingerprint": "stable contract checksum identity",
    "surface_profile": "intended audience and use mode",
    "response_status": "current response readiness state",
    "request_id": "request correlation identifier",
    "served_at": "response generation timestamp",
}

KPI_CARD_FIELD_SEMANTICS: dict[str, str] = {
    "severity": "bounded operational severity",
    "threshold_basis": "threshold measurement basis",
    "policy_pack": "named evaluation profile",
    "actionability_state": "bounded urgency hint",
    "source_status": "primary source derivation mode",
}

KPI_RESPONSE_EXAMPLES: dict[str, dict[str, str]] = {
    "empty_shape": {
        "readiness_status": "empty",
        "cards": "empty",
        "summary": "present",
        "change_digest": "present",
        "source_mix_summary": "present",
        "capabilities": "present",
        "sections": "present",
    },
    "ready_shape": {
        "readiness_status": "ready",
        "cards": "populated",
        "summary": "populated",
        "change_digest": "populated",
        "source_mix_summary": "populated",
        "capabilities": "present",
        "sections": "present",
    },
}

KPI_SURFACE_MAP: dict[str, Any] = {
    "family_id": "tenant_analytics_endpoint_family_v1",
    "endpoints": [
        {"name": "kpis", "path": "/api/analytics/kpis", "role": "primary_read"},
        {"name": "kpi_trends", "path": "/api/analytics/kpis/trends", "role": "trend_read"},
        {"name": "kpi_insights", "path": "/api/analytics/kpis/insights", "role": "insight_read"},
        {
            "name": "kpi_recommendations",
            "path": "/api/analytics/kpis/recommendations",
            "role": "recommendation_read",
        },
        {"name": "kpi_refresh", "path": "/api/analytics/kpis/refresh", "role": "refresh_action"},
        {
            "name": "kpi_refresh_history",
            "path": "/api/analytics/kpis/refresh-history",
            "role": "refresh_history_read",
        },
        {"name": "events", "path": "/api/analytics/events", "role": "event_read"},
        {
            "name": "events_summary",
            "path": "/api/analytics/events/summary",
            "role": "event_summary_read",
        },
    ],
}

KPI_WORKFLOW_HINTS: dict[str, list[str]] = {
    "primary_flow": [
        "kpis",
        "kpi_trends",
        "kpi_insights",
        "kpi_recommendations",
    ],
    "operational_flow": [
        "kpi_refresh",
        "kpi_refresh_history",
    ],
    "observability_flow": [
        "events",
        "events_summary",
    ],
}

KPI_CONTRACT_FINGERPRINT_ALGORITHM = "sha256"
KPI_CONTRACT_FINGERPRINT_BASIS = "surface_contract_v1"
KPI_CONTRACT_COMPATIBILITY_MODE = "backward_additive_v1"
KPI_CONTRACT_COMPATIBILITY_FINGERPRINT_SCOPE = "stable_contract_basis"

KPI_STABILITY_TIERS: dict[str, list[str]] = {
    "stable_core_fields": [
        "surface_id",
        "contract_version",
        "tenant_id",
        "sections",
        "request_id",
        "served_at",
    ],
    "extensible_metadata_blocks": [
        "capabilities",
        "contract_invariants",
        "contract_fingerprint",
        "contract_compatibility",
        "surface_profile",
        "field_semantics",
        "card_field_semantics",
        "response_examples",
        "surface_map",
        "workflow_hints",
        "stability_tiers",
    ],
    "data_dependent_blocks": [
        "kpis",
        "summary",
        "change_digest",
        "source_mix_summary",
        "readiness_status",
        "snapshot_date",
        "generated_at",
        "freshness_status",
        "source_mode",
        "response_status",
    ],
    "stable_card_core_fields": [
        "key",
        "title",
        "description",
        "value",
        "readiness_status",
        "source_status",
        "trend",
    ],
    "optional_card_fields": [
        "lineage",
        "source_breakdown",
        "severity",
        "threshold_basis",
        "policy_pack",
        "actionability_state",
    ],
}

KPI_GUARANTEED_TOP_LEVEL_FIELDS: list[str] = [
    "surface_id",
    "contract_version",
    "capabilities",
    "sections",
    "surface_profile",
    "field_semantics",
    "card_field_semantics",
    "response_examples",
    "surface_map",
    "workflow_hints",
    "stability_tiers",
    "contract_fingerprint",
    "contract_compatibility",
    "request_id",
    "served_at",
    "response_status",
    "tenant_id",
    "snapshot_date",
    "generated_at",
    "readiness_status",
    "freshness_status",
    "source_mode",
    "kpis",
    "summary",
    "change_digest",
    "source_mix_summary",
    "contract_invariants",
]

KPI_ALWAYS_PRESENT_SECTIONS: list[str] = [
    "cards",
    "summary",
    "change_digest",
    "source_mix_summary",
    "capabilities",
    "contract_identity",
    "surface_profile",
    "field_semantics",
    "card_field_semantics",
    "response_examples",
    "surface_map",
    "workflow_hints",
    "stability_tiers",
    "contract_fingerprint",
    "contract_compatibility",
    "contract_invariants",
]

KPI_OPTIONAL_CARD_FIELDS: list[str] = [
    "lineage",
    "source_breakdown",
    "severity",
    "threshold_basis",
    "policy_pack",
    "actionability_state",
]


def _build_kpi_contract_invariants() -> dict[str, Any]:
    """Return bounded client-facing compatibility guarantees for the KPI surface."""
    return {
        "guaranteed_top_level_fields": list(KPI_GUARANTEED_TOP_LEVEL_FIELDS),
        "always_present_sections": list(KPI_ALWAYS_PRESENT_SECTIONS),
        "optional_card_fields": list(KPI_OPTIONAL_CARD_FIELDS),
        "empty_state_contract_stable": True,
    }


def _build_kpi_contract_compatibility() -> dict[str, Any]:
    """Return bounded compatibility assertions for stable KPI client integrations."""
    return {
        "compatibility_mode": KPI_CONTRACT_COMPATIBILITY_MODE,
        "backward_compatible_with": [KPI_CONTRACT_VERSION],
        "stable_core_enforced": True,
        "additive_metadata_extensions_allowed": True,
        "data_dependent_blocks_may_vary": True,
        "fingerprint_scope": KPI_CONTRACT_COMPATIBILITY_FINGERPRINT_SCOPE,
    }


def _build_kpi_surface_profile() -> dict[str, Any]:
    """Return bounded intended-consumption metadata for the KPI surface."""
    return {
        "audience_profiles": list(KPI_SURFACE_PROFILE["audience_profiles"]),
        "primary_audience": KPI_SURFACE_PROFILE["primary_audience"],
        "consumption_mode": KPI_SURFACE_PROFILE["consumption_mode"],
    }


def _build_kpi_field_semantics() -> dict[str, str]:
    """Return a minimal client guide for top-level KPI contract blocks."""
    return dict(KPI_FIELD_SEMANTICS)


def _build_kpi_card_field_semantics() -> dict[str, str]:
    """Return a minimal client guide for KPI card governance fields."""
    return dict(KPI_CARD_FIELD_SEMANTICS)


def _build_kpi_response_examples() -> dict[str, dict[str, str]]:
    """Return canonical empty/ready shape markers for client integration guidance."""
    return {
        "empty_shape": dict(KPI_RESPONSE_EXAMPLES["empty_shape"]),
        "ready_shape": dict(KPI_RESPONSE_EXAMPLES["ready_shape"]),
    }


def _build_kpi_surface_map() -> dict[str, Any]:
    """Return bounded endpoint-family map for related analytics endpoints."""
    return {
        "family_id": KPI_SURFACE_MAP["family_id"],
        "endpoints": [dict(endpoint) for endpoint in KPI_SURFACE_MAP["endpoints"]],
    }


def _build_kpi_workflow_hints() -> dict[str, list[str]]:
    """Return bounded recommended endpoint-consumption order for analytics clients."""
    return {
        "primary_flow": list(KPI_WORKFLOW_HINTS["primary_flow"]),
        "operational_flow": list(KPI_WORKFLOW_HINTS["operational_flow"]),
        "observability_flow": list(KPI_WORKFLOW_HINTS["observability_flow"]),
    }


def _build_kpi_stability_tiers() -> dict[str, list[str]]:
    """Return bounded stability and change-safety tiers for the KPI contract."""
    return {
        "stable_core_fields": list(KPI_STABILITY_TIERS["stable_core_fields"]),
        "extensible_metadata_blocks": list(KPI_STABILITY_TIERS["extensible_metadata_blocks"]),
        "data_dependent_blocks": list(KPI_STABILITY_TIERS["data_dependent_blocks"]),
        "stable_card_core_fields": list(KPI_STABILITY_TIERS["stable_card_core_fields"]),
        "optional_card_fields": list(KPI_STABILITY_TIERS["optional_card_fields"]),
    }


def _build_kpi_contract_fingerprint() -> dict[str, str]:
    """Return deterministic checksum for stable contract identity inputs."""
    basis_payload = {
        "fingerprint_basis": KPI_CONTRACT_FINGERPRINT_BASIS,
        "surface_id": KPI_SURFACE_ID,
        "contract_version": KPI_CONTRACT_VERSION,
        "guaranteed_top_level_fields": list(KPI_GUARANTEED_TOP_LEVEL_FIELDS),
        "always_present_sections": list(KPI_ALWAYS_PRESENT_SECTIONS),
        "capabilities": dict(KPI_SURFACE_CAPABILITIES),
        "contract_invariants": _build_kpi_contract_invariants(),
        "surface_profile": _build_kpi_surface_profile(),
        "surface_map": _build_kpi_surface_map(),
        "workflow_hints": _build_kpi_workflow_hints(),
        "stability_tiers": _build_kpi_stability_tiers(),
        "contract_compatibility": _build_kpi_contract_compatibility(),
    }
    canonical = json.dumps(basis_payload, sort_keys=True, separators=(",", ":"))
    value = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return {
        "algorithm": KPI_CONTRACT_FINGERPRINT_ALGORITHM,
        "value": value,
        "fingerprint_basis": KPI_CONTRACT_FINGERPRINT_BASIS,
    }


def attach_kpi_response_envelope(
    payload: dict[str, Any], *, request_id: str | None, served_at: str | None = None
) -> dict[str, Any]:
    """Attach bounded request/response envelope fields to an already-built KPI payload."""
    response_status = str(payload.get("readiness_status") or "unknown").strip().lower() or "unknown"
    enriched = dict(payload)
    enriched["request_id"] = request_id
    enriched["served_at"] = served_at or datetime.now(timezone.utc).isoformat()
    enriched["response_status"] = response_status
    enriched["contract_invariants"] = _build_kpi_contract_invariants()
    return enriched


def _lineage_for_metric(metric_key: str) -> dict[str, object] | None:
    event_types = EVENT_DERIVED_METRIC_LINEAGE.get(str(metric_key).strip().lower())
    if not event_types:
        return None
    return {
        "source_type": "platform_events",
        "source_event_types": list(event_types),
        "derived_from": "event_projection",
    }


def _breakdown_for_metric(
    metric_key: str, event_counts: dict[str, int]
) -> list[dict[str, Any]] | None:
    """Return per-event-type count breakdown for event-derived KPIs only.

    Returns None for metrics not in EVENT_DERIVED_METRIC_LINEAGE.
    """
    event_types = EVENT_DERIVED_METRIC_LINEAGE.get(str(metric_key).strip().lower())
    if not event_types:
        return None
    return [
        {"event_type": et, "count": int(event_counts.get(et, 0))}
        for et in event_types
    ]


def clear_kpi_state() -> None:
    _kpi_repository.clear_state()


def refresh_tenant_metrics(*, tenant_id: int, uow: Any, snapshot_date: str | None = None) -> list[dict[str, Any]]:
    repo = uow.kpi_repository
    conn = getattr(uow, "conn", None)
    day = snapshot_date or datetime.now(timezone.utc).date().isoformat()

    analytics_latest = uow.analytics_repository.get_latest_kpi_snapshot(tenant_id=int(tenant_id), conn=conn)
    analytics_counts = dict((analytics_latest or {}).get("event_counts_json", {}))
    analytics_events_ingested_total = int((analytics_latest or {}).get("total_events", 0) or 0)

    usage_rows = uow.usage_repository.list_for_tenant_period(
        int(tenant_id),
        period_key="current",
        conn=conn,
    )
    usage_by_metric = {
        str(item.get("metric", "")).strip().lower(): int(item.get("value", 0) or 0)
        for item in usage_rows
    }
    analytics_events_reads_total = int(usage_by_metric.get("analytics.events.read", 0) or 0)
    analytics_kpi_reads_total = int(usage_by_metric.get("analytics.kpi.read", 0) or 0)
    analytics_reads_total = analytics_events_reads_total + analytics_kpi_reads_total
    analytics_kpi_reads_share_pct = (
        int(round((analytics_kpi_reads_total * 100.0) / analytics_reads_total))
        if analytics_reads_total > 0
        else 0
    )

    metric_values: dict[str, int] = {}
    if conn is None:
        for event_type, metric_key in EVENT_METRIC_MAP.items():
            metric_values[metric_key] = len(
                uow.analytics_repository.list_event_projections(
                    tenant_id=int(tenant_id),
                    event_type=event_type,
                    limit=1_000_000,
                    conn=conn,
                )
            )
    else:
        for event_type, metric_key in EVENT_METRIC_MAP.items():
            metric_values[metric_key] = repo.count_events_by_type(
                tenant_id=int(tenant_id),
                event_type=event_type,
                conn=conn,
            )

    subscription = uow.billing_repository.get_subscription(int(tenant_id), conn=conn)
    metric_values["total_active_subscriptions"] = 1 if subscription and subscription.get("status") == "active" else 0
    if conn is None:
        failed_jobs = uow.job_repository.list_for_tenant(int(tenant_id), status="failed", limit=1_000_000, conn=conn)
        metric_values["total_failed_jobs"] = len(failed_jobs)

        notifications = uow.notification_repository.list_for_tenant(int(tenant_id), limit=1_000_000, conn=conn)
        metric_values["total_failed_notifications"] = sum(
            1 for row in notifications if str(row.get("status", "")).lower() == "failed"
        )
    else:
        metric_values["total_failed_jobs"] = repo.count_failed_jobs(tenant_id=int(tenant_id), conn=conn)
        metric_values["total_failed_notifications"] = repo.count_failed_notifications(tenant_id=int(tenant_id), conn=conn)

    metric_values["analytics_events_ingested_total"] = analytics_events_ingested_total
    metric_values["analytics_events_reads_total"] = analytics_events_reads_total
    metric_values["analytics_kpi_reads_total"] = analytics_kpi_reads_total
    metric_values["analytics_reads_total"] = analytics_reads_total
    metric_values["analytics_kpi_reads_share_pct"] = analytics_kpi_reads_share_pct

    # Event-to-KPI projection bridge v1: derive KPI-friendly counters from append-only platform_events.
    event_counts = event_ingestion_service.summary_for_tenant(int(tenant_id), uow=uow)
    metric_values["analytics_events_reads_from_events_total"] = int(event_counts.get(ANALYTICS_EVENT_READ, 0) or 0)
    metric_values["analytics_kpi_reads_from_events_total"] = int(event_counts.get(ANALYTICS_KPI_READ, 0) or 0)
    metric_values["billing_usage_recorded_from_events_total"] = int(event_counts.get(BILLING_USAGE_RECORDED, 0) or 0)

    rows: list[dict[str, Any]] = []
    for metric_key, metric_value in metric_values.items():
        lineage = _lineage_for_metric(metric_key)
        rows.append(
            repo.upsert_metric_snapshot(
                tenant_id=int(tenant_id),
                metric_key=metric_key,
                metric_value=int(metric_value),
                snapshot_date=day,
                metadata_json={
                    "title": METRIC_TITLES.get(metric_key, metric_key),
                    "source": "analytics_sink_v1" if metric_key in {
                        "total_students",
                        "total_enrollments",
                        "total_grades_submitted",
                        "analytics_events_ingested_total",
                        "analytics_events_reads_total",
                        "analytics_kpi_reads_total",
                        "analytics_reads_total",
                        "analytics_kpi_reads_share_pct",
                        "analytics_events_reads_from_events_total",
                        "analytics_kpi_reads_from_events_total",
                        "billing_usage_recorded_from_events_total",
                    } else "platform_core",
                    "analytics_today": int(analytics_counts.get(_metric_key_to_event(metric_key), 0)),
                    "lineage": lineage,
                },
                conn=conn,
            )
        )

    rows.sort(key=lambda item: str(item["metric_key"]))
    return rows


def refresh_tenant_dashboard_snapshot(
    *,
    tenant_id: int,
    uow: Any,
    snapshot_date: str | None = None,
) -> dict[str, Any]:
    repo = uow.kpi_repository
    conn = getattr(uow, "conn", None)
    day = snapshot_date or datetime.now(timezone.utc).date().isoformat()

    metrics = refresh_tenant_metrics(tenant_id=int(tenant_id), uow=uow, snapshot_date=day)

    cards: list[dict[str, Any]] = []
    for metric in metrics:
        metric_key = str(metric["metric_key"])
        history = repo.list_metric_history(
            tenant_id=int(tenant_id),
            metric_key=metric_key,
            days=7,
            conn=conn,
        )
        cards.append(
            {
                "metric_key": metric_key,
                "title": METRIC_TITLES.get(metric_key, metric_key),
                "value": int(metric["metric_value"]),
                "trend_7d": [
                    {"snapshot_date": str(point["snapshot_date"]), "value": int(point["metric_value"])}
                    for point in history
                ],
                "metadata_json": dict(metric.get("metadata_json") or {}),
            }
        )

    payload = {
        "tenant_id": int(tenant_id),
        "snapshot_date": day,
        "cards": cards,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": "kpi_metrics_engine_v1",
    }

    return repo.upsert_dashboard_snapshot(
        tenant_id=int(tenant_id),
        snapshot_date=day,
        snapshot_json=payload,
        conn=conn,
    )


def get_latest_tenant_metrics(*, tenant_id: int, uow: Any) -> list[dict[str, Any]]:
    repo = uow.kpi_repository
    conn = getattr(uow, "conn", None)
    return repo.list_latest_metrics(tenant_id=int(tenant_id), conn=conn)


def get_tenant_product_kpis(*, tenant_id: int, uow: Any) -> dict[str, Any]:
    repo = uow.kpi_repository
    conn = getattr(uow, "conn", None)
    rows = repo.list_latest_metrics(tenant_id=int(tenant_id), conn=conn)

    if not rows:
        cards: list[dict[str, Any]] = []
        summary = _build_kpi_portfolio_summary(cards)
        change_digest = _build_kpi_change_digest(cards)
        source_mix_summary = _build_kpi_source_mix_summary(cards)
        return {
            "surface_id": KPI_SURFACE_ID,
            "contract_version": KPI_CONTRACT_VERSION,
            "capabilities": dict(KPI_SURFACE_CAPABILITIES),
            "surface_profile": _build_kpi_surface_profile(),
            "field_semantics": _build_kpi_field_semantics(),
            "card_field_semantics": _build_kpi_card_field_semantics(),
            "response_examples": _build_kpi_response_examples(),
            "surface_map": _build_kpi_surface_map(),
            "workflow_hints": _build_kpi_workflow_hints(),
            "stability_tiers": _build_kpi_stability_tiers(),
            "contract_fingerprint": _build_kpi_contract_fingerprint(),
            "contract_compatibility": _build_kpi_contract_compatibility(),
            "tenant_id": int(tenant_id),
            "snapshot_date": None,
            "generated_at": None,
            "readiness_status": "empty",
            "freshness_status": "empty",
            "source_mode": "empty",
            "kpis": cards,
            "summary": summary,
            "change_digest": change_digest,
            "source_mix_summary": source_mix_summary,
            "sections": _build_kpi_sections_manifest(
                cards=cards,
                summary=summary,
                change_digest=change_digest,
                source_mix_summary=source_mix_summary,
                capabilities=dict(KPI_SURFACE_CAPABILITIES),
                surface_id=KPI_SURFACE_ID,
                contract_version=KPI_CONTRACT_VERSION,
                surface_profile=_build_kpi_surface_profile(),
                field_semantics=_build_kpi_field_semantics(),
                card_field_semantics=_build_kpi_card_field_semantics(),
                response_examples=_build_kpi_response_examples(),
                surface_map=_build_kpi_surface_map(),
                workflow_hints=_build_kpi_workflow_hints(),
                stability_tiers=_build_kpi_stability_tiers(),
                contract_fingerprint=_build_kpi_contract_fingerprint(),
                contract_compatibility=_build_kpi_contract_compatibility(),
            ),
        }

    snapshot_date = str(rows[0].get("snapshot_date")) if rows else None
    generated_at = max(str(item.get("updated_at") or "") for item in rows) or None

    # Fetch event counts once — reused for per-card source_breakdown without extra queries.
    event_counts: dict[str, int] = event_ingestion_service.summary_for_tenant(
        int(tenant_id), uow=uow
    )

    cards: list[dict[str, Any]] = []
    for row in rows:
        metric_key = str(row.get("metric_key") or "").strip().lower()
        metadata_json = dict(row.get("metadata_json") or {})
        title = str(metadata_json.get("title") or METRIC_TITLES.get(metric_key, metric_key))
        trend_rows = repo.list_metric_history(
            tenant_id=int(tenant_id),
            metric_key=metric_key,
            days=7,
            conn=conn,
        )
        metric_value = int(row.get("metric_value") or 0)
        severity, threshold_basis, policy_pack = _severity_for_metric(metric_key, metric_value)
        cards.append(
            {
                "key": metric_key,
                "title": title,
                "description": title,
                "value": metric_value,
                "lineage": metadata_json.get("lineage"),
                "readiness_status": "ready",
                "source_status": _card_source_status(metric_key=metric_key, lineage=metadata_json.get("lineage")),
                "source_breakdown": _breakdown_for_metric(metric_key, event_counts),
                "severity": severity,
                "threshold_basis": threshold_basis,
                "policy_pack": policy_pack,
                "actionability_state": _actionability_for_severity(severity),
                "trend": [
                    {
                        "snapshot_date": str(point.get("snapshot_date")),
                        "value": int(point.get("metric_value") or 0),
                    }
                    for point in trend_rows
                ],
            }
        )

    summary = _build_kpi_portfolio_summary(cards)
    change_digest = _build_kpi_change_digest(cards)
    source_mix_summary = _build_kpi_source_mix_summary(cards)

    return {
        "surface_id": KPI_SURFACE_ID,
        "contract_version": KPI_CONTRACT_VERSION,
        "capabilities": dict(KPI_SURFACE_CAPABILITIES),
        "surface_profile": _build_kpi_surface_profile(),
        "field_semantics": _build_kpi_field_semantics(),
        "card_field_semantics": _build_kpi_card_field_semantics(),
        "response_examples": _build_kpi_response_examples(),
        "surface_map": _build_kpi_surface_map(),
        "workflow_hints": _build_kpi_workflow_hints(),
        "stability_tiers": _build_kpi_stability_tiers(),
        "contract_fingerprint": _build_kpi_contract_fingerprint(),
        "contract_compatibility": _build_kpi_contract_compatibility(),
        "tenant_id": int(tenant_id),
        "snapshot_date": snapshot_date,
        "generated_at": generated_at,
        "readiness_status": "ready",
        "freshness_status": _freshness_status(snapshot_date=snapshot_date, generated_at=generated_at),
        "source_mode": _response_source_mode(cards),
        "kpis": cards,
        "summary": summary,
        "change_digest": change_digest,
        "source_mix_summary": source_mix_summary,
        "sections": _build_kpi_sections_manifest(
            cards=cards,
            summary=summary,
            change_digest=change_digest,
            source_mix_summary=source_mix_summary,
            capabilities=dict(KPI_SURFACE_CAPABILITIES),
            surface_id=KPI_SURFACE_ID,
            contract_version=KPI_CONTRACT_VERSION,
            surface_profile=_build_kpi_surface_profile(),
            field_semantics=_build_kpi_field_semantics(),
            card_field_semantics=_build_kpi_card_field_semantics(),
            response_examples=_build_kpi_response_examples(),
            surface_map=_build_kpi_surface_map(),
            workflow_hints=_build_kpi_workflow_hints(),
            stability_tiers=_build_kpi_stability_tiers(),
            contract_fingerprint=_build_kpi_contract_fingerprint(),
            contract_compatibility=_build_kpi_contract_compatibility(),
        ),
    }


def execute_tenant_product_kpi_refresh(*, tenant_id: int, uow: Any) -> dict[str, Any]:
    normalized_tenant_id = int(tenant_id)
    try:
        refreshed_rows = refresh_tenant_metrics(tenant_id=normalized_tenant_id, uow=uow)
        latest = get_tenant_product_kpis(tenant_id=normalized_tenant_id, uow=uow)
        result = {
            "tenant_id": normalized_tenant_id,
            "refresh_executed": True,
            "snapshot_date": latest.get("snapshot_date"),
            "generated_at": latest.get("generated_at"),
            "readiness_status": latest.get("readiness_status"),
            "freshness_status": latest.get("freshness_status"),
            "source_mode": latest.get("source_mode"),
            "kpi_count": len(refreshed_rows),
        }
        event_ingestion_service.record_event(
            normalized_tenant_id,
            KPI_REFRESH_EXECUTED,
            {
                "status": "success",
                "snapshot_date": result.get("snapshot_date"),
                "generated_at": result.get("generated_at"),
                "kpi_count": int(result.get("kpi_count") or 0),
            },
            uow=uow,
        )
        return result
    except Exception:
        event_ingestion_service.record_event(
            normalized_tenant_id,
            KPI_REFRESH_EXECUTED,
            {
                "status": "failed",
                "snapshot_date": None,
                "generated_at": None,
                "kpi_count": 0,
            },
            uow=uow,
        )
        raise


def get_tenant_product_kpi_refresh_history(*, tenant_id: int, uow: Any, limit: int = 10) -> dict[str, Any]:
    normalized_tenant_id = int(tenant_id)
    normalized_limit = int(limit)
    if normalized_limit < 1 or normalized_limit > 50:
        normalized_limit = 10

    events = event_ingestion_service.list_events_for_tenant(
        normalized_tenant_id,
        event_type=KPI_REFRESH_EXECUTED,
        limit=normalized_limit,
        uow=uow,
    )
    recent_refreshes: list[dict[str, Any]] = []
    for event in events:
        payload = dict(event.get("payload_json") or {})
        recent_refreshes.append(
            {
                "event_id": int(event.get("id") or 0),
                "created_at": str(event.get("created_at") or ""),
                "status": str(payload.get("status") or "unknown"),
                "kpi_count": int(payload.get("kpi_count") or 0),
                "snapshot_date": payload.get("snapshot_date"),
                "generated_at": payload.get("generated_at"),
            }
        )

    last = recent_refreshes[0] if recent_refreshes else None
    return {
        "tenant_id": normalized_tenant_id,
        "limit": normalized_limit,
        "last_refresh_at": last.get("created_at") if last else None,
        "last_refresh_status": last.get("status") if last else None,
        "last_refresh_kpi_count": int(last.get("kpi_count") or 0) if last else None,
        "recent_refreshes": recent_refreshes,
    }


def get_tenant_product_kpi_trends(*, tenant_id: int, uow: Any, window_days: int = 30) -> dict[str, Any]:
    repo = uow.kpi_repository
    conn = getattr(uow, "conn", None)
    rows = repo.list_latest_metrics(tenant_id=int(tenant_id), conn=conn)

    normalized_window_days = int(window_days)
    if normalized_window_days not in {7, 30, 90}:
        normalized_window_days = 30

    if not rows:
        return {
            "tenant_id": int(tenant_id),
            "window_days": normalized_window_days,
            "snapshot_date": None,
            "generated_at": None,
            "trends": [],
        }

    snapshot_date = str(rows[0].get("snapshot_date")) if rows else None
    generated_at = max(str(item.get("updated_at") or "") for item in rows) or None

    trends: list[dict[str, Any]] = []
    for row in rows:
        metric_key = str(row.get("metric_key") or "").strip().lower()
        title = str((row.get("metadata_json") or {}).get("title") or METRIC_TITLES.get(metric_key, metric_key))
        trend_rows = repo.list_metric_history(
            tenant_id=int(tenant_id),
            metric_key=metric_key,
            days=normalized_window_days,
            conn=conn,
        )
        points = [
            {
                "date": str(point.get("snapshot_date")),
                "value": int(point.get("metric_value") or 0),
            }
            for point in trend_rows
        ]
        latest_value = points[-1]["value"] if points else int(row.get("metric_value") or 0)
        previous_value = points[-2]["value"] if len(points) > 1 else None
        delta = (latest_value - previous_value) if previous_value is not None else None
        trends.append(
            {
                "key": metric_key,
                "title": title,
                "description": title,
                "latest_value": latest_value,
                "previous_value": previous_value,
                "delta": delta,
                "points": points,
            }
        )

    return {
        "tenant_id": int(tenant_id),
        "window_days": normalized_window_days,
        "snapshot_date": snapshot_date,
        "generated_at": generated_at,
        "trends": trends,
    }


def get_tenant_product_kpi_insights(*, tenant_id: int, uow: Any, window_days: int = 30) -> dict[str, Any]:
    trend_payload = get_tenant_product_kpi_trends(
        tenant_id=int(tenant_id),
        uow=uow,
        window_days=window_days,
    )
    trends = list(trend_payload.get("trends") or [])

    if not trends:
        return {
            "tenant_id": int(tenant_id),
            "window_days": int(trend_payload.get("window_days") or 30),
            "snapshot_date": None,
            "generated_at": None,
            "insights": [],
        }

    insights: list[dict[str, Any]] = []
    for trend in trends:
        insight = _build_insight_from_trend_row(trend)
        insights.append(insight)

    return {
        "tenant_id": int(tenant_id),
        "window_days": int(trend_payload.get("window_days") or 30),
        "snapshot_date": trend_payload.get("snapshot_date"),
        "generated_at": trend_payload.get("generated_at"),
        "insights": insights,
    }


def get_tenant_product_kpi_recommendations(*, tenant_id: int, uow: Any, window_days: int = 30) -> dict[str, Any]:
    insight_payload = get_tenant_product_kpi_insights(
        tenant_id=int(tenant_id),
        uow=uow,
        window_days=window_days,
    )
    insights = list(insight_payload.get("insights") or [])

    if not insights:
        return {
            "tenant_id": int(tenant_id),
            "window_days": int(insight_payload.get("window_days") or 30),
            "snapshot_date": None,
            "generated_at": None,
            "recommendations": [],
        }

    recommendations: list[dict[str, Any]] = []
    for insight in insights:
        recommendations.append(_build_recommendation_from_insight_row(insight))

    return {
        "tenant_id": int(tenant_id),
        "window_days": int(insight_payload.get("window_days") or 30),
        "snapshot_date": insight_payload.get("snapshot_date"),
        "generated_at": insight_payload.get("generated_at"),
        "recommendations": recommendations,
    }


def get_rector_dashboard(*, tenant_id: int, uow: Any) -> dict[str, Any]:
    repo = uow.kpi_repository
    conn = getattr(uow, "conn", None)

    latest = repo.get_latest_dashboard_snapshot(tenant_id=int(tenant_id), conn=conn)
    if latest is None:
        latest = refresh_tenant_dashboard_snapshot(tenant_id=int(tenant_id), uow=uow)

    dashboard = dict(latest.get("snapshot_json") or {})
    if not dashboard:
        dashboard = {
            "tenant_id": int(tenant_id),
            "snapshot_date": str(latest["snapshot_date"]),
            "cards": [],
            "generated_at": latest.get("updated_at"),
            "source": "kpi_metrics_engine_v1",
        }
    return dashboard


def refresh_all_tenants(*, uow: Any) -> dict[str, int]:
    conn = getattr(uow, "conn", None)
    tenants = uow.tenant_repository.list_tenant_profiles(conn=conn)

    refreshed = 0
    failed = 0
    for tenant in tenants:
        tenant_id = int(tenant["tenant_id"])
        try:
            refresh_tenant_dashboard_snapshot(tenant_id=tenant_id, uow=uow)
            refreshed += 1
        except Exception:
            failed += 1
    return {"tenants_total": len(tenants), "refreshed": refreshed, "failed": failed}


def _metric_key_to_event(metric_key: str) -> str:
    for event_type, key in EVENT_METRIC_MAP.items():
        if key == metric_key:
            return event_type
    return ""


def _freshness_status(*, snapshot_date: str | None, generated_at: str | None) -> str:
    if snapshot_date and generated_at:
        return "ready"
    return "partial_metadata"


def _card_source_status(*, metric_key: str, lineage: Any) -> str:
    if isinstance(lineage, dict) and str(lineage.get("source_type") or "").strip().lower() == "platform_events":
        return "derived_from_events"
    if str(metric_key).strip().lower() in USAGE_DERIVED_METRICS:
        return "derived_from_usage"
    return "derived_from_snapshot"


def _response_source_mode(cards: list[dict[str, Any]]) -> str:
    source_markers = {
        str(card.get("source_status") or "").strip().lower()
        for card in cards
        if str(card.get("source_status") or "").strip()
    }
    if not source_markers:
        return "empty"
    if len(source_markers) == 1:
        marker = next(iter(source_markers))
        if marker == "derived_from_events":
            return "derived_from_events"
        if marker == "derived_from_usage":
            return "derived_from_usage"
        return "derived_from_snapshot"
    return "mixed_source"


# ---------------------------------------------------------------------------
# KPI threshold / severity rules v1
# ---------------------------------------------------------------------------
# KPI_SEVERITY_RULES: metric_key → {basis, semantics}
# count  → warning_gte / critical_gte thresholds on raw value
# percent → warning when value <= low_warning OR value >= high_warning
# ---------------------------------------------------------------------------

KPI_SEVERITY_RULES: dict[str, dict[str, Any]] = {
    "total_failed_jobs": {
        "basis": "count",
        "warning_gte": 1,
        "critical_gte": 5,
        "policy_pack": "default_ops_v1",
    },
    "total_failed_notifications": {
        "basis": "count",
        "warning_gte": 1,
        "critical_gte": 5,
        "policy_pack": "default_ops_v1",
    },
    "analytics_kpi_reads_share_pct": {
        "basis": "percentage",
        # <20% → adoption too low; >80% → KPI reads dominate heavily
        "low_warning_lte": 20,
        "high_warning_gte": 80,
        "policy_pack": "analytics_adoption_v1",
    },
}


def _severity_for_metric(metric_key: str, value: int) -> tuple[str | None, str | None, str | None]:
    """Return (severity, threshold_basis, policy_pack) for a KPI card.

    Returns (None, None, None) for KPI without a threshold rule.
    Possible severity values: 'normal' | 'warning' | 'critical' | 'no_data'
    policy_pack is the named evaluation profile that produced the severity.
    """
    rule = KPI_SEVERITY_RULES.get(str(metric_key).strip().lower())
    if rule is None:
        return None, None, None

    basis = str(rule["basis"])
    policy_pack: str | None = rule.get("policy_pack")  # type: ignore[assignment]

    if basis == "count":
        v = int(value)
        if v >= int(rule["critical_gte"]):
            return "critical", basis, policy_pack
        if v >= int(rule["warning_gte"]):
            return "warning", basis, policy_pack
        return "normal", basis, policy_pack

    if basis == "percentage":
        v = int(value)
        if v == 0:
            return "no_data", basis, policy_pack
        if v <= int(rule["low_warning_lte"]) or v >= int(rule["high_warning_gte"]):
            return "warning", basis, policy_pack
        return "normal", basis, policy_pack

    return None, None, None


# ---------------------------------------------------------------------------
# KPI actionability state / escalation readiness v1
# ---------------------------------------------------------------------------
# Derived purely from severity — no additional rule duplication.
# severity → actionability_state:
#   critical  → act_now
#   warning   → review
#   normal    → observe
#   no_data   → no_action
#   None      → None  (non-thresholded KPI; no urgency semantics applicable)
# ---------------------------------------------------------------------------

_SEVERITY_TO_ACTIONABILITY: dict[str, str] = {
    "critical": "act_now",
    "warning": "review",
    "normal": "observe",
    "no_data": "no_action",
}


def _actionability_for_severity(severity: str | None) -> str | None:
    """Map pre-computed severity to bounded actionability_state.

    Returns None for non-thresholded KPI (severity is None).
    """
    if severity is None:
        return None
    return _SEVERITY_TO_ACTIONABILITY.get(str(severity).strip().lower())


def _build_kpi_portfolio_summary(cards: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate already-computed card signals into a bounded portfolio overview."""
    severity_counts = {
        "normal": 0,
        "warning": 0,
        "critical": 0,
        "no_data": 0,
    }
    actionability_counts = {
        "no_action": 0,
        "observe": 0,
        "review": 0,
        "act_now": 0,
    }

    for card in cards:
        sev = str(card.get("severity") or "").strip().lower()
        if sev in severity_counts:
            severity_counts[sev] += 1

        action_state = str(card.get("actionability_state") or "").strip().lower()
        if action_state in actionability_counts:
            actionability_counts[action_state] += 1

    overall_status = "healthy"
    if severity_counts["critical"] > 0:
        overall_status = "urgent"
    elif severity_counts["warning"] > 0:
        overall_status = "attention_needed"

    return {
        "total_kpis": len(cards),
        "severity_counts": severity_counts,
        "actionability_counts": actionability_counts,
        "overall_portfolio_status": overall_status,
    }


def _build_kpi_change_digest(cards: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate bounded change direction from existing card trend points.

    Uses only card-level trend data already assembled in get_tenant_product_kpis.
    """
    change_counts = {
        "improved": 0,
        "declined": 0,
        "unchanged": 0,
        "no_data": 0,
    }

    for card in cards:
        points = list(card.get("trend") or [])
        if len(points) < 2:
            change_counts["no_data"] += 1
            continue

        latest = int(points[-1].get("value") or 0)
        previous = int(points[-2].get("value") or 0)
        delta = latest - previous
        if delta > 0:
            change_counts["improved"] += 1
        elif delta < 0:
            change_counts["declined"] += 1
        else:
            change_counts["unchanged"] += 1

    total = len(cards)
    if total == 0 or change_counts["no_data"] == total:
        direction = "no_data"
    elif change_counts["improved"] > change_counts["declined"]:
        direction = "improving"
    elif change_counts["declined"] > change_counts["improved"]:
        direction = "declining"
    else:
        direction = "stable"

    return {
        "total_kpis": total,
        "change_counts": change_counts,
        "overall_change_direction": direction,
    }


def _build_kpi_source_mix_summary(cards: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate portfolio source composition from already-computed card source_status."""
    source_mix_counts = {
        "derived_from_events": 0,
        "derived_from_usage": 0,
        "derived_from_snapshot": 0,
        "mixed_source": 0,
        "empty": 0,
    }

    for card in cards:
        status = str(card.get("source_status") or "").strip().lower()
        if status in {"derived_from_events", "derived_from_usage", "derived_from_snapshot"}:
            source_mix_counts[status] += 1
        elif status:
            source_mix_counts["mixed_source"] += 1
        else:
            source_mix_counts["empty"] += 1

    total = len(cards)
    if total == 0:
        dominant_source_mode = "empty"
    else:
        mode_candidates = {
            "events": source_mix_counts["derived_from_events"],
            "usage": source_mix_counts["derived_from_usage"],
            "snapshot": source_mix_counts["derived_from_snapshot"],
            "mixed": source_mix_counts["mixed_source"],
        }
        top_count = max(mode_candidates.values())
        top_modes = [mode for mode, count in mode_candidates.items() if count == top_count]
        dominant_source_mode = top_modes[0] if len(top_modes) == 1 and top_count > 0 else "mixed"

    return {
        "total_kpis": total,
        "source_mix_counts": source_mix_counts,
        "dominant_source_mode": dominant_source_mode,
    }


def _build_kpi_sections_manifest(
    *,
    cards: list[dict[str, Any]],
    summary: dict[str, Any] | None,
    change_digest: dict[str, Any] | None,
    source_mix_summary: dict[str, Any] | None,
    capabilities: dict[str, Any] | None,
    surface_id: str | None,
    contract_version: str | None,
    surface_profile: dict[str, Any] | None,
    field_semantics: dict[str, Any] | None,
    card_field_semantics: dict[str, Any] | None,
    response_examples: dict[str, Any] | None,
    surface_map: dict[str, Any] | None,
    workflow_hints: dict[str, Any] | None,
    stability_tiers: dict[str, Any] | None,
    contract_fingerprint: dict[str, Any] | None,
    contract_compatibility: dict[str, Any] | None,
) -> dict[str, str]:
    """Describe section presence/content for the current KPI payload."""

    summary_total = int((summary or {}).get("total_kpis") or 0)
    change_total = int((change_digest or {}).get("total_kpis") or 0)
    source_mix_total = int((source_mix_summary or {}).get("total_kpis") or 0)

    return {
        "cards": "populated" if len(cards) > 0 else "empty",
        "summary": "populated" if summary_total > 0 else "present",
        "change_digest": "populated" if change_total > 0 else "present",
        "source_mix_summary": "populated" if source_mix_total > 0 else "present",
        "capabilities": "present" if isinstance(capabilities, dict) and len(capabilities) > 0 else "empty",
        "contract_identity": "present" if surface_id and contract_version else "empty",
        "surface_profile": "present" if isinstance(surface_profile, dict) and len(surface_profile) > 0 else "empty",
        "field_semantics": "present" if isinstance(field_semantics, dict) and len(field_semantics) > 0 else "empty",
        "card_field_semantics": "present" if isinstance(card_field_semantics, dict) and len(card_field_semantics) > 0 else "empty",
        "response_examples": "present" if isinstance(response_examples, dict) and len(response_examples) > 0 else "empty",
        "surface_map": "present" if isinstance(surface_map, dict) and len(surface_map) > 0 else "empty",
        "workflow_hints": "present" if isinstance(workflow_hints, dict) and len(workflow_hints) > 0 else "empty",
        "stability_tiers": "present" if isinstance(stability_tiers, dict) and len(stability_tiers) > 0 else "empty",
        "contract_fingerprint": "present"
        if isinstance(contract_fingerprint, dict) and len(contract_fingerprint) > 0
        else "empty",
        "contract_compatibility": "present"
        if isinstance(contract_compatibility, dict) and len(contract_compatibility) > 0
        else "empty",
        "contract_invariants": "present",
    }


def _build_insight_from_trend_row(trend: dict[str, Any]) -> dict[str, Any]:
    metric_key = str(trend.get("key") or "").strip().lower()
    title = str(trend.get("title") or metric_key)
    latest_value = int(trend.get("latest_value") or 0)
    delta_raw = trend.get("delta")
    delta = int(delta_raw) if delta_raw is not None else None
    points = list(trend.get("points") or [])

    insight_type = "no_data"
    summary = f"{title}: no recent data available."

    if metric_key == "analytics_kpi_reads_share_pct" and points:
        if latest_value >= 70:
            insight_type = "high_share"
            summary = f"{title} is high at {latest_value}% in the latest snapshot."
        elif latest_value <= 30:
            insight_type = "low_share"
            summary = f"{title} is low at {latest_value}% in the latest snapshot."
        elif delta is None or delta == 0:
            insight_type = "no_change"
            summary = f"{title} is stable at {latest_value}% across the selected window."
        elif delta > 0:
            insight_type = "growth"
            summary = f"{title} increased by {delta} points to {latest_value}%."
        else:
            insight_type = "decline"
            summary = f"{title} decreased by {abs(delta)} points to {latest_value}%."
    elif points:
        if delta is None:
            insight_type = "no_data"
            summary = f"{title} has only one snapshot in the selected window."
        elif delta > 0:
            insight_type = "growth"
            summary = f"{title} increased by {delta} in the selected window."
        elif delta < 0:
            insight_type = "decline"
            summary = f"{title} decreased by {abs(delta)} in the selected window."
        else:
            insight_type = "no_change"
            summary = f"{title} remained unchanged in the selected window."

    return {
        "key": metric_key,
        "title": title,
        "type": insight_type,
        "summary": summary,
        "value": latest_value,
        "delta": delta,
    }


def _build_recommendation_from_insight_row(insight: dict[str, Any]) -> dict[str, Any]:
    metric_key = str(insight.get("key") or "").strip().lower()
    title = str(insight.get("title") or metric_key)
    insight_type = str(insight.get("type") or "no_data").strip().lower()

    recommendation_type = "no_action"
    priority = "low"
    summary = f"No immediate action required for {title.lower()}."

    if insight_type == "decline":
        recommendation_type = "investigate_decline"
        priority = "high"
        summary = f"Investigate recent decline in {title.lower()} and identify the main contributing factor."
    elif insight_type == "growth":
        recommendation_type = "sustain_growth"
        priority = "medium"
        summary = f"Sustain momentum in {title.lower()} by reinforcing the latest effective workflow."
    elif insight_type == "no_change":
        recommendation_type = "monitor_stability"
        priority = "low"
        summary = f"Monitor {title.lower()} and keep the current operating pattern stable."
    elif insight_type == "low_share" and metric_key == "analytics_kpi_reads_share_pct":
        recommendation_type = "increase_adoption"
        priority = "medium"
        summary = "Increase KPI usage adoption to raise the KPI share of analytics reads."
    elif insight_type == "high_share" and metric_key == "analytics_kpi_reads_share_pct":
        recommendation_type = "rebalance_usage"
        priority = "medium"
        summary = "Rebalance KPI and event-level reads to keep analytics usage aligned across workflows."

    return {
        "key": metric_key,
        "title": title,
        "type": recommendation_type,
        "priority": priority,
        "summary": summary,
        "based_on": insight_type,
    }
