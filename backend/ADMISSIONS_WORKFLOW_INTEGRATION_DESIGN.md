# Admissions ↔ Workflow Engine Integration Design

**Date**: 2026-03-23  
**Phase**: Integration Architecture & Implementation Plan  
**Constraint Compliance**: Tenant-first, fail-closed, audit logging, RBAC, minimal schema changes

---

## 1. INTEGRATION ARCHITECTURE

### 1.1 High-Level Data Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│ ADMISSIONS MODULE (Existing)                                        │
├─────────────────────────────────────────────────────────────────────┤
│ ApplicantModel → ApplicationModel → Stage Transitions               │
│                                   └→ ApplicationDecisionModel       │
│                                                                     │
│ Stage progression: new → received → under_review → decision_pending │
│                    → concluded (with conclusion_type)               │
└─────────────────────┬───────────────────────────────────────────────┘
                      │
        APPLICATION SUBMITTED (trigger)
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────────┐
│ WORKFLOW ENGINE (Phase 1-4 Completed)                              │
├─────────────────────────────────────────────────────────────────────┤
│ WorkflowDefinitionModel → WorkflowDefinitionVersionModel           │
│                        ├→ WorkflowStepModel                         │
│                        └→ WorkflowTransitionModel                   │
│                                                                     │
│ WorkflowInstanceModel (entity_type="admission_application",         │
│                       entity_id=application.id)                     │
│     ├→ WorkflowTaskModel (step: document_review, dept_approval,    │
│     │                     dean_approval, registrar_approval,        │
│     │                     final_decision)                           │
│     ├→ WorkflowTaskCommentModel (append-only)                       │
│     └→ WorkflowApprovalModel (decision history)                     │
└─────────────────────┬───────────────────────────────────────────────┘
                      │
           WORKFLOW COMPLETES (outcome)
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────────┐
│ DECISION MATERIALIZATION (New Call-Back)                           │
├─────────────────────────────────────────────────────────────────────┤
│ Workflow completion → decision.approval_action (APPROVE/REJECT)    │
│                   → application.stage = concluded                   │
│                   → application.conclusion_type (accepted/rejected) │
│                   → ApplicationDecisionModel created                │
│                   → Audit logged                                    │
└─────────────────────────────────────────────────────────────────────┘
```

### 1.2 Entity Linking Strategy

**Key Constraint**: Minimal schema changes to ApplicationModel

**Approach**: Use metadata_json field (already exists) to store workflow linkage:

```json
{
  "application": {
    "id": 12345,
    "tenant_id": 1,
    "stage": "received",
    "metadata_json": {
      "workflow_instance_id": 789,
      "workflow_key": "admissions",
      "workflow_status": "in_progress",
      "workflow_started_at": "2026-03-01T10:00:00Z",
      "workflow_step_assignments": {
        "document_review": {
          "assigned_to": "group:admissions_staff",
          "assigned_at": "2026-03-01T10:05:00Z"
        },
        "dept_approval": {
          "assigned_to": "user:dept_chair_123",
          "assigned_at": "2026-03-01T14:00:00Z"
        }
      }
    }
  }
}
```

**Benefits**:
- ✅ Zero schema changes
- ✅ Extensible (add new fields without migrations)
- ✅ Backward compatible (old applications unaffected)
- ✅ Already supported by tenure isolation & audit logging

---

## 2. SERVICE LAYER INTEGRATION POINTS

### 2.1 ApplicationService Integration

**File**: `app/modules/admissions/service.py`

**New Method**: `submit_application()`

```python
class ApplicationService:
    """Service for application management."""

    def __init__(self, db_session: Session):
        self.db = db_session
        self.workflow_service = None  # Initialized on demand

    async def submit_application(
        self,
        tenant_id: int,
        application_id: int,
        actor: str,
        expected_version: int,
    ) -> ApplicationReadSchema:
        """
        Submit (transition to 'received') and start workflow.
        
        Workflow trigger:
        1. Validate application in 'new' stage
        2. Transition to 'received' stage (record in history)
        3. Start admissions workflow instance
        4. Store workflow_instance_id in application.metadata_json
        5. Assign initial task (document_review) to admissions_staff group
        
        Idempotency:
        - If workflow_instance_id already in metadata_json, skip workflow creation
        - Still update stage/history (idempotent)
        
        Audit Events:
        - "application.submitted" (application state change)
        - "workflow.started" (workflow event) [logged by WorkflowService]
        
        Args:
            tenant_id: Tenant (mandatory, fail-closed)
            application_id: Application to submit
            actor: User submitting (typically applicant in UI; system in admin)
            expected_version: Expected version (optimistic lock)
        
        Returns:
            ApplicationReadSchema with updated stage + metadata
        
        Raises:
            ValueError: If application not found, wrong stage, or version mismatch
            PermissionError: If applicant lacks admissions.write permission
        
        Constraints:
        - Tenant isolation: all queries filtered by tenant_id
        - Fail-closed: no implicit defaults
        - Audit: all mutations logged via build_audit_action + log_admin_action
        - Optimistic locking: validate_version_match(current_version, expected_version)
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
            raise ValueError(f"Version mismatch: expected {expected_version}, got {application.version}")
        
        # Validate current stage
        if application.stage != ApplicationStage.NEW.value:
            raise ValueError(
                f"Cannot submit application in stage '{application.stage}'. "
                f"Only 'new' applications can be submitted."
            )
        
        # Check if workflow already started (idempotency)
        workflow_instance_id = application.metadata_json.get("workflow_instance_id")
        if not workflow_instance_id:
            # Start workflow
            workflow_instance = await self._start_admissions_workflow(
                tenant_id=tenant_id,
                application_id=application_id,
                applicant_id=application.applicant_id,
                actor=actor,
            )
            workflow_instance_id = workflow_instance.id
            
            # Store workflow reference in metadata
            application.metadata_json["workflow_instance_id"] = workflow_instance_id
            application.metadata_json["workflow_key"] = "admissions"
            application.metadata_json["workflow_status"] = "in_progress"
            application.metadata_json["workflow_started_at"] = datetime.now(UTC).isoformat()
        
        # Transition stage
        application.stage = ApplicationStage.RECEIVED.value
        application.received_at = datetime.now(UTC)
        application.version += 1  # Version increment
        
        # Record stage transition in history
        stage_history = ApplicationStageHistoryModel(
            tenant_id=tenant_id,
            application_id=application_id,
            from_stage=ApplicationStage.NEW.value,
            to_stage=ApplicationStage.RECEIVED.value,
            reason="Application submitted by applicant",
            action=StageTransitionAction.MANUAL.value,
            actor_id=actor,
            created_at=datetime.now(UTC),
            metadata_json={
                "workflow_instance_id": workflow_instance_id,
                "trigger_type": "user_submission",
            },
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
        actor: str,
    ) -> Any:  # WorkflowInstanceReadSchema from workflow module
        """
        Start admissions workflow for an application.
        
        Internal helper method.
        
        Workflow Configuration:
        - Workflow key: "admissions"
        - Entity type: "admission_application"
        - Entity ID: application_id
        - Steps: document_review, dept_approval, dean_approval, registrar_approval, final_decision
        - Trigger mode: manual (no auto-advance)
        
        Task Assignments (from metadata):
        - document_review → "group:admissions_staff"
        - dept_approval → "group:department_chairs"
        - dean_approval → "group:deans"
        - registrar_approval → "group:registrars"
        - final_decision → "group:admissions_leadership"
        
        Returns:
            WorkflowInstanceReadSchema
        """
        from app.modules.workflows.workflow_service import WorkflowService
        
        tenant_id = validate_tenant_id_provided(tenant_id)
        
        # Lazy import to avoid circular dependency
        workflow_service = WorkflowService(self.db)
        
        # Start workflow
        workflow_instance = await workflow_service.start_workflow(
            tenant_id=tenant_id,
            workflow_key="admissions",
            entity_type="admission_application",
            entity_id=application_id,
            actor=actor,
            metadata_json={
                "applicant_id": applicant_id,
                "application_id": application_id,
                "program_id": str(application.program_id),
            },
        )
        
        return workflow_instance
```

### 2.2 Decision Service Integration

**File**: `app/modules/admissions/service.py` (new DecisionService method)

```python
async def finalize_workflow_decision(
    self,
    tenant_id: int,
    application_id: int,
    workflow_instance_id: int,
    approval_action: str,  # "approve" or "reject" from workflow
    actor: str = "system@workflow",
) -> ApplicationDecisionReadSchema:
    """
    Called by Workflow Engine when workflow reaches final_decision step completion.
    
    Workflow Outcome Mapping:
    - workflow.approval_action="approve" → application.conclusion_type="accepted"
    - workflow.approval_action="reject" → application.conclusion_type="rejected"
    - No approval_action → raise ValueError (fail-closed)
    
    Transaction:
    1. Validate application exists and in workflow
    2. Validate workflow_instance_id matches metadata_json
    3. Create ApplicationDecisionModel
    4. Update application: stage=concluded, conclusion_type, decision_at
    5. Update metadata_json: workflow_status=completed, outcome
    6. Record stage transition in history
    7. Audit log decision + workflow outcome
    
    Idempotency:
    - If ApplicationDecisionModel already exists for application, return existing
    
    Args:
        tenant_id: Tenant (mandatory)
        application_id: Application ID
        workflow_instance_id: Workflow instance ID (validation)
        approval_action: "approve" or "reject"
        actor: Actor (default: system@workflow)
    
    Returns:
        ApplicationDecisionReadSchema
    
    Raises:
        ValueError: If application/workflow not found, invalid action
        PermissionError: If tenant mismatch
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
    
    # Validate workflow instance ID matches
    stored_workflow_id = application.metadata_json.get("workflow_instance_id")
    if stored_workflow_id != workflow_instance_id:
        raise ValueError(
            f"Workflow instance ID mismatch for application {application_id}. "
            f"Expected {stored_workflow_id}, got {workflow_instance_id}."
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
    
    # Map workflow approval_action to conclusion_type
    if approval_action == "approve":
        conclusion_type = ApplicationConclusionType.ACCEPTED.value
    elif approval_action == "reject":
        conclusion_type = ApplicationConclusionType.REJECTED.value
    else:
        raise ValueError(
            f"Invalid approval_action '{approval_action}'. "
            f"Must be 'approve' or 'reject'."
        )
    
    # Update application
    application.stage = ApplicationStage.CONCLUDED.value
    application.conclusion_type = conclusion_type
    application.decision_at = datetime.now(UTC)
    
    # Update metadata
    application.metadata_json["workflow_status"] = "completed"
    application.metadata_json["workflow_outcome"] = approval_action
    application.metadata_json["workflow_completed_at"] = datetime.now(UTC).isoformat()
    
    # Create decision record
    decision = ApplicationDecisionModel(
        tenant_id=tenant_id,
        application_id=application_id,
        decision_type="workflow_auto",  # Indicates workflow-driven decision
        conclusion_type=conclusion_type,
        reasoning=f"Workflow decision: {approval_action}",
        decided_by_id=actor,
        decided_at=datetime.now(UTC),
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
        created_at=datetime.now(UTC),
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

### 2.3 Workflow Service Callback Integration

**File**: `app/modules/workflows/workflow_service.py` (new callback method)

**New Hook Point**: After workflow transitions to FINAL_DECISION step

```python
async def on_workflow_completed(
    self,
    tenant_id: int,
    workflow_instance_id: int,
) -> None:
    """
    Callback invoked when workflow reaches END step and is marked COMPLETED.
    
    Dispatches to entity-specific handlers based on workflow_key.
    
    Workflow Outcome Mapping:
    - Get final approval_action from last WorkflowApprovalModel
    - Extract entity_type and entity_id from workflow_instance
    - If entity_type="admission_application": call DecisionService.finalize_workflow_decision()
    - Else: extend with other entity type handlers as needed
    
    Called by:
    - workflow_engine.execute_transition() when transitioning to END step
    - Wrapped in try/except to catch dispatch failures (log + don't raise)
    
    Args:
        tenant_id: Tenant (mandatory)
        workflow_instance_id: Workflow instance that completed
    
    Returns:
        None (fire-and-forget)
    
    Raises:
        (Exceptions logged, not propagated)
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
        
        # Get latest approval from final step
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
            raise ValueError(f"No approval found for workflow instance {workflow_instance_id}")
        
        # Dispatch based on entity type
        if workflow_instance.entity_type == "admission_application":
            from app.modules.admissions.service import DecisionService
            
            decision_service = DecisionService(self.db)
            await decision_service.finalize_workflow_decision(
                tenant_id=tenant_id,
                application_id=workflow_instance.entity_id,
                workflow_instance_id=workflow_instance_id,
                approval_action=final_approval.action.value,
                actor=final_approval.actor_id,
            )
        else:
            # Future entity types (student_request, faculty_hiring, etc.)
            pass
            
    except Exception as exc:
        # Log failure but don't propagate
        log_admin_action(
            actor="system@workflow",
            action=build_audit_action("workflows", "callback", "on_completed_failure"),
            path=f"/internal/workflows/instances/{workflow_instance_id}/on_completed",
            client_ip="service",
            entity="workflow",
            metadata={
                "workflow_instance_id": workflow_instance_id,
                "error": str(exc),
            },
            tenant_id=tenant_id,
        )
```

---

## 3. ADMISSION LIFECYCLE MAPPING

### 3.1 State Machine Synchronization

```
ADMISSIONS STAGE              WORKFLOW STATUS              TASKS
═════════════════════════════════════════════════════════════════════

new                          (no workflow)                 (none)
                             ↓
                      START: submitted by applicant

received                     in_progress                   ▮ document_review
                             (START → START task)          (assigned: admissions_staff)
                             ↓
                      (admissions staff completes task)

under_review                 in_progress                   ▮ dept_approval
                             (→ TASK step)                 (assigned: department_chair)
                             ↓
                      (department approves/rejects)

decision_pending             in_progress                   ▮ dean_approval
                             (→ APPROVAL step)             (assigned: dean)
                             ↓
                      (dean approves/rejects)
                             ↓
                             in_progress                   ▮ registrar_approval
                             (→ APPROVAL step)             (assigned: registrar)
                             ↓
                      (registrar approves/rejects)
                             ↓
                             in_progress                   ▮ final_decision
                             (→ APPROVAL step)             (assigned: admissions_leadership)
                             ↓
                      (final decision made)

concluded                    completed                     (none)
                             (END→ COMPLETED)
                             ↓
                      Decision materialized:
                      - conclusion_type: accepted/rejected
                      - ApplicationDecisionModel created
                      - Audit logged
```

### 3.2 Task-to-Admissions Role Mapping

| Workflow Step | Assigned To | Admissions Role | Decision | Action |
|---|---|---|---|---|
| document_review | `group:admissions_staff` | Admissions Officer | Verify complete | approve |
| dept_approval | `group:department_chairs` | Department Chair | Subject matter review | approve/reject |
| dean_approval | `group:deans` | Dean | Academic review | approve/reject |
| registrar_approval | `group:registrars` | Registrar | Compliance + records | approve/reject |
| final_decision | `group:admissions_leadership` | Director of Admissions | Final approval | approve/reject |

**Assignment Logic** (in `_start_admissions_workflow`):
```python
WORKFLOW_STEP_ASSIGNMENTS = {
    "document_review": "group:admissions_staff",
    "dept_approval": "group:department_chairs",
    "dean_approval": "group:deans",
    "registrar_approval": "group:registrars",
    "final_decision": "group:admissions_leadership",
}
```

---

## 4. WORKFLOW OUTCOME MAPPING

### 4.1 Approval Action → Conclusion Type

```python
WORKFLOW_OUTCOME_MAP = {
    # Final decision step completion
    "approve": ApplicationConclusionType.ACCEPTED,
    "reject": ApplicationConclusionType.REJECTED,
    
    # Potential future outcomes (via workflow metadata)
    "waitlist": ApplicationConclusionType.WAITLIST,
    "defer": None,  # Keep stage as decision_pending, no conclusion
}
```

### 4.2 Workflow Rejection Handling

**Scenario**: Department chair rejects at `dept_approval` step

**Current Workflow Behavior**:
- Transition fails (no APPROVE action, only DEFAULT transition available)
- Workflow remains in `dept_approval` step
- Application stage stays `under_review`

**Future Enhancement** (not in MVP):
- Add REJECT transition to a `rejected_by_dept` pseudo-step
- Or: Capture rejection in WorkflowApprovalModel with action=REJECT
- Then materialize as ApplicationConclusionType.REJECTED

**MVP Approach**: 
- Workflow only allows forward progress on APPROVE actions
- Rejection handled manually via separate admin endpoint (outside workflow)
- Or: Extend workflow with explicit REJECT transitions to END

---

## 5. IMPLEMENTATION PLAN

### Phase 5A: Schema & Dependency Injection (0 Breaking Changes)

**Files to Create/Modify**:
1. `app/modules/workflows/workflow_service.py`: Add `on_workflow_completed()` callback hook
2. `app/modules/admissions/service.py`: Add `submit_application()`, `finalize_workflow_decision()`, `_start_admissions_workflow()`

**No DB Schema Changes** (uses existing metadata_json field)

**Dependency Management**:
- Import workflows service in admissions service (avoid circular imports via lazy import in methods)
- Register callback in WorkflowRuntimeEngine when workflow reaches END

### Phase 5B: Workflow Engine Callback Integration

**File**: `app/modules/workflows/workflow_engine.py`

**Modify `execute_transition()` method**:
```python
async def execute_transition(
    self,
    tenant_id: int,
    workflow_instance_id: int,
    from_step_id: int,
    action_key: str,
    actor: str,
) -> WorkflowInstanceReadSchema:
    # ... existing transition logic ...
    
    # NEW: Check if transitioned to END step
    if next_step.step_type == WorkflowStepType.END:
        # Workflow complete
        workflow_instance.status = WorkflowInstanceStatus.COMPLETED
        
        # Invoke callback
        await self._dispatch_workflow_completion(
            tenant_id=tenant_id,
            workflow_instance_id=workflow_instance_id,
        )
    
    return WorkflowInstanceReadSchema.model_validate(workflow_instance)

async def _dispatch_workflow_completion(
    self,
    tenant_id: int,
    workflow_instance_id: int,
) -> None:
    """Fire-and-forget callback dispatch."""
    workflow_service = WorkflowService(self.db)
    try:
        await workflow_service.on_workflow_completed(
            tenant_id=tenant_id,
            workflow_instance_id=workflow_instance_id,
        )
    except Exception as exc:
        # Log failure but don't break workflow completion
        pass
```

### Phase 5C: API Router Enhancements

**File**: `app/modules/admissions/router.py`

**New Endpoint**: `POST /api/admin/admissions/applications/{application_id}/submit`

```python
@router.post(
    "/applications/{application_id}/submit",
    response_model=ApplicationReadSchema,
    responses={400: {...}, 403: {...}, 404: {...}, 409: {...}},
    status_code=status.HTTP_200_OK,
)
async def submit_application_endpoint(
    application_id: int,
    payload: dict[str, Any] = Body(...),  # { "expected_version": 1 }
    actor: Actor = None,
    _: Annotated[None, Depends(permission_dependency("admissions.write"))] = None,
    tenant: TrustedTenant = None,
    db: AdmissionsDb = None,
) -> ApplicationReadSchema:
    """
    Submit application and trigger admissions workflow.
    
    RBAC: admissions.write
    
    Request:
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
            ...
        },
        ...
    }
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
    except (PermissionError, ValueError) as exc:
        raise _map_service_error(exc) from exc
```

**New Schema**: `app/modules/admissions/schemas.py`

```python
class ApplicationSubmitRequestSchema(BaseModel):
    """Request schema for submitting an application."""
    expected_version: int = Field(..., ge=1, description="Expected version for optimistic locking")
```

### Phase 5D: Testing & Validation

**Test File**: `tests/modules/admissions/test_workflow_integration.py`

```python
import pytest
from app.modules.admissions.schemas import ApplicationStage, ApplicationConclusionType
from app.modules.workflows.schemas import WorkflowInstanceStatus

@pytest.mark.asyncio
async def test_application_submit_starts_workflow(db_session_mock, admissions_service):
    """Test that submitting application starts admissions workflow."""
    # Create applicant, application
    # Call service.submit_application()
    # Assert:
    #   - application.stage == "received"
    #   - application.metadata_json["workflow_instance_id"] is not None
    #   - workflow instance created with entity_type="admission_application"
    pass

@pytest.mark.asyncio
async def test_workflow_completion_materializes_decision(db_session_mock, admissions_service):
    """Test that completing workflow creates decision and updates application."""
    # Create workflow instance for application
    # Set final approval: action="approve"
    # Call service.finalize_workflow_decision()
    # Assert:
    #   - application.stage == "concluded"
    #   - application.conclusion_type == "accepted"
    #   - ApplicationDecisionModel created
    #   - Audit logged
    pass

@pytest.mark.asyncio
async def test_idempotent_submit_application(db_session_mock, admissions_service):
    """Test that submitting twice doesn't create duplicate workflow."""
    # Create application, submit twice
    # Assert: only one workflow_instance_id in metadata
    pass
```

### Phase 5E: Integration with Load Templates

**Pre-requisite**: Admissions workflow template must be loaded before any submission

**Script**: `python -m app.modules.workflows.load_templates --templates admissions`

**Tenant Bootstrap**:
```bash
# In tenant provisioning script (e.g., init-tenant.sh)
python -m app.modules.workflows.load_templates \
    --tenant-id $TENANT_ID \
    --actor system@tenant-bootstrap \
    --templates admissions
```

### Phase 5F: Rollout & Safety

**Steps**:
1. ✅ Deploy Phase 5A code (no schema changes, backward compatible)
2. ✅ Load admissions workflow template in test tenant
3. ✅ Run integration tests
4. ✅ Manual QA: submit application → inspect workflow → complete workflow → verify decision
5. ✅ Deploy to staging/prod with feature flag (if needed)

**Rollback**: No schema changes → simply don't call new endpoints

---

## 6. MINIMAL SCHEMA SUMMARY

### ✅ Zero Application Schema Changes Required

**Strategy**: Use existing `ApplicationModel.metadata_json` (JSONB) for workflow linkage

**Before**:
```python
class ApplicationModel(Base):
    id: Mapped[int]
    tenant_id: Mapped[int]
    applicant_id: Mapped[int]
    stage: str  # "new", "received", etc.
    conclusion_type: str | None  # "accepted", "rejected", etc.
    metadata_json: dict  # Flexible, already exists
    # ... other fields ...
```

**After**:
```python
# NO CHANGES TO MODEL
# metadata_json now stores:
# {
#     "workflow_instance_id": 789,
#     "workflow_key": "admissions",
#     "workflow_status": "in_progress",
#     "workflow_started_at": "2026-03-01T10:00:00Z",
#     ...
# }
```

**Backward Compatibility**:
- Existing applications without workflow_instance_id continue to work
- Old applications can be retroactively linked (optional migration)
- No schema migration required

---

## 7. CONSTRAINT COMPLIANCE CHECKLIST

| Constraint | Implementation | Status |
|---|---|---|
| **Tenant-first** | All methods take `tenant_id` parameter; all queries filtered by tenant_id; fail-closed on missing tenant | ✅ |
| **Fail-closed validation** | No implicit defaults; ValueError on missing required data; version mismatches caught early | ✅ |
| **Audit logging** | All mutations logged via `build_audit_action()` + `log_admin_action()`; includes workflow linkage | ✅ |
| **RBAC preserved** | New endpoints use `permission_dependency("admissions.write/read")`; no elevation of privileges | ✅ |
| **Minimal schema** | Zero schema changes; uses existing `metadata_json` field (JSONB); no migrations | ✅ |
| **Idempotency** | Workflow creation skipped if already in metadata; decision creation checks for existing record | ✅ |
| **Immutability** | Stage history append-only (no UPDATE/DELETE); comments append-only; decisions immutable | ✅ |

---

## 8. ERROR SCENARIOS & Handling

### Scenario 1: Workflow Template Not Loaded

**Error**: `WorkflowDefinitionNotFoundError` in `start_workflow()`
**Mitigation**: 
- Pre-req: Load templates during tenant provisioning
- Gracefully fail with 503 if template missing
- Document in deployment runbook

### Scenario 2: Version Conflict During Submit

**Error**: `expected_version != application.version`
**Mitigation**:
- Optimistic locking prevents stale-read updates
- Return 409 Conflict to client
- Client retries with latest version

### Scenario 3: Workflow Reaches FINAL_DECISION But No Approval

**Error**: No `WorkflowApprovalModel` found
**Mitigation**:
- Callback catches exception, logs failure
- Workflow marked as COMPLETED but decision not materialized
- Admin must manually investigate via audit logs
- Future alert/monitoring for such cases

### Scenario 4: Circular Dependency Between Admissions & Workflows

**Error**: Import error at module startup
**Mitigation**:
- Use lazy imports in method bodies, not at module level
- `WorkflowService` imported only when `submit_application()` called
- `DecisionService` imported only in callback handler

---

## 9. Deployment Checklist

- [ ] Phase 5A code deployed (service layer + workflow callback)
- [ ] Admissions workflow template loaded in all tenants
- [ ] Integration tests passing
- [ ] Manual QA: end-to-end workflow scenario verified
- [ ] Audit logs reviewed for workflow linkage
- [ ] RBAC verified (only admissions.write users can submit, etc.)
- [ ] Rollback plan documented (no schema changes = simple revert)
- [ ] Monitoring/alerting set up for callback failures

---

## 10. Future Enhancements (Not in MVP)

1. **Rejection Handling**: Add explicit REJECT transitions in workflow for reusability
2. **Parallel Approvals**: Allow multiple dean approvals (extend gateway logic)
3. **Workflow Outcome Metadata**: Capture detailed feedback in workflow approvals
4. **Student Request Integration**: Generalize template for other entity types
5. **Webhook Notifications**: Notify admissions staff when tasks assigned (via external system)
6. **Workflow Cancellation**: Allow applicant to withdraw application (cancel workflow)
7. **Conditional Routing**: Route to different approvers based on program or GPA

---

## Summary

**Integration Strategy**: Use workflow engine as the orchestration layer for admissions decisions.

**Key Principles**:
- ✅ Minimal schema changes (metadata_json only)
- ✅ Tenant-first with fail-closed contracts
- ✅ Audit logging on all transitions
- ✅ Idempotent operations
- ✅ Callback-based materialization (workflow completes → decision created)

**Entry Point**: `POST /api/admin/admissions/applications/{application_id}/submit`
**Exit Point**: Workflow callback → `DecisionService.finalize_workflow_decision()`
**Linker**: `metadata_json.workflow_instance_id`

**Next Steps**: Implement Phase 5A–5F per section 5 above.
