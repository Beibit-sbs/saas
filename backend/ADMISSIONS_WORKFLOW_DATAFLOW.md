# Admissions ↔ Workflow Engine Integration - Data Flow Diagrams

## 1. Application Submission Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ CLIENT: ADMISSIONS PORTAL                                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Applicant fills form → Click "Submit" button                   │
│                                                                 │
│  POST /api/admin/admissions/applications/{app_id}/submit        │
│  {                                                              │
│    "expected_version": 1                                        │
│  }                                                              │
│                                                                 │
└────────────────────────────┬──────────────────────────────────┘
                             │
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│ BACKEND: ADMISSIONS SERVICE LAYER                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ApplicationService.submit_application()                        │
│  ├─ Validate: application.stage == "new"                        │
│  ├─ Validate: optimistic lock (expected_version == actual)      │
│  │                                                              │
│  └─→ _start_admissions_workflow()                               │
│      ├─ Call WorkflowService.start_workflow() with:             │
│      │  ├─ tenant_id                                            │
│      │  ├─ workflow_key = "admissions"                          │
│      │  ├─ entity_type = "admission_application"                │
│      │  ├─ entity_id = application.id                           │
│      │  └─ metadata_json = {applicant_id, program_id, ...}      │
│      │                                                          │
│      └─← Back with workflow_instance_id = 789                   │
│                                                                 │
│  Store in metadata_json:                                        │
│  ├─ workflow_instance_id = 789                                  │
│  ├─ workflow_key = "admissions"                                 │
│  ├─ workflow_status = "in_progress"                             │
│  └─ workflow_started_at = "2026-03-01T10:00:00Z"                │
│                                                                 │
│  Update application state:                                      │
│  ├─ stage: "new" → "received"                                   │
│  ├─ received_at = current_time                                  │
│  └─ version++                                                   │
│                                                                 │
│  Record in ApplicationStageHistoryModel (append-only)            │
│  Log audit event: "application.submitted"                       │
│                                                                 │
└────────────────────────────┬──────────────────────────────────┘
                             │
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│ BACKEND: WORKFLOW ENGINE SERVICE LAYER                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  WorkflowService.start_workflow()                               │
│  ├─ Query WorkflowDefinitionModel by key="admissions"           │
│  ├─ Get active WorkflowDefinitionVersionModel                   │
│  ├─ Get version steps (document_review, dept_approval, ...)     │
│  │                                                              │
│  ├─ Create WorkflowInstanceModel:                               │
│  │  ├─ id = 789                                                 │
│  │  ├─ tenant_id = 1                                            │
│  │  ├─ entity_type = "admission_application"                    │
│  │  ├─ entity_id = 123 (application.id)                         │
│  │  ├─ current_step_id = document_review.id                     │
│  │  └─ status = "in_progress"                                   │
│  │                                                              │
│  ├─ Create WorkflowTaskModel for document_review step:          │
│  │  ├─ workflow_instance_id = 789                               │
│  │  ├─ step_id = document_review.id                             │
│  │  ├─ status = "open"                                          │
│  │  ├─ assignee_type = "group"                                  │
│  │  └─ assignee_ref = "group:admissions_staff"                  │
│  │                                                              │
│  └─ Log audit event: "workflow.started"                         │
│                                                                 │
│  Return: WorkflowInstanceReadSchema                             │
│  {                                                              │
│    "id": 789,                                                   │
│    "tenant_id": 1,                                              │
│    "entity_type": "admission_application",                      │
│    "entity_id": 123,                                            │
│    "current_step_id": 456,                                      │
│    "status": "in_progress",                                     │
│    ...                                                          │
│  }                                                              │
│                                                                 │
└────────────────────────────┬──────────────────────────────────┘
                             │
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│ CLIENT: RESPONSE                                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  HTTP 200 OK                                                    │
│  {                                                              │
│    "id": 123,                                                   │
│    "stage": "received",                                         │
│    "metadata_json": {                                           │
│      "workflow_instance_id": 789,                               │
│      "workflow_key": "admissions",                              │
│      "workflow_status": "in_progress",                          │
│      "workflow_started_at": "2026-03-01T10:00:00Z",             │
│      ...                                                        │
│    }                                                            │
│  }                                                              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Workflow Task Progression Flow

```
┌──────────────────────────────────────────────────────────────────────┐
│ ADMISSIONS STAFF PORTAL                                              │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Staff sees task: "Review application documents"                    │
│  Task ID: 1001, assigned to: "group:admissions_staff"               │
│  {                                                                   │
│    "workflow_instance_id": 789,                                      │
│    "entity_type": "admission_application",                          │
│    "entity_id": 123,                                                │
│    "step_name": "document_review",                                  │
│  }                                                                   │
│                                                                      │
│  ┌─ COMPLETE TASK ─┐                                                │
│  │ Action: "start"  │  (approve + move to next step)                │
│  └──────────────────┘                                                │
│                                                                      │
└──────────────┬───────────────────────────────────────────────────────┘
               │
               ↓
┌──────────────────────────────────────────────────────────────────────┐
│ WORKFLOW ENGINE: EXECUTE TRANSITION                                  │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  WorkflowRuntimeEngine.execute_transition(                          │
│    tenant_id=1,                                                     │
│    workflow_instance_id=789,                                        │
│    from_step_id=456,  /* document_review */                         │
│    action_key="start",                                              │
│    actor="staff@admissions",                                        │
│  )                                                                   │
│                                                                      │
│  ├─ Find transition: document_review --[start]--> dept_approval     │
│  │                                                                  │
│  ├─ Create WorkflowApprovalModel:                                   │
│  │  ├─ workflow_instance_id = 789                                   │
│  │  ├─ step_id = 456 (document_review)                              │
│  │  ├─ action = "approve"  /* normalized from "start" */            │
│  │  ├─ actor_id = "staff@admissions"                                │
│  │  └─ metadata_json = {...}                                        │
│  │                                                                  │
│  ├─ Update WorkflowInstanceModel:                                   │
│  │  ├─ current_step_id = 457 (dept_approval)                        │
│  │  └─ status = "in_progress"                                       │
│  │                                                                  │
│  ├─ Complete old task (document_review): status="completed"         │
│  │                                                                  │
│  ├─ Create new WorkflowTaskModel (dept_approval):                   │
│  │  ├─ workflow_instance_id = 789                                   │
│  │  ├─ step_id = 457 (dept_approval)                                │
│  │  ├─ status = "open"                                              │
│  │  ├─ assignee_type = "group"                                      │
│  │  └─ assignee_ref = "group:department_chairs"                     │
│  │                                                                  │
│  └─ Log audit: "workflow.transition" + "task.created"               │
│                                                                      │
└──────────────┬───────────────────────────────────────────────────────┘
               │
               ↓
┌──────────────────────────────────────────────────────────────────────┐
│ APPLICATION STATE (synchronized)                                     │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Background: Update ApplicationModel on major transitions           │
│  (Optional: could be done manually via separate endpoint)           │
│                                                                      │
│  Update ApplicationModel:                                            │
│  ├─ stage: "under_review" (inferred from workflow progress)         │
│  ├─ metadata_json.workflow_status = "in_progress"                   │
│  └─ metadata_json.current_step = "dept_approval"                    │
│                                                                      │
│  Log to ApplicationStageHistoryModel for audit trail                 │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 3. Workflow Completion & Decision Materialization Flow

```
┌──────────────────────────────────────────────────────────────────────┐
│ ADMISSIONS LEADERSHIP PORTAL                                         │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Director reviews all prior approvals:                              │
│  ├─ Document review: ✓ Complete                                     │
│  ├─ Department approval: ✓ Complete                                 │
│  ├─ Dean approval: ✓ Complete                                       │
│  ├─ Registrar approval: ✓ Complete                                  │
│  │                                                                  │
│  ├─ FINAL DECISION: [ APPROVE ] or [ REJECT ]                      │
│                                                                      │
└──────────────┬───────────────────────────────────────────────────────┘
               │
               ↓ (Click APPROVE)
│
┌──────────────────────────────────────────────────────────────────────┐
│ WORKFLOW ENGINE: FINAL TRANSITION                                    │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  WorkflowRuntimeEngine.execute_transition(                          │
│    tenant_id=1,                                                     │
│    workflow_instance_id=789,                                        │
│    from_step_id=460,  /* final_decision */                          │
│    action_key="complete",                                           │
│    actor="director@admissions",                                     │
│  )                                                                   │
│                                                                      │
│  ├─ Find transition: final_decision --[complete]--> END             │
│  │                                                                  │
│  ├─ Create WorkflowApprovalModel:                                   │
│  │  ├─ step_id = 460 (final_decision)                               │
│  │  ├─ action = "approve"  /* mapped from "complete" */             │
│  │  └─ actor_id = "director@admissions"                             │
│  │                                                                  │
│  ├─ Update to END step:                                             │
│  │  ├─ current_step_id = END.id                                     │
│  │  └─ status = "COMPLETED"  /* WorkflowInstanceStatus.COMPLETED */ │
│  │                                                                  │
│  ├─ [NEW] DISPATCH COMPLETION CALLBACK:                             │
│  │                                                                  │
│  │    WorkflowService.on_workflow_completed(                        │
│  │      tenant_id=1,                                                │
│  │      workflow_instance_id=789                                    │
│  │    )                                                              │
│  │                                                                  │
│  └─ Log: "workflow.completed"                                       │
│                                                                      │
└──────────────┬───────────────────────────────────────────────────────┘
               │
               ↓
┌──────────────────────────────────────────────────────────────────────┐
│ WORKFLOW SERVICE CALLBACK HANDLER                                    │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  WorkflowService.on_workflow_completed()                            │
│                                                                      │
│  ├─ Fetch WorkflowInstanceModel (id=789)                            │
│  │                                                                  │
│  ├─ Extract: entity_type="admission_application", entity_id=123   │
│  │                                                                  │
│  ├─ Get latest WorkflowApprovalModel (order by created_at DESC)   │
│  │  └─ action="approve"                                            │
│  │                                                                  │
│  ├─ DISPATCH based on entity_type:                                 │
│  │                                                                  │
│  │  If entity_type == "admission_application":                     │
│  │  │                                                              │
│  │  └─ DecisionService.finalize_workflow_decision(                 │
│  │      tenant_id=1,                                               │
│  │      application_id=123,                                        │
│  │      workflow_instance_id=789,                                  │
│  │      approval_action="approve",  /* from WorkflowApprovalModel */│
│  │      actor="director@admissions"                                │
│  │    )                                                             │
│  │                                                                  │
│  └─ [END] (fire-and-forget, exceptions logged)                     │
│                                                                      │
└──────────────┬───────────────────────────────────────────────────────┘
               │
               ↓
┌──────────────────────────────────────────────────────────────────────┐
│ ADMISSIONS SERVICE: DECISION MATERIALIZATION                         │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  DecisionService.finalize_workflow_decision()                       │
│                                                                      │
│  ├─ Fetch ApplicationModel (id=123)                                 │
│  │                                                                  │
│  ├─ Validate workflow_instance_id matches metadata_json             │
│  │                                                                  │
│  ├─ Map approval_action → conclusion_type:                         │
│  │  ├─ action="approve" → conclusion_type="accepted"               │
│  │  └─ action="reject" → conclusion_type="rejected"                │
│  │                                                                  │
│  ├─ Update ApplicationModel:                                        │
│  │  ├─ stage: "decision_pending" → "concluded"                     │
│  │  ├─ conclusion_type = "accepted"                                │
│  │  ├─ decision_at = current_time                                  │
│  │  └─ version++                                                   │
│  │                                                                  │
│  ├─ Create ApplicationDecisionModel:                                │
│  │  ├─ tenant_id = 1                                               │
│  │  ├─ application_id = 123                                        │
│  │  ├─ decision_type = "workflow_auto"                             │
│  │  ├─ conclusion_type = "accepted"                                │
│  │  ├─ decided_by_id = "director@admissions"                       │
│  │  ├─ decided_at = current_time                                   │
│  │  └─ metadata_json = {workflow_instance_id, approval_action,...} │
│  │                                                                  │
│  ├─ Record ApplicationStageHistoryModel (append-only):              │
│  │  ├─ from_stage = "decision_pending"                             │
│  │  ├─ to_stage = "concluded"                                      │
│  │  ├─ reason = "Workflow completed with decision: approve"        │
│  │  ├─ trigger_type = "workflow_completion"                        │
│  │  └─ workflow_instance_id = 789 (in metadata)                    │
│  │                                                                  │
│  ├─ Update metadata_json:                                           │
│  │  ├─ workflow_status = "completed"                               │
│  │  ├─ workflow_outcome = "approve"                                │
│  │  └─ workflow_completed_at = current_time                        │
│  │                                                                  │
│  ├─ Audit log: "decision.finalize" + "application.concluded"       │
│  │                                                                  │
│  └─ Commit transaction                                              │
│                                                                      │
└──────────────┬───────────────────────────────────────────────────────┘
               │
               ↓
┌──────────────────────────────────────────────────────────────────────┐
│ FINAL STATE - APPLICATION CONCLUDED                                  │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ApplicationModel:                                                   │
│  {                                                                   │
│    "id": 123,                                                        │
│    "tenant_id": 1,                                                   │
│    "applicant_id": 42,                                               │
│    "stage": "concluded",  /* ← Changed from "decision_pending" */   │
│    "conclusion_type": "accepted",  /* ← Set by workflow */          │
│    "decision_at": "2026-03-01T16:00:00Z",                           │
│    "version": 5,  /* Incremented */                                 │
│    "metadata_json": {                                               │
│      "workflow_instance_id": 789,                                    │
│      "workflow_key": "admissions",                                  │
│      "workflow_status": "completed",  /* ← Updated */               │
│      "workflow_outcome": "approve",  /* ← New */                    │
│      "workflow_completed_at": "2026-03-01T16:00:00Z",               │
│      ...                                                            │
│    }                                                                 │
│  }                                                                   │
│                                                                      │
│  ApplicationDecisionModel:                                           │
│  {                                                                   │
│    "id": 201,                                                        │
│    "application_id": 123,                                            │
│    "decision_type": "workflow_auto",                                │
│    "conclusion_type": "accepted",                                   │
│    "reasoning": "Workflow decision: approve",                       │
│    "decided_by_id": "director@admissions",                          │
│    "decided_at": "2026-03-01T16:00:00Z",                            │
│    "metadata_json": {                                               │
│      "workflow_instance_id": 789,                                    │
│      "approval_action": "approve",                                  │
│      "decision_source": "workflow_engine"                           │
│    }                                                                 │
│  }                                                                   │
│                                                                      │
│  WorkflowInstanceModel:                                              │
│  {                                                                   │
│    "id": 789,                                                        │
│    "status": "COMPLETED",  /* ← Set to COMPLETED */                 │
│    "current_step_id": END_STEP_ID,                                  │
│    ...                                                              │
│  }                                                                   │
│                                                                      │
│  Audit Trail (ApplicationStageHistoryModel + WorkflowTaskModel):    │
│  ├─ application.created (stage=new)                                 │
│  ├─ application.submitted (stage=received, workflow_init)           │
│  ├─ document_review task completed                                  │
│  ├─ dept_approval task completed                                    │
│  ├─ dean_approval task completed                                    │
│  ├─ registrar_approval task completed                               │
│  ├─ final_decision task completed (approved)                        │
│  ├─ decision.finalize (stage=concluded, conclusion=accepted)        │
│  └─ workflow.completed (END reached)                                │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 4. Tenancy Isolation

```
┌──────────────────────────────────────────────────────────────────────┐
│ REQUEST: Tenant A (tenant_id=1)                                      │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  POST /api/admin/admissions/applications/123/submit                 │
│  (Header: Bearer JWT with tenant_id claim = 1)                      │
│                                                                      │
└──────────────┬───────────────────────────────────────────────────────┘
               │
               ├─ Verify: tenant_id extracted from JWT = 1
               │
               ├─ Call: ApplicationService.submit_application(
               │          tenant_id=1,  ← explicit, fail-closed
               │          application_id=123
               │        )
               │
               ├─ Query: SELECT * FROM app_admissions_applications
               │          WHERE id=123 AND tenant_id=1  ← FILTERED by tenant
               │          Result: ✓ Found (belongs to Tenant A)
               │
               ├─ Call: WorkflowService.start_workflow(
               │          tenant_id=1,  ← explicit
               │          workflow_key="admissions",
               │          entity_type="admission_application",
               │          entity_id=123
               │        )
               │
               ├─ Query: SELECT * FROM app_workflows_instances
               │          WHERE tenant_id=1  ← FILTERED
               │          Result: Create with tenant_id=1
               │
               └─ ✓ All queries scoped to tenant_id=1

┌──────────────────────────────────────────────────────────────────────┐
│ REQUEST: Tenant B (tenant_id=2) -- HOSTILE INTENT                   │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  POST /api/admin/admissions/applications/123/submit                 │
│  (JWT indicates: tenant_id=2, but tries application_id=123 from    │
│   Tenant A)                                                          │
│                                                                      │
└──────────────┬───────────────────────────────────────────────────────┘
               │
               ├─ Call: ApplicationService.submit_application(
               │          tenant_id=2,  ← from JWT
               │          application_id=123  ← cross-tenant
               │        )
               │
               ├─ Query: SELECT * FROM app_admissions_applications
               │          WHERE id=123 AND tenant_id=2  ← FILTERED
               │          Result: ✗ NOT FOUND (123 belongs to tenant_id=1)
               │
               └─ ✗ ValueError: "Application 123 not found in tenant 2"
                   HTTP 404 returned to attacker
                   Audit log: Unauthorized access attempt
```

---

## 5. Idempotency Guarantees

```
┌──────────────────────────────────────────────────────────────────────┐
│ CALL 1: submit_application(application_id=123, version=1)            │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ├─ Fetch: application (version=1)                                   │
│  ├─ Lock OK: expected_version(1) == actual_version(1)               │
│  │                                                                  │
│  ├─ Start workflow:                                                  │
│  │  └─ Create WorkflowInstanceModel (id=789)                        │
│  │                                                                  │
│  ├─ Store in metadata_json:                                          │
│  │  └─ workflow_instance_id = 789  ← FIRST TIME                     │
│  │                                                                  │
│  ├─ Update: application.stage = "received", version=2               │
│  └─ Commit                                                           │
│                                                                      │
│  RESULT: ✓ workflow_instance_id = 789                                │
│          application.version = 2                                     │
│                                                                      │
└──────────────┬───────────────────────────────────────────────────────┘
               │ (Network timeout, client retries)
               │
┌──────────────────────────────────────────────────────────────────────┐
│ CALL 2: submit_application(application_id=123, version=2)            │
│         [RETRY WITH UPDATED VERSION]                                │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ├─ Fetch: application (version=2)                                   │
│  ├─ Lock OK: expected_version(2) == actual_version(2)               │
│  │                                                                  │
│  ├─ Check workflow already started:                                  │
│  │  └─ workflow_instance_id already in metadata_json = 789          │
│  │     SKIP workflow creation (idempotent)                          │
│  │                                                                  │
│  ├─ Update: application.stage = "received", version=3               │
│  │  (Already at "received", but version incremented)                │
│  │                                                                  │
│  └─ Commit                                                           │
│                                                                      │
│  RESULT: ✓ workflow_instance_id = 789 (same as before)               │
│          application.version = 3                                     │
│          NO DUPLICATE WORKFLOW CREATED!                              │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────┐
│ CALL 3: finalize_workflow_decision(..., approval_action="approve")   │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ├─ Check if ApplicationDecisionModel already exists:                │
│  │  └─ Query WHERE application_id=123 AND tenant_id=1               │
│  │     Result: EXISTS (from previous finalize call)                 │
│  │                                                                  │
│  ├─ RETURN EXISTING DECISION (idempotent)                            │
│  └─ NO UPDATE, NO DUPLICATE                                          │
│                                                                      │
│  RESULT: ✓ Application still "concluded"                             │
│          ✓ Decision still "accepted"                                 │
│          ✓ No version conflicts or audit log spam                    │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 6. Error Scenarios

```
SCENARIO 1: Application in Wrong Stage
─────────────────────────────────────────
  Client calls: submit_application(application_id=123)
  But: application.stage = "concluded"  (already finished)
  
  Expected: ✗ ValueError
  Client receives: HTTP 400 "Cannot submit application in stage 'concluded'..."
  
  
SCENARIO 2: Optimistic Lock Conflict
──────────────────────────────────────
  Client A: submit_application(app_id=123, expected_version=5)
  Client B: submit_application(app_id=123, expected_version=5)
  
  Sequence:
  ├─ Client A acquires lock, version updates to 6
  ├─ Client B tries, expected(5) != actual(6)
  ├─ Client B receives: HTTP 409 "Version mismatch: expected 5, got 6"
  └─ Client B retries with version=6
  
  
SCENARIO 3: Workflow Template Not Loaded
──────────────────────────────────────────
  Client calls: submit_application(application_id=123)
  But: WorkflowDefinitionModel with key="admissions" doesn't exist
  
  Expected: ✗ WorkflowDefinitionNotFoundError
  Workflow cascade: WorkflowService.start_workflow() fails
  Client receives: HTTP 400 "Workflow 'admissions' not found"
  Mitigation: Load templates during tenant bootstrap
  
  
SCENARIO 4: Non-existent Approval Action
─────────────────────────────────────────
  Workflow callback calls: finalize_workflow_decision(
    approval_action="abstain"  ← Invalid
  )
  
  Expected: ✗ ValueError
  Exception logged:
    - "Invalid approval_action 'abstain'. Must be 'approve' or 'reject'."
    - Audit event: "decision.finalize_failure"
  Result: Decision not materialized, workflow stuck in "in_progress"
  
  
SCENARIO 5: Cross-Tenant Access Attempt
────────────────────────────────────────
  JWT: tenant_id=2
  Request: submit_application(application_id=123)  ← belongs to tenant_id=1
  
  Expected: ✗ PermissionError
  Query: SELECT ... WHERE id=123 AND tenant_id=2
  Result: NOT FOUND
  Client receives: HTTP 404 "Application 123 not found..."
  Audit log: Unauthorized access attempt recorded
```

---

## Summary

**Integration achieves**:
- ✅ Workflow as primary orchestrator for admissions decisions
- ✅ Tenant isolation enforced at every layer
- ✅ Idempotent operations (retryable)
- ✅ Fail-closed validation (no implicit defaults)
- ✅ Complete audit trail (every step logged)
- ✅ Minimal schema impact (metadata_json only)
- ✅ Callback-driven decision materialization (loose coupling)
