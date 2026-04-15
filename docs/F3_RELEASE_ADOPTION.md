# F3.8 Release & Adoption Specification

**Version:** v1.0  
**Status:** Specification Ready (implementation unfrozen 2026-04-21)  
**Target Completion:** 2026-05-05 (post-F3.4/F3.5 delivery)  
**Release Owner:** Product Manager, Release Engineering  
**Adoption Owner:** Institutional Research Team

---

## Overview

F3.8 Release & Adoption defines the deployment strategy, feature flag architecture, rollout stages, and adoption playbook for the Intervention Effectiveness Lab.

**Key principles:**
- **Progressive rollout:** Canary → Staged → Full production
- **Feature flag controlled:** All F3 features gated, can disable in production without code redeploy
- **Rollback-first design:** Every deployment must have a documented rollback path
- **Data-driven adoption:** Metrics guide GO/NO-GO decision at each stage

---

## Deployment Architecture

### 1. Feature Flag Matrix

**Tool:** LaunchDarkly or feature-flag-vendor (TBD by platform)

| Feature | Flag Key | Default | Owner | Production Control |
|---------|----------|---------|-------|-------------------|
| F3 cohort creation (finalize) | `f3_cohort_finalization` | false | Backend | Product Manager |
| F3 cohort analysis | `f3_cohort_analysis` | false | Backend | Product Manager |
| F3 outcome reporting | `f3_outcome_reporting` | false | Frontend | Product Manager |
| F3 guardrail enforcement | `f3_guardrails_enabled` | true (post-unfreeze) | Backend | Engineering Lead |
| F3 export functionality | `f3_export_enabled` | false | Frontend | Compliance Officer |
| F3 audit logging | `f3_audit_logging` | true | Backend | SRE |
| F3 observability dashboards | `f3_grafana_enabled` | false | DevOps | Product Manager |

**Flag rollout strategy:**
- **Canary:** Enabled for 5% of tenants (institutions)
- **Staged:** Enabled for 25% → 50% → 75% → 100%
- **Granular:** Can enable by tenant_id, user role, or random % sampling

### 2. Deployment Stages

```
┌─────────────────────────────────────────────────────┐
│ Stage 0: Code Merge (pre-release)                   │
│ ✓ All tests pass, security scan passed              │
│ ✓ FF default = false (dark mode)                    │
│ Action: Merge to main, tag release                  │
└─────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────┐
│ Stage 1: Internal Canary (24 hours)                 │
│ ✓ Deploy to staging env                             │
│ ✓ Internal team (research + compliance) tests F3    │
│ ✓ FF enabled for internal test tenant               │
│ Decision: Health check, latency, errors < 0.1%     │
│ Rollback: Disable FF (`f3_cohort_finalization`)    │
└─────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────┐
│ Stage 2: Partner Canary (3 days)                    │
│ ✓ Deploy to prod, FF enabled for 2 pilot tenants   │
│ ✓ Monitor metrics: latency, error rate, user signal│
│ Decision: SLO met? No P0 incidents?                 │
│ GO threshold: P95 ≤ 2s, error rate < 0.5%          │
│ Rollback: Disable FF via LaunchDarkly               │
└─────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────┐
│ Stage 3: Staged Rollout (2 weeks)                   │
│ ✓ Widening: 5% → 25% → 50% → 75% of tenants       │
│ ✓ Each stage: 2–3 days monitoring                   │
│ ✓ Watch for: Outlier behavior, feedback, incidents │
│ Decision: KPI on track? Adoption healthy?           │
│ Rollback: Narrow % or disable FF                    │
└─────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────┐
│ Stage 4: GA (General Availability)                  │
│ ✓ 100% of tenants enabled                          │
│ ✓ FF can remain for gradual deprecation (1 quarter)│
│ ✓ Retire FF after all code paths tested in prod    │
│ Decision: Final checks + stakeholder sign-off       │
│ Rollback: Still possible via FF disable             │
└─────────────────────────────────────────────────────┘
```

---

## Rollback Policy

### Immediate Rollback Triggers (Emergency)

| Trigger | Severity | Action | Time |
|---------|----------|--------|------|
| Data loss detected | P0 | Disable all FF → emergency downtime window if needed | < 5 min |
| FERPA violation | P0 | Emergency data dump + audit, disable exports | < 5 min |
| Cross-tenant access leak | P0 | Kill all sessions, revoke tokens, incident response | < 5 min |
| Availability SLO: error rate > 5% | P1 | Disable FF, investigate | < 15 min |
| Performance SLO: P95 > 5s | P1 | Rollback or disable FF | < 15 min |

### Graceful Rollback Triggers (Controlled)

| Trigger | Severity | Decision Maker | Action | Timeline |
|---------|----------|----------------|--------|----------|
| User feedback: adoption < 10% after 1 week | P2 | Product Manager | Disable FF, gather feedback, redesign | 3–7 days |
| KPI miss: guardrail pass rate < 70% | P2 | Engineering Lead | Root cause analysis, code hotfix or FF disable | 2–5 days |
| Performance regression: P95 increases > 20% | P2 | SRE | Investigate query/load, optimize or rollback | 1–3 days |

### Rollback Execution

**Steps (< 5 minutes):**
```bash
# 1. Announce rollback via Slack/status page
slack_channel #f3-rollout "🚨 F3 rollback initiated (Reason: [trigger])"
post_status_page "F3 service temporarily disabled for emergency maintenance"

# 2. Disable all feature flags
launch_darkly_disable_flag("f3_cohort_finalization")
launch_darkly_disable_flag("f3_cohort_analysis")
launch_darkly_disable_flag("f3_outcome_reporting")
launch_darkly_disable_flag("f3_export_enabled")

# 3. Verify API returns 503 for F3 endpoints
curl https://api.institution.edu/api/admin/interventions/cohorts/finalize
# Expected: 503 Service Unavailable

# 4. Monitor error rate drop (should see < 0.1% within 2 min)
prometheus_query("rate(f3_http_errors_total[1m])")

# 5. Post-mortem email
send_email @vp-eng @product "F3 Rollback Initiated" \
  "Trigger: [reason], Rollback time: [duration], Root cause: TBD"
```

---

## Environment Configuration

### Staging Deployment

**Purpose:** Internal canary validation before production  
**URL:** `https://staging-api.institution.edu/`  
**Database:** PostgreSQL staging (separate from production)  
**Feature flags:** Test flags enabled  
**Audience:** Internal research team + compliance officer

```yaml
# docker-compose.staging.yml
services:
  backend:
    image: backend:${RELEASE_TAG}
    environment:
      DATABASE_URL: postgresql://app@staging-db:5432/app
      LAUNCHDARKLY_ENV: staging
      F3_COHORT_FINALIZATION: false
      F3_AUDIT_LOGGING: true
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health/live"]
      interval: 10s
      timeout: 5s
      retries: 3
```

### Production Deployment

**Purpose:** Customer-facing service  
**URL:** `https://api.institution.edu/`  
**Database:** PostgreSQL production (multi-region replicated)  
**Feature flags:** LaunchDarkly config (progressive rollout)  
**Audience:** All institutions

```yaml
# docker-compose.prod.yml
services:
  backend:
    image: backend:${RELEASE_TAG}
    environment:
      DATABASE_URL: postgresql://app@prod-db:5432/app
      LAUNCHDARKLY_ENV: production
      F3_COHORT_FINALIZATION: false  # Controlled by LaunchDarkly
      F3_AUDIT_LOGGING: true
      F3_OBSERVABILITY_ENABLED: true
    traffic_policy:
      max_rps: 1000  # Rate limit across all tenants
      circuit_breaker: enabled
    alerting:
      - name: f3_error_rate_high
        threshold: error_rate > 1%
      - name: f3_latency_slo_violated
        threshold: p95_latency > 2s
```

---

## Release Timeline

### Pre-Release Testing (2026-04-21 → 2026-05-10)

| Date | Milestone | Owner | Status Check |
|------|-----------|-------|--------------|
| 2026-04-21 | F3.3 unfreeze (backend + API) | Backend | All 40 tests passing, router wired |
| 2026-04-28 | F3.4 frontend delivery | Frontend | UI pages built, 25 E2E tests passing |
| 2026-05-05 | F3.5 observability + F3.4 complete | DevOps | Prometheus + Grafana dashboards live; P95 ≤ 2s |
| 2026-05-10 | F3.6 security + testing matrix | Security | Pen-test passed, compliance tests ✅ |

### Release Day (2026-05-15)

**Preparation (22:00 → 23:00):**
- [ ] Code tagged: `release/f3-v1.0.0`
- [ ] All staging tests pass
- [ ] FF defaults set to `false`
- [ ] Incident response team on-call (SRE, Backend, Compliance)
- [ ] Status page prepared
- [ ] Rollback runbook reviewed

**Stage 1 Canary Deployment (23:00 → 2026-05-16 23:00):**
- [ ] Deploy to staging
- [ ] Internal team tests (research + compliance) → 2 hours
- [ ] Permission to proceed to Stage 2? ✅ GO
- [ ] Action: Internal go/no-go review

**Stage 2 Partner Canary (2026-05-16 23:00 → 2026-05-19 23:00):**
- [ ] Deploy to prod with FF = false (dark mode)
- [ ] Enable FF for 2 pilot institutions (tenant IDs TBD)
- [ ] Monitor metrics every 4 hours
- [ ] Daily status: metrics dashboard + feedback summary
- [ ] After 72h: decision to widen or rollback

**Stage 3 Staged Rollout (2026-05-20 → 2026-06-02):**
- [ ] Day 1: 5% of institutions (random)
- [ ] Day 3: 25% → Decision point
- [ ] Day 7: 50% → Decision point
- [ ] Day 10: 75% → Decision point
- [ ] Day 14: 100% GA

**Post-Release (2026-06-02+):**
- [ ] Monitor KPIs for 2 weeks
- [ ] Gather feedback + iterate
- [ ] Plan for deprecation of feature flags (Q3 2026)

---

## Key Metrics & Decision Gates

### Stage 1 (Staging) GO Criteria

```
✅ Health check: /health/live returns 200
✅ Latency: P50 < 500ms, P95 < 2s (on mock data)
✅ Error rate: < 0.1%
✅ Compliance officer: "No data leaks detected"
✅ Research team: "UI is intuitive"
✅ All tests: 40 backend, 25 E2E passing
→ Decision: PROCEED to Stage 2
```

### Stage 2 (Partner Canary) GO Criteria

```
Dashboard to monitor per institution:
├─ Finalized cohorts: > 0 (active usage)
├─ Analyzed outcomes: > 0
├─ Guardrail pass rate: > 80%
├─ P95 latency: < 2s (sustained)
├─ Error rate: < 0.5%
├─ User satisfaction: > 4/5 rating (survey)
├─ FERPA violations: 0

✅ All criteria met for 48+ hours?
→ Decision: WIDEN to Stage 3 (25%)
❌ Any criteria missed?
→ Decision: HOLD (gather logs) or ROLLBACK
```

### Stage 3 (Staged Rollout) GO Criteria

**At each % increase:**
```
├─ Latency: P95 still < 2s?
├─ Error rate: still < 0.5%?
├─ Guardrail pass rate: still > 80%?
├─ No new P1 incidents?
├─ Institution feedback: positive?
→ YES to all? Proceed to next stage
→ NO to any? Pause + investigate
```

---

## Adoption Playbook

### Research Team Onboarding

**Timeline:** Before Stage 2, during Stage 1

**Activities:**
1. **Training (2 hours)**
   - F3 conceptual overview (guardrails, limitations)
   - How to interpret confidence bands + guardrails
   - How to use the dashboard (filters, exports)
   - Compliance requirements (FERPA, 7-year retention)

2. **Dry Run (4 hours)**
   - Create a test cohort (playbook selection → finalization)
   - Run analysis on historical data
   - Export outcomes + interpret results
   - Identify questions + pain points

3. **Go-Live Support (2 weeks)**
   - Daily office hours for questions
   - Escalation path (research-lead → SRE on-call)
   - Weekly feedback collection + prioritization

### Institution Adoption Tiers

| Tier | Institution Size | Adoption Speed | Support Level | Timeline |
|------|------------------|----------------|---------------|----------|
| Tier 1 (Pilot) | < 100 students | Canary (manual onboarding) | Premium (daily check-ins) | Stage 2 |
| Tier 2 (Early Adopter) | 100–1K students | Fast (Week 1) | Standard (weekly check-ins) | Stage 3a (5–25%) |
| Tier 3 (Mainstream) | 1K–10K students | Moderate (Weeks 2–4) | Standard (on-demand) | Stage 3b (50–75%) |
| Tier 4 (Late Majority) | 10K+ students | Gradual (Months 1–3) | Self-service | Stage 4 (GA) |

### Adoption Metrics (Success KPIs)

| KPI | Target | Measurement | Owner |
|-----|--------|-------------|-------|
| Activation rate | > 50% at T+30 days | # institutions with ≥ 1 cohort finalized | Product Mgr |
| Feature usage | > 70% create an analysis | # analysis runs / # finalized cohorts | Product Mgr |
| User satisfaction | > 4.2/5.0 | NPS survey | Product Mgr |
| Support resolution | < 24h | Avg time to resolve support ticket | Support Lead |
| Guardrail pass rate | > 80% | # passed / # analyzed | Engineering |

---

## Post-GA Maintenance

### Feature Flag Lifecycle

**Phase 1 (immediately post-GA):** Flags enabled for 100%, remain in code  
**Phase 2 (30 days post-GA):** Code monitoring shows stable behavior  
**Phase 3 (60 days post-GA):** Remove FF checks from code, clean up LaunchDarkly  
**Phase 4 (90 days post-GA):** FF infrastructure decommissioned  

### Hotfix Process

**If P1 bug discovered in production:**

```bash
# 1. Create branch from release tag
git checkout -b hotfix/f3-v1.0.1 release/f3-v1.0.0

# 2. Apply fix + run tests locally
# ... edit code ...
pytest tests/modules/interventions/ -v

# 3. Merge to main + tag release
git merge --ff-only hotfix/f3-v1.0.1
git tag release/f3-v1.0.1
git push origin release/f3-v1.0.1

# 4. Deploy hotfix (rapid path, skip Stage 1–2)
kubectl set image deployment/backend \
  backend=backend:f3-v1.0.1 -n production

# 5. Monitor for 15 minutes, verify fix applied
curl https://api.institution.edu/api/admin/interventions/cohorts/analyze
```

---

## Success Criteria

F3.8 Release & Adoption is **complete** when:

- [ ] Feature flags configured in LaunchDarkly (7 total)
- [ ] Staging environment tested + GO from research team
- [ ] Partner canary (2 institutions) running for 72h, all metrics green
- [ ] Staged rollout progressed to 100% over 2 weeks
- [ ] Adoption KPIs met: activation > 50%, satisfaction > 4.2/5
- [ ] Zero P0 incidents during rollout
- [ ] Adoption playbook executed + research team trained
- [ ] Post-GA maintenance schedule established

---

## References

- **F3 Product Contract:** `docs/F3_PRODUCT_CONTRACT.md` (guardrails, API contract)
- **F3 Observability Spec:** `docs/F3_OBSERVABILITY_SPEC.md` (SLO definitions)
- **F3 Testing Matrix:** `docs/F3_TESTING_MATRIX.md` (pre-release gates)
- **Release process:** `docs/RELEASE_GATE.md`
- **Incident response:** `docs/runbooks/F3_DATA_BREACH_RESPONSE.md`, `docs/runbooks/F3_OUTAGE_RESPONSE.md`
