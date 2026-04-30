"""Week 8 — Observability + Performance tests.

DoD coverage:
- Brain Prometheus counter functions increment correctly
- render_metrics() includes brain_signals_emitted_total / brain_decisions_total /
  brain_actions_dispatched_total
- list_entities_impl() respects max_limit=200 (memory fallback path)
- Alembic migration pg45qr67st89 is syntactically importable
"""
from __future__ import annotations



from app.modules.observability.metrics import (
    clear_metrics_state,
    record_brain_action_dispatched,
    record_brain_decision_made,
    record_brain_signal_emitted,
    render_metrics,
)


# ---------------------------------------------------------------------------
# Brain counter — increment helpers
# ---------------------------------------------------------------------------

class TestBrainCounters:
    def setup_method(self) -> None:
        clear_metrics_state()

    def test_brain_signal_emitted_appears_in_render(self) -> None:
        record_brain_signal_emitted(tenant_id=42)
        output = render_metrics()
        assert "brain_signals_emitted_total" in output
        assert 'tenant_id="42"' in output

    def test_brain_decision_made_appears_in_render(self) -> None:
        record_brain_decision_made(tenant_id=10, decision_type="risk")
        output = render_metrics()
        assert "brain_decisions_total" in output
        assert 'decision_type="risk"' in output

    def test_brain_action_dispatched_success_appears_in_render(self) -> None:
        record_brain_action_dispatched(tenant_id=5, status="success")
        output = render_metrics()
        assert "brain_actions_dispatched_total" in output
        assert 'status="success"' in output

    def test_brain_action_dispatched_failure_appears_in_render(self) -> None:
        record_brain_action_dispatched(tenant_id=5, status="failure")
        output = render_metrics()
        assert 'status="failure"' in output

    def test_multiple_tenants_tracked_separately(self) -> None:
        record_brain_signal_emitted(tenant_id=1)
        record_brain_signal_emitted(tenant_id=2)
        record_brain_signal_emitted(tenant_id=2)
        output = render_metrics()
        lines = [ln for ln in output.splitlines() if "brain_signals_emitted_total" in ln and "{" in ln]
        # Both tenants must appear
        assert any('tenant_id="1"' in ln for ln in lines)
        assert any('tenant_id="2"' in ln for ln in lines)

    def test_counter_accumulates_across_calls(self) -> None:
        for _ in range(5):
            record_brain_decision_made(tenant_id=7, decision_type="preventive")
        output = render_metrics()
        lines = [ln for ln in output.splitlines() if "brain_decisions_total" in ln and 'tenant_id="7"' in ln]
        assert lines, "Expected brain_decisions_total line for tenant 7"
        count = int(lines[0].split()[-1])
        assert count == 5

    def test_clear_metrics_resets_brain_counters(self) -> None:
        record_brain_signal_emitted(tenant_id=99)
        clear_metrics_state()
        output = render_metrics()
        lines = [ln for ln in output.splitlines() if "brain_signals_emitted_total{" in ln]
        assert not lines, "Brain signal counter should be empty after clear"

    def test_none_tenant_defaults_to_dash(self) -> None:
        record_brain_signal_emitted(tenant_id=None)
        output = render_metrics()
        assert 'tenant_id="-"' in output


# ---------------------------------------------------------------------------
# render_metrics — Brain section present even with zero data
# ---------------------------------------------------------------------------

class TestRenderMetricsBrainSection:
    def setup_method(self) -> None:
        clear_metrics_state()

    def test_help_lines_always_present(self) -> None:
        output = render_metrics()
        assert "# HELP brain_signals_emitted_total" in output
        assert "# HELP brain_decisions_total" in output
        assert "# HELP brain_actions_dispatched_total" in output

    def test_type_lines_always_present(self) -> None:
        output = render_metrics()
        assert "# TYPE brain_signals_emitted_total counter" in output
        assert "# TYPE brain_decisions_total counter" in output
        assert "# TYPE brain_actions_dispatched_total counter" in output


# ---------------------------------------------------------------------------
# Pagination — list_entities_impl memory-fallback path
# ---------------------------------------------------------------------------

class TestEntityListPagination:
    def test_max_limit_caps_result_in_memory_fallback(self) -> None:
        import app.modules.university_core.shared as shared
        from app.modules.university_core.entity_impl import list_entities_impl

        entity = "students"
        with shared._state_lock:
            shared._state.data[entity].clear()
            shared._state.counters[entity] = 0
            for i in range(1, 6):
                shared._state.data[entity][i] = {
                    "id": i,
                    "name": f"Student {i}",
                    "email": f"s{i}@uni.edu",
                    "tenant_id": 1,
                    "program": "CS",
                    "created_at": "2026-01-01T00:00:00+00:00",
                }

        # Ensure memory fallback (no DB URL)
        import unittest.mock as mock
        with mock.patch(
            "app.modules.university_core.entity_impl._db_url_impl",
            return_value=None,
        ):
            results = list_entities_impl(entity, max_limit=3)

        assert len(results) == 3, f"Expected 3, got {len(results)}"

    def test_max_limit_default_200_does_not_truncate_small_dataset(self) -> None:
        import app.modules.university_core.shared as shared
        from app.modules.university_core.entity_impl import list_entities_impl

        entity = "students"
        with shared._state_lock:
            shared._state.data[entity].clear()
            shared._state.counters[entity] = 0
            for i in range(1, 6):
                shared._state.data[entity][i] = {
                    "id": i,
                    "name": f"Student {i}",
                    "email": f"s{i}@uni.edu",
                    "tenant_id": 1,
                    "program": "CS",
                    "created_at": "2026-01-01T00:00:00+00:00",
                }

        import unittest.mock as mock
        with mock.patch(
            "app.modules.university_core.entity_impl._db_url_impl",
            return_value=None,
        ):
            results = list_entities_impl(entity)

        assert len(results) == 5, "Default max_limit=200 must return all 5 rows"


# ---------------------------------------------------------------------------
# Alembic migration importability
# ---------------------------------------------------------------------------

class TestAlembicMigrationRetention:
    def test_migration_pg45qr67st89_importable(self) -> None:
        import importlib.util
        import pathlib

        migration_path = pathlib.Path(__file__).parent.parent / "alembic" / "versions" / "pg45qr67st89_add_audit_events_retention_policy.py"
        spec = importlib.util.spec_from_file_location("pg45qr67st89_migration", migration_path)
        assert spec is not None, f"Migration file not found at {migration_path}"
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)  # type: ignore[union-attr]
        assert hasattr(mod, "upgrade")
        assert hasattr(mod, "downgrade")
        assert mod.revision == "pg45qr67st89"
        assert mod.down_revision == "of34pq56rs78"
