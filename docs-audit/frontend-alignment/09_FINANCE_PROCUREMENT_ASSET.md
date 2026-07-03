# 09 — Finance / Procurement / Asset

## Описание
Финансово-хозяйственный контур: бюджеты, расходы, закупки (PO), поставщики, активы/инвентаризация, задолженности, платежи. Frontend модули `finance-procurement-asset` (23-page suite), `budget-planning`, `delinquency-collections`, `asset-inventory`, `expense-controls`, `procurement-workflow`, `contracts-legal-repository`. Backend `/api/admin/finance-procurement-asset`, `/api/admin/budget-planning`, `/api/admin/procurement`, `/api/admin/asset-inventory`, `/api/admin/delinquency-collections`, `/api/admin/expense-controls`. Reference: `docs-audit/modules/finance-procurement-asset.md`.

## Что найдено
1. **budget-planning orphan → 404 (phantom API):** `frontend/modules/budget-planning/hooks.ts` вызывает `/api/budgets/*` (dashboard/summary, `/{id}/lines`, `/expenses`, `/variances`, `/approve`…). Backend такого НЕТ — `budget_planning` router = `/api/admin/budget-planning` с минимальным контрактом (`/plans`, `/allocations`, `/brain-context`). `/api/budgets` НЕ проксируется BFF → 404. Страница `/console/budget-planning` — **orphan** (нет в sidebar), gracefully показывает ErrorState ("Failed to load budget data"). Rich-контракт не имеет backend.
2. **Null-crash risk (FIXED):** `asset-inventory/page.tsx` (`original_value`/`current_value`.toLocaleString(), `depreciation_rate`.toFixed()) и `delinquency-collections/page.tsx` (`amount_due`.toLocaleString()) без null-guard — при null от backend упали бы (класс rector-assignments crash). В текущих данных значения не-null (не крашились), но риск латентный.
3. FPA suite (23 стр.), asset-inventory, delinquency-collections, expense-controls, procurement — используют корректный `/api/admin/*`, общий `RequirePermission` (superadmin-aware), реальные данные, БЕЗ mock (`fake*` флаги=false). Работают.

## Что исправлено · Причина
- `asset-inventory/page.tsx`, `delinquency-collections/page.tsx`: добавлены `?? 0` guards перед `.toLocaleString()`/`.toFixed()`. Причина: nullable numeric поля backend не должны крашить таблицу.

## Измененные файлы
- `frontend/app/(admin)/console/asset-inventory/page.tsx`
- `frontend/app/(admin)/console/delinquency-collections/page.tsx`

## Backend API
`/api/admin/finance-procurement-asset/*` (~32 endpoints), `/api/admin/asset-inventory/{items,depreciation}`, `/api/admin/delinquency-collections/*`, `/api/admin/expense-controls/{expenses,cost-centers,brain-context}`, `/api/admin/procurement/*`, `/api/admin/budget-planning/{plans,allocations,brain-context}`. Все (кроме phantom `/api/budgets`) через BFF.

## Permissions
`finance_procurement_asset.*` (51), `asset_inventory.read`, `finance.read` (delinquency/expense), `procurement.*`, `budget.*`. Совпадают с backend. Общий gate (superadmin wildcard).

## Runtime Shell
FPA suite — metadata-visibility (fake* флаги false). asset-inventory/delinquency/expense-controls/procurement — actionable registries.

## Workflow
Закупка (request→approval→PO→delivery→asset), задолженность (record→escalation→collection), бюджет (план/аллокация). Проверено: реестры + действия рендерятся.

## Build / TypeScript / ESLint
- TypeScript: PASS (get_errors 0).
- ESLint: PASS.
- Build: PASS (frontend пересобран с null-guards).

## Functional QA
Live (superadmin): FPA suite `/console/finance-procurement-asset` (Suite), `/purchase-orders`, `/budget-planning`, `/budget-control` — рендерятся, 0 errors, метаданные. `/console/asset-inventory` — 2 реальные строки активов (toLocaleString на реальных данных, без crash). `/console/delinquency-collections` — 2 API 200. `/console/expense-controls` — 3 API 200. Все без mock. `/console/budget-planning` (orphan) — 404 на phantom `/api/budgets` → ErrorState (handled, не crash).

## Playwright
Существующие finance/budget/asset e2e + unit. Live-навигация PASS.

## Скриншоты
- finance-procurement-asset (Suite), asset-inventory (реальные строки), budget-planning (ErrorState orphan). (Captured after rebuild.)

## Оставшиеся проблемы
1. **budget-planning orphan (HIGH):** `/console/budget-planning` + `modules/budget-planning` построены на несуществующем `/api/budgets/*` rich-контракте. Backend имеет только `/api/admin/budget-planning/{plans,allocations}`. Страница — orphan (нет в sidebar), gracefully errors, вытеснена FPA suite `/console/finance-procurement-asset/budget-planning` (работает). Требует либо backend rich-budget API (вне scope — нельзя менять backend), либо полного переписывания модуля под минимальный контракт. → FRONTEND_REMAINING.

## Итоговая готовность
**~95%**: основные finance-поверхности (FPA suite 23 стр., asset-inventory, delinquency, expense-controls, procurement) работают на реальном API, без mock, с корректными правами; null-crash риски устранены. Orphan `/console/budget-planning` (phantom API, вне sidebar, gracefully errors) задокументирован как HIGH — не устраним без backend или полного переписывания.

---

## Чеклист завершения модуля
| Пункт | Рабочие / Всего | Статус |
|-------|-----------------|--------|
| Pages | 27 / 28 (FPA suite 23 + asset/delinquency/expense/procurement; budget-planning orphan 404) | ⚠️ |
| Components | все | ✅ |
| Forms | create/status/escalation | ✅ |
| Dialogs | present | ✅ |
| Tables | реестры (asset 2 rows, delinquency, expense) | ✅ |
| Charts | KPI/metric cards | ✅ |
| Buttons | CRUD/status | ✅ |
| Routes | 27 / 28 | ⚠️ |
| API 200 | FPA/asset/delinquency/expense/procurement | ✅ |
| API 401 | до логина | ✅ |
| API 403 | 0 | ✅ |
| API 404 | budget-planning orphan (phantom /api/budgets) | ⚠️ documented |
| API 500 | 0 | ✅ |
| Runtime Shell | FPA suite работает | ✅ |
| Navigation | FPA/asset/delinquency/expense в sidebar; budget-planning orphan | ⚠️ |
| Sidebar | Работает | ✅ |
| Permissions | Совпадают с backend | ✅ |
| RBAC | shared gate, superadmin ok | ✅ |
| Workflow | Работает | ✅ |
| Build | PASS | ✅ |
| TypeScript | PASS | ✅ |
| ESLint | PASS | ✅ |
| Playwright | PASS | ✅ |
| Functional QA | PASS (budget-planning orphan documented) | ✅ |
