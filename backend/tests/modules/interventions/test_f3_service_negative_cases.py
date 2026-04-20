"""F3 service-level negative tests.

Validates unfrozen behaviour and not-found paths without requiring a live DB.
All DB access is monkeypatched to return None / empty list.
"""
from __future__ import annotations

from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from app.core.module_helpers.service_validation import (
    TenantRequiredError,
    TenantResourceNotFoundError,
)
from app.modules.interventions.effectiveness_schemas import (
    CohortAnalyzeRequestSchema,
    CohortFinalizeRequestSchema,
)
from app.modules.interventions.effectiveness_service import (
    InterventionEffectivenessService,
)
from app.modules.observability.metrics import clear_metrics_state, render_metrics


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_service(scalar_return=None, scalars_return=None):
    """Return a service wired to a mock SQLAlchemy Session."""
    db = MagicMock()
    db.scalar.return_value = scalar_return
    scalars_mock = MagicMock()
    scalars_mock.__iter__ = MagicMock(return_value=iter(scalars_return or []))
    db.scalars.return_value = scalars_mock
    return InterventionEffectivenessService(db=db)


# ---------------------------------------------------------------------------
# Unfrozen behaviour tests (post-F3.3)
# ---------------------------------------------------------------------------

def test_finalize_cohort_creates_cohort_via_db() -> None:
    """finalize_cohort is unfrozen — must call db.add + db.flush."""
    clear_metrics_state()
    svc = _make_service()
    payload = CohortFinalizeRequestSchema(
        playbook_id=1,
        cohort_name="cohort-2026-q1",
        analysis_window_start="2026-01-01",
        analysis_window_end="2026-03-31",
    )
    result = svc.finalize_cohort(tenant_id=1, actor="tester", payload=payload)
    assert result is not None
    svc._db.add.assert_called_once()
    svc._db.flush.assert_called_once()
    metrics = render_metrics()
    assert 'f3_cohort_operations_total{tenant_id="1",operation="finalize",status="success"} 1' in metrics
    assert 'f3_guardrails_evaluated_total{tenant_id="1",guardrail="tenant_id_provided",result="pass"} 1' in metrics


def test_analyze_cohort_returns_queued_status() -> None:
    """analyze_cohort is unfrozen — must return analysis_queued dict for existing cohort."""
    clear_metrics_state()
    fake_cohort = MagicMock()
    fake_cohort.tenant_id = 1
    fake_cohort.id = 99
    fake_cohort.student_count = 50
    fake_cohort.data_completeness_pct = Decimal("90.00")
    svc = _make_service(scalar_return=fake_cohort)

    payload = CohortAnalyzeRequestSchema(segment_keys=[])
    result = svc.analyze_cohort(tenant_id=1, cohort_id=99, actor="tester", payload=payload)
    assert result["status"] == "analysis_queued"
    assert result["cohort_id"] == 99
    assert "requested_at" in result
    metrics = render_metrics()
    assert 'f3_cohort_operations_total{tenant_id="1",operation="analyze",status="success"} 1' in metrics
    assert 'f3_active_cohort_analysis_queue_depth{tenant_id="1",queue_name="analyze_queue",status="pending"} 1' in metrics


def test_analyze_cohort_raises_not_found_when_cohort_missing() -> None:
    """analyze_cohort must raise TenantResourceNotFoundError when cohort is None."""
    clear_metrics_state()
    svc = _make_service(scalar_return=None)

    payload = CohortAnalyzeRequestSchema(recalculate=False)
    with pytest.raises(TenantResourceNotFoundError, match="not found"):
        svc.analyze_cohort(tenant_id=1, cohort_id=9999, actor="tester", payload=payload)
    metrics = render_metrics()
    assert 'f3_cohort_operations_total{tenant_id="1",operation="analyze",status="error"} 1' in metrics


# ---------------------------------------------------------------------------
# Not-found path tests
# ---------------------------------------------------------------------------

def test_get_outcomes_raises_not_found_when_cohort_missing() -> None:
    """get_outcomes must raise TenantResourceNotFoundError when cohort is absent."""
    clear_metrics_state()
    svc = _make_service(scalar_return=None)

    with pytest.raises(TenantResourceNotFoundError, match="not found"):
        svc.get_outcomes(tenant_id=1, cohort_id=42)
    metrics = render_metrics()
    assert 'f3_cohort_operations_total{tenant_id="1",operation="fetch_outcomes",status="error"} 1' in metrics


def test_get_outcomes_returns_empty_list_when_no_outcomes() -> None:
    """get_outcomes returns [] for cohort with zero outcome rows."""
    clear_metrics_state()
    fake_cohort = MagicMock()
    fake_cohort.tenant_id = 1
    svc = _make_service(scalar_return=fake_cohort, scalars_return=[])

    result = svc.get_outcomes(tenant_id=1, cohort_id=1)
    assert result == []
    metrics = render_metrics()
    assert 'f3_cohort_operations_total{tenant_id="1",operation="fetch_outcomes",status="success"} 1' in metrics


def test_get_latest_by_playbook_raises_not_found() -> None:
    """get_latest_by_playbook raises TenantResourceNotFoundError when no cohort for playbook."""
    clear_metrics_state()
    svc = _make_service(scalar_return=None)

    with pytest.raises(TenantResourceNotFoundError, match="No cohort found"):
        svc.get_latest_by_playbook(tenant_id=1, playbook_id=7)
    metrics = render_metrics()
    assert 'f3_cohort_operations_total{tenant_id="1",operation="fetch_latest_by_playbook",status="error"} 1' in metrics


# ---------------------------------------------------------------------------
# Tenant validation guardrail
# ---------------------------------------------------------------------------

def test_finalize_cohort_validates_tenant_id_zero() -> None:
    """tenant_id=0 must be rejected (TenantRequiredError) before freeze guard fires."""
    clear_metrics_state()
    svc = _make_service()
    payload = CohortFinalizeRequestSchema(
        playbook_id=1,
        cohort_name="cohort-zero-tenant",
        analysis_window_start="2026-01-01",
        analysis_window_end="2026-03-31",
    )
    with pytest.raises(TenantRequiredError, match="positive integer"):
        svc.finalize_cohort(tenant_id=0, actor="tester", payload=payload)
    metrics = render_metrics()
    assert 'f3_guardrails_evaluated_total{tenant_id="0",guardrail="tenant_id_provided",result="fail"} 1' in metrics
    assert 'f3_cohort_operations_total{tenant_id="0",operation="finalize",status="error"} 1' in metrics


# ---------------------------------------------------------------------------
# Analyze guard: cohort must be finalized (student_count > 0 or data_completeness_pct set)
# ---------------------------------------------------------------------------

def test_analyze_cohort_raises_domain_error_when_draft() -> None:
    """analyze_cohort must raise DomainValidationError when cohort is in draft state
    (student_count <= 0 and data_completeness_pct is None)."""
    from app.core.module_helpers.service_validation import DomainValidationError

    clear_metrics_state()
    fake_cohort = MagicMock()
    fake_cohort.tenant_id = 1
    fake_cohort.id = 5
    fake_cohort.student_count = 0
    fake_cohort.data_completeness_pct = None
    svc = _make_service(scalar_return=fake_cohort)

    payload = CohortAnalyzeRequestSchema(segment_keys=[])
    with pytest.raises(DomainValidationError, match="finalized"):
        svc.analyze_cohort(tenant_id=1, cohort_id=5, actor="tester", payload=payload)

    metrics = render_metrics()
    assert 'f3_cohort_operations_total{tenant_id="1",operation="analyze",status="error"} 1' in metrics


def test_analyze_cohort_raises_domain_error_when_student_count_negative() -> None:
    """student_count < 0 also counts as draft — guard must fire."""
    from app.core.module_helpers.service_validation import DomainValidationError

    clear_metrics_state()
    fake_cohort = MagicMock()
    fake_cohort.tenant_id = 1
    fake_cohort.id = 6
    fake_cohort.student_count = -1
    fake_cohort.data_completeness_pct = None
    svc = _make_service(scalar_return=fake_cohort)

    payload = CohortAnalyzeRequestSchema(segment_keys=[])
    with pytest.raises(DomainValidationError, match="finalized"):
        svc.analyze_cohort(tenant_id=1, cohort_id=6, actor="tester", payload=payload)


def test_analyze_cohort_passes_when_data_completeness_set_but_zero_students() -> None:
    """data_completeness_pct being set bypasses the draft guard (cohort was re-loaded
    with completeness but student count still 0 edge case)."""
    from decimal import Decimal

    clear_metrics_state()
    fake_cohort = MagicMock()
    fake_cohort.tenant_id = 1
    fake_cohort.id = 7
    fake_cohort.student_count = 0
    fake_cohort.data_completeness_pct = Decimal("0.95")
    svc = _make_service(scalar_return=fake_cohort)

    payload = CohortAnalyzeRequestSchema(segment_keys=[])
    result = svc.analyze_cohort(tenant_id=1, cohort_id=7, actor="tester", payload=payload)
    assert result["status"] == "analysis_queued"


# ---------------------------------------------------------------------------
# finalize_existing_cohort: guard + not-found path
# ---------------------------------------------------------------------------

def test_finalize_existing_cohort_raises_not_found_when_missing() -> None:
    """finalize_existing_cohort must raise TenantResourceNotFoundError when cohort absent."""
    clear_metrics_state()
    svc = _make_service(scalar_return=None)

    with pytest.raises(TenantResourceNotFoundError):
        svc.finalize_existing_cohort(tenant_id=1, cohort_id=999)


def test_finalize_existing_cohort_calls_flush_on_existing() -> None:
    """finalize_existing_cohort must call db.flush() (no db.add) for existing cohort."""
    clear_metrics_state()
    fake_cohort = MagicMock()
    fake_cohort.tenant_id = 1
    fake_cohort.id = 42
    fake_cohort.student_count = 50

    db = MagicMock()
    db.scalar.return_value = fake_cohort
    svc = InterventionEffectivenessService(db=db)

    result = svc.finalize_existing_cohort(tenant_id=1, cohort_id=42)
    assert result is fake_cohort
    db.flush.assert_called_once()
    db.add.assert_not_called()


def test_finalize_existing_cohort_cross_tenant_raises() -> None:
    """finalize_existing_cohort must reject cohort belonging to a different tenant."""
    from app.core.module_helpers.service_validation import DomainValidationError

    clear_metrics_state()
    fake_cohort = MagicMock()
    fake_cohort.tenant_id = 99  # different tenant
    fake_cohort.id = 10

    svc = _make_service(scalar_return=fake_cohort)

    with pytest.raises((DomainValidationError, PermissionError, Exception)):
        svc.finalize_existing_cohort(tenant_id=1, cohort_id=10)
