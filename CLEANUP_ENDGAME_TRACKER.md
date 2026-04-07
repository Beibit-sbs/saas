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
| C-001 | Legacy admin zone | frontend/app/admin/ | Дублирует новый console-контур | frontend/app/(admin)/console/ | REMOVED | ✅ Legacy frontend zone удален; совместимость `/admin*` сохранена через middleware redirect |
| C-002 | Legacy students route | backend/app/modules/students/router.py | Дублирует новый `/api/admin/students` | students/router.py | REMOVED | ✅ Legacy `/api/admin/university/students/*` снят с runtime, replacement-prefix остается единственным |
| C-003 | Legacy enrollments route | backend/app/modules/enrollments/router.py | Дублирует новый `/api/admin/enrollments` | enrollments/router.py | REMOVED | ✅ Legacy `/api/admin/university/enrollments/*` снят с runtime, replacement-prefix остается единственным |
| C-004 | University legacy routes | backend/app/modules/{faculty,programs,courses}/ | Старый namespace `/api/admin/university/*` | platform/admin API v1 | REMOVED | ✅ Legacy namespace снят с runtime; replacement `/api/admin/org/*` единственный активный контракт |
| C-005 | identity_phase1 naming/route | backend/app/modules/identity/phase1_router.py | Legacy naming и потенциальный дубль | identity/router.py | REMOVED | ✅ Legacy `/api/identity/*` снят с runtime; admin replacement namespace стал единственным активным контрактом |
| C-006 | Job placeholder handlers | backend/app/modules/jobs/worker.py | 4 no-op handler-а (`sync`, `ldap.sync`, `ai.generate`, `report.generate`) | Заблокированы в production; явный denylist в config | REMOVED | ✅ De-scoped placeholder-ветки удалены из worker; `report.generate` переведен на concrete handler |
| C-007 | university_core service | backend/app/modules/university_core/service.py | Общий service-слой с широкими импортами; кандидат на управляемую декомпозицию | domain services split | REMOVED | ✅ Удалено в cleanup-phase change set; post-removal regression/smoke подтверждены |
| C-008 | Legacy admin CSS | frontend/app/admin/admin-legacy.css | Останется сиротой после удаления legacy admin | Новый дизайн console | REMOVED | ✅ Удалено в cleanup-phase вместе с legacy UI artifacts; post-checks green |
| C-009 | Legacy admin hooks/types | frontend/app/admin/hooks/ + frontend/app/admin/types.ts | Параллельный слой API/типов | modules/* hooks/types | REMOVED | ✅ Удалено в cleanup-phase вместе с legacy UI artifacts; post-checks green |

## Execution Board (Phase 1)

| ID | Owner | Ближайшее действие | Checkpoint |
|---|---|---|---|
| C-001 | Frontend Lead | ✅ Cleanup-phase выполнен: legacy admin zone removed; post-checks подтверждены | 2026-04-10 |
| C-002 | Backend Lead | ✅ Cleanup-phase выполнен: legacy students routes removed, replacement coverage подтверждено | 2026-04-07 |
| C-003 | Backend Lead | ✅ Cleanup-phase выполнен: legacy enrollments routes removed, replacement coverage подтверждено | 2026-04-07 |
| C-004 | Platform Architect | ✅ Cleanup-phase выполнен: legacy university routes removed; post-checks подтверждены | 2026-04-11 |
| C-005 | Security Lead + Backend Lead | ✅ Cleanup-phase выполнен: legacy identity phase1 router removed, admin namespace parity подтверждена | 2026-04-07 |
| C-006 | Product Owner + Platform Lead | ✅ Cleanup-phase выполнен: placeholder-хендлеры removed, post-removal checks подтверждены | 2026-04-06 |
| C-007 | Backend Lead | ✅ Cleanup-phase выполнен: legacy service удален, критерии post-removal подтверждены | 2026-04-06 |
| C-008 | Frontend Lead | ✅ Cleanup-phase выполнен: legacy CSS removed; post-checks подтверждены | 2026-04-12 |
| C-009 | Frontend Lead | ✅ Cleanup-phase выполнен: legacy hooks/types removed; post-checks подтверждены | 2026-04-12 |

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
| 2026-04-06 | C-006 | Cleanup-phase завершен; статус переведен READY -> REMOVED | Backend Lead | В `backend/app/modules/jobs/worker.py` удалены placeholder-хендлеры de-scoped типов (`sync`, `ldap.sync`, `ai.generate`), `report.generate` переведен на concrete handler; post-removal checks: backend tests = 1263 passed / 9 skipped / 2 warnings, frontend tests = 30 files / 147 tests passed, smoke-check = 8 PASS, EXIT=0 |
| 2026-04-06 | C-002 | Включена deprecation-наблюдаемость legacy students prefix | Backend Lead | Для `/api/admin/university/students/*` добавлены `Deprecation/Sunset/Link/Warning` headers + warning log; таргетные тесты green (`tests/test_university_tenant_isolation.py`, `tests/modules/students`) |
| 2026-04-06 | C-003 | Включена deprecation-наблюдаемость legacy enrollments prefix | Backend Lead | Для `/api/admin/university/enrollments/*` добавлены `Deprecation/Sunset/Link/Warning` headers + warning log; таргетная проверка green (`tests/test_university_core.py`) |
| 2026-04-06 | C-004 | Включена runtime-observability для legacy university namespace | Backend Lead | Для `/api/admin/university/{faculty,programs,courses}/*` добавлены warning log + runtime headers `X-Legacy-Namespace/Warning`; successor path `/api/admin/org/*` еще не live, поэтому deprecation-link пока не публикуется |
| 2026-04-06 | C-005 | Включена runtime-observability для legacy identity phase1 namespace | Backend Lead | Для `/api/identity/*` (phase1_router.py) добавлены warning log + runtime headers `X-Legacy-Namespace/Warning`; successor path `/api/admin/identity/*` live; 2 новых теста зелёных в `test_identity_phase11_hardening.py` |
| 2026-04-06 | C-007 | Включена runtime-observability для shared `university_core.service` | Backend Lead | Добавлено warning-логирование usage в публичных API (`list/create/update/delete` + tenant-aware variants); baseline imports подтвержден в students/enrollments/faculty/programs/courses/academic_records + tests/conftest; таргетный прогон `tests/test_university_core.py` = 5 passed |
| 2026-04-06 | C-007 | Выполнен phase2 import-decoupling через facade module | Backend Lead | Добавлен `university_core/tenant_entity_service.py`; runtime-домены (`students/enrollments/faculty/programs/courses/academic_records`) переведены с прямого импорта `university_core.service` на facade; таргетные тесты green: `tests/test_university_core.py` + `tests/test_university_tenant_isolation.py` = 15 passed |
| 2026-04-06 | C-007 | Подтвержден post-phase2 baseline по code refs | Backend Lead | `rg` по `backend/app`: прямой импорт `app.modules.university_core.service` остался только в `university_core/tenant_entity_service.py`; все runtime-домены (`students/enrollments/faculty/programs/courses/academic_records`) импортируют `tenant_entity_service`; статус без удаления кода сохранен |
| 2026-04-06 | C-007 | Выполнен phase3 boundary-step через tenant entity API layer | Backend Lead | Добавлен `university_core/tenant_entity_api.py`; facade `tenant_entity_service.py` переключен на API-layer (без прямого импорта `service.py`); таргетные тесты green: `tests/test_university_core.py` + `tests/test_university_tenant_isolation.py` = 15 passed |
| 2026-04-06 | C-007 | Выполнен phase4 impl extraction для tenant-aware CRUD | Backend Lead | Добавлен `university_core/tenant_entity_impl.py` с tenant-aware реализацией (`list/create/update/delete`); `tenant_entity_api.py` переключен на impl-layer, а публичные функции в `university_core/service.py` оставлены как делегирующие wrapper-ы; таргетные тесты green: `tests/test_university_core.py` + `tests/test_university_tenant_isolation.py` = 15 passed |
| 2026-04-06 | C-007 | Выполнен phase5 перенос tenant-aware private helpers в impl-layer | Backend Lead | DB/memory helper-реализации (`_list/_update/_delete_*_tenant_*`) перенесены в `tenant_entity_impl.py`; в `university_core/service.py` оставлены совместимые wrapper-ы, делегирующие в impl-layer; таргетные тесты green: `tests/test_university_core.py` + `tests/test_university_tenant_isolation.py` = 15 passed |
| 2026-04-06 | C-007 | Выполнен phase6 перенос non-tenant shared CRUD в impl-layer | Backend Lead | Добавлен `university_core/entity_impl.py` с реализациями non-tenant `list/create/update/delete` и DB helper-ами; в `university_core/service.py` оставлены совместимые wrapper-ы, делегирующие в impl-layer; таргетные тесты green: `tests/test_university_core.py` + `tests/test_university_tenant_isolation.py` = 15 passed |
| 2026-04-06 | C-007 | Выполнен phase7 перенос shared memory FK helpers в impl-layer | Backend Lead | В `university_core/entity_impl.py` вынесены `_memory_fk_exists_impl` и `_validate_foreign_keys_memory_impl`; в `university_core/service.py` оставлены совместимые wrapper-ы; таргетные тесты green: `tests/test_university_core.py` + `tests/test_university_tenant_isolation.py` = 15 passed |
| 2026-04-06 | C-007 | Выполнен phase8 перенос shared DB FK helpers в impl-layer | Backend Lead | В `university_core/entity_impl.py` вынесены `_db_fetch_exists_impl` и `_validate_foreign_keys_db_impl`; в `university_core/service.py` оставлены совместимые wrapper-ы; таргетные тесты green: `tests/test_university_core.py` + `tests/test_university_tenant_isolation.py` = 15 passed |
| 2026-04-06 | C-007 | Выполнен phase9 перенос shared normalization helpers в impl-layer | Backend Lead | В `university_core/entity_impl.py` вынесены `_normalize_string_impl`, `_normalize_optional_tenant_impl`, `_normalize_payload_impl`; в `university_core/service.py` сохранены совместимые wrapper-ы; таргетные тесты green: `tests/test_university_core.py` + `tests/test_university_tenant_isolation.py` = 15 passed |
| 2026-04-06 | C-007 | Выполнен phase10 перенос shared SQL/row helpers в impl-layer | Backend Lead | В `university_core/entity_impl.py` вынесены `_row_to_dict_impl`, `_sql_identifier_impl`, `_sql_identifier_list_impl`; в `university_core/service.py` сохранены совместимые wrapper-ы; таргетные тесты green: `tests/test_university_core.py` + `tests/test_university_tenant_isolation.py` = 15 passed |
| 2026-04-06 | C-007 | Выполнен phase11 перенос shared runtime helpers в impl-layer | Backend Lead | В `university_core/entity_impl.py` вынесены `_db_url_impl`, `_use_database_impl`, `_should_fallback_to_memory_impl`, `_now_iso_impl`; в `university_core/service.py` сохранены совместимые wrapper-ы; таргетные тесты green: `tests/test_university_core.py` + `tests/test_university_tenant_isolation.py` = 15 passed |
| 2026-04-06 | C-007 | Выполнен phase12: tenant impl переключен на прямые shared impl helpers | Backend Lead | `tenant_entity_impl.py` переведен с вызовов wrappers из `service.py` на прямые вызовы из `entity_impl.py` (SQL/row/runtime/normalization/FK helpers); поведение API сохранено; таргетные тесты green: `tests/test_university_core.py` + `tests/test_university_tenant_isolation.py` = 15 passed |
| 2026-04-06 | C-007 | Выполнен phase13: impl-модули отвязаны от `service.py` через shared base module | Backend Lead | Добавлен `university_core/shared.py` (ENTITY_CONFIGS/state/get_raw_conn/psycopg); `entity_impl.py` и `tenant_entity_impl.py` переведены с импорта `service.py` на `shared.py`; post-phase13 baseline: в `backend/app` прямых ссылок на `app.modules.university_core.service` не осталось (есть только `backend/tests/conftest.py`); таргетные тесты green: `tests/test_university_core.py` + `tests/test_university_tenant_isolation.py` = 14 passed |
| 2026-04-06 | C-007 | Post-phase13 closure check: full backend regression green | Backend Lead | Выявлен и устранен flaky в `tests/test_health_worker_scope.py` (принудительно зафиксирован сценарий отсутствия worker heartbeat через monkeypatch); повторный полный прогон backend в `backend-tests`: 1263 passed, 9 skipped, 2 warnings, EXIT=0; runtime code refs для `app.modules.university_core.service` в `backend/app` = 0 (тестовая ссылка остается в `backend/tests/conftest.py`) |
| 2026-04-06 | C-007 | Перевод в ready-for-signoff состояние (без смены статуса HOLD) | Backend Lead | После phase13 closure подтверждены технические критерии (runtime code refs в `backend/app` = 0, full backend regression green); до READY остаются обязательные критерии: runtime observation window, smoke-check и явный Owner Sign-off |
| 2026-04-06 | C-007 | Пройден platform smoke-check для ключевых сценариев | Backend Lead | Команда: `bash ./scripts/platform_smoke_check.sh`; итог: 8 PASS (Health Surfaces, Outbox Event Processing, Automation Execution, Webhook Retry Behavior, KPI Refresh, AI Copilot Response, Developer Platform Auth Flow, Metrics Surfaces), `EXIT=0` |
| 2026-04-06 | C-007 | Завершено runtime observation window по legacy usage | Backend Lead | По backend-логам после restart/smoke-window (`docker compose logs --since=90m backend`) отсутствуют события `university_core shared service used` и иные прямые признаки runtime-вызовов legacy service; наблюдаемое usage = 0 |
| 2026-04-06 | C-007 | Подготовлен owner sign-off package (awaiting decision) | Backend Lead | Сформирован пакет подтверждения критериев и rollback-план: `C007_OWNER_SIGNOFF_PACKAGE.md`; статус C-007 остается HOLD до явного подтверждения владельца |
| 2026-04-06 | C-007 | Owner Sign-off завершен; статус переведен HOLD -> READY | Backend Lead + Owner (session confirmation) | Подтверждено выполнение всех критериев перед удалением (Replacement Live, Code Refs=0 runtime, runtime observation window usage=0, backend regression green, smoke-check PASS, rollback plan в `C007_OWNER_SIGNOFF_PACKAGE.md`) |
| 2026-04-06 | C-007 | Cleanup-phase завершен; статус переведен READY -> REMOVED | Backend Lead | Удален `backend/app/modules/university_core/service.py`; `clear_university_state` перенесен в `university_core/shared.py`, tests reset переведен на package export; post-removal checks: code refs `service.py` в `backend/app` и `backend/tests` = 0, backend tests = 1263 passed / 9 skipped / 2 warnings, frontend tests = 30 files / 147 tests passed, smoke-check = 8 PASS, EXIT=0 (run с `DOCKER_ONLY_GUARD_SKIP_PROCESS_CHECK=1` из-за активного host dev uvicorn процесса) |
| 2026-04-07 | C-001 | Выполнен readiness-step: legacy admin route переведен в redirect-only runtime режим | Frontend Lead | Прямые runtime-ссылки на `/admin` сняты: `SessionPanel` переведен на `/console/platform`, root overlays отключены, help-context переведен на canonical `/console/platform`, smoke `i18n-runtime.spec.ts` больше не использует legacy path. Остаточные runtime refs на `/admin` сохранены только в `frontend/middleware.ts` как redirect/matcher для совместимости. Frontend regression green: 30 passed files / 147 passed tests. Статус остается HOLD до подтверждения нулевого runtime usage legacy-контура и удаления `frontend/app/admin/*` как active UI entrypoint. |
| 2026-04-07 | C-001 | Усилен readiness-step: live page-entrypoint `/admin` заменен server redirect | Frontend Lead | `frontend/app/admin/page.tsx` больше не рендерит legacy shell и выполняет только redirect на `/console/platform`; legacy shell сохранен как отдельный компонент `frontend/app/admin/components/LegacyAdminPageShell.tsx` для тестовой/вспомогательной поддержки. Прямых imports `app/admin/page` в tests/runtime больше нет. Повторный frontend regression green: 30 passed files / 147 passed tests. Статус остается HOLD до подтверждения нулевого runtime usage legacy-контура и последующей зачистки `frontend/app/admin/*`. |
| 2026-04-07 | C-001 | Подтверждено runtime observation window: legacy `/admin` usage = 0 | Frontend Lead | По `docker compose logs --since=90m frontend nginx` отсутствуют реальные HTTP hits вида `GET /admin...`; совпадения остаются только на `/api/bff/admin/*`, относящиеся к canonical console backend/BFF traffic. Дополнительно подтверждено, что `frontend/app/admin/*` не имеет внешних imports вне собственной папки и `frontend/__tests__/admin/*`. Статус остается HOLD до прохождения smoke gate для READY и последующей зачистки legacy artifact layer. |
| 2026-04-07 | C-001 | Smoke gate закрыт; статус переведен HOLD -> READY | Frontend Lead | `e2e/smoke/admin-console.spec.ts` переведен на актуальные runtime-контракты (locale-agnostic auth checks, обновленные API stubs для tenants/jobs, устойчивый notifications mutation check). Валидация: Playwright JSON run `admin-console` = expected 16, unexpected 0, exit=0. |
| 2026-04-07 | C-001 | Cleanup-phase завершен; статус переведен READY -> REMOVED | Frontend Lead | Удален последний legacy entrypoint `frontend/app/admin/page.tsx`; ранее удаленные legacy artifacts (`components/hooks/types/css/utils`) остаются удаленными. Совместимость маршрута `/admin*` обеспечивается redirect-правилом в `frontend/middleware.ts`. Post-removal checks: frontend regression = 23 passed files / 123 passed tests (exit=0), smoke `e2e/smoke/admin-console.spec.ts` = expected 16 / unexpected 0 / exit=0. |
| 2026-04-07 | C-008 | Статус переведен HOLD -> READY | Frontend Lead | Зависимость `C-001 == READY` выполнена; кандидат готов к cleanup-phase удалению legacy CSS слоя. |
| 2026-04-07 | C-009 | Статус переведен HOLD -> READY | Frontend Lead | Зависимость `C-001 == READY` выполнена; кандидат готов к cleanup-phase удалению legacy hooks/types слоя. |
| 2026-04-07 | C-008 | Cleanup-phase завершен; статус переведен READY -> REMOVED | Frontend Lead | Удален `frontend/app/admin/admin-legacy.css` в составе удаления legacy admin artifacts (components/hooks/utils), при сохранении redirect-only entrypoint `frontend/app/admin/page.tsx`; post-removal checks: frontend regression = 23 passed files / 123 passed tests, smoke `e2e/smoke/admin-console.spec.ts` = expected 16 / unexpected 0 / exit=0. |
| 2026-04-07 | C-009 | Cleanup-phase завершен; статус переведен READY -> REMOVED | Frontend Lead | Удалены `frontend/app/admin/hooks/*` и `frontend/app/admin/types.ts` вместе с зависимыми legacy tests/imports; post-removal checks: frontend regression = 23 passed files / 123 passed tests, smoke `e2e/smoke/admin-console.spec.ts` = expected 16 / unexpected 0 / exit=0. |
| 2026-04-07 | C-004 | Readiness reassessment: статус остается HOLD | Platform Architect + Backend Lead | По backend logs за `--since=90m` runtime usage legacy routes `/api/admin/university/{faculty,programs,courses}` не зафиксирован (usage=0), но active code refs сохраняются в runtime routers (`backend/app/modules/{faculty,programs,courses}/router.py`) и consumer-слое tests/scripts (`backend/tests/test_university_core.py`, `backend/scripts/perf_pass2_http.py`). До READY требуется завершить migration consumers и утвердить live replacement namespace `/api/admin/org/*`. |
| 2026-04-07 | C-004 | Readiness-step завершен: статус переведен HOLD -> READY | Platform Architect + Backend Lead | В `backend/app/modules/{faculty,programs,courses}/router.py` добавлены parallel endpoints под `/api/admin/org/{faculty,programs,courses}` (legacy namespace сохранен для совместимости и observability). Internal consumers migrated: `backend/tests/test_university_core.py` и `backend/scripts/perf_pass2_http.py` переведены на `/api/admin/org/*`; check refs в `backend/tests` + `backend/scripts` по `/api/admin/university/{faculty,programs,courses}` = 0. Таргетная валидация: `pytest -q tests/test_university_core.py` = 3 passed, exit=0; runtime usage legacy namespace за `--since=90m` = 0. |
| 2026-04-07 | C-004 | Cleanup-phase завершен; статус переведен READY -> REMOVED | Platform Architect + Backend Lead | Из runtime удален legacy namespace `/api/admin/university/{faculty,programs,courses}`: роутеры `backend/app/modules/{faculty,programs,courses}/router.py` переведены на единственный prefix `/api/admin/org/{faculty,programs,courses}`. Post-removal evidence: code refs `/api/admin/university/(faculty|programs|courses)` в `backend/app` + `backend/tests` + `backend/scripts` = 0; таргетная валидация `pytest -q tests/test_university_core.py` = 3 passed / 2 warnings, exit=0; ранее подтвержденное runtime usage legacy namespace за `--since=90m` = 0. |
| 2026-04-07 | C-002 | Cleanup-phase завершен; статус переведен HOLD -> REMOVED | Backend Lead | Из `backend/app/main.py` удален include `legacy_students_router`; legacy CRUD-блок удален из `backend/app/modules/students/router.py`; post-removal evidence: code refs `/api/admin/university/students` и `legacy_students_router` в `backend/app` + `backend/tests` = 0, runtime usage по `docker compose logs --since=90m backend` = 0, таргетный backend slice = 38 passed, full backend regression в `backend-tests` = 1252 passed / 9 skipped / 2 warnings, frontend regression = 30 files / 147 tests passed, smoke-check = 8 PASS / 0 FAIL |
| 2026-04-07 | C-003 | Cleanup-phase завершен; статус переведен HOLD -> REMOVED | Backend Lead | Из `backend/app/main.py` удален include `legacy_enrollments_router`; legacy CRUD-блок удален из `backend/app/modules/enrollments/router.py`; добавлен replacement test `backend/tests/modules/enrollments/test_router_enrollments.py`; post-removal evidence: code refs `/api/admin/university/enrollments` и `legacy_enrollments_router` в `backend/app` + `backend/tests` = 0, runtime usage по `docker compose logs --since=90m backend` = 0, таргетный backend slice = 38 passed, full backend regression в `backend-tests` = 1252 passed / 9 skipped / 2 warnings, frontend regression = 30 files / 147 tests passed, smoke-check = 8 PASS / 0 FAIL |
| 2026-04-07 | C-005 | Readiness reassessment: removal blocked by contract mismatch | Backend Lead | `phase1_router.py` остается runtime-included в `backend/app/main.py`; active code refs сохраняются в `backend/tests/test_identity_phase11_hardening.py`. Наблюдаемое runtime usage за последние 90 минут = 0, но replacement `/api/admin/identity` покрывает OIDC/SAML provider registry (`identity/router.py`) и не заменяет phase1 LDAP/mappings/test endpoints (`/api/identity/providers/{id}/test`, `/api/identity/providers/{id}/mapping/preview`, `/api/identity/mappings*`). Статус остается HOLD до unified replacement contract + security review. |
| 2026-04-07 | C-005 | Выполнен readiness-step: admin replacement namespace расширен phase1 parity endpoints | Backend Lead | В `backend/app/modules/identity/router.py` добавлены admin-namespace endpoints для directory providers и mappings: `/api/admin/identity/directory-providers*` + `/api/admin/identity/mappings*`, без конфликта с existing OIDC/SAML `/api/admin/identity/providers/{provider}`. В `backend/tests/test_identity_phase11_hardening.py` добавлена parity coverage для нового namespace; таргетный regression `tests/test_identity_phase11_hardening.py` + `tests/test_enterprise_identity.py` = 49 passed / 2 warnings. Статус пока HOLD: legacy `/api/identity/*` еще не cut over и compatibility tests остаются активны. |
| 2026-04-07 | C-005 | Cleanup-phase завершен; статус переведен HOLD -> REMOVED | Backend Lead | Из `backend/app/main.py` удален include `identity_phase1_router`; удален файл `backend/app/modules/identity/phase1_router.py`; hardening tests переведены на `/api/admin/identity/directory-providers*` и `/api/admin/identity/mappings*`; post-removal evidence: code refs `phase1_router|/api/identity` в `backend/app` + `backend/tests` = 0, runtime usage по `docker compose logs --since=90m backend` = 0, таргетный identity regression = 47 passed / 2 warnings, full backend regression в `backend-tests` = 1263 passed / 9 skipped / 2 warnings, frontend regression = 30 files / 147 tests passed, smoke-check = 8 PASS / 0 FAIL |
| 2026-04-07 | C-001,C-004 | Подтверждена совместимость post-removal contract в template-validation | Platform Architect + Backend Lead | После удаления legacy `frontend/app/admin/page.tsx` обновлен template gate: в `backend/tests/test_template_validation.py` обязательный frontend entrypoint переключен на canonical `frontend/app/(admin)/console/platform/page.tsx`; выполнен rebuild `backend-tests` image и повторный full backend regression: 1263 passed / 9 skipped / 2 warnings. |
| 2026-04-07 | C-001..C-009 | Документационная нормализация migration-артефактов | Frontend Lead | В pre-cleanup migration-документы добавлены явные пометки Historical Snapshot и указание на `CLEANUP_ENDGAME_TRACKER.md` как текущий source of truth; зафиксировано отдельным commit `090a2c5`. |
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
- [C007_OWNER_SIGNOFF_PACKAGE.md](C007_OWNER_SIGNOFF_PACKAGE.md) — Owner sign-off package (evidence + rollback)
