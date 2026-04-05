# Runbooks — Production Incident Playbooks

---

## RB-01: Jobs Stuck / Queue Growing

**Симптом:** `jobs_queue_size` > 50 долго не снижается; worker не обрабатывает задачи.

**Как проверить:**
```bash
# Метрики очереди
docker exec ai-nginx-1 python3 -c "import urllib.request; r = urllib.request.urlopen('http://nginx/metrics', timeout=5); print([l for l in r.read().decode().splitlines() if 'jobs_queue' in l])"

# Логи worker
docker logs ai-worker-1 --tail=50 2>&1

# Heartbeat worker
docker exec ai-backend-1 python -c "from app.platform.runtime_state import get_worker_heartbeat; import json; print(json.dumps(get_worker_heartbeat(), default=str))"

# Health deep (требует auth-токен)
docker exec ai-backend-1 python3 -c "import urllib.request; r = urllib.request.urlopen('http://backend:8000/health/deep', timeout=5); print(r.read().decode())"
```

**Как восстановить:**
1. Перезапустить worker: `docker compose --env-file .env restart worker`
2. Если не помогает — проверить DB: `docker exec ai-db-1 psql -U app app -c "SELECT status, count(*) FROM jobs GROUP BY status;"`
3. Застрявшие running-задачи — вручную reset: `UPDATE jobs SET status='queued', started_at=NULL WHERE status='running' AND started_at < NOW() - INTERVAL '10 minutes';`
4. Если DB недоступна — `docker compose --env-file .env restart db`

---

## RB-02: Backend Down / 502 от nginx

**Симптом:** nginx возвращает 502 на `/api/*`; `ai-backend-1` unhealthy или exit.

**Как проверить:**
```bash
# Статус контейнеров
docker compose --env-file .env ps

# Логи backend
docker logs ai-backend-1 --tail=100 2>&1 | grep -E 'ERROR|CRITICAL|RuntimeError'

# Прямая проверка backend
docker exec ai-backend-1 python3 -c "import urllib.request; print(urllib.request.urlopen('http://backend:8000/health/live', timeout=3).read().decode())"
```

**Как восстановить:**
1. `docker compose --env-file .env restart backend`
2. Если падает при старте — проверить env: `JWT_SECRET`, `DATABASE_URL`, `INTERNAL_API_TOKEN`
3. Если DB connection refused: `docker compose --env-file .env restart db` → дождаться healthy → `docker compose --env-file .env restart backend`
4. OOM: `docker stats ai-backend-1` → увеличить memory limit в compose или перезапустить

---

## RB-03: DB Connection Error

**Симптом:** логи содержат `DependencyUnavailableError` / `psycopg.OperationalError`; `/health/ready` возвращает `ready: false`.

**Как проверить:**
```bash
# Ready endpoint
docker exec ai-backend-1 python3 -c "import urllib.request; print(urllib.request.urlopen('http://backend:8000/health/ready', timeout=5).read().decode())"

# DB живёт?
docker exec ai-db-1 pg_isready -U app -d app

# Соединения к DB
docker exec ai-db-1 psql -U app app -c "SELECT count(*) FROM pg_stat_activity;"

# Логи postgres
docker logs ai-db-1 --tail=30 2>&1
```

**Как восстановить:**
1. `docker compose --env-file .env restart db` → ждать `(healthy)` → `docker compose --env-file .env restart backend`
2. Если volume повреждён: `docker compose --env-file .env down db` → `docker volume inspect ai_postgres_data` → restore из backup:
   ```bash
    cd /home/sbs/AI && DATABASE_URL='postgresql://user:pass@host:5432/target_db' bash scripts/restore_db.sh --execute --confirm RESTORE backups/latest.dump
   ```
3. Проверить disk space: `df -h` — postgres падает при 100% диска

---

## RB-04: Auth Failure Spike / Lockout

**Симптом:** `auth_login_failures_total` резко растёт; пользователи не могут залогиниться; `security_anomalies_total` > 0.

**Как проверить:**
```bash
# Auth failure метрики
python3 -c "
import urllib.request
r = urllib.request.urlopen('http://nginx/metrics', timeout=5)
lines = [l for l in r.read().decode().splitlines() if 'auth_login_fail' in l or 'security_anomal' in l]
print('\n'.join(lines))
"

# Логи auth попыток
docker logs ai-backend-1 --tail=200 2>&1 | python3 -c "
import sys, json
for line in sys.stdin:
    try:
        d = json.loads(line)
        if 'auth' in d.get('message','') or 'login' in d.get('message',''):
            print(d.get('timestamp',''), d.get('message',''), d.get('actor_id',''))
    except: pass
"

# Rate limit статус
docker exec ai-backend-1 python3 -c "import urllib.request; print(urllib.request.urlopen('http://backend:8000/health/ready', timeout=5).read().decode())"
```

**Как восстановить:**
1. **Brute-force атака**: Source IP виден в nginx логах → заблокировать в nginx `deny <ip>;` в `nginx.conf`; перезагрузить: `docker exec ai-nginx-1 nginx -s reload`
2. **Credential stuffing**: убедиться что `AUTH_CSRF_PROTECTION_ENABLED=true`, rate limiting активен
3. **Законные пользователи заблокированы** (ошибка конфига): проверить `JWT_SECRET` не изменился; при ротации — выпустить новые токены
4. **LDAP недоступен**: `AUTH_LDAP_ENABLED=false` временно → перезапустить backend → восстановить LDAP → вернуть `true`

---

## Общие команды диагностики

```bash
# Все сервисы
docker compose --env-file .env ps

# Метрики (сырые)
docker exec ai-nginx-1 python3 -c "import urllib.request; print(urllib.request.urlopen('http://nginx/metrics', timeout=5).read().decode())" | head -60

# Prometheus targets
docker exec ai-prometheus-1 python3 -c "import urllib.request; import json; r = urllib.request.urlopen('http://prometheus:9090/api/v1/targets', timeout=5); print(json.dumps(json.loads(r.read()), indent=2))"

# Последние 50 structured logs backend
docker logs ai-backend-1 --tail=50 2>&1 | python3 -c "
import sys, json
for line in sys.stdin:
    try:
        d = json.loads(line)
        lvl = d.get('level', 'INFO')
        if lvl in ('ERROR', 'WARNING', 'CRITICAL'):
            print(d.get('timestamp',''), lvl, d.get('message',''), d.get('logger',''))
    except: pass
"
```
