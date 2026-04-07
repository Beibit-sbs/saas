# Pilot Release Note — AI Engineering Center Platform
**Date:** 2026-04-06
**Version:** Pilot baseline (Alembic head `d4c5e6f7a8b9`)
**Approved by:** Бейбит
**Rollout window:** 06.04.2026 08:14
**Rollback owner:** Бейбит

---

## Executive Summary

The AI Engineering Center university pilot platform is **ready for launch**. All automated quality gates and governance conditions have been verified as of 2026-04-06. The platform delivers a fully tenant-isolated, RBAC-controlled academic operations system covering organizational structure, scheduling, KPI dashboards, automation workflows, AI Copilot, and developer API surfaces.

---

## Gate Evidence Summary

| Gate | Script | Result | Details |
|------|--------|--------|---------|
| Architecture governance | `release_gate.sh` | ✅ PASS | 7 passed |
| Tenant safety | `release_gate.sh` | ✅ PASS | 8 passed |
| Platform regression | `release_gate.sh` | ✅ PASS | 439 passed, 9 skipped |
| Security regression | `release_gate.sh` | ✅ PASS | 42 passed |
| Template validation | `release_gate.sh` | ✅ PASS | 5 passed |
| Migration safety | `release_gate.sh` | ✅ PASS | Head=`d4c5e6f7a8b9`, rollback readiness=PASS |
| Frontend safety | `release_gate.sh` | ✅ PASS | 30 test files, 147 tests |
| Phase B scheduling smoke | `scheduling_phase_b_smoke_check.sh` | ✅ PASS | 4/4 (lesson create/list, attendance upsert/list) |
| Platform smoke (8 surfaces) | `platform_smoke_check.sh` | ✅ PASS | 8/8 (health, outbox, automation, webhooks, KPI, AI Copilot, dev auth, metrics) |
| Preflight safe gate | `university_pilot_safe_gate.sh` | ✅ PASS | 62 tests (tenant isolation + guardrails + readiness + frontend middleware) |

**Full release gate final line:** `[release-gate] PASS: release gate and rollback readiness are green`

---

## Governance Conditions

| Condition | Status | Evidence |
|-----------|--------|---------|
| Role mapping (6 roles) approved | ✅ Done | `PILOT_DEPLOYMENT_CHECKLIST.md` — RBAC mapping configured; safe gate guardrails=7 passed |
| LDAP role mapping validated | ✅ Done | OpenLDAP stack operational; 6 groups + 6 users; validated in safe gate |
| Feature flag matrix reviewed | ✅ Done | `PILOT_FEATURE_FLAG_MATRIX.md`; one runtime flag (`admin.local_users.tab`); all others permission-gated |
| Backup + restore drill | ✅ Done | 2026-04-06 08:30–09:15 UTC; backup=75s/245 MB; restore=125s; RTO well within target |
| Tenant isolation walkthrough | ✅ Done | Automated isolation suite: 8 passed (safe gate) + 8 passed (release gate); no cross-tenant leak |
| Pilot business sign-off | ✅ Approved | approved_by=Бейбит; decision_date=2026-04-06; scope=все |
| Operational contacts confirmed | ✅ Done | Section 13 of `UNIVERSITY_OPERATIONAL_MODEL.md`; incident bridge tested 2026-04-06 10:30 UTC |

---

## What Was Delivered

### Platform Layers Active at Pilot Launch
- **Tenant management** — isolated tenants with per-tenant LDAP, RBAC, settings, and audit log
- **Org structure** — faculty / department / school tree with full RBAC scoping
- **Educational programs + curriculum** — discipline catalog, working curriculum, cohort management
- **Phase B scheduling** — lesson schedule, attendance tracking (upsert/list), instructor roles
- **AI Context Layer + Risk Detection** — intervention case creation, academic risk signals
- **KPI dashboards + Rector view** — 14 KPI cards refreshed on schedule
- **AI Copilot admin answers** — integrated for pilot admin teams
- **Developer platform** — app lifecycle, secret rotation, scoped API access via `/api/dev/*`
- **Automation workflow engine** — rule-based side effects routed through action registry
- **Webhook delivery + retry** — outbox events, retry backlog monitored (backlog=0 at launch)
- **Ops Console v1.1** — available to `ops_engineer` and `platform_admin`
- **Audit log export** — CSV export, filterable by event type and actor

### Role Surface Coverage

| Role | Key surfaces |
|------|-------------|
| `platform_admin` | Cross-tenant operations, secrets rotation, federation, RBAC, ops console |
| `institution_admin` | Tenant RBAC, LDAP config, local users, developer apps, KPI dashboard |
| `academic_admin` | Academic records, enrollments, KPI dashboard (read-only) |
| `it_support` | Backup/restore, job inspection, audit log |
| `developer` | Developer app lifecycle, `/api/dev/*` routes |
| `ops_engineer` | Ops console, worker heartbeat, latency + ops metrics, audit log |

---

## Remaining Actions (Post-Launch)

| Action | Owner | Window |
|--------|-------|--------|
| First-30-min monitoring (§8.2 of Operational Model) | `ops_engineer` | Immediately post-deploy |
| Confirm KPI refresh runs for ≥1 tenant | `ops_engineer` | Within 1 hour of launch |
| Confirm AI Copilot response for ≥1 admin | `institution_admin` | Within 2 hours of launch |
| Webhook retry backlog stays at 0 | `ops_engineer` | Monitor for 48h |
| Post-pilot review (decision: pilot → production) | Бейбит + `platform_admin` | Within 5 business days |

---

## Rollback

If rollback is required:
1. Repoint `current` symlink to previous release.
2. Restart: API → worker → scheduler.
3. Run `bash scripts/platform_smoke_check.sh` — must return 8/8.
4. Open incident timeline and attach request/trace IDs.

**Rollback owner:** Бейбит
**Previous release available:** Yes (confirmed in release gate rollback readiness check)

---

## References

- [PILOT_DEPLOYMENT_CHECKLIST.md](PILOT_DEPLOYMENT_CHECKLIST.md)
- [UNIVERSITY_OPERATIONAL_MODEL.md](UNIVERSITY_OPERATIONAL_MODEL.md) — §8 Incident Response, §11.3 Pre-Pilot Conditions
- [BACKUP_RESTORE_DRILL.md](BACKUP_RESTORE_DRILL.md)
- [PILOT_RBAC_AUDIT.md](PILOT_RBAC_AUDIT.md)
- [PILOT_FEATURE_FLAG_MATRIX.md](PILOT_FEATURE_FLAG_MATRIX.md)
- [GUARDRAILS.md](GUARDRAILS.md)
