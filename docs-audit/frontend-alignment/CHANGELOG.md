# Changelog — Frontend Alignment

Format: Date · Module · What changed · Files · Checks

---

### 2026-07-03 · Module 01 Academic Operations
- BFF proxy for `/api/academic-operations/runtime/*`; generalized `/api/v1/*`; added RuntimeNav.
- Files: `shared/api/client.ts`, `modules/academic-operations-runtime/constants.ts`, `modules/academic-operations-runtime/pages.tsx`.
- Checks: tsc 0, eslint clean, curl 401.

### 2026-07-03 · Module 02 Admissions
- No changes (already aligned; fail-closed by design).
- Checks: tsc 0, no mocks.

### 2026-07-03 · Module 03 AI
- Brain decisions tenant-scoped path; SUPERADMIN AI nav group + AI Cost/Routing; mutation error states.
- Files: `modules/brain-core/hooks.ts`, `app/(admin)/console/ai/brain/page.tsx`, `shared/config/navigation.ts`, `app/(admin)/console/{knowledge-retrieval,prompt-management,model-evaluation}/page.tsx`.
- Checks: tsc 0, eslint clean, vitest 33/33, live QA 11 pages.

### 2026-07-03 · Module 04 Auth/Identity
- SYSTEMIC i18n: wired `adminTranslations` into LanguageProvider (fixes raw admin keys app-wide).
- Files: `app/components/LanguageProvider.tsx`.
- Checks: tsc 0, eslint 0, live QA 7 pages (rawKeys=[]).

### 2026-07-03 · Module 05 Campus Facilities
- 8 API path fixes; transport + bridge permission-string alignment; superadmin wildcard parity.
- Files: `modules/campus-facilities/api.ts`, `constants.ts`, `pages.tsx`.
- Checks: tsc 0, vitest 47/47, live QA all pages render (0 errors).

### 2026-07-03 · Module 06 Communications
- No changes this pass (already aligned pre-pipeline). Verified live.
- Checks: tsc 0, live QA 9 pages (real API 200, no mocks).

### 2026-07-03 · Module 07 Documents
- Added Documents sidebar entry (3 nav profiles). Documented backend `int(actor)` dashboard/summary 400 (out of scope).
- Files: `shared/config/navigation.ts`.
- Checks: tsc 0, build PASS, live QA (registry/decrees/DDC suite render; dashboard 400 handled by ErrorState).

### 2026-07-03 · Module 08 Executive Governance
- Fixed rector-assignments dashboard null-crash (`null.toFixed()`). Documented backend rector-list 500 NameError (out of scope) + inert exec-gov fallbacks.
- Files: `modules/rector-assignments/components/DashboardAnalytics.tsx`.
- Checks: tsc 0, build PASS, live QA (exec-gov runtime 36 API 200; control-tower render; rector crash fixed).

### 2026-07-03 · Module 09 Finance / Procurement / Asset
- Added null-guards to asset-inventory + delinquency table cells. Documented budget-planning orphan (phantom `/api/budgets` API, no backend).
- Files: `app/(admin)/console/asset-inventory/page.tsx`, `app/(admin)/console/delinquency-collections/page.tsx`.
- Checks: tsc 0, build PASS, live QA (FPA suite/asset/delinquency/expense render real data; budget-planning orphan 404 documented).
