from __future__ import annotations

from datetime import datetime
from unittest.mock import MagicMock

import pytest

from app.modules.workflows.models import WorkflowInstanceStatus, WorkflowTaskStatus
from app.modules.workflows.workflow_engine import WorkflowRuntimeEngine


class _ScalarResult:
    def __init__(self, value):
        self._value = value

    def scalar_one_or_none(self):
        return self._value


class _ScalarsResult:
    def __init__(self, values):
        self._values = list(values)

    def scalars(self):
        return self

    def all(self):
        return list(self._values)


def test_workflow_status_enums_include_failed_and_timed_out() -> None:
    assert WorkflowInstanceStatus.FAILED.value == "failed"
    assert WorkflowInstanceStatus.TIMED_OUT.value == "timed_out"
    assert WorkflowTaskStatus.FAILED.value == "failed"
    assert WorkflowTaskStatus.TIMED_OUT.value == "timed_out"


def test_runtime_marks_instance_failed_when_transition_missing() -> None:
    instance = MagicMock()
    instance.id = 42
    instance.tenant_id = 1
    instance.workflow_definition_version_id = 100
    instance.status = WorkflowInstanceStatus.PENDING
    instance.completed_at = None
    instance.current_step_id = 7

    db = MagicMock()
    db.execute.side_effect = [
        _ScalarResult(instance),
        _ScalarsResult([]),
        _ScalarsResult([]),
    ]

    engine = WorkflowRuntimeEngine(db)

    with pytest.raises(ValueError, match="No valid transition"):
        import asyncio

        asyncio.run(
            engine.execute_transition(
                tenant_id=1,
                workflow_instance_id=42,
                from_step_id=7,
                action_key="complete",
                actor="test-user",
            )
        )

    assert instance.status == WorkflowInstanceStatus.FAILED
    assert isinstance(instance.completed_at, datetime)
    assert instance.current_step_id is None
    db.flush.assert_called()
    db.commit.assert_called()
