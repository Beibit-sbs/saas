# docs-audit — Полный архитектурный и функциональный аудит проекта

> **Статус:** Read-only аудит. В код проекта изменения НЕ вносились. Только анализ.
> **Дата аудита:** 2026-07-02
> **Метод:** статическая инспекция исходного кода (`backend/`, `frontend/`, `infra/`, миграции), плюс сверка с документами `A-050…A-056` и системными документами `SBS_UB_*`.
> **Правило приоритета:** при конфликте документа и кода — **приоритет у кода** (как зафиксировано в `SBS_UB_PROJECT_CONTEXT_2026.md`).

Проект — **мультитенантная University OS SaaS‑платформа** (внутреннее имя **SBS UB**; в UI входа — «AI University Console»; в `README.md` — шаблон «AI Engineering Center»). Ядро — доменные модули + централизованный слой принятия решений **Brain Core** + пользовательские **Runtime Shells**.

---

## Как читать эту документацию

Документация разбита на небольшие тематически связанные файлы. Начните с обзора, затем переходите к нужному разделу.

### Верхнеуровневые документы

| # | Документ | Содержание |
|---|----------|-----------|
| 00 | [00_PROJECT_OVERVIEW.md](00_PROJECT_OVERVIEW.md) | Цель проекта, бизнес‑задачи, пользователи, типы организаций, основные процессы |
| 01 | [01_SYSTEM_ARCHITECTURE.md](01_SYSTEM_ARCHITECTURE.md) | Frontend / Backend / Database / Event / Integration / Tenant / Platform архитектура, безопасность |
| 02 | [02_MODULE_DEPENDENCY_MAP.md](02_MODULE_DEPENDENCY_MAP.md) | Карта системы, центральные и зависимые модули, dependency graph |
| 03 | [03_ROLES_AND_RBAC.md](03_ROLES_AND_RBAC.md) | Полный аудит ролей, RBAC, ABAC, permissions |
| 04 | [04_DATABASE.md](04_DATABASE.md) | Аудит БД: EntityConfig‑реестр, таблицы, связи, enum, миграции |
| 05 | [05_API.md](05_API.md) | Аудит API: 151 роутер, префиксы, методы, permissions |
| 06 | [06_RUNTIME_SHELLS.md](06_RUNTIME_SHELLS.md) | Аудит Runtime Shell |
| 07 | [07_BRAIN_MODULES.md](07_BRAIN_MODULES.md) | Аудит Brain Core и доменных Brain‑модулей |
| 08 | [08_WORKFLOWS.md](08_WORKFLOWS.md) | Аудит бизнес‑процессов (workflows) |
| 09 | [09_INTEGRATIONS.md](09_INTEGRATIONS.md) | Внешние/внутренние интеграции, очереди, события |
| 10 | [10_FEATURE_FLAGS.md](10_FEATURE_FLAGS.md) | Feature flags |
| 11 | [11_BACKGROUND_JOBS.md](11_BACKGROUND_JOBS.md) | Cron, jobs, tasks, events |
| 12 | [12_PROJECT_STATISTICS.md](12_PROJECT_STATISTICS.md) | Итоговая статистика |

### Каталоги детальной документации

| Папка | Индекс | Содержание |
|-------|--------|-----------|
| [modules/](modules/) | [modules/README.md](modules/README.md) | Каталог всех ~241 backend / ~81 frontend модулей + отдельные файлы по ключевым модулям |
| [pages/](pages/) | [pages/README.md](pages/README.md) | Каталог страниц (380 `page.tsx`) и ролевых зон |
| [api/](api/) | [api/README.md](api/README.md) | Каталог API по логическим группам |
| [database/](database/) | [database/README.md](database/README.md) | Каталог таблиц по доменам |
| [runtime_shells/](runtime_shells/) | [runtime_shells/README.md](runtime_shells/README.md) | Runtime Shells по отдельности |
| [brains/](brains/) | [brains/README.md](brains/README.md) | Brain‑модули по отдельности |

---

## Ключевые характеристики проекта (кратко)

- **Стек:** FastAPI (Python 3.12) · Next.js 14.2 (App Router, React 18) · PostgreSQL · Redis · Docker Compose · Nginx.
- **Мультитенантность:** строгая (fail‑closed), tenant_id из токена; изоляция на уровне БД (`tenant_id` + частично RLS).
- **Brain Core:** автономный движок принятия решений (signal → context → classify → reason → policy → action → outcome → learning), **человеко‑контролируемый** (никаких автономных исполнений).
- **Масштаб:** ~241 backend модуль, ~81 frontend модуль, 211 EntityConfig‑сущностей, 96 миграций, 151 роутер, 685+ permission‑guarded endpoint, 380 страниц.

Полная статистика: [12_PROJECT_STATISTICS.md](12_PROJECT_STATISTICS.md).

---

## Важные оговорки об источниках и достоверности

1. **Числа могут расходиться между документами проекта.** Например, число backend‑модулей: `241` (авторитетный `SBS_UB_AUTHORITATIVE_SYSTEM_EVIDENCE_INVENTORY.md`) vs `~250` (листинг директорий) vs `285` (скан с под‑пакетами). Приведены оба варианта, где это существенно.
2. **Идентичность продукта противоречива:** `README.md` описывает репозиторий как доменно‑нейтральный «шаблон платформы», тогда как `SBS_UB_*` — как университетскую платформу. Оба варианта отражены в [00_PROJECT_OVERVIEW.md](00_PROJECT_OVERVIEW.md).
3. **Зрелость ≠ покрытие.** Код присутствует широко, но «strict strong‑closed» верификация — 9/20 вертикалей (по `GLOBAL-ROADMAP-R2`). Раздел проблем в каждом модуле это отмечает.
4. Где информация отсутствует или не выводима из структуры — это указано явно.
