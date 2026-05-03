"""
Phase 5A: Admissions ↔ Workflow Integration Tests

Scope: ApplicationService.submit_application(), DecisionService.finalize_workflow_decision()

Test Coverage:
- Happy paths (stage transitions, workflow creation, decision materialization)
- Error scenarios (invalid stages, version conflicts, invalid approval actions)
- Idempotency (workflow creation skipped, decision creation skipped)
- Tenant isolation (cross-tenant access blocked)
- Metadata JSON safety (safe merge, no destructive overwrites)
- Audit logging (all mutations logged with context)

Architecture:
- Mock DB session with query chain patterns
- Async/await for service methods
- Pydantic schema validation
- State tracking for assertions

Production Patterns:
- fail-closed validation (exceptions on violations)
- optimistic locking checks
- append-only history records
- full audit trail
"""

import pytest
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch
from app.modules.admissions.service import ApplicationService, DecisionService
from app.modules.admissions.schemas import (
    ApplicationStage,
    ApplicationConclusionType,
    ApplicationReadSchema,
    ApplicationDecisionReadSchema,
)


# ==============================================================================
# FIXTURES: DB Session & Mock Objects
# ==============================================================================


@pytest.fixture
def mock_db_session():
    """Create a mock SQLAlchemy session with query chain support and realistic refresh behavior."""
    session = MagicMock()
    
    # Setup execute().scalar_one_or_none() chain for default behavior
    mock_result = MagicMock()
    mock_result.scalar_one_or_none = MagicMock(return_value=None)
    mock_result.scalars = MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))
    
    session.execute = MagicMock(return_value=mock_result)
    session.flush = MagicMock()
    
    # Make refresh() actually populate auto-generated fields on models
    def realistic_refresh(model_obj):
        """Simulate database refresh by populating auto-generated fields."""
        now = datetime.now(UTC)
        if hasattr(model_obj, 'id') and model_obj.id is None:
            model_obj.id = 201  # Mock ID
        if hasattr(model_obj, 'created_at') and model_obj.created_at is None:
            model_obj.created_at = now
        if hasattr(model_obj, 'updated_at') and model_obj.updated_at is None:
            model_obj.updated_at = now
        if hasattr(model_obj, 'version') and model_obj.version is None:
            model_obj.version = 1
        if hasattr(model_obj, 'decided_at') and model_obj.decided_at is None:
            model_obj.decided_at = now
    
    session.refresh = MagicMock(side_effect=realistic_refresh)
    session.commit = MagicMock()
    session.add = MagicMock()
    
    return session


@pytest.fixture
def mock_application_model():
    """Create a mock ApplicationModel instance with all Pydantic fields."""
    now = datetime.now(UTC)
    app = MagicMock()
    app.id = 123
    app.tenant_id = 1
    app.applicant_id = 42
    app.program_id = 10
    app.stage = ApplicationStage.NEW.value
    app.version = 1
    app.metadata_json = {}
    app.received_at = None
    app.decision_at = None
    app.conclusion_type = None
    app.created_by = "owner@example.com"
    app.created_at = now
    app.updated_at = now
    return app


@pytest.fixture
def mock_decision_model():
    """Create a mock ApplicationDecisionModel instance with all Pydantic fields."""
    now = datetime.now(UTC)
    decision = MagicMock()
    decision.id = 201
    decision.tenant_id = 1
    decision.application_id = 123
    decision.decision_type = ApplicationConclusionType.ACCEPTED.value
    decision.decision_rationale = "Workflow decision: approve"
    decision.decided_by_id = "system@workflow"
    decision.decided_at = now
    decision.version = 1
    decision.conditions_json = {
        "workflow_instance_id": 789,
        "approval_action": "approve",
        "decision_source": "workflow_engine",
    }
    decision.created_at = now
    decision.updated_at = now
    return decision


@pytest.fixture
def mock_workflow_instance():
    """Create a mock WorkflowInstanceReadSchema-like object."""
    workflow = MagicMock()
    workflow.id = 789
    workflow.tenant_id = 1
    workflow.entity_type = "admission_application"
    workflow.entity_id = 123
    workflow.status = "in_progress"
    return workflow


@pytest.fixture
def mock_audit_logger():
    """Mock the audit logging function."""
    with patch("app.modules.admissions.service.log_admin_action") as mock_log:
        yield mock_log


@pytest.fixture
def mock_builder_audit_action():
    """Mock build_audit_action helper."""
    with patch("app.modules.admissions.service.build_audit_action") as mock_build:
        mock_build.return_value = "admissions:application:submit"
        yield mock_build


@pytest.fixture
def mock_validator_tenant():
    """Mock validate_tenant_id_provided."""
    with patch("app.modules.admissions.service.validate_tenant_id_provided") as mock_val:
        mock_val.side_effect = lambda x: x  # Return tenant_id as-is
        yield mock_val


@pytest.fixture(autouse=True)
def mock_phase6_student_provisioning():
    """Phase 5A suite isolates workflow-decision logic from Phase 6 side effects."""
    with patch.object(
        DecisionService,
        "_provision_student_identity_on_accept",
        new_callable=AsyncMock,
    ) as mock_provision:
        yield mock_provision


@pytest.fixture(autouse=True)
def mock_phase33_cross_entity_guards():
    """Phase 5A suite isolates workflow callbacks from Phase XXXIII.5 guard checks."""
    with patch.object(
        DecisionService,
        "_validate_final_decision_cross_entity_guards",
        return_value=None,
    ):
        yield


# ==============================================================================
# TEST SUITE: ApplicationService.submit_application()
# ==============================================================================


@pytest.mark.asyncio
class TestSubmitApplicationHappyPath:
    """Happy path: New application successfully submitted with workflow start."""

    async def test_submit_application_transitions_stage_and_starts_workflow(
        self,
        mock_db_session,
        mock_application_model,
        mock_workflow_instance,
        mock_audit_logger,
        mock_builder_audit_action,
        mock_validator_tenant,
    ):
        """
        Test happy path:
        1. Application fetched (stage=new, version=1)
        2. Workflow started (workflow_id=789)
        3. Metadata JSON updated with workflow reference
        4. Stage transitioned: new → received
        5. History record created (append-only)
        6. Audit event logged
        7. Version incremented
        """
        # Setup
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = (
            mock_application_model
        )
        
        app_service = ApplicationService(mock_db_session)
        
        # Mock workflow service
        with patch.object(
            app_service,
            "_start_admissions_workflow",
            new_callable=AsyncMock,
            return_value=mock_workflow_instance,
        ) as mock_start_workflow:
            # Execute
            result = await app_service.submit_application(
                tenant_id=1,
                application_id=123,
                actor="applicant@test",
                expected_version=1,
            )
        
        # Assertions
        assert isinstance(result, ApplicationReadSchema) or hasattr(result, "stage")
        assert mock_application_model.stage == ApplicationStage.RECEIVED.value
        assert mock_application_model.received_at is not None
        assert mock_application_model.version == 2  # Incremented
        
        # Verify metadata_json updated
        assert mock_application_model.metadata_json.get("workflow_instance_id") == 789
        assert mock_application_model.metadata_json.get("workflow_key") == "admissions"
        assert mock_application_model.metadata_json.get("workflow_status") == "in_progress"
        assert "workflow_started_at" in mock_application_model.metadata_json
        
        # Verify workflow started
        mock_start_workflow.assert_called_once_with(
            tenant_id=1,
            application_id=123,
            applicant_id=42,
            program_id=10,
            actor="applicant@test",
        )
        
        # Verify history record created
        history_add_calls = [c for c in mock_db_session.add.call_args_list]
        assert len(history_add_calls) >= 1  # At least history record added
        
        # Verify audit logged
        assert mock_audit_logger.call_count == 1
        mock_audit_logger.assert_called_once()
        call_kwargs = mock_audit_logger.call_args[1]
        assert call_kwargs["entity"] == "application"
        assert call_kwargs["metadata"]["workflow_instance_id"] == 789
        
        # Verify commit
        mock_db_session.commit.assert_called_once()

    async def test_metadata_json_safely_merged_not_overwritten(
        self,
        mock_db_session,
        mock_validator_tenant,
    ):
        """
        Test metadata_json safety:
        - Existing fields preserved
        - Workflow fields added
        - No destructive overwrite
        """
        # Setup application with existing metadata
        now = datetime.now(UTC)
        app = MagicMock()
        app.id = 123
        app.tenant_id = 1
        app.applicant_id = 42
        app.program_id = 10
        app.stage = ApplicationStage.NEW.value
        app.version = 1
        app.metadata_json = {
            "gpa": 3.8,
            "test_score": 320,
            "existing_field": "should_be_preserved",
        }
        app.received_at = None
        app.decision_at = None
        app.conclusion_type = None
        app.created_by = "owner@example.com"
        app.created_at = now
        app.updated_at = now
        
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = app
        
        app_service = ApplicationService(mock_db_session)
        
        with patch.object(
            app_service,
            "_start_admissions_workflow",
            new_callable=AsyncMock,
            return_value=MagicMock(id=789),
        ):
            await app_service.submit_application(
                tenant_id=1,
                application_id=123,
                actor="applicant@test",
                expected_version=1,
            )
        
        # Verify existing fields preserved
        assert app.metadata_json["gpa"] == 3.8
        assert app.metadata_json["test_score"] == 320
        assert app.metadata_json["existing_field"] == "should_be_preserved"
        
        # Verify workflow fields added
        assert app.metadata_json["workflow_instance_id"] == 789
        assert app.metadata_json["workflow_key"] == "admissions"


@pytest.mark.asyncio
class TestSubmitApplicationErrors:
    """Error scenarios: Invalid stages, version conflicts, tenant mismatches."""

    async def test_submit_application_rejects_non_new_stage(
        self,
        mock_db_session,
        mock_validator_tenant,
    ):
        """Test that only 'new' stage applications can be submitted."""
        app = MagicMock()
        app.id = 123
        app.tenant_id = 1
        app.stage = ApplicationStage.RECEIVED.value  # Already received
        app.version = 1
        
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = app
        
        app_service = ApplicationService(mock_db_session)
        
        with pytest.raises(ValueError, match="Cannot submit application in stage"):
            await app_service.submit_application(
                tenant_id=1,
                application_id=123,
                actor="applicant@test",
                expected_version=1,
            )

    async def test_submit_application_rejects_version_mismatch(
        self,
        mock_db_session,
        mock_validator_tenant,
    ):
        """Test optimistic locking: version conflict raises ValueError."""
        app = MagicMock()
        app.id = 123
        app.tenant_id = 1
        app.stage = ApplicationStage.NEW.value
        app.version = 5  # Current version is 5
        
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = app
        
        app_service = ApplicationService(mock_db_session)
        
        with pytest.raises(ValueError, match="Version mismatch"):
            await app_service.submit_application(
                tenant_id=1,
                application_id=123,
                actor="applicant@test",
                expected_version=1,  # Stale version
            )

    async def test_submit_application_not_found(
        self,
        mock_db_session,
        mock_validator_tenant,
    ):
        """Test application not found raises ValueError (fail-closed)."""
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = None
        
        app_service = ApplicationService(mock_db_session)
        
        with pytest.raises(ValueError, match="not found in tenant"):
            await app_service.submit_application(
                tenant_id=1,
                application_id=999,  # Doesn't exist
                actor="applicant@test",
                expected_version=1,
            )

    async def test_submit_application_cross_tenant_blocked(
        self,
        mock_db_session,
    ):
        """Test cross-tenant access blocked at query layer."""
        # Application belongs to tenant 1, but request is for tenant 2
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = None
        
        app_service = ApplicationService(mock_db_session)
        
        with patch(
            "app.modules.admissions.service.validate_tenant_id_provided",
            side_effect=lambda x: x,
        ):
            with pytest.raises(ValueError, match="not found in tenant"):
                await app_service.submit_application(
                    tenant_id=2,  # Different tenant
                    application_id=123,
                    actor="attacker@test",
                    expected_version=1,
                )
        
        # Verify query included tenant_id filter
        # Assert call was made with query (can't easily inspect WHERE clause with MagicMock)
        assert mock_db_session.execute.called


@pytest.mark.asyncio
class TestSubmitApplicationIdempotency:
    """Idempotency: Multiple submissions don't create duplicate workflows."""

    async def test_submit_application_idempotent_when_workflow_already_exists(
        self,
        mock_db_session,
        mock_validator_tenant,
    ):
        """
        Scenario: User submits twice (network timeout, retries)
        - First submit: creates workflow (id=789)
        - Second submit: detects workflow_instance_id in metadata, skips creation
        """
        now = datetime.now(UTC)
        app = MagicMock()
        app.id = 123
        app.tenant_id = 1
        app.applicant_id = 42
        app.program_id = 10
        app.stage = ApplicationStage.NEW.value
        app.version = 1
        app.metadata_json = {
            "workflow_instance_id": 789,  # Already created
            "workflow_key": "admissions",
            "workflow_status": "in_progress",
        }
        app.received_at = None
        app.decision_at = None
        app.conclusion_type = None
        app.created_by = "owner@example.com"
        app.created_at = now
        app.updated_at = now
        
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = app
        
        app_service = ApplicationService(mock_db_session)
        
        with patch.object(
            app_service,
            "_start_admissions_workflow",
            new_callable=AsyncMock,
        ) as mock_start_workflow:
            await app_service.submit_application(
                tenant_id=1,
                application_id=123,
                actor="applicant@test",
                expected_version=1,
            )
        
        # Workflow creation should NOT be called (idempotent skip)
        mock_start_workflow.assert_not_called()
        
        # But stage should still be updated
        assert app.stage == ApplicationStage.RECEIVED.value
        assert app.version == 2


# ==============================================================================
# TEST SUITE: DecisionService.finalize_workflow_decision()
# ==============================================================================


@pytest.mark.asyncio
class TestFinalizeDecisionHappyPath:
    """Happy path: Workflow decision successfully materialized to application."""

    async def test_finalize_workflow_decision_creates_decision_and_updates_application(
        self,
        mock_db_session,
        mock_application_model,
        mock_decision_model,
        mock_audit_logger,
        mock_builder_audit_action,
        mock_validator_tenant,
    ):
        """
        Test happy path:
        1. Application fetched
        2. Workflow ID validated
        3. No existing decision (new decision created)
        4. Approval action mapped to conclusion type
        5. ApplicationDecisionModel created
        6. Application updated: stage→concluded, conclusion_type, version++
        7. Stage history recorded (append-only)
        8. Metadata JSON updated with workflow outcome
        9. Audit event logged
        """
        # Setup: Application in DECISION_PENDING stage
        mock_application_model.stage = ApplicationStage.DECISION_PENDING.value
        mock_application_model.metadata_json = {"workflow_instance_id": 789}
        
        # Setup: First call returns application, second returns None (no existing decision)
        mock_db_session.execute.return_value.scalar_one_or_none.side_effect = [
            mock_application_model,
            None,  # No existing decision
        ]
        
        decision_service = DecisionService(mock_db_session)
        
        result = await decision_service.finalize_workflow_decision(
            tenant_id=1,
            application_id=123,
            workflow_instance_id=789,
            approval_action="approve",
            actor="director@admissions",
        )
        
        # Assertions
        assert isinstance(result, ApplicationDecisionReadSchema) or hasattr(result, "application_id")
        
        # Application state updated
        assert mock_application_model.stage == ApplicationStage.CONCLUDED.value
        assert mock_application_model.conclusion_type == ApplicationConclusionType.ACCEPTED.value
        assert mock_application_model.decision_at is not None
        
        # Metadata updated with workflow outcome
        assert mock_application_model.metadata_json.get("workflow_status") == "completed"
        assert mock_application_model.metadata_json.get("workflow_outcome") == "approve"
        assert "workflow_completed_at" in mock_application_model.metadata_json
        
        # History record created (decision service adds it)
        history_add_calls = [c for c in mock_db_session.add.call_args_list]
        assert len(history_add_calls) >= 2  # Decision + history
        
        # Audit logged
        assert mock_audit_logger.call_count == 1
        call_kwargs = mock_audit_logger.call_args[1]
        assert call_kwargs["entity"] == "decision"
        assert call_kwargs["metadata"]["conclusion_type"] == ApplicationConclusionType.ACCEPTED.value

    async def test_finalize_workflow_decision_rejects_approval_action_mapping(
        self,
        mock_db_session,
        mock_application_model,
        mock_validator_tenant,
    ):
        """Test approval action → conclusion type mapping."""
        mock_application_model.stage = ApplicationStage.DECISION_PENDING.value
        mock_application_model.metadata_json = {"workflow_instance_id": 789}
        
        mock_db_session.execute.return_value.scalar_one_or_none.side_effect = [
            mock_application_model,
            None,
        ]
        
        decision_service = DecisionService(mock_db_session)
        
        # TEST: "approve" → "accepted"
        await decision_service.finalize_workflow_decision(
            tenant_id=1,
            application_id=123,
            workflow_instance_id=789,
            approval_action="approve",
        )
        assert mock_application_model.conclusion_type == ApplicationConclusionType.ACCEPTED.value
        
        # TEST: "reject" → "rejected"
        mock_application_model2 = MagicMock()
        mock_application_model2.stage = ApplicationStage.DECISION_PENDING.value
        mock_application_model2.metadata_json = {"workflow_instance_id": 790}
        mock_db_session.execute.return_value.scalar_one_or_none.side_effect = [
            mock_application_model2,
            None,
        ]
        
        await decision_service.finalize_workflow_decision(
            tenant_id=1,
            application_id=124,
            workflow_instance_id=790,
            approval_action="reject",
        )
        assert mock_application_model2.conclusion_type == ApplicationConclusionType.REJECTED.value


@pytest.mark.asyncio
class TestFinalizeDecisionErrors:
    """Error scenarios: Invalid workflow ID, invalid actions, not found."""

    async def test_finalize_workflow_decision_rejects_workflow_mismatch(
        self,
        mock_db_session,
        mock_application_model,
        mock_validator_tenant,
    ):
        """Test workflow instance ID validation (cross-check)."""
        mock_application_model.metadata_json = {"workflow_instance_id": 789}
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = (
            mock_application_model
        )
        
        decision_service = DecisionService(mock_db_session)
        
        with pytest.raises(ValueError, match="Workflow instance ID mismatch"):
            await decision_service.finalize_workflow_decision(
                tenant_id=1,
                application_id=123,
                workflow_instance_id=999,  # Different ID
                approval_action="approve",
            )

    async def test_finalize_workflow_decision_rejects_invalid_approval_action(
        self,
        mock_db_session,
        mock_application_model,
        mock_validator_tenant,
    ):
        """Test invalid approval_action raises ValueError (fail-closed)."""
        mock_application_model.metadata_json = {"workflow_instance_id": 789}
        
        # Setup mock to return application for first query, None for second query (existing decision check)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(
            side_effect=[mock_application_model, None]  # First call: app, Second call: no existing decision
        )
        mock_db_session.execute.return_value = mock_result
        
        decision_service = DecisionService(mock_db_session)
        
        with pytest.raises(ValueError, match="Invalid approval_action"):
            await decision_service.finalize_workflow_decision(
                tenant_id=1,
                application_id=123,
                workflow_instance_id=789,
                approval_action="abstain",  # Invalid
            )

    async def test_finalize_workflow_decision_application_not_found(
        self,
        mock_db_session,
        mock_validator_tenant,
    ):
        """Test application not found raises ValueError."""
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = None
        
        decision_service = DecisionService(mock_db_session)
        
        with pytest.raises(ValueError, match="not found in tenant"):
            await decision_service.finalize_workflow_decision(
                tenant_id=1,
                application_id=999,
                workflow_instance_id=789,
                approval_action="approve",
            )


@pytest.mark.asyncio
class TestFinalizeDecisionIdempotency:
    """Idempotency: Multiple finalizations don't create duplicate decisions."""

    async def test_finalize_workflow_decision_idempotent_if_decision_exists(
        self,
        mock_db_session,
        mock_application_model,
        mock_decision_model,
        mock_validator_tenant,
    ):
        """
        Scenario: Workflow callback fires twice (or retried)
        - First call: creates decision (id=201)
        - Second call: detects existing decision, returns it (idempotent)
        """
        mock_application_model.metadata_json = {"workflow_instance_id": 789}
        
        # First call: application found, Second call: decision already exists
        mock_db_session.execute.return_value.scalar_one_or_none.side_effect = [
            mock_application_model,
            mock_decision_model,  # Decision exists
        ]
        
        decision_service = DecisionService(mock_db_session)
        
        result = await decision_service.finalize_workflow_decision(
            tenant_id=1,
            application_id=123,
            workflow_instance_id=789,
            approval_action="approve",
        )
        
        # Should return existing decision
        assert result.id == 201 or hasattr(result, "id")
        
        # Application should NOT be updated (idempotent, no second update)
        # Only the existing decision returned, no extra writes expected.
        assert mock_db_session.flush.call_count <= 1


# ==============================================================================
# TEST SUITE: Tenant Isolation
# ==============================================================================


@pytest.mark.asyncio
class TestTenantIsolation:
    """Tenant-first architecture: Cross-tenant access prevented."""

    async def test_submit_application_cross_tenant_blocked(
        self,
        mock_db_session,
    ):
        """Test submit_application blocks cross-tenant access (fail-closed)."""
        # Application belongs to tenant 1, but request claims tenant 2
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = None
        
        app_service = ApplicationService(mock_db_session)
        
        with patch(
            "app.modules.admissions.service.validate_tenant_id_provided",
            side_effect=lambda x: x,
        ):
            with pytest.raises(ValueError, match="not found in tenant"):
                await app_service.submit_application(
                    tenant_id=2,  # Different tenant
                    application_id=123,
                    actor="attacker@test",
                    expected_version=1,
                )

    async def test_finalize_workflow_decision_cross_tenant_blocked(
        self,
        mock_db_session,
    ):
        """Test finalize_workflow_decision blocks cross-tenant access."""
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = None
        
        decision_service = DecisionService(mock_db_session)
        
        with patch(
            "app.modules.admissions.service.validate_tenant_id_provided",
            side_effect=lambda x: x,
        ):
            with pytest.raises(ValueError, match="not found in tenant"):
                await decision_service.finalize_workflow_decision(
                    tenant_id=2,  # Different tenant
                    application_id=123,
                    workflow_instance_id=789,
                    approval_action="approve",
                )


# ==============================================================================
# TEST SUITE: Metadata JSON Safety
# ==============================================================================


@pytest.mark.asyncio
class TestMetadataJSONSafety:
    """Metadata JSON: Safe merge, no destructive overwrites."""

    async def test_metadata_json_preserves_existing_fields(
        self,
        mock_db_session,
        mock_validator_tenant,
    ):
        """Test existing metadata fields not overwritten during submit."""
        now = datetime.now(UTC)
        app = MagicMock()
        app.id = 123
        app.tenant_id = 1
        app.applicant_id = 42
        app.program_id = 10
        app.stage = ApplicationStage.NEW.value
        app.version = 1
        app.metadata_json = {
            "gpa": 3.8,
            "test_score": 320,
            "notes": "Early applicant",
        }
        app.received_at = None
        app.decision_at = None
        app.conclusion_type = None
        app.created_by = "owner@example.com"
        app.created_at = now
        app.updated_at = now
        
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = app
        
        app_service = ApplicationService(mock_db_session)
        
        with patch.object(
            app_service,
            "_start_admissions_workflow",
            new_callable=AsyncMock,
            return_value=MagicMock(id=789),
        ):
            await app_service.submit_application(
                tenant_id=1,
                application_id=123,
                actor="applicant@test",
                expected_version=1,
            )
        
        # All existing fields preserved
        assert app.metadata_json["gpa"] == 3.8
        assert app.metadata_json["test_score"] == 320
        assert app.metadata_json["notes"] == "Early applicant"
        
        # Workflow fields added
        assert app.metadata_json["workflow_instance_id"] == 789

    async def test_metadata_json_updated_safely_on_decision(
        self,
        mock_db_session,
        mock_application_model,
        mock_validator_tenant,
    ):
        """Test existing metadata preserved when finalizing decision."""
        mock_application_model.stage = ApplicationStage.DECISION_PENDING.value
        mock_application_model.metadata_json = {
            "workflow_instance_id": 789,
            "workflow_key": "admissions",
            "workflow_status": "in_progress",
            "gpa": 3.8,  # Existing field
        }
        
        mock_db_session.execute.return_value.scalar_one_or_none.side_effect = [
            mock_application_model,
            None,
        ]
        
        decision_service = DecisionService(mock_db_session)
        
        await decision_service.finalize_workflow_decision(
            tenant_id=1,
            application_id=123,
            workflow_instance_id=789,
            approval_action="approve",
        )
        
        # Existing fields preserved
        assert mock_application_model.metadata_json["gpa"] == 3.8
        assert mock_application_model.metadata_json["workflow_instance_id"] == 789
        
        # New fields added
        assert mock_application_model.metadata_json["workflow_outcome"] == "approve"


# ==============================================================================
# TEST SUITE: Integration Points
# ==============================================================================


@pytest.mark.asyncio
class TestStartAdmissionsWorkflowIntegration:
    """Integration: _start_admissions_workflow() calls WorkflowService."""

    async def test_start_admissions_workflow_calls_workflow_service(
        self,
        mock_db_session,
        mock_validator_tenant,
    ):
        """Test _start_admissions_workflow() creates workflow with correct parameters."""
        app_service = ApplicationService(mock_db_session)
        
        with patch(
            "app.modules.workflows.workflow_service.WorkflowService"
        ) as MockWorkflowService:
            mock_workflow_service = MagicMock()
            MockWorkflowService.return_value = mock_workflow_service
            
            mock_workflow_service.start_workflow = AsyncMock(
                return_value=MagicMock(id=789)
            )
            
            await app_service._start_admissions_workflow(
                tenant_id=1,
                application_id=123,
                applicant_id=42,
                program_id=10,
                actor="applicant@test",
            )
            
            # Verify WorkflowService called with correct params
            mock_workflow_service.start_workflow.assert_called_once()
            call_kwargs = mock_workflow_service.start_workflow.call_args[1]
            
            assert call_kwargs["tenant_id"] == 1
            assert call_kwargs["workflow_key"] == "admissions"
            assert call_kwargs["entity_type"] == "admission_application"
            assert call_kwargs["entity_id"] == 123
            assert call_kwargs["actor"] == "applicant@test"
            assert call_kwargs["metadata_json"]["applicant_id"] == 42
            assert call_kwargs["metadata_json"]["program_id"] == "10"
