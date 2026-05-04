from __future__ import annotations

from uuid import uuid4

from tests.conftest import ADMIN_HEADERS, client

from app.modules.auth.token_service import create_access_token
from app.modules.billing import service as billing_service
from app.modules.tenants import service as module_tenant_service
from app.platform.event_ingestion import service as event_ingestion_service
from app.platform.kpi import service as kpi_service
from app.platform.uow import UnitOfWork


def _create_tenant(prefix: str) -> int:
    slug = f"{prefix}-{uuid4().hex[:8]}"
    tenant = module_tenant_service.create_tenant({"slug": slug, "name": f"{prefix} Tenant"})
    return int(tenant["id"])


def _analytics_read_headers(*, tenant_id: int) -> dict[str, str]:
    token = create_access_token(
        user_id=f"kpi.viewer.{tenant_id}@example.com",
        roles=["student"],
        auth_source="test",
        tenant_id=tenant_id,
        permissions=["analytics.data.read"],
    )
    return {"Authorization": f"Bearer {token}"}


def _emit_event(*, tenant_id: int, event_type: str, count: int = 1) -> None:
    for idx in range(count):
        event_ingestion_service.record_event(
            tenant_id=tenant_id,
            event_type=event_type,
            payload={"seq": idx + 1, "source": "test-a0135"},
        )


def _refresh_metrics(*, tenant_id: int) -> None:
    with UnitOfWork() as uow:
        kpi_service.refresh_tenant_metrics(tenant_id=tenant_id, uow=uow)


def _cards_by_key(body: dict) -> dict[str, dict]:
    return {str(item["key"]): item for item in body["kpis"]}


def test_wave1_dashboard_includes_student_success_metrics(reset_shared_state) -> None:
    tenant_id = _create_tenant("a0135-student-success")

    _emit_event(tenant_id=tenant_id, event_type="academic.attendance_risk.detected", count=3)
    _emit_event(tenant_id=tenant_id, event_type="academic.grade_risk.detected", count=2)
    _emit_event(tenant_id=tenant_id, event_type="interventions.case.created", count=4)
    _emit_event(tenant_id=tenant_id, event_type="interventions.case_outcome.recorded", count=2)
    _emit_event(tenant_id=tenant_id, event_type="interventions.auto_triggered", count=3)

    _refresh_metrics(tenant_id=tenant_id)

    response = client.get("/api/analytics/kpis", headers=_analytics_read_headers(tenant_id=tenant_id))
    assert response.status_code == 200, response.text
    cards = _cards_by_key(response.json())

    assert "high_risk_students_count" in cards
    assert "intervention_resolution_rate" in cards
    assert "intervention_auto_created_count" in cards


def test_wave1_dashboard_includes_delinquency_metrics(reset_shared_state) -> None:
    tenant_id = _create_tenant("a0135-delinquency")

    billing_service.create_delinquency_record(tenant_id, invoice_id="inv-1", status="overdue", amount_cents=120000)
    billing_service.create_delinquency_record(tenant_id, invoice_id="inv-2", status="collections", amount_cents=80000)
    billing_service.resolve_delinquency_record(
        tenant_id,
        1,
        resolution="paid",
        actor="a0135-test",
    )

    _refresh_metrics(tenant_id=tenant_id)

    response = client.get("/api/analytics/kpis", headers=_analytics_read_headers(tenant_id=tenant_id))
    assert response.status_code == 200, response.text
    cards = _cards_by_key(response.json())

    assert cards["delinquency_cases_active"]["value"] == 1
    assert cards["overdue_amount_at_risk"]["value"] == 80000
    assert cards["delinquency_recovery_rate"]["value"] == 50


def test_wave1_dashboard_includes_scheduling_capacity_metrics(reset_shared_state) -> None:
    tenant_id = _create_tenant("a0135-scheduling")

    _emit_event(tenant_id=tenant_id, event_type="scheduling.section.created", count=4)
    _emit_event(tenant_id=tenant_id, event_type="enrollment.created", count=3)
    _emit_event(tenant_id=tenant_id, event_type="enrollment.capacity_risk.detected", count=2)
    _emit_event(tenant_id=tenant_id, event_type="scheduling.section.conflict_detected", count=1)

    _refresh_metrics(tenant_id=tenant_id)

    response = client.get("/api/analytics/kpis", headers=_analytics_read_headers(tenant_id=tenant_id))
    assert response.status_code == 200, response.text
    cards = _cards_by_key(response.json())

    assert cards["course_fill_rate"]["value"] == 75
    assert cards["capacity_risk_sections_count"]["value"] == 2
    assert cards["scheduling_conflicts_count"]["value"] == 1


def test_wave1_source_breakdown_uses_expected_module_events(reset_shared_state) -> None:
    tenant_id = _create_tenant("a0135-breakdown")

    _emit_event(tenant_id=tenant_id, event_type="interventions.auto_triggered", count=2)

    _refresh_metrics(tenant_id=tenant_id)

    response = client.get("/api/analytics/kpis", headers=_analytics_read_headers(tenant_id=tenant_id))
    assert response.status_code == 200, response.text
    cards = _cards_by_key(response.json())

    breakdown = cards["intervention_auto_created_count"]["source_breakdown"] or []
    values = {str(item["event_type"]): int(item["count"]) for item in breakdown}
    assert values.get("interventions.auto_triggered", 0) == 2


def test_wave1_severity_and_actionability_for_high_and_critical(reset_shared_state) -> None:
    tenant_warning = _create_tenant("a0135-warning")
    tenant_critical = _create_tenant("a0135-critical")

    _emit_event(tenant_id=tenant_warning, event_type="scheduling.section.conflict_detected", count=1)
    _emit_event(tenant_id=tenant_critical, event_type="scheduling.section.conflict_detected", count=6)

    _refresh_metrics(tenant_id=tenant_warning)
    _refresh_metrics(tenant_id=tenant_critical)

    warning = client.get("/api/analytics/kpis", headers=_analytics_read_headers(tenant_id=tenant_warning))
    critical = client.get("/api/analytics/kpis", headers=_analytics_read_headers(tenant_id=tenant_critical))
    assert warning.status_code == 200, warning.text
    assert critical.status_code == 200, critical.text

    warning_card = _cards_by_key(warning.json())["scheduling_conflicts_count"]
    critical_card = _cards_by_key(critical.json())["scheduling_conflicts_count"]

    assert warning_card["severity"] == "warning"
    assert warning_card["actionability_state"] == "review"
    assert critical_card["severity"] == "critical"
    assert critical_card["actionability_state"] == "act_now"


def test_wave1_metrics_are_tenant_isolated(reset_shared_state) -> None:
    tenant_a = _create_tenant("a0135-iso-a")
    tenant_b = _create_tenant("a0135-iso-b")

    _emit_event(tenant_id=tenant_a, event_type="interventions.auto_triggered", count=4)
    _emit_event(tenant_id=tenant_b, event_type="interventions.auto_triggered", count=1)

    _refresh_metrics(tenant_id=tenant_a)
    _refresh_metrics(tenant_id=tenant_b)

    body_a = client.get("/api/analytics/kpis", headers=_analytics_read_headers(tenant_id=tenant_a)).json()
    body_b = client.get("/api/analytics/kpis", headers=_analytics_read_headers(tenant_id=tenant_b)).json()

    cards_a = _cards_by_key(body_a)
    cards_b = _cards_by_key(body_b)

    assert cards_a["intervention_auto_created_count"]["value"] == 4
    assert cards_b["intervention_auto_created_count"]["value"] == 1


def test_wave1_contract_fingerprint_stable_and_refresh_history_present(reset_shared_state) -> None:
    tenant_id = _create_tenant("a0135-fingerprint")
    rw_headers = _analytics_read_headers(tenant_id=tenant_id)
    rw_headers["Authorization"] = rw_headers["Authorization"]

    _emit_event(tenant_id=tenant_id, event_type="interventions.auto_triggered", count=1)
    _refresh_metrics(tenant_id=tenant_id)

    first = client.get("/api/analytics/kpis", headers=rw_headers)
    assert first.status_code == 200, first.text
    first_fingerprint = first.json()["contract_fingerprint"]["value"]

    # refresh-history endpoint must remain available and return contract-compliant shape
    refresh_history = client.get("/api/analytics/kpis/refresh-history", headers=rw_headers)
    assert refresh_history.status_code == 200, refresh_history.text
    assert "recent_refreshes" in refresh_history.json()

    # Admin rector dashboard remains backward-compatible and now includes wave1 keys after refresh
    dashboard = client.get(
        "/api/v1/admin/platform/kpi/dashboard",
        params={"tenant_id": tenant_id},
        headers=ADMIN_HEADERS,
    )
    assert dashboard.status_code == 200, dashboard.text
    dashboard_keys = {str(item["metric_key"]) for item in dashboard.json()["cards"]}
    assert "intervention_auto_created_count" in dashboard_keys

    second = client.get("/api/analytics/kpis", headers=rw_headers)
    assert second.status_code == 200, second.text
    second_fingerprint = second.json()["contract_fingerprint"]["value"]
    assert second_fingerprint == first_fingerprint
