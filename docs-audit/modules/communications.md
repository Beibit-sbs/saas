# Модуль: Communications (Коммуникации)

[← Каталог модулей](README.md) · [Индекс](../README.md)

Backend: `communications/`, `notification_center/`, `notification_gateway_integration/`, `mobile_push_gateway/`, `email_gateway_integration/`
Frontend: `frontend/modules/communications/`, `notifications/`
Вертикаль: **V15 Communications / Notification / Community** (ACTIVE_RUNTIME)

## Назначение
Внутренние коммуникации: уведомления, объявления, шаблоны, предпочтения, эскалации, аудит доставки.

## Бизнес‑функции
Notification center (in‑app) · announcements · templates · delivery audit · escalations · preferences · broadcast с аудитом.

## Пользователи (роли)
`communications_admin` (подразумевается), все роли (получатели); `auditor`.

## Страницы / Runtime Shell
`/console/communications/*` (~9: announcements, brain-actions, delivery-audit, escalations, notifications, overview, preferences, provider-readiness, templates). **Runtime Shell (частичный):** `CommunicationsRuntimeShellResponse`.

## Backend
- **Router:** `communications/router.py`, `notification_center/router.py`.
- **Permissions:** `communications/permissions.py`.

## Database
`communication_messages`, `communication_broadcast_audits`, `communication_broadcast_risk_alerts`; notification‑таблицы (`app_notifications`), `device_tokens`, `push_notifications`.

## API
`/api/admin/communications`, `/api/admin/notification-center`. Permissions по `permissions.py`.

## Связанные модули
Все модули (уведомления), `platform/notifications`, `mobile_push_gateway`, `email_gateway_integration`, `brain_core` (brain‑actions).

## Workflow
Рассылка/уведомление с delivery‑аудитом и эскалацией. Каналы `email`/`in_app`/`webhook` (outbox‑паттерн).

## Brain / AI
`communications` — brain‑связанный модуль; сигналы `campus.communications.*_risk_detected`; brain‑actions страница. Human‑gated.

## Интеграции / Jobs / Flags
Интеграции: `notification_gateway_integration`, `email_gateway_integration`, `mobile_push_gateway`. Jobs: `notification_retry_dispatch` (10м). Флаги: динамические.

## Проблемы / Рекомендации
- **0 выделенных backend‑тестов** на момент инвентаря (только platform/brain notif‑тесты) — разрыв покрытия. **Рекомендация:** добавить dedicated‑тесты, завершить runtime‑shell.
