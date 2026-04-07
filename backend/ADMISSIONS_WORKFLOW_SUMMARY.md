# Admissions ↔ Workflow Engine Integration - Executive Summary

**Project Status**: Design Complete ✅  
**Complexity**: Medium (5 phases, 10-15 hours)  
**Risk Level**: Low (zero DB schema changes)  
**Start Date**: 2026-03-23

---

## Integration Vision

Transform the Admissions module to use the Workflow Engine as the primary orchestrator for application decisions. When an applicant submits an application, the Workflow Engine automatically manages the multi-step approval process (document review → department → dean → registrar → final decision), and materializes the final decision back into the Admissions database.

```
Applicant Submits
    ↓
Workflow Starts (5 steps)
    ↓
Staff Complete Tasks
    ↓
Workflow Completes
    ↓
Decision Created ✓
```

---

## Key Design Decisions

### 1. Zero Schema Changes ✅
- **Strategy**: Use existing `ApplicationModel.metadata_json` (JSONB) field for workflow linkage
- **Why**: Backward compatible, no migrations required, extensible
- **What's stored**: `workflow_instance_id`, workflow status, timestamps, step assignments

### 2. Tenant-First Architecture ✅
- **Pattern**: All methods take explicit `tenant_id` parameter (no implicit defaults)
- **Validation**: Every query filtered by tenant_id; fail-closed on mismatches
- **Security**: Cross-tenant access raises 404 (not 403) to avoid leaking existence

### 3. Fail-Closed Contracts ✅
- **No silent failures**: Version conflicts, stage violations, not-found errors raise exceptions
- **Optimistic locking**: `expected_version` parameter prevents stale-read updates
- **Example**: Submit only works if application is in "new" stage; raises ValueError otherwise

### 4. Idempotent Operations ✅
- **Submission**: Check if workflow already started; skip creation if so
- **Decision**: Check if decision already exists; return existing if found
- **Retryable**: Safe to retry submissions without duplicate workflow creation

### 5. Callback-Driven Decision Materialization ✅
- **Decoupling**: Workflow completion triggers callback → decision service
- **Fire-and-forget**: Callback failures logged but don't block workflow completion
- **Extensible**: Same callback pattern works for other entity types (student requests, hiring, etc.)

---

## Service Layer Integration Points

### ApplicationService
**New Methods**:
- `submit_application()`: Transition new→received + start workflow
- `_start_admissions_workflow()`: Helper to initialize workflow instance

### DecisionService (New)
**New Methods**:
- `finalize_workflow_decision()`: Called by workflow callback to materialize decision

### WorkflowService
**New Methods**:
- `on_workflow_completed()`: Callback handler for workflow completion
- `_dispatch_admissions_decision()`: Helper to route to admissions

### WorkflowRuntimeEngine
**Modified Methods**:
- `execute_transition()`: Added callback invocation when transitioning to END

---

## Admission Lifecycle Mapping

```
ADMISSIONS STAGE    →    WORKFLOW STEP           →    ASSIGNED GROUP
═════════════════════════════════════════════════════════════════════
new                      (no workflow)
    ↓
received              document_review               admissions_staff
    ↓
under_review          dept_approval                 department_chairs
    ↓
decision_pending      dean_approval                 deans
    ↓
                      registrar_approval            registrars
    ↓
                      final_decision                admissions_leadership
    ↓
concluded             (workflow complete)           (decision created)
    - conclusion_type="accepted" or "rejected"
    - ApplicationDecisionModel created
    - Audit logged
```

---

## Constraint Compliance ✅

| Constraint | Implementation | Status |
|---|---|---|
| Tenant-first | All queries filtered by tenant_id; mandatory parameter | ✅ |
| Fail-closed | Version mismatches, wrong stages raise exceptions | ✅ |
| Audit logging | All mutations logged via build_audit_action() | ✅ |
| RBAC preserved | Endpoints use permission_dependency("admissions.write/read") | ✅ |
| Minimal schema | Zero DB changes; uses existing metadata_json field | ✅ |
| Idempotency | Workflow/decision creation skipped if already exists | ✅ |
| Immutability | Stage history append-only; comments append-only | ✅ |

---

## Implementation Phases

### Phase 5A: Admissions Service Extension (3-4 hours)
**Deliverables**:
- Add `submit_application()` to ApplicationService
- Create `DecisionService` class
- Add schemas and imports

### Phase 5B: Workflow Engine Callback (2-3 hours)
**Deliverables**:
- Add `on_workflow_completed()` to WorkflowService
- Modify `execute_transition()` in WorkflowRuntimeEngine
- Callback dispatch logic

### Phase 5C: API Router Enhancement (1-2 hours)
**Deliverables**:
- New endpoint: `POST /api/admin/admissions/applications/{app_id}/submit`
- Request/response schemas
- RBAC integration

### Phase 5D: Testing & Validation (2-3 hours)
**Deliverables**:
- 8+ integration test cases (mocked DB)
- Error scenario tests
- Idempotency tests
- All tests passing

### Phase 5E: Workflow Template Integration (0.5-1 hour)
**Deliverables**:
- Pre-req: Admissions template loaded
- Tenant bootstrap script updated
- Template verification

### Phase 5F: E2E Testing & Deployment (1-2 hours)
**Deliverables**:
- Manual E2E test (submit → complete → verify)
- RBAC verification
- Audit log verification
- Rollback plan documented
- Production deployment

**Total**: 10-15 hours | **Risk**: Low | **Complexity**: Medium

---

## Data Flow: Submission to Decision

```
1. APPLICANT SUBMITS
   ├─ POST /api/admin/admissions/applications/123/submit
   └─ Body: { "expected_version": 1 }

2. ADMISSIONS SERVICE
   ├─ Validate: stage=new, version=1
   ├─ Lock: increment version to 2
   └─ Start workflow (lazy import WorkflowService)

3. WORKFLOW ENGINE STARTS
   ├─ Create WorkflowInstanceModel
   ├─ Create WorkflowTaskModel (document_review step)
   ├─ Assign to: "group:admissions_staff"
   └─ Return workflow_instance_id=789

4. ADMISSIONS UPDATES
   ├─ Store workflow_instance_id in metadata_json
   ├─ Transition stage: new → received
   ├─ Record in ApplicationStageHistoryModel
   ├─ Audit log: "application.submitted"
   └─ Commit

5. RESPONSE TO CLIENT
   └─ HTTP 200 { id: 123, stage: "received", metadata_json: {...workflow_instance_id...} }

────────────────────────────────────────────────────────────────

6. STAFF COMPLETE TASKS
   ├─ Document review: approve → dept_approval step
   ├─ Dept approval: approve → dean_approval step
   ├─ Dean approval: approve → registrar_approval step
   ├─ Registrar approval: approve → final_decision step
   └─ Final decision: approve → END step

7. WORKFLOW COMPLETION CALLBACK
   ├─ WorkflowRuntimeEngine.execute_transition() triggers END
   ├─ Invokes WorkflowService.on_workflow_completed()
   ├─ Callback extracts: entity_type="admission_application", entity_id=123
   └─ Dispatches to DecisionService.finalize_workflow_decision()

8. DECISION MATERIALIZATION
   ├─ Create ApplicationDecisionModel
   ├─ Update application: stage=concluded, conclusion_type=accepted
   ├─ Store outcome in metadata_json
   ├─ Record in ApplicationStageHistoryModel
   ├─ Audit log: "decision.finalize"
   └─ Commit

9. FINAL STATE
   ├─ Application.stage = "concluded"
   ├─ Application.conclusion_type = "accepted"
   ├─ ApplicationDecisionModel.id = 201
   ├─ metadata_json.workflow_status = "completed"
   └─ Every step audited ✓
```

---

## Workflow Outcome Mapping

| Workflow Approval Action | Application Conclusion Type |
|---|---|
| approve | accepted |
| reject | rejected |
| (future) waitlist | waitlist |

---

## Entry & Exit Points

**Entry**: 
- `POST /api/admin/admissions/applications/{application_id}/submit`
- Requires: `admissions.write` RBAC permission
- Request: `{ "expected_version": 1 }`

**Exit**: 
- Workflow callback → DecisionService.finalize_workflow_decision()
- Internal API (no HTTP endpoint)
- Automatic on workflow completion

**Linking**: 
- Field: `ApplicationModel.metadata_json.workflow_instance_id`
- Validation: Checked before decision materialization

---

## Error Scenarios & Handling

| Scenario | Error | HTTP Response | Resolution |
|---|---|---|---|
| Application not in "new" stage | ValueError: "Cannot submit..." | 400 | Submit only new applications |
| Version conflict (stale read) | ValueError: "Version mismatch..." | 409 | Client retries with latest version |
| Workflow template missing | WorkflowDefinitionNotFoundError | 400 or 503 | Load template during tenant bootstrap |
| Invalid approval_action | ValueError: "Invalid approval_action..." | 400 | Fix workflow template or approval logic |
| Cross-tenant access | ValueError: "not found in tenant..." | 404 | Audit logged; no 403 to avoid leaking |
| Workflow callback failure | Logged but not propagated | N/A | Monitoring alert; manual investigation |

---

## Backward Compatibility ✅

**Existing Applications**: Continue to work without workflow linkage
- No schema changes
- Old applications have empty `metadata_json`
- Can be retroactively linked (optional)

**New Applications**: Automatically linked to workflow on submission
- `metadata_json.workflow_instance_id` populated

**Rollback**: Simply revert code; workflows stay in DB (harmless)

---

## Pre-Deployment Validation

### Code Compilation
```bash
python -m py_compile app/modules/admissions/service.py
python -m py_compile app/modules/workflows/workflow_service.py
python -m py_compile app/modules/admissions/router.py
# All must succeed ✓
```

### Tests
```bash
pytest tests/modules/admissions/test_workflow_integration.py -v
# All 8+ tests must pass ✓
```

### Template
```bash
python -m app.modules.workflows.load_templates \
    --tenant-id 1 \
    --templates admissions
# Must succeed ✓
```

### E2E Test
1. Submit application via API
2. Manually complete each workflow task
3. Verify application stage → "concluded"
4. Verify ApplicationDecisionModel created
5. Check audit logs

---

## Documentation Artifacts

**Architecture Documents**:
1. `ADMISSIONS_WORKFLOW_INTEGRATION_DESIGN.md` - Comprehensive design (9 sections)
2. `ADMISSIONS_WORKFLOW_DATAFLOW.md` - Data flow diagrams (6 flows)
3. `ADMISSIONS_WORKFLOW_IMPLEMENTATION.md` - Phase-by-phase roadmap with code (6 phases)
4. `ADMISSIONS_WORKFLOW_SUMMARY.md` - This file (one-page overview)

**Code Locations**:
- Service layer: `app/modules/admissions/service.py` + `app/modules/admissions/__init__.py`
- Workflow integration: `app/modules/workflows/workflow_service.py` + `workflow_engine.py`
- Router: `app/modules/admissions/router.py`
- Schemas: `app/modules/admissions/schemas.py`
- Tests: `tests/modules/admissions/test_workflow_integration.py`

---

## Next Steps (Post-Design)

1. **Schedule Implementation**
   - Assign developer(s) to phases
   - Allocate 10-15 hours
   - Target: 2-3 day sprint

2. **Execute Phase 5A-5F**
   - Follow implementation roadmap
   - Use provided code snippets
   - Validate at each phase

3. **Deploy to Staging**
   - Run E2E tests
   - Verify RBAC
   - Check audit logs

4. **Deploy to Production**
   - Execute deployment runbook
   - Monitor metrics
   - Alert on callback failures

5. **Monitor & Optimize**
   - Track submission rate
   - Monitor decision materialization success
   - Capture latency metrics

---

## Questions & Clarifications

**Q: Why metadata_json instead of new columns?**
- A: Extensibility, backward compatibility, no migrations needed

**Q: What happens if callback fails?**
- A: Exception logged, workflow marked completed, decision not materialized → alert + manual review

**Q: Can workflow be cancelled?**
- A: Not in MVP; future enhancement via separate endpoint

**Q: What about rejections?**
- A: Add explicit REJECT transitions to workflow (future enhancement)

**Q: How are groups assigned?**
- A: Via hardcoded mapping in `_start_admissions_workflow()` (future: make configurable)

---

## Success Criteria

✅ **MVP Complete When**:
- All 5 phases implemented
- All tests passing
- E2E scenario working
- Zero schema changes
- Tenant isolation verified
- RBAC verified
- Audit logs complete

🎯 **ROI**:
- Admissions decisions now automated
- Staff time reduction (manual routing eliminated)
- Audit trail complete (compliance ready)
- Extensible to other workflows (templates reusable)

💡 **Future Enhancements**:
- Parallel approvals (multiple deans)
- Reject transitions (admissibility rules)
- Conditional routing (program-specific approvers)
- Webhook notifications (external systems)
- Custom SLA tracking (step completion deadline)

---

## Contact & Support

**Design & Architecture**: [Your Team]  
**Implementation Lead**: [TBD - assign at sprint start]  
**QA & Testing**: [TBD - assign at sprint start]  
**Deployment & DevOps**: [TBD - assign at sprint start]

**Documentation**: See three detailed markdown files
- 40+ pages total design documentation
- Ready-to-use code snippets
- Phase-by-phase roadmap
- Full test suite provided

---

**Status**: 🟢 Ready for Implementation  
**Approval**: [Pending design review]  
**Next Sync**: [Pending sprint planning]

---

## Appendix: Key Constraints Addressed

| Constraint | How It's Met |
|---|---|
| **Tenant-first** | Explicit tenant_id on every method; all queries WHERE tenant_id=?; fail-closed on missing |
| **Fail-closed** | No implicit defaults; version mismatches raise; permission checks early |
| **Audit logging** | All mutations logged with actor, timestamp, reason, metadata |
| **RBAC preserved** | Endpoints use permission_dependency(); no privilege escalation |
| **Minimal schema** | Zero DB fields added; uses existing metadata_json (JSONB) |
| **Idempotency** | Workflow/decision creation skipped if already exists; retryable |

---

**END OF SUMMARY**

For detailed architecture, see: `ADMISSIONS_WORKFLOW_INTEGRATION_DESIGN.md`  
For data flows, see: `ADMISSIONS_WORKFLOW_DATAFLOW.md`  
For implementation steps, see: `ADMISSIONS_WORKFLOW_IMPLEMENTATION.md`
