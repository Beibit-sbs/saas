# API‑группа: Brain (`/api/admin/brain`)

[← Каталог API](README.md) · Brain: [../brains/brain-core.md](../brains/brain-core.md)

Роутер: `brain_core/router.py` · Guard: `admin.dashboard.read` · Изоляция тенанта: `_assert_tenant_match()` (A‑009).

## Core endpoints

| Метод | Путь | Описание | Response (сводно) |
|-------|------|----------|-------------------|
| GET | `/api/admin/brain/health` | Health Brain‑модуля | `{status}` |
| GET | `/tenants/{tenant_id}/signals` | Список сигналов тенанта | сигналы |
| GET | `/tenants/{tenant_id}/decisions` | Список решений тенанта | решения |
| GET | `/decisions/{decision_id}` | Запись решения | решение |
| GET | `/explanations/{decision_id}` | Объяснение решения | explanation |
| GET | `/dispatch/snapshot` | Снапшот очереди диспетчера | queue |
| GET | `/policy/{tenant_id}` | Профиль политики тенанта | policy |
| PUT | `/policy/{tenant_id}` | Обновить политику (пороги риска, требования одобрения) | policy |
| GET | `/recommendations/{tenant_id}` | Ожидающие рекомендации | list |
| GET | `/executive-kpi/{tenant_id}` | Исполнительные KPI‑сводки | kpi |

## Simulation / Prediction

| Метод | Путь |
|-------|------|
| POST | `/simulate/student-risk`, `/simulate/what-if`, `/simulate/thesis-delay`, `/simulate/faculty-overload`, `/simulate/budget-variance`, `/simulate/vendor-sla-degraded`, `/simulate/contract-risk-high`, `/simulate/supply-low` |
| POST | `/predict` (предиктивный движок), `/anomalies` (детекция аномалий) |

## Permissions
`admin.dashboard.read` (+ policy‑write требует соответствующих прав). Роли: `platform_admin`, `admin`, `executive`/`rector` (просмотр), `auditor` (read).

## Request/Response
Схемы — `brain_core/schemas.py`. Все запросы tenant‑scoped; PUT policy принимает пороги/флаги (`require_approval_for_critical` и т.п.).
