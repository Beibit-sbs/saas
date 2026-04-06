# Secrets Rotation Runbook (AI + Existing DB)

## Цель

Этот runbook адаптирован под текущий проект и текущую инфраструктуру.

Ключевой принцип:
- не создаем новую БД;
- не мигрируем на отдельный storage для AI;
- работаем с уже существующими `db`/`redis` и сервисами `backend`, `worker`, `scheduler`.

---

## Контур и секреты

| Секрет | Переменная | Где хранится | Кто использует |
|---|---|---|---|
| JWT signing key | `JWT_SECRET` | `infra/.env` / secrets manager | `backend`, `worker`, `scheduler` |
| Ключ шифрования runtime settings | `INTEGRATIONS_ENCRYPTION_KEY` | `infra/.env` / secrets manager | `backend` (LDAP/AI/integrations) |
| Internal API token | `INTERNAL_API_TOKEN` | `infra/.env` / secrets manager | internal endpoints, scheduler/worker integration |
| Metrics token | `METRICS_TOKEN` + `infra/prometheus/metrics_token` | env + файл для Prometheus | `backend`, `prometheus` |
| DB доступ | `DATABASE_URL` | `infra/.env` | все backend-процессы |
| Redis доступ | `REDIS_URL` | `infra/.env` | backend cache/queue, worker/scheduler |

Примечание:
- приоритет ключа шифрования: `INTEGRATIONS_ENCRYPTION_KEY` -> fallback на `JWT_SECRET` (только dev-local поведение).

---

## Перед ротацией (обязательно)

```bash
cd /home/sbs/AI/infra

# 1) Проверить, что стек поднят и healthy
docker compose --env-file .env ps

# 2) Проверить, что backend видит текущую БД (не новую)
docker compose --env-file .env exec -T backend python -c "
from app.platform.repository.db import transaction
with transaction() as conn:
    conn.execute('SELECT 1')
print('DB OK (existing connection)')
"

# 3) Зафиксировать backup перед изменениями
cd /home/sbs/AI
bash scripts/backup_db.sh
```

---

## 1) Ротация `JWT_SECRET`

Эффект:
- все текущие пользовательские сессии инвалидируются;
- потребуется повторный логин.

```bash
# 1) Сгенерировать новый секрет
python3 -c "import secrets; print(secrets.token_hex(48))"

# 2) Обновить JWT_SECRET в /home/sbs/AI/infra/.env

# 3) Применить к backend-процессам
cd /home/sbs/AI/infra
docker compose --env-file .env up -d --force-recreate backend worker scheduler

# 4) Проверить готовность
curl -sf http://localhost:8000/health/ready | python3 -m json.tool
```

---

## 2) Ротация `INTEGRATIONS_ENCRYPTION_KEY`

Эффект:
- старые encrypted runtime settings нельзя расшифровать новым ключом,
  пока настройки не будут пересохранены;
- особенно важно для LDAP и AI provider credentials.

```bash
# 1) Сгенерировать новый ключ
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# 2) Обновить INTEGRATIONS_ENCRYPTION_KEY в /home/sbs/AI/infra/.env

# 3) Перезапустить backend
cd /home/sbs/AI/infra
docker compose --env-file .env up -d --force-recreate backend
```

После перезапуска:
1. Admin -> Integrations -> LDAP: открыть и сохранить конфиг.
2. Admin -> Integrations -> AI: открыть и сохранить конфиг провайдера.
3. Выполнить тесты подключения в UI (LDAP test / AI provider validate).

---

## 3) Ротация `INTERNAL_API_TOKEN`

Эффект:
- internal вызовы со старым токеном начнут получать 401.

```bash
# 1) Новый токен
python3 -c "import secrets; print(secrets.token_urlsafe(48))"

# 2) Обновить INTERNAL_API_TOKEN в /home/sbs/AI/infra/.env

# 3) Перезапустить все internal-consumers
cd /home/sbs/AI/infra
docker compose --env-file .env up -d --force-recreate backend worker scheduler
```

---

## 4) Ротация `METRICS_TOKEN`

```bash
# 1) Новый токен
python3 -c "import secrets; print(secrets.token_hex(32))"

# 2) Обновить одновременно:
#    - /home/sbs/AI/infra/.env  (METRICS_TOKEN)
#    - /home/sbs/AI/infra/prometheus/metrics_token

# 3) Перезапуск
cd /home/sbs/AI/infra
docker compose --env-file .env up -d --force-recreate backend prometheus
```

---

## 5) Ротация `DATABASE_URL` (только существующая БД)

Важно:
- меняем доступы к уже существующей БД;
- новую БД не создаем;
- host/database name должны остаться целевыми для текущего кластера.

```bash
# 1) На стороне DBA: сменить пароль/учетку в существующей PostgreSQL

# 2) Обновить DATABASE_URL в /home/sbs/AI/infra/.env
# пример: postgresql://<user>:<new_password>@db:5432/<existing_db>

# 3) Перезапуск backend-процессов
cd /home/sbs/AI/infra
docker compose --env-file .env up -d --force-recreate backend worker scheduler

# 4) Проверка соединения
docker compose --env-file .env exec -T backend python -c "
from app.platform.repository.db import transaction
with transaction() as conn:
    conn.execute('SELECT 1')
print('DB OK (existing DB)')
"
```

---

## 6) Ротация `REDIS_URL`

```bash
# 1) Сменить пароль/параметры Redis и синхронно обновить REDIS_URL в .env

# 2) Перезапуск
cd /home/sbs/AI/infra
docker compose --env-file .env up -d --force-recreate redis backend worker scheduler

# 3) Проверка
docker compose --env-file .env exec -T backend python -c "
import os, redis
r = redis.from_url(os.environ['REDIS_URL'])
r.ping()
print('Redis OK')
"
```

---

## 7) Проверка “AI читает нашу систему” после ротации

Цель проверки: убедиться, что AI gateway продолжает работать с текущими данными и текущими подключениями.

```bash
cd /home/sbs/AI/infra

# 1) readiness
curl -sf http://localhost:8000/health/ready | python3 -m json.tool

# 2) worker/scheduler живы
docker compose --env-file .env ps backend worker scheduler db redis

# 3) backend все еще читает текущую БД
docker compose --env-file .env exec -T backend python -c "
from app.platform.repository.db import transaction
with transaction() as conn:
    conn.execute('SELECT 1')
print('DB read path OK')
"
```

Плюс через Admin UI:
1. Integrations -> AI -> Validate provider.
2. Проверить AI chat endpoint в вашем стандартном smoke-сценарии.

---

## Быстрый rollback

Если после ротации что-то сломалось:
1. Вернуть предыдущие значения секретов в `/home/sbs/AI/infra/.env`.
2. Вернуть предыдущий `infra/prometheus/metrics_token` (если менялся).
3. Перезапустить затронутые сервисы через `docker compose --env-file .env up -d --force-recreate ...`.
4. Проверить `health/ready` и ключевые smoke-пути.

---

## Рекомендованный график

| Секрет | Интервал |
|---|---|
| `JWT_SECRET` | 6-12 месяцев или сразу при компрометации |
| `INTEGRATIONS_ENCRYPTION_KEY` | 12 месяцев |
| `INTERNAL_API_TOKEN` | 6 месяцев |
| `METRICS_TOKEN` | 12 месяцев |
| `DATABASE_URL` credentials | по политике DBA |
| `REDIS_URL` credentials | по политике DBA |
