# PRODUCTION REMEDIATION STATUS

Дата обновления: 2026-04-06

## Выполнено в этой итерации

1. Закрыт внешний доступ к API docs путям на nginx уровне.
- Изменение: добавлены явные блоки для `/docs`, `/redoc`, `/openapi.json`.
- Файл: `infra/nginx/nginx.conf`.
- Текущий runtime результат: пути возвращают 404 (не публичная документация).

2. Исправлен разрыв контракта метрик на health-странице.
- Изменение: `useMetrics()` больше не обращается к старому `/metrics`, теперь читает `/api/v1/platform/ops/summary` и маппит ответ в текущий UI-формат.
- Файл: `frontend/modules/platform/health/hooks.ts`.
- Проверка: frontend lint проходит без ошибок.

3. Добавлены backend тесты в Docker image.
- Изменение: в Dockerfile добавлены `COPY tests ./tests` и `COPY pytest.ini ./pytest.ini`.
- Файл: `backend/Dockerfile`.
- Проверка: в процессе контейнерной сборки видно, что слои tests/pytest.ini включены.

4. Устранено дублирование метрик в platform ops summary.
- Изменение: `event_queue_size` больше не дублирует `outbox_backlog` напрямую; теперь вычисляется как агрегат очередей (`outbox_backlog + retry_backlog`) с fallback для частичных данных.
- Файл: `backend/app/platform/router_ops.py`.

5. Добавлены page-level permission guards для чувствительных frontend зон.
- Изменение: Admissions page требует `admissions.read`, write-операции отображаются только при `admissions.write`.
- Файл: `frontend/app/(admin)/console/admissions/page.tsx`.
- Изменение: Platform control plane требует `tenants.read`.
- Файл: `frontend/app/(admin)/console/platform/page.tsx`.

6. Проверены и подтверждены production guardrails для окружения и origin-политики.
- Изменение: проведена верификация runtime-конфигурации и CORS-поведения без расширения attack surface.
- Файл: `backend/app/core/config.py` (обязательная валидация критичных env), `backend/app/main.py` (startup `validate_required_environment()`).
- Результат: backend не содержит `CORSMiddleware`/`ALLOW_ORIGINS` конфигурации (cross-origin доступ не открыт по умолчанию); обязательные runtime env (`DATABASE_URL`, `REDIS_URL`, `JWT_SECRET`, `INTERNAL_API_TOKEN`, `INTEGRATIONS_ENCRYPTION_KEY`) валидируются при старте.

7. Production-safety для placeholder job handlers.
- Изменение: placeholder handlers теперь явно заблокированы в production mode через `is_production_mode()` check в `_execute_placeholder()`.
- Файл: `backend/app/modules/jobs/worker.py`.
- Документация: создана дефолтная записка о de-scope (`docs/PLACEHOLDER_HANDLERS_DENYLIST.md`).
- Результат: любая попытка выполнить placeholder handler тип в production выбросит ошибку с ясным сообщением; тесты проходят; product scope decision отложен до stakeholder sign-off.

## Валидация

- Frontend lint: PASS.
- Проверка синтаксических ошибок измененных файлов: PASS.
- Backend job tests: PASS (`tests/test_jobs.py` — 5 passed).

## Открытые пункты до production

1. Подготовить безопасный план вывода legacy контуров через `CLEANUP_ENDGAME_TRACKER.md` (кандидаты C-001..C-009 в статусе HOLD).
2. **Stakeholder sign-off на product scope для placeholder handlers**: реализовать конкретные обработчики или явно де-скопировать из product (удалить типы из enum/UI).

## Связанные документы

- Аудит: `AUDIT_REPORT_FULL.md`
- Финальный cleanup-трекер: `CLEANUP_ENDGAME_TRACKER.md`
- Placeholder handlers de-scope: `docs/PLACEHOLDER_HANDLERS_DENYLIST.md`
