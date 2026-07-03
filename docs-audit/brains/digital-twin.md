# Brain: Digital Twin (Цифровой двойник)

[← Каталог Brain](README.md) · [Обзор Brain](../07_BRAIN_MODULES.md)

Модуль: `backend/app/modules/digital_twin/` · API prefix `/api/admin/digital-twin` · A‑056

## Назначение
Предиктивная симуляция операций вуза и capacity what‑if моделирование. **Только чтение**, fail‑closed, без автономных действий.

## Функции
Наблюдение измерений кампуса · what‑if симуляция вместимости/ресурсов · раннее предупреждение по вместимости · реестр сценариев · аудируемые решения по сценариям · лог решений (readback).

## Используемые / входные данные
Измерения: студенты, персонал, аудитории/здания, расписания, бюджеты, инвентарь, нагрузка сервисов, события безопасности. Источники (reuse): 5 сигнальных реестров + capacity‑модули (`enrollments`, `scheduling`, `room_booking`, `asset_inventory`, `dormitory_management`, `dining`). Live enrollments/classroom capacity wiring (A‑056.4/.7).

## Выходные данные
`GET /tenants/{id}/state` (измерения + источники), `GET /tenants/{id}/safety-boundaries` (запрещённые действия), what‑if сценарии, decision log.

## Permissions
`state.read`, `safety.read`, `simulate.run`, `decision.record`, `decision.read` (`digital_twin/permissions.py`, импортируется в `rbac/service.py`).

## Запрещённые действия (fail‑closed)
`autonomous_budget_commitment`, `autonomous_academic_decision`, `autonomous_disciplinary_decision`, `hidden_scoring`, `any_execution_without_human_approval`, `supplier_order_without_human_approval`.

## Связанные Runtime Shell
Собственный frontend shell (`frontend/modules/digital-twin`, `/console/digital-twin`); переиспользует capacity‑модули.

## Гарантии / Проблемы
Не фабрикует числа симуляций; при сбое БД честно возвращает None. Проблема: полнота живой проводки данных (A‑056.* в процессе). Тест‑коллекция чинилась (`A-056.G1`).
