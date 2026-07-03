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
