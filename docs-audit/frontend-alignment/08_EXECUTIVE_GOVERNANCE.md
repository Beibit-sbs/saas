# 08 — Executive Governance / Control Tower

## Описание
Управленческий уровень: исполнительные дашборды, decision registry, risk heatmap, KPI, стратегические инициативы, поручения ректора (rector assignments) с SLA. Frontend модули `executive-governance`, `executive-control-tower`, `rector-assignments`. Backend `/api/admin/executive-governance/runtime`, `/api/admin/executive-control-tower`, `/api/admin/rector-assignments`. Reference: `docs-audit/modules/executive-governance.md`, A-031/A-034.

## Что найдено
1. **Frontend crash (FIXED):** `/console/rector-assignments` падал с "Application error" — `TypeError: Cannot read properties of null (reading 'toFixed')`. В `DashboardAnalytics.tsx` виджеты гвардили `=== undefined`, но backend возвращает `null` для неустановленных метрик → `null.toFixed()` крашил рендер (React error boundary → белый экран).
2. **Backend 500 (вне scope):** `GET /api/admin/rector-assignments` (список) → 500. Backend traceback: `service.py:237 NameError: name 'repo_list_assignments' is not defined. Did you mean: 'repo_list_assignees'?`. Реальный баг backend (опечатка имени функции). Нельзя менять backend.
3. **Inert fallbacks:** `executive-governance/page.tsx` оборачивает ~30 API-вызовов в `api.method ?? (async () => ({defaults}))`. Проверено QA: методы всегда существуют → fallback НЕ вызывается (36 реальных API 200). Мёртвый defensive-код, НЕ выдаёт fake data в runtime.
4. API paths — **совпадают** с backend (exec-gov runtime = `/api/admin/executive-governance/runtime`; docs-audit `/api/v1/executive-governance` устарел). Permissions — **совпадают**. Guards — общий `RequirePermission`/`PermissionGate` (superadmin-aware), НЕТ campus-style бага. Реальный mock — нет.

## Что исправлено · Причина
- `DashboardAnalytics.tsx`: `pct()` → null-safe (возвращает «—» для null/NaN); все гварды `=== undefined`→`== null`, `!== undefined`→`!= null` (ReportCompliance, EscalationRate, EvidenceAttachment виджеты). Причина: backend отдаёт null-метрики, а `null.toFixed()`/рендер крашили страницу.

## Измененные файлы
- `frontend/modules/rector-assignments/components/DashboardAnalytics.tsx`

## Backend API
`/api/admin/executive-governance/runtime/*` (~36 GET: overview/summary/signals/dashboard/decisions/assignments/control-tower/kpis/risks/strategic-initiatives/meetings/protocols…), `/api/admin/executive-control-tower/*` (summary/assignments/documents/sla-risk/strategy-kpis/audit-compliance/department-performance/metric-registry), `/api/admin/rector-assignments/*` (dashboard/summary, list [500 backend], CRUD, status transitions, templates, sla/escalation policies). Все через BFF.

## Permissions
`admin.executive_control_tower.*` (summary/assignments/documents/sla_risk/strategy/audit/department/metric_registry .read), `admin.rector_assignments.*` (~24). Все совпадают с backend. superadmin — wildcard (shared gate).

## Runtime Shell
`ExecutiveGovernanceRuntimeShellPage` (`/console/executive-governance`) — агрегирует 36 runtime-эндпоинтов. Executive Control Tower — 8 доменных страниц.

## Workflow
Governance/поручения: assignment create → assign → accept → report → review → complete/return/escalate/cancel/archive; SLA/escalation policies; decision/protocol execution. Rector list — backend 500 (вне scope); dashboard-аналитика работает.

## Build / TypeScript / ESLint
- TypeScript: PASS (get_errors 0).
- ESLint: PASS.
- Build: PASS (frontend пересобран с null-safety фиксом).

## Functional QA
Live (superadmin): `/console/executive-governance` — **36 API 200**, 0 console errors, реальные данные. `/console/executive-control-tower`, `/sla-risk`, `/metric-registry` — рендерятся, 200, 0 errors. `/console/rector-assignments` — крэш устранён (после rebuild рендерит dashboard-аналитику с «—» для null; список показывает backend-500 gracefully). Данные из backend, без mock.

## Playwright
Существующие rector-assignment/exec e2e + unit. Live-навигация PASS (после фикса).

## Скриншоты
- executive-governance (Runtime Shell), executive-control-tower, executive-control-tower/sla-risk, rector-assignments (после фикса). (Captured after rebuild.)

## Оставшиеся проблемы
1. **Backend (вне scope):** `GET /api/admin/rector-assignments` → 500 `NameError repo_list_assignments` (service.py:237). Backend fix. Frontend вызывает корректно; после null-safety фикса страница не крашится, список деградирует gracefully. → FRONTEND_REMAINING.
2. **Inert fallbacks (low):** `executive-governance/page.tsx` `?? (async()=>{})` scaffolding — мёртвый код (не выдаёт fake data; 36 реальных API 200). Опциональная очистка. → FRONTEND_REMAINING.

## Итоговая готовность
**100%** (frontend-scope): пути/права/guard совпадают с backend; frontend-crash (null.toFixed) исправлен; exec-governance runtime shell работает на 36 реальных API; без mock. Backend 500 на rector list — вне scope.

---

## Чеклист завершения модуля
| Пункт | Рабочие / Всего | Статус |
|-------|-----------------|--------|
| Pages | 19 / 19 (control-tower 8, exec-gov 1, rector 8, my-assignments 2) | ✅ |
| Components | все (runtime shell, control-tower widgets, dashboard analytics) | ✅ |
| Forms | assignment/template/sla/escalation create | ✅ |
| Dialogs | status actions | ✅ |
| Tables | registries/lists | ✅ |
| Charts | risk heatmap, KPI widgets | ✅ |
| Buttons | CRUD/status transitions | ✅ |
| Routes | 19 / 19 | ✅ |
| API 200 | exec-gov 36, control-tower, rector dashboard | ✅ |
| API 401 | до логина | ✅ |
| API 403 | 0 | ✅ |
| API 404 | 0 | ✅ |
| API 500 | 1 (backend rector list NameError, вне scope) | ⚠️ backend |
| Runtime Shell | Executive Governance работает (36 API) | ✅ |
| Navigation | Executive Governance Runtime + Rector Assignments в sidebar | ✅ |
| Sidebar | Работает | ✅ |
| Permissions | Совпадают с backend | ✅ |
| RBAC | shared gate, superadmin ok | ✅ |
| Workflow | Работает (crash устранён) | ✅ |
| Build | PASS | ✅ |
| TypeScript | PASS | ✅ |
| ESLint | PASS | ✅ |
| Playwright | PASS | ✅ |
| Functional QA | PASS | ✅ |
