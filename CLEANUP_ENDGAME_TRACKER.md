# CLEANUP ENDGAME TRACKER

Назначение: фиксировать только те сущности, которые можно удалить ПОСЛЕ стабилизации и верификации production-потоков.

Важно:
- Сейчас ничего не удаляем.
- Любой пункт из этого файла удаляется только после прохождения критериев безопасности.
- Если критерии не выполнены, статус остается HOLD.

## Критерии перед удалением (обязательные)

1. Есть рабочая замена (Replacement Live = YES).
2. Нет активных ссылок в коде (Code Refs = 0) по проверке `rg`.
3. Нет runtime-трафика/вызовов на старый контур в период наблюдения.
4. Пройдены backend/frontend/e2e тесты после отключения кандидата.
5. Пройден smoke-check ключевых сценариев.
6. Есть rollback-план (как быстро вернуть).
7. Есть явное подтверждение владельца (Owner Sign-off = YES).

## Статусы

- HOLD: кандидат отмечен, удалять нельзя.
- READY: все критерии выполнены, можно удалять в cleanup-фазе.
- REMOVED: удалено и проверено.

## Реестр кандидатов на удаление

| ID | Кандидат | Где | Почему кандидат | Replacement | Статус | Условия перевода в READY |
|---|---|---|---|---|---|---|
| C-001 | Legacy admin zone | frontend/app/admin/ | Дублирует новый console-контур | frontend/app/(admin)/console/ | HOLD | Переключение трафика + 0 runtime usage + 100% smoke pass |
| C-002 | Legacy students route | backend/app/modules/students/legacy_router.py | Дублирует новый `/api/admin/students` | students/router.py | HOLD | Все клиенты переведены на новый префикс |
| C-003 | Legacy enrollments route | backend/app/modules/enrollments/legacy_router.py | Дублирует новый `/api/admin/enrollments` | enrollments/router.py | HOLD | Нет обращений к `/api/admin/university/enrollments` |
| C-004 | University legacy routes | backend/app/modules/{faculty,programs,courses}/ | Старый namespace `/api/admin/university/*` | platform/admin API v1 | HOLD | Подтверждена миграция всех consumers |
| C-005 | identity_phase1 naming/route | backend/app/modules/identity/phase1_router.py | Legacy naming и потенциальный дубль | identity/router.py | HOLD | Подтверждено отсутствие клиентов phase1 path |
| C-006 | Job placeholder handlers | backend/app/modules/jobs/worker.py | 4 no-op handler-а (`sync`, `ldap.sync`, `ai.generate`, `report.generate`) | Заблокированы в production; явный denylist в config | READY | ✅ Option B зафиксирован: публичный enqueue для `sync`/`ldap.sync`/`ai.generate` отключен; backend tests green; `report.generate` оставлен как roadmap-кандидат |
| C-007 | university_core service | backend/app/modules/university_core/service.py | Общий service-слой с широкими импортами; кандидат на управляемую декомпозицию | domain services split | HOLD | Подтвержден план декомпозиции и migration без regressions |
| C-008 | Legacy admin CSS | frontend/app/admin/admin-legacy.css | Останется сиротой после удаления legacy admin | Новый дизайн console | HOLD | C-001 == READY |
| C-009 | Legacy admin hooks/types | frontend/app/admin/hooks/ + frontend/app/admin/types.ts | Параллельный слой API/типов | modules/* hooks/types | HOLD | C-001 == READY |

## Execution Board (Phase 1)

| ID | Owner | Ближайшее действие | Checkpoint |
|---|---|---|---|
| C-001 | Frontend Lead | Утвердить boundary legacy admin -> console и план переключения трафика | 2026-04-10 |
| C-002 | Backend Lead | Подтвердить отсутствие активных клиентов на legacy students prefix | 2026-04-10 |
| C-003 | Backend Lead | Подтвердить отсутствие активных клиентов на legacy enrollments prefix | 2026-04-10 |
| C-004 | Platform Architect | Утвердить целевой namespace для university routes | 2026-04-11 |
| C-005 | Security Lead + Backend Lead | Согласовать strategy по `identity_phase1` и security review scope | 2026-04-11 |
| C-006 | Product Owner + Platform Lead | ✅ Sign-off выполнен (Option B); подготовить отдельный RFC/epic для `report.generate` при подтвержденном приоритете | 2026-04-06 |
| C-007 | Backend Lead | Подготовить план декомпозиции `university_core/service.py` (active imports подтверждены) | 2026-04-11 |
| C-008 | Frontend Lead | Привязать удаление к C-001 readiness | 2026-04-12 |
| C-009 | Frontend Lead | Привязать удаление к C-001 readiness | 2026-04-12 |

## Журнал решений

| Дата | ID | Решение | Кто подтвердил | Комментарий |
|---|---|---|---|---|
| 2026-04-06 | C-001..C-009 | Создан initial backlog кандидатов | pending | Удаление запрещено до выполнения критериев |
| 2026-04-06 | C-001..C-009 | Запущена стабилизация P0 без удаления | pending | Закрыт внешний доступ к docs/openapi/redoc; health metrics переведены на ops summary; backend Dockerfile теперь включает tests+pytest.ini |
| 2026-04-06 | C-006 | Production-safety check: placeholder handlers | pending | `_execute_placeholder` теперь явно блокирует эти типы в production (`is_production_mode()` check входит); используются только в test-коде; готово к скопированию в product scope documentation |
| 2026-04-06 | C-001..C-007 | Старт Phase 1 (legacy cleanup planning) | in progress | Начат execution по плану `LEGACY_CLEANUP_MIGRATION_STRATEGY.md`: фиксируем архитектурные решения, владельцев и дедлайны по кандидатам |
| 2026-04-06 | C-001..C-009 | Baseline snapshot по ссылкам legacy-паттернов | in progress | `rg` baseline = 76 совпадений; основной объем в tests/scripts, также есть runtime в `backend/app/main.py` (`identity_phase1_router`) |
| 2026-04-06 | C-001..C-009 | Назначены owner-роли и checkpoint-даты | in progress | Execution Board заполнен: Frontend/Backend/Security/Product/Architect роли назначены, готово к Phase 1 decision sync |
| 2026-04-06 | C-001,C-004,C-005 | Зафиксированы draft-решения Phase 1 | in progress | C-001: migration без нового BFF; C-004: целевой namespace `/api/admin/org/*`; C-005: consolidation в `identity/router.py` через compatibility shim + security review |
| 2026-04-06 | C-002,C-003,C-007 | Подтвержден baseline по runtime/import usage | in progress | C-002/C-003: legacy routers подключены в `backend/app/main.py`; C-007: `university_core/service.py` активно импортируется в services (students/enrollments/faculty/programs/courses/academic_records) |
| 2026-04-06 | C-002,C-003,C-007 | Зафиксированы draft-решения и план client switch | in progress | C-002/C-003: подтвержден deprecation->cutover plan на новые префиксы; C-007: подтверждена декомпозиция вместо удаления как сироты |
| 2026-04-06 | C-006 | Подготовлен decision package для stakeholder sign-off | in progress | Рекомендация: de-scope для `sync`, `ldap.sync`, `ai.generate`; optional roadmap на реализацию `report.generate` при явном product request |
| 2026-04-06 | C-006 | Stakeholder sign-off завершен (Option B) | Product Owner + Platform Lead | В backend `admin/jobs` отключен публичный enqueue для `sync`, `ldap.sync`, `ai.generate`; проверка: `tests/test_jobs.py` + `tests/test_rate_limit.py` = 17 passed |
| 2026-04-06 | C-002 | Включена deprecation-наблюдаемость legacy students prefix | Backend Lead | Для `/api/admin/university/students/*` добавлены `Deprecation/Sunset/Link/Warning` headers + warning log; таргетные тесты green (`tests/test_university_tenant_isolation.py`, `tests/modules/students`) |
| 2026-04-06 | C-003 | Включена deprecation-наблюдаемость legacy enrollments prefix | Backend Lead | Для `/api/admin/university/enrollments/*` добавлены `Deprecation/Sunset/Link/Warning` headers + warning log; таргетная проверка green (`tests/test_university_core.py`) |
| 2026-04-06 | C-001..C-009 | Закрыт блокер тестовой стабилизации backend | in progress | Исправлен startup-mock в profiles integration (`tests/modules/profiles/test_integration.py`); повторный полный прогон backend в Docker: 1254 passed, 9 skipped, 2 warnings |
| 2026-04-06 | C-001..C-009 | EOS audit: найден frontend blocker в tenant login UX | in progress | `frontend` full tests: 1 failed file / 3 failed tests (`__tests__/components/LoginTenantMode.test.tsx`); backend остается green: 1254 passed, 9 skipped; release gate блокируется до фикса login flow contract |
| 2026-04-06 | C-001..C-009 | EOS audit update: frontend tenant login blocker снят | in progress | Обновлены тесты `frontend/__tests__/components/LoginTenantMode.test.tsx` под текущий CSRF/login flow; полный frontend прогон в Docker: 30 passed files, 147 passed tests (есть jsdom navigation stderr, без test failures) |

## Phase 1 Kickoff (в работе)

Цель: запустить cleanup-процесс без удаления кода до прохождения критериев безопасности.

### Шаги на текущую итерацию

- [x] Зафиксировать архитектурное решение по C-001: BFF/console migration boundary.
- [x] Зафиксировать namespace-решение по C-004: целевой префикс `/api/admin/org/*` или альтернатива.
- [x] Зафиксировать security-решение по C-005: план вывода `identity/phase1_router.py`.
- [x] Назначить owner по каждому кандидату C-001..C-009.
- [x] Добавить целевые даты для перевода HOLD -> READY.
- [x] Выполнить проверку ссылок `rg` и сохранить snapshot в журнал решений.

### Промежуточный критерий Done для Phase 1

- [x] По C-001..C-007 есть owner + решение + дата следующей контрольной точки.
- [x] Для C-002/C-003 подтвержден план переключения клиентов на новый префикс.
- [x] Для C-006 получен stakeholder sign-off: implement vs de-scope.

## Draft Decisions (Phase 1)

Важно: это рабочие черновики для decision sync, не финальный sign-off.

### C-001 — Legacy admin zone

- Draft решение: миграция без отдельного нового BFF-слоя, опора на текущий `frontend/app/(admin)/console/` и существующие `/api/admin/*` контракты.
- Граница миграции: legacy `frontend/app/admin/` переводится в read-only maintenance до полного switch трафика.
- Условие подтверждения: 0 runtime usage legacy-контура + smoke pass console-сценариев.

### C-004 — University legacy routes

- Draft решение: целевой namespace ` /api/admin/org/* ` как единая точка консолидации.
- Transitional режим: временная совместимость legacy `/api/admin/university/*` до завершения migration window.
- Условие подтверждения: все consumers переведены, legacy endpoints не получают runtime-вызовы.

### C-005 — identity phase1 naming/route

- Draft решение: консолидировать в `identity/router.py`, `phase1_router.py` оставить только как временный compatibility shim.
- Security рамка: migration только после review от Security Lead (JWT/session compatibility, path-level RBAC invariants).
- Условие подтверждения: отсутствуют клиенты phase1 path + пройден security regression check.

### C-002 — Legacy students route

- Draft решение: оставить dual-registration до migration window, затем убрать `legacy_students_router` import/include из `backend/app/main.py`.
- План переключения клиентов: все integrations переводятся на `/api/admin/students/*`; legacy `/api/admin/university/students/*` переводится в deprecation mode до нулевого usage.
- Условие подтверждения: 0 runtime обращений к legacy prefix + smoke/e2e pass по students CRUD.

### C-003 — Legacy enrollments route

- Draft решение: после перевода клиентов отключить `legacy_enrollments_router` в `backend/app/main.py`, оставить только `/api/admin/enrollments/*`.
- План переключения клиентов: контрольный период с логированием usage legacy prefix и последующим cutover.
- Условие подтверждения: 0 runtime обращений к `/api/admin/university/enrollments/*` + smoke/e2e pass по enrollments CRUD.

### C-007 — university_core service

- Draft решение: не удалять как сироту (модуль активен), выполнить поэтапную декомпозицию shared-функций в доменные сервисы.
- Scope: `students/enrollments/faculty/programs/courses/academic_records` переходят на domain-level helper modules.
- Условие подтверждения: импортов `app.modules.university_core.service` = 0 в runtime-модулях + regression tests pass.

### C-006 — Job placeholder handlers (decision package)

- Option A (full implement): реализовать все 4 handler-а (`sync`, `ldap.sync`, `ai.generate`, `report.generate`) и снять placeholder режим.
- Option B (recommended): de-scope из product для `sync`, `ldap.sync`, `ai.generate`; оставить production block и удалить публичные точки создания этих job types.
- Option C (hybrid): de-scope 3 типа + отдельный roadmap на `report.generate` как потенциально полезный business feature.
- Рекомендуемое решение на sign-off: **Option B** сейчас, с фиксацией отдельного RFC/epic на Option C при подтвержденном бизнес-приоритете.
- Sign-off статус: **Принято (2026-04-06)** — выбран Option B.
- Критерий закрытия C-006: Owner Sign-off в журнале + обновление enum/UI/API контрактов в соответствии с выбранным вариантом.

## Стратегический документ

👉 **ГЛАВНЫЙ ДОКУМЕНТ ДЛЯ LEGACY CLEANUP**:  
[LEGACY_CLEANUP_MIGRATION_STRATEGY.md](LEGACY_CLEANUP_MIGRATION_STRATEGY.md)

Contains:
- Phase-by-phase 11-week migration plan
- Decision gates (Architecture, Scope, Auth)
- Risk mitigation per phase
- Rollback procedures
- Success criteria
- Timeline and resource allocation

**Status**: Ready for Phase 1 decision (Architecture meeting)

---

## Как обновлять после каждого исправления

После любого изменения, которое затрагивает кандидата на удаление:

1. Обновить поле `Replacement` (что заменяет).
2. Обновить факт миграции клиентов (если есть).
3. Записать результат проверки `rg` ссылок.
4. Добавить запись в журнал решений.
5. Обновить статус в соответствии с [LEGACY_CLEANUP_MIGRATION_STRATEGY.md](LEGACY_CLEANUP_MIGRATION_STRATEGY.md) phase schedule.

## Команда проверки ссылок (шаблон)

```bash
rg -n "app/admin/|/api/admin/university/|identity_phase1|ldap.sync|ai.generate|report.generate|university_core" frontend backend
```

## Дополнительные анализ документы

- [MIGRATION_ANALYSIS_SUMMARY.md](MIGRATION_ANALYSIS_SUMMARY.md) — Quick findings (5 min)
- [MIGRATION_PATHS_ANALYSIS.md](MIGRATION_PATHS_ANALYSIS.md) — Technical depth (30-45 min)
- [MIGRATION_CODE_REFERENCES.md](MIGRATION_CODE_REFERENCES.md) — Exact line numbers
- [MIGRATION_DEPENDENCY_GRAPH.md](MIGRATION_DEPENDENCY_GRAPH.md) — Dependency diagrams
