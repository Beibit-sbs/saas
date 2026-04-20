"""
Unit tests for PlaybookService (interventions/playbook_service.py).

Covers the service layer methods that are currently at 22% coverage:
- create_playbook (duplicate name, max steps, duplicate step_order, happy path)
- get_playbook / list_playbooks
- update_playbook (version mismatch, field updates)
- delete_playbook (active executions guard, happy path)
- start_execution (disabled playbook, student concurrency, case concurrency, happy)
- get_execution / list_executions (with filters)
- complete_step / skip_step / _maybe_complete_execution
- abandon_execution (already completed/abandoned guard)
"""

from __future__ import annotations

from datetime import datetime, UTC
from types import SimpleNamespace
from unittest.mock import MagicMock, patch, PropertyMock

import pytest

from app.core.module_helpers.service_validation import (
    DomainValidationError,
    OptimisticLockConflictError,
    TenantRequiredError,
    TenantResourceNotFoundError,
)
from app.modules.interventions.playbook_models import (
    PlaybookAssigneeRole,
    PlaybookExecutionStatus,
    PlaybookStepActionType,
    PlaybookStepExecutionStatus,
    PlaybookTriggerType,
)
from app.modules.interventions.playbook_schemas import (
    PlaybookCreateSchema,
    PlaybookExecutionStartSchema,
    PlaybookStepCompleteSchema,
    PlaybookStepCreateSchema,
    PlaybookStepSkipSchema,
    PlaybookUpdateSchema,
)
from app.modules.interventions.playbook_service import (
    MAX_CONCURRENT_EXECUTIONS_PER_CASE,
    MAX_CONCURRENT_EXECUTIONS_PER_STUDENT,
    MAX_PLAYBOOK_STEPS,
    PlaybookService,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_playbook(*, tenant_id: int = 1, playbook_id: int = 10, enabled: bool = True, version: int = 1):
    pb = SimpleNamespace(
        id=playbook_id,
        tenant_id=tenant_id,
        name="Test PB",
        description=None,
        enabled=enabled,
        version=version,
        steps=[],
        metadata_json={},
        created_by="actor",
        updated_by="actor",
    )
    return pb


def _make_execution(*, execution_id: int = 100, tenant_id: int = 1, status: PlaybookExecutionStatus = PlaybookExecutionStatus.IN_PROGRESS):
    return SimpleNamespace(
        id=execution_id,
        tenant_id=tenant_id,
        playbook_id=10,
        status=status,
        started_at=datetime.now(UTC),
        completed_at=None,
        abandoned_at=None,
        abandon_reason=None,
        updated_at=None,
        step_executions=[],
    )


def _make_step_exec(*, step_exec_id: int = 200, execution_id: int = 100, step_id: int = 50, status: PlaybookStepExecutionStatus = PlaybookStepExecutionStatus.PENDING):
    return SimpleNamespace(
        id=step_exec_id,
        execution_id=execution_id,
        step_id=step_id,
        status=status,
        performed_by=None,
        performed_at=None,
        outcome_note=None,
        metadata_json={},
    )


def _make_step(*, step_id: int = 50, is_mandatory: bool = True):
    return SimpleNamespace(id=step_id, is_mandatory=is_mandatory, step_order=0)


def _create_payload(name: str = "Test Playbook", steps: list | None = None) -> PlaybookCreateSchema:
    if steps is None:
        steps = [PlaybookStepCreateSchema(step_order=0, title="Step A", action_type=PlaybookStepActionType.NOTE)]
    return PlaybookCreateSchema(name=name, steps=steps)


# ---------------------------------------------------------------------------
# create_playbook
# ---------------------------------------------------------------------------


class TestCreatePlaybook:
    def test_rejects_zero_tenant(self):
        db = MagicMock()
        with pytest.raises(TenantRequiredError, match="tenant"):
            PlaybookService(db).create_playbook(tenant_id=0, actor="a", payload=_create_payload())

    def test_rejects_duplicate_name(self):
        db = MagicMock()
        db.scalar.return_value = _make_playbook()
        with pytest.raises(DomainValidationError, match="already exists"):
            PlaybookService(db).create_playbook(tenant_id=1, actor="a", payload=_create_payload())

    def test_rejects_too_many_steps(self):
        db = MagicMock()
        db.scalar.return_value = None
        steps = [
            PlaybookStepCreateSchema(step_order=i, title=f"Step {i}", action_type=PlaybookStepActionType.NOTE)
            for i in range(MAX_PLAYBOOK_STEPS + 1)
        ]
        with pytest.raises(DomainValidationError, match="max steps"):
            PlaybookService(db).create_playbook(tenant_id=1, actor="a", payload=_create_payload(steps=steps))

    def test_rejects_duplicate_step_order(self):
        db = MagicMock()
        db.scalar.return_value = None
        steps = [
            PlaybookStepCreateSchema(step_order=0, title="Step A", action_type=PlaybookStepActionType.NOTE),
            PlaybookStepCreateSchema(step_order=0, title="Step B", action_type=PlaybookStepActionType.ESCALATION),
        ]
        with pytest.raises(DomainValidationError, match="duplicate step_order"):
            PlaybookService(db).create_playbook(tenant_id=1, actor="a", payload=_create_payload(steps=steps))

    @patch("app.modules.interventions.playbook_service.log_admin_action")
    def test_happy_path_creates_and_audits(self, mock_audit):
        db = MagicMock()
        db.scalar.return_value = None
        # After db.add + db.flush, playbook gets id
        created_playbook = MagicMock()
        created_playbook.id = 42
        created_playbook.name = "Test Playbook"
        db.add.side_effect = None
        db.flush.side_effect = None

        # We need the service to actually create model instances — mock the model constructor
        # Just verify it doesn't raise
        service = PlaybookService(db)
        steps = [PlaybookStepCreateSchema(step_order=0, title="Step A", action_type=PlaybookStepActionType.NOTE)]
        payload = _create_payload(steps=steps)
        result = service.create_playbook(tenant_id=1, actor="owner@test", payload=payload)
        assert db.add.called
        assert db.flush.called
        assert mock_audit.called


# ---------------------------------------------------------------------------
# get_playbook / list_playbooks
# ---------------------------------------------------------------------------


class TestGetPlaybook:
    def test_not_found_raises(self):
        db = MagicMock()
        db.scalar.return_value = None
        with pytest.raises(TenantResourceNotFoundError, match="not found"):
            PlaybookService(db).get_playbook(tenant_id=1, playbook_id=999)

    def test_wrong_tenant_raises(self):
        db = MagicMock()
        db.scalar.return_value = _make_playbook(tenant_id=2)
        with pytest.raises(TenantResourceNotFoundError):
            PlaybookService(db).get_playbook(tenant_id=1, playbook_id=10)

    def test_happy_path(self):
        pb = _make_playbook(tenant_id=1)
        db = MagicMock()
        db.scalar.return_value = pb
        result = PlaybookService(db).get_playbook(tenant_id=1, playbook_id=10)
        assert result.id == 10


class TestListPlaybooks:
    def test_zero_tenant_raises(self):
        db = MagicMock()
        with pytest.raises(TenantRequiredError, match="tenant"):
            PlaybookService(db).list_playbooks(tenant_id=0)

    def test_returns_items_and_total(self):
        db = MagicMock()
        db.scalar.return_value = 2
        db.scalars.return_value = [_make_playbook(), _make_playbook(playbook_id=11)]
        items, total = PlaybookService(db).list_playbooks(tenant_id=1)
        assert total == 2
        assert len(items) == 2


# ---------------------------------------------------------------------------
# update_playbook
# ---------------------------------------------------------------------------


class TestUpdatePlaybook:
    def test_not_found_raises(self):
        db = MagicMock()
        db.get.return_value = None
        payload = PlaybookUpdateSchema(expected_version=1, name="New Name")
        with pytest.raises(TenantResourceNotFoundError, match="not found"):
            PlaybookService(db).update_playbook(tenant_id=1, playbook_id=999, actor="a", payload=payload)

    def test_wrong_tenant_raises(self):
        db = MagicMock()
        db.get.return_value = _make_playbook(tenant_id=2)
        payload = PlaybookUpdateSchema(expected_version=1, name="New Name")
        with pytest.raises(TenantResourceNotFoundError):
            PlaybookService(db).update_playbook(tenant_id=1, playbook_id=10, actor="a", payload=payload)

    @patch("app.modules.interventions.playbook_service.validate_version_match")
    def test_version_mismatch_raises(self, mock_vm):
        db = MagicMock()
        db.get.return_value = _make_playbook(tenant_id=1, version=2)
        mock_vm.side_effect = OptimisticLockConflictError("Version mismatch")
        payload = PlaybookUpdateSchema(expected_version=1, name="New Name")
        with pytest.raises(OptimisticLockConflictError, match="[Vv]ersion"):
            PlaybookService(db).update_playbook(tenant_id=1, playbook_id=10, actor="a", payload=payload)

    @patch("app.modules.interventions.playbook_service.log_admin_action")
    @patch("app.modules.interventions.playbook_service.validate_version_match")
    def test_happy_updates_fields(self, mock_vm, mock_audit):
        pb = _make_playbook(tenant_id=1, version=1)
        db = MagicMock()
        db.get.return_value = pb
        payload = PlaybookUpdateSchema(expected_version=1, name="Renamed", enabled=False)
        result = PlaybookService(db).update_playbook(tenant_id=1, playbook_id=10, actor="a", payload=payload)
        assert result.name == "Renamed"
        assert result.enabled is False
        assert result.version == 2


# ---------------------------------------------------------------------------
# delete_playbook
# ---------------------------------------------------------------------------


class TestDeletePlaybook:
    def test_not_found_raises(self):
        db = MagicMock()
        db.get.return_value = None
        with pytest.raises(TenantResourceNotFoundError, match="not found"):
            PlaybookService(db).delete_playbook(tenant_id=1, playbook_id=999, actor="a")

    def test_active_executions_guard(self):
        db = MagicMock()
        db.get.return_value = _make_playbook(tenant_id=1)
        db.scalar.return_value = 2  # active_count
        with pytest.raises(DomainValidationError, match="active execution"):
            PlaybookService(db).delete_playbook(tenant_id=1, playbook_id=10, actor="a")

    @patch("app.modules.interventions.playbook_service.log_admin_action")
    def test_happy_deletes(self, mock_audit):
        db = MagicMock()
        db.get.return_value = _make_playbook(tenant_id=1)
        db.scalar.return_value = 0
        PlaybookService(db).delete_playbook(tenant_id=1, playbook_id=10, actor="a")
        assert db.delete.called
        assert mock_audit.called


# ---------------------------------------------------------------------------
# start_execution
# ---------------------------------------------------------------------------


class TestStartExecution:
    def test_playbook_not_found(self):
        db = MagicMock()
        db.scalar.return_value = None
        payload = PlaybookExecutionStartSchema(playbook_id=99, triggered_by=PlaybookTriggerType.MANUAL)
        with pytest.raises(TenantResourceNotFoundError, match="not found"):
            PlaybookService(db).start_execution(tenant_id=1, actor="a", payload=payload)

    def test_playbook_disabled(self):
        db = MagicMock()
        db.scalar.return_value = _make_playbook(enabled=False)
        payload = PlaybookExecutionStartSchema(playbook_id=10, triggered_by=PlaybookTriggerType.MANUAL)
        with pytest.raises(DomainValidationError, match="disabled"):
            PlaybookService(db).start_execution(tenant_id=1, actor="a", payload=payload)

    def test_student_concurrency_guard(self):
        db = MagicMock()
        db.scalar.side_effect = [_make_playbook(enabled=True), MAX_CONCURRENT_EXECUTIONS_PER_STUDENT]
        payload = PlaybookExecutionStartSchema(
            playbook_id=10, student_profile_id=777, triggered_by=PlaybookTriggerType.AUTO,
        )
        with pytest.raises(DomainValidationError, match="Too many active.*student"):
            PlaybookService(db).start_execution(tenant_id=1, actor="a", payload=payload)

    def test_case_concurrency_guard(self):
        db = MagicMock()
        db.scalar.side_effect = [_make_playbook(enabled=True), 0, MAX_CONCURRENT_EXECUTIONS_PER_CASE]
        payload = PlaybookExecutionStartSchema(
            playbook_id=10, student_profile_id=777, case_id=99, triggered_by=PlaybookTriggerType.AUTO,
        )
        with pytest.raises(DomainValidationError, match="Too many active.*case"):
            PlaybookService(db).start_execution(tenant_id=1, actor="a", payload=payload)

    @patch("app.modules.interventions.playbook_service.observe_playbook_execution_started")
    @patch("app.modules.interventions.playbook_service.log_admin_action")
    def test_happy_creates_execution_and_steps(self, mock_audit, mock_metric):
        step1 = SimpleNamespace(id=50, step_order=0, title="S1")
        step2 = SimpleNamespace(id=51, step_order=1, title="S2")
        pb = _make_playbook(enabled=True)
        pb.steps = [step1, step2]
        db = MagicMock()
        db.scalar.return_value = pb
        db.add.return_value = None
        db.flush.return_value = None

        payload = PlaybookExecutionStartSchema(playbook_id=10, triggered_by=PlaybookTriggerType.MANUAL)
        result = PlaybookService(db).start_execution(tenant_id=1, actor="a", payload=payload)
        assert result is not None
        assert mock_metric.called
        assert mock_audit.called
        # 1 execution + 2 step_execution stubs = 3 db.add calls
        assert db.add.call_count == 3


# ---------------------------------------------------------------------------
# get_execution / list_executions
# ---------------------------------------------------------------------------


class TestGetExecution:
    def test_not_found(self):
        db = MagicMock()
        db.scalar.return_value = None
        with pytest.raises(TenantResourceNotFoundError, match="not found"):
            PlaybookService(db).get_execution(tenant_id=1, execution_id=999)

    def test_wrong_tenant(self):
        db = MagicMock()
        db.scalar.return_value = _make_execution(tenant_id=2)
        with pytest.raises(TenantResourceNotFoundError):
            PlaybookService(db).get_execution(tenant_id=1, execution_id=100)


class TestListExecutions:
    def test_returns_items_and_total(self):
        db = MagicMock()
        db.scalar.return_value = 1
        db.scalars.return_value = [_make_execution()]
        items, total = PlaybookService(db).list_executions(tenant_id=1)
        assert total == 1
        assert len(items) == 1

    def test_with_status_filter(self):
        db = MagicMock()
        db.scalar.return_value = 0
        db.scalars.return_value = []
        items, total = PlaybookService(db).list_executions(
            tenant_id=1, status=PlaybookExecutionStatus.COMPLETED,
        )
        assert total == 0


# ---------------------------------------------------------------------------
# complete_step
# ---------------------------------------------------------------------------


class TestCompleteStep:
    def test_step_exec_not_found(self):
        db = MagicMock()
        db.get.return_value = None
        payload = PlaybookStepCompleteSchema(outcome_note="done")
        with pytest.raises(TenantResourceNotFoundError, match="not found"):
            PlaybookService(db).complete_step(
                tenant_id=1, execution_id=100, step_execution_id=999, actor="a", payload=payload,
            )

    def test_step_wrong_execution(self):
        db = MagicMock()
        se = _make_step_exec(execution_id=999)
        db.get.return_value = se
        payload = PlaybookStepCompleteSchema(outcome_note="done")
        with pytest.raises(DomainValidationError, match="does not belong"):
            PlaybookService(db).complete_step(
                tenant_id=1, execution_id=100, step_execution_id=200, actor="a", payload=payload,
            )

    def test_execution_completed_rejects(self):
        se = _make_step_exec(execution_id=100)
        ex = _make_execution(status=PlaybookExecutionStatus.COMPLETED)
        db = MagicMock()
        db.get.side_effect = [se, ex]
        payload = PlaybookStepCompleteSchema(outcome_note="done")
        with pytest.raises(DomainValidationError, match="status"):
            PlaybookService(db).complete_step(
                tenant_id=1, execution_id=100, step_execution_id=200, actor="a", payload=payload,
            )

    def test_already_completed_step_rejects(self):
        se = _make_step_exec(execution_id=100, status=PlaybookStepExecutionStatus.COMPLETED)
        ex = _make_execution(status=PlaybookExecutionStatus.IN_PROGRESS)
        db = MagicMock()
        db.get.side_effect = [se, ex]
        payload = PlaybookStepCompleteSchema(outcome_note="done")
        with pytest.raises(DomainValidationError, match="already completed"):
            PlaybookService(db).complete_step(
                tenant_id=1, execution_id=100, step_execution_id=200, actor="a", payload=payload,
            )

    @patch("app.modules.interventions.playbook_service.observe_playbook_step_action")
    def test_happy_completes_step(self, mock_metric):
        se = _make_step_exec(execution_id=100, status=PlaybookStepExecutionStatus.PENDING)
        ex = _make_execution(status=PlaybookExecutionStatus.IN_PROGRESS)
        db = MagicMock()
        db.get.side_effect = [se, ex]
        # _maybe_complete_execution queries step execs
        db.scalars.return_value = [se]  # still pending after update
        payload = PlaybookStepCompleteSchema(outcome_note="task done")
        result = PlaybookService(db).complete_step(
            tenant_id=1, execution_id=100, step_execution_id=200, actor="advisor", payload=payload,
        )
        assert result.status == PlaybookStepExecutionStatus.COMPLETED
        assert result.performed_by == "advisor"
        assert mock_metric.called


# ---------------------------------------------------------------------------
# skip_step
# ---------------------------------------------------------------------------


class TestSkipStep:
    def test_step_exec_not_found(self):
        db = MagicMock()
        db.get.return_value = None
        payload = PlaybookStepSkipSchema(outcome_note="skip")
        with pytest.raises(TenantResourceNotFoundError, match="not found"):
            PlaybookService(db).skip_step(
                tenant_id=1, execution_id=100, step_execution_id=999, actor="a", payload=payload,
            )

    def test_mandatory_step_cannot_skip(self):
        se = _make_step_exec(execution_id=100, step_id=50)
        ex = _make_execution(status=PlaybookExecutionStatus.IN_PROGRESS)
        mandatory_step = _make_step(step_id=50, is_mandatory=True)
        db = MagicMock()
        db.get.side_effect = [se, ex, mandatory_step]
        payload = PlaybookStepSkipSchema(outcome_note="skip")
        with pytest.raises(DomainValidationError, match="mandatory"):
            PlaybookService(db).skip_step(
                tenant_id=1, execution_id=100, step_execution_id=200, actor="a", payload=payload,
            )

    @patch("app.modules.interventions.playbook_service.observe_playbook_step_action")
    def test_happy_skips_optional_step(self, mock_metric):
        se = _make_step_exec(execution_id=100, step_id=50)
        ex = _make_execution(status=PlaybookExecutionStatus.IN_PROGRESS)
        optional_step = _make_step(step_id=50, is_mandatory=False)
        db = MagicMock()
        db.get.side_effect = [se, ex, optional_step]
        db.scalars.return_value = [se]
        payload = PlaybookStepSkipSchema(outcome_note="not needed")
        result = PlaybookService(db).skip_step(
            tenant_id=1, execution_id=100, step_execution_id=200, actor="advisor", payload=payload,
        )
        assert result.status == PlaybookStepExecutionStatus.SKIPPED
        assert mock_metric.called


# ---------------------------------------------------------------------------
# abandon_execution
# ---------------------------------------------------------------------------


class TestAbandonExecution:
    def test_not_found(self):
        db = MagicMock()
        db.get.return_value = None
        with pytest.raises(TenantResourceNotFoundError, match="not found"):
            PlaybookService(db).abandon_execution(tenant_id=1, execution_id=999, actor="a", reason="no longer needed")

    def test_already_completed_rejects(self):
        db = MagicMock()
        db.get.return_value = _make_execution(status=PlaybookExecutionStatus.COMPLETED)
        with pytest.raises(DomainValidationError, match="already"):
            PlaybookService(db).abandon_execution(tenant_id=1, execution_id=100, actor="a", reason="too late")

    def test_already_abandoned_rejects(self):
        db = MagicMock()
        db.get.return_value = _make_execution(status=PlaybookExecutionStatus.ABANDONED)
        with pytest.raises(DomainValidationError, match="already"):
            PlaybookService(db).abandon_execution(tenant_id=1, execution_id=100, actor="a", reason="dup")

    @patch("app.modules.interventions.playbook_service.observe_playbook_execution_finished")
    @patch("app.modules.interventions.playbook_service.log_admin_action")
    def test_happy_abandons(self, mock_audit, mock_metric):
        ex = _make_execution(status=PlaybookExecutionStatus.IN_PROGRESS)
        db = MagicMock()
        db.get.return_value = ex
        result = PlaybookService(db).abandon_execution(tenant_id=1, execution_id=100, actor="a", reason="student withdrew")
        assert result.status == PlaybookExecutionStatus.ABANDONED
        assert result.abandon_reason == "student withdrew"
        assert mock_audit.called
        assert mock_metric.called
