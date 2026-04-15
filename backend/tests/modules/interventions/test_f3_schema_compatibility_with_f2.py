from __future__ import annotations

from pathlib import Path

from app.modules.interventions.effectiveness_models import (
    InterventionCohortMemberModel,
    InterventionCohortModel,
    InterventionCohortOutcomeModel,
)
from app.modules.interventions.playbook_models import (
    PlaybookExecutionModel,
    PlaybookModel,
    PlaybookStepExecutionModel,
    PlaybookStepModel,
)


def test_f3_migration_is_chained_to_f2_revision() -> None:
    migration_path = Path(__file__).resolve().parents[3] / "alembic" / "versions" / "f8c1d2e3a4b5_add_f3_intervention_effectiveness_schema_v1.py"
    migration_text = migration_path.read_text(encoding="utf-8")

    # F3 merges the main HEAD (b2c4d6e8f0a1) and F2 branch (a2b3c4d5e6f7).
    # Both main schema and F2 playbook tables are guaranteed to exist before F3 runs.
    assert 'down_revision = ("b2c4d6e8f0a1", "a2b3c4d5e6f7")' in migration_text


def test_f3_migration_references_f2_execution_fk() -> None:
    migration_path = Path(__file__).resolve().parents[3] / "alembic" / "versions" / "f8c1d2e3a4b5_add_f3_intervention_effectiveness_schema_v1.py"
    migration_text = migration_path.read_text(encoding="utf-8")

    assert "app_playbook_executions.id" in migration_text


def test_f3_table_names_do_not_conflict_with_f2_tables() -> None:
    f2_tables = {
        PlaybookModel.__tablename__,
        PlaybookStepModel.__tablename__,
        PlaybookExecutionModel.__tablename__,
        PlaybookStepExecutionModel.__tablename__,
    }
    f3_tables = {
        InterventionCohortModel.__tablename__,
        InterventionCohortMemberModel.__tablename__,
        InterventionCohortOutcomeModel.__tablename__,
    }

    assert f2_tables.isdisjoint(f3_tables)
