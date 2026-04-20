# F1/F2 Day7 Official Review Checklist

**Date:** 2026-04-20  
**Phase:** Official day-7 post-release review  
**Approver:** Engineering Lead  
**Status:** ⏳ PENDING (fill at review)

---

## Pre-Review Setup

- [ ] All host dev processes killed (`make kill-host`)
- [ ] Docker stack up and healthy (`make up && docker compose -f infra/docker-compose.yml ps`)
- [ ] All tests passing locally (`make ci`)
- [ ] Repository in clean state (no uncommitted changes)

---

## 🎯 F1 Risk Phase Review (day-7)

### Data Integrity

- [ ] Risk pipeline baseline data captured and persisted
- [ ] All student records with risk assessment populated (count in DB matches seed)
- [ ] Historical risk snapshots exist (at least 3 for regression test)
- [ ] No data loss vs day-1 baseline

**Command:** `docker compose -f infra/docker-compose.yml exec -T postgres psql -U sbs_admin -d sbs -c "SELECT COUNT(*) FROM risk_phases WHERE phase='F1' AND created_at < now() - interval '7 days';"`

### Test Coverage & Quality

- [ ] Backend test suite: **1950 tests PASS, 0 FAIL** (run: `make test`)
- [ ] Coverage maintained at **83.99%** (run: `docker compose -f infra/docker-compose.yml run --rm --no-deps backend-tests pytest --cov=backend/app --cov-report=term-missing -q`)
- [ ] No new flaky tests introduced
- [ ] No regressions vs day-3 baseline

**Expected:** All day-3 tests still pass with same coverage

### API Contracts

- [ ] Risk API endpoint `/api/v1/risk/students` returns complete schema (course, gpa, engagement, risk_score)
- [ ] Risk report schema matches contract spec (`backend/tests/contracts/risk_spec.yaml`)
- [ ] No breaking changes in endpoint signatures

**Command:** `docker compose -f infra/docker-compose.yml exec -T backend python -c "from backend.app.routes.risk import router; print([r.path for r in router.routes])"`

### Observability

- [ ] All risk-phase metrics instrumented (p95, errors, throughput)
- [ ] Alert rules for risk pipeline active in Prometheus
- [ ] Grafana risk-observability dashboard loads without errors
- [ ] No silent failures (all errors logged and alerted)

**Command:** `make f3-5-observability-kickoff` (validates alert rules)

### Operational Readiness

- [ ] Rollback path documented and tested (can revert F1 if needed)
- [ ] Post-release backup exists and is restorable
- [ ] No hard-coded credentials or secrets in logs
- [ ] Docker-only execution verified (no host dev processes)

---

## 🎯 F2 Playbooks Phase Review (day-7)

### Data Integrity

- [ ] Playbook recommendations generated for at-risk cohorts
- [ ] Intervention playbooks applied to student records
- [ ] Recommendation state persisted and queryable
- [ ] No data loss vs day-1 baseline

**Command:** `docker compose -f infra/docker-compose.yml exec -T postgres psql -U sbs_admin -d sbs -c "SELECT COUNT(*) FROM playbook_recommendations WHERE phase='F2' AND created_at < now() - interval '7 days';"`

### Test Coverage & Quality

- [ ] All playbook-domain tests passing (run: `make test`)
- [ ] Playbook generation deterministic (same input → same output)
- [ ] No regressions vs day-3 baseline
- [ ] No new flaky tests

### API Contracts

- [ ] Playbook API endpoint `/api/v1/playbooks/{student_id}` returns complete schema
- [ ] Playbook mutation endpoints (`POST /api/v1/playbooks/{id}/apply`) idempotent (repeat request = same state)
- [ ] No breaking changes in signatures

### Observability

- [ ] All playbook metrics instrumented (generation time, apply success rate)
- [ ] Alert rules for playbook failures active
- [ ] Grafana platform-ops dashboard shows playbook metrics
- [ ] No silent failures

### Operational Readiness

- [ ] Rollback path documented (can revert F2 mutations if needed)
- [ ] Post-release backup restorable
- [ ] No secrets in logs
- [ ] Docker-only verified

---

## 🔐 Security & Compliance

- [ ] No new CVEs in dependencies (`npm audit --production` < threshold)
- [ ] No hardcoded secrets in code or logs
- [ ] Auth tokens/API keys properly scoped (test with invalid token should fail)
- [ ] Debug logs sanitised (no raw payloads dumped)

---

## 🏁 Sign-Off

| Role | Name | Signature | Date |
|------|------|-----------|------|
| Engineering Lead | PENDING | PENDING | 2026-04-20 |
| QA Lead | PENDING | PENDING | 2026-04-20 |
| Product Manager | PENDING | PENDING | 2026-04-20 |

---

## 📝 Notes & Findings

(Fill during review)

---

## ✅ Final Disposition

- [ ] **PASS** — All items checked, ready for production
- [ ] **CONDITIONAL PASS** — Minor issues documented, remediation plan in place
- [ ] **FAIL** — Blocking issues found, cannot proceed to F3

**Decision:** ________________  
**Reason:** ________________

---

## Next Steps (upon PASS)

1. Commit sign-off artifact to repo
2. Unlock F3 development (gates F3.3 unfreeze)
3. Publish release notes to stakeholders
4. Begin F3.4/F3.5 parallel Phase 1 kickoff (2026-04-21 11:30 UTC)
