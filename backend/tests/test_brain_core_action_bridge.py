"""Regression tests for Brain Core → Module action callback bridge.

Verifies that:
1. ``wire_action_handlers`` registers a real handler for ``create_intervention_case``
   on the ActionDispatcher when a session_factory is provided.
2. The registered handler calls ``session.add()`` with an InterventionCaseModel
   (proves real DB objects are created, not just in-memory stubs).
3. When ``session_factory=None`` (test/CI mode) the function is a no-op and
   the dispatcher's built-in in-memory sink remains active.
4. Failures in the handler (e.g. DB errors) are caught and returned as
   ``{"status": "failed", ...}`` without propagating exceptions.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch


from app.modules.brain_core.action_bridge import (
    _make_create_intervention_case_handler,
    _make_create_student_support_case_handler,
    wire_action_handlers,
)
from app.modules.interventions.models import (
    InterventionCaseModel,
    InterventionCaseSeverity,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_mock_session_factory(side_effect: Exception | None = None):
    """Return a callable that produces a mock SQLAlchemy session."""
    session = MagicMock()
    if side_effect:
        session.commit.side_effect = side_effect
    factory = MagicMock(return_value=session)
    return factory, session


# ---------------------------------------------------------------------------
# wire_action_handlers
# ---------------------------------------------------------------------------


class TestWireActionHandlers:
    def test_noop_when_no_session_factory(self):
        """With session_factory=None the function must not register any handler."""
        dispatcher = MagicMock()
        wire_action_handlers(dispatcher=dispatcher, session_factory=None)
        dispatcher.register_module_handler.assert_not_called()

    def test_registers_create_intervention_case(self):
        """Providing a session_factory registers intervention + module handlers."""
        factory, _ = _make_mock_session_factory()
        dispatcher = MagicMock()
        wire_action_handlers(dispatcher=dispatcher, session_factory=factory)
        assert dispatcher.register_module_handler.call_count >= 19
        registered_names = [call.args[0] for call in dispatcher.register_module_handler.call_args_list]
        assert "create_intervention_case" in registered_names
        assert "create_student_support_case" in registered_names
        assert "create_disciplinary_review_case" in registered_names
        assert "create_supervision_task" in registered_names
        assert "create_collections_case" in registered_names
        assert "create_financial_aid_review" in registered_names
        assert "create_housing_request" in registered_names
        assert "create_alumni_engagement_task" in registered_names
        assert "create_career_opportunity" in registered_names
        assert "create_hr_review_case" in registered_names
        assert "create_facilities_work_order" in registered_names
        assert "create_asset_inspection" in registered_names
        assert "create_ethics_review" in registered_names
        assert "create_equipment_booking" in registered_names
        assert "create_scholarship_review" in registered_names
        assert "create_transport_disruption_alert" in registered_names
        assert "create_ip_asset_record" in registered_names
        assert "create_sla_breach_record" in registered_names


class TestMakeCreateStudentSupportCaseHandler:
    def test_returns_created_status_and_calls_entity_create(self):
        handler = _make_create_student_support_case_handler()

        with patch(
            "app.modules.university_core.tenant_entity_service.create_entity_for_tenant",
            return_value={"id": 55},
        ) as create_mock:
            result = handler(
                tenant_id=3,
                decision_id="dec-student-1",
                payload={"student_id": "ST-100", "event_type": "academic.attendance_risk.detected"},
            )

        assert result["status"] == "created"
        assert result["item"]["source"] == "student_life_module"
        create_mock.assert_called_once()
        args = create_mock.call_args.args
        assert args[0] == "student_life_counseling_cases"
        assert args[2] == 3
        assert args[1]["student_id"] == "ST-100"
        assert args[1]["status"] == "open"

    def test_returns_failed_when_student_id_missing(self):
        handler = _make_create_student_support_case_handler()

        with patch("app.modules.university_core.tenant_entity_service.create_entity_for_tenant") as create_mock:
            result = handler(tenant_id=3, decision_id="dec-student-2", payload={})

        assert result["status"] == "failed"
        assert "student_id" in result["reason"]
        create_mock.assert_not_called()


# ---------------------------------------------------------------------------
# _make_create_intervention_case_handler
# ---------------------------------------------------------------------------


class TestMakeCreateInterventionCaseHandler:
    def _run(
        self,
        payload: dict[str, Any] | None = None,
        *,
        side_effect: Exception | None = None,
    ):
        factory, session = _make_mock_session_factory(side_effect=side_effect)
        # Make session.refresh() populate case.id so the return dict can be built
        fake_case = MagicMock(spec=InterventionCaseModel)
        fake_case.id = 42
        session.add.side_effect = lambda obj: setattr(obj, "id", 42)
        session.refresh.return_value = None

        handler = _make_create_intervention_case_handler(factory)
        result = handler(tenant_id=1, decision_id="dec-001", payload=payload or {})
        return result, session

    def test_returns_created_status_on_success(self):
        result, _ = self._run()
        assert result["status"] == "created"
        assert result["item"]["source"] == "real_db"

    def test_session_add_called_with_intervention_model(self):
        _, session = self._run(payload={"risk_level": "high", "student_id": 7})
        assert session.add.called
        added_obj = session.add.call_args[0][0]
        assert isinstance(added_obj, InterventionCaseModel)

    def test_severity_mapped_from_payload(self):
        _, session = self._run(payload={"risk_level": "low"})
        added_obj = session.add.call_args[0][0]
        assert added_obj.severity == InterventionCaseSeverity.LOW

    def test_severity_defaults_to_medium_for_unknown_level(self):
        _, session = self._run(payload={"risk_level": "critical"})
        added_obj = session.add.call_args[0][0]
        assert added_obj.severity == InterventionCaseSeverity.MEDIUM

    def test_student_profile_id_set(self):
        _, session = self._run(payload={"student_id": 99})
        added_obj = session.add.call_args[0][0]
        assert added_obj.student_profile_id == 99

    def test_student_profile_id_none_when_not_provided(self):
        _, session = self._run(payload={})
        added_obj = session.add.call_args[0][0]
        assert added_obj.student_profile_id is None

    def test_session_commit_and_close_called(self):
        _, session = self._run()
        session.commit.assert_called_once()
        session.close.assert_called_once()

    def test_db_error_returns_failed_status(self):
        result, session = self._run(side_effect=RuntimeError("db exploded"))
        assert result["status"] == "failed"
        assert "db exploded" in result["reason"]
        session.rollback.assert_called_once()
        session.close.assert_called_once()

    def test_metadata_contains_brain_decision_id(self):
        _, session = self._run(payload={})
        added_obj = session.add.call_args[0][0]
        assert added_obj.metadata_json.get("decision_id") == "dec-001"
        assert added_obj.metadata_json.get("source") == "brain_core"

    def test_due_at_after_opened_at(self):
        """Ensure the DB check constraint due_at >= opened_at is always satisfied."""
        _, session = self._run()
        added_obj = session.add.call_args[0][0]
        assert added_obj.due_at > added_obj.opened_at


# ---------------------------------------------------------------------------
# Dispatcher integration: module handler takes priority over in-memory sink
# ---------------------------------------------------------------------------


class TestDispatcherModuleHandlerPriority:
    """Verify that registered module handlers run instead of built-in sinks."""

    def test_registered_handler_called_not_in_memory_sink(self):
        """When a module handler is registered for ``create_intervention_case``,
        the dispatcher calls it and does NOT fall through to the in-memory workflow.
        """
        from app.modules.brain_core.actions.dispatcher import ActionDispatcher

        real_handler_calls: list[tuple] = []

        def real_handler(tenant_id: int, decision_id: str, payload: dict) -> dict:
            real_handler_calls.append((tenant_id, decision_id, payload))
            return {"status": "ok", "source": "module_handler"}

        dispatcher = ActionDispatcher()
        dispatcher.register_module_handler("create_intervention_case", real_handler)

        # Patch the in-memory workflow to detect if it is wrongly called
        dispatcher._workflow.create_intervention_case = MagicMock(
            return_value={"status": "in_memory"}
        )

        results = dispatcher.dispatch(
            tenant_id=1,
            decision_id="dec-999",
            actions=[
                {
                    "name": "create_intervention_case",
                    "action_type": "workflow_task",
                    "requires_approval": False,
                    "payload": {"student_id": 5, "risk_level": "high"},
                }
            ],
        )

        # Module handler must have been invoked
        assert len(real_handler_calls) == 1
        assert real_handler_calls[0][0] == 1
        assert real_handler_calls[0][1] == "dec-999"

        # In-memory stub must NOT have been called
        dispatcher._workflow.create_intervention_case.assert_not_called()

        # Result must reflect the module handler's return value (keys merged at top level)
        assert results[0]["source"] == "module_handler"

    def test_registered_student_support_handler_called_not_in_memory_sink(self):
        """Registered handler for student support must take priority over in-memory sink."""
        from app.modules.brain_core.actions.dispatcher import ActionDispatcher

        real_handler_calls: list[tuple] = []

        def real_handler(tenant_id: int, decision_id: str, payload: dict) -> dict:
            real_handler_calls.append((tenant_id, decision_id, payload))
            return {"status": "ok", "source": "student_life_handler"}

        dispatcher = ActionDispatcher()
        dispatcher.register_module_handler("create_student_support_case", real_handler)

        dispatcher._workflow.create_student_support_case = MagicMock(
            return_value={"status": "in_memory"}
        )

        results = dispatcher.dispatch(
            tenant_id=2,
            decision_id="dec-student-77",
            actions=[
                {
                    "name": "create_student_support_case",
                    "action_type": "workflow_task",
                    "requires_approval": False,
                    "payload": {"student_id": "ST-9", "event_type": "academic.attendance_risk.detected"},
                }
            ],
        )

        assert len(real_handler_calls) == 1
        assert real_handler_calls[0][0] == 2
        assert real_handler_calls[0][1] == "dec-student-77"
        dispatcher._workflow.create_student_support_case.assert_not_called()
        assert results[0]["source"] == "student_life_handler"

    def test_in_memory_sink_used_when_no_module_handler_registered(self):
        """Without wiring, the original in-memory sink remains active."""
        from app.modules.brain_core.actions.dispatcher import ActionDispatcher

        dispatcher = ActionDispatcher()
        # Override the in-memory workflow method to a simple stub
        dispatcher._workflow.create_intervention_case = MagicMock(
            return_value={"status": "in_memory_ok", "item": {"id": "stub"}}
        )

        results = dispatcher.dispatch(
            tenant_id=1,
            decision_id="dec-000",
            actions=[
                {
                    "name": "create_intervention_case",
                    "action_type": "workflow_task",
                    "requires_approval": False,
                    "payload": {},
                }
            ],
        )

        dispatcher._workflow.create_intervention_case.assert_called_once()
        assert results[0]["status"] == "in_memory_ok"
