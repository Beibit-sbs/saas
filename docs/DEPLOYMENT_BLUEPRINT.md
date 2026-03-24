# Deployment Blueprint

## Purpose

This document defines the minimal production deployment blueprint for piloting the platform in a real university environment.

Constraints:

- no platform redesign
- no heavy external infrastructure
- simple Linux-friendly deployment model
- secure and reproducible operations
- tenant-safe and institution-safe execution boundaries

Related pilot-operability documents:

- `docs/PILOT_DEPLOYMENT_CHECKLIST.md`
- `docs/PILOT_RBAC_AUDIT.md`
- `docs/PILOT_FEATURE_FLAG_MATRIX.md`
- `docs/BACKUP_RESTORE_DRILL.md`

## 1. Production Topology

### Minimal topology

```text
Users / Admins
    |
    v
Nginx Reverse Proxy
    |
    v
API Node (FastAPI)
    |
    +--> PostgreSQL
    |
    +--> Redis

Worker Node
    |
    +--> PostgreSQL
    +--> Redis
    |
    +--> Event processing
    +--> Automation execution
    +--> Webhook delivery

Scheduler Node
    |
    +--> PostgreSQL
    +--> Redis
    |
    +--> KPI refresh
    +--> retries
    +--> maintenance tasks
```

### Minimal server layout

- `nginx` reverse proxy
- `api` application node
- `worker` background processing node
- `scheduler` scheduled jobs node
- `postgresql` database node
- `redis` cache and queue coordination node

### Allowed pilot simplifications

- `worker` and `scheduler` may run on the same Linux host
- `nginx` and `api` may run on the same Linux host for a small pilot
- `postgresql` and `redis` should remain isolated from the application runtime when possible

## 2. Deployment Architecture

### Runtime model

The preferred pilot deployment model is:

- Linux servers
- `systemd` for service lifecycle
- Docker-ready application images or Python virtualenv services
- Nginx as reverse proxy and TLS terminator
- PostgreSQL as the system of record
- Redis for queue coordination, worker heartbeat, and lightweight runtime state

### Service layout

Recommended service units:

- `platform-api.service`
- `platform-worker.service`
- `platform-scheduler.service`
- `nginx.service`
- `postgresql.service`
- `redis.service`

### Release layout

Suggested release structure:

- `/opt/ai-university/releases/<release-id>`
- `/opt/ai-university/current` as symlink to the active release
- `/etc/ai-university/platform.env` for environment configuration

This enables a simple forward deployment and quick code rollback without changing the overall architecture.

## 3. Environment Variables

### Required variables

- `DATABASE_URL`
- `REDIS_URL`
- `JWT_SECRET`
- `API_BASE_URL`
- `ADMIN_PANEL_URL`
- `INTERNAL_API_TOKEN`

### Recommended additional variables

- `APP_ENV=production`
- `LOG_LEVEL=INFO`
- `CORS_ALLOWED_ORIGINS`
- `TRUST_PROXY_HEADERS=true`
- `REQUEST_TIMEOUT_SECONDS=30`
- `WORKER_HEARTBEAT_TTL_SECONDS=60`
- `WEBHOOK_RETRY_LIMIT=5`
- `JOB_RETRY_LIMIT=5`

### Validation rules at startup

Startup validation must fail fast when:

- any required variable is missing
- `JWT_SECRET` is shorter than 32 characters
- `DATABASE_URL` is not a PostgreSQL DSN
- `REDIS_URL` is not a Redis DSN
- `API_BASE_URL` is not HTTPS
- `ADMIN_PANEL_URL` is not HTTPS

Secrets must never be printed to logs.

## 4. Security Hardening

### Reverse proxy hardening

Nginx must enforce:

- HTTPS only
- HTTP to HTTPS redirect
- `Strict-Transport-Security`
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `Referrer-Policy: strict-origin-when-cross-origin`
- content security policy for the admin console
- `server_tokens off`
- bounded request body size

### Application hardening

The platform must implement:

- request logging with request id
- secure handling of proxy headers
- API audit logging for all admin mutations
- RBAC verification on all admin and internal routes
- placeholder rate limiting for auth and BFF entry points

### Tenant-safety rules

All platform endpoints must remain tenant-safe:

- tenant scope is derived from trusted server-side context
- client-provided `tenant_id` is accepted only for explicitly privileged platform operations
- cross-tenant operations are restricted to platform-level roles
- cross-institution views are restricted by federation permissions
- audit logs must capture actor, tenant scope, institution scope, and operation type

## 5. Backup And Restore Strategy

### Backup policy

- daily PostgreSQL snapshot using `pg_dump -Fc`
- retention of 7 days
- backup files stored on a dedicated backup path
- optional secondary copy to another internal storage target

### Backup script

File: `scripts/backup_db.sh`

```bash
#!/usr/bin/env bash
set -euo pipefail

BACKUP_DIR="/var/backups/ai-university/postgres"
TIMESTAMP="$(date +%F_%H-%M-%S)"
FILE="${BACKUP_DIR}/ai_university_${TIMESTAMP}.dump"

mkdir -p "${BACKUP_DIR}"
pg_dump "${DATABASE_URL}" -Fc -f "${FILE}"

find "${BACKUP_DIR}" -type f -name "*.dump" -mtime +7 -delete
echo "Backup created: ${FILE}"
```

### Restore script

File: `scripts/restore_db.sh`

```bash
#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 2 ]]; then
  echo "Usage: $0 <target_database_url> <dump_file>"
  exit 1
fi

TARGET_DATABASE_URL="$1"
DUMP_FILE="$2"

pg_restore --clean --if-exists --no-owner --no-privileges \
  -d "${TARGET_DATABASE_URL}" "${DUMP_FILE}"

echo "Restore completed from ${DUMP_FILE}"
```

### Restore test procedure

- provision a temporary restore database
- restore the most recent dump
- verify schema version
- run basic row-count and critical-table checks
- validate application startup against the restored database in isolation
- record backup and restore elapsed time for the pilot readiness report

## 6. Health Checks

The platform must expose the following health endpoints:

- `GET /health`
- `GET /health/db`
- `GET /health/worker`

### Expected behavior

`GET /health`

- returns `200` when the API process is healthy
- returns version, environment, and dependency summary

`GET /health/db`

- performs a lightweight database probe such as `SELECT 1`
- returns `200` when PostgreSQL is healthy
- returns `503` when PostgreSQL is unavailable

`GET /health/worker`

- checks worker heartbeat from Redis or PostgreSQL
- returns `200` when the worker heartbeat is fresh
- returns `503` when worker heartbeat exceeds the configured TTL

## 7. Monitoring Endpoints

To keep monitoring lightweight for the pilot, the platform should expose internal JSON monitoring endpoints.

### Monitoring endpoints

- `GET /metrics/ops`
- `GET /metrics/latency`

### `GET /metrics/ops`

This endpoint should expose:

- `event_queue_size`
- `failed_automation_executions`
- `failed_webhooks`
- `failed_jobs`
- `worker_last_heartbeat`
- `scheduler_last_run`
- `outbox_backlog`
- `retry_backlog`

### `GET /metrics/latency`

This endpoint should expose:

- `p50_ms`
- `p95_ms`
- `p99_ms`
- `requests_per_minute`
- `http_4xx_count`
- `http_5xx_count`

### Monitoring access rules

- monitoring endpoints must be internal-only
- no tenant-sensitive records may be returned
- outputs must be aggregated counts only

## 8. Deployment Checklist

### Standard deployment flow

1. confirm a valid database backup exists for the last 24 hours
2. confirm PostgreSQL and Redis are reachable
3. pull or unpack the new release
4. verify environment configuration and secrets
5. run database migrations
6. restart the API service
7. restart the worker service
8. restart the scheduler service
9. run smoke tests
10. verify all health endpoints
11. verify worker heartbeat and queue drain behavior
12. confirm admin login and read-only AI Copilot behavior

### Operational commands

- `alembic upgrade head`
- `systemctl restart platform-api.service`
- `systemctl restart platform-worker.service`
- `systemctl restart platform-scheduler.service`
- `curl -fsS https://<host>/health`

## 9. Rollback Procedure

### Code rollback

If the issue is application-level and the database schema remains compatible:

1. repoint `/opt/ai-university/current` to the previous release
2. restart API
3. restart worker
4. restart scheduler
5. validate health endpoints and smoke tests

### Migration rollback policy

- pilot releases should use additive migrations only
- destructive migrations should not be used during the pilot phase
- migration rollback is allowed only when the migration is explicitly reversible and safe
- otherwise prefer a forward fix over a destructive schema rollback

### Rollback prerequisites

- a recent verified backup must exist before each deployment
- each release must be self-contained and restartable

## 10. Pilot Scope

### Enabled for the first university

- students
- enrollments
- grades
- automation rules
- KPI dashboard
- semantic context layer
- AI Copilot in read-only mode
- federation administration only if the pilot includes multiple institutions or campuses

### Disabled for the pilot

- external developer apps
- marketplace features
- write-enabled AI actions
- nonessential experimental extensions

### Recommended feature flags

- `AI_COPILOT_READ_ONLY=true`
- `EXTERNAL_APPS_ENABLED=false`
- `MARKETPLACE_ENABLED=false`

## 11. Admin Role Matrix

| Role | Scope | Platform | Federation | Academic Data | Automation | KPI / Analytics | AI Copilot | Operations |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Platform Admin | global | full | full | read/write across all tenants | full | full | read-only | full |
| Institution Admin | institution | limited | manage within institution | read/write within linked tenants | full in scope | full in scope | read-only | basic |
| Academic Admin | tenant or institution | none | read-only | read/write students, enrollments, grades | manage academic rules | read dashboards | read-only | none |
| IT Support | operational | none | read-only | read-only when required for support | retry or view only | read health metrics | none | logs, jobs, webhook retry |

### Permission groups

- `platform.read`
- `platform.write`
- `federation.read`
- `federation.write`
- `students.read`
- `students.write`
- `enrollments.read`
- `enrollments.write`
- `grades.read`
- `grades.write`
- `automation.read`
- `automation.write`
- `analytics.read`
- `ai.copilot.read`
- `jobs.read`
- `jobs.retry`
- `webhooks.read`
- `webhooks.retry`
- `audit.read`
- `health.read`

### Pilot restriction

No role receives write-capable AI permissions during the pilot.

## 12. Incident Response Plan

Detailed operational procedures and triage playbooks are documented in `docs/INCIDENT_OPS_RUNBOOK.md`.

### Database outage

Indicators:

- `GET /health/db` returns `503`
- API requests fail with `5xx`
- worker backlog increases

Response:

1. verify PostgreSQL service state
2. verify disk space, active connections, and database logs
3. pause scheduler and worker if they intensify the outage
4. restore database service
5. validate `GET /health/db`
6. restart worker and scheduler in a controlled order

### Worker crash

Indicators:

- `GET /health/worker` returns `503`
- outbox backlog grows
- automation and webhooks stop progressing

Response:

1. inspect `platform-worker.service`
2. review recent worker logs
3. restart the worker
4. confirm heartbeat freshness
5. confirm backlog reduction
6. if crash loop continues, disable the triggering rule or job family and evaluate rollback

### Automation loop

Indicators:

- rapid job growth
- repeated event-trigger cycles
- Redis queue size grows continuously

Response:

1. disable the problematic automation rule
2. pause or throttle the worker if required
3. identify the triggering event path
4. verify whether the rule re-emits its own triggering event
5. correct guards, deduplication, or event filtering before re-enable

### Webhook failures

Indicators:

- `failed_webhooks` increases
- retry backlog grows
- downstream endpoint errors repeat

Response:

1. check target endpoint availability
2. check DNS, TLS, routing, and timeout conditions
3. temporarily disable the failing webhook target if needed
4. retry after downstream recovery
5. inspect repeated failure payloads for schema or auth mismatch

### Common incident flow

1. confirm the incident
2. contain the blast radius
3. restore service
4. validate recovery
5. document root cause and operator actions
6. add a preventive guardrail

## 13. Validation Checklist

After deployment, run the following validation sequence.

### API health

- `GET /health` returns `200`
- `GET /health/db` returns `200`
- `GET /health/worker` returns `200`
- admin login succeeds
- tenant-scoped endpoints do not permit cross-tenant access

### Event worker processing

- create a test event
- confirm the outbox record is consumed
- confirm backlog decreases

### Automation execution

- enable a safe test automation rule
- trigger the matching event
- confirm successful execution
- confirm no runaway retries or recursive loop behavior

### KPI refresh

- trigger a KPI refresh job
- confirm KPI values are recomputed
- confirm tenant and institution boundaries remain correct

### AI Copilot

- execute read-only AI queries
- confirm no mutation path is available
- confirm audit logging is present
- confirm tenant-safe and institution-safe response boundaries

## 14. Summary

For the first pilot, the target operating standard is:

- additive migrations only
- nightly database backups with weekly restore verification
- Nginx TLS termination
- `systemd`-managed API, worker, and scheduler processes
- internal-only health detail and monitoring endpoints
- read-only AI Copilot
- no external developer ecosystem features
- explicit platform, institution, and tenant scoping in RBAC and audit logs