from app.modules.interventions.effectiveness_models import (
    InterventionCohortMemberModel,
    InterventionCohortModel,
    InterventionCohortOutcomeModel,
    InterventionCohortOutcomeType,
)


def test_f3_outcome_enum_contains_expected_values() -> None:
    assert InterventionCohortOutcomeType.DROPOUT_RATE.value == "dropout_rate"
    assert InterventionCohortOutcomeType.GPA_IMPROVEMENT.value == "gpa_improvement"
    assert InterventionCohortOutcomeType.COURSE_COMPLETION_RATE.value == "course_completion_rate"
    assert InterventionCohortOutcomeType.PERSISTENCE_RATE.value == "persistence_rate"


def test_f3_models_table_names_are_stable() -> None:
    assert InterventionCohortModel.__tablename__ == "app_intervention_cohorts"
    assert InterventionCohortMemberModel.__tablename__ == "app_intervention_cohort_members"
    assert InterventionCohortOutcomeModel.__tablename__ == "app_intervention_cohort_outcomes"


def test_f3_cohort_outcomes_have_required_columns() -> None:
    columns = InterventionCohortOutcomeModel.__table__.columns.keys()
    assert "cohort_id" in columns
    assert "outcome_type" in columns
    assert "uplift_pp" in columns
    assert "measurement_completeness_pct" in columns
