# 12 — Итоговая статистика проекта

[← 11 Background Jobs](11_BACKGROUND_JOBS.md) · [Индекс](README.md)

> Числа получены статической инспекцией кода + сверкой с системными документами. Где источники расходятся — приведены варианты. Статические подсчёты приблизительны (±), точный источник для API — OpenAPI работающего сервиса.

---

## 13.1 Сводная таблица

| Показатель | Значение | Источник / примечание |
|-----------|----------|-----------------------|
| **Модули (backend)** | **~241** (авторитетно) · ~250 директорий · 285 со скан‑подпакетами | `SBS_UB_AUTHORITATIVE_SYSTEM_EVIDENCE_INVENTORY.md` / листинг / скан |
| **Модули (frontend)** | **~81** (~85 директорий) | `frontend/modules/` |
| **Страницы (page.tsx)** | **380** (~370 под `/console`) | скан `frontend/app/**/page.tsx` |
| **Ролевые зоны** | 6: `/console(admin)`, `/student`, `/faculty`, `/registrar`, `/profile`, `/login` | `middleware.ts` |
| **API‑роутеры** | **151** (143 модульных + 8 платформенных) | `app/main.py` |
| **API endpoints (permission‑guarded)** | **685+** | `SBS_UB_PROJECT_CONTEXT_2026.md` |
| **Runtime Shells** | **7–8** | frontend + `*_runtime` роутеры |
| **Brain‑вертикали (домены)** | **6** | Student Success, Academic Operations, Reporting/Ministry, Executive Governance, Research Science, Quality Accreditation |
| **Brain: сигнальные сценарии** | **66** | `brain_core/registry.py` (SignalRegistry) |
| **Brain: решения (decisions)** | **36** | `brain_core/registry.py` (DecisionRegistry) |
| **Сигнальные реестры (L2)** | **5** | student_risk, curriculum_gap, finance_anomaly, procurement_risk, academic_quality |
| **Роли (каноничные)** | **~13** + институт‑настраиваемые | `rbac/service.py`, `permissions.py` |
| **Таблицы БД** | **~250+** | 211 EntityConfig + ORM‑специфичные |
| **EntityConfig‑сущности** | **211** | `university_core/shared.py` |
| **Сервисы (`service.py`)** | **~225** | скан модулей |
| **Модели (`models.py` модулей)** | **36** | скан модулей (SQLAlchemy ORM) |
| **Repository (`repository.py`)** | **14** | скан модулей |
| **DTO (`schemas.py` файлов)** | **~91** | скан модулей (Pydantic) |
| **Workflows (бизнес‑процессы)** | **~11 крупных** (+ workflow‑движок с определениями/версиями) | [08_WORKFLOWS.md](08_WORKFLOWS.md) |
| **Feature Flags** | динамические `(module,key)`; единого каталога ключей нет | `feature_flags/service.py` |
| **Integrations (country‑adapter)** | **10** (+4 gateway = 14 integration‑related) | `*_integration` модули |
| **Background Jobs (cron)** | **9** периодических + модульная jobs‑очередь | `platform/jobs/scheduler.py` |
| **События (event registry)** | **232** exact (+ prefix‑реестр) · 260 в историческом контексте | `platform/events/registry.py` |
| **KPI‑метрики** | **150+** ключей | `platform/kpi/service.py` |
| **Миграции (Alembic)** | **~96** | `backend/alembic/versions/` |
| **Платформенные роутеры** | **7–8** | `app/platform/router_*.py` |
| **Shared UI компоненты** | **~30** | `frontend/shared/ui/` |
| **Продуктовые вертикали** | **~20–25** (V01–V25), strict strong‑closed **9/20** | `GLOBAL-ROADMAP-R2` |

---

## 13.2 Зрелость (честный срез)

| Измерение | Состояние |
|-----------|-----------|
| Функциональное покрытие (код есть) | Высокое (~241 backend / ~81 FE модуль) |
| Runtime‑верификация (тесты в сессии инвентаря) | Низкая — полностью реверифицирован только Finance |
| Security‑верификация | Не запускалась в сессии инвентаря |
| Операционная готовность (Docker/E2E) | Не верифицирована в той сессии |
| Production‑готовность | **НЕТ** — 9/20 вертикалей, латентный тест‑долг, git не сверен |
| AI/Brain зрелость | Частичная — brain_core есть + human‑gated; кросс‑вертикальная проводка (дерево A‑055) в процессе |

Тестовая база (по `README.md`, недавняя Docker‑валидация): backend 1161 passed / 9 skipped, frontend 138 passed; lint backend/frontend — passed.

---

## 13.3 Ключевые риски целостности

1. **Незакоммиченный код:** `admissions_crm` (V12) и `innovation_commercialization` — на диске, но не в git.
2. **Дубликаты/семейства модулей** (academic_operations/runtime; accreditation×3; hr_payroll×2; student_services×2; research×3+).
3. **Интеграции — L2** (нет живых вызовов провайдеров).
4. **Планировщик** — кастомный in‑memory (нет распределённого брокера).
5. **Разночтения в документах** по счётчикам и идентичности продукта (README «шаблон» vs SBS_UB «University OS»).

---

## 13.4 Навигация по детальным каталогам

- Модули: [modules/README.md](modules/README.md)
- Страницы: [pages/README.md](pages/README.md)
- API: [api/README.md](api/README.md)
- База данных: [database/README.md](database/README.md)
- Runtime Shells: [runtime_shells/README.md](runtime_shells/README.md)
- Brain‑модули: [brains/README.md](brains/README.md)
