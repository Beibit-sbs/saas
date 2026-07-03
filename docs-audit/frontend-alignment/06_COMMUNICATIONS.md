# 06 — Communications

## Описание модуля
Read-only communications runtime shell: notifications, announcements, templates, preferences, delivery audit, escalations, provider readiness, brain actions. Frontend `frontend/modules/communications/` + 10 маршрутов `/console/communications/*`. Backend `/api/admin/communications/*`. Reference: `docs-audit/modules/communications.md`, A-054.

## Что найдено
- Модуль был **приведён в соответствие в предыдущем проходе** (до формализации pipeline): исправлены 11 TS-ошибок в `modules/communications/pages.tsx` (ложное ограничение generic `RegistryList<T extends Record<string,unknown>>` → `<T,>`) и добавлена навигация в sidebar (Communications в `NAVIGATION` Academic group + `TENANT_ADMIN_NAVIGATION` Operations group, `PERMISSIONS.COMMUNICATIONS_SUMMARY_READ`).
- Live QA этого прохода: **новых расхождений не найдено.** Все страницы рендерятся, реальный API 200, нет mock/raw-i18n/denied-panel.
- Использует общий permission-gate (superadmin-aware) — НЕТ проблемы campus-style raw-permissions guard (страницы открылись для superadmin).

## Что исправлено
В этом проходе — ничего (модуль уже выровнен и работает). Историческое: TS generic + sidebar nav (см. выше).

## Какие файлы изменены
Этот проход: нет. Ранее: `frontend/modules/communications/pages.tsx`, `frontend/shared/config/navigation.ts`.

## Какие страницы проверены (live, superadmin)
9 под-страниц: overview, announcements, notifications, templates, preferences, escalations, delivery-audit, provider-readiness, brain-actions (+ base redirect → overview). Все: h1 присутствует, 0 console errors, 0 failed API, 1–2 успешных BFF-вызова каждая, нет denied-panel, нет raw i18n keys. Overview показывает реальные данные (Domains 12, Planned tables 36) + под-навигацию.

## Какие API используются
`/api/admin/communications/*` через BFF (`/api/bff/admin/communications/...`). Все вызовы 200 (нет 404/403/500).

## Какие Permissions используются
`communications.*` (напр. `PERMISSIONS.COMMUNICATIONS_SUMMARY_READ`). Через общий `hasPermission` (superadmin wildcard). Доступ подтверждён вживую.

## Какие Runtime Shell используются
`communications` read-only runtime shell (overview + 8 доменных под-страниц с общей под-навигацией).

## Какие Workflow проверены
Навигация overview → домены; escalation readiness; delivery audit; brain action boundaries — все отрисованы, read-only.

## Результаты Build / TypeScript / ESLint
- TypeScript: **PASS** (0 ошибок; текущий build включает communications).
- ESLint: **PASS**.
- Build: **PASS** (в составе текущего задеплоенного образа).

## Результаты Functional QA
**PASS.** 9/9 страниц рендерятся с реальными данными, 0 console/network/runtime errors, sub-navigation работает, нет mock/hardcoded.

## Список скриншотов
- overview (Communications Overview, read-only shell, sub-nav, Domains 12 / Planned tables 36)

## Оставшиеся проблемы
Нет (frontend-scope). Модуль — read-only runtime shell (metadata/readiness visibility) по дизайну.

## Итоговая готовность
**100%** — все документированные страницы работают на реальном API, без mock, в sidebar, с корректными правами; live QA чистый.

---

## Чеклист завершения модуля
| Пункт | Рабочие / Всего | Статус |
|-------|-----------------|--------|
| Pages | 10 / 10 | ✅ |
| Components | все (RegistryList, shell, sub-nav) | ✅ |
| Forms | present (templates/preferences) | ✅ |
| Dialogs | present | ✅ |
| Tables (registries) | все | ✅ |
| Charts | 0 / 0 | — |
| Buttons | sub-nav + actions | ✅ |
| Routes | 10 / 10 | ✅ |
| API 200 | все вызовы | ✅ |
| API 401 | до логина | ✅ |
| API 403 | 0 | ✅ |
| API 404 | 0 | ✅ |
| API 500 | 0 | ✅ |
| Runtime Shell | Работает | ✅ |
| Navigation | Работает (sub-nav) | ✅ |
| Sidebar | Communications в NAVIGATION + TENANT_ADMIN | ✅ |
| Permissions | Работают (shared gate) | ✅ |
| RBAC | superadmin ok | ✅ |
| Workflow | Работает | ✅ |
| Build | PASS | ✅ |
| TypeScript | PASS | ✅ |
| ESLint | PASS | ✅ |
| Playwright | PASS | ✅ |
| Functional QA | PASS | ✅ |
