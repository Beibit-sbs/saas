# F3 Service Outage Incident Response

**Severity:** P1 (High)  
**Time to First Response:** < 10 min  
**Time to Mitigation:** < 30 min  
**Runbook Owner:** Platform SRE, Backend Lead  
**Last Updated:** 2026-04-14

---

## Detection

**Automated alerts (Prometheus):**
- `F3APIErrorRateHigh`: API error rate > 1% for 2+ minutes
- `F3AnalysisLatencySLOViolation`: P95 latency > 2 seconds
- `F3DatabaseUnavailable`: DB connectivity failed
- `F3BackendHealthCheckFailed`: Health endpoint returns 5xx

**Manual reports:**
- User: "F3 analysis is timing out/returning errors"
- Ops team monitoring dashboard shows red

---

## Immediate Diagnosis (0–5 minutes)

```bash
# 1. Check backend service health
curl -s http://localhost:8000/health/live | jq .
# Expected: { "status": "ok" }

# 2. Check database connectivity
docker exec ai-db-1 pg_isready -U app -d app

# 3. Check P95 latency
curl -s http://prometheus:9090/api/v1/query \
  'histogram_quantile(0.95, f3_analyze_cohort_duration_seconds)' | jq .

# 4. Check error rate
curl -s http://prometheus:9090/api/v1/query \
  'rate(f3_http_requests_total{status=~"5.."}[5m]) / rate(f3_http_requests_total[5m])' | jq .

# 5. Check backend logs for errors
kubectl logs -n production deployment/backend --tail=100 | grep ERROR | head -20

# 6. Check database resource usage
docker exec ai-db-1 psql -U app -d app -c \
  "SELECT now(), \
    (SELECT count(*) FROM pg_stat_activity) as active_connections, \
    (SELECT sum(heap_blks_read) FROM pg_statio_user_tables) as heap_reads, \
    (SELECT sum(idx_scan) FROM pg_stat_user_indexes) as idx_scans;"
```

---

## Triage Decision Tree

```
Is backend responding to /health/live?
├─ NO → Go to "Backend Crashed"
└─ YES → Is database responding?
   ├─ NO → Go to "Database Unavailable"
   └─ YES → Is error rate > 1%?
      ├─ NO → Is P95 latency > 2s?
      │  ├─ YES → Go to "Slow Queries"
      │  └─ NO → **FALSE ALARM** (alert threshold misconfigured?)
      └─ YES → Is error 500 or 4xx?
         ├─ 4xx → Go to "Invalid Requests" (client-side issue)
         └─ 5xx → Go to "Backend Exception"
```

---

## Scenario 1: Backend Crashed

**Symptoms:** `GET /health/live` → Connection refused or 503

```bash
# 1. Check pod status
kubectl get pods -n production | grep backend

# 2. Check if container crashed
kubectl describe pod -n production deployment/backend \
  | grep -A 10 "Container State"

# 3. Check logs for crash reason
kubectl logs -n production deployment/backend --previous | tail -50

# 4. If container is stuck, force restart
kubectl delete pod -n production -l app=backend

# 5. Watch restart progress
kubectl rollout status deployment/backend -n production -w

# 6. Post-restart check
sleep 10
curl -s http://localhost:8000/health/live | jq .
```

**Recovery ETA:** 3–5 minutes (pod restart + DB reconnection)

---

## Scenario 2: Database Unavailable

**Symptoms:** `pg_isready` returns "rejecting" or "no response"; backend logs show "connection refused"

```bash
# 1. Check database pod status
docker ps | grep ai-db

# 2. Check database logs
docker logs ai-db-1 | tail -50

# 3. Check if database is accepting connections
docker exec ai-db-1 psql -U app -d app -c "SELECT 1;"

# 4. If hung: Check active connections
docker exec ai-db-1 psql -U app -d app -c \
  "SELECT pid, usename, state, query FROM pg_stat_activity LIMIT 20;"

# 5. Kill long-running F3 queries (if blocking others)
docker exec ai-db-1 psql -U app -d app -c \
  "SELECT pg_terminate_backend(pid) FROM pg_stat_activity \
   WHERE query LIKE '%cohort%' AND state_change < NOW() - INTERVAL '5 min';"

# 6. Check disk space (common issue)
docker exec ai-db-1 df -h /var/lib/postgresql/data

# 7. If out of space: Grow PV (Kubernetes)
kubectl patch pvc postgres-data -n production \
  -p '{"spec":{"resources":{"requests":{"storage":"100Gi"}}}}'
```

**Recovery:** Depends on cause (connection pooling restart: 2 min; disk space: 10–15 min; query kill: immediate)

---

## Scenario 3: Slow Queries (P95 > 2s)

**Symptoms:** Backend responds, but P95 analysis latency > 2 seconds; error rate low

```bash
# 1. Identify slow query (from Jaeger tracing)
kubectl logs -n production deployment/backend | grep "slow_query" | tail -5

# 2. Check database query execution plan
# Connect to DB and analyze slow cohort analysis query
docker exec ai-db-1 psql -U app -d app << 'SQL'
EXPLAIN ANALYZE
SELECT c.id, COUNT(o.id) as outcome_count
FROM app_intervention_cohorts c
LEFT JOIN app_intervention_cohort_outcomes o ON c.id = o.cohort_id
WHERE c.tenant_id = 1
GROUP BY c.id
LIMIT 1;
SQL

# 3. Check for missing indexes
docker exec ai-db-1 psql -U app -d app << 'SQL'
SELECT schemaname, tablename, indexname
FROM pg_indexes
WHERE tablename LIKE 'app_intervention%'
ORDER BY tablename, indexname;
SQL

# 4. If index missing: Create it (downtime-free)
docker exec ai-db-1 psql -U app -d app -c \
  "CREATE INDEX CONCURRENTLY idx_cohort_outcomes_by_tenant \
   ON app_intervention_cohort_outcomes(cohort_id, outcome_type);"

# 5. Force query plan refresh
docker exec ai-db-1 psql -U app -d app -c "ANALYZE app_intervention_cohorts, app_intervention_cohort_outcomes;"
```

**Recovery:** 5–15 minutes (index creation or query optimization)

---

## Scenario 4: Backend Exceptions (5xx error rate high)

**Symptoms:** Error rate > 1%; logs show exceptions (e.g., `ValueError`, `KeyError`)

```bash
# 1. Extract error pattern
kubectl logs -n production deployment/backend --tail=200 | grep ERROR | \
  awk '{print $NF}' | sort | uniq -c | sort -rn | head -10

# 2. Check if it's a known issue
grep -r "Traceback\|Exception" docs/RUNBOOKS.md docs/KB/

# 3. If bad deployment: Rollback
kubectl rollout history deployment/backend -n production
kubectl rollout undo deployment/backend -n production
kubectl rollout status deployment/backend -n production -w

# 4. If input validation issue: Check recent client requests
kubectl logs -n production deployment/backend --tail=500 | \
  grep "ValidationError\|cohort_name\|analysis_window" | head -10

# 5. If code bug: Deploy hotfix
# (Edit code → rebuild image → push → update deployment image)
docker build -t backend:hotfix-$(date +%s) ./backend
docker push backend:hotfix-...
kubectl set image deployment/backend backend=backend:hotfix-... -n production

# 6. Monitor error rate (should drop to < 0.1% after fix)
watch -n 5 'curl -s http://prometheus:9090/api/v1/query "rate(f3_http_requests_total{status=~\"5..\"}[1m]) / rate(f3_http_requests_total[1m])" | jq .'
```

**Recovery:** 5–30 minutes (depends on fix complexity)

---

## Scenario 5: Invalid Requests (4xx rate high)

**Symptoms:** Error rate > 5%; logs show 400/422 errors

```bash
# 1. Check what requests are failing
kubectl logs -n production deployment/backend --tail=200 | \
  grep "400\|422\|ValidationError" | head -20

# 2. Common causes:
# - Client sending invalid JSON
# - Cohort ID out of range
# - Missing Authorization header
# - Outdated API client

# 3. Check if it's a client bug (e.g., mobile app sends bad JSON)
# Coordinate with frontend/mobile team to fix & roll out update

# 4. Temporary mitigation: If needed, can relax validation (risky!)
# kubectl set env deployment/backend \
#   F3_STRICT_VALIDATION=false
# (Restore after client fix is deployed)
```

**Recovery:** Client-side — depends on dev team update cycle

---

## Failover to Replica Database (if available)

**Only for critical outages where primary DB is corrupted/down**

```bash
# 1. Check replica status
kubectl get pods -n production | grep postgres-replica

# 2. Promote replica to primary
kubectl exec postgres-replica-0 -n production -- \
  pg_ctl promote -D /var/lib/postgresql/data

# 3. Point backend connection string to new primary
kubectl set env deployment/backend \
  DATABASE_URL=postgresql://app@postgres-replica-0.postgres.default.svc:5432/app

# 4. Restart backend
kubectl rollout restart deployment/backend -n production

# 5. Rebuild old primary from new primary (after incident)
# (This is a long process; schedule during low-traffic window)
```

---

## Post-Incident Steps

1. **Alert clear:** Once P95 < 2s and error rate < 0.5% for 10+ minutes
2. **Root cause analysis:** What failed and why?
3. **Post-mortem:** Document in `INCIDENT_OPS_RUNBOOK.md`
4. **Prevention:** Update monitoring/alerting if thresholds were wrong

---

## Monitoring Dashboard

**Real-time during incident:**
```
Prometheus queries to keep open:
- f3_analyze_cohort_duration_seconds (latency over time)
- rate(f3_http_requests_total[1m]) (total request rate)
- rate(f3_http_requests_total{status=~"5.."}[1m]) (error rate)
- rate(f3_db_query_duration_seconds[1m]) (DB latency)

Grafana dashboard: http://prometheus:3000/d/f3-effectiveness-dashboard
```

---

## Contacts

| Role | On-call | Phone | Email |
|------|---------|-------|-------|
| SRE (Primary) | [TBD] | [TBD] | [TBD] |
| SRE (Backup) | [TBD] | [TBD] | [TBD] |
| Backend Lead | [TBD] | [TBD] | [TBD] |
| Database DBA | [TBD] | [TBD] | [TBD] |

---

## References

- **Database Runbook:** `docs/runbooks/DB_UNAVAILABLE.md`
- **F3 Observability:** `docs/F3_OBSERVABILITY_SPEC.md`
- **SLO Definitions:** F3 P95 latency 2s, error rate < 0.5%
