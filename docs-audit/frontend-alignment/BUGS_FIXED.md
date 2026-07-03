# Bugs Fixed — Frontend Alignment

Format: Date · Module · File · Problem · Cause · Fix · Verification

---

### 2026-07-03 · Academic Operations · frontend/shared/api/client.ts
- **Problem:** 9 sub-runtime pages returned 404.
- **Cause:** `mapToBffPath` did not proxy the non-standard prefix `/api/academic-operations/runtime/*` (only `/api/admin`, `/api/v1`).
- **Fix:** Added rule `if (path.startsWith("/api/academic-operations/runtime/")) return "/api/bff/" + slice`. Also generalized `/api/v1/*` proxying. Added `RuntimeNav` (constants.ts + pages.tsx) so sub-pages are reachable.
- **Verification:** curl 404→401; tsc 0; eslint clean.

### 2026-07-03 · AI (Brain Core) · frontend/modules/brain-core/hooks.ts, frontend/app/(admin)/console/ai/brain/page.tsx
- **Problem:** Brain Core Decision Center 404 on `/api/admin/brain/decisions`.
- **Cause:** Backend exposes tenant-scoped `GET /tenants/{tenant_id}/decisions` (A-009 isolation); frontend called `/decisions`.
- **Fix:** `useBrainDecisions(tenantId)` → `/tenants/${tenantId}/decisions`; page passes `tenantId`.
- **Verification:** live browser — `/tenants/1/decisions`=200, renders 5 decisions; 0 console errors.

### 2026-07-03 · AI · frontend/shared/config/navigation.ts, console/{knowledge-retrieval,prompt-management,model-evaluation}/page.tsx
- **Problem:** AI Cost/Routing in no nav profile; SUPERADMIN had no AI group; mutation errors not surfaced.
- **Cause:** Missing nav entries + missing `isError` UI.
- **Fix:** Added AI group (8 items) to SUPERADMIN_NAVIGATION + AI Cost/Routing to main NAVIGATION; added error states.
- **Verification:** live browser — sidebar AI group visible; vitest 33/33.

### 2026-07-03 · Auth/Identity (SYSTEMIC i18n) · frontend/app/components/LanguageProvider.tsx
- **Problem:** Admin pages (RBAC, Identity, LDAP, Local Users, Service Accounts) rendered raw i18n keys (`rbacRolesTitle`, `identityProvider`, …).
- **Cause:** `LanguageProvider.t()` read only `commonTranslations`; `adminTranslations` (i18n/admin/*.ts) was dead code, never wired — missing keys fell back to the raw key.
- **Fix:** Merged `adminTranslations` into `getRuntimeDictionary` (common precedence) + fallback dicts.
- **Verification:** live browser — `rawKeysFound: []` on all 5 admin pages; tsc 0; eslint 0.

### 2026-07-03 · Campus Facilities · frontend/modules/campus-facilities/api.ts
- **Problem:** 8 API paths would 404.
- **Cause:** FE `/transport/routes|/vehicles|/schedules` vs BE `/transport-routes|-vehicles|-schedules`; FE 3× `/transport/*/metadata` vs BE single `/transport/metadata`; FE `/bridges/finance-asset` vs BE `/bridges/finance-assets`.
- **Fix:** Rewrote paths to match backend router decorators.
- **Verification:** vitest ApiClient 7/7; tsc 0.

### 2026-07-03 · Campus Facilities · frontend/modules/campus-facilities/constants.ts
- **Problem:** Route-guard permissions never matched backend → permanent fail-close on transport + 4 bridges.
- **Cause:** FE `campus_facilities.transport.read` / `campus_facilities.bridges.*` vs BE `campus_facilities.transport_routes.read` / `campus_facilities.*_bridge.read`.
- **Fix:** Aligned routeDefinition + dashboard-card `requiredPermission` to backend strings (display endpoints kept count=52).
- **Verification:** vitest Guards 33/33, Types 7/7; tsc 0.

### 2026-07-03 · Campus Facilities (SYSTEMIC superadmin) · frontend/modules/campus-facilities/pages.tsx
- **Problem:** All campus pages fail-closed for superadmin.
- **Cause:** Campus guard read raw `user.permissions` (empty for superadmin) without the superadmin wildcard that shared `hasPermission` applies.
- **Fix:** `CampusFacilitiesPageRuntime` feeds superadmin all route permissions (`Object.values(CAMPUS_FACILITIES_ROUTE_PERMISSION_MAP)`).
- **Verification:** live browser — all campus pages `accessDenied:false`, 0 console errors.
