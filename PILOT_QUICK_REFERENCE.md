# 🚀 Pilot Deployment Quick Reference

## Status: ✅ VALIDATED & READY

All validation gates have passed. System is ready for university pilot deployment.

---

## Validation Summary

| Gate | Result | Tests | Evidence |
|------|--------|-------|----------|
| **Pilot Safe Gate** | ✅ PASS | 62/62 | `make pilot-safe-gate` |
| **Release Gate** | ✅ PASS | 7/7 | `bash ./scripts/release_gate.sh` |
| **Backend Health** | ✅ READY | - | `/health/ready` → `{"status":"ready","ready":true}` |
| **Frontend Health** | ✅ READY | - | `/api/internal/ready` → `{"status":"ok"}` |
| **LDAP Stack** | ✅ OPERATIONAL | 6 groups + 6 users | OpenLDAP container healthy |

---

## Key Infrastructure

```
Platform Services:
  • Backend (FastAPI) ......... http://backend:8000
  • Frontend (Next.js) ........ http://frontend:3000
  • nginx (proxy) ............. http://nginx + TLS
  • Redis ..................... redis://redis:6379
  • PostgreSQL ................ db://db:5432
  • Worker .................... async processing
  • Scheduler ................. periodic tasks
  • LDAP (OpenLDAP) ........... ldap://ldap:389
  
RBAC Roles Configured:
  1. platform_admin         (cross-tenant, platform-wide)
  2. institution_admin      (faculty/department scope)
  3. academic_admin         (academic data only)
  4. it_support            (incident + backups)
  5. developer             (public API lifecycle)
  6. ops_engineer          (observability + ops)
```

---

## Startup Commands

```bash
# Start full stack with LDAP
make pilot-ldap-up

# Run full validation suite (62 tests)
make pilot-safe-gate

# Stop everything
make pilot-ldap-down

# Watch logs in real-time
make docker-logs

# Check release gate
bash ./scripts/release_gate.sh
```

---

## Quick Health Check (Local)

```bash
# Backend ready?
curl http://localhost:8000/health/ready

# Frontend running?
curl http://localhost:3000/api/internal/ready

# LDAP responding?
docker exec ai-ldap-1 ldapwhoami -H ldap://localhost

# Check stack status
docker compose ps
```

---

## Environment Variables Ready

**File:** `/infra/.env`

```bash
AUTH_LDAP_ENABLED=true
LDAP_SERVER_URI=ldap://ldap:389
LDAP_BIND_DN=cn=admin,dc=example,dc=local
LDAP_BASE_DN=dc=example,dc=local
LDAP_USER_FILTER=(cn={username})
LDAP_GROUP_ROLE_MAP_FILE=./ldap_group_role_map.json
```

---

## Test Credentials (DEV ONLY)

⚠️ **DO NOT USE IN PRODUCTION**

```
LDAP Server: ldap://ldap:389
Admin: cn=admin,dc=example,dc=local / password: admin

Test Users (all password: password123):
  - admin_user          → platform_admin
  - inst_admin          → institution_admin
  - acad_admin          → academic_admin
  - support_user        → it_support
  - dev_user            → developer
  - ops_user            → ops_engineer
```

---

## Deployment Checklist (For Ops)

- [ ] Read `docs/PILOT_DEPLOYMENT_CHECKLIST.md`
- [ ] Schedule deployment window (off-peak)
- [ ] Coordinate backup creation and test restore
- [ ] Prepare incident response contacts
- [ ] Brief university stakeholders
- [ ] Pre-deployment: Run `make pilot-safe-gate` (should see 62/62 PASS)
- [ ] Deploy release artifact
- [ ] Restart services: API → worker → scheduler
- [ ] Post-deployment: Verify health endpoints
- [ ] Watch metrics for 30 minutes
- [ ] Record sign-off in PILOT_DEPLOYMENT_CHECKLIST.md

---

## Rollback Triggers

Rollback **immediately** if:
- Persistent 5xx errors after restart
- Tenant isolation breach detected
- Worker heartbeat missing
- Webhook backlog grows without recovery
- Smoke test fails

**Rollback command:**
```bash
# Point to previous release
sudo ln -sf /opt/ai-university/releases/<previous-id> /opt/ai-university/current

# Restart services
sudo systemctl restart platform-api platform-worker platform-scheduler

# Verify
curl http://localhost:8000/health/ready
bash ./scripts/platform_smoke_check.sh
```

---

## First 30 Minutes Monitoring

Watch these metrics via `/metrics/ops`:
```
✓ event_queue_size         (should be stable/decaying)
✓ retry_backlog            (should be zero or low)
✓ dead_webhooks            (should stay zero)
✓ dead_automation_executions (should stay zero)
✓ developer_api_error_count (should be zero)
```

Look for repeating error patterns in logs.

---

## Support Contacts

| Role | Responsibility |
|------|---|
| `ops_engineer` | P1/P2 incidents, 24/7 |
| `it_support` | First-line user support |
| `platform_admin` | Escalation, rollback decisions |

> Fill in actual contact details in `docs/UNIVERSITY_OPERATIONAL_MODEL.md` § 13

---

## Full Documentation

- **Operational Model:** `docs/UNIVERSITY_OPERATIONAL_MODEL.md`
- **Deployment Checklist:** `docs/PILOT_DEPLOYMENT_CHECKLIST.md`
- **Architecture Guardrails:** `docs/GUARDRAILS.md`
- **Feature Flags:** `docs/PILOT_FEATURE_FLAG_MATRIX.md`
- **Backup/Recovery:** `docs/BACKUP_RESTORE_DRILL.md`
- **Full Summary:** `DEPLOYMENT_SUMMARY_APPROVED.md`

---

**Ready to deploy! 🎯**

Questions? Refer to operational documents or reach out to platform ops team.
