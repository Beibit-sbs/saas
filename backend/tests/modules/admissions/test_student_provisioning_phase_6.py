"""
Phase 6: Student Provisioning after Accepted Admission Decision

Scope:
- Service layer only (DecisionService.finalize_workflow_decision)
- No router/schema changes
- Tenant-first + fail-closed behavior
- Idempotent Person/Student creation
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest

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
            elif name == "StudentModel":
                model_obj.id = 8001
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
def mock_program_model():
    program = MagicMock()
    program.id = 10
    program.tenant_id = 1
    return program


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
def mock_audit_logger():
    with patch("app.modules.admissions.service.log_admin_action") as mock_log:
        yield mock_log


@pytest.fixture
def mock_validator_tenant():
    with patch("app.modules.admissions.service.validate_tenant_id_provided") as mock_val:
        mock_val.side_effect = lambda x: x
        yield mock_val


@pytest.mark.asyncio
class TestPhase6StudentProvisioning:
    async def test_accepted_decision_creates_person_and_student_when_missing(
        self,
        mock_db_session,
        mock_application_model,
        mock_applicant_model,
        mock_program_model,
        mock_audit_logger,
        mock_validator_tenant,
    ):
        """Accepted workflow outcome provisions Person + Student exactly once."""
        # finalize() queries:
        # 1 app, 2 existing_decision
        # provision() queries: 3 applicant, 4 program, 5 person existing, 6 student existing
        mock_db_session.execute.return_value.scalar_one_or_none.side_effect = [
            mock_application_model,
            None,
            mock_applicant_model,
            mock_program_model,
            None,
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
        assert mock_application_model.stage == ApplicationStage.CONCLUDED.value
        assert mock_application_model.conclusion_type == ApplicationConclusionType.ACCEPTED.value

        # Metadata gets identity links for idempotent traceability
        assert "person_id" in mock_application_model.metadata_json
        assert "student_id" in mock_application_model.metadata_json
        assert "student_number" in mock_application_model.metadata_json
        assert mock_application_model.metadata_json["student_number"] == "ADM-1-123"

        # decision + stage history + person + student
        assert mock_db_session.add.call_count >= 4

        # decision finalize audit + person created audit + student created audit
        assert mock_audit_logger.call_count >= 3
        entities = [call.kwargs.get("entity") for call in mock_audit_logger.call_args_list]
        assert "decision" in entities
        assert "person" in entities
        assert "student" in entities

    async def test_rejected_decision_does_not_create_student(
        self,
        mock_db_session,
        mock_application_model,
        mock_audit_logger,
        mock_validator_tenant,
    ):
        """Rejected outcome must never provision Student identity."""
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
        assert "student_id" not in mock_application_model.metadata_json
        assert "person_id" not in mock_application_model.metadata_json

        # decision + stage history only
        assert mock_db_session.add.call_count == 2

    async def test_idempotency_existing_person_and_student_no_duplicates(
        self,
        mock_db_session,
        mock_application_model,
        mock_applicant_model,
        mock_program_model,
        mock_validator_tenant,
    ):
        """Retry-safe: existing Person/Student are reused, no duplicate inserts."""
        existing_person = MagicMock()
        existing_person.id = 7001
        existing_person.email = mock_applicant_model.email

        existing_student = MagicMock()
        existing_student.id = 8001
        existing_student.person_id = existing_person.id
        existing_student.student_number = "ADM-1-123"

        mock_db_session.execute.return_value.scalar_one_or_none.side_effect = [
            mock_application_model,
            None,
            mock_applicant_model,
            mock_program_model,
            existing_person,
            existing_student,
        ]

        service = DecisionService(mock_db_session)
        await service.finalize_workflow_decision(
            tenant_id=1,
            application_id=123,
            workflow_instance_id=789,
            approval_action="approve",
            actor="system@workflow",
        )

        # decision + history only; no person/student add when already exists
        assert mock_db_session.add.call_count == 2
        assert mock_application_model.metadata_json["person_id"] == 7001
        assert mock_application_model.metadata_json["student_id"] == 8001

    async def test_fail_closed_if_program_missing_in_profiles(
        self,
        mock_db_session,
        mock_application_model,
        mock_applicant_model,
        mock_validator_tenant,
    ):
        """Accepted decision fails closed if target program not found in tenant."""
        mock_db_session.execute.return_value.scalar_one_or_none.side_effect = [
            mock_application_model,
            None,
            mock_applicant_model,
            None,
        ]

        service = DecisionService(mock_db_session)

        with pytest.raises(ValueError, match="Program 10 not found in tenant 1"):
            await service.finalize_workflow_decision(
                tenant_id=1,
                application_id=123,
                workflow_instance_id=789,
                approval_action="approve",
                actor="system@workflow",
            )

    async def test_retry_with_existing_decision_returns_existing_without_duplicate_side_effects(
        self,
        mock_db_session,
        mock_application_model,
        mock_existing_decision,
        mock_validator_tenant,
    ):
        """Idempotent callback retry: existing decision short-circuits safely."""
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
        mock_db_session.add.assert_not_called()
        mock_db_session.commit.assert_not_called()
