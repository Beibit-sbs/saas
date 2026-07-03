# 10 — Полный аудит Feature Flags

[← 09 Интеграции](09_INTEGRATIONS.md) · [Индекс](README.md) · Далее: [11 Background Jobs →](11_BACKGROUND_JOBS.md)

Источники: `app/platform/feature_flags/service.py`, `app/modules/feature_flags/`, миграция `ff01a2b3c4d5_feature_flags_rollout_percentage.py`.

---

## 11.1 Модель feature flags

- **Хранение:** DB‑backed (persistent) + in‑memory кэш (двухуровневый: `_flag_cache[(tenant_id, module, key)]` + `_tenant_list_cache[tenant_id]`). Таблица `app_platform_feature_flags`.
- **Область (scope):** `platform` (глобально) или `tenant` (для конкретного тенанта).
- **Структура флага:** `scope`, `module` (напр. `admissions`), `key` (напр. `early_warning_auto_intervention`), `enabled` (bool), `rollout_percentage` (0–100), `tenant_id`.
- **Оценка:** детерминированный bucketing по **SHA‑256** от актора — обеспечивает стабильное поведение при частичном раскате (`rollout_percentage < 100`).

---

## 11.2 Ключевые функции

| Функция | Назначение |
|---------|-----------|
| `set_platform_feature(module, key, enabled, rollout_percentage=100)` | Глобальный платформенный флаг |
| `set_tenant_feature(tenant_id, module, key, enabled, rollout_percentage=100)` | Тенант‑специфичный флаг |
| `is_flag_enabled_for_actor(module, key, actor_id, tenant_id)` | Оценка с детерминированным bucketing |
| `list_tenant_features(tenant_id)` | Список флагов тенанта (наполняет кэш) |
| `clear_feature_flag_cache()` | Сброс кэша (при мутациях) |

---

## 11.3 API и UI

- **API:** `/api/admin/feature-flags` (модульный роутер) и `/api/v1/admin/feature-flags` (платформенный): create/set, list по тенанту, delete.
- **UI:** админ‑консоль, вкладка **feature-flags** (`/console/platform/feature-flags`, `frontend/modules/feature-flags`) — видимость и переключение on/off.

---

## 11.4 Известные ключи флагов

> **Явного централизованного каталога ключей в статике не обнаружено.** Ключи создаются динамически по паре `(module, key)`. Примеры паттернов из кода/документации: `early_warning_auto_intervention` (модуль `admissions`/интервенции), флаги по модулям `academic_integrity` и др.

Управляющий флаг маршрутизации биллинга — на уровне конфигурации: `is_billing_module_router_enabled()` (`app/core/config.py`) определяет, подключать ли `billing_router` (не через таблицу флагов, а через окружение).

---

## 11.5 Зрелость и проблемы (аудит)

- По `README.md` и `SBS_UB_PROJECT_CONTEXT_2026.md`: модуль feature flags помечен как **scaffold / требующий явного ревью перед продакшеном**. Ранее описывался как in‑memory; текущая реализация — DB‑backed с кэшем и rollout %.
- **Нет единого реестра ключей** — усложняет аудит активных флагов; рекомендация: централизованный каталог ключей.
- Разночтение статуса между историческим `README` («scaffold/in‑memory») и текущим кодом (DB‑backed) — приведены оба.
