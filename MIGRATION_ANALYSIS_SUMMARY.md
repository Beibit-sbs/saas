# Migration Analysis — Executive Summary

> Historical Snapshot (2026-04-06): этот документ отражает состояние до cleanup-phase.
> Текущий источник истины по статусам C-001/C-004/C-008/C-009: CLEANUP_ENDGAME_TRACKER.md.

**Date**: 6 апреля 2026  
**Status**: ✅ Complete analysis of 6 migration candidates

---

## KEY FINDINGS AT A GLANCE

| Candidate | Type | Status | Refs | Complexity | Blocker |
|-----------|------|--------|-----|-----------|---------|
| **C-001** | Frontend zone | ✅ both exist | 8 | **HIGH** | BFF proxy redesign |
| **C-002** | Backend router | ✅ ready | 2 | **MED** | None (after C-001) |
| **C-003** | Backend router | ✅ ready | 2 | **MED** | None (after C-001) |
| **C-004** | 3 routers | ❌ no replacement | 3 | **HIGH** | Architecture decision |
| **C-005** | Dual auth | ⚠️  dual layer | 8 | **HIGH** | Auth flow unification |
| **C-007** | Data layer | ⚠️  orphaned | 8 | **MED** | Distribution strategy |

---

## IMMEDIATE ACTION ITEMS

### 🔴 BLOCKED (Cannot Proceed)

**C-004**: Faculty, Programs, Courses (`/api/admin/university/*`)
- ❌ **No replacement architected**
- Requires: Architecture Board decision on university routes namespace
- Options: Keep legacy? → `/api/platform/admin/*/`? → Consolidate?
- **Timeline**: 4-6 weeks + decision

**C-005**: Identity Phase1 Router
- ❌ **Login flow depends on phase1_service**
- Tests require phase1_router mocking (hardening suite)
- Requires: Unified auth/identity endpoint design
- **Timeline**: 2-3 weeks + security review

### ⏳ BLOCKED ON DEPENDENCY

**C-001**: Frontend Admin Zone
- ⚠️  BFF proxy rewrite required
- useAdminUniversity uses legacy `/api/bff/admin/university/*` paths
- **Timeline**: 2-3 weeks

**C-002 & C-003**: Students/Enrollments Legacy Routers
- ✅ **Ready to migrate** (after BFF)
- Simple prefix swap (same endpoints)
- **Timeline**: 2-3 days each (once C-001 complete)

### ℹ️  REVIEW REQUIRED

**C-007**: University Core Service
- Currently shared config layer (6 modules import)
- Question: Distribute configs to each module, or keep shared?
- **Timeline**: 3-5 days (low priority)

---

## PHASE-BY-PHASE ROADMAP

```
CURRENT (Today)
│
├─ Decision: Architecture on C-004/C-007 namespace → 1 week
├─ Decision: Auth unification for C-005 → 1 week
│
├─ PHASE 1: BFF Proxy Redesign (C-001)
│   Duration: 2-3 weeks
│   Deliverable: /api/bff/admin/* fully functional
│   Blocks: C-002, C-003
│
├─ PHASE 2: Legacy Router Cleanup (C-002, C-003)
│   Duration: 4-6 days
│   Deliverable: Prefix migrated, tests passing
│   Depends: C-001 complete
│
├─ PHASE 3: Architecture Decisions Implemented
│   Duration: 4-6 weeks
│   Candidates: C-004 (faculty/programs/courses), C-005 (identity), C-007 (configs)
│   Risk: HIGH (multiple components affected)
│
└─ PRODUCTION READY
    All candidates: READY or REMOVED status
    Rollback plan: Documented + tested
```

---

## REFERENCE TOTALS

| Candidate | Code Refs | Where | Impact |
|-----------|-----------|-------|--------|
| C-001 | 8 | frontend/app/admin + BFF routing | 33 files to reorganize |
| C-002 | 2 | main.py imports only | Low — simple swap |
| C-003 | 2 | main.py imports only | Low — simple swap |
| C-004 | 3 | main.py includes (faculty/programs/courses) | High — 3 routers blocked |
| C-005 | 8 | auth/hardening tests/health checks | High — login path dependency |
| C-007 | 8 | 6 service modules import | High — 6 module refactoring |

---

## RISK ASSESSMENT

### Critical Path Dependencies
```
C-001 (BFF) → C-002, C-003 (prefix migration)
C-004 decision → C-007 distribution
C-005 auth unification → Remove phase1_router safely
```

### Security Considerations
- ⚠️  **C-005**: Identity module hardening (LDAP injection tests) depends on phase1_router
- ⚠️  **C-001**: BFF proxy attack surface; careful credential forwarding required
- ⚠️  **C-004**: Faculty/programs/courses table-level access controls in university_core

### Test Coverage
- ❌ No dedicated `test_university_core.py` (C-007)
- ❌ No `test_legacy_enrollments.py` or `test_legacy_students.py` found
- ✅ `test_identity_phase11_hardening.py` exists (C-005 security tests)
- ✅ Frontend e2e tests check `/api/bff/*` paths (C-001 affects)

---

## FILE LOCATIONS REFERENCE

```
Analysis files:
├── MIGRATION_PATHS_ANALYSIS.md     ← Detailed technical breakdown
├── MIGRATION_PATHS_ANALYSIS.json   ← Structured data (JSON)
└── MIGRATION_ANALYSIS_SUMMARY.md   ← This file

Code locations:
Backend:
├── backend/app/main.py                                (router includes)
├── backend/app/modules/students/router.py            (C-002)
├── backend/app/modules/enrollments/router.py         (C-003)
├── backend/app/modules/faculty/router.py             (C-004)
├── backend/app/modules/programs/router.py            (C-004)
├── backend/app/modules/courses/router.py             (C-004)
├── backend/app/modules/identity/phase1_router.py     (C-005)
├── backend/app/modules/identity/router.py            (C-005)
├── backend/app/modules/university_core/service.py    (C-007)
└── backend/app/modules/auth/router.py                (C-005 dependency)

Frontend:
├── frontend/app/admin/ (33 files)                     (C-001)
├── frontend/app/(admin)/console/                      (C-001 replacement)
├── frontend/shared/api/client.ts                      (BFF routing)
└── frontend/app/api/bff/[...path]/route.ts           (BFF proxy)

Tests:
└── backend/tests/test_identity_phase11_hardening.py  (C-005 hardening)
```

---

## NEXT STEPS (THIS WEEK)

1. **Review**: Architecture board reviews findings
2. **Decide**: C-004 namespace + C-007 distribution strategy
3. **Unblock**: C-005 auth unification design
4. **Plan**: C-001 BFF redesign starts (lowest blocker first)

---

## NOTES

- All paths verified to exist (✅ not hypothetical)
- Reference counts from automated grep (repeatable)
- Endpoints extracted from decorator analysis (@router.get, etc.)
- Complexity estimates based on codebase structure + dependency graph
- BFF proxy is critical dependency (mentioned in 4+ contexts)

