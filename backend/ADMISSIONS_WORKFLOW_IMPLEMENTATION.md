# Admissions ↔ Workflow Engine Integration - Implementation Roadmap

**Status**: Design Complete - Ready for Implementation  
**Target**: 5 implementation phases (5A-5F)  
**Duration Estimate**: 2-3 days  
**Risk Level**: Low (zero schema changes, backward compatible)

---

## Phase 5A: Admissions Service Extension

### Task 5A.1: Modify `ApplicationService` class

**File**: `app/modules/admissions/service.py`

**Changes**:
1. Import `WorkflowService` (lazy import in method to avoid circular dependency)
2. Add `submit_application()` method
3. Add `_start_admissions_workflow()` helper method

**Code to Add**:
```python
# At top of ApplicationService class

async def submit_application(
    self,
    tenant_id: int,
    application_id: int,
    actor: str,
    expected_version: int,
) -> ApplicationReadSchema:
    """
    Submit application (new → received) and start admissions workflow.
    
    Constraints:
    - tenant_id: fail-closed (mandatory)
    - expected_version: optimistic locking
    - application.stage must be "new"
    
    Returns:
        ApplicationReadSchema with workflow linkage in metadata_json
    
    Raises:
        ValueError: wrong stage, version conflict, not found
        PermissionError: tenant mismatch
        
    Audit events:
    - "application.submitted"
    - "workflow.started" (via WorkflowService)
    """
    tenant_id = validate_tenant_id_provided(tenant_id)
    
    # Fetch application
    application = self.db.execute(
        select(ApplicationModel).where(
            and_(
                ApplicationModel.id == application_id,
                ApplicationModel.tenant_id == tenant_id,
            )
        )
    ).scalar_one_or_none()
    
    if not application:
        raise ValueError(f"Application {application_id} not found in tenant {tenant_id}")
    
    # Validate optimistic lock
    if application.version != expected_version:
        raise ValueError(
            f"Version mismatch for application {application_id}: "
            f"expected {expected_version}, got {application.version}"
        )
    
    # Validate current stage
    if application.stage != ApplicationStage.NEW.value:
        raise ValueError(
            f"Cannot submit application in stage '{application.stage}'. "
            f"Only 'new' applications can be submitted."
        )
    
    # Check if workflow already started (idempotency)
    workflow_instance_id = application.metadata_json.get("workflow_instance_id")
    if not workflow_instance_id:
        workflow_instance = await self._start_admissions_workflow(
            tenant_id=tenant_id,
            application_id=application_id,
            applicant_id=application.applicant_id,
            program_id=application.program_id,
            actor=actor,
        )
        workflow_instance_id = workflow_instance.id
        
        # Store workflow reference
        application.metadata_json["workflow_instance_id"] = workflow_instance_id
        application.metadata_json["workflow_key"] = "admissions"
        application.metadata_json["workflow_status"] = "in_progress"
        application.metadata_json["workflow_started_at"] = _utc_now().isoformat()
    
    # Transition stage
    application.stage = ApplicationStage.RECEIVED.value
    application.received_at = _utc_now()
    application.version += 1
    
    # Record in history (append-only)
    stage_history = ApplicationStageHistoryModel(
        tenant_id=tenant_id,
        application_id=application_id,
        from_stage=ApplicationStage.NEW.value,
        to_stage=ApplicationStage.RECEIVED.value,
        reason="Application submitted by applicant",
        action=StageTransitionAction.MANUAL.value,
        actor_id=actor,
        created_at=_utc_now(),
        metadata_json={"workflow_instance_id": workflow_instance_id, "trigger_type": "user_submission"},
    )
    self.db.add(stage_history)
    
    self.db.flush()
    
    # Audit logging
    log_admin_action(
        actor=actor,
        action=build_audit_action("admissions", "application", "submit"),
        path=f"/internal/admissions/applications/{application_id}/submit",
        client_ip="service",
        entity="application",
        metadata={
            "resource_id": str(application_id),
            "workflow_instance_id": workflow_instance_id,
            "stage_transition": f"{ApplicationStage.NEW.value} → {ApplicationStage.RECEIVED.value}",
        },
        tenant_id=tenant_id,
    )
    
    self.db.commit()
    return ApplicationReadSchema.model_validate(application)


async def _start_admissions_workflow(
    self,
    tenant_id: int,
    application_id: int,
    applicant_id: int,
    program_id: int,
    actor: str,
) -> "WorkflowInstanceReadSchema":  # From workflows module
    """
    Internal helper: Start admissions workflow for an application.
    
    Fires up initial task assignment (document_review → admissions_staff).
    """
    from app.modules.workflows.workflow_service import WorkflowService
    
    workflow_service = WorkflowService(self.db)
    
    workflow_instance = await workflow_service.start_workflow(
        tenant_id=tenant_id,
        workflow_key="admissions",
        entity_type="admission_application",
        entity_id=application_id,
        actor=actor,
        metadata_json={
            "applicant_id": applicant_id,
            "application_id": application_id,
            "program_id": str(program_id),
        },
    )
    
    return workflow_instance
```

### Task 5A.2: Create `DecisionService` class

**File**: `app/modules/admissions/service.py` (new class)

**Code to Add**:
```python
# New section at end of file

class DecisionService:
    """Service for application decision management."""

    def __init__(self, db_session: Session):
        self.db = db_session

    async def finalize_workflow_decision(
        self,
        tenant_id: int,
        application_id: int,
        workflow_instance_id: int,
        approval_action: str,
        actor: str = "system@workflow",
    ) -> ApplicationDecisionReadSchema:
        """
        Finalize admission decision based on workflow outcome.
        
        Called by: WorkflowService.on_workflow_completed() callback
        
        Workflow Action Mapping:
        - "approve" → conclusion_type="accepted"
        - "reject" → conclusion_type="rejected"
        
        Transaction:
        1. Validate application exists and matches workflow instance
        2. Check if decision already exists (idempotency)
        3. Create ApplicationDecisionModel
        4. Update application: stage=concluded, conclusion_type, decision_at
        5. Record stage transition in history
        6. Audit log
        7. Commit
        
        Args:
            tenant_id: Tenant (mandatory, fail-closed)
            application_id: Application to finalize
            workflow_instance_id: Workflow that completed (validation)
            approval_action: "approve" or "reject"
            actor: Decision maker (default: system)
        
        Returns:
            ApplicationDecisionReadSchema
        
        Raises:
            ValueError: application not found, workflow mismatch, invalid action
            PermissionError: tenant mismatch
        """
        tenant_id = validate_tenant_id_provided(tenant_id)
        
        # Fetch application
        application = self.db.execute(
            select(ApplicationModel).where(
                and_(
                    ApplicationModel.id == application_id,
                    ApplicationModel.tenant_id == tenant_id,
                )
            )
        ).scalar_one_or_none()
        
        if not application:
            raise ValueError(f"Application {application_id} not found in tenant {tenant_id}")
        
        # Validate workflow instance ID
        stored_workflow_id = application.metadata_json.get("workflow_instance_id")
        if stored_workflow_id != workflow_instance_id:
            raise ValueError(
                f"Workflow instance ID mismatch for application {application_id}: "
                f"expected {stored_workflow_id}, got {workflow_instance_id}"
            )
        
        # Check if decision already exists (idempotency)
        existing_decision = self.db.execute(
            select(ApplicationDecisionModel).where(
                and_(
                    ApplicationDecisionModel.application_id == application_id,
                    ApplicationDecisionModel.tenant_id == tenant_id,
                )
            )
        ).scalar_one_or_none()
        
        if existing_decision:
            return ApplicationDecisionReadSchema.model_validate(existing_decision)
        
        # Map approval action to conclusion type
        if approval_action == "approve":
            conclusion_type = ApplicationConclusionType.ACCEPTED.value
        elif approval_action == "reject":
            conclusion_type = ApplicationConclusionType.REJECTED.value
        else:
            raise ValueError(
                f"Invalid approval_action '{approval_action}'. Must be 'approve' or 'reject'."
            )
        
        # Update application
        application.stage = ApplicationStage.CONCLUDED.value
        application.conclusion_type = conclusion_type
        application.decision_at = _utc_now()
        
        # Update metadata
        application.metadata_json["workflow_status"] = "completed"
        application.metadata_json["workflow_outcome"] = approval_action
        application.metadata_json["workflow_completed_at"] = _utc_now().isoformat()
        
        # Create decision record
        decision = ApplicationDecisionModel(
            tenant_id=tenant_id,
            application_id=application_id,
            decision_type="workflow_auto",
            conclusion_type=conclusion_type,
            reasoning=f"Workflow decision: {approval_action}",
            decided_by_id=actor,
            decided_at=_utc_now(),
            metadata_json={
                "workflow_instance_id": workflow_instance_id,
                "approval_action": approval_action,
                "decision_source": "workflow_engine",
            },
        )
        self.db.add(decision)
        
        # Record stage transition
        stage_history = ApplicationStageHistoryModel(
            tenant_id=tenant_id,
            application_id=application_id,
            from_stage=ApplicationStage.DECISION_PENDING.value,
            to_stage=ApplicationStage.CONCLUDED.value,
            reason=f"Workflow completed with decision: {approval_action}",
            action=StageTransitionAction.AUTOMATED.value,
            actor_id=actor,
            created_at=_utc_now(),
            metadata_json={
                "workflow_instance_id": workflow_instance_id,
                "trigger_type": "workflow_completion",
                "approval_action": approval_action,
            },
        )
        self.db.add(stage_history)
        
        self.db.flush()
        
        # Audit logging
        log_admin_action(
            actor=actor,
            action=build_audit_action("admissions", "decision", "finalize"),
            path=f"/internal/admissions/applications/{application_id}/decision",
            client_ip="service",
            entity="decision",
            metadata={
                "resource_id": str(application_id),
                "workflow_instance_id": workflow_instance_id,
                "conclusion_type": conclusion_type,
                "approval_action": approval_action,
            },
            tenant_id=tenant_id,
        )
        
        self.db.commit()
        return ApplicationDecisionReadSchema.model_validate(decision)
```

### Task 5A.3: Add Schemas

**File**: `app/modules/admissions/schemas.py`

**Add to file**:
```python
class ApplicationSubmitRequestSchema(BaseModel):
    """Request schema for submitting an application."""
    expected_version: int = Field(..., ge=1, description="Expected version for optimistic locking")

    model_config = {"json_schema_extra": {"example": {"expected_version": 1}}}
```

### Checklist 5A

- [ ] Add `submit_application()` method to `ApplicationService`
- [ ] Add `_start_admissions_workflow()` helper method
- [ ] Create `DecisionService` class with `finalize_workflow_decision()` method
- [ ] Add `ApplicationSubmitRequestSchema` to schemas.py
- [ ] Verify imports: `WorkflowService`, `build_audit_action`, `log_admin_action`
- [ ] Run `python -m py_compile app/modules/admissions/service.py`
- [ ] ✅ Code compiles without errors

---

## Phase 5B: Workflow Engine Callback Integration

### Task 5B.1: Add workflow completion callback to `WorkflowService`

**File**: `app/modules/workflows/workflow_service.py`

**Add New Method**:
```python
async def on_workflow_completed(
    self,
    tenant_id: int,
    workflow_instance_id: int,
) -> None:
    """
    Callback invoked when workflow reaches END step and transitions to COMPLETED status.
    
    Dispatches to entity-specific handlers based on workflow_key and entity_type.
    
    Called by: WorkflowRuntimeEngine.execute_transition() when transitioning to END
    
    Current Handlers:
    - entity_type="admission_application": DecisionService.finalize_workflow_decision()
    
    Future Handlers:
    - entity_type="student_request": StudentRequestService.finalize_...()
    - entity_type="faculty_hiring": FacultyHiringService.finalize_...()
    
    Fire-and-Forget Pattern:
    - Exceptions are logged but not propagated
    - Allows workflow completion without blocking on callback failures
    
    Args:
        tenant_id: Tenant (mandatory, fail-closed)
        workflow_instance_id: Workflow instance that completed
    
    Returns:
        None (async fire-and-forget)
    
    Exceptions:
        All exceptions logged via audit_action, not raised to caller
    """
    tenant_id = validate_tenant_id_provided(tenant_id)
    
    try:
        # Fetch workflow instance
        workflow_instance = self.db.execute(
            select(WorkflowInstanceModel).where(
                and_(
                    WorkflowInstanceModel.id == workflow_instance_id,
                    WorkflowInstanceModel.tenant_id == tenant_id,
                )
            )
        ).scalar_one_or_none()
        
        if not workflow_instance:
            raise ValueError(f"Workflow instance {workflow_instance_id} not found in tenant {tenant_id}")
        
        # Get latest approval (final decision)
        final_approval = self.db.execute(
            select(WorkflowApprovalModel)
            .where(
                and_(
                    WorkflowApprovalModel.workflow_instance_id == workflow_instance_id,
                    WorkflowApprovalModel.tenant_id == tenant_id,
                )
            )
            .order_by(desc(WorkflowApprovalModel.created_at))
            .limit(1)
        ).scalar_one_or_none()
        
        if not final_approval:
            raise ValueError(
                f"No approval found for completed workflow instance {workflow_instance_id}"
            )
        
        # Dispatch based on entity type
        if workflow_instance.entity_type == "admission_application":
            await self._dispatch_admissions_decision(
                tenant_id=tenant_id,
                workflow_instance_id=workflow_instance_id,
                entity_id=workflow_instance.entity_id,
                final_approval=final_approval,
            )
        # Future: add other entity type handlers here
        
    except Exception as exc:
        # Log failure but don't propagate
        log_admin_action(
            actor="system@workflow",
            action=build_audit_action("workflows", "callback", "on_workflow_completed_failure"),
            path=f"/internal/workflows/instances/{workflow_instance_id}/on_workflow_completed",
            client_ip="service",
            entity="workflow",
            metadata={
                "workflow_instance_id": workflow_instance_id,
                "error": str(exc),
            },
            tenant_id=tenant_id,
        )


async def _dispatch_admissions_decision(
    self,
    tenant_id: int,
    workflow_instance_id: int,
    entity_id: int,
    final_approval: WorkflowApprovalModel,
) -> None:
    """Internal helper for admissions decision dispatch."""
    from app.modules.admissions.service import DecisionService
    
    decision_service = DecisionService(self.db)
    await decision_service.finalize_workflow_decision(
        tenant_id=tenant_id,
        application_id=entity_id,
        workflow_instance_id=workflow_instance_id,
        approval_action=final_approval.action.value,
        actor=final_approval.actor_id,
    )
```

### Task 5B.2: Modify `execute_transition()` to invoke callback

**File**: `app/modules/workflows/workflow_engine.py`

**Modify `execute_transition()` method** (find the section where END step is handled):

```python
# In execute_transition(), after transitioning to END step:

if next_step.step_type == WorkflowStepType.END:
    # Mark workflow as completed
    workflow_instance.current_step_id = next_step.id
    workflow_instance.status = WorkflowInstanceStatus.COMPLETED
    
    # NEW: Invoke completion callback (fire-and-forget)
    await self._dispatch_workflow_completion(
        tenant_id=tenant_id,
        workflow_instance_id=workflow_instance.id,
    )

# Add new method to WorkflowRuntimeEngine class:

async def _dispatch_workflow_completion(
    self,
    tenant_id: int,
    workflow_instance_id: int,
) -> None:
    """Dispatch workflow completion callback (fire-and-forget)."""
    workflow_service = WorkflowService(self.db)
    try:
        await workflow_service.on_workflow_completed(
            tenant_id=tenant_id,
            workflow_instance_id=workflow_instance_id,
        )
    except Exception:
        # Callback failures are logged by on_workflow_completed()
        pass
```

### Checklist 5B

- [ ] Add `on_workflow_completed()` method to `WorkflowService`
- [ ] Add `_dispatch_admissions_decision()` helper to `WorkflowService`
- [ ] Modify `execute_transition()` in `WorkflowRuntimeEngine` to call `_dispatch_workflow_completion()`
- [ ] Add `_dispatch_workflow_completion()` method to `WorkflowRuntimeEngine`
- [ ] Verify imports: `DecisionService`, `desc` (from sqlalchemy)
- [ ] Run `python -m py_compile app/modules/workflows/workflow_engine.py`
- [ ] Run `python -m py_compile app/modules/workflows/workflow_service.py`
- [ ] ✅ Code compiles without errors

---

## Phase 5C: API Router Enhancement

### Task 5C.1: Add submit endpoint to Admissions router

**File**: `app/modules/admissions/router.py`

**Add New Endpoint** (after existing application endpoints):

```python
@router.post(
    "/applications/{application_id}/submit",
    response_model=ApplicationReadSchema,
    responses={400: {"model": ErrorDetailResponse}, 403: {"model": ErrorDetailResponse}, 404: {"model": ErrorDetailResponse}, 409: {"model": ErrorDetailResponse}},
    status_code=status.HTTP_200_OK,
)
async def submit_application_endpoint(
    application_id: int,
    payload: dict[str, Any] = Body(...),
    actor: Actor = None,
    _: Annotated[None, Depends(permission_dependency("admissions.write"))] = None,
    tenant: TrustedTenant = None,
    db: AdmissionsDb = None,
) -> ApplicationReadSchema:
    """
    Submit application and trigger admissions workflow.
    
    Transitions: new → received
    Workflow: Starts admissions workflow instance for document review → decision flow
    
    RBAC: admissions.write
    
    Request Body:
    {
        "expected_version": 1
    }
    
    Response:
    {
        "id": 123,
        "stage": "received",
        "metadata_json": {
            "workflow_instance_id": 456,
            "workflow_key": "admissions",
            "workflow_status": "in_progress",
            "workflow_started_at": "2026-03-01T10:00:00Z"
        },
        ...
    }
    
    Errors:
    - 400: Invalid request (wrong version, wrong stage)
    - 403: Permission denied (not admissions.write)
    - 404: Application not found (cross-tenant access attempt?)
    - 409: Conflict (version mismatch, already submitted)
    """
    request_model = _parse_payload(ApplicationSubmitRequestSchema, payload)
    service = ApplicationService(db)
    try:
        return await service.submit_application(
            tenant_id=int(tenant["id"]),
            application_id=application_id,
            actor=actor,
            expected_version=request_model.expected_version,
        )
    except PermissionError as exc:
        raise permission_error_to_http(exc) from exc
    except IntegrityError as exc:
        raise integrity_error_to_http(exc) from exc
    except ValueError as exc:
        raise _map_service_error(exc) from exc
```

### Task 5C.2: Update router imports

**File**: `app/modules/admissions/router.py` (at top)

```python
from app.modules.admissions.service import (
    ApplicantService,
    ApplicationService,
    DecisionService,  # NEW
    DocumentService,
    StageTransitionService,
)
from app.modules.admissions.schemas import (
    # ... existing imports ...
    ApplicationSubmitRequestSchema,  # NEW
)
```

### Task 5C.3: Update service exports

**File**: `app/modules/admissions/__init__.py`

```python
from app.modules.admissions.service import (
    ApplicantService,
    ApplicationService,
    DecisionService,  # NEW
    DocumentService,
    StageTransitionService,
)

__all__ = [
    "ApplicantService",
    "ApplicationService",
    "DecisionService",  # NEW
    "DocumentService",
    "StageTransitionService",
]
```

### Checklist 5C

- [ ] Add `submit_application_endpoint` to admissions router
- [ ] Add imports: `ApplicationSubmitRequestSchema`, `DecisionService`
- [ ] Update `__init__.py` exports
- [ ] Run `python -m py_compile app/modules/admissions/router.py`
- [ ] ✅ Code compiles without errors

---

## Phase 5D: Testing & Validation

### Task 5D.1: Create integration test file

**File**: `tests/modules/admissions/test_workflow_integration.py`

```python
"""
Integration tests for Admissions ↔ Workflow Engine integration.

Tests:
- Application submission starts workflow
- Workflow completion materializes decision
- Idempotent submissions
- Tenant isolation
- Optimistic locking
- Error scenarios
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.modules.admissions.schemas import (
    ApplicationStage,
    ApplicationConclusionType,
    ApplicationReadSchema,
)
from app.modules.admissions.service import (
    ApplicationService,
    DecisionService,
)
from app.modules.workflows.schemas import WorkflowInstanceStatus


@pytest.mark.asyncio
async def test_submit_application_starts_workflow():
    """Test that submitting application starts admissions workflow."""
    # Setup
    db_session_mock = MagicMock()
    app = MagicMock()
    app.stage = ApplicationStage.NEW.value
    app.version = 1
    app.id = 123
    app.tenant_id = 1
    app.applicant_id = 42
    app.program_id = 10
    app.metadata_json = {}
    
    db_session_mock.execute.return_value.scalar_one_or_none.return_value = app
    
    # Mock WorkflowService
    with patch("app.modules.admissions.service.WorkflowService") as MockWorkflowService:
        mock_workflow_service = AsyncMock()
        MockWorkflowService.return_value = mock_workflow_service
        
        workflow_instance = MagicMock()
        workflow_instance.id = 789
        workflow_instance.status = WorkflowInstanceStatus.IN_PROGRESS
        mock_workflow_service.start_workflow.return_value = workflow_instance
        
        # Execute
        service = ApplicationService(db_session_mock)
        result = await service.submit_application(
            tenant_id=1,
            application_id=123,
            actor="applicant@test",
            expected_version=1,
        )
        
        # Assert
        assert result.stage == ApplicationStage.RECEIVED.value
        assert result.metadata_json.get("workflow_instance_id") == 789
        mock_workflow_service.start_workflow.assert_called_once()


@pytest.mark.asyncio
async def test_workflow_completion_finalizes_decision():
    """Test that workflow completion creates decision and updates application."""
    # Setup
    db_session_mock = MagicMock()
    app = MagicMock()
    app.id = 123
    app.tenant_id = 1
    app.stage = ApplicationStage.DECISION_PENDING.value
    app.metadata_json = {"workflow_instance_id": 789}
    
    db_session_mock.execute.return_value.scalar_one_or_none.side_effect = [
        app,  # Application query
        None,  # Decision query (doesn't exist)
    ]
    
    # Execute
    service = DecisionService(db_session_mock)
    result = await service.finalize_workflow_decision(
        tenant_id=1,
        application_id=123,
        workflow_instance_id=789,
        approval_action="approve",
        actor="director@admissions",
    )
    
    # Assert
    assert result.application_id == 123
    assert app.stage == ApplicationStage.CONCLUDED.value
    assert app.conclusion_type == ApplicationConclusionType.ACCEPTED.value
    db_session_mock.commit.assert_called_once()


@pytest.mark.asyncio
async def test_idempotent_workflow_submission():
    """Test that submitting twice doesn't create duplicate workflow instances."""
    # Setup
    db_session_mock = MagicMock()
    app = MagicMock()
    app.id = 123
    app.tenant_id = 1
    app.stage = ApplicationStage.NEW.value
    app.version = 1
    app.metadata_json = {"workflow_instance_id": 789}  # Already created
    
    db_session_mock.execute.return_value.scalar_one_or_none.return_value = app
    
    # Mock WorkflowService
    with patch("app.modules.admissions.service.WorkflowService") as MockWorkflowService:
        mock_workflow_service = AsyncMock()
        MockWorkflowService.return_value = mock_workflow_service
        
        # Execute
        service = ApplicationService(db_session_mock)
        await service.submit_application(
            tenant_id=1,
            application_id=123,
            actor="applicant@test",
            expected_version=1,
        )
        
        # Assert: WorkflowService.start_workflow NOT called (idempotent skip)
        mock_workflow_service.start_workflow.assert_not_called()


@pytest.mark.asyncio
async def test_invalid_approval_action_raises_error():
    """Test that invalid approval_action is rejected."""
    db_session_mock = MagicMock()
    app = MagicMock()
    app.id = 123
    app.tenant_id = 1
    app.metadata_json = {"workflow_instance_id": 789}
    
    db_session_mock.execute.return_value.scalar_one_or_none.side_effect = [
        app,
        None,
    ]
    
    service = DecisionService(db_session_mock)
    
    with pytest.raises(ValueError, match="Invalid approval_action"):
        await service.finalize_workflow_decision(
            tenant_id=1,
            application_id=123,
            workflow_instance_id=789,
            approval_action="abstain",  # Invalid
        )


@pytest.mark.asyncio
async def test_cross_tenant_access_blocked():
    """Test that cross-tenant access is blocked (fail-closed)."""
    db_session_mock = MagicMock()
    db_session_mock.execute.return_value.scalar_one_or_none.return_value = None  # Not found
    
    service = ApplicationService(db_session_mock)
    
    with pytest.raises(ValueError, match="not found in tenant"):
        await service.submit_application(
            tenant_id=2,  # Tenant B
            application_id=123,  # Belongs to Tenant A
            actor="attacker@test",
            expected_version=1,
        )


@pytest.mark.asyncio
async def test_version_mismatch_rejected():
    """Test that optimistic locking prevents stale-read updates."""
    db_session_mock = MagicMock()
    app = MagicMock()
    app.id = 123
    app.tenant_id = 1
    app.stage = ApplicationStage.NEW.value
    app.version = 5  # Current version
    
    db_session_mock.execute.return_value.scalar_one_or_none.return_value = app
    
    service = ApplicationService(db_session_mock)
    
    with pytest.raises(ValueError, match="Version mismatch"):
        await service.submit_application(
            tenant_id=1,
            application_id=123,
            actor="applicant@test",
            expected_version=1,  # Stale version
        )


@pytest.mark.asyncio
async def test_wrong_stage_rejected():
    """Test that only 'new' applications can be submitted."""
    db_session_mock = MagicMock()
    app = MagicMock()
    app.id = 123
    app.tenant_id = 1
    app.stage = ApplicationStage.CONCLUDED.value  # Already finished
    app.version = 1
    
    db_session_mock.execute.return_value.scalar_one_or_none.return_value = app
    
    service = ApplicationService(db_session_mock)
    
    with pytest.raises(ValueError, match="Cannot submit application in stage"):
        await service.submit_application(
            tenant_id=1,
            application_id=123,
            actor="applicant@test",
            expected_version=1,
        )


@pytest.mark.asyncio
async def test_idempotent_decision_creation():
    """Test that finalizing decision twice doesn't create duplicates."""
    db_session_mock = MagicMock()
    app = MagicMock()
    app.id = 123
    app.tenant_id = 1
    app.metadata_json = {"workflow_instance_id": 789}
    
    existing_decision = MagicMock()
    existing_decision.id = 201
    
    db_session_mock.execute.return_value.scalar_one_or_none.side_effect = [
        app,
        existing_decision,  # Decision already exists
    ]
    
    service = DecisionService(db_session_mock)
    result = await service.finalize_workflow_decision(
        tenant_id=1,
        application_id=123,
        workflow_instance_id=789,
        approval_action="approve",
    )
    
    # Assert: Returned existing decision (not creating new one)
    assert result.id == 201
    # db_session_mock.add() should be called fewer times
    add_calls = [c for c in db_session_mock.method_calls if "add" in str(c)]
    # Only application update, no new decision added
    assert len(add_calls) <= 1
```

### Task 5D.2: Run tests

```bash
cd /home/sbs/AI/backend

# Run newly created tests
python -m pytest tests/modules/admissions/test_workflow_integration.py -v

# Run all admissions tests
python -m pytest tests/modules/admissions/ -v

# Run all tests (to check for regressions)
python -m pytest tests/ -v
```

### Checklist 5D

- [ ] Create `test_workflow_integration.py` with 8+ test cases
- [ ] All tests are async (use `@pytest.mark.asyncio`)
- [ ] All tests use mocked DB sessions
- [ ] Run tests: `pytest tests/modules/admissions/test_workflow_integration.py -v`
- [ ] ✅ All tests pass
- [ ] Check for import errors: `python -m py_compile tests/modules/admissions/test_workflow_integration.py`
- [ ] ✅ Code compiles without errors

---

## Phase 5E: Integration with Workflow Template Loading

### Task 5E.1: Pre-requisite check

Verify Admissions workflow template exists:

```bash
cd /home/sbs/AI/backend

# Check if template file exists
test -f app/modules/workflows/templates/admissions_workflow.json && echo "✓ Template exists" || echo "✗ Template missing"

# Verify template JSON syntax
python -m json.tool app/modules/workflows/templates/admissions_workflow.json > /dev/null && echo "✓ Valid JSON" || echo "✗ Invalid JSON"
```

### Task 5E.2: Load template in test tenant

```bash
cd /home/sbs/AI/backend

# Load admissions workflow template
python -m app.modules.workflows.load_templates \
    --tenant-id 1 \
    --actor system@bootstrap \
    --templates admissions

# Expected output: "Loaded template: admissions"
```

### Task 5E.3: Update tenant bootstrap script

**File**: `scripts/init-tenant.sh` (if exists) or create new

```bash
#!/bin/bash
# Tenant initialization script

TENANT_ID=${1:-1}
BACKEND_DIR="/home/sbs/AI/backend"

echo "Initializing tenant $TENANT_ID..."

cd "$BACKEND_DIR"

# Load workflow templates
python -m app.modules.workflows.load_templates \
    --tenant-id "$TENANT_ID" \
    --actor system@tenant-bootstrap \
    --templates admissions student_request faculty_hiring

echo "✓ Tenant $TENANT_ID initialized"
```

### Checklist 5E

- [ ] Verify admissions workflow template exists and is valid JSON
- [ ] Manually load template using CLI command
- [ ] ✅ Template loads successfully (check DB)
- [ ] Update tenant bootstrap script to load templates
- [ ] Document in deployment runbook

---

## Phase 5F: End-to-End Testing & Deployment

### Task 5F.1: Manual E2E test (staging)

**Scenario**: Submit application → Complete workflow → Verify decision

**Steps**:
1. Create applicant via API
2. Create application in "new" stage
3. Call: `POST /api/admin/admissions/applications/{app_id}/submit`
4. Verify: Response has `workflow_instance_id` in `metadata_json`
5. Manually fetch workflow instance via `/api/admin/workflows/instances`
6. Manually complete each task: document_review → dept_approval → dean_approval → registrar_approval → final_decision
7. Verify: Application stage transitioned to "concluded"
8. Verify: ApplicationDecisionModel created with conclusion_type="accepted"
9. Check audit logs for all events

### Task 5F.2: Verify RBAC

**Test**: Only users with `admissions.write` can submit

```bash
# Test without permission: should fail with 403
curl -X POST \
    http://nginx/api/admin/admissions/applications/123/submit \
  -H "Authorization: Bearer <JWT_WITHOUT_ADMISSIONS_WRITE>" \
  -H "Content-Type: application/json" \
  -d '{"expected_version": 1}'

# Expected: HTTP 403 Forbidden

# Test with permission: should succeed
curl -X POST \
    http://nginx/api/admin/admissions/applications/123/submit \
  -H "Authorization: Bearer <JWT_WITH_ADMISSIONS_WRITE>" \
  -H "Content-Type: application/json" \
  -d '{"expected_version": 1}'

# Expected: HTTP 200 OK
```

### Task 5F.3: Verify Audit Logging

**Check PostgreSQL audit tables**:

```sql
-- Admissions audit logs
SELECT * FROM app_audit_logs
WHERE entity = 'application'
  AND action ILIKE '%submit%'
ORDER BY logged_at DESC
LIMIT 5;

-- Workflow audit logs
SELECT * FROM app_audit_logs
WHERE entity = 'workflow'
ORDER BY logged_at DESC
LIMIT 10;

-- Decision logs
SELECT * FROM app_audit_logs
WHERE entity = 'decision'
  AND action ILIKE '%finalize%'
ORDER BY logged_at DESC
LIMIT 5;
```

### Task 5F.4: Verify Backward Compatibility

**Test**: Old applications without workflow linkage still work

```python
# Application without workflow_instance_id in metadata_json
app = ApplicationModel(
    tenant_id=1,
    applicant_id=42,
    stage=ApplicationStage.NEW.value,
    metadata_json={},  # No workflow reference
)

# Should still be retrievable, queryable, etc.
service = ApplicationService(db)
result = await service.get_application(tenant_id=1, application_id=app.id)
assert result.stage == "new"
```

### Task 5F.5: Rollback Plan

**No schema changes** → Rollback is simple:
1. Revert code changes (git revert commit)
2. Redeploy old app version
3. Existing workflow instances stay in DB (no harm)
4. New submissions don't trigger workflows (fail-safe)

### Checklist 5F

- [ ] Manual E2E test: submit → complete → verify
- [ ] RBAC test: permission check working
- [ ] Audit logs: all events recorded
- [ ] Backward compatibility: old apps still work
- [ ] Rollback plan documented
- [ ] ✅ Ready for production deployment

---

## Implementation Timeline

| Phase | Tasks | Hours | Dependencies |
|---|---|---|---|
| 5A | Service layer (submit + decision) | 3-4h | None |
| 5B | Workflow callback integration | 2-3h | 5A |
| 5C | Router endpoints | 1-2h | 5A, 5B |
| 5D | Testing & validation | 2-3h | 5A, 5B, 5C |
| 5E | Template integration | 0.5-1h | 5D |
| 5F | E2E testing & deployment | 1-2h | 5E |
| **Total** | **All phases** | **10-15h** | **Sequential** |

---

## Pre-Deployment Checklist

- [ ] All code compiles (`py_compile`)
- [ ] All tests pass (`pytest`)
- [ ] Admissions workflow template loaded in test tenant
- [ ] Manual E2E test successful in staging
- [ ] RBAC verified
- [ ] Audit logging verified
- [ ] Backward compatibility tested
- [ ] Code review completed
- [ ] Rollback plan documented
- [ ] Deployment runbook updated
- [ ] Team notified of new endpoint: `POST /api/admin/admissions/applications/{app_id}/submit`

---

## Post-Deployment Monitoring

**Metrics to Monitor**:
1. Application submission rate (POST /submit endpoint)
2. Workflow completion rate
3. Decision materialization success rate
4. Callback failure rate (should be 0%)
5. Error rates by type (version conflicts, not found, etc.)

**Alerts**:
1. Alert if callback failure rate > 0%
2. Alert if decision materialization fails
3. Alert if submission fails (> 5% error rate)

**Logs to Check**:
1. Workflow completion events
2. Decision finalization events
3. Version conflict occurrences
4. Cross-tenant access attempts

---

## Success Criteria

✅ **Definition of Done**:
- All 5 phases implemented
- All tests passing
- Zero schema changes (metadata_json only)
- Tenant isolation enforced
- Audit logging complete
- RBAC verified
- E2E test successful
- Documentation complete
- Rollback plan ready
- Production deployment successful

🎉 **Result**: Admissions module now driven by Workflow Engine with full decision automation.
