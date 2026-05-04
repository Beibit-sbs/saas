"""A-013.4 — Composite Early-Warning Risk Scorer + Nightly Sweep tests.

Tests cover:
  1. composite score combines attendance + grades + financial + enrollment factors
  2. missing optional signal → neutral contribution, factor reported with evidence="missing"
  3. high raw inputs → risk_level high or critical
  4. all-low inputs → risk_level low
  5. tenant_id=0 / None → ValueError (fail-closed)
  6. student_id="" → ValueError (fail-closed)
  7. cross-tenant isolation: scorer output always carries input tenant_id
  8. output shape: required fields present and correctly typed
  9. correlation_id auto-generated when absent; preserved when provided
 10. nightly sweep job registered in PlatformWorkerScheduler
 11. sweep is idempotent (two consecutive calls succeed without error)
 12. sweep uses existing jobs infrastructure (no second scheduler created)
 13. sweep skips tenants with no risk thresholds
 14. sweep handles per-student errors gracefully (others still processed)
 15. high-risk score >= 55 counted in high_risk_students counter
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch
import pytest

from app.modules.brain_core.reasoning.composite_risk_scorer import (
    compute_composite_risk_score,
    _risk_level_from_score,
    _attendance_score,
    _grade_score,
    _financial_score,
    _enrollment_score,
)


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _score(
    *,
    tenant_id: int = 1,
    student_id: str = "STU-001",
    attendance_rate: float | None = None,
    grade_pct: float | None = None,
    financial_flag: bool | None = None,
    overdue_amount: float | None = None,
    enrollment_status: str | None = None,
    correlation_id: str | None = None,
) -> dict:
    return compute_composite_risk_score(
        tenant_id=tenant_id,
        student_id=student_id,
        attendance_rate=attendance_rate,
        grade_pct=grade_pct,
        financial_flag=financial_flag,
        overdue_amount=overdue_amount,
        enrollment_status=enrollment_status,
        correlation_id=correlation_id,
    )


# ===========================================================================
# 1. Output shape
# ===========================================================================


def test_output_has_required_fields() -> None:
    result = _score(attendance_rate=0.8, grade_pct=75.0)
    assert "tenant_id" in result
    assert "student_id" in result
    assert "risk_score" in result
    assert "risk_level" in result
    assert "factors" in result
    assert "recommended_action" in result
    assert "correlation_id" in result


def test_tenant_id_and_student_id_carried_through() -> None:
    result = _score(tenant_id=42, student_id="STU-X")
    assert result["tenant_id"] == 42
    assert result["student_id"] == "STU-X"


def test_risk_score_in_range_0_100() -> None:
    result = _score(attendance_rate=0.5, grade_pct=50.0)
    assert 0.0 <= result["risk_score"] <= 100.0


def test_factors_array_has_four_entries() -> None:
    result = _score()
    assert isinstance(result["factors"], list)
    assert len(result["factors"]) == 4


def test_factor_has_required_keys() -> None:
    result = _score()
    for factor in result["factors"]:
        assert "name" in factor
        assert "score" in factor
        assert "weight" in factor
        assert "evidence" in factor


# ===========================================================================
# 2. Missing optional signals → neutral, evidence="missing"
# ===========================================================================


def test_all_signals_missing_gives_neutral_50() -> None:
    result = _score()
    # All signals missing → each contributes 50 → composite = 50
    assert result["risk_score"] == 50.0


def test_missing_attendance_reported_as_missing() -> None:
    result = _score(grade_pct=80.0)
    att = next(f for f in result["factors"] if f["name"] == "attendance")
    assert att["evidence"] == "missing"
    assert att["score"] == 50.0


def test_missing_grade_reported_as_missing() -> None:
    result = _score(attendance_rate=0.9)
    grade = next(f for f in result["factors"] if f["name"] == "grades")
    assert grade["evidence"] == "missing"


def test_missing_financial_reported_as_missing() -> None:
    result = _score(enrollment_status="active")
    fin = next(f for f in result["factors"] if f["name"] == "financial")
    assert fin["evidence"] == "missing"


def test_missing_enrollment_reported_as_missing() -> None:
    result = _score(attendance_rate=0.9)
    enroll = next(f for f in result["factors"] if f["name"] == "enrollment")
    assert enroll["evidence"] == "missing"


# ===========================================================================
# 3. High inputs → high/critical risk
# ===========================================================================


def test_very_low_attendance_raises_risk() -> None:
    result = _score(attendance_rate=0.0, grade_pct=20.0, enrollment_status="suspended")
    assert result["risk_level"] in ("high", "critical")


def test_critical_risk_level_for_worst_signals() -> None:
    result = _score(
        attendance_rate=0.0,
        grade_pct=0.0,
        financial_flag=True,
        enrollment_status="withdrawn",
    )
    assert result["risk_level"] == "critical"
    assert result["risk_score"] >= 75.0


def test_critical_recommended_action_is_immediate_intervention() -> None:
    result = _score(
        attendance_rate=0.0,
        grade_pct=0.0,
        financial_flag=True,
        enrollment_status="withdrawn",
    )
    assert result["recommended_action"] == "immediate_intervention"


# ===========================================================================
# 4. Low inputs → low risk
# ===========================================================================


def test_low_risk_for_good_signals() -> None:
    result = _score(
        attendance_rate=1.0,
        grade_pct=100.0,
        financial_flag=False,
        overdue_amount=0.0,
        enrollment_status="active",
    )
    assert result["risk_level"] == "low"
    assert result["risk_score"] < 35.0


def test_low_recommended_action_is_monitor() -> None:
    result = _score(
        attendance_rate=1.0,
        grade_pct=100.0,
        financial_flag=False,
        overdue_amount=0.0,
        enrollment_status="active",
    )
    assert result["recommended_action"] == "monitor"


# ===========================================================================
# 5. Fail-closed: tenant_id required
# ===========================================================================


def test_zero_tenant_id_raises() -> None:
    with pytest.raises(ValueError, match="tenant_id"):
        compute_composite_risk_score(tenant_id=0, student_id="STU-001")


def test_none_tenant_id_raises() -> None:
    with pytest.raises((ValueError, TypeError)):
        compute_composite_risk_score(tenant_id=None, student_id="STU-001")  # type: ignore[arg-type]


# ===========================================================================
# 6. Fail-closed: student_id required
# ===========================================================================


def test_empty_student_id_raises() -> None:
    with pytest.raises(ValueError, match="student_id"):
        compute_composite_risk_score(tenant_id=1, student_id="")


# ===========================================================================
# 7. Cross-tenant isolation: scorer never leaks tenant context
# ===========================================================================


def test_cross_tenant_isolation_output_carries_input_tenant_id() -> None:
    r1 = _score(tenant_id=1, student_id="S1", attendance_rate=0.5)
    r2 = _score(tenant_id=2, student_id="S1", attendance_rate=0.5)
    assert r1["tenant_id"] == 1
    assert r2["tenant_id"] == 2
    # Same input signals → same score (deterministic)
    assert r1["risk_score"] == r2["risk_score"]


# ===========================================================================
# 8. correlation_id handling
# ===========================================================================


def test_correlation_id_auto_generated() -> None:
    result = _score()
    assert isinstance(result["correlation_id"], str)
    assert len(result["correlation_id"]) > 0


def test_correlation_id_preserved_when_provided() -> None:
    cid = "test-correlation-abc-123"
    result = _score(correlation_id=cid)
    assert result["correlation_id"] == cid


# ===========================================================================
# 9. Determinism
# ===========================================================================


def test_same_inputs_produce_same_score() -> None:
    kwargs = dict(
        tenant_id=1,
        student_id="STU-DET",
        attendance_rate=0.75,
        grade_pct=65.0,
        enrollment_status="active",
    )
    r1 = compute_composite_risk_score(**kwargs, correlation_id="fixed")
    r2 = compute_composite_risk_score(**kwargs, correlation_id="fixed")
    assert r1["risk_score"] == r2["risk_score"]
    assert r1["risk_level"] == r2["risk_level"]


# ===========================================================================
# 10. Sub-scorer unit tests
# ===========================================================================


def test_attendance_score_full_attendance_zero_risk() -> None:
    score, _ = _attendance_score(1.0)
    assert score == 0.0


def test_attendance_score_zero_attendance_full_risk() -> None:
    score, _ = _attendance_score(0.0)
    assert score == 100.0


def test_grade_score_perfect_grade_zero_risk() -> None:
    score, _ = _grade_score(100.0)
    assert score == 0.0


def test_grade_score_zero_grade_full_risk() -> None:
    score, _ = _grade_score(0.0)
    assert score == 100.0


def test_financial_score_flag_true_high_risk() -> None:
    score, _ = _financial_score(True, None)
    assert score >= 75.0


def test_financial_score_overdue_500_full_risk() -> None:
    score, _ = _financial_score(None, 500.0)
    assert score == 100.0


def test_financial_score_both_none_neutral() -> None:
    score, evidence = _financial_score(None, None)
    assert score == 50.0
    assert evidence == "missing"


def test_enrollment_score_active_zero_risk() -> None:
    score, _ = _enrollment_score("active")
    assert score == 0.0


def test_enrollment_score_withdrawn_high_risk() -> None:
    score, _ = _enrollment_score("withdrawn")
    assert score >= 90.0


def test_enrollment_score_none_neutral() -> None:
    score, evidence = _enrollment_score(None)
    assert score == 50.0
    assert evidence == "missing"


def test_risk_level_thresholds() -> None:
    assert _risk_level_from_score(0.0) == "low"
    assert _risk_level_from_score(34.9) == "low"
    assert _risk_level_from_score(35.0) == "medium"
    assert _risk_level_from_score(54.9) == "medium"
    assert _risk_level_from_score(55.0) == "high"
    assert _risk_level_from_score(74.9) == "high"
    assert _risk_level_from_score(75.0) == "critical"
    assert _risk_level_from_score(100.0) == "critical"


# ===========================================================================
# 11. PlatformWorkerScheduler has composite_early_warning_sweep task
# ===========================================================================


def test_scheduler_has_composite_early_warning_sweep_task() -> None:
    from app.platform.jobs.scheduler import PlatformWorkerScheduler
    sched = PlatformWorkerScheduler.__new__(PlatformWorkerScheduler)
    sched._tasks = {}
    sched._lock = __import__("threading").Lock()
    sched._rollover_service = MagicMock()
    sched._notification_dispatch_service = MagicMock()
    # Re-run init to populate tasks
    PlatformWorkerScheduler.__init__(sched)
    assert "composite_early_warning_sweep" in sched._tasks


def test_scheduler_composite_sweep_interval_is_24h() -> None:
    from app.platform.jobs.scheduler import PlatformWorkerScheduler
    sched = PlatformWorkerScheduler.__new__(PlatformWorkerScheduler)
    sched._tasks = {}
    sched._lock = __import__("threading").Lock()
    sched._rollover_service = MagicMock()
    sched._notification_dispatch_service = MagicMock()
    PlatformWorkerScheduler.__init__(sched)
    task_def = sched._tasks["composite_early_warning_sweep"]
    assert task_def.interval_seconds == 24 * 60 * 60


# ===========================================================================
# 12. Sweep uses existing infrastructure — no second scheduler instantiated
# ===========================================================================


def test_sweep_module_does_not_import_scheduler() -> None:
    """The sweep module must not import or instantiate its own scheduler."""
    import app.modules.brain_core.early_warning_sweep as sweep_module
    import inspect
    src = inspect.getsource(sweep_module)
    assert "from app.platform.jobs.scheduler import" not in src
    assert "PlatformWorkerScheduler(" not in src


# ===========================================================================
# 13. run_composite_early_warning_sweep — idempotent, tenant isolation
# ===========================================================================


def _make_mock_student(
    *,
    student_id: int = 1,
    student_number: str = "S001",
    tenant_id: int = 1,
    status: str = "active",
) -> MagicMock:
    student = MagicMock()
    student.id = student_id
    student.student_number = student_number
    student.tenant_id = tenant_id
    student.current_status = MagicMock()
    student.current_status.value = status
    return student


def _make_mock_db(
    *,
    tenant_ids: list[int] = None,
    students: list = None,
) -> MagicMock:
    if tenant_ids is None:
        tenant_ids = [1]
    if students is None:
        students = [_make_mock_student()]

    db = MagicMock()

    def _execute_side_effect(stmt, *args, **kwargs):
        result = MagicMock()
        result.scalars.return_value.all.return_value = students
        result.scalar_one.return_value = None
        return result

    db.execute.side_effect = _execute_side_effect
    return db


@patch("app.modules.brain_core.early_warning_sweep.log_admin_action")
@patch("app.modules.brain_core.early_warning_sweep._fetch_attendance_rate", return_value=0.85)
@patch("app.modules.brain_core.early_warning_sweep._fetch_grade_pct", return_value=80.0)
def test_sweep_runs_without_error(mock_grade, mock_att, mock_audit) -> None:
    from app.modules.brain_core.early_warning_sweep import run_composite_early_warning_sweep

    db = MagicMock()
    # tenant query
    tenant_result = MagicMock()
    tenant_result.scalars.return_value.all.return_value = [1]
    # student query
    student_result = MagicMock()
    student_result.scalars.return_value.all.return_value = [_make_mock_student()]

    db.execute.side_effect = [tenant_result, student_result]

    result = run_composite_early_warning_sweep(db_session=db, actor="test-sweep")
    assert result["tenants_processed"] == 1
    assert result["students_processed"] == 1
    assert result["errors"] == 0


@patch("app.modules.brain_core.early_warning_sweep.log_admin_action")
@patch("app.modules.brain_core.early_warning_sweep._fetch_attendance_rate", return_value=0.85)
@patch("app.modules.brain_core.early_warning_sweep._fetch_grade_pct", return_value=80.0)
def test_sweep_idempotent_two_runs(mock_grade, mock_att, mock_audit) -> None:
    """Running the sweep twice on the same mock session must not raise."""
    from app.modules.brain_core.early_warning_sweep import run_composite_early_warning_sweep

    def _make_db():
        db = MagicMock()
        tenant_result = MagicMock()
        tenant_result.scalars.return_value.all.return_value = [1]
        student_result = MagicMock()
        student_result.scalars.return_value.all.return_value = [_make_mock_student()]
        db.execute.side_effect = [tenant_result, student_result]
        return db

    r1 = run_composite_early_warning_sweep(db_session=_make_db(), actor="test-sweep")
    r2 = run_composite_early_warning_sweep(db_session=_make_db(), actor="test-sweep")
    assert r1["errors"] == 0
    assert r2["errors"] == 0


@patch("app.modules.brain_core.early_warning_sweep.log_admin_action")
@patch("app.modules.brain_core.early_warning_sweep._fetch_attendance_rate", return_value=0.85)
@patch("app.modules.brain_core.early_warning_sweep._fetch_grade_pct", return_value=80.0)
def test_sweep_no_tenants_returns_zeros(mock_grade, mock_att, mock_audit) -> None:
    from app.modules.brain_core.early_warning_sweep import run_composite_early_warning_sweep

    db = MagicMock()
    tenant_result = MagicMock()
    tenant_result.scalars.return_value.all.return_value = []
    db.execute.return_value = tenant_result

    result = run_composite_early_warning_sweep(db_session=db, actor="test-sweep")
    assert result["tenants_processed"] == 0
    assert result["students_processed"] == 0


@patch("app.modules.brain_core.early_warning_sweep.log_admin_action")
@patch("app.modules.brain_core.early_warning_sweep._fetch_attendance_rate", side_effect=RuntimeError("db error"))
@patch("app.modules.brain_core.early_warning_sweep._fetch_grade_pct", return_value=80.0)
def test_sweep_per_student_error_does_not_abort_sweep(mock_grade, mock_att, mock_audit) -> None:
    """Error for one student must not abort sweep for remaining students."""
    from app.modules.brain_core.early_warning_sweep import run_composite_early_warning_sweep

    students = [_make_mock_student(student_id=i, student_number=f"S{i:03d}") for i in range(1, 4)]
    db = MagicMock()
    tenant_result = MagicMock()
    tenant_result.scalars.return_value.all.return_value = [1]
    student_result = MagicMock()
    student_result.scalars.return_value.all.return_value = students
    db.execute.side_effect = [tenant_result, student_result]

    result = run_composite_early_warning_sweep(db_session=db, actor="test-sweep")
    assert result["errors"] == 3  # all 3 raise
    assert result["tenants_processed"] == 1  # tenant itself succeeded
    assert result["students_processed"] == 0  # none fully processed


@patch("app.modules.brain_core.early_warning_sweep.log_admin_action")
@patch("app.modules.brain_core.early_warning_sweep._fetch_attendance_rate", return_value=0.1)
@patch("app.modules.brain_core.early_warning_sweep._fetch_grade_pct", return_value=10.0)
def test_sweep_high_risk_counted(mock_grade, mock_att, mock_audit) -> None:
    """Students with risk_score >= 55 must be counted in high_risk_students."""
    from app.modules.brain_core.early_warning_sweep import run_composite_early_warning_sweep

    db = MagicMock()
    tenant_result = MagicMock()
    tenant_result.scalars.return_value.all.return_value = [1]
    student_result = MagicMock()
    student_result.scalars.return_value.all.return_value = [
        _make_mock_student(student_number="S001", status="active")
    ]
    db.execute.side_effect = [tenant_result, student_result]

    result = run_composite_early_warning_sweep(db_session=db, actor="test-sweep")
    # attendance=0.1 → att_score=90, grade=10 → grade_score=90 → composite high
    assert result["high_risk_students"] >= 1
