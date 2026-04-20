# Wave 1 Prep Design Brief: #32 Billing Router + Models

Дата: 2026-04-18
Task ID: #32
Статус: PREP-API-PARITY-EXPANDED
Owner: Platform Backend Team
Reviewers: Architecture, QA

## 1) Контекст и цель

Billing в системе уже работает частично через platform-слой (plans/subscription/usage), но модульная область `modules/billing` не имеет собственного router и явных моделей/схем API-контракта.

Цель prep-фазы: подготовить контракт и структуру данных для контролируемого post-day7 внедрения без нарушения One Active Delivery и без параллельного разрозненного потока.

## 2) Текущее состояние (as-is)

- Есть backend логика жизненного цикла подписки в `backend/app/modules/billing/service.py`.
- В `backend/app/modules/billing` добавлен scaffold: `router.py`, `schemas.py`, `models.py`.
- Подключение в runtime добавлено в `backend/app/main.py` через feature flag `BILLING_MODULE_ROUTER_ENABLED` (по умолчанию OFF/fail-safe).
- В module router добавлены parity-endpoints для plans/subscription assign/usage increment (под собственным префиксом `/api/admin/billing`).
- Публичные billing endpoints сейчас находятся в platform-роутерах:
  - `backend/app/platform/router_admin.py`
  - `backend/app/modules/platform/router.py`
- Frontend роутинг `/console/billing/*` уже есть и покрыт route-тестом:
  - `frontend/__tests__/admin/BillingRoutes.test.tsx`

## 3) Целевое состояние (to-be, post-day7)

- Добавить `backend/app/modules/billing/router.py` как модульный entrypoint billing API.
- Добавить `backend/app/modules/billing/schemas.py` для стабильного API-контракта.
- Добавить `backend/app/modules/billing/models.py` для явного доменного слоя billing (без дублирования существующих platform-таблиц).
- Сохранить единый контур исполнения:
  - переход поэтапный,
  - обратная совместимость существующих platform endpoints,
  - без запуска отдельного независимого delivery-stream.

## 4) API Contract Draft (черновик)

Префикс (actual, per layer architecture): `/api/admin/billing`

1. `GET /plans`
2. `POST /plans`
3. `PUT /tenants/{tenant_id}/subscription`
4. `POST /tenants/{tenant_id}/subscription/transition`
5. `POST /tenants/{tenant_id}/subscription/plan-change`
6. `POST /tenants/{tenant_id}/usage/{metric}`
7. `GET /tenants/{tenant_id}/state`

Примечание: в фазе внедрения сохранить backward-compatible прокси/алиасы для текущих путей в platform-роутерах до формального cutover.

## 5) Data Model Map (черновик)

Минимальный набор сущностей:

1. `billing_plan`
- code (unique)
- name
- price_cents
- features (json)
- limits (json)
- created_at / updated_at

2. `tenant_subscription`
- tenant_id (unique)
- plan_id
- status (trial/active/suspended/cancelled)
- started_at
- trial_ends_at
- current_period_start/current_period_end
- next_plan_id (nullable)
- updated_at

3. `usage_counter`
- tenant_id
- metric
- period_key
- value
- updated_at

4. `invoice`
- tenant_id
- period_key
- plan_code
- base_amount_cents
- usage_amount_cents
- total_amount_cents
- currency
- breakdown (json)
- created_at

## 6) Migration Outline (draft)

1. Инвентаризация текущих таблиц и полей, которые уже используются repository/service.
2. Подготовка Alembic migration только для отсутствующих структур/индексов.
3. Добавление check/index constraints под статусы и ключи `(tenant_id, metric, period_key)`.
4. Rollback план для миграции (включая verify query).

## 7) Skeleton Test List (prep-ready)

Backend contract skeleton:

1. `backend/tests/modules/billing/test_billing_router_contract_skeleton.py`
- test_get_plans_contract_shape
- test_create_plan_contract_shape
- test_assign_subscription_contract_shape
- test_transition_subscription_contract_shape
- test_plan_change_contract_shape
- test_usage_increment_contract_shape
- test_get_tenant_state_contract_shape

Compatibility skeleton:

2. `backend/tests/modules/billing/test_billing_platform_compat_skeleton.py`
- test_legacy_platform_billing_paths_still_respond_during_migration
- test_legacy_and_new_paths_return_compatible_payload_keys

Frontend integration skeleton:

3. `frontend/__tests__/admin/BillingApiContractSkeleton.test.tsx`
- test_billing_plans_screen_reads_new_api_contract
- test_billing_quotas_screen_handles_subscription_state
- test_billing_usage_screen_handles_usage_metric_contract

## 8) Риски и контроль

Риски:

1. Дублирование логики между platform и modules/billing.
2. Ломка текущих frontend path expectations.
3. Регресс idempotency/replay semantics на мутациях.

Контрмеры:

1. Compatibility phase с dual-path contract checks.
2. Запрет remove старых путей до green contract matrix.
3. Обязательный replay/idempotency чек в mutation tests.

## 9) Ready Criteria (для перевода в active delivery после day7)

1. Contract draft согласован (Architecture + QA).
2. Model map + migration outline подтверждены.
3. Skeleton test list добавлен в test plan.
4. Нет конфликтов с One Active Delivery / Unified Contour policy.
