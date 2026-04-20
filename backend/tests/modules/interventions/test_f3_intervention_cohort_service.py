"""F3 integration test skeleton — InterventionEffectivenessService with mock DB.

Scenario: Program Manager finalizes a cohort after a Q1-2026 dropout-risk intervention.
- 50 students treated (F1 risk_band=high, F2 playbook_execution exists)
- 50 students control group
- Expected outcome: 4pp dropout-rate reduction

All DB calls are mocked; no live PostgreSQL required.
"""
from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from app.core.module_helpers.service_validation import (
    DomainValidationError,
    TenantRequiredError,
    TenantResourceNotFoundError,
)
from app.modules.interventions.effectiveness_models import (
    InterventionCohortModel,
    InterventionCohortOutcomeModel,
    InterventionCohortOutcomeType,
)
from app.modules.interventions.effectiveness_schemas import (
    CohortAnalyzeRequestSchema,
    CohortFinalizeRequestSchema,
)
from app.modules.interventions.effectiveness_service import (
    InterventionEffectivenessService,
)


# ---------------------------------------------------------------------------
# Shared mock data
# ---------------------------------------------------------------------------

MOCK_NOW = datetime(2026, 2, 1, 0, 0, 0, tzinfo=timezone.utc)
WINDOW_START = date(2025, 9, 1)
WINDOW_END = date(2026, 1, 31)
TENANT_ID = 1
PLAYBOOK_ID = 10
COHORT_ID = 42


def _mock_cohort(*, tenant_id: int = TENANT_ID) -> InterventionCohortModel:
    cohort = MagicMock(spec=InterventionCohortModel)
    cohort.id = COHORT_ID
    cohort.tenant_id = tenant_id
    cohort.playbook_id = PLAYBOOK_ID
    cohort.cohort_name = "Q1-2026-dropout-intervention"
    cohort.analysis_window_start = WINDOW_START
    cohort.analysis_window_end = WINDOW_END
    cohort.student_count = 50
    cohort.data_completeness_pct = Decimal("94.00")
    cohort.created_by = "program_manager@example.com"
    cohort.created_at = MOCK_NOW
    return cohort


def _mock_outcome(
    outcome_type: InterventionCohortOutcomeType,
    uplift: Decimal,
) -> InterventionCohortOutcomeModel:
    outcome = MagicMock(spec=InterventionCohortOutcomeModel)
    outcome.id = 200
    outcome.tenant_id = TENANT_ID
    outcome.cohort_id = COHORT_ID
    outcome.outcome_type = outcome_type
    outcome.segment_name = None
    outcome.outcome_value_treated = Decimal("0.1400")
    outcome.outcome_value_control = Decimal("0.1800")
    outcome.uplift_pp = uplift
    outcome.measurement_completeness_pct = Decimal("94.00")
    outcome.measured_at = MOCK_NOW
    return outcome


def _make_svc(*, scalar_return=None, scalars_list=None) -> InterventionEffectivenessService:
    db = MagicMock()
    db.scalar.return_value = scalar_return
    scalars_mock = MagicMock()
    scalars_mock.__iter__ = MagicMock(return_value=iter(scalars_list or []))
    db.scalars.return_value = scalars_mock
    return InterventionEffectivenessService(db=db)


# ---------------------------------------------------------------------------
# finalize_cohort: unfrozen behaviour (F3.3 unfreeze complete 2026-04-17)
# ---------------------------------------------------------------------------

class TestFinalizeCohortUnfrozen:
    """finalize_cohort executes business logic after F3.3 unfreeze."""

    def _payload(self) -> CohortFinalizeRequestSchema:
        return CohortFinalizeRequestSchema(
            playbook_id=PLAYBOOK_ID,
            cohort_name="Q1-2026-dropout-intervention",
            analysis_window_start=WINDOW_START,
            analysis_window_end=WINDOW_END,
        )

    def test_creates_cohort_for_valid_tenant(self) -> None:
        svc = _make_svc()
        result = svc.finalize_cohort(tenant_id=TENANT_ID, actor="pm@example.com", payload=self._payload())
        assert result.tenant_id == TENANT_ID
        assert result.playbook_id == PLAYBOOK_ID

    def test_calls_db_add_and_flush(self) -> None:
        """DB should be called when creating a cohort."""
        db = MagicMock()
        svc = InterventionEffectivenessService(db=db)
        svc.finalize_cohort(tenant_id=TENANT_ID, actor="pm@example.com", payload=self._payload())
        db.add.assert_called_once()
        db.flush.assert_called_once()

    def test_tenant_zero_rejected(self) -> None:
        svc = _make_svc()
        with pytest.raises(TenantRequiredError):
            svc.finalize_cohort(tenant_id=0, actor="pm@example.com", payload=self._payload())


# ---------------------------------------------------------------------------
# analyze_cohort: unfrozen behaviour (F3.3 unfreeze complete 2026-04-17)
# ---------------------------------------------------------------------------

class TestAnalyzeCohortUnfrozen:
    def test_queues_analysis_for_existing_cohort(self) -> None:
        cohort = _mock_cohort()
        svc = _make_svc(scalar_return=cohort)
        payload = CohortAnalyzeRequestSchema(segment_keys=[])
        result = svc.analyze_cohort(tenant_id=TENANT_ID, cohort_id=COHORT_ID, actor="pm@example.com", payload=payload)
        assert result["status"] == "analysis_queued"
        assert result["cohort_id"] == COHORT_ID

    def test_raises_not_found_for_missing_cohort(self) -> None:
        svc = _make_svc(scalar_return=None)
        payload = CohortAnalyzeRequestSchema(segment_keys=[])
        with pytest.raises(TenantResourceNotFoundError):
            svc.analyze_cohort(tenant_id=TENANT_ID, cohort_id=9999, actor="pm@example.com", payload=payload)


# ---------------------------------------------------------------------------
# get_outcomes: successful read path
# ---------------------------------------------------------------------------

class TestGetOutcomes:
    def test_returns_two_outcomes(self) -> None:
        cohort = _mock_cohort()
        outcomes = [
            _mock_outcome(InterventionCohortOutcomeType.DROPOUT_RATE, Decimal("-4.000")),
            _mock_outcome(InterventionCohortOutcomeType.GPA_IMPROVEMENT, Decimal("0.070")),
        ]
        svc = _make_svc(scalar_return=cohort, scalars_list=outcomes)
        result = svc.get_outcomes(tenant_id=TENANT_ID, cohort_id=COHORT_ID)
        assert len(result) == 2

    def test_returns_empty_list_when_no_outcomes(self) -> None:
        cohort = _mock_cohort()
        svc = _make_svc(scalar_return=cohort, scalars_list=[])
        result = svc.get_outcomes(tenant_id=TENANT_ID, cohort_id=COHORT_ID)
        assert result == []

    def test_raises_not_found_for_absent_cohort(self) -> None:
        svc = _make_svc(scalar_return=None)
        with pytest.raises(TenantResourceNotFoundError, match="not found"):
            svc.get_outcomes(tenant_id=TENANT_ID, cohort_id=99)

    def test_cross_tenant_cohort_raises(self) -> None:
        """Cohort belonging to tenant_id=2 must not be readable by tenant_id=1."""
        cohort = _mock_cohort(tenant_id=2)
        svc = _make_svc(scalar_return=cohort)
        with pytest.raises(Exception):  # TenantResourceNotFoundError or equivalent
            svc.get_outcomes(tenant_id=TENANT_ID, cohort_id=COHORT_ID)


# ---------------------------------------------------------------------------
# get_latest_by_playbook
# ---------------------------------------------------------------------------

class TestGetLatestByPlaybook:
    def test_returns_cohort_for_playbook(self) -> None:
        cohort = _mock_cohort()
        svc = _make_svc(scalar_return=cohort)
        result = svc.get_latest_by_playbook(tenant_id=TENANT_ID, playbook_id=PLAYBOOK_ID)
        assert result.id == COHORT_ID

    def test_raises_not_found_for_unknown_playbook(self) -> None:
        svc = _make_svc(scalar_return=None)
        with pytest.raises(TenantResourceNotFoundError, match="No cohort found"):
            svc.get_latest_by_playbook(tenant_id=TENANT_ID, playbook_id=999)

    def test_tenant_zero_rejected(self) -> None:
        svc = _make_svc()
        with pytest.raises(TenantRequiredError):
            svc.get_latest_by_playbook(tenant_id=0, playbook_id=PLAYBOOK_ID)


# ---------------------------------------------------------------------------
# Scenario: full F1→F3 lookup chain (mocked)
# ---------------------------------------------------------------------------

class TestF1ToF3MockedChain:
    """
    Simulates the data flow from F1 risk snapshot → F2 playbook execution → F3 cohort outcome.
    All external calls (F1 risk service, F2 playbook service) are mocked.

    This test validates that the F3 service layer correctly:
    1. Resolves tenant context
    2. Queries the correct cohort by playbook_id
    3. Returns outcome metrics without cross-tenant contamination
    """

    def test_programmatic_lookup_returns_correct_cohort(self) -> None:
        cohort = _mock_cohort()
        outcome = _mock_outcome(InterventionCohortOutcomeType.DROPOUT_RATE, Decimal("-4.000"))

        db = MagicMock()
        db.scalar.return_value = cohort
        scalars_mock = MagicMock()
        scalars_mock.__iter__ = MagicMock(return_value=iter([outcome]))
        db.scalars.return_value = scalars_mock

        svc = InterventionEffectivenessService(db=db)

        # Step 1: locate cohort by playbook_id
        found_cohort = svc.get_latest_by_playbook(tenant_id=TENANT_ID, playbook_id=PLAYBOOK_ID)
        assert found_cohort.id == COHORT_ID

        # Step 2: retrieve outcomes
        db.scalar.return_value = cohort  # reset for get_outcomes query
        outcomes = svc.get_outcomes(tenant_id=TENANT_ID, cohort_id=found_cohort.id)
        assert len(outcomes) == 1
        assert outcomes[0].outcome_type == InterventionCohortOutcomeType.DROPOUT_RATE
        assert outcomes[0].uplift_pp == Decimal("-4.000")
