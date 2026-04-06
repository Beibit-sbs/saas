from __future__ import annotations

from collections.abc import Generator
from datetime import UTC, date, datetime
from unittest.mock import MagicMock

import pytest

from app.modules.interventions import risk_router as risk_router_module
from app.modules.interventions import router as cases_router_module
from app.modules.interventions.dependencies import get_interventions_db
from app.modules.interventions.models import (
    InterventionCaseSeverity,
    OutcomeTrackingStatus,
    RiskMetric,
    RiskSignalType,
    RiskThresholdCategory,
    RiskThresholdComparison,
)
from app.modules.interventions.risk_service import RiskDetectionResult
from app.modules.rbac import service as rbac_service
from tests.conftest import ADMIN_HEADERS, _auth_headers, _configure_db_only_role_resolution, app, client


@pytest.fixture(autouse=True)
def _enable_intervention_permissions_for_admin(monkeypatch: pytest.MonkeyPatch):
    permissions = set(rbac_service.BASELINE_ROLE_PERMISSIONS.get("admin", set()))
    permissions.update({"admin.jobs.read", "admin.jobs.write"})
    monkeypatch.setitem(rbac_service.BASELINE_ROLE_PERMISSIONS, "admin", permissions)
    _configure_db_only_role_resolution(
        monkeypatch,
        {
            "owner@example.com": ["admin"],
            "student.no.jobs@example.com": ["student"],
        },
    )


@pytest.fixture(autouse=True)
def override_interventions_db(reset_shared_state) -> Generator[MagicMock, None, None]:
    session = MagicMock()
    previous_factory = getattr(app.state, "interventions_session_factory", None)
    app.state.interventions_session_factory = lambda: session
    app.dependency_overrides[get_interventions_db] = lambda: session
    app.dependency_overrides[risk_router_module.get_interventions_db] = lambda: session
    app.dependency_overrides[cases_router_module.get_interventions_db] = lambda: session
    try:
        yield session
    finally:
        if previous_factory is None:
            delattr(app.state, "interventions_session_factory")
        else:
            app.state.interventions_session_factory = previous_factory
        app.dependency_overrides.pop(get_interventions_db, None)
        app.dependency_overrides.pop(risk_router_module.get_interventions_db, None)
        app.dependency_overrides.pop(cases_router_module.get_interventions_db, None)


@pytest.fixture
def admin_headers() -> dict[str, str]:
    return dict(ADMIN_HEADERS)


@pytest.fixture
def student_headers() -> dict[str, str]:
    return _auth_headers("student.no.jobs@example.com", ["student"])


def test_create_risk_threshold_success(
    monkeypatch: pytest.MonkeyPatch,
    admin_headers: dict[str, str],
    override_interventions_db: MagicMock,
) -> None:
    now = datetime(2026, 4, 6, 10, 0, 0, tzinfo=UTC)

    class _Threshold:
        id = 1
        tenant_id = 1
        risk_category = RiskThresholdCategory.ATTENDANCE
        rule_name = "absence_3plus"
        metric = RiskMetric.ABSENCE_COUNT
        threshold_value = 3.0
        comparison = RiskThresholdComparison.GTE
        severity_level = InterventionCaseSeverity.MEDIUM
        signal_type = RiskSignalType.ATTENDANCE_RISK
        enabled = True
        auto_create_case = True
        window_days = 30
        escalate_to_refs_json = ["faculty_advisor"]
        created_at = now
        updated_at = now

    async def _fake_create_threshold(self, tenant_id: int, request):
        assert tenant_id == 1
        assert request.rule_name == "absence_3plus"
        return _Threshold()

    monkeypatch.setattr(
        "app.modules.interventions.risk_service.InterventionRiskService.create_threshold",
        _fake_create_threshold,
    )

    response = client.post(
        "/api/admin/interventions/risk/thresholds",
        headers=admin_headers,
        json={
            "risk_category": "attendance",
            "rule_name": "absence_3plus",
            "metric": "absence_count",
            "threshold_value": 3,
            "comparison": "gte",
            "severity_level": "medium",
            "signal_type": "attendance_risk",
            "enabled": True,
            "auto_create_case": True,
            "window_days": 30,
            "escalate_to_refs_json": ["faculty_advisor"],
        },
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["rule_name"] == "absence_3plus"
    assert body["metric"] == "absence_count"


def test_run_risk_detection_success(
    monkeypatch: pytest.MonkeyPatch,
    admin_headers: dict[str, str],
    override_interventions_db: MagicMock,
) -> None:
    async def _fake_run_daily_detection(self, tenant_id: int, actor: str):
        assert tenant_id == 1
        assert actor == "owner@example.com"
        return RiskDetectionResult(
            tenant_id=1,
            thresholds_evaluated=2,
            signals_created=3,
            cases_created=1,
        )

    monkeypatch.setattr(
        "app.modules.interventions.risk_service.InterventionRiskService.run_daily_detection",
        _fake_run_daily_detection,
    )

    response = client.post("/api/admin/interventions/risk/run-detection", headers=admin_headers)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["thresholds_evaluated"] == 2
    assert body["signals_created"] == 3


def test_get_kpi_summary_success(
    monkeypatch: pytest.MonkeyPatch,
    admin_headers: dict[str, str],
    override_interventions_db: MagicMock,
) -> None:
    async def _fake_get_kpi_summary(self, tenant_id: int):
        assert tenant_id == 1
        return {
            "tenant_id": 1,
            "open_cases_total": 4,
            "signals_last_24h": 7,
            "auto_created_cases_last_24h": 2,
            "severity_breakdown": {"low": 1, "medium": 4, "high": 2},
        }

    monkeypatch.setattr(
        "app.modules.interventions.risk_service.InterventionRiskService.get_kpi_summary",
        _fake_get_kpi_summary,
    )

    response = client.get("/api/admin/interventions/risk/kpi-summary", headers=admin_headers)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["open_cases_total"] == 4
    assert body["severity_breakdown"]["high"] == 2


def test_risk_threshold_write_requires_permission(student_headers: dict[str, str]) -> None:
    response = client.post(
        "/api/admin/interventions/risk/thresholds",
        headers=student_headers,
        json={
            "risk_category": "attendance",
            "rule_name": "absence_3plus",
            "metric": "absence_count",
            "threshold_value": 3,
            "comparison": "gte",
            "severity_level": "medium",
            "signal_type": "attendance_risk",
        },
    )

    assert response.status_code == 403, response.text


def test_upsert_outcome_success(
    monkeypatch: pytest.MonkeyPatch,
    admin_headers: dict[str, str],
    override_interventions_db: MagicMock,
) -> None:
    now = datetime(2026, 4, 6, 10, 0, 0, tzinfo=UTC)

    class _Outcome:
        id = 10
        tenant_id = 1
        case_id = 100
        baseline_risk_score = 72.0
        current_risk_score = 58.0
        outcome = "improved"
        improvement_date = date(2026, 4, 6)
        measurement_notes = "Attendance stabilized"
        outcome_notes = None
        created_at = now
        updated_at = now

    async def _fake_upsert_outcome(self, tenant_id: int, case_id: int, request):
        assert tenant_id == 1
        assert case_id == 100
        assert request.outcome == OutcomeTrackingStatus.IMPROVED
        return _Outcome()

    monkeypatch.setattr(
        "app.modules.interventions.risk_service.InterventionRiskService.upsert_outcome",
        _fake_upsert_outcome,
    )

    response = client.put(
        "/api/admin/interventions/risk/outcomes/100",
        headers=admin_headers,
        json={
            "baseline_risk_score": 72,
            "current_risk_score": 58,
            "outcome": "improved",
            "improvement_date": "2026-04-06",
            "measurement_notes": "Attendance stabilized",
        },
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["case_id"] == 100
    assert body["outcome"] == "improved"
