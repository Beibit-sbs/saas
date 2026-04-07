# Migration Dependency Graph

Visual representation of migration blockers and dependencies.

---

## OVERALL MIGRATION FLOW

```
┌─────────────────────────────────────────────────────────────────┐
│                     CURRENT STATE (Day 0)                       │
│                                                                 │
│  ✅ C-002: legacy_students_router (ready, awaiting BFF)         │
│  ✅ C-003: legacy_enrollments_router (ready, awaiting BFF)      │
│  ⏳ C-001: Frontend admin zone (blocked on BFF design)          │
│  ⏳ C-004: University routes (blocked on architecture)          │
│  ⏳ C-005: Identity phase1 (blocked on auth unification)        │
│  ⚠️  C-007: university_core service (blocked on C-004)          │
└─────────────────────────────────────────────────────────────────┘

                            ↓↓↓

┌─────────────────────────────────────────────────────────────────┐
│                   DEPENDENCY CUT: DECISIONS                     │
│                                                                 │
│  📋 [Architecture Board] C-004: Namespace decision (A/B/C)      │
│  🔒 [Security] C-005: Identity unification design               │
│  👥 [Frontend] C-001: BFF proxy scope + component layout        │
│  🏗️  [DevOps] Deployment + rollback strategy                    │
└─────────────────────────────────────────────────────────────────┘

                            ↓↓↓

┌─────────────────────────────────────────────────────────────────┐
│         PHASE 1: C-001 BFF REDESIGN (Weeks 3-4)                │
│                                                                 │
│  └─→ Redesign BFF proxy layer                                  │
│  └─→ Consolidate useAdminUniversity hooks                      │
│  └─→ Reorganize 33 admin files → (admin)/console/              │
│  └─→ E2E: Admin zone fully functional ✅                       │
└─────────────────────────────────────────────────────────────────┘
            ↓
        UNBLOCKS ✅
            ↓
       C-002, C-003

┌─────────────────────────────────────────────────────────────────┐
│        PHASE 2: C-002/C-003 CLEANUP (Week 5)                   │
│                                                                 │
│  └─→ Remove legacy_students_router definition                  │
│  └─→ Remove legacy_enrollments_router definition               │
│  └─→ Update main.py includes                                   │
│  └─→ Tests: ✅ 100% passing                                    │
└─────────────────────────────────────────────────────────────────┘
            ↓
        INDEPENDENT
            ↓
       PARALLEL WORK

┌─────────────────────────────────────────────────────────────────┐
│    PHASE 3.A: C-004 IMPLEMENTATION (Weeks 6-8)                 │
│    [Requires: c-004_namespace_decision == APPROVED]            │
│                                                                 │
│  └─→ Migrate faculty/programs/courses routers                  │
│  └─→ Update 6 service imports                                  │
│  └─→ Consolidate university_core configs (C-007 direct)        │
│  └─→ Integration tests: ✅ All modules linked                  │
└─────────────────────────────────────────────────────────────────┘

                    INDEPENDENT OF
                          ↓
┌─────────────────────────────────────────────────────────────────┐
│    PHASE 3.B: C-005 AUTH UNIFICATION (Weeks 9-10)              │
│    [Requires: c-005_identity_design == APPROVED + TESTED]      │
│                                                                 │
│  └─→ Implement unified identity endpoint                       │
│  └─→ Migrate auth/ dependencies                                │
│  └─→ Refactor hardening tests                                  │
│  └─→ Security review + pen test: ✅ Approved                   │
└─────────────────────────────────────────────────────────────────┘

            ↓↓ (Both A & B complete)

┌─────────────────────────────────────────────────────────────────┐
│         PHASE 4: CLEANUP & PRODUCTION (Weeks 11+)              │
│                                                                 │
│  └─→ Monitor production (0 errors)                             │
│  └─→ Documentation complete                                    │
│  └─→ Rollback procedures tested                                │
│  └─→ Mark candidates: READY or REMOVED ✅                      │
└─────────────────────────────────────────────────────────────────┘
```

---

## DEPENDENCY MATRIX (DETAILED)

```
                C-001    C-002    C-003    C-004    C-005    C-007
                (BFF)   (Stud)   (Enr)    (Univ)   (Auth)   (Core)
                ----    ------    -----    ------   -----    -----

C-001 (BFF)      —       ✅        ✅       —        —        —
                 |     BLOCKS    BLOCKS
                 |
C-002 (Stud)   WAIT      —         —        —        —        —
                |
C-003 (Enr)    WAIT      —         —        —        —        —
                |
C-004 (Univ)     —       —         —        —        —       NEEDS
                                                              C-007
C-005 (Auth)     —       —         —        —        —        —
                 |
C-007 (Core)   (independent until C-004 namespace confirmed)

LEGEND:
✅ = blocks this candidate
— = no dependency
WAIT = waits for
NEEDS = needs for proper execution
```

---

## BLOCKED CANDIDATES FLOWCHART

```
C-001: Frontend Admin Zone
├─ Decision: BFF proxy scope?
│  ├─ A: Just path rewriting (simpler)
│  └─ B: Full auth proxy (more complex)
├─ Design: Component reorganization plan?
├─ Timeline: OK (2-3 weeks)
└─ READY FOR: Planning NOW
   ├─→ START IMPLEMENTATION: Week 3
   └─→ UNBLOCKS: C-002, C-003

C-004: University Routes (Faculty/Programs/Courses)
├─ Decision: Namespace?
│  ├─ A: Keep /api/admin/university/* (status quo)
│  ├─ B: → /api/platform/admin/university/* (consolidate)
│  └─ C: → /api/v1/admin/university/* (new version)
├─ Owner: Architecture Board
├─ Review: Ripple on 6 services
├─ Dependency: Resolves C-007 (config distribution)
└─ READY FOR: Planning NOW
   ├─→ DECISION NEEDED: End of Week 1
   └─→ START IMPLEMENTATION: Week 6

C-005: Identity Phase1 Router
├─ Decision: Identity endpoint unification design?
│  ├─ Current: phase1_router (/api/identity) + router (/api/admin/identity)
│  └─ Unified: Single endpoint? Or coexist?
├─ Owner: Auth/Security team
├─ Blocker: Login flow uses phase1_service
│  └─ Mocking: Tests depend on phase1_router
├─ Risk: HIGH (authentication critical)
├─ Timeline: 2-3 weeks (after design approved)
└─ READY FOR: Planning NOW
   ├─→ DESIGN NEEDED: Week 1-2
   ├─→ SECURITY REVIEW: Week 2
   └─→ START IMPLEMENTATION: Week 9

C-007: University Core (Data Layer)
├─ Blocked by: C-004 namespace decision
│  └─ Reason: EntityConfig table names may change
├─ Options:
│  ├─ Option 1: Distribute configs to each module
│  ├─ Option 2: Keep shared but rename (→ core/)
│  └─ Option 3: Migrate to ORM metadata (SQLAlchemy)
├─ Timeline: 3-5 days (implementation only)
└─ READY FOR: Implementation after C-004
   ├─→ WAIT FOR: C-004 decision
   └─→ START IMPLEMENTATION: Week 6 (parallel with C-004)
```

---

## DECISION TREE

```
START
│
├─ WEEK 1: Architecture Board Review
│  │
│  ├─ DECISION: C-004 Namespace
│  │  │
│  │  ├─ APPROVED → Path forward clear
│  │  │  └─ Proceed to WEEK 2 decisions
│  │  │
│  │  ├─ DEFERRED → Risk: 1 week delay
│  │  │  └─ Escalate to VP Engineering
│  │  │
│  │  └─ REJECTED → Revisit architecture
│  │     └─ 2-week delay; new design sprint
│  │
│  └─ DECISION: C-001 BFF Scope
│     │
│     ├─ APPROVED → Can start Week 3
│     │  └─ Proceed to WEEK 2: Security review
│     │
│     ├─ DEFERRED → Risk: 1 week delay
│     │  └─ Escalate to Frontend Lead
│     │
│     └─ REJECTED → BFF not changing
│        └─ Stop: Can't migrate C-002/C-003
│
├─ WEEK 2: Security & Auth Team Review
│  │
│  ├─ DECISION: C-005 Auth Unification Design
│  │  │
│  │  ├─ APPROVED → Can start Week 9
│  │  │  └─ Proceed to WEEK 3: Execution
│  │  │
│  │  ├─ DEFERRED → Risk: 2 week delay
│  │  │  └─ Run parallel design + C-001/C-004
│  │  │
│  │  └─ REJECTED → Use federated auth
│  │     └─ Stop: C-005 cannot proceed
│  │
│  └─ DESIGN: Hardening test strategy for C-005
│     └─ Acceptance criteria: phase1 removal ≠ auth loss
│
├─ WEEK 3-4: PHASE 1 (C-001 BFF)
│  └─ OUTPUT: featureflag:/api/bff/admin/* ready ✅
│     └─ UNBLOCKS: C-002, C-003
│
├─ WEEK 5: PHASE 2 (C-002/C-003)
│  └─ OUTPUT: legacy routers removed ✅
│     └─ Verification: 0 errors in production
│
├─ WEEK 6-8: PHASE 3.A (C-004 + C-007)
│  └─ OUTPUT: University routes at new namespace ✅
│     └─ Verification: 6 services + config distributed
│
├─ WEEK 9-10: PHASE 3.B (C-005)
│  └─ OUTPUT: Unified identity endpoint ✅
│     └─ Verification: Login flow secure + tests pass
│
├─ WEEK 11+: PHASE 4 (Cleanup)
│  └─ OUTPUT: All candidates in READY/REMOVED status ✅
│     └─ Verification: 7-day production stability
│
└─ END: Migration complete
   └─ Rollback procedures tested & documented
```

---

## CRITICAL PATH ANALYSIS

```
CRITICAL PATH (determines overall timeline):
C-001 (BFF decision) → C-001 implementation → C-002/C-003 → END
= 1 week (decision) + 2 weeks (implementation) + 3 days (cleanup) = ~21 days

PARALLEL CRITICAL PATHS:
Path A: C-004 decision → C-004 impl → C-007 → END (requires C-001 done)
        = 1 week + 4 weeks + 3 days = ~32 days

Path B: C-005 design → C-005 impl → END (independent, but lower priority)
        = 2 weeks + 2 weeks = ~28 days

MINIMUM TOTAL TIME (with ideal parallelization):
max(Path A, Path B, C-001→C-002/C-003) = 32 days (4.5 weeks)
+ 1 week buffer = 40 days (5.5 weeks absolute minimum)

REALISTIC TIMELINE (with reviews + testing):
= 8-10 weeks (including decision delays)
```

---

## ROLLBACK DEPENDENCY GRAPH

```
DEPLOYMENT ORDER (safe rollback):

1st: C-001 BFF
     └─ Has: Feature flag (can disable old paths)
     └─ Rollback: 5 min (code revert, no schema change)

2nd: C-002 Students
     └─ Has: No feature flag needed (prefix-only)
     └─ Rollback: 5 min (re-add legacy_router)

3rd: C-003 Enrollments
     └─ Has: No feature flag needed (prefix-only)
     └─ Rollback: 5 min (re-add legacy_router)

4th: C-004 University Routes
     └─ Has: Schema migration (if namespace scheme changes)
     └─ Rollback: 30 min (database migration rollback)

5th: C-005 Identity
     └─ Has: Auth path change (critical)
     └─ Rollback: 10 min (direct revert, but security test)

6th: C-007 Config Distribution
     └─ Has: Import path changes only
     └─ Rollback: 5 min (revert to shared config)

CASCADE ROLLBACK (if ANY step fails):
→ Start from failed step
→ Reverse deploy order above
→ Total RTO: 15-30 min (if decision caught in internal feed)
```

---

## MONITORING DURING MIGRATION

```
PHASE 1 (C-001 BFF):
Monitor:
  - BFF proxy latency (p95, p99)
  - 4xx errors (spikes = broken rules)
  - Auth token forwarding (logs)
  - Component render errors (console)
Alert on:
  - BFF latency spike > 500ms
  - 4xx error rate > 1% above baseline
  - Auth token missing errors > 0

PHASE 2 (C-002/C-003 Legacy Cleanup):
Monitor:
  - /api/admin/students endpoint latency
  - /api/admin/enrollments endpoint latency
  - Database connection pool usage
  - Service cross-dependencies (grades, transcripts, scheduling)
Alert on:
  - Endpoint latency spike > 200ms
  - Database error rate > 0.1%
  - Any 5xx errors in dependent services

PHASE 3 (C-004/C-005/C-007):
Monitor:
  - /api/platform/admin/university/* latency (if C-004 Option B)
  - /api/identity and /api/admin/identity endpoints
  - Import resolution errors
  - Database schema health
Alert on:
  - Login failures > 0 (C-005 critical)
  - University routes 5xx errors > 0
  - Schema integrity violations

PHASE 4 (Cleanup):
Monitor:
  - Production stability (all errors trending down)
  - Resource usage (CPU, memory, DB connections)
  - Customer support tickets (zero migration-related)
Hold on:
  - Any regression in baseline metrics
```

---

## GO/NO-GO CRITERIA BY PHASE

```
PHASE 1 (BFF): GO if
  ✅ BFF latency < 100ms (addition)
  ✅ 0 auth token forwarding errors
  ✅ E2E smoke tests: 100% pass
  ✅ Admin console fully functional
  ✅ 0 blocking bugs reported

PHASE 2 (C-002/C-003): GO if
  ✅ PHASE 1 == GO
  ✅ legacy_students_router tests: 100% pass
  ✅ legacy_enrollments_router tests: 100% pass
  ✅ Cross-service integration tests pass (grades, transcripts, scheduling)
  ✅ Production: 0 errors for 24 hours

PHASE 3 (C-004/C-005/C-007): GO if
  ✅ C-004 namespace decision: APPROVED
  ✅ C-005 auth design: APPROVED + TESTED
  ✅ Security review: PASSED
  ✅ University route integration tests: 100% pass
  ✅ Identity hardening tests: 100% pass

PHASE 4 (Cleanup): GO if
  ✅ All prior phases: SUCCESS
  ✅ Production: Stable for 7 days
  ✅ Metrics: All green (no regressions)
  ✅ Support: Zero migration-related tickets
  ✅ Rollback procedures: Documented + tested
```

