from __future__ import annotations

from uuid import uuid4

from app.modules.tenants import service as module_tenant_service
from app.platform.event_ingestion import service as event_ingestion_service
from app.platform.kpi import service as kpi_service
from app.platform.uow import UnitOfWork


def _create_tenant(prefix: str) -> int:
    slug = f"{prefix}-{uuid4().hex[:8]}"
    tenant = module_tenant_service.create_tenant({"slug": slug, "name": f"{prefix} Tenant"})
    return int(tenant["id"])


def _emit_many(*, tenant_id: int, event_type: str, count: int, base_id: int) -> None:
    for index in range(count):
        event_ingestion_service.record_event(
            tenant_id=tenant_id,
            event_type=event_type,
            payload={"id": base_id + index, "source": "test-a0196"},
        )


def _refresh_values(*, tenant_id: int) -> dict[str, int]:
    with UnitOfWork() as uow:
        rows = kpi_service.refresh_tenant_metrics(tenant_id=tenant_id, uow=uow)
    return {str(item["metric_key"]): int(item["metric_value"]) for item in rows}


def test_a0196_tenant_scoped_security_visitor_access_kpis(reset_shared_state) -> None:
    tenant_id = _create_tenant("a0196-scope")

    _emit_many(tenant_id=tenant_id, event_type="visitor.registered", count=5, base_id=10_000)
    _emit_many(tenant_id=tenant_id, event_type="visitor.checked_in", count=3, base_id=11_000)
    _emit_many(tenant_id=tenant_id, event_type="visitor.unauthorized_attempt", count=2, base_id=12_000)
    _emit_many(tenant_id=tenant_id, event_type="visitor.checked_out", count=4, base_id=13_000)
    _emit_many(tenant_id=tenant_id, event_type="visitor.cancelled", count=1, base_id=14_000)

    _emit_many(tenant_id=tenant_id, event_type="access.denied", count=6, base_id=15_000)
    _emit_many(tenant_id=tenant_id, event_type="security.anomaly", count=2, base_id=16_000)
    _emit_many(tenant_id=tenant_id, event_type="card.issued", count=7, base_id=17_000)
    _emit_many(tenant_id=tenant_id, event_type="card.reactivated", count=1, base_id=18_000)
    _emit_many(tenant_id=tenant_id, event_type="card.suspended", count=3, base_id=19_000)

    _emit_many(tenant_id=tenant_id, event_type="security.incident.opened", count=4, base_id=20_000)
    _emit_many(tenant_id=tenant_id, event_type="security.incident.escalated", count=2, base_id=21_000)
    _emit_many(tenant_id=tenant_id, event_type="security.incident.resolved", count=3, base_id=22_000)

    values = _refresh_values(tenant_id=tenant_id)

    assert values["visitor_requests_pending_count"] == 5
    assert values["visitors_checked_in_count"] == 3
    assert values["visitor_unauthorized_attempts_count"] == 2
    assert values["visitor_visits_completed_count"] == 4
    assert values["visitor_visits_cancelled_count"] == 1

    assert values["access_denied_count"] == 6
    assert values["unauthorized_attempts_count"] == 8
    assert values["active_access_cards_count"] == 8
    assert values["suspended_access_cards_count"] == 3
    assert values["security_access_anomaly_count"] == 2

    assert values["security_incidents_open_count"] == 4
    assert values["security_incidents_escalated_count"] == 2
    assert values["security_incidents_resolved_count"] == 3
    assert values["security_incident_review_required_count"] == 4
    assert values["security_high_risk_incidents_count"] == 2


def test_a0196_cross_tenant_isolation_for_security_visitor_access_kpis(reset_shared_state) -> None:
    tenant_a = _create_tenant("a0196-tenant-a")
    tenant_b = _create_tenant("a0196-tenant-b")

    _emit_many(tenant_id=tenant_a, event_type="visitor.checked_out", count=5, base_id=30_000)
    _emit_many(tenant_id=tenant_a, event_type="security.incident.resolved", count=2, base_id=31_000)
    _emit_many(tenant_id=tenant_a, event_type="access.denied", count=4, base_id=32_000)

    _emit_many(tenant_id=tenant_b, event_type="visitor.checked_out", count=1, base_id=40_000)
    _emit_many(tenant_id=tenant_b, event_type="security.incident.resolved", count=7, base_id=41_000)
    _emit_many(tenant_id=tenant_b, event_type="access.denied", count=2, base_id=42_000)

    values_a = _refresh_values(tenant_id=tenant_a)
    values_b = _refresh_values(tenant_id=tenant_b)

    assert values_a["visitor_visits_completed_count"] == 5
    assert values_b["visitor_visits_completed_count"] == 1

    assert values_a["security_incidents_resolved_count"] == 2
    assert values_b["security_incidents_resolved_count"] == 7

    assert values_a["access_denied_count"] == 4
    assert values_b["access_denied_count"] == 2


def test_a0196_missing_optional_metrics_default_safely(reset_shared_state) -> None:
    tenant_id = _create_tenant("a0196-defaults")
    values = _refresh_values(tenant_id=tenant_id)

    assert values["visitor_visits_completed_count"] == 0
    assert values["visitor_visits_cancelled_count"] == 0
    assert values["security_incidents_resolved_count"] == 0
    assert values["security_incident_review_required_count"] == 0
    assert values["security_high_risk_incidents_count"] == 0


def test_a0196_lineage_for_target_metrics_is_deterministic() -> None:
    expected = {
        "security_high_risk_incidents_count": ["security.incident.escalated"],
        "visitor_visits_completed_count": ["visitor.checked_out"],
        "visitor_visits_cancelled_count": ["visitor.cancelled"],
        "access_denied_count": ["access.denied"],
        "security_access_anomaly_count": ["security.anomaly"],
    }
    for metric_key, lineage in expected.items():
        assert kpi_service.EVENT_DERIVED_METRIC_LINEAGE.get(metric_key) == lineage


def test_a0196_no_duplicate_security_visitor_access_metric_keys() -> None:
    keys = [
        "visitor_requests_pending_count",
        "visitors_checked_in_count",
        "visitor_unauthorized_attempts_count",
        "visitor_visits_completed_count",
        "visitor_visits_cancelled_count",
        "access_denied_count",
        "unauthorized_attempts_count",
        "active_access_cards_count",
        "suspended_access_cards_count",
        "security_access_anomaly_count",
        "security_incidents_open_count",
        "security_incidents_escalated_count",
        "security_incidents_resolved_count",
        "security_incident_review_required_count",
        "security_high_risk_incidents_count",
    ]
    assert len(keys) == len(set(keys))


def test_a0196_kpi_policy_contract_consistency() -> None:
    metric_titles = kpi_service.METRIC_TITLES
    lineage = kpi_service.EVENT_DERIVED_METRIC_LINEAGE

    for key in [
        "visitor_requests_pending_count",
        "visitors_checked_in_count",
        "visitor_unauthorized_attempts_count",
        "visitor_visits_completed_count",
        "visitor_visits_cancelled_count",
        "access_denied_count",
        "unauthorized_attempts_count",
        "active_access_cards_count",
        "suspended_access_cards_count",
        "security_access_anomaly_count",
        "security_incidents_open_count",
        "security_incidents_escalated_count",
        "security_incidents_resolved_count",
        "security_incident_review_required_count",
        "security_high_risk_incidents_count",
    ]:
        assert key in metric_titles
        assert key in lineage
        assert isinstance(metric_titles[key], str)
        assert metric_titles[key].strip()

    # Policy contract: metrics may be thresholded (present in severity rules)
    # or non-thresholded (absent from severity rules) depending on KPI semantics.
    rules = kpi_service.KPI_SEVERITY_RULES
    for key in [
        "security_incidents_open_count",
        "security_incidents_escalated_count",
        "security_incidents_resolved_count",
        "security_incident_review_required_count",
        "security_high_risk_incidents_count",
    ]:
        if key in rules:
            assert rules[key].get("basis") in {"count", "ratio", "score"}
