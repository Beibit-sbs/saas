# Recovery

## PostgreSQL backup -> restore

1. Остановить write-heavy worker/scheduler.
2. Выполнить backup через `scripts/backup_db.sh`.
3. Выполнить restore через `scripts/restore_db.sh --execute --confirm RESTORE` в изолированную target DB.
4. Поднять backend.
5. Проверить:
   - `/health/ready`
   - `/health/deep`
   - login smoke
   - one read/write smoke on pilot module

## Redis restart

1. Перезапустить Redis.
2. Дождаться `PING` success.
3. Проверить `/health/ready`.
4. Проверить worker/scheduler heartbeat в `/health/deep`.

## Backend restart without consistency loss

1. Не перезапускать backend до восстановления PostgreSQL.
2. После рестарта backend убедиться, что readiness стал true до возврата трафика.
3. Проверить одну запись оценки или заявки end-to-end.

## Reconnect logic

1. DB reconnect валидируется через новый session open в readiness probe.
2. Redis reconnect валидируется через `PING` в readiness probe.
3. Recovery событие должно появиться в structured logs как `dependency_recovered`.