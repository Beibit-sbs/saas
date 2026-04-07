# DB Unavailable

## Проверить

1. Открыть `/health/ready` и убедиться, что `postgresql.status=down`.
2. Проверить логи backend по `error_code=postgresql.unavailable`.
3. Проверить PostgreSQL процесс и доступность порта.
4. Проверить `alembic_version` после восстановления подключения.

## Действия

1. Если PostgreSQL не запущен, поднять сервис БД.
2. Если БД запущена, проверить лимиты подключений и блокировки.
3. Если после деплоя есть drift, сравнить `current_version` и `expected_head` из `/health/ready`.
4. После восстановления выполнить:
   - `/health/ready`
   - `/health/deep`
   - smoke login

## Что логировать

1. Время начала сбоя.
2. Причину: process down / connection refused / migrations drift / saturation.
3. Время восстановления readiness.
4. Request IDs ошибок из backend логов.