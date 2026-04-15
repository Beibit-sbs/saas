from __future__ import annotations

import asyncio
from unittest.mock import MagicMock

import pytest

from app.core.module_helpers.service_validation import TenantResourceNotFoundError
from app.modules.interventions.risk_service import InterventionRiskService, RiskDetectionResult
from app.modules.observability.metrics import (
    clear_metrics_state,
    observe_playbook_execution_finished,
    observe_playbook_execution_started,
    observe_playbook_step_action,
    observe_risk_recommendation_ack,
    observe_risk_scoring_duration,
    observe_risk_scoring_job,
    render_metrics,
    set_risk_high_band_students_total,
    set_risk_latest_snapshot_age_seconds,
)


def test_render_metrics_contains_risk_observability_series() -> None:
    clear_metrics_state()
    observe_risk_scoring_job(tenant_id=1, status="success")
    observe_risk_scoring_duration(tenant_id=1, status="success", duration_seconds=0.42)
    set_risk_high_band_students_total(tenant_id=1, total=3)
    observe_risk_recommendation_ack(tenant_id=1, status="success")
    set_risk_latest_snapshot_age_seconds(tenant_id=1, age_seconds=321.0)

    metrics = render_metrics()

    assert 'risk_scoring_jobs_total{tenant_id="1",status="success"} 1' in metrics
    assert 'risk_scoring_duration_seconds_count{tenant_id="1",status="success"} 1' in metrics
    assert 'risk_high_band_students_total{tenant_id="1"} 3' in metrics
    assert 'risk_recommendation_ack_total{tenant_id="1",status="success"} 1' in metrics
    assert 'risk_latest_snapshot_age_seconds{tenant_id="1"} 321.000' in metrics


def test_recompute_scores_records_success_metrics(monkeypatch: pytest.MonkeyPatch) -> None:
    clear_metrics_state()
    service = InterventionRiskService(MagicMock())

    async def _fake_run_daily_detection(*, tenant_id: int, actor: str) -> RiskDetectionResult:
        assert tenant_id == 1
        assert actor == "owner@example.com"
        return RiskDetectionResult(
            tenant_id=tenant_id,
            thresholds_evaluated=2,
            signals_created=4,
            cases_created=1,
        )

    async def _fake_refresh(*, tenant_id: int) -> None:
        assert tenant_id == 1

    monkeypatch.setattr(service, "run_daily_detection", _fake_run_daily_detection)
    monkeypatch.setattr(service, "_refresh_observability_snapshot", _fake_refresh)

    result = asyncio.run(service.recompute_scores(tenant_id=1, actor="owner@example.com"))

    assert result.cases_created == 1
    metrics = render_metrics()
    assert 'risk_scoring_jobs_total{tenant_id="1",status="success"} 1' in metrics
    assert 'risk_scoring_duration_seconds_count{tenant_id="1",status="success"} 1' in metrics


def test_acknowledge_recommendation_records_error_metric() -> None:
    clear_metrics_state()
    db = MagicMock()
    db.execute.return_value.scalar_one_or_none.return_value = None
    service = InterventionRiskService(db)

    with pytest.raises(TenantResourceNotFoundError):
        asyncio.run(
            service.acknowledge_recommendation(
                tenant_id=1,
                recommendation_id=404,
                actor="owner@example.com",
                note="ack",
            )
        )

    metrics = render_metrics()
    assert 'risk_recommendation_ack_total{tenant_id="1",status="error"} 1' in metrics


def test_render_metrics_contains_playbook_observability_series() -> None:
    clear_metrics_state()
    observe_playbook_execution_started(tenant_id=1, triggered_by="manual")
    observe_playbook_step_action(tenant_id=1, action="completed")
    observe_playbook_execution_finished(tenant_id=1, status="completed", duration_seconds=12.5)

    metrics = render_metrics()

    assert 'playbook_executions_total{tenant_id="1",status="started",triggered_by="manual"} 1' in metrics
    assert 'playbook_executions_total{tenant_id="1",status="completed",triggered_by="-"} 1' in metrics
    assert 'playbook_execution_duration_seconds_count{tenant_id="1",status="completed"} 1' in metrics
    assert 'playbook_step_actions_total{tenant_id="1",action="completed"} 1' in metrics
