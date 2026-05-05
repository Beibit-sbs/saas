"""A-014.6 Wave 2 KPI backend tests.

Covers:
- All Wave 2 metric keys are present after refresh_tenant_metrics()
- Correct event-derived computation for each domain group
- Zero-value metrics do not crash (no events = 0 values)
- Severity rules are defined for all Wave 2 metric keys
- METRIC_TITLES are defined for all Wave 2 metric keys
"""
from __future__ import annotations

from uuid import uuid4

from tests.conftest import ADMIN_HEADERS, client

from app.modules.auth.token_service import create_access_token
from app.modules.tenants import service as module_tenant_service
from app.platform.event_ingestion import service as event_ingestion_service
from app.platform.kpi import service as kpi_service
from app.platform.uow import UnitOfWork

WAVE2_METRIC_KEYS = {
    "grade_decline_risk_count",
    "grade_intervention_cases_count",
    "thesis_completion_risk_count",
    "thesis_intervention_cases_count",
    "attendance_recovery_actions_count",
    "graduation_risk_students_count",
    "degree_progress_intervention_cases_count",
    "scholarship_risk_cases_count",
    "financial_aid_risk_cases_count",
}


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
            payload={"seq": idx + 1, "source": "test-a0146"},
        )


def _refresh_metrics(*, tenant_id: int) -> None:
    with UnitOfWork() as uow:
        kpi_service.refresh_tenant_metrics(tenant_id=tenant_id, uow=uow)


def _cards_by_key(body: dict) -> dict[str, dict]:
    return {str(item["key"]): item for item in body["kpis"]}


def test_wave2_metric_titles_defined_for_all_keys() -> None:
    """All Wave 2 metric keys must have display titles in METRIC_TITLES."""
    for key in WAVE2_METRIC_KEYS:
        assert key in kpi_service.METRIC_TITLES, f"METRIC_TITLES missing entry for '{key}'"
        assert kpi_service.METRIC_TITLES[key], f"METRIC_TITLES['{key}'] must be non-empty"


def test_wave2_event_lineage_defined_for_all_keys() -> None:
    """All Wave 2 metric keys must have event lineage in EVENT_DERIVED_METRIC_LINEAGE."""
    for key in WAVE2_METRIC_KEYS:
        assert key in kpi_service.EVENT_DERIVED_METRIC_LINEAGE, (
            f"EVENT_DERIVED_METRIC_LINEAGE missing entry for '{key}'"
        )
        assert len(kpi_service.EVENT_DERIVED_METRIC_LINEAGE[key]) > 0, (
            f"EVENT_DERIVED_METRIC_LINEAGE['{key}'] must list at least one event type"
        )


def test_wave2_severity_rules_defined_for_all_keys() -> None:
    """All Wave 2 metric keys must have severity threshold rules in KPI_SEVERITY_RULES."""
    for key in WAVE2_METRIC_KEYS:
        assert key in kpi_service.KPI_SEVERITY_RULES, f"KPI_SEVERITY_RULES missing entry for '{key}'"
        rule = kpi_service.KPI_SEVERITY_RULES[key]
        assert "basis" in rule, f"KPI_SEVERITY_RULES['{key}'] must have 'basis'"
        assert "policy_pack" in rule, f"KPI_SEVERITY_RULES['{key}'] must have 'policy_pack'"


def test_wave2_all_keys_present_after_refresh_zero_events(reset_shared_state) -> None:
    """refresh_tenant_metrics() returns all Wave 2 keys even when no relevant events exist."""
    tenant_id = _create_tenant("a0146-zero")

    _refresh_metrics(tenant_id=tenant_id)

    response = client.get("/api/analytics/kpis", headers=_analytics_read_headers(tenant_id=tenant_id))
    assert response.status_code == 200, response.text
    cards = _cards_by_key(response.json())

    for key in WAVE2_METRIC_KEYS:
        assert key in cards, f"KPI card missing for '{key}' when no events emitted"
        assert cards[key]["value"] == 0, f"Expected 0 for '{key}' with no events, got {cards[key]['value']}"


def test_wave2_grade_decline_risk_derived_from_grade_risk_event(reset_shared_state) -> None:
    """grade_decline_risk_count reflects academic.grade_risk.detected event count."""
    tenant_id = _create_tenant("a0146-grade")

    _emit_event(tenant_id=tenant_id, event_type="academic.grade_risk.detected", count=5)
    _refresh_metrics(tenant_id=tenant_id)

    response = client.get("/api/analytics/kpis", headers=_analytics_read_headers(tenant_id=tenant_id))
    assert response.status_code == 200, response.text
    cards = _cards_by_key(response.json())

    assert cards["grade_decline_risk_count"]["value"] == 5


def test_wave2_graduation_risk_derived_from_degree_progress_event(reset_shared_state) -> None:
    """graduation_risk_students_count reflects degree_progress.graduation_risk.detected count."""
    tenant_id = _create_tenant("a0146-graduation")

    _emit_event(tenant_id=tenant_id, event_type="degree_progress.graduation_risk.detected", count=3)
    _refresh_metrics(tenant_id=tenant_id)

    response = client.get("/api/analytics/kpis", headers=_analytics_read_headers(tenant_id=tenant_id))
    assert response.status_code == 200, response.text
    cards = _cards_by_key(response.json())

    assert cards["graduation_risk_students_count"]["value"] == 3


def test_wave2_scholarship_risk_derived_from_scholarship_event(reset_shared_state) -> None:
    """scholarship_risk_cases_count reflects scholarship.award.at_risk_detected count."""
    tenant_id = _create_tenant("a0146-scholarship")

    _emit_event(tenant_id=tenant_id, event_type="scholarship.award.at_risk_detected", count=2)
    _refresh_metrics(tenant_id=tenant_id)

    response = client.get("/api/analytics/kpis", headers=_analytics_read_headers(tenant_id=tenant_id))
    assert response.status_code == 200, response.text
    cards = _cards_by_key(response.json())

    assert cards["scholarship_risk_cases_count"]["value"] == 2


def test_wave2_financial_aid_risk_derived_from_financial_aid_event(reset_shared_state) -> None:
    """financial_aid_risk_cases_count reflects financial_aid.warning.detected count."""
    tenant_id = _create_tenant("a0146-finaid")

    _emit_event(tenant_id=tenant_id, event_type="financial_aid.warning.detected", count=4)
    _refresh_metrics(tenant_id=tenant_id)

    response = client.get("/api/analytics/kpis", headers=_analytics_read_headers(tenant_id=tenant_id))
    assert response.status_code == 200, response.text
    cards = _cards_by_key(response.json())

    assert cards["financial_aid_risk_cases_count"]["value"] == 4


def test_wave2_thesis_completion_risk_derived_from_thesis_event(reset_shared_state) -> None:
    """thesis_completion_risk_count reflects thesis.status_changed count."""
    tenant_id = _create_tenant("a0146-thesis")

    _emit_event(tenant_id=tenant_id, event_type="thesis.status_changed", count=2)
    _refresh_metrics(tenant_id=tenant_id)

    response = client.get("/api/analytics/kpis", headers=_analytics_read_headers(tenant_id=tenant_id))
    assert response.status_code == 200, response.text
    cards = _cards_by_key(response.json())

    assert cards["thesis_completion_risk_count"]["value"] == 2


def test_wave2_attendance_recovery_derived_from_attendance_risk_event(reset_shared_state) -> None:
    """attendance_recovery_actions_count reflects academic.attendance_risk.detected count."""
    tenant_id = _create_tenant("a0146-attendance")

    _emit_event(tenant_id=tenant_id, event_type="academic.attendance_risk.detected", count=6)
    _refresh_metrics(tenant_id=tenant_id)

    response = client.get("/api/analytics/kpis", headers=_analytics_read_headers(tenant_id=tenant_id))
    assert response.status_code == 200, response.text
    cards = _cards_by_key(response.json())

    assert cards["attendance_recovery_actions_count"]["value"] == 6


def test_wave2_grade_intervention_cases_count_from_interventions_created(reset_shared_state) -> None:
    """grade_intervention_cases_count reflects interventions.case.created count."""
    tenant_id = _create_tenant("a0146-grade-iv")

    _emit_event(tenant_id=tenant_id, event_type="interventions.case.created", count=7)
    _refresh_metrics(tenant_id=tenant_id)

    response = client.get("/api/analytics/kpis", headers=_analytics_read_headers(tenant_id=tenant_id))
    assert response.status_code == 200, response.text
    cards = _cards_by_key(response.json())

    # grade_intervention_cases_count, thesis_intervention_cases_count, and
    # degree_progress_intervention_cases_count all use intervention_created count.
    assert cards["grade_intervention_cases_count"]["value"] == 7
    assert cards["thesis_intervention_cases_count"]["value"] == 7
    assert cards["degree_progress_intervention_cases_count"]["value"] == 7
