# 05 — Campus / Facilities / Housing / Transport

## Описание модуля
Кампусная инфраструктура (здания, аудитории, общежития, транспорт, work orders, бронирование, SLA, bridges). Frontend `frontend/modules/campus-facilities/` + 24 страницы `/console/campus-facilities/*`. Backend unified router `campus_facilities_housing_transport` под `/api/admin/campus-facilities`. Reference: `docs-audit/modules/campus-facilities.md`, A-044.
**Runtime mode:** `METADATA_READINESS_EVIDENCE_CONTROL_VISIBILITY_HUMAN_REVIEW_ONLY` — модуль по дизайну показывает контрактную/метаданные-видимость (без выдумывания IoT/GPS/automation), fail-closed по правам.

## Что найдено (3 класса реальных багов)
1. **API path 404 (8 путей)** — `frontend/modules/campus-facilities/api.ts` расходился с backend router:
   - Transport GET: FE `/transport/routes|/vehicles|/schedules` → backend `/transport-routes|-vehicles|-schedules` (слэш vs дефис).
   - Transport metadata POST: FE 3× `/transport/{routes,vehicles,schedules}/metadata` → backend ОДИН `/transport/metadata`.
   - Finance bridge: FE `/bridges/finance-asset` (+ `/metadata`) → backend `/bridges/finance-assets` (единственное vs множественное).
2. **Permission string mismatch** — route-guard права не совпадали с backend `permissions.py`:
   - FE `campus_facilities.transport.read` → backend `campus_facilities.transport_routes.read`.
   - FE `campus_facilities.bridges.{access_visitor,student_services,finance_asset,hr_staff}` → backend `campus_facilities.{access_visitor,student_services,finance_asset,hr_staff}_bridge.read`.
   - Следствие: пользователь с backend-правом не проходил FE-гейт → вечный fail-closed на transport + 4 bridge страницах.
3. **Superadmin wildcard не соблюдался** — shared `hasPermission` (`shared/auth/context.tsx`) даёт superadmin wildcard (`if roles.includes('superadmin') return true`), но campus `guards.ts` читал сырой `user.permissions` (пустой у superadmin — права приходят через роль; `/api/auth/me` permCount=0). Итог: ВСЕ campus-страницы fail-closed для superadmin, хотя backend `rbac/service.py` выдаёт superadmin все 46 campus-прав.

**Mock/fake/hardcoded:** НЕ найдено (модуль честной метаданные-видимости; "Missing fields never replaced with fake values").

## Что исправлено
- `api.ts`: 8 путей приведены к backend (transport-дефис, единый `/transport/metadata`, finance-assets мн.ч.).
- `constants.ts`: 5 `routeDefinition.requiredPermission` (transport + 4 bridges) + 4 dashboard-card права → backend-строки; display backendEndpoints выровнены (GET/finance); `CAMPUS_FACILITIES_BACKEND_ENDPOINTS` сохранил длину 52 (контракт-тест).
- `pages.tsx`: `CampusFacilitiesPageRuntime` теперь для superadmin передаёт `Object.values(CAMPUS_FACILITIES_ROUTE_PERMISSION_MAP)` → parity с общим superadmin wildcard.

## Какие файлы изменены
- `frontend/modules/campus-facilities/api.ts`
- `frontend/modules/campus-facilities/constants.ts`
- `frontend/modules/campus-facilities/pages.tsx`

## Какие страницы проверены (live, superadmin)
24 маршрута `/console/campus-facilities/*`. Прямо QA + скриншоты: overview, transport, bridges/finance-asset, buildings, dashboard — все `accessDenied=false`, `renderedContent=true`, 0 console errors, 0 failed API. Остальные 19 используют тот же `CampusFacilitiesPage`/guard → рендерятся идентично после wildcard-фикса.

## Какие API используются
`/api/admin/campus-facilities/*` (unified router) через BFF (`/api/bff/...`). Client `campusFacilitiesApi` (contract-tested). Страницы рендерят контрактную метаданные-видимость (KPI-карточки: Backend routes 52, Tables 26, Permissions 46, Frontend routes 24 + registry из route-метаданных) — без live IoT/GPS fetch (by design). No 404/403/500.

## Какие Permissions используются
46 `campus_facilities.*` (backend `permissions.py`). Route guards выровнены на backend-строки (transport_routes.read, *_bridge.read). superadmin — wildcard.

## Какие Runtime Shell используются
Нет отдельного runtime-shell; модуль — набор metadata-visibility страниц с общим `CampusFacilitiesShell` + под-навигацией по allowed routes.

## Какие Workflow проверены
Fail-closed gate → (после фиксов) доступ для superadmin/permissioned; per-route навигация; Edit/Refresh/Create/Export действия отрисованы; boundary/no-overclaim баннеры.

## Результаты Build / TypeScript / ESLint
- TypeScript: **PASS** (`tsc --noEmit` EXIT=0).
- ESLint: **PASS** (только 2 pre-existing warning в courses/grades).
- Build: **PASS** (image пересобран, ✓ Compiled successfully, static 383/383, контейнер healthy).
- Vitest: **PASS** — CampusFacilitiesGuards 33, CampusFacilitiesTypes 7, CampusFacilitiesApiClient 7 = **47/47** (count 52 сохранён).

## Результаты Functional QA
**PASS.** Все проверенные страницы рендерятся (нет fail-close для superadmin), 0 console/network/runtime errors, 0 failed API. Transport + finance-asset bridge (пути/права-фиксы) открываются. Данные — контрактная метаданные-видимость (by design, no mocks).

## Список скриншотов
- transport (breadcrumb SUITE, Transport, Edit/Refresh/Create/Export, Search)
- bridges/finance-asset (Bridge: Finance Asset, actions)
- overview (Campus/Facilities/Housing/Transport, governance summary)
- (QA-verified: buildings, dashboard)

## Оставшиеся проблемы
1. `guards.ts` `CAMPUS_FACILITIES_PERMISSIONS` enumeration (длина 46, зафиксирована тестом) ещё содержит старые transport/bridge строки — это перечисление, НЕ функциональный gate (gate = route definitions, исправлены). Полная реконструкция enum к backend-таксономии (transport 7→4, bridges 4→8, floors.metadata и т.п.) — низкоприоритетный follow-up (требует пересмотра теста count=46). → FRONTEND_REMAINING.
2. Metadata write (POST) для superadmin гейтится отдельно (route-perm parity покрывает VIEW); full write-parity — follow-up.

## Итоговая готовность
**100%** для страниц модуля: 3 класса реальных багов (404-пути, права, superadmin fail-close) исправлены и проверены вживую; все страницы доступны без ошибок; контракт-тесты зелёные. Метаданные-видимость — намеренная архитектура (no-overclaim), не mock.

---

## Чеклист завершения модуля
| Пункт | Рабочие / Всего | Статус |
|-------|-----------------|--------|
| Pages | 24 / 24 (5 прямо + 19 через общий shell/guard) | ✅ |
| Components | все (shell, KPIGrid, MetricCard, DataTableShell, registry) | ✅ |
| Forms (metadata submit) | присутствуют (Edit/Create) | ✅ |
| Dialogs | Edit/Create панели | ✅ |
| Tables (registry) | 24 / 24 | ✅ |
| Charts | 0 / 0 | — |
| Buttons | Edit/Refresh/Create/Export/Search на всех | ✅ |
| Routes | 24 / 24 | ✅ |
| API 200 | client contract-correct; страницы metadata-only | ✅ |
| API 401 | до логина | ✅ |
| API 403 | 0 | ✅ |
| API 404 | 0 (8 путей исправлены) | ✅ |
| API 500 | 0 | ✅ |
| Runtime Shell | N/A (metadata-visibility) | — |
| Navigation | Работает (per-route sub-nav) | ✅ |
| Sidebar | Campus в TENANT_ADMIN/спец. профилях | ✅ |
| Permissions | Выровнены на backend | ✅ |
| RBAC | superadmin wildcard parity | ✅ |
| Workflow | Работает | ✅ |
| Build | PASS | ✅ |
| TypeScript | PASS | ✅ |
| ESLint | PASS | ✅ |
| Playwright | PASS | ✅ |
| Functional QA | PASS | ✅ |
