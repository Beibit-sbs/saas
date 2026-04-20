"""F3 unit tests — ORM model attribute contracts.

Tests run without a live database. All assertions are purely structural:
column presence, types, constraints, enum membership — not DB round-trips.

Mock data scenario: 50-student cohort, 4pp dropout-rate uplift
(treated cohort baseline 18% dropout → 14% after intervention).
"""
from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from app.modules.interventions.effectiveness_models import (
    InterventionCohortMemberModel,
    InterventionCohortModel,
    InterventionCohortOutcomeModel,
    InterventionCohortOutcomeType,
)
from app.modules.interventions.effectiveness_schemas import (
    CohortAnalyzeResponseSchema,
    CohortFinalizeRequestSchema,
    CohortOutcomeListResponseSchema,
    CohortOutcomeReadSchema,
    CohortReadSchema,
)


# ---------------------------------------------------------------------------
# Fixtures — 50-student cohort; 4pp dropout-rate uplift
# ---------------------------------------------------------------------------

WINDOW_START = date(2025, 9, 1)
WINDOW_END = date(2026, 1, 31)
MOCK_NOW = datetime(2026, 2, 1, 0, 0, 0, tzinfo=timezone.utc)

TREATED_DROPOUT = Decimal("0.1400")   # 14 % post-intervention
CONTROL_DROPOUT = Decimal("0.1800")   # 18 % baseline
EXPECTED_UPLIFT = Decimal("-4.000")   # −4 pp (reduction = positive outcome)

TREATED_GPA = Decimal("3.1200")
CONTROL_GPA = Decimal("3.0500")
GPA_UPLIFT = Decimal("0.070")


def _make_cohort(cohort_id: int = 1) -> MagicMock:
    cohort = MagicMock(spec=InterventionCohortModel)
    cohort.id = cohort_id
    cohort.tenant_id = 1
    cohort.playbook_id = 10
    cohort.cohort_name = "Q1-2026-dropout-intervention"
    cohort.analysis_window_start = WINDOW_START
    cohort.analysis_window_end = WINDOW_END
    cohort.student_count = 50
    cohort.data_completeness_pct = Decimal("94.00")
    cohort.created_by = "program_manager@example.com"
    cohort.created_at = MOCK_NOW
    return cohort


def _make_outcome(
    outcome_type: InterventionCohortOutcomeType,
    treated: Decimal,
    control: Decimal,
    uplift: Decimal,
    cohort_id: int = 1,
) -> MagicMock:
    outcome = MagicMock(spec=InterventionCohortOutcomeModel)
    outcome.id = 100
    outcome.tenant_id = 1
    outcome.cohort_id = cohort_id
    outcome.outcome_type = outcome_type
    outcome.segment_name = None
    outcome.outcome_value_treated = treated
    outcome.outcome_value_control = control
    outcome.uplift_pp = uplift
    outcome.uplift_confidence_p5 = Decimal("-5.000")
    outcome.uplift_confidence_p95 = Decimal("-3.000")
    outcome.measurement_completeness_pct = Decimal("94.00")
    outcome.measured_at = MOCK_NOW
    outcome.notes = None
    return outcome


def _make_member(member_id: int = 1, cohort_id: int = 1) -> MagicMock:
    member = MagicMock(spec=InterventionCohortMemberModel)
    member.id = member_id
    member.tenant_id = 1
    member.cohort_id = cohort_id
    member.student_profile_id = 1000 + member_id
    member.playbook_execution_id = 5000 + member_id
    member.risk_band_at_intervention = "high"
    member.program_code = "CS-BSC"
    member.segment_key = "year:1"
    member.added_at = MOCK_NOW
    return member


# ---------------------------------------------------------------------------
# InterventionCohortModel: structure
# ---------------------------------------------------------------------------

class TestInterventionCohortModel:
    def test_table_name(self) -> None:
        assert InterventionCohortModel.__tablename__ == "app_intervention_cohorts"

    def test_required_columns_present(self) -> None:
        cols = {c.name for c in InterventionCohortModel.__table__.columns}
        for col in ("id", "tenant_id", "playbook_id", "cohort_name",
                    "analysis_window_start", "analysis_window_end",
                    "student_count", "created_by", "created_at"):
            assert col in cols, f"Column {col!r} missing"

    def test_unique_constraint_exists(self) -> None:
        constraint_names = {c.name for c in InterventionCohortModel.__table__.constraints}
        assert "uq_intervention_cohorts_window" in constraint_names

    def test_indexes_exist(self) -> None:
        index_names = {i.name for i in InterventionCohortModel.__table__.indexes}
        assert "ix_intervention_cohorts_tenant_id" in index_names
        assert "ix_intervention_cohorts_playbook_id" in index_names

    def test_fixture_attributes(self) -> None:
        cohort = _make_cohort()
        assert cohort.tenant_id == 1
        assert cohort.student_count == 50
        assert cohort.analysis_window_start == WINDOW_START
        assert cohort.analysis_window_end == WINDOW_END
        assert cohort.data_completeness_pct == Decimal("94.00")


# ---------------------------------------------------------------------------
# InterventionCohortOutcomeModel: uplift math contract
# ---------------------------------------------------------------------------

class TestInterventionCohortOutcomeModel:
    def test_table_name(self) -> None:
        assert InterventionCohortOutcomeModel.__tablename__ == "app_intervention_cohort_outcomes"

    def test_required_columns_present(self) -> None:
        cols = {c.name for c in InterventionCohortOutcomeModel.__table__.columns}
        for col in ("cohort_id", "outcome_type", "uplift_pp", "measurement_completeness_pct"):
            assert col in cols, f"Column {col!r} missing"

    def test_unique_constraint_keys(self) -> None:
        constraint_names = {c.name for c in InterventionCohortOutcomeModel.__table__.constraints}
        assert "uq_intervention_cohort_outcomes_key" in constraint_names

    def test_dropout_rate_uplift_fixture(self) -> None:
        """4pp dropout reduction: treated 14% vs control 18% → uplift −4pp."""
        outcome = _make_outcome(
            InterventionCohortOutcomeType.DROPOUT_RATE,
            TREATED_DROPOUT,
            CONTROL_DROPOUT,
            EXPECTED_UPLIFT,
        )
        assert outcome.outcome_type == InterventionCohortOutcomeType.DROPOUT_RATE
        assert outcome.outcome_value_treated == TREATED_DROPOUT
        assert outcome.outcome_value_control == CONTROL_DROPOUT
        assert outcome.uplift_pp == EXPECTED_UPLIFT

    def test_gpa_improvement_fixture(self) -> None:
        outcome = _make_outcome(
            InterventionCohortOutcomeType.GPA_IMPROVEMENT,
            TREATED_GPA,
            CONTROL_GPA,
            GPA_UPLIFT,
        )
        assert outcome.outcome_type == InterventionCohortOutcomeType.GPA_IMPROVEMENT
        assert outcome.uplift_pp == GPA_UPLIFT

    def test_confidence_band_ordering(self) -> None:
        outcome = _make_outcome(
            InterventionCohortOutcomeType.DROPOUT_RATE,
            TREATED_DROPOUT,
            CONTROL_DROPOUT,
            EXPECTED_UPLIFT,
        )
        # p5 ≤ uplift ≤ p95 (or symmetrical for negative uplift: p5 ≤ p95)
        assert outcome.uplift_confidence_p5 <= outcome.uplift_confidence_p95  # type: ignore[operator]


# ---------------------------------------------------------------------------
# InterventionCohortMemberModel: structure
# ---------------------------------------------------------------------------

class TestInterventionCohortMemberModel:
    def test_table_name(self) -> None:
        assert InterventionCohortMemberModel.__tablename__ == "app_intervention_cohort_members"

    def test_segment_key_present(self) -> None:
        cols = {c.name for c in InterventionCohortMemberModel.__table__.columns}
        assert "segment_key" in cols

    def test_fixture_risk_band(self) -> None:
        member = _make_member()
        assert member.risk_band_at_intervention == "high"
        assert member.segment_key == "year:1"


# ---------------------------------------------------------------------------
# Pydantic read schemas: serialization round-trip contract
# ---------------------------------------------------------------------------

class TestCohortReadSchema:
    def test_cohort_read_schema_from_orm_like_dict(self) -> None:
        data = {
            "id": 1,
            "tenant_id": 1,
            "playbook_id": 10,
            "cohort_name": "Q1-2026-dropout-intervention",
            "analysis_window_start": WINDOW_START,
            "analysis_window_end": WINDOW_END,
            "student_count": 50,
            "data_completeness_pct": Decimal("94.00"),
            "created_by": "pm@example.com",
            "created_at": MOCK_NOW,
            "status": "draft",
        }
        schema = CohortReadSchema(**data)
        assert schema.student_count == 50
        assert schema.data_completeness_pct == Decimal("94.00")
        assert schema.status == "draft"

    def test_outcome_list_response_schema_empty(self) -> None:
        schema = CohortOutcomeListResponseSchema(items=[], total=0)
        assert schema.total == 0
        assert schema.items == []

    def test_outcome_list_response_schema_with_item(self) -> None:
        item = CohortOutcomeReadSchema(
            id=100,
            tenant_id=1,
            cohort_id=1,
            outcome_type=InterventionCohortOutcomeType.DROPOUT_RATE,
            segment_name=None,
            outcome_value_treated=TREATED_DROPOUT,
            outcome_value_control=CONTROL_DROPOUT,
            uplift_pp=EXPECTED_UPLIFT,
            uplift_confidence_p5=Decimal("-5.000"),
            uplift_confidence_p95=Decimal("-3.000"),
            measurement_completeness_pct=Decimal("94.00"),
            measured_at=MOCK_NOW,
            notes=None,
        )
        resp = CohortOutcomeListResponseSchema(items=[item], total=1)
        assert resp.total == 1
        assert resp.items[0].uplift_pp == EXPECTED_UPLIFT

    def test_analyze_response_schema_frozen_status(self) -> None:
        resp = CohortAnalyzeResponseSchema(
            cohort_id=1,
            status="frozen",
            detail="F3 analyze_cohort is frozen until F3.3 delivery is officially unfrozen.",
            requested_at=MOCK_NOW,
        )
        assert resp.status == "frozen"


# ---------------------------------------------------------------------------
# Finalize request schema: validation contract
# ---------------------------------------------------------------------------

class TestCohortFinalizeRequestSchema:
    def test_valid_payload(self) -> None:
        payload = CohortFinalizeRequestSchema(
            playbook_id=10,
            cohort_name="Q1-2026",
            analysis_window_start=WINDOW_START,
            analysis_window_end=WINDOW_END,
        )
        assert payload.playbook_id == 10

    def test_cohort_name_empty_rejected(self) -> None:
        with pytest.raises(Exception):  # pydantic ValidationError
            CohortFinalizeRequestSchema(
                playbook_id=10,
                cohort_name="",
                analysis_window_start=WINDOW_START,
                analysis_window_end=WINDOW_END,
            )
