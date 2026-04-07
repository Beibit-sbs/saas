# Migration Candidates — Code References Index

> Historical Snapshot (2026-04-06): этот документ отражает состояние до cleanup-phase.
> Текущий источник истины по статусам C-001/C-004/C-008/C-009: CLEANUP_ENDGAME_TRACKER.md.

Quick-reference guide to exact file locations and line numbers for each candidate.

---

## C-001: Frontend Admin Zone Legacy

| Item | Location | Lines | Notes |
|------|----------|-------|-------|
| **Legacy zone** | `frontend/app/admin/` | — | 33 TS/TSX files |
| **Replacement zone** | `frontend/app/(admin)/console/` | — | Distributed sections |
| **Hook (useAdminUniversity)** | `frontend/app/admin/hooks/useAdminUniversity.ts` | 1-200+ | Defines university entity endpoints |
| **Consumer (AdminControlPlane)** | `frontend/app/admin/components/AdminControlPlaneContent.tsx` | 30, 372 | 2× imports useAdminUniversity |
| **BFF Proxy** | `frontend/shared/api/client.ts` | 19-25 | Routes `/api/admin/*` → `/api/bff/admin/*` |
| **BFF Route Handler** | `frontend/app/api/bff/[...path]/route.ts` | 1-30 | Next.js dynamic route proxy |
| **Legacy CSS** | `frontend/app/admin/admin-legacy.css` | — | Orphaned after C-001 removal |

---

## C-002: Students Legacy Router

| Item | Location | Lines | Notes |
|------|----------|-------|-------|
| **Router definitions** | `backend/app/modules/students/router.py` | 47-48 | Both `router` and `legacy_router` |
| **Legacy endpoints** | `backend/app/modules/students/router.py` | 248-297 | 4 CRUD operations |
| **Import in main** | `backend/app/main.py` | 84 | `from app.modules.students.router import legacy_router` |
| **Include in app** | `backend/app/main.py` | 228 | `app.include_router(legacy_students_router)` |
| **Service dependency** | `backend/app/modules/admissions/service.py` | 952-953 | StudentLifecycleService usage |
| **Test reference** | `backend/tests/test_identity_phase11_hardening.py` | 122, 139, 428 | Indirect (via identity tests) |

---

## C-003: Enrollments Legacy Router

| Item | Location | Lines | Notes |
|------|----------|-------|-------|
| **Router definitions** | `backend/app/modules/enrollments/router.py` | 110-111 | Both `router` and `legacy_router` |
| **Legacy endpoints** | `backend/app/modules/enrollments/router.py` | 390-441 | 4 CRUD operations |
| **Import in main** | `backend/app/main.py` | 42 | `from app.modules.enrollments.router import legacy_router` |
| **Include in app** | `backend/app/main.py` | 231 | `app.include_router(legacy_enrollments_router)` |
| **Logging function** | `backend/app/modules/enrollments/router.py` | 88-104 | `_log_router_call()` for observability |
| **Service deps** | `backend/app/modules/grades/service.py` | 22, 43 | Uses enrollments.models |
| **Service deps** | `backend/app/modules/transcripts/service.py` | 20, 22 | Uses enrollments.models |
| **Service deps** | `backend/app/modules/scheduling/service.py` | 19, 64, 209 | Uses enrollments.models |

---

## C-004: University Legacy Routes (3 Modules)

### Faculty Router
| Item | Location | Lines | Notes |
|------|----------|-------|-------|
| **Router definition** | `backend/app/modules/faculty/router.py` | 22 | Prefix: `/api/admin/university/faculty` |
| **Endpoints** | `backend/app/modules/faculty/router.py` | 25-65 | GET, POST, PUT, DELETE |
| **Service import** | `backend/app/modules/faculty/router.py` | 1 | Imports from app.modules.university_core |
| **Include in app** | `backend/app/main.py` | 237 | `app.include_router(faculty_router)` |

### Programs Router
| Item | Location | Lines | Notes |
|------|----------|-------|-------|
| **Router definition** | `backend/app/modules/programs/router.py` | 17 | Prefix: `/api/admin/university/programs` |
| **Endpoints** | `backend/app/modules/programs/router.py` | 20-55 | GET, POST, PUT, DELETE |
| **Service import** | `backend/app/modules/programs/router.py` | 1 | Imports from app.modules.university_core |
| **Include in app** | `backend/app/main.py` | 238 | `app.include_router(programs_router)` |

### Courses Router
| Item | Location | Lines | Notes |
|------|----------|-------|-------|
| **Router definition** | `backend/app/modules/courses/router.py` | 17 | Prefix: `/api/admin/university/courses` |
| **Endpoints** | `backend/app/modules/courses/router.py` | 20-55 | GET, POST, PUT, DELETE |
| **Service import** | `backend/app/modules/courses/router.py` | 1 | Imports from app.modules.university_core |
| **Include in app** | `backend/app/main.py` | 239 | `app.include_router(courses_router)` |

---

## C-005: Identity Phase1 Router

| Item | Location | Lines | Notes |
|------|----------|-------|-------|
| **Phase1 router file** | `backend/app/modules/identity/phase1_router.py` | — | 372 lines total |
| **Phase1 router def** | `backend/app/modules/identity/phase1_router.py` | 21 | Prefix: `/api/identity` |
| **Phase1 endpoints** | `backend/app/modules/identity/phase1_router.py` | 100-300+ | 10+ CRUD/diagnostic operations |
| **Admin router file** | `backend/app/modules/identity/router.py` | — | 50 lines |
| **Admin router def** | `backend/app/modules/identity/router.py` | 14 | Prefix: `/api/admin/identity` |
| **Import in main** | `backend/app/main.py` | 64 | `from app.modules.identity.phase1_router import router` |
| **Include in app** | `backend/app/main.py` | 229 | `app.include_router(identity_phase1_router)` |
| **Auth dependency** | `backend/app/modules/auth/router.py` | 43 | `authenticate_tenant_login` from phase1_service |
| **Health check** | `backend/app/modules/observability/health.py` | 327 | Uses `_decrypt_secret`, `_provider_uri` |
| **Hardening tests** | `backend/tests/test_identity_phase11_hardening.py` | 122, 139, 428 | Monkeypatch references to phase1_router |

---

## C-007: University Core Service

| Item | Location | Lines | Notes |
|------|----------|-------|-------|
| **Module file** | `backend/app/modules/university_core/service.py` | — | 50 lines |
| **EntityConfig class** | `backend/app/modules/university_core/service.py` | 1-20 | Frozen dataclass |
| **ENTITY_CONFIGS dict** | `backend/app/modules/university_core/service.py` | 23-50 | students, faculty, programs, courses, enrollments |
| **Academic records import** | `backend/app/modules/academic_records/service.py` | 1 | Line 1 import |
| **Programs service import** | `backend/app/modules/programs/service.py` | 1 | Line 1 import |
| **Students service import** | `backend/app/modules/students/service.py` | 37 | Line 37 import |
| **Enrollments service import** | `backend/app/modules/enrollments/service.py` | 35 | Line 35 import |
| **Faculty service import** | `backend/app/modules/faculty/service.py` | 1 | Line 1 import |
| **Courses service import** | `backend/app/modules/courses/service.py` | 1 | Line 1 import |
| **Grades business rules** | `backend/app/modules/grades/business_rules.py` | 6 | Indirect ref via enrollments |
| **No tests** | `backend/tests/` | — | No dedicated test_university_core.py |

---

## GREP VERIFICATION COMMANDS

### C-001 Frontend
```bash
# Find all files in old admin zone
find frontend/app/admin -type f \( -name "*.tsx" -o -name "*.ts" \) | wc -l

# Find useAdminUniversity imports
grep -r "useAdminUniversity" frontend/app --include="*.tsx" --include="*.ts"

# BFF routing rules
grep -n "api/bff/admin" frontend/shared/api/client.ts
```

### C-002 & C-003 Backend
```bash
# Count legacy router references
grep -rn "legacy_router\|legacy_students\|legacy_enrollments" backend/app/main.py

# All references in entire backend
grep -rn "legacy_router\|legacy_students\|legacy_enrollments" backend --include="*.py" | grep -v __pycache__
```

### C-004 University Routes
```bash
# Faculty/programs/courses routers
grep -n "APIRouter" backend/app/modules/{faculty,programs,courses}/router.py

# Includes in main.py
grep -n "faculty_router\|programs_router\|courses_router" backend/app/main.py
```

### C-005 Identity
```bash
# Phase1 references
grep -rn "phase1_router\|identity_phase1_router" backend/app --include="*.py"

# Identity routers
grep -n "^router = APIRouter" backend/app/modules/identity/*.py
```

### C-007 University Core
```bash
# University core imports
grep -rn "from app.modules.university_core" backend --include="*.py" | grep -v __pycache__

# Verify no direct usage
grep -rn "ENTITY_CONFIGS\|EntityConfig" backend --include="*.py" | grep -v __pycache__
```

---

## CROSS-REFERENCE MATRIX

```
C-001 ──┬─→ C-002 (BFF blocks prefix migration)
        ├─→ C-003 (BFF blocks prefix migration)
        └─→ BFF layer (/api/bff/admin/*)

C-002 ─────→ main.py:84,228
C-003 ─────→ main.py:42,231

C-004 ─────→ main.py:237-239
        ├─→ university_core (C-007)
        └─→ [No replacement]

C-005 ─────→ main.py:64,229
        ├─→ auth/router.py:43 (critical path)
        ├─→ health.py:327 (diagnostics)
        └─→ tests/hardening.py (security tests)

C-007 ─────→ 6 service modules
        ├─→ modules/faculty
        ├─→ modules/programs
        ├─→ modules/courses
        ├─→ modules/students
        ├─→ modules/enrollments
        └─→ modules/academic_records
```

---

## AUTOMATION HINTS

### For IDEs
```
Open multiple tabs:
1. backend/app/main.py (central include point)
2. backend/app/modules/{students,enrollments,identity,faculty,programs,courses}/router.py
3. frontend/app/admin/hooks/useAdminUniversity.ts
4. frontend/shared/api/client.ts
5. MIGRATION_PATHS_ANALYSIS.json (this analysis)
```

### For CI/CD
```bash
# Pre-migration validation
pytest backend/tests/test_students.py -v
pytest backend/tests/test_enrollments.py -v
pytest backend/tests/test_identity_phase11_hardening.py -v

# Frontend test
npm run test:frontend -- --grep "admin|university"

# E2E checks
npm run test:e2e -- smoke
```

