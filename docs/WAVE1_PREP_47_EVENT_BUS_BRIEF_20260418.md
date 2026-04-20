# Wave 1 Prep Design Brief: #47 Event Bus + Outbox Patterns

Дата: 2026-04-18
Task ID: #47
Статус: PREP-OPEN
Owner: Platform Architecture Team
Reviewers: Backend Lead, QA

## 1) Контекст и цель

Event bus в системе Uже реализован на 70-80%: PostgreSQL outbox pattern с at-least-once delivery, 6 event handlers, webhook subsystem с HMAC signing и retry. Цель hardening — закрыть gaps в event registry, DLQ management, admin UI и unpublished event types.

## 2) Текущее состояние (as-is)

### Что EXISTS (production-ready):

| Компонент | Файлы | LOC | Статус |
|-----------|-------|-----|--------|
| Outbox model + repository | `platform/events/models.py`, `repository.py` | ~434 | ✅ Полный CRUD, `FOR UPDATE SKIP LOCKED` |
| Event publisher | `platform/events/publisher.py` | 112 | ✅ Через UoW / session / standalone |
| Outbox worker | `platform/events/worker.py` | 171 | ✅ Batch, idempotent handlers, exp backoff |
| 6 Event handlers | `platform/events/handlers/*` | ~323 | ✅ Notification, Webhook, Analytics, EducationGraph, Automation, ContextProjection |
| Webhook subsystem | `platform/webhooks/*` | ~1158 | ✅ CRUD, HMAC signing, retry, SSRF-safe |
| Scheduler jobs | `platform/jobs/scheduler.py` | — | ✅ outbox_event_dispatch (60s), webhook_retry_dispatch (120s) |
| In-process event bus | `platform_shared/events.py` | 90 | ✅ Legacy pub/sub для тестов |
| Tests | `test_platform_outbox_events.py`, `test_platform_webhooks_v1.py`, etc. | ~650+ | ✅ |

### Delivery Guarantees (уже реализованы):

- ✅ At-least-once delivery (retry + exponential backoff, max 5 retries)
- ✅ Idempotency per handler (`event:{id}:handler:{name}`)
- ✅ Outbox atomicity (event вставляется в ту же DB transaction)
- ✅ Concurrency safety (`FOR UPDATE SKIP LOCKED`)
- ✅ Dead-letter logging (`outbox_event_dead_lettered`, `webhook_delivery_exhausted`)
- ✅ Trace context propagation (`inject_trace_context()`)
- ✅ Webhook duplicate suppression (`has_delivered_event()`)
- ✅ Status machine: `pending → processing → processed/failed`

### Продюсируемые события (5 call sites):

| Модуль | Event type | Aggregate |
|--------|-----------|-----------|
| `tenant/service.py` | `tenant.created` | tenant |
| `students/service.py` | `student.created` | student_profile |
| `enrollments/service.py` | `enrollment.created` | enrollment |
| `grades/service.py` | `grade.submitted` | grade_submission |
| `automation/actions.py` | (динамический) | зависит от правила |

### Объявленные, но НЕ продюсируемые event types (6):

`user.created`, `role.assigned`, `ai.chat.executed`, `integration.updated`, `workflow.approved`, `file.uploaded`

## 3) Gaps для закрытия (to-be, post-day7)

### Gap 1: Event Type Registry + Schema Validation (HIGH)

**Проблема:** Нет центрального реестра допустимых event_type. Валидация только для TENANT_AWARE подмножества. Нет версионирования схем.

**Решение (draft):**
- Создать `platform/events/registry.py` — единый enum/registry всех event types с Pydantic payload schemas
- При `EventPublisher.publish()` — валидация event_type против registry, reject unknown types
- Версионирование: `event_type.v1` → `event_type.v2` с явным mapping

**Skeleton test list:**
- `test_event_registry_rejects_unknown_type`
- `test_event_registry_validates_payload_schema`
- `test_event_registry_versioned_type_mapping`

### Gap 2: Admin UI для Webhook Subscriptions (HIGH)

**Проблема:** Webhook CRUD есть в API, но нет admin UI для управления подписками.

**Решение (draft):**
- Frontend: `/console/webhooks` — list subscriptions, create, edit, deactivate, delivery history
- Использовать существующий API: `GET/POST /api/v1/admin/platform/webhooks/subscriptions`, etc.
- Добавить в admin navigation config

**Skeleton test list:**
- `test_webhook_subscriptions_page_renders`
- `test_webhook_create_form_validation`
- `test_webhook_delivery_history_display`

### Gap 3: Dead-Letter Queue (DLQ) Management (MEDIUM)

**Проблема:** Dead-letter только логируется; нет таблицы/UI для просмотра и re-drive.

**Решение (draft):**
- Добавить статус `dead_lettered` в OutboxEventModel (сейчас max_retries → failed)
- API: `GET /api/admin/events/dlq` — список dead-lettered событий
- API: `POST /api/admin/events/dlq/{event_id}/redrive` — повторная обработка
- Admin UI: виджет DLQ в `/console/webhooks` или отдельная страница `/console/events/dlq`

**Skeleton test list:**
- `test_dlq_list_returns_dead_lettered_events`
- `test_dlq_redrive_resets_event_to_pending`
- `test_dlq_redrive_respects_idempotency`

### Gap 4: Unpublished Event Types (MEDIUM)

**Проблема:** 6 event types объявлены в `TENANT_AWARE_EVENT_TYPES`, но нигде не продюсируются.

**Решение (draft):**
- `user.created` → wire в `auth/local_users_service.py` при create
- `role.assigned` → wire в `rbac/service.py` при assign_role
- `ai.chat.executed` → wire в `ai_gateway/service.py` после successful chat
- `integration.updated` → wire в `integrations/router.py` после PUT
- `workflow.approved` → wire в `workflows/service.py` при approve
- `file.uploaded` → отложить (нет file module)

**Skeleton test list:**
- `test_user_created_event_published`
- `test_role_assigned_event_published`
- `test_ai_chat_executed_event_published`
- `test_integration_updated_event_published`
- `test_workflow_approved_event_published`

### Gap 5: Event Replay / Re-processing (LOW for pilot)

**Решение (draft):**
- API: `POST /api/admin/events/{event_id}/replay` — повторная публикация события
- Safeguard: только admin, только для processed/failed, audit trail обязателен

### Gap 6: Event Filtering / Routing Rules (LOW for pilot)

**Решение (draft):**
- Дать handlers возможность register для конкретных event types (event_type filter)
- Сейчас каждый handler проверяет внутри себя — вынести в worker routing

## 4) Execution Priority (post-day7)

| Шаг | Gap | Приоритет | Зависимости |
|-----|-----|-----------|-------------|
| 1 | Event Type Registry | P0 | Нет |
| 2 | Unpublished Event Wiring (5 из 6) | P0 | Gap 1 |
| 3 | DLQ Management (API + basic) | P1 | Нет |
| 4 | Admin UI — Webhooks | P1 | F3.4 Frontend wave |
| 5 | Event Replay | P2 | Gap 3 |
| 6 | Event Filtering | P2 | Gap 1 |

## 5) Риски и ограничения

1. PostgreSQL outbox достаточен для текущей нагрузки (single-tenant pilot). При масштабировании — рассмотреть fan-out через Redis Streams или внешний broker.
2. Event ordering — best-effort (ORDER BY available_at, created_at, id), нет per-aggregate ordering. Для пилота допустимо.
3. Batch size фиксирован (20). При росте — добавить adaptive throttling.

## 6) Definition of Done (для перехода #47 из HARDENING → EXISTS)

- [ ] Event type registry с schema validation
- [ ] ≥5 unpublished event types wired к call sites
- [ ] DLQ API (list + redrive)
- [ ] Webhook subscriptions admin UI
- [ ] Regression: все существующие outbox/webhook тесты green
- [ ] Coverage: ≥80% на новый код
