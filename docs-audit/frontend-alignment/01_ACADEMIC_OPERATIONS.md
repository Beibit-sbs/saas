# 01 — Academic Operations

## Описание модуля
Runtime-shell driven academic operations module (`/console/academic-operations/*`). Frontend module `modules/academic-operations-runtime`. Backend routers under `/api/v1/academic-operations/*` (runtime shell) and `/api/academic-operations/runtime/*` (sub-runtime routers). Reference docs: `docs-audit/modules/academic-operations.md`, A-052.

## Что найдено
- **BFF proxy bug (systemic):** sub-runtime routers use the non-standard prefix `/api/academic-operations/runtime/*` (not `/api/v1`, not `/api/admin`). `mapToBffPath` in `shared/api/client.ts` did not proxy this prefix → 9 sub-runtime pages fetched the frontend origin → **404** (confirmed via curl).
- **Missing sub-navigation:** the 9 sub-runtime pages had no in-shell navigation entry, making them unreachable from the runtime-shell entry point.

## Что исправлено
- Added proxy rule to `mapToBffPath`: `if (path.startsWith("/api/academic-operations/runtime/")) return "/api/bff/" + path.slice(5)`.
- Added `ACADEMIC_OPERATIONS_RUNTIME_NAV_ITEMS` + a `RuntimeNav` component rendered in the runtime-shell page so all 9 sub-pages are reachable.

## Какие файлы изменены
- `frontend/shared/api/client.ts`
- `frontend/modules/academic-operations-runtime/constants.ts`
- `frontend/modules/academic-operations-runtime/pages.tsx`

## Какие страницы проверены
22 routes under `/console/academic-operations/*` (runtime-shell + dashboard + 9 sub-runtime pages + sub-views). All resolve; no mock/hardcoded data.

## Какие API используются
`/api/v1/academic-operations/*` (runtime shell) and `/api/academic-operations/runtime/*` (sub-runtime) via BFF proxy → backend `/api/...`. Verified `/api/bff/academic-operations/runtime/dashboard` returns 401 (auth-handled), not 404.

## Какие Permissions используются
Frontend `PERMISSIONS.ACADEMIC_OPERATIONS_*` map exactly to backend `academic_operations.*`.

## Какие Runtime Shell используются
`academic-operations/runtime-shell` + 9 sub-runtime shells (dashboard, etc.).

## Какие Workflow проверены
Runtime-shell entry → sub-runtime navigation → data fetch chain.

## Результаты Build / TypeScript / ESLint
- TypeScript: **0 errors**
- ESLint: **clean**
- Build: image rebuilt successfully.

## Результаты Functional QA
Verified in TENANT_ADMIN sidebar; routes reachable; API BFF-proxied (401 handled, no 404). No mocks.

## Список скриншотов
(Pre-pipeline module; screenshots captured for the AI module onward.)

## Оставшиеся проблемы
None (frontend-scope). 

## Итоговая готовность
**100%** — frontend fully aligned to backend + docs-audit.
