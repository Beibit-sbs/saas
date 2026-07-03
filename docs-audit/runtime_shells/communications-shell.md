# Runtime Shell: Communications (частичный)

[← Каталог Runtime Shells](README.md)

## Назначение
Дашборд коммуникаций: уведомления, delivery‑аудит, эскалации, предпочтения, brain‑actions.

## Страницы
`/console/communications/*` (~9: overview, announcements, notifications, templates, escalations, delivery-audit, preferences, provider-readiness, brain-actions).

## Backend
`communications/router.py` (Prefix `/api/admin/communications`), `notification_center/router.py`.

## Frontend
`frontend/modules/communications/` — `api.ts` (`CommunicationsRuntimeShellResponse`), `pages.tsx`, `types.ts`, `components/`.

## Permissions
`communications/permissions.py`. Роли: `communications_admin`, `auditor`, получатели.

## Связанные Brain Modules
[Brain Core](../brains/brain-core.md) (brain‑actions страница). Каналы `email`/`in_app`/`webhook` (outbox).

## Проблемы
Частичный shell; **0 выделенных backend‑тестов** на момент инвентаря (V15). Текущая активная волна (A‑054).
