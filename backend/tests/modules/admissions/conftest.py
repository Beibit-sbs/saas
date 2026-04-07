import asyncio
from collections.abc import Callable
from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest
from sqlalchemy.orm import Session

from app.modules.admissions.models import (
    ApplicantModel,
    ApplicationDecisionModel,
    ApplicationDocumentModel,
    ApplicationModel,
    ApplicationStageHistoryModel,
)
from app.modules.admissions.schemas import (
    ApplicationConclusionType,
    ApplicationStage,
    DocumentStatus,
)
from app.modules.admissions import service as admissions_service


class ScalarListResult:
    def __init__(self, items: list[object]):
        self._items = items

    def all(self) -> list[object]:
        return list(self._items)


class ExecuteResult:
    def __init__(
        self,
        *,
        scalar_one_or_none: object | None = None,
        scalar: object | None = None,
        scalars: list[object] | None = None,
    ):
        self._scalar_one_or_none = scalar_one_or_none
        self._scalar = scalar
        self._scalars = scalars or []

    def scalar_one_or_none(self) -> object | None:
        return self._scalar_one_or_none

    def scalar(self) -> object | None:
        return self._scalar

    def scalars(self) -> ScalarListResult:
        return ScalarListResult(self._scalars)


@pytest.fixture
def run_async() -> Callable:
    return asyncio.run


@pytest.fixture
def db_session() -> MagicMock:
    session = MagicMock(spec=Session)

    def fake_refresh(instance: object) -> None:
        now = datetime(2026, 3, 22, 12, 0, 0, tzinfo=timezone.utc)
        if getattr(instance, "id", None) is None:
            defaults = {
                "ApplicantModel": 101,
                "ApplicationModel": 201,
                "ApplicationDocumentModel": 301,
                "ApplicationStageHistoryModel": 401,
                "ApplicationDecisionModel": 501,
            }
            instance.id = defaults.get(instance.__class__.__name__, 1)
        if hasattr(instance, "created_at") and getattr(instance, "created_at", None) is None:
            instance.created_at = now
        if hasattr(instance, "updated_at") and getattr(instance, "updated_at", None) is None:
            instance.updated_at = now
        if hasattr(instance, "version") and getattr(instance, "version", None) is None:
            instance.version = 1
        if hasattr(instance, "decided_at") and getattr(instance, "decided_at", None) is None:
            instance.decided_at = now

    session.refresh.side_effect = fake_refresh
    return session


@pytest.fixture
def audit_calls(monkeypatch: pytest.MonkeyPatch) -> list[dict]:
    calls: list[dict] = []

    def fake_log_admin_action(**kwargs):
        calls.append(kwargs)

    monkeypatch.setattr(admissions_service, "log_admin_action", fake_log_admin_action)
    return calls


@pytest.fixture
def now() -> datetime:
    return datetime(2026, 3, 22, 12, 0, 0, tzinfo=timezone.utc)


@pytest.fixture
def applicant_factory(now: datetime):
    def factory(**overrides) -> ApplicantModel:
        return ApplicantModel(
            id=overrides.get("id", 101),
            tenant_id=overrides.get("tenant_id", 1),
            email=overrides.get("email", "student@example.com"),
            first_name=overrides.get("first_name", "Ada"),
            last_name=overrides.get("last_name", "Lovelace"),
            phone=overrides.get("phone", "+10000000000"),
            program_id=overrides.get("program_id", 501),
            application_year=overrides.get("application_year", 2026),
            status=overrides.get("status", "active"),
            external_id=overrides.get("external_id", "sis-101"),
            metadata_json=overrides.get("metadata_json", {"citizenship": "US"}),
            created_by=overrides.get("created_by", "owner@example.com"),
            created_at=overrides.get("created_at", now),
            updated_at=overrides.get("updated_at", now),
        )

    return factory


@pytest.fixture
def application_factory(now: datetime):
    def factory(**overrides) -> ApplicationModel:
        return ApplicationModel(
            id=overrides.get("id", 201),
            tenant_id=overrides.get("tenant_id", 1),
            applicant_id=overrides.get("applicant_id", 101),
            program_id=overrides.get("program_id", 501),
            stage=overrides.get("stage", ApplicationStage.NEW.value),
            conclusion_type=overrides.get("conclusion_type"),
            received_at=overrides.get("received_at"),
            decision_at=overrides.get("decision_at"),
            version=overrides.get("version", 1),
            metadata_json=overrides.get("metadata_json", {}),
            created_by=overrides.get("created_by", "owner@example.com"),
            created_at=overrides.get("created_at", now),
            updated_at=overrides.get("updated_at", now),
        )

    return factory


@pytest.fixture
def document_factory(now: datetime):
    def factory(**overrides) -> ApplicationDocumentModel:
        return ApplicationDocumentModel(
            id=overrides.get("id", 301),
            tenant_id=overrides.get("tenant_id", 1),
            application_id=overrides.get("application_id", 201),
            document_type=overrides.get("document_type", "transcript"),
            document_key=overrides.get("document_key", "s3://tenant-1/app-201/transcript.pdf"),
            file_name=overrides.get("file_name", "transcript.pdf"),
            file_size_bytes=overrides.get("file_size_bytes", 4096),
            mime_type=overrides.get("mime_type", "application/pdf"),
            status=overrides.get("status", DocumentStatus.RECEIVED.value),
            metadata_json=overrides.get("metadata_json", {}),
            created_by=overrides.get("created_by", "owner@example.com"),
            created_at=overrides.get("created_at", now),
            verified_at=overrides.get("verified_at"),
            verified_by=overrides.get("verified_by"),
        )

    return factory


@pytest.fixture
def stage_history_factory(now: datetime):
    def factory(**overrides) -> ApplicationStageHistoryModel:
        return ApplicationStageHistoryModel(
            id=overrides.get("id", 401),
            tenant_id=overrides.get("tenant_id", 1),
            application_id=overrides.get("application_id", 201),
            from_stage=overrides.get("from_stage", ApplicationStage.NEW.value),
            to_stage=overrides.get("to_stage", ApplicationStage.RECEIVED.value),
            reason=overrides.get("reason", "submission received"),
            actor_id=overrides.get("actor_id", "reviewer@example.com"),
            action_type=overrides.get("action_type", "manual"),
            metadata_json=overrides.get("metadata_json", {}),
            created_at=overrides.get("created_at", now),
        )

    return factory


@pytest.fixture
def decision_factory(now: datetime):
    def factory(**overrides) -> ApplicationDecisionModel:
        return ApplicationDecisionModel(
            id=overrides.get("id", 501),
            tenant_id=overrides.get("tenant_id", 1),
            application_id=overrides.get("application_id", 201),
            decision_type=overrides.get("decision_type", ApplicationConclusionType.ACCEPTED.value),
            decision_rationale=overrides.get("decision_rationale", "Strong portfolio"),
            decided_by_id=overrides.get("decided_by_id", "dean@example.com"),
            decided_at=overrides.get("decided_at", now),
            conditions_json=overrides.get("conditions_json", {}),
            version=overrides.get("version", 1),
            created_at=overrides.get("created_at", now),
            updated_at=overrides.get("updated_at", now),
        )

    return factory


    # ==============================================================================
    # PHASE 5A: WORKFLOW INTEGRATION FIXTURES
    # ==============================================================================


    @pytest.fixture
    def workflow_instance_factory(now: datetime):
        """Factory for creating workflow instance-like objects."""
        def factory(**overrides) -> MagicMock:
            workflow = MagicMock()
            workflow.id = overrides.get("id", 789)
            workflow.tenant_id = overrides.get("tenant_id", 1)
            workflow.workflow_key = overrides.get("workflow_key", "admissions")
            workflow.entity_type = overrides.get("entity_type", "admission_application")
            workflow.entity_id = overrides.get("entity_id", 201)
            workflow.status = overrides.get("status", "in_progress")
            workflow.created_by_id = overrides.get("created_by_id", "applicant@example.com")
            workflow.created_at = overrides.get("created_at", now)
            workflow.started_at = overrides.get("started_at", now)
            return workflow
    
        return factory


    @pytest.fixture
    def mock_workflow_service(monkeypatch: pytest.MonkeyPatch, workflow_instance_factory):
        """Mock WorkflowService.start_workflow() for Phase 5A tests."""
        mock_service = MagicMock()
    
        async def async_start_workflow(**kwargs):
            return workflow_instance_factory(
                id=789,
                entity_id=kwargs.get("entity_id", 201),
                workflow_key=kwargs.get("workflow_key", "admissions"),
            )
    
        mock_service.start_workflow = async_start_workflow
    
        # Patch at service module level
        monkeypatch.setattr(
            "app.modules.admissions.service.WorkflowService",
            lambda db: mock_service,
        )
    
        return mock_service


    # ==============================================================================
    # ASSERTION HELPERS FOR PHASE 5A
    # ==============================================================================


    @pytest.fixture
    def assert_metadata_safe():
        """Assert metadata_json was safely merged, not overwritten."""
        def _check(original: dict, updated: dict, expected_new_keys: set[str]):
            # Verify all original keys preserved
            for key in original:
                assert key in updated, f"Original key '{key}' was lost"
                assert updated[key] == original[key], f"Original key '{key}' value changed"
        
            # Verify new keys added
            for key in expected_new_keys:
                assert key in updated, f"Expected new key '{key}' not added"
    
        return _check


    @pytest.fixture
    def assert_audit_event():
        """Assert audit event was logged with expected structure."""
        def _check(audit_calls: list[dict], entity: str, expected_metadata_keys: set[str]):
            assert len(audit_calls) > 0, "No audit calls recorded"
        
            last_call = audit_calls[-1]
            assert last_call.get("entity") == entity
        
            metadata = last_call.get("metadata", {})
            for key in expected_metadata_keys:
                assert key in metadata, f"Expected metadata key '{key}' not found"
    
        return _check


    @pytest.fixture
    def assert_version_incremented():
        """Assert optimistic lock version was incremented."""
        def _check(original_version: int, updated_version: int):
            assert updated_version == original_version + 1, \
                f"Version not incremented: {original_version} -> {updated_version}"
    
        return _check


    @pytest.fixture
    def assert_stage_transition():
        """Assert stage transition and timestamp were set."""
        def _check(from_stage: str, to_stage: str, application, received_at_set: bool = True):
            assert application.stage == to_stage, f"Stage not updated: {application.stage}"
        
            if to_stage == ApplicationStage.RECEIVED.value and received_at_set:
                assert application.received_at is not None, "received_at not set"
        
            if to_stage == ApplicationStage.CONCLUDED.value:
                assert application.decision_at is not None, "decision_at not set"
    
        return _check


    @pytest.fixture
    def assert_decision_materialized():
        """Assert decision was properly materialized from workflow."""
        def _check(decision, approval_action: str, expected_conclusion: str):
            assert decision is not None, "Decision not created"
            assert hasattr(decision, "decision_type"), "Decision missing decision_type"
            assert decision.decision_type == expected_conclusion, \
                f"Decision type mismatch: {decision.decision_type} != {expected_conclusion}"
        
            if hasattr(decision, "conditions_json"):
                conditions = decision.conditions_json or {}
                assert conditions.get("workflow_outcome") == approval_action, \
                    "Workflow outcome not stored in conditions"
    
        return _check


    # ==============================================================================
    # QUERY HELPER FIXTURES
    # ==============================================================================


    @pytest.fixture
    def mock_db_with_application(db_session: MagicMock, application_factory):
        """Mock DB session pre-configured to return an application."""
        def _setup(application_kwargs: dict | None = None) -> tuple[MagicMock, ApplicationModel]:
            kwargs = application_kwargs or {}
            application = application_factory(**kwargs)
        
            # Setup query result
            result = MagicMock()
            result.scalar_one_or_none = MagicMock(return_value=application)
            result.scalar = MagicMock(return_value=application)
            result.scalars = MagicMock(
                return_value=MagicMock(all=MagicMock(return_value=[application]))
            )
        
            db_session.execute = MagicMock(return_value=result)
        
            return db_session, application
    
        return _setup


    @pytest.fixture
    def mock_db_with_decision(db_session: MagicMock, decision_factory):
        """Mock DB session pre-configured to return a decision."""
        def _setup(decision_kwargs: dict | None = None) -> tuple[MagicMock, ApplicationDecisionModel]:
            kwargs = decision_kwargs or {}
            decision = decision_factory(**kwargs)
        
            result = MagicMock()
            result.scalar_one_or_none = MagicMock(return_value=decision)
            result.scalar = MagicMock(return_value=decision)
        
            db_session.execute = MagicMock(return_value=result)
        
            return db_session, decision
    
        return _setup


    # ==============================================================================
    # TENANT ISOLATION TEST HELPERS
    # ==============================================================================


    @pytest.fixture
    def mock_validate_tenant(monkeypatch: pytest.MonkeyPatch):
        """Mock validate_tenant_id_provided."""
        calls = []
    
        def fake_validate(tenant_id: int) -> int:
            calls.append(tenant_id)
            return tenant_id
    
        monkeypatch.setattr(
            "app.modules.admissions.service.validate_tenant_id_provided",
            fake_validate,
        )
    
        return calls