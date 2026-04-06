# Migration Paths Analysis — Legacy Routes/Modules

**Date**: 6 апреля 2026  
**Scope**: Systematic analysis of 7 migration candidates  
**Method**: File existence verification, grep reference count, endpoint mapping, complexity estimation

---

## SUMMARY TABLE

| ID | Legacy Path | Replacement Path | Status | Refs | Endpoints | Complexity | Blockers |
|----:|--|--|--|--:|--:|--|--|
| C-001 | `frontend/app/admin/` | `frontend/app/(admin)/console/` | ✅ exists | **8** | N/A | **HIGH** (33 files, route mapping) | BFF proxy rewrite needed |
| C-002 | `backend/.../students/legacy_router.py` | `backend/.../students/router.py` | ✅ exists | **2** | 4 (CRUD) | **MEDIUM** (same endpoints, prefix change) | None confirmed |
| C-003 | `backend/.../enrollments/legacy_router.py` | `backend/.../enrollments/router.py` | ✅ exists | **2** | 4 (CRUD) | **MEDIUM** (same endpoints, prefix change) | None confirmed |
| C-004 | `/api/admin/university/{faculty,programs,courses}` | platform/admin API v1 | ⚠️ PARTIAL | **3** | 12 (CRUD×3) | **HIGH** (no true replacement in current API) | Replacement not yet architected |
| C-005 | `backend/.../identity/phase1_router.py` | `backend/.../identity/router.py` | ⚠️ DUAL | **8** | 10+ (identity management) | **HIGH** (dual auth path, hardening tests) | Tests reference phase1_router explicitly |
| C-007 | `backend/.../university_core/service.py` | N/A | ❌ ORPHANED | **8** | N/A | **MEDIUM** (6 module dependencies) | Shared data layer, not a router |

---

## DETAILED FINDINGS

### C-001: Legacy Admin Zone Frontend

**Legacy Path**: `frontend/app/admin/`  
**Replacement Path**: `frontend/app/(admin)/console/`  
**Status**: Both exist; migration requires route/component switching

#### Inventory
```
frontend/app/admin (33 TS/TSX files):
├── components/ (7 files)
├── hooks/ (8 files - useAdminUniversity, useAdminJobs, useAdminRbac, etc.)
├── page.tsx
├── types.ts
├── utils.ts
├── admin-legacy.css
└── utils/

frontend/app/(admin)/console (multi-section structure):
├── admissions/, ai/, audit/, automation/, billing/
├── dashboard/, developer/, enrollments/, feature-flags/
├── grades/, health/, integrations/, interventions/
├── jobs/, notifications/, ops/, platform/
├── preferences/, profile/, scheduling/, security/
├── students/, tenants/, transcripts/
└── page.tsx
```

#### Key Findings
- **File count**: 33 legacy files vs. distributed structure in console/
- **API Layer**: Old admin uses BFF proxy (`/api/bff/admin/university/*`)
- **BFF Routing**: Frontend routes `/api/admin/*` → `/api/bff/admin/*` via [client.ts line 23](frontend/shared/api/client.ts#L23)
- **Reference Count**: 8 imports of `useAdminUniversity` and related hooks
- **New Structure**: Console uses direct module paths (no legacy "university" namespace)

#### Complexity Estimate: **HIGH**
- ❌ No direct 1:1 route mapping; console restructures information architecture
- ❌ Component tree requires rewrite (admin/ → (admin)/console/)
- ⚠️  useAdminUniversity hook references `/api/bff/admin/university/` paths only
- **Migration blocker**: Frontend still using BFF; direct client removal requires client-side API layer migration

---

### C-002: Legacy Students Route (Backend)

**Legacy Path**: `backend/app/modules/students/legacy_router.py` (exported as `legacy_router` from router.py)  
**Replacement Path**: `backend/app/modules/students/router.py`  
**Status**: Both defined in same file; direct replacement available

#### Endpoints Defined
```python
# Line 47-48 (router.py)
router = APIRouter(prefix="/api/admin/students", tags=["students"])
legacy_router = APIRouter(prefix="/api/admin/university/students", tags=["students"])
```

#### Legacy Endpoints (4 endpoints, lines 248-297)
- `@legacy_router.get("")` → GET /api/admin/university/students
- `@legacy_router.post("")` → POST /api/admin/university/students
- `@legacy_router.put("{student_id}")` → PUT /api/admin/university/students/{id}
- `@legacy_router.delete("{student_id}")` → DELETE /api/admin/university/students/{id}

#### New Endpoints (6 endpoints, lines 87-226)
- `@router.post("")` → POST /api/admin/students (create)
- `@router.get("")` → GET /api/admin/students (list)
- `@router.get("{student_id}")` → GET /api/admin/students/{id} (read)
- `@router.patch("{student_id}/status")` → PATCH /api/admin/students/{id}/status
- `@router.post("{student_id}/program-bindings")` → POST /api/admin/students/{id}/program-bindings
- `@router.get("{student_id}/program")` → GET /api/admin/students/{id}/program

#### Reference Count
- **Backend refs**: 2 (imports in [main.py line 84](backend/app/main.py#L84), include at line 228)
- **Test refs**: 0 confirmed (no direct test_legacy_students)
- **Service refs**: Used by admissions.service (line 952-953) indirectly

#### Complexity Estimate: **MEDIUM**
- ✅ Same function signatures (copy-paste level similarity)
- ✅ Ready replacement exists with extended functionality
- ⚠️  Old endpoints lack /program and /program-bindings operations
- **Migration path**: Direct prefix swap; test data validation required

---

### C-003: Legacy Enrollments Route (Backend)

**Legacy Path**: `backend/app/modules/enrollments/legacy_router.py`  
**Replacement Path**: `backend/app/modules/enrollments/router.py`  
**Status**: Both defined; replacement has extended endpoints

#### Endpoints Defined
```python
# Line 110-111 (router.py)
router = APIRouter(prefix="/api/admin", tags=["enrollments"])
legacy_router = APIRouter(prefix="/api/admin/university/enrollments", tags=["enrollments"])
```

#### Legacy Endpoints (4 endpoints, lines 390-441)
- `@legacy_router.get("")` → GET /api/admin/university/enrollments
- `@legacy_router.post("")` → POST /api/admin/university/enrollments
- `@legacy_router.put("{enrollment_id}")` → PUT /api/admin/university/enrollments/{id}
- `@legacy_router.delete("{enrollment_id}")` → DELETE /api/admin/university/enrollments/{id}

#### New Endpoints (8 endpoints, lines 114-461)
- Full CRUD at `/api/admin/enrollments/` and nested under `/api/admin/courses/{course_id}/roster`
- Includes status change, course roster listing, advanced filtering

#### Reference Count
- **Backend refs**: 2 (imports in [main.py line 42](backend/app/main.py#L42), include at line 231)
- **Service deps**: grades.service, transcripts.service, scheduling.service use enrollments.models
- **Test refs**: None detected for legacy path

#### Complexity Estimate: **MEDIUM**
- ✅ Endpoint signatures compatible
- ✅ New router strictly extends functionality
- ⚠️  Missing course roster aggregation in legacy
- **Migration path**: Prefix migration + client needs roster endpoint awareness

---

### C-004: University Legacy Routes (Faculty, Programs, Courses)

**Legacy Paths**:
- `backend/app/modules/faculty/router.py` → `/api/admin/university/faculty`
- `backend/app/modules/programs/router.py` → `/api/admin/university/programs`
- `backend/app/modules/courses/router.py` → `/api/admin/university/courses`

**Replacement Path**: `platform/admin API v1` (incomplete)  
**Status**: ⚠️ **PARTIAL** — no direct replacement architected

#### Current State
```python
# Faculty (router.py line 22)
router = APIRouter(prefix="/api/admin/university/faculty", tags=["university-faculty"])
# 4 endpoints: GET, POST, PUT, DELETE

# Programs (router.py line 17)
router = APIRouter(prefix="/api/admin/university/programs", tags=["university-programs"])
# 4 endpoints: GET, POST, PUT, DELETE

# Courses (router.py line 17)
router = APIRouter(prefix="/api/admin/university/courses", tags=["university-courses"])
# 4 endpoints: GET, POST, PUT, DELETE
```

#### Endpoints Summary
| Module | GET / | POST / | PUT /{id} | DELETE /{id} |
|--------|-------|--------|----------|------------|
| Faculty | ✅ | ✅ | ✅ | ✅ |
| Programs | ✅ | ✅ | ✅ | ✅ |
| Courses | ✅ | ✅ | ✅ | ✅ |

#### Reference Count
- **Includes in main.py**: 3 (lines 237-239)
- **Service cross-refs**: 
  - Faculty service uses university_core (line 1)
  - Programs service uses university_core (line 1)
  - Courses service uses university_core (line 1)

#### Complexity Estimate: **HIGH**
- ❌ **No replacement exists** in current architecture
- ❌ Platform v1 admin router exists but doesn't absorb these routes
- ⚠️  These are "university domain" APIs not yet migrated to platform namespace
- **Architecture gap**: Either keep legacy namespace or architect platform/university/{faculty,programs,courses}

#### Migration Blockers
1. **No target namespace decided** — is it:
   - `/api/platform/admin/university/{faculty,programs,courses}`?
   - `/api/v1/admin/university/*`?
   - Keep existing `/api/admin/university/*`?
2. **university_core dependency** — C-007 must be resolved first
3. **No migration timeline** — requires architecture decision

---

### C-005: Identity Phase1 Router

**Legacy Path**: `backend/app/modules/identity/phase1_router.py`  
**Replacement Path**: `backend/app/modules/identity/router.py`  
**Status**: ⚠️ **DUAL LAYER** — both active, different prefixes

#### Router Definition
```python
# phase1_router.py (line 21)
router = APIRouter(prefix="/api/identity", tags=["identity"])
# 10+ endpoints for provider/mapping management

# router.py (line 14)
router = APIRouter(prefix="/api/admin/identity", tags=["identity-admin"])
# Different permission context, different endpoints
```

#### Endpoints in Phase1 Router (372 lines)
- Provider CRUD: `/api/identity/providers`, `/api/identity/providers/{id}`, `/api/identity/providers/{id}/test`
- Mapping CRUD: `/api/identity/mappings`, `/api/identity/mappings/{id}`
- Preview/diagnostics: `/api/identity/providers/{id}/mapping/preview`

#### Endpoints in Admin Router (50 lines)
- Provider management (list, upsert): `/api/admin/identity/providers`
- Permission layer: `admin.integrations.manage`

#### Reference Count
- **Backend refs**: 8
  - main.py import [line 64](backend/app/main.py#L64)
  - main.py include [line 229](backend/app/main.py#L229)
  - auth/router.py uses phase1_service [line 43](backend/app/modules/auth/router.py#L43)
  - observability/health.py [line 327](backend/app/modules/observability/health.py#L327)
  - tests: test_identity_phase11_hardening.py [lines 122, 139, 428](backend/tests/test_identity_phase11_hardening.py)

#### Complexity Estimate: **HIGH**
- ❌ **Dual authority**: phase1 handles provider setup, router handles admin integration
- ⚠️  Tests explicitly mock `phase1_router` (hardening tests depend on phase1)
- ⚠️  Login flow uses phase1_service.authenticate_tenant_login (auth path dependency)
- **Architecture issue**: Both routers handle identity but with different scopes

#### Migration Blockers
1. **Login flow hardening** — phase1_router is tested for LDAP injection attack resistance
2. **No unified identity endpoint yet** — router assumes OAuth patterns, phase1 is LDAP-centric
3. **Test mocking** — removing phase1 breaks identity hardening test suite

---

### C-007: University Core Service (Orphaned Module)

**Path**: `backend/app/modules/university_core/service.py`  
**Type**: Data layer service, not a router  
**Status**: ❌ **ORPHANED** — no entry point, shared by 6 modules

#### Module Contents
```python
# service.py (50 lines)
@dataclass(frozen=True)
class EntityConfig:
    table: str
    fields: tuple[str, ...]
    required: tuple[str, ...]
    fk_fields: tuple[str, ...] = ()

ENTITY_CONFIGS = {
    "students": EntityConfig(...),
    "faculty": EntityConfig(...),
    "programs": EntityConfig(...),
    "courses": EntityConfig(...),
    "enrollments": EntityConfig(...),
}
```

#### Dependency Map
```
university_core.service
├── academic_records/service.py (line 1 import)
├── programs/service.py (line 1 import)
├── students/service.py (line 37 import)
├── enrollments/service.py (line 35 import)
├── faculty/service.py (line 1 import)
└── courses/service.py (line 1 import)
```

#### Reference Count
- **Code refs**: 8 (6 services + 2 additional refs)
- **No router**: No APIRouter definition
- **No direct usage**: Used only via module imports
- **No tests**: No dedicated test_university_core.py

#### Purpose Analysis
- Central registry of database table configurations
- Metadata layer for university domain entities
- Defines field mappings, required fields, foreign key relationships

#### Complexity Estimate: **MEDIUM**
- ✅ Self-contained; no external dependencies
- ✅ Pure data structure (no business logic)
- ⚠️  6 modules depend on this; removal requires redistribution of configs
- **Migration path**: Either consolidate into each module or keep as shared config layer

#### Migration Blockers
1. **Distributed config**: Each service needs its EntityConfig definition
2. **Import path changes**: All 6 services must update imports
3. **No clear replacement**: Decision needed — per-module or new location?

---

## REFERENCE VERIFICATION COMMANDS

```bash
# Verify all legacy references
grep -rn "legacy_router\|legacy_students\|legacy_enrollments" backend/app --include="*.py" | grep -v __pycache__

# Phase1 identity references
grep -rn "phase1_router\|identity_phase1" backend/app --include="*.py" | grep -v __pycache__

# University core references
grep -rn "from app\.modules\.university_core" backend/app --include="*.py" | grep -v __pycache__

# Frontend admin references
find frontend/app/admin -type f \( -name "*.tsx" -o -name "*.ts" \) | wc -l

# BFF proxy checks
grep -rn "api/bff/admin/university" frontend/app --include="*.tsx" --include="*.ts"
```

---

## MIGRATION ESTIMATE MATRIX

| Candidate | Effort | Risk | Timeline | Owner |
|-----------|--------|------|----------|-------|
| **C-001** | 40 hrs | HIGH (route rewrite, BFF) | 2 weeks | Frontend team |
| **C-002** | 8 hrs | LOW (prefix swap) | 2-3 days | Backend team |
| **C-003** | 8 hrs | LOW (prefix swap) | 2-3 days | Backend team |
| **C-004** | 60 hrs | HIGH (no replacement) | 4-6 weeks | Architecture |
| **C-005** | 20 hrs | MEDIUM (test mocking) | 1-2 weeks | Security/Auth team |
| **C-007** | 12 hrs | LOW (data layer) | 3-5 days | Backend team |

---

## RECOMMENDATION

### PHASE 1 (No Blocker Changes)
✅ **C-002 & C-003**: Frontend BFF layer decoupling is prerequisite; can proceed after C-001

### PHASE 2 (After BFF Proxy Resolved)
✅ **C-002**: Students legacy route → `/api/admin/students` (2-3 days)  
✅ **C-003**: Enrollments legacy route → `/api/admin/enrollments` (2-3 days)

### PHASE 3 (Architecture Decision Needed)
⏳ **C-004**: Require Architecture Board decision on university routes namespace  
⏳ **C-005**: Coordinate with Auth/Security on identity unification  
⏳ **C-007**: Distribute EntityConfig post-C-004

### PHASE 4 (BFF Redesign)
❌ **C-001**: Blocked until frontend API client rewrite (depends on Phase 2 completion)

