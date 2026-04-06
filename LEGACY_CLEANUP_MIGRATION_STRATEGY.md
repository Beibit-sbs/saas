# Legacy Cleanup Migration Strategy

**Document**: Phase-by-phase plan for safe legacy route/module retirement  
**Version**: 1.0  
**Date**: 2026-04-06  
**Status**: ready for implementation planning  

---

## Overview

Based on codebase analysis, 6 legacy routes/modules are ready for planned retirement. This document maps **safe migration phases** with dependencies and rollback plans.

### Timeline
- **Phase 1 (Weeks 1-2)**: Decisions + BFF design → C-001 prerequisites
- **Phase 2 (Weeks 3-4)**: BFF redesign → enables C-002, C-003
- **Phase 3 (Weeks 5-6)**: Quick route cleanups → C-002, C-003
- **Phase 4 (Weeks 7-8)**: Namespace consolidation → C-004, C-007
- **Phase 5 (Weeks 9-10)**: Auth unification → C-005
- **Phase 6 (Weeks 11+)**: Validation + orphan removal

---

## Phase 1: Architecture Decisions (Weeks 1-2)

### Objective
Resolve design questions blocking downstream phases.

### Blockers to Clear

| Decision | Impact | Recommendation |
|----------|--------|-----------------|
| **BFF scope**: Should new console have dedicated BFF layer or use existing `/api/admin/*`? | Affects C-001, C-002, C-003 | Use existing API; no new BFF layer (simpler, faster) |
| **University namespace**: Consolidate under `/api/admin/org/` or keep separate? | Affects C-004, C-007 | Consolidate under `/api/admin/org/` (cleaner hierarchy) |
| **Identity auth unification**: Single identity service or separate auth identity module? | Affects C-005 | Unified under `/api/admin/identity/` (reduces redundancy) |

### Action Items

```
PHASE_1_WEEK_1:
  [ ] Architecture team reviews above recommendations
  [ ] Decision: BFF consolidation strategy (meeting: 2 hours)
  [ ] Decision: Namespace hierarchy (meeting: 1 hour)
  [ ] Decision: Auth identity unification (meeting: 1.5 hours)
  [ ] Document decisions in ARCHITECTURE_DECISIONS.md
  [ ] CTO/Lead sign-off required

PHASE_1_WEEK_2:
  [ ] Create detailed API contract for C-002/C-003 new paths
  [ ] Create detailed org namespace design document
  [ ] Create detailed identity auth design document
  [ ] Backend team pre-implementation review
  [ ] Schedule Phase 2 kickoff
```

### Success Criteria
✅ All 3 decisions documented and signed off  
✅ API contracts reviewed and approved  
✅ Team alignment on approach

---

## Phase 2: BFF Redesign (Weeks 3-4)

### Objective
Redesign frontend API integration to support new console routes (C-001).

### Scope: C-001 (Legacy Admin Zone)

**From**: `frontend/app/admin/` (old structure, fragmented API calls)  
**To**: `frontend/app/(admin)/console/` (new structure, unified API)

### Key Changes

1. **API Layer Consolidation**
   - Move from scattered admin-specific hooks to unified `modules/console/api.ts`
   - Consolidate types from `frontend/app/admin/types.ts` → `frontend/modules/console/types.ts`
   - Keep backward compatibility with old paths during transition

2. **Component Rewiring**
   - AdminJobsTab, AdminUsersTab → unified ConsoleJobsPanel, ConsoleUsersPanel
   - Leverage existing permission system (`admissions.read`, `tenants.read`, etc.)
   - No new auth changes needed (already done in P1 remediation)

3. **Migration Approach**
   - Run old and new in parallel for 2 sprints
   - Create feature flag: `CONSOLE_ENABLED` (default: true in non-prod)
   - Gradual traffic shift: prod 0% → 50% → 100%

### Action Items

```
PHASE_2_WEEK_3:
  [ ] Create unified console API module (frontend/modules/console/api.ts)
  [ ] Create TypeScript types consolidation PR
  [ ] Rewire ConsoleJobsPanel to use new API
  [ ] Rewire ConsoleUsersPanel to use new API
  [ ] Feature flag integration (FF name: CONSOLE_REDESIGN)
  [ ] PR review + approval
  [ ] Lint/test pass

PHASE_2_WEEK_4:
  [ ] Deploy to staging with 0% traffic to new console
  [ ] Run smoke tests on old admin zone (ensure no regression)
  [ ] Shift to 25% traffic on new console
  [ ] 48h monitoring (no errors, <5% latency delta)
  [ ] Shift to 100% traffic
  [ ] Old admin zone still live (feature flag OFF activates old routes)
  [ ] Phase 3 kickoff scheduled
```

### Rollback Plan
```
If issues found:
  - Set CONSOLE_ENABLED=false (traffic auto-reverts to old admin)
  - Revert last 3 commits on frontend
  - No database migrations (safe revert)
  - Estimated recovery time: <5 minutes
```

### Success Criteria
✅ New console has 100% traffic in prod  
✅ Old admin zone metrics show 0% traffic  
✅ Error rate unchanged (< 0.1% delta)  
✅ Latency stable (< 50ms delta)  
✅ All navigation works in new layout  

---

## Phase 3: Quick Route Migrations (Weeks 5-6)

### Objective
Migrate student/enrollment routes now that frontend BFF is ready (C-002, C-003).

### Scope: C-002 + C-003

**C-002**: `backend/app/modules/students/legacy_router.py`  
→ Use `students/router.py` with `/api/admin/students/` prefix consistently

**C-003**: `backend/app/modules/enrollments/legacy_router.py`  
→ Use `enrollments/router.py` with `/api/admin/enrollments/` prefix consistently

### Action Items

```
PHASE_3_WEEK_5 (C-002 Migration):
  [ ] Backend: Verify students/router.py has all endpoints from legacy_router
  [ ] Backend: Add /api/admin/students/ prefix enforcement
  [ ] Backend: Remove legacy_router.py import from main.py
  [ ] Backend: Update route registration to use students/router only
  [ ] Frontend: Update import paths in admin pages (use unified API from Phase 2)
  [ ] Tests: Run pytest tests/modules/students/ (must pass)
  [ ] Deploy to prod with monitoring

PHASE_3_WEEK_6 (C-003 Migration):
  [ ] Backend: Verify enrollments/router.py has all endpoints from legacy_router
  [ ] Backend: Add /api/admin/enrollments/ prefix enforcement
  [ ] Backend: Remove legacy_router.py import from main.py
  [ ] Backend: Update route registration to use enrollments/router only
  [ ] Frontend: Verify enrollment pages use unified API
  [ ] Tests: Run pytest tests/modules/enrollments/
  [ ] Delete old legacy_router.py files
  [ ] Deploy to prod with monitoring
  [ ] Mark C-002, C-003 as REMOVED in CLEANUP_ENDGAME_TRACKER
```

### Testing Checklist

```
For C-002:
  - [ ] GET /api/admin/students → 200 (list)
  - [ ] POST /api/admin/students → 201 (create)
  - [ ] GET /api/admin/students/{id} → 200 (read)
  - [ ] PUT /api/admin/students/{id} → 200 (update)
  - [ ] DELETE /api/admin/students/{id} → 204 (delete)
  - [ ] Old /api/admin/university/students/* → 404 (legacy blocked)
  - [ ] Frontend pages load without errors
  - [ ] No 404s in nginx logs

For C-003:
  - [Same pattern as C-002]
```

### Rollback Plan
```
Each migration is reversible:
  1. Uncomment legacy_router import
  2. Comment new router import
  3. Restart backend
  4. No data loss (routes remain equivalent)
  5. Estimated recovery: <2 minutes
```

### Success Criteria
✅ C-002 fully migrated and tested  
✅ C-003 fully migrated and tested  
✅ Zero orphaned legacy_router.py files  
✅ API contracts honored 100%  
✅ Frontend pages work without changes  
✅ CLEANUP_ENDGAME_TRACKER updated to REMOVED  

---

## Phase 4: Namespace Consolidation (Weeks 7-8)

### Objective
Consolidate university routes under unified `/api/admin/org/` namespace (C-004, C-007).

### Scope: C-004 + C-007

**C-004**: University legacy routes  
`backend/app/modules/{faculty,programs,courses}/router.py` → `/api/admin/org/{faculty,programs,courses}/`

**C-007**: university_core service  
Orphaned module; consolidate into org/service.py or archive

### Analysis Result (from migration subagent)
```
Complexity: HIGH (affects data model, multiple routes)
Blockers: 
  - Decide namespace hierarchy (/api/admin/org/faculty vs /api/admin/university/faculty)
  - Review data model compatibility
  - Check for circular imports in service layer
Risk: Medium (data layer touched, but no breaking changes to external API)
```

### Action Items

```
PHASE_4_WEEK_7 (Design):
  [ ] Backend: Design consolidated /api/admin/org/ API contract
  [ ] Backend: Map faculty, programs, courses routes to new namespace
  [ ] Backend: Audit university_core service for actual usage (check references)
  [ ] Backend: If C-007 is true orphan, mark for file-level deletion
  [ ] Frontend: Identify all references to /api/admin/university/
  [ ] Frontend: Check if routes need updates
  [ ] Team review of design

PHASE_4_WEEK_8 (Implementation):
  [ ] Backend: Implement new /api/admin/org/* routes
  [ ] Backend: Keep old /api/admin/university/* as redirect (returns 301 Moved Permanently)
  [ ] Frontend: Update API calls to use new namespace (if needed)
  [ ] Tests: Run full pytest suite (esp. org_structure, faculty, programs, courses tests)
  [ ] Deploy to staging, monitor for 48h
  [ ] Deploy to prod with gradual rollout
  [ ] After 1 week, delete old university/* routes (cleanup phase)
  [ ] Mark C-004, C-007 as REMOVED
```

### Success Criteria
✅ All university routes migrated to `/api/admin/org/`  
✅ Old paths return 301 redirects (or deprecated headers)  
✅ Zero orphaned modules  
✅ Service layer consolidated  
✅ Frontend works without additional changes  

---

## Phase 5: Identity Auth Unification (Weeks 9-10)

### Objective
Consolidate identity/auth routes; retire legacy phase1 naming (C-005).

### Scope: C-005

**C-005**: Identity phase1 naming  
`backend/app/modules/identity/phase1_router.py` → unified `/api/admin/identity/` routes

### Analysis Result
```
Complexity: HIGH (auth paths tied to security context)
Blockers:
  - Verify no active client sessions using phase1 paths
  - Review JWT/session token expectations
  - Check RBAC rules tied to old paths
Risk: MEDIUM-HIGH (auth is security-critical)
```

### Action Items

```
PHASE_5_WEEK_9 (Analysis):
  [ ] Security team audit: Find all references to phase1_router
  [ ] Check if any JWT/session generation tied to phase1 paths
  [ ] Check RBAC rules for path-based conditions
  [ ] Verify new identity/router.py is feature-complete vs phase1
  [ ] Create detailed security review document

PHASE_5_WEEK_10 (Implementation):
  [ ] Backend: If phase1 is just old naming, rename routes → /api/admin/identity/
  [ ] Backend: If phase1 has behavior diffs, implement compatibility layer
  [ ] Backend: Add feature flag IDENTITY_V2 for gradual rollout
  [ ] Tests: Run full identity test suite + security tests
  [ ] Deploy to staging + security review
  [ ] Staged prod deployment (10% → 50% → 100%)
  [ ] Monitor auth logs for errors
  [ ] After successful validation, mark C-005 as REMOVED
```

### Rollback Plan
```
Auth is critical — ensure immediate rollback:
  1. Feature flag IDENTITY_V2=false
  2. Restart backend
  3. Sessions remain valid (no token format change)
  4. Estimated recovery: <2 minutes
```

### Success Criteria
✅ No phase1 naming in active code  
✅ All identity routes under `/api/admin/identity/`  
✅ Zero auth errors in logs  
✅ Session/JWT compatibility verified  
✅ Load tests pass (auth is perf-sensitive)  

---

## Phase 6: Validation & Final Cleanup (Weeks 11+)

### Objective
Final validation that no orphans remain; clean up old files.

### Checklist

```
VALIDATION:
  [ ] Run grep for all legacy paths across codebase (should return 0)
  [ ] Run orphan detection: find unused modules
  [ ] Check for stale imports in __init__.py files
  [ ] Run full backend test suite (pytest)
  [ ] Run frontend lint
  [ ] Run e2e smoke tests
  [ ] Load test (measure performance impact)

CLEANUP:
  [ ] Delete legacy_router.py files (if not already done)
  [ ] Delete phase1_router.py
  [ ] Delete university_core/service.py (if orphaned)
  [ ] Remove old admin CSS (frontend/app/admin/admin-legacy.css)
  [ ] Remove old admin hooks/types (if unused)
  [ ] Archive old docs referencing legacy paths

DOCUMENTATION:
  [ ] Update API docs (remove old endpoints)
  [ ] Update architecture diagrams
  [ ] Mark all C-001..C-007 as REMOVED in CLEANUP_ENDGAME_TRACKER
  [ ] Create summary migration report
  [ ] Post-mortem: lessons learned
```

### Success Criteria
✅ Codebase grep returns 0 for legacy paths  
✅ No orphaned modules remain  
✅ All tests pass  
✅ Frontend works end-to-end  
✅ Performance metrics stable or improved  
✅ CLEANUP_ENDGAME_TRACKER fully updated  

---

## Cross-Phase: Continuous Validation

### Per-Phase Checklist (run after each phase)

```
After each phase deployment:
  1. Error rate: must be < 0.1% above baseline
  2. Latency: must be < 50ms above baseline (p95)
  3. Log audit: no 404s for new routes (old routes expected to 404/301)
  4. User reports: zero auth/access issues
  5. Database: no long-running queries (migration didn't lock tables)
  6. Feature flags: enabled as expected
  7. Rollback plan tested manually (simulate outage, verify recovery)
```

### Monitoring Dashboard Requirements

```
Create dashboard tracking:
  - Old route traffic (should trend to 0% each phase)
  - New route traffic (should trend to 100% each phase)
  - Error rate by route
  - Auth success rate
  - 404 count for old paths
  - Feature flag states (console, identity_v2, etc.)
```

---

## Risk Mitigation

| Risk | Mitigation | Owner |
|------|-----------|-------|
| Database locks during migration | Use readonly migrations; test on staging | Backend Lead |
| Session invalidation (auth) | Ensure token compatibility; feature flags | Security Team |
| Client API breaking | Run compatibility layer; staged rollout | Backend + Frontend |
| Missed references to old routes | Grep validation; code review | Tech Lead |
| Performance regression | Load tests each phase; monitor baselines | Performance Team |
| Unplanned downtime | Rollback plan per phase; staff on-call | DevOps |

---

## Timeline Summary

| Phase | Weeks | Owner | Status |
|-------|-------|-------|--------|
| 1: Decisions | 1-2 | Architecture | 📋 Scheduled |
| 2: BFF Redesign | 3-4 | Frontend + Backend | 📋 Depends on Phase 1 |
| 3: Route Migrations | 5-6 | Backend | 📋 Depends on Phase 2 |
| 4: Namespace Consolidation | 7-8 | Backend | 📋 Depends on Phase 3 |
| 5: Auth Unification | 9-10 | Backend + Security | 📋 Depends on Phase 4 |
| 6: Validation + Cleanup | 11+ | All | 📋 Depends on Phase 5 |

**Total Planned Duration**: 11 weeks + validation  
**Risk Level**: Medium (phased approach reduces blast radius)  
**Rollback Complexity**: Low-Medium (each phase independently reversible)

---

## Decision Gate: Should We Start Phase 1?

### Prerequisites
- [ ] CTO/Lead approves this plan
- [ ] Architecture team agrees on 3 decisions
- [ ] Backend team bandwidth available (Weeks 1-10)
- [ ] Frontend team bandwidth available (Weeks 2-6)
- [ ] Security team available for C-005 review (Week 9)

### Go/No-Go Criteria
- **GO**: All prerequisites met + stakeholder alignment
- **NO-GO**: Any blocker unresolved; reschedule to next quarter

---

## Supporting Documents

- [MIGRATION_ANALYSIS_SUMMARY.md](MIGRATION_ANALYSIS_SUMMARY.md) — Technical findings
- [MIGRATION_CODE_REFERENCES.md](MIGRATION_CODE_REFERENCES.md) — Exact code locations
- [MIGRATION_DEPENDENCY_GRAPH.md](MIGRATION_DEPENDENCY_GRAPH.md) — Dependency diagrams
- [CLEANUP_ENDGAME_TRACKER.md](CLEANUP_ENDGAME_TRACKER.md) — Master cleanup ledger

---

**Status**: Ready for Phase 1 decision  
**Last Updated**: 2026-04-06  
**Next Action**: Schedule architecture decision meeting (Phase 1, Week 1)
