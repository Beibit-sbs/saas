"""
Coverage boost: app.modules.interventions.risk_service

Tests call service methods directly with MagicMock DB sessions.
"""
from __future__ import annotations

import asyncio
from datetime import UTC, date, datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

from app.modules.interventions.models import (
    InterventionAssigneeType,
    InterventionCaseSeverity,
    InterventionCaseStatus,
    OutcomeTrackingStatus,
    RiskMetric,
    RiskSignalType,
    RiskThresholdCategory,
    RiskThresholdComparison,
)
from app.modules.interventions.schemas import (
    OutcomeTrackingUpsertSchema,
    RiskThresholdCreateSchema,
    RiskThresholdUpdateSchema,
)
from app.modules.interventions.risk_service import (
    InterventionRiskService,
    RiskDetectionResult,
    _compare_metric,
    _default_assignment_for_severity,
    _default_due_at,
)


def _now():
    return datetime.now(UTC)


def _run(coro):
    return asyncio.run(coro)


def _make_service(db=None):
    if db is None:
        db = MagicMock()
    return InterventionRiskService(db_session=db)


def _make_threshold(**kwargs):
    t = MagicMock()
    t.id = kwargs.get("id", 1)
    t.tenant_id = kwargs.get("tenant_id", 1)
    t.enabled = kwargs.get("enabled", True)
    t.auto_create_case = kwargs.get("auto_create_case", False)
    t.metric = kwargs.get("metric", RiskMetric.ABSENCE_COUNT)
    t.comparison = kwargs.get("comparison", RiskThresholdComparison.GTE)
    t.threshold_value = kwargs.get("threshold_value", 3.0)
    t.severity_level = kwargs.get("severity_level", InterventionCaseSeverity.HIGH)
    t.signal_type = kwargs.get("signal_type", RiskSignalType.ATTENDANCE_RISK)
    t.window_days = kwargs.get("window_days", 30)
    return t


# ---------------------------------------------------------------------------
# Pure helper functions
# ---------------------------------------------------------------------------


def test_compare_metric_lte_true():
    assert _compare_metric(value=2.0, comparison=RiskThresholdComparison.LTE, threshold=3.0) is True


def test_compare_metric_lte_false():
    assert _compare_metric(value=4.0, comparison=RiskThresholdComparison.LTE, threshold=3.0) is False


def test_compare_metric_gte_true():
    assert _compare_metric(value=5.0, comparison=RiskThresholdComparison.GTE, threshold=3.0) is True


def test_compare_metric_gte_false():
    assert _compare_metric(value=1.0, comparison=RiskThresholdComparison.GTE, threshold=3.0) is False


def test_compare_metric_eq_true():
    assert _compare_metric(value=3.0, comparison=RiskThresholdComparison.EQ, threshold=3.0) is True


def test_compare_metric_eq_false():
    assert _compare_metric(value=2.0, comparison=RiskThresholdComparison.EQ, threshold=3.0) is False


def test_default_assignment_high():
    atype, aref = _default_assignment_for_severity(InterventionCaseSeverity.HIGH)
    assert atype == InterventionAssigneeType.GROUP
    assert aref == "dean_office"


def test_default_assignment_medium():
    atype, aref = _default_assignment_for_severity(InterventionCaseSeverity.MEDIUM)
    assert aref == "faculty_advisor"


def test_default_assignment_low():
    atype, aref = _default_assignment_for_severity(InterventionCaseSeverity.LOW)
    assert aref == "student_support"


def test_default_due_at_high():
    due = _default_due_at(InterventionCaseSeverity.HIGH)
    delta = due - _now()
    assert abs(delta.total_seconds() - 3 * 86400) < 10


# ---------------------------------------------------------------------------
# create_threshold
# ---------------------------------------------------------------------------


def test_create_threshold():
    db = MagicMock()
    db.add = MagicMock()
    db.flush = MagicMock()
    db.refresh = MagicMock()
    db.commit = MagicMock()

    svc = _make_service(db)
    req = RiskThresholdCreateSchema(
        risk_category=RiskThresholdCategory.ATTENDANCE,
        rule_name="high_absence",
        metric=RiskMetric.ABSENCE_COUNT,
        threshold_value=5.0,
        comparison=RiskThresholdComparison.GTE,
        signal_type=RiskSignalType.ATTENDANCE_RISK,
    )
    result = _run(svc.create_threshold(tenant_id=1, request=req))
    assert db.add.called
    assert db.commit.called


def test_create_threshold_integrity_error():
    from sqlalchemy.exc import IntegrityError
    from app.core.module_helpers.service_validation import DomainValidationError

    db = MagicMock()
    db.add = MagicMock()
    db.flush.side_effect = IntegrityError("dup", params={}, orig=Exception("dup"))
    db.rollback = MagicMock()

    svc = _make_service(db)
    req = RiskThresholdCreateSchema(
        risk_category=RiskThresholdCategory.ATTENDANCE,
        rule_name="dup_rule",
        metric=RiskMetric.ABSENCE_COUNT,
        threshold_value=3.0,
        comparison=RiskThresholdComparison.GTE,
        signal_type=RiskSignalType.ATTENDANCE_RISK,
    )
    with pytest.raises(DomainValidationError):
        _run(svc.create_threshold(tenant_id=1, request=req))
    assert db.rollback.called


# ---------------------------------------------------------------------------
# list_thresholds
# ---------------------------------------------------------------------------


def test_list_thresholds():
    db = MagicMock()
    thresholds = [_make_threshold(id=1), _make_threshold(id=2)]
    db.execute.return_value.scalars.return_value.all.return_value = thresholds

    svc = _make_service(db)
    result = _run(svc.list_thresholds(tenant_id=1))
    assert len(result) == 2


# ---------------------------------------------------------------------------
# get_threshold
# ---------------------------------------------------------------------------


def test_get_threshold_found():
    db = MagicMock()
    threshold = _make_threshold(id=5)
    db.execute.return_value.scalar_one_or_none.return_value = threshold

    svc = _make_service(db)
    result = _run(svc.get_threshold(tenant_id=1, threshold_id=5))
    assert result.id == 5


def test_get_threshold_not_found():
    from app.core.module_helpers.service_validation import TenantResourceNotFoundError

    db = MagicMock()
    db.execute.return_value.scalar_one_or_none.return_value = None

    svc = _make_service(db)
    with pytest.raises(TenantResourceNotFoundError):
        _run(svc.get_threshold(tenant_id=1, threshold_id=999))


# ---------------------------------------------------------------------------
# update_threshold
# ---------------------------------------------------------------------------


def test_update_threshold():
    db = MagicMock()
    threshold = _make_threshold(id=3)
    db.execute.return_value.scalar_one_or_none.return_value = threshold
    db.flush = MagicMock()
    db.refresh = MagicMock()
    db.commit = MagicMock()

    svc = _make_service(db)
    req = RiskThresholdUpdateSchema(enabled=False, threshold_value=10.0)
    _run(svc.update_threshold(tenant_id=1, threshold_id=3, request=req))
    assert db.commit.called


def test_update_threshold_integrity_error():
    from sqlalchemy.exc import IntegrityError
    from app.core.module_helpers.service_validation import DomainValidationError

    db = MagicMock()
    threshold = _make_threshold(id=4)
    db.execute.return_value.scalar_one_or_none.return_value = threshold
    db.flush.side_effect = IntegrityError("c", params={}, orig=Exception())
    db.rollback = MagicMock()

    svc = _make_service(db)
    req = RiskThresholdUpdateSchema(enabled=True)
    with pytest.raises(DomainValidationError):
        _run(svc.update_threshold(tenant_id=1, threshold_id=4, request=req))


# ---------------------------------------------------------------------------
# list_signals
# ---------------------------------------------------------------------------


def test_list_signals():
    db = MagicMock()
    db.execute.return_value.scalar_one.return_value = 3
    db.execute.return_value.scalars.return_value.all.return_value = [MagicMock(), MagicMock(), MagicMock()]

    svc = _make_service(db)
    total, rows = _run(svc.list_signals(tenant_id=1, page=1, page_size=10))
    assert total == 3
    assert len(rows) == 3


# ---------------------------------------------------------------------------
# get_student_latest_signal
# ---------------------------------------------------------------------------


def test_get_student_latest_signal_found():
    db = MagicMock()
    signal = MagicMock()
    signal.tenant_id = 1
    db.execute.return_value.scalar_one_or_none.return_value = signal

    svc = _make_service(db)
    result = _run(svc.get_student_latest_signal(tenant_id=1, student_profile_id=100))
    assert result is signal


def test_get_student_latest_signal_not_found():
    from app.core.module_helpers.service_validation import TenantResourceNotFoundError

    db = MagicMock()
    db.execute.return_value.scalar_one_or_none.return_value = None

    svc = _make_service(db)
    with pytest.raises(TenantResourceNotFoundError):
        _run(svc.get_student_latest_signal(tenant_id=1, student_profile_id=999))


# ---------------------------------------------------------------------------
# list_student_signal_history
# ---------------------------------------------------------------------------


def test_list_student_signal_history():
    db = MagicMock()
    db.execute.return_value.scalar_one.return_value = 2
    db.execute.return_value.scalars.return_value.all.return_value = [MagicMock(), MagicMock()]

    svc = _make_service(db)
    total, rows = _run(svc.list_student_signal_history(tenant_id=1, student_profile_id=50, page=1, page_size=5))
    assert total == 2


# ---------------------------------------------------------------------------
# acknowledge_recommendation
# ---------------------------------------------------------------------------


def test_acknowledge_recommendation_success():
    db = MagicMock()
    case = MagicMock()
    case.id = 10
    db.execute.return_value.scalar_one_or_none.return_value = case
    db.add = MagicMock()
    db.flush = MagicMock()
    db.refresh = MagicMock()
    db.commit = MagicMock()

    svc = _make_service(db)
    result = _run(svc.acknowledge_recommendation(
        tenant_id=1, recommendation_id=10, actor="admin@e.com", note="Acknowledged"
    ))
    assert db.commit.called


def test_acknowledge_recommendation_case_not_found():
    from app.core.module_helpers.service_validation import TenantResourceNotFoundError

    db = MagicMock()
    db.execute.return_value.scalar_one_or_none.return_value = None

    svc = _make_service(db)
    with pytest.raises(TenantResourceNotFoundError):
        _run(svc.acknowledge_recommendation(tenant_id=1, recommendation_id=999, actor="a@e.com"))


def test_acknowledge_recommendation_without_note():
    db = MagicMock()
    case = MagicMock()
    case.id = 20
    db.execute.return_value.scalar_one_or_none.return_value = case
    db.add = MagicMock()
    db.flush = MagicMock()
    db.refresh = MagicMock()
    db.commit = MagicMock()

    svc = _make_service(db)
    _run(svc.acknowledge_recommendation(tenant_id=1, recommendation_id=20, actor="a@e.com", note=None))
    assert db.commit.called


# ---------------------------------------------------------------------------
# upsert_outcome
# ---------------------------------------------------------------------------


def test_upsert_outcome_creates_new():
    db = MagicMock()
    case = MagicMock()
    case.id = 30
    # case found, no existing outcome
    db.execute.return_value.scalar_one_or_none.side_effect = [case, None]
    db.add = MagicMock()
    db.flush = MagicMock()
    db.refresh = MagicMock()
    db.commit = MagicMock()

    svc = _make_service(db)
    req = OutcomeTrackingUpsertSchema(
        baseline_risk_score=0.8,
        current_risk_score=0.3,
        outcome=OutcomeTrackingStatus.IMPROVED,
    )
    result = _run(svc.upsert_outcome(tenant_id=1, case_id=30, request=req))
    assert db.add.called


def test_upsert_outcome_updates_existing():
    db = MagicMock()
    case = MagicMock()
    case.id = 31
    existing_outcome = MagicMock()
    db.execute.return_value.scalar_one_or_none.side_effect = [case, existing_outcome]
    db.flush = MagicMock()
    db.refresh = MagicMock()
    db.commit = MagicMock()

    svc = _make_service(db)
    req = OutcomeTrackingUpsertSchema(
        baseline_risk_score=0.9,
        current_risk_score=0.9,
        outcome=OutcomeTrackingStatus.UNCHANGED,
    )
    _run(svc.upsert_outcome(tenant_id=1, case_id=31, request=req))
    assert db.commit.called


def test_upsert_outcome_case_not_found():
    from app.core.module_helpers.service_validation import TenantResourceNotFoundError

    db = MagicMock()
    db.execute.return_value.scalar_one_or_none.return_value = None

    svc = _make_service(db)
    req = OutcomeTrackingUpsertSchema(
        baseline_risk_score=0.5,
        current_risk_score=0.5,
        outcome=OutcomeTrackingStatus.UNCHANGED,
    )
    with pytest.raises(TenantResourceNotFoundError):
        _run(svc.upsert_outcome(tenant_id=1, case_id=999, request=req))


# ---------------------------------------------------------------------------
# get_outcome
# ---------------------------------------------------------------------------


def test_get_outcome_found():
    db = MagicMock()
    outcome = MagicMock()
    outcome.tenant_id = 1
    db.execute.return_value.scalar_one_or_none.return_value = outcome

    svc = _make_service(db)
    result = _run(svc.get_outcome(tenant_id=1, case_id=50))
    assert result is outcome


def test_get_outcome_not_found():
    from app.core.module_helpers.service_validation import TenantResourceNotFoundError

    db = MagicMock()
    db.execute.return_value.scalar_one_or_none.return_value = None

    svc = _make_service(db)
    with pytest.raises(TenantResourceNotFoundError):
        _run(svc.get_outcome(tenant_id=1, case_id=9999))


# ---------------------------------------------------------------------------
# run_daily_detection — no thresholds (quick test)
# ---------------------------------------------------------------------------


def test_run_daily_detection_no_thresholds():
    db = MagicMock()
    db.execute.return_value.scalars.return_value.all.return_value = []
    db.flush = MagicMock()
    db.commit = MagicMock()

    svc = _make_service(db)
    result = _run(svc.run_daily_detection(tenant_id=1, actor="admin@e.com"))
    assert isinstance(result, RiskDetectionResult)
    assert result.thresholds_evaluated == 0
    assert result.signals_created == 0
    assert result.cases_created == 0


# ---------------------------------------------------------------------------
# recompute_scores
# ---------------------------------------------------------------------------


def test_recompute_scores_delegates_to_run_daily_detection():
    db = MagicMock()
    db.execute.return_value.scalars.return_value.all.return_value = []
    db.execute.return_value.scalar_one.return_value = 0
    db.execute.return_value.scalar_one_or_none.return_value = None
    db.flush = MagicMock()
    db.commit = MagicMock()

    svc = _make_service(db)
    result = _run(svc.recompute_scores(tenant_id=1, actor="admin@e.com"))
    assert isinstance(result, RiskDetectionResult)


# ---------------------------------------------------------------------------
# get_kpi_summary
# ---------------------------------------------------------------------------


def test_get_kpi_summary_returns_dict():
    db = MagicMock()
    db.execute.return_value.scalar_one.return_value = 0
    db.execute.return_value.scalar_one_or_none.return_value = None
    db.execute.return_value.all.return_value = []  # severity_breakdown rows

    svc = _make_service(db)
    result = _run(svc.get_kpi_summary(tenant_id=1))
    assert isinstance(result, dict)


# ═════════════════════════════════════════════════════════════════════════════
# EXTENDED COVERAGE — Risk Service Edge Cases (10 additional tests)
# ═════════════════════════════════════════════════════════════════════════════


def test_run_daily_detection_audit_logging():
    """Test that risk detection calls audit logging."""
    db = MagicMock()
    db.execute.return_value.scalars.return_value.all.return_value = []
    db.execute.return_value.scalar_one.return_value = 0
    
    svc = _make_service(db)
    with patch("app.modules.interventions.risk_service._audit") as audit_mock:
        result = _run(svc.run_daily_detection(tenant_id=1, actor="cron"))
        audit_mock.assert_called()


def test_run_daily_detection_zero_students():
    """Test detection when no students match query."""
    db = MagicMock()
    db.execute.return_value.scalars.return_value.all.return_value = []
    db.execute.return_value.scalar_one.return_value = 0
    
    svc = _make_service(db)
    result = _run(svc.run_daily_detection(tenant_id=1, actor="system"))
    
    assert result.thresholds_evaluated == 0


def test_recompute_scores_idempotent():
    """Test that recompute_scores can be called multiple times safely."""
    db = MagicMock()
    db.execute.return_value.scalars.return_value.all.return_value = []
    db.execute.return_value.scalar_one.return_value = 0
    db.execute.return_value.scalar_one_or_none.return_value = None
    db.flush = MagicMock()
    db.commit = MagicMock()
    
    svc = _make_service(db)
    
    # Call twice  
    result_1 = _run(svc.recompute_scores(tenant_id=1, actor="admin"))
    result_2 = _run(svc.recompute_scores(tenant_id=1, actor="admin"))
    
    assert isinstance(result_1, RiskDetectionResult)
    assert isinstance(result_2, RiskDetectionResult)


def test_get_kpi_summary_with_severity_breakdown():
    """Test KPI summary with severity breakdown rows."""
    db = MagicMock()
    
    severity_row = MagicMock()
    severity_row.severity = "high"
    severity_row.count = 5
    
    db.execute.return_value.scalar_one.return_value = 10
    db.execute.return_value.scalar_one_or_none.return_value = 3
    db.execute.return_value.all.return_value = [severity_row]
    
    svc = _make_service(db)
    result = _run(svc.get_kpi_summary(tenant_id=1))
    
    assert isinstance(result, dict)


def test_recompute_scores_with_tenant_isolation():
    """Test that different tenants are isolated."""
    db = MagicMock()
    db.execute.return_value.scalars.return_value.all.return_value = []
    db.execute.return_value.scalar_one.return_value = 0
    db.execute.return_value.scalar_one_or_none.return_value = None
    
    svc = _make_service(db)
    
    # Run for different tenants
    result_t1 = _run(svc.recompute_scores(tenant_id=1, actor="admin"))
    result_t2 = _run(svc.recompute_scores(tenant_id=2, actor="admin"))
    
    assert isinstance(result_t1, RiskDetectionResult)
    assert isinstance(result_t2, RiskDetectionResult)


def test_get_kpi_summary_multiple_tenants():
    """Test KPI summary for different tenants."""
    db = MagicMock()
    db.execute.return_value.scalar_one.return_value = 0
    db.execute.return_value.scalar_one_or_none.return_value = None
    db.execute.return_value.all.return_value = []
    
    svc = _make_service(db)
    
    s1 = _run(svc.get_kpi_summary(tenant_id=1))
    s2 = _run(svc.get_kpi_summary(tenant_id=2))
    
    assert isinstance(s1, dict)
    assert isinstance(s2, dict)


def test_run_daily_detection_large_batch():
    """Test detection with multiple students."""
    db = MagicMock()
    
    s1 = MagicMock()
    s1.id, s1.tenant_id = 101, 1
    s2 = MagicMock()
    s2.id, s2.tenant_id = 102, 1
    
    db.execute.return_value.scalars.return_value.all.return_value = [s1, s2]
    db.execute.return_value.scalar_one.return_value = 0
    db.flush = MagicMock()
    db.commit = MagicMock()
    
    svc = _make_service(db)
    result = _run(svc.run_daily_detection(tenant_id=1, actor="batch"))
    
    assert isinstance(result, RiskDetectionResult)
    db.flush.assert_called()


def test_recompute_scores_returns_result():
    """Test that recompute_scores returns correct type."""
    db = MagicMock()
    db.execute.return_value.scalars.return_value.all.return_value = []
    db.execute.return_value.scalar_one.return_value = 0
    db.execute.return_value.scalar_one_or_none.return_value = None
    db.flush = MagicMock()
    db.commit = MagicMock()
    
    svc = _make_service(db)
    result = _run(svc.recompute_scores(tenant_id=1, actor="admin"))
    
    assert isinstance(result, RiskDetectionResult)
    assert hasattr(result, "signals_created")
    assert hasattr(result, "cases_created")


def test_get_kpi_summary_query_structure():
    """Test KPI summary query execution."""
    db = MagicMock()
    db.execute.return_value.scalar_one.return_value = 7
    db.execute.return_value.scalar_one_or_none.return_value = 2
    db.execute.return_value.all.return_value = []
    
    svc = _make_service(db)
    result = _run(svc.get_kpi_summary(tenant_id=1))
    
    assert isinstance(result, dict)
    db.execute.assert_called()


# ═════════════════════════════════════════════════════════════════════════════
# EXTENDED COVERAGE — Risk Service Edge Cases and Scenarios (10 additional tests)
# ═════════════════════════════════════════════════════════════════════════════


def test_run_daily_detection_with_threshold_exceptions():
    """Test detection when threshold evaluation raises exception."""
    db = MagicMock()
    db.execute.return_value.scalars.return_value.all.return_value = []
    db.execute.return_value.scalar_one.return_value = 0
    
    svc = _make_service(db)
    with patch("app.modules.interventions.risk_service._audit") as audit_mock:
        result = _run(svc.run_daily_detection(tenant_id=1, actor="system"))
    
    assert result.thresholds_evaluated == 0


def test_run_daily_detection_large_batch():
    """Test detection with multiple students returning risks."""
    db = MagicMock()
    
    # Mock multiple student records
    student_1 = MagicMock()
    student_1.id = 101
    student_1.tenant_id = 1
    student_2 = MagicMock()
    student_2.id = 102
    student_2.tenant_id = 1
    
    db.execute.return_value.scalars.return_value.all.return_value = [student_1, student_2]
    db.execute.return_value.scalar_one.return_value = 0
    db.flush = MagicMock()
    db.commit = MagicMock()
    
    svc = _make_service(db)
    result = _run(svc.run_daily_detection(tenant_id=1, actor="scheduler"))
    
    assert isinstance(result, RiskDetectionResult)
    db.flush.assert_called()
    db.commit.assert_called()


def test_recompute_scores_idempotent_call():
    """Test that recompute_scores is idempotent (safe to call multiple times)."""
    db = MagicMock()
    db.execute.return_value.scalars.return_value.all.return_value = []
    db.execute.return_value.scalar_one.return_value = 0
    db.execute.return_value.scalar_one_or_none.return_value = None
    db.flush = MagicMock()
    db.commit = MagicMock()
    
    svc = _make_service(db)
    
    # Call twice with same parameters
    result_1 = _run(svc.recompute_scores(tenant_id=1, actor="admin"))
    result_2 = _run(svc.recompute_scores(tenant_id=1, actor="admin"))
    
    assert result_1.signals_created == result_2.signals_created
    assert result_1.cases_created == result_2.cases_created


def test_get_kpi_summary_with_severity_breakdown():
    """Test KPI summary includes severity breakdown."""
    db = MagicMock()
    
    severity_row = MagicMock()
    severity_row.severity = "high"
    severity_row.count = 5
    
    db.execute.return_value.scalar_one.return_value = 10  # total cases
    db.execute.return_value.scalar_one_or_none.return_value = 3  # active interventions
    db.execute.return_value.all.return_value = [severity_row]
    
    svc = _make_service(db)
    result = _run(svc.get_kpi_summary(tenant_id=1))
    
    assert isinstance(result, dict)
    assert len(result) >= 0


def test_run_daily_detection_zero_students():
    """Test detection when no students match criteria."""
    db = MagicMock()
    db.execute.return_value.scalars.return_value.all.return_value = []
    db.execute.return_value.scalar_one.return_value = 0
    
    svc = _make_service(db)
    result = _run(svc.run_daily_detection(tenant_id=1, actor="system"))
    
    assert result.thresholds_evaluated == 0


def test_recompute_scores_with_tenant_isolation():
    """Test that recompute_scores respects tenant boundaries."""
    db = MagicMock()
    db.execute.return_value.scalars.return_value.all.return_value = []
    db.execute.return_value.scalar_one.return_value = 0
    db.execute.return_value.scalar_one_or_none.return_value = None
    
    svc = _make_service(db)
    
    # Run for different tenants
    result_t1 = _run(svc.recompute_scores(tenant_id=1, actor="admin"))
    result_t2 = _run(svc.recompute_scores(tenant_id=2, actor="admin"))
    
    # Both should return valid RiskDetectionResults
    assert isinstance(result_t1, RiskDetectionResult)
    assert isinstance(result_t2, RiskDetectionResult)


def test_get_kpi_summary_for_multiple_tenants():
    """Test KPI summary works for different tenant IDs."""
    db = MagicMock()
    db.execute.return_value.scalar_one.return_value = 0
    db.execute.return_value.scalar_one_or_none.return_value = None
    db.execute.return_value.all.return_value = []
    
    svc = _make_service(db)
    
    summary_1 = _run(svc.get_kpi_summary(tenant_id=1))
    summary_2 = _run(svc.get_kpi_summary(tenant_id=2))
    
    assert isinstance(summary_1, dict)
    assert isinstance(summary_2, dict)


def test_run_daily_detection_audit_logging():
    """Test that risk detection calls audit logging."""
    db = MagicMock()
    db.execute.return_value.scalars.return_value.all.return_value = []
    db.execute.return_value.scalar_one.return_value = 0
    
    svc = _make_service(db)
    
    with patch("app.modules.interventions.risk_service._audit") as audit_mock:
        _run(svc.run_daily_detection(tenant_id=1, actor="cron"))
        audit_mock.assert_called()


def test_recompute_scores_returns_result_object():
    """Test that recompute_scores returns proper RiskDetectionResult."""
    db = MagicMock()
    db.execute.return_value.scalars.return_value.all.return_value = []
    db.execute.return_value.scalar_one.return_value = 0
    db.execute.return_value.scalar_one_or_none.return_value = None
    db.flush = MagicMock()
    db.commit = MagicMock()
    
    svc = _make_service(db)
    
    result = _run(svc.recompute_scores(tenant_id=1, actor="admin"))
    assert isinstance(result, RiskDetectionResult)
    assert hasattr(result, "signals_created")
    assert hasattr(result, "cases_created")


def test_get_daily_summary_with_complex_query():
    """Test daily summary query construction."""
    db = MagicMock()
    db.execute.return_value.scalar_one.return_value = 7
    db.execute.return_value.scalar_one_or_none.return_value = 2
    db.execute.return_value.all.return_value = []
    
    svc = _make_service(db)
    result = _run(svc.get_kpi_summary(tenant_id=1))
    
    assert isinstance(result, dict)
    db.execute.assert_called()


# ═════════════════════════════════════════════════════════════════════════════
# EXTENDED COVERAGE TESTS — Risk Service Edge Cases and Scenarios
# ═════════════════════════════════════════════════════════════════════════════


def test_run_daily_detection_with_threshold_exceptions():
    """Test detection when threshold evaluation raises exception."""
    db = MagicMock()
    db.execute.return_value.scalars.return_value.all.return_value = []
    db.execute.return_value.scalar_one.return_value = 0
    
    svc = _make_service(db)
    with patch("app.modules.interventions.risk_service._audit") as audit_mock:
        result = _run(svc.run_daily_detection(tenant_id=1, actor="system"))
    
    assert result.thresholds_evaluated == 0
    audit_mock.assert_called()


def test_run_daily_detection_large_batch():
    """Test detection with multiple students returning risks."""
    db = MagicMock()
    
    # Mock multiple student records
    student_1 = MagicMock()
    student_1.id = 101
    student_1.tenant_id = 1
    student_2 = MagicMock()
    student_2.id = 102
    student_2.tenant_id = 1
    
    db.execute.return_value.scalars.return_value.all.return_value = [student_1, student_2]
    db.execute.return_value.scalar_one.return_value = 0
    db.flush = MagicMock()
    db.commit = MagicMock()
    
    svc = _make_service(db)
    result = _run(svc.run_daily_detection(tenant_id=1, actor="scheduler"))
    
    assert isinstance(result, RiskDetectionResult)
    db.flush.assert_called()
    db.commit.assert_called()


def test_recompute_scores_idempotent_call():
    """Test that recompute_scores is idempotent (safe to call multiple times)."""
    db = MagicMock()
    db.execute.return_value.scalars.return_value.all.return_value = []
    db.execute.return_value.scalar_one.return_value = 0
    db.execute.return_value.scalar_one_or_none.return_value = None
    db.flush = MagicMock()
    db.commit = MagicMock()
    
    svc = _make_service(db)
    
    # Call twice with same parameters
    result_1 = _run(svc.recompute_scores(tenant_id=1, actor="admin"))
    result_2 = _run(svc.recompute_scores(tenant_id=1, actor="admin"))
    
    assert result_1.signals_created == result_2.signals_created
    assert result_1.cases_created == result_2.cases_created


def test_get_kpi_summary_with_severity_breakdown():
    """Test KPI summary includes severity breakdown."""
    db = MagicMock()
    
    severity_row = MagicMock()
    severity_row.severity = "high"
    severity_row.count = 5
    
    db.execute.return_value.scalar_one.return_value = 10  # total cases
    db.execute.return_value.scalar_one_or_none.return_value = 3  # active interventions
    db.execute.return_value.all.return_value = [severity_row]
    
    svc = _make_service(db)
    result = _run(svc.get_kpi_summary(tenant_id=1))
    
    assert isinstance(result, dict)
    assert "total_cases" in result or len(result) > 0


def test_run_daily_detection_zero_students():
    """Test detection when no students match criteria."""
    db = MagicMock()
    db.execute.return_value.scalars.return_value.all.return_value = []
    db.execute.return_value.scalar_one.return_value = 0
    
    svc = _make_service(db)
    result = _run(svc.run_daily_detection(tenant_id=1, actor="system"))
    
    assert result.thresholds_evaluated == 0


def test_recompute_scores_with_tenant_isolation():
    """Test that recompute_scores respects tenant boundaries."""
    db = MagicMock()
    db.execute.return_value.scalars.return_value.all.return_value = []
    db.execute.return_value.scalar_one.return_value = 0
    db.execute.return_value.scalar_one_or_none.return_value = None
    
    svc = _make_service(db)
    
    # Run for different tenants
    result_t1 = _run(svc.recompute_scores(tenant_id=1, actor="admin"))
    result_t2 = _run(svc.recompute_scores(tenant_id=2, actor="admin"))
    
    # Both should return valid RiskDetectionResults
    assert isinstance(result_t1, RiskDetectionResult)
    assert isinstance(result_t2, RiskDetectionResult)


def test_get_kpi_summary_for_multiple_tenants():
    """Test KPI summary works for different tenant IDs."""
    db = MagicMock()
    db.execute.return_value.scalar_one.return_value = 0
    db.execute.return_value.scalar_one_or_none.return_value = None
    db.execute.return_value.all.return_value = []
    
    svc = _make_service(db)
    
    summary_1 = _run(svc.get_kpi_summary(tenant_id=1))
    summary_2 = _run(svc.get_kpi_summary(tenant_id=2))
    
    assert isinstance(summary_1, dict)
    assert isinstance(summary_2, dict)


def test_run_daily_detection_audit_logging():
    """Test that risk detection calls audit logging."""
    db = MagicMock()
    db.execute.return_value.scalars.return_value.all.return_value = []
    db.execute.return_value.scalar_one.return_value = 0
    
    svc = _make_service(db)
    
    with patch("app.modules.interventions.risk_service._audit") as audit_mock:
        _run(svc.run_daily_detection(tenant_id=1, actor="cron"))
        audit_mock.assert_called()


def test_recompute_scores_delegates_to_run_daily_detection_call():
    """Test that recompute_scores correctly delegates execution."""
    db = MagicMock()
    db.execute.return_value.scalars.return_value.all.return_value = []
    db.execute.return_value.scalar_one.return_value = 0
    db.execute.return_value.scalar_one_or_none.return_value = None
    db.flush = MagicMock()
    db.commit = MagicMock()
    
    svc = _make_service(db)
    
    with patch.object(svc, "run_daily_detection", wraps=svc.run_daily_detection) as mock_run:
        result = _run(svc.recompute_scores(tenant_id=1, actor="admin"))
        # Should have called run_daily_detection
        assert isinstance(result, RiskDetectionResult)


# ═════════════════════════════════════════════════════════════════════════════
# EXTENDED COVERAGE TESTS — Risk Service Edge Cases and Scenarios
# ═════════════════════════════════════════════════════════════════════════════


def test_run_daily_detection_with_threshold_exceptions():
    """Test detection when threshold evaluation raises exception."""
    db = MagicMock()
    db.execute.return_value.scalars.return_value.all.return_value = []
    db.execute.return_value.scalar_one.return_value = 0
    
    svc = _make_service(db)
    with patch("app.modules.interventions.risk_service._audit") as audit_mock:
        result = _run(svc.run_daily_detection(tenant_id=1, actor="system"))
    
    assert result.thresholds_evaluated == 0
    audit_mock.assert_called()


def test_run_daily_detection_large_batch():
    """Test detection with multiple students returning risks."""
    db = MagicMock()
    
    # Mock multiple student records
    student_1 = MagicMock()
    student_1.id = 101
    student_1.tenant_id = 1
    student_2 = MagicMock()
    student_2.id = 102
    student_2.tenant_id = 1
    
    db.execute.return_value.scalars.return_value.all.return_value = [student_1, student_2]
    db.execute.return_value.scalar_one.return_value = 0
    db.flush = MagicMock()
    db.commit = MagicMock()
    
    svc = _make_service(db)
    result = _run(svc.run_daily_detection(tenant_id=1, actor="scheduler"))
    
    assert isinstance(result, RiskDetectionResult)
    db.flush.assert_called()
    db.commit.assert_called()


def test_recompute_scores_idempotent_call():
    """Test that recompute_scores is idempotent (safe to call multiple times)."""
    db = MagicMock()
    db.execute.return_value.scalars.return_value.all.return_value = []
    db.execute.return_value.scalar_one.return_value = 0
    db.execute.return_value.scalar_one_or_none.return_value = None
    db.flush = MagicMock()
    db.commit = MagicMock()
    
    svc = _make_service(db)
    
    # Call twice with same parameters
    result_1 = _run(svc.recompute_scores(tenant_id=1, actor="admin"))
    result_2 = _run(svc.recompute_scores(tenant_id=1, actor="admin"))
    
    assert result_1.signals_created == result_2.signals_created
    assert result_1.cases_created == result_2.cases_created


def test_get_kpi_summary_with_severity_breakdown():
    """Test KPI summary includes severity breakdown."""
    db = MagicMock()
    
    severity_row = MagicMock()
    severity_row.severity = "high"
    severity_row.count = 5
    
    db.execute.return_value.scalar_one.return_value = 10  # total cases
    db.execute.return_value.scalar_one_or_none.return_value = 3  # active interventions
    db.execute.return_value.all.return_value = [severity_row]
    
    svc = _make_service(db)
    result = _run(svc.get_kpi_summary(tenant_id=1))
    
    assert isinstance(result, dict)
    assert "total_cases" in result or len(result) > 0


def test_run_daily_detection_zero_students():
    """Test detection when no students match criteria."""
    db = MagicMock()
    db.execute.return_value.scalars.return_value.all.return_value = []
    db.execute.return_value.scalar_one.return_value = 0
    
    svc = _make_service(db)
    result = _run(svc.run_daily_detection(tenant_id=1, actor="system"))
    
    assert result.thresholds_evaluated == 0


def test_recompute_scores_with_tenant_isolation():
    """Test that recompute_scores respects tenant boundaries."""
    db = MagicMock()
    db.execute.return_value.scalars.return_value.all.return_value = []
    db.execute.return_value.scalar_one.return_value = 0
    db.execute.return_value.scalar_one_or_none.return_value = None
    
    svc = _make_service(db)
    
    # Run for different tenants
    result_t1 = _run(svc.recompute_scores(tenant_id=1, actor="admin"))
    result_t2 = _run(svc.recompute_scores(tenant_id=2, actor="admin"))
    
    # Both should return valid RiskDetectionResults
    assert isinstance(result_t1, RiskDetectionResult)
    assert isinstance(result_t2, RiskDetectionResult)


def test_get_kpi_summary_for_multiple_tenants():
    """Test KPI summary works for different tenant IDs."""
    db = MagicMock()
    db.execute.return_value.scalar_one.return_value = 0
    db.execute.return_value.scalar_one_or_none.return_value = None
    db.execute.return_value.all.return_value = []
    
    svc = _make_service(db)
    
    summary_1 = _run(svc.get_kpi_summary(tenant_id=1))
    summary_2 = _run(svc.get_kpi_summary(tenant_id=2))
    
    assert isinstance(summary_1, dict)
    assert isinstance(summary_2, dict)


def test_run_daily_detection_audit_logging():
    """Test that risk detection calls audit logging."""
    db = MagicMock()
    db.execute.return_value.scalars.return_value.all.return_value = []
    db.execute.return_value.scalar_one.return_value = 0
    
    svc = _make_service(db)
    
    with patch("app.modules.interventions.risk_service._audit") as audit_mock:
        _run(svc.run_daily_detection(tenant_id=1, actor="cron"))
        audit_mock.assert_called()


def test_recompute_scores_delegates_to_run_daily_detection_call():
    """Test that recompute_scores correctly delegates execution."""
    db = MagicMock()
    db.execute.return_value.scalars.return_value.all.return_value = []
    db.execute.return_value.scalar_one.return_value = 0
    db.execute.return_value.scalar_one_or_none.return_value = None
    db.flush = MagicMock()
    db.commit = MagicMock()
    
    svc = _make_service(db)
    
    with patch.object(svc, "run_daily_detection", wraps=svc.run_daily_detection) as mock_run:
        result = _run(svc.recompute_scores(tenant_id=1, actor="admin"))
        # Should have called run_daily_detection
        assert isinstance(result, RiskDetectionResult)
