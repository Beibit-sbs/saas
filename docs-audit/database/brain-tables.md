# Кластер таблиц: Brain Core

[← Каталог таблиц](README.md) · Brain: [../brains/brain-core.md](../brains/brain-core.md)

ORM: `brain_core/models.py`. Миграции: `fa12bc34de56_create_brain_core_tables`, `fb23cd45ef67_add_brain_core_extended_tables`, `lh01ij23kl45_add_brain_signal_dedup_key`.

## Таблицы (сводно)

| Таблица | Описание | PK | FK | CRUD |
|---------|----------|----|----|------|
| `brain_core_signal_definitions` | Определения типов сигналов (реестр) | id | tenant_id→app_tenants | Brain signal registry |
| `brain_core_signals` | Принятые сигналы (с dedup_key) | id | tenant_id | Brain signal intake |
| decisions | Записи решений (DecisionRegistry) | id | tenant_id, signal_id | Brain decision |
| explanations | Объяснения решений | id | tenant_id, decision_id | Brain explainability |
| outcomes | Исходы кейсов | id | tenant_id, decision_id | Brain outcome/learning |

## Связи
signal_definition 1:N signals; signal 1:N decisions; decision 1:1 explanation; decision 1:N outcomes.

## Изоляция
Все tenant‑scoped; API использует `_assert_tenant_match()` (A‑009). Signal dedup через `dedup_key`.

## Используется в
Все доменные brain‑вертикали, Runtime Shells, Executive KPI, Digital Twin.
