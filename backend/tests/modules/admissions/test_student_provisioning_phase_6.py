"""Admissions Phase 6 provisioning tests for canonical Students lifecycle integration."""

from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.module_helpers.service_validation import DomainValidationError
from app.modules.admissions.schemas import ApplicationConclusionType, ApplicationStage
from app.modules.admissions.service import DecisionService


def _now() -> datetime:
    return datetime.now(UTC)


@pytest.fixture
def mock_db_session():
    session = MagicMock()

    mock_result = MagicMock()
    mock_result.scalar_one_or_none = MagicMock(return_value=None)
    session.execute = MagicMock(return_value=mock_result)

    def realistic_refresh(model_obj):
        now = _now()
        if hasattr(model_obj, "id") and getattr(model_obj, "id", None) is None:
            name = model_obj.__class__.__name__
            if name == "ApplicationDecisionModel":
                model_obj.id = 9001
            elif name == "PersonModel":
                model_obj.id = 7001
            elif name == "ApplicationStageHistoryModel":
                model_obj.id = 4001
            else:
                model_obj.id = 1
        if hasattr(model_obj, "created_at") and getattr(model_obj, "created_at", None) is None:
            model_obj.created_at = now
        if hasattr(model_obj, "updated_at") and getattr(model_obj, "updated_at", None) is None:
            model_obj.updated_at = now
        if hasattr(model_obj, "version") and getattr(model_obj, "version", None) is None:
            model_obj.version = 1
        if hasattr(model_obj, "decided_at") and getattr(model_obj, "decided_at", None) is None:
            model_obj.decided_at = now

    session.refresh = MagicMock(side_effect=realistic_refresh)
    session.flush = MagicMock()
    session.add = MagicMock()
    session.commit = MagicMock()
    return session


@pytest.fixture
def mock_application_model():
    app = MagicMock()
    app.id = 123
    app.tenant_id = 1
    app.applicant_id = 42
    app.program_id = 10
    app.stage = ApplicationStage.DECISION_PENDING.value
    app.version = 2
    app.metadata_json = {"workflow_instance_id": 789}
    app.received_at = _now()
    app.decision_at = None
    app.conclusion_type = None
    app.created_by = "owner@example.com"
    app.created_at = _now()
    app.updated_at = _now()
    return app


@pytest.fixture
def mock_applicant_model():
    applicant = MagicMock()
    applicant.id = 42
    applicant.tenant_id = 1
    applicant.email = "accepted@student.edu"
    applicant.first_name = "Accepted"
    applicant.last_name = "Student"
    applicant.phone = "+10000000001"
    applicant.application_year = 2026
    applicant.external_id = "ext-accepted-42"
    return applicant


@pytest.fixture
def mock_existing_decision():
    decision = MagicMock()
    decision.id = 201
    decision.tenant_id = 1
    decision.application_id = 123
    decision.decision_type = ApplicationConclusionType.ACCEPTED.value
    decision.decision_rationale = "Workflow decision: approve"
    decision.decided_by_id = "system@workflow"
    decision.decided_at = _now()
    decision.version = 1
    decision.conditions_json = {"workflow_instance_id": 789, "approval_action": "approve"}
    decision.created_at = _now()
    decision.updated_at = _now()
    return decision


@pytest.fixture
def lifecycle_result_factory():
    def _factory(
        *,
        profile_id: int = 5001,
        student_number: str = "ADM-1-123",
        binding_id: int = 6001,
        program_id: int = 10,
    ) -> SimpleNamespace:
        return SimpleNamespace(
            student_profile=SimpleNamespace(
                id=profile_id,
                student_number=student_number,
            ),
            active_primary_program=SimpleNamespace(
                id=binding_id,
                program_id=program_id,
            ),
        )

    return _factory


@pytest.fixture
def mock_lifecycle_provision(monkeypatch: pytest.MonkeyPatch, lifecycle_result_factory):
    mock = AsyncMock(return_value=lifecycle_result_factory())
    monkeypatch.setattr(
        "app.modules.students.service.StudentLifecycleService.provision_student_for_admissions_compat",
        mock,
    )
    return mock


@pytest.fixture
def mock_audit_logger():
    with patch("app.modules.admissions.service.log_admin_action") as mock_log:
        yield mock_log


@pytest.fixture
def mock_validator_tenant():
    with patch("app.modules.admissions.service.validate_tenant_id_provided") as mock_val:
        mock_val.side_effect = lambda x: x
        yield mock_val


@pytest.mark.asyncio
class TestPhase6StudentProvisioningStudentsLifecycle:
    async def test_accepted_decision_triggers_students_lifecycle_provisioning(
        self,
        mock_db_session,
        mock_application_model,
        mock_applicant_model,
        mock_lifecycle_provision,
        mock_validator_tenant,
    ):
        mock_db_session.execute.return_value.scalar_one_or_none.side_effect = [
            mock_application_model,
            None,
            mock_applicant_model,
            None,
        ]

        service = DecisionService(mock_db_session)
        result = await service.finalize_workflow_decision(
            tenant_id=1,
            application_id=123,
            workflow_instance_id=789,
            approval_action="approve",
            actor="system@workflow",
        )

        assert result.application_id == 123
        assert mock_application_model.conclusion_type == ApplicationConclusionType.ACCEPTED.value
        mock_lifecycle_provision.assert_awaited_once()

    async def test_reuse_existing_student_profile_no_duplicate_create(
        self,
        mock_db_session,
        mock_application_model,
        mock_applicant_model,
        mock_lifecycle_provision,
        mock_validator_tenant,
    ):
        existing_person = MagicMock()
        existing_person.id = 7001
        existing_person.email = mock_applicant_model.email

        mock_db_session.execute.return_value.scalar_one_or_none.side_effect = [
            mock_application_model,
            None,
            mock_applicant_model,
            existing_person,
        ]

        service = DecisionService(mock_db_session)
        await service.finalize_workflow_decision(
            tenant_id=1,
            application_id=123,
            workflow_instance_id=789,
            approval_action="approve",
            actor="system@workflow",
        )

        # Only decision + stage history should be added when person exists.
        assert mock_db_session.add.call_count == 2
        mock_lifecycle_provision.assert_awaited_once()

    async def test_reuse_existing_program_binding_no_duplicate_binding_create(
        self,
        mock_db_session,
        mock_application_model,
        mock_applicant_model,
        mock_lifecycle_provision,
        mock_validator_tenant,
        lifecycle_result_factory,
    ):
        existing_person = MagicMock()
        existing_person.id = 7001
        existing_person.email = mock_applicant_model.email
        mock_lifecycle_provision.return_value = lifecycle_result_factory(
            profile_id=7007,
            student_number="ADM-1-123",
            binding_id=6010,
            program_id=10,
        )

        mock_db_session.execute.return_value.scalar_one_or_none.side_effect = [
            mock_application_model,
            None,
            mock_applicant_model,
            existing_person,
        ]

        service = DecisionService(mock_db_session)
        await service.finalize_workflow_decision(
            tenant_id=1,
            application_id=123,
            workflow_instance_id=789,
            approval_action="approve",
            actor="system@workflow",
        )

        assert mock_application_model.metadata_json["student_program_binding_id"] == 6010
        mock_lifecycle_provision.assert_awaited_once()

    async def test_idempotent_retry_existing_decision_short_circuits_without_provisioning(
        self,
        mock_db_session,
        mock_application_model,
        mock_existing_decision,
        mock_lifecycle_provision,
        mock_validator_tenant,
    ):
        mock_db_session.execute.return_value.scalar_one_or_none.side_effect = [
            mock_application_model,
            mock_existing_decision,
        ]

        service = DecisionService(mock_db_session)
        result = await service.finalize_workflow_decision(
            tenant_id=1,
            application_id=123,
            workflow_instance_id=789,
            approval_action="approve",
            actor="system@workflow",
        )

        assert result.id == 201
        mock_lifecycle_provision.assert_not_awaited()
        mock_db_session.add.assert_not_called()
        mock_db_session.commit.assert_not_called()

    async def test_person_creation_path_then_provisioning_executes(
        self,
        mock_db_session,
        mock_application_model,
        mock_applicant_model,
        mock_lifecycle_provision,
        mock_audit_logger,
        mock_validator_tenant,
    ):
        mock_db_session.execute.return_value.scalar_one_or_none.side_effect = [
            mock_application_model,
            None,
            mock_applicant_model,
            None,
        ]

        service = DecisionService(mock_db_session)
        await service.finalize_workflow_decision(
            tenant_id=1,
            application_id=123,
            workflow_instance_id=789,
            approval_action="approve",
            actor="system@workflow",
        )

        # decision + stage history + person create
        assert mock_db_session.add.call_count == 3
        mock_lifecycle_provision.assert_awaited_once()

        actions = [call.kwargs.get("action") for call in mock_audit_logger.call_args_list]
        assert "profiles.person.created" in actions

    async def test_fail_closed_program_not_in_tenant_raises_domain_validation(
        self,
        mock_db_session,
        mock_application_model,
        mock_applicant_model,
        mock_lifecycle_provision,
        mock_validator_tenant,
    ):
        existing_person = MagicMock()
        existing_person.id = 7001
        existing_person.email = mock_applicant_model.email
        mock_lifecycle_provision.side_effect = DomainValidationError(
            "Program 10 not found or does not belong to tenant 1"
        )

        mock_db_session.execute.return_value.scalar_one_or_none.side_effect = [
            mock_application_model,
            None,
            mock_applicant_model,
            existing_person,
        ]

        service = DecisionService(mock_db_session)
        with pytest.raises(DomainValidationError, match="Program 10 not found"):
            await service.finalize_workflow_decision(
                tenant_id=1,
                application_id=123,
                workflow_instance_id=789,
                approval_action="approve",
                actor="system@workflow",
            )

    async def test_fail_closed_person_mismatch_raises_domain_validation(
        self,
        mock_db_session,
        mock_application_model,
        mock_applicant_model,
        mock_lifecycle_provision,
        mock_validator_tenant,
    ):
        existing_person = MagicMock()
        existing_person.id = 7001
        existing_person.email = mock_applicant_model.email
        mock_lifecycle_provision.side_effect = DomainValidationError(
            "Person mismatch for tenant 1"
        )

        mock_db_session.execute.return_value.scalar_one_or_none.side_effect = [
            mock_application_model,
            None,
            mock_applicant_model,
            existing_person,
        ]

        service = DecisionService(mock_db_session)
        with pytest.raises(DomainValidationError, match="Person mismatch"):
            await service.finalize_workflow_decision(
                tenant_id=1,
                application_id=123,
                workflow_instance_id=789,
                approval_action="approve",
                actor="system@workflow",
            )

    async def test_fail_closed_tenant_mismatch_raises_domain_validation(
        self,
        mock_db_session,
        mock_application_model,
        mock_applicant_model,
        mock_lifecycle_provision,
        mock_validator_tenant,
    ):
        existing_person = MagicMock()
        existing_person.id = 7001
        existing_person.email = mock_applicant_model.email
        mock_lifecycle_provision.side_effect = DomainValidationError(
            "tenant mismatch during students provisioning"
        )

        mock_db_session.execute.return_value.scalar_one_or_none.side_effect = [
            mock_application_model,
            None,
            mock_applicant_model,
            existing_person,
        ]

        service = DecisionService(mock_db_session)
        with pytest.raises(DomainValidationError, match="tenant mismatch"):
            await service.finalize_workflow_decision(
                tenant_id=1,
                application_id=123,
                workflow_instance_id=789,
                approval_action="approve",
                actor="system@workflow",
            )

    async def test_metadata_compatibility_keys_populated(
        self,
        mock_db_session,
        mock_application_model,
        mock_applicant_model,
        mock_lifecycle_provision,
        mock_validator_tenant,
        lifecycle_result_factory,
    ):
        existing_person = MagicMock()
        existing_person.id = 7001
        existing_person.email = mock_applicant_model.email
        mock_lifecycle_provision.return_value = lifecycle_result_factory(
            profile_id=5009,
            student_number="ADM-1-123",
            binding_id=6011,
            program_id=10,
        )
        mock_db_session.execute.return_value.scalar_one_or_none.side_effect = [
            mock_application_model,
            None,
            mock_applicant_model,
            existing_person,
        ]

        service = DecisionService(mock_db_session)
        await service.finalize_workflow_decision(
            tenant_id=1,
            application_id=123,
            workflow_instance_id=789,
            approval_action="approve",
            actor="system@workflow",
        )

        assert mock_application_model.metadata_json["student_id"] == 5009
        assert mock_application_model.metadata_json["student_number"] == "ADM-1-123"
        assert mock_application_model.metadata_json["student_profile_id"] == 5009
        assert mock_application_model.metadata_json["student_program_binding_id"] == 6011

    async def test_audit_events_include_decision_and_student_provision_and_conditional_person_create(
        self,
        mock_db_session,
        mock_application_model,
        mock_applicant_model,
        mock_lifecycle_provision,
        mock_audit_logger,
        mock_validator_tenant,
    ):
        # Person missing -> person.created expected.
        mock_db_session.execute.return_value.scalar_one_or_none.side_effect = [
            mock_application_model,
            None,
            mock_applicant_model,
            None,
        ]

        service = DecisionService(mock_db_session)
        await service.finalize_workflow_decision(
            tenant_id=1,
            application_id=123,
            workflow_instance_id=789,
            approval_action="approve",
            actor="system@workflow",
        )

        actions = [call.kwargs.get("action") for call in mock_audit_logger.call_args_list]
        assert "admissions.decision.finalize" in actions
        assert "admissions.student_provision.completed" in actions
        assert "profiles.person.created" in actions

    async def test_rejected_decision_does_not_call_students_provisioning(
        self,
        mock_db_session,
        mock_application_model,
        mock_lifecycle_provision,
        mock_validator_tenant,
    ):
        mock_db_session.execute.return_value.scalar_one_or_none.side_effect = [
            mock_application_model,
            None,
        ]

        service = DecisionService(mock_db_session)
        await service.finalize_workflow_decision(
            tenant_id=1,
            application_id=123,
            workflow_instance_id=789,
            approval_action="reject",
            actor="system@workflow",
        )

        assert mock_application_model.conclusion_type == ApplicationConclusionType.REJECTED.value
        mock_lifecycle_provision.assert_not_awaited()
