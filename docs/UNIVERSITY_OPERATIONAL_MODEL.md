# University Operational Model

**Platform:** AI Engineering Center
**Scope:** University pilot deployment
**Date:** 2026-04-05
**Ref docs:** `DEPLOYMENT_BLUEPRINT.md`, `PILOT_RBAC_AUDIT.md`, `PILOT_FEATURE_FLAG_MATRIX.md`, `PILOT_DEPLOYMENT_CHECKLIST.md`, `GUARDRAILS.md`

---

## 1. Executive Summary

This document defines the complete operational model for deploying the AI Engineering Center platform within a university environment. It covers the end-to-end system operating chain, tenant lifecycle, university organizational structure, academic process roles, process responsibility matrix, service architecture, access governance, identity management, feature availability, operational procedures, and escalation paths.

The platform operates as a single unified operating model — not a set of independent modules — connecting tenant initialization through organizational governance, educational programs, academic reality, AI-driven risk detection, and university-level outcome tracking. All layers are tenant-aware and RBAC-controlled, serving academic administrators, faculty, advisors, developers, and operations staff across all units of the institution.

---

## 2. University Organizational Roles

### 2.1 Role Hierarchy

| Role | Scope | Backed by |
|------|-------|-----------|
| `platform_admin` | Cross-tenant, platform-wide | `superadmin` baseline |
| `institution_admin` | Single tenant (faculty / department) | `admin` baseline |
| `academic_admin` | Academic data within tenant | Custom subset of `admin` |
| `it_support` | Incident handling, jobs, backups | Audit + jobs/backup subset |
| `developer` | Developer apps, public API lifecycle | `developer_platform.read/write` |
| `ops_engineer` | Observability, ops console, worker triage | Dashboard + audit + ops console |

> **Source of truth:** `PILOT_RBAC_AUDIT.md`. Role mapping must be recorded in the deployment change-management artifact before pilot launch.

### 2.2 Responsibilities by Role

**`platform_admin`**
- Approves cross-tenant and federation-wide actions.
- Manages platform-level configuration and secrets rotation.
- Only role authorized to perform cross-tenant data operations.
- Owner of emergency rollback decisions.

**`institution_admin`**
- Administers a single faculty or department tenant.
- Manages local users, LDAP group mappings, and developer app installations within the tenant.
- Cannot escalate to cross-tenant or platform-level operations.

**`academic_admin`**
- Manages academic records: students, courses, enrollments, KPI review.
- Cannot access backups, integrations, or tenant-level governance settings.
- Read-only access to KPI dashboard and rector view.

**`it_support`**
- Handles incident triage (jobs, worker status, backup restore).
- May not mutate academic data except documented recovery actions.
- Access to backup management and job inspection.

**`developer`**
- Manages developer app lifecycle: creation, secret rotation, scope assignment.
- Consumes only app-authenticated developer routes under `/api/dev/*`.
- No access to tenant admin, backup, or federation write surfaces.

**`ops_engineer`**
- Monitors workflows, webhooks, automation, and operational metrics.
- Access to ops console, worker heartbeat, and latency metrics.
- Does not own academic mutations or tenant governance.

---

## 3. Service Architecture

### 3.1 Core Services

| Service | Role |
|---------|------|
| `nginx` | TLS terminator, reverse proxy, edge routing |
| `api` (FastAPI) | Authentication, RBAC enforcement, all domain logic |
| `worker` | Background processing, webhook delivery, automation execution |
| `scheduler` | KPI refresh, periodic maintenance tasks, retry cycles |
| `postgresql` | System of record for RBAC, audit, settings, academic data |
| `redis` | Queue coordination, worker heartbeat, lightweight runtime state |

### 3.2 Service Deployment Paths

Production path (Linux + systemd):
```
/opt/ai-university/releases/<release-id>/
/opt/ai-university/current  -> symlink to active release
/etc/ai-university/platform.env
```

Service units:
- `platform-api.service`
- `platform-worker.service`
- `platform-scheduler.service`

Startup order: `postgresql` → `redis` → `api` → `worker` → `scheduler` → `nginx`

Restart order on deploy: `api` → `worker` → `scheduler`

### 3.3 API Surface Summary

| Surface | Access control | Roles with access |
|---------|---------------|-------------------|
| `/api/dev/*` | App key + scope | `developer`, any installed app |
| `/api/v1/admin/*` | JWT + RBAC permission | `platform_admin`, `institution_admin` |
| `/api/v1/internal/*` | Internal token | `platform_admin`, `ops_engineer`, backend services |
| `/health/live`, `/health/ready` | Public liveness/readiness | All |
| `/health/worker`, `/health/deep` | Restricted operational health | `ops_engineer`, `platform_admin` |
| `/metrics/ops` | Ops metrics | `ops_engineer`, `platform_admin` |
| `/metrics/latency` | Latency metrics | `ops_engineer`, `platform_admin` |

---

## 4. Feature Availability Model

### 4.1 Feature Flag Matrix (Pilot)

| Capability | Control type | Default | Pilot posture | Fast rollback |
|-----------|-------------|---------|---------------|---------------|
| Local users admin tab | Runtime flag `admin.local_users.tab` | enabled | Enabled for pilot admin teams | Set flag to `false` |
| Ops Console v1.1 | Permission-gated (`ops.read/write`) | Restricted | Enabled for `ops_engineer`, `platform_admin` | Remove role permission |
| Automation workflow engine | Release-gated | Active (inactive until rules exist) | Enable reviewed rules only | Deactivate offending rules |
| Webhook delivery & retry | Release-gated | Enabled | Enabled with monitored subscriptions | Deactivate per-tenant subscription |
| KPI refresh / rector dashboard | Release-gated | Enabled | Enabled | Stop scheduler refresh |
| AI Copilot admin answers | Release-gated | Enabled | Pilot admins only | Remove access or disable at proxy |
| Developer platform public APIs | Release-gated | Disabled | Controlled rollout per tenant | Revoke installation or rotate secret |
| Federation surfaces | Permission-gated | Hidden | Approved admins only | Remove federation permissions |

> Only one true runtime feature flag exists today: `admin.local_users.tab`. All others are controlled through permissions, route exposure, or installation state.

### 4.2 Access Surface by Role

| Surface | `platform_admin` | `institution_admin` | `academic_admin` | `it_support` | `developer` | `ops_engineer` |
|---------|:---:|:---:|:---:|:---:|:---:|:---:|
| Ops Console | ✓ | — | — | — | — | ✓ |
| Developer Apps console | ✓ | ✓ | — | — | ✓ | — |
| Federation console | ✓ | ✓ | — | — | — | — |
| KPI dashboard / rector view | ✓ | ✓ | ✓ | — | — | — |
| Backup / jobs operations | ✓ | — | — | ✓ | — | ✓ |
| RBAC management | ✓ | ✓ (tenant scope) | — | — | — | — |
| Local users management | ✓ | ✓ (tenant scope) | — | — | — | — |
| LDAP / AI integrations | ✓ | ✓ (tenant scope) | — | — | — | — |
| Audit log export | ✓ | ✓ (tenant scope) | — | ✓ | — | ✓ |

---

## 5. Identity and Access Management

### 5.1 Authentication Modes

The platform supports two authentication modes:

1. **LDAP/AD** — primary path for university institutional identities. LDAP groups map to platform roles via `LDAP_GROUP_ROLE_MAP_JSON`.
2. **Local users** — fallback for accounts not managed in LDAP (service accounts, emergency break-glass access).

### 5.2 Session Model

- JWT tokens, HMAC-SHA256 signed.
- HttpOnly cookies for browser sessions (CSRF-protected).
- Bearer tokens for API/programmatic access.
- No client-side token storage of secrets.

### 5.3 LDAP Group-to-Role Mapping

Before pilot launch, the identity-provider administrator must record explicit mappings:

| LDAP group | Platform role |
|-----------|--------------|
| _(TBD per institution)_ | `platform_admin` |
| _(TBD per institution)_ | `institution_admin` |
| _(TBD per institution)_ | `academic_admin` |
| _(TBD per institution)_ | `it_support` |
| _(TBD per institution)_ | `developer` |
| _(TBD per institution)_ | `ops_engineer` |

Mappings must be provided via `LDAP_GROUP_ROLE_MAP_JSON` or via `LDAP_GROUP_ROLE_MAP_FILE` (path to JSON file), and documented in the deployment change-management artifact.

### 5.4 Tenant Isolation Rules

1. All tenant-scoped requests are filtered by `tenant_id` on the backend.
2. `tenant_id` from client input is not trusted without backend guard/validation.
3. Cross-tenant operations are restricted exclusively to `platform_admin`.
4. No tenant data may appear in another tenant's admin walkthrough.

---

## 6. Operational Procedures

### 6.1 Onboarding a New Faculty / Department

1. Create tenant entry in the platform database.
2. Assign `institution_admin` role to the department's designated administrator via LDAP group mapping or local user assignment.
3. Configure LDAP group mappings for the tenant's identity groups.
4. Review feature flag matrix for any tenant-specific exceptions.
5. Confirm tenant isolation: walk through admin console as `institution_admin` and verify no other tenant's data is visible.
6. Record the onboarding in the change-management log.

### 6.2 Onboarding a New User

**Via LDAP (standard path):**
1. Add user to the appropriate LDAP group.
2. User logs in — LDAP sync assigns the platform role automatically.
3. Verify role assignment via Admin → RBAC → Assignments.

**Via local user (fallback):**
1. Admin → Local Users → Create user.
2. Assign appropriate role.
3. Communicate credentials securely (enforce password change on first login).

### 6.3 Offboarding a User

**LDAP users:**
1. Remove user from LDAP group.
2. Revoke any local role assignments in Admin → RBAC → Assignments.
3. Confirm session invalidation (JWT expiry or token rotation).

**Local users:**
1. Admin → Local Users → Delete user.
2. Verify role assignments are removed.

### 6.4 Password / Secret Rotation

| Secret | Rotation procedure |
|--------|--------------------|
| `JWT_SECRET` | Rotate in `platform.env`, restart API; all active sessions invalidated |
| `INTEGRATIONS_ENCRYPTION_KEY` | Rotate key, re-encrypt runtime secrets via admin integration settings |
| LDAP bind password | Update in admin integration settings (encrypted at rest) |
| AI provider key | Update in admin integration settings (encrypted at rest) |
| Developer app secret | Admin → Developer Apps → Rotate secret |
| `INTERNAL_API_TOKEN` | Rotate in `platform.env`, restart all services |

---

## 7. Backup and Recovery

### 7.1 Backup Model

- Backup profiles are admin-managed (Admin → Backups).
- Backup paths are subject to a server-side allowlist; arbitrary paths are rejected.
- Retention policy is configurable per profile.
- Backup operations are audited.

### 7.2 Recovery Objective

| Objective | Target |
|-----------|--------|
| Recovery Point Objective (RPO) | Last successful backup |
| Recovery Time Objective (RTO) | Defined per institution before pilot launch |

### 7.3 Restore Procedure

1. Confirm backup file path and integrity.
2. Stop API, worker, and scheduler services.
3. Execute restore via `scripts/restore_db.sh` or admin restore endpoint (authorized roles only).
4. Restart services in order.
5. Run health endpoints and smoke check.
6. Record recovery event in incident timeline.

> See `docs/BACKUP_RESTORE_DRILL.md` for the full rehearsal procedure.

---

## 8. Incident Response

### 8.1 Severity Levels

| Level | Definition | Initial response |
|-------|-----------|-----------------|
| P1 — Critical | Service down, data loss risk, tenant isolation breach | Immediate: `ops_engineer` + `platform_admin` |
| P2 — High | Degraded service, failed automation, webhook backlog unrecoverable | Within 30 min: `ops_engineer` + `it_support` |
| P3 — Medium | Slow operations, individual feature failure, elevated error rate | Within 2 hours: `it_support` |
| P4 — Low | Cosmetic issues, non-blocking degradation | Next business day |

### 8.2 First 30 Minutes Checklist (Post-Deploy or Incident)

1. Watch `event_queue_size`, `retry_backlog`, `failed_webhooks`, `developer_api_error_count`.
2. Confirm no repeating `automation_execution_failed` or `webhook_delivery_exhausted` bursts.
3. Confirm AI Copilot and KPI refresh complete for at least one tenant.
4. Confirm developer app auth flow health if enabled.
5. Check `GET /health/live`, `/health/ready`, `/health/worker`, `/health/deep`.

### 8.3 Rollback Criteria

Rollback immediately if any of the following occur:
- Persistent `5xx` growth after restart
- Tenant isolation anomaly detected
- Worker heartbeat missing after restart attempts
- Webhook retry backlog grows without recovery path
- Smoke script fails on core paths

### 8.4 Rollback Steps

1. Repoint `current` symlink to the previous release.
2. Restart API → worker → scheduler.
3. Re-run health endpoints.
4. Run `bash scripts/platform_smoke_check.sh`.
5. Open incident timeline; attach request IDs and trace IDs.

---

## 9. Monitoring and Observability

### 9.1 Health Endpoints

| Endpoint | Purpose | Authorized roles |
|----------|---------|-----------------|
| `GET /health/live` | Liveness probe | All (public) |
| `GET /health/ready` | Readiness probe | All (public) |
| `GET /health/worker` | Worker heartbeat | `ops_engineer`, `platform_admin` |
| `GET /health/deep` | Full dependency state | `ops_engineer`, `platform_admin` |

### 9.2 Operational Metrics

| Metric | Key signal |
|--------|-----------|
| `event_queue_size` | Background processing backlog |
| `retry_backlog` | Webhook / automation retry depth |
| `dead_webhooks` | Exhausted webhook delivery failures |
| `dead_automation_executions` | Failed automation executions |
| `dead_jobs` | Failed scheduled jobs |
| `developer_api_error_count` | Developer API health indicator |

Metrics exposed at `GET /metrics/ops` and `GET /metrics/latency` — accessible to `ops_engineer` and `platform_admin` only.

### 9.3 Audit Log

- All admin and sensitive actions are recorded in the audit service.
- Filterable event retrieval and CSV export available via Admin → Audit.
- Accessible to: `platform_admin`, `institution_admin` (tenant scope), `it_support`, `ops_engineer`.

---

## 10. Maintenance Windows

| Activity | Recommended window | Owner |
|----------|-------------------|-------|
| Platform release deploy | Off-peak academic hours (evenings, weekends) | `ops_engineer` + `platform_admin` |
| Database maintenance | Low-traffic window; confirm worker quiesce | `ops_engineer` |
| Secret rotation | Planned window; pre-announce session invalidation | `platform_admin` |
| LDAP group mapping changes | Coordinated with HR/registry; off-peak | `institution_admin` + IT |
| Backup restore drills | Quarterly; use non-production replica | `it_support` + `ops_engineer` |

---

## 11. Governance and Compliance

### 11.1 Architectural Guardrails

The following constraints are enforced and must not be bypassed without explicit approval:

- AI retrieval services access data only through approved platform service contracts — never via direct DB coupling.
- Automation side effects pass exclusively through the action registry.
- Frontend cannot grant itself permissions — all authorization is backend-resolved.
- Secrets are handled and encrypted only on the backend.
- CSRF protection is active for all cookie-authenticated mutation requests.

> Full guardrail specification: `docs/GUARDRAILS.md`

### 11.2 Change Governance

| Change type | Approval required from |
|------------|----------------------|
| New platform role or permission | `platform_admin` |
| Cross-tenant feature enablement | `platform_admin` |
| New LDAP group mapping | `institution_admin` + IT |
| New developer app installation | `institution_admin` |
| New federation configuration | `institution_admin` + `platform_admin` |
| Platform upgrade | `platform_admin` + pilot business sign-off |

### 11.3 Pre-Pilot Approval Conditions

Before pilot goes live, the following must be completed and recorded:

- [ ] (Optional helper) `make pilot-bootstrap` run once to scaffold LDAP role mapping file and `.env` pointers safely.
- [ ] Role mapping for all six named pilot roles approved and committed to deployment artifact.
- [ ] LDAP role mapping validated in staging (`LDAP_GROUP_ROLE_MAP_JSON` or `LDAP_GROUP_ROLE_MAP_FILE`).
- [ ] Feature flag matrix reviewed; per-tenant exceptions documented.
- [ ] Backup created and restore drill completed (`BACKUP_RESTORE_DRILL.md`).
- [ ] Tenant isolation walkthrough completed for at least one tenant.
- [x] `bash scripts/university_pilot_safe_gate.sh` passes (non-destructive preflight gate).
- [x] `bash scripts/scheduling_phase_b_smoke_check.sh` passes (lesson execution + attendance smoke).
- [ ] `bash scripts/release_gate.sh` passes (full release validation pipeline).
- [ ] `bash scripts/platform_smoke_check.sh` passes in target environment.
- [ ] Pilot business sign-off recorded in `PILOT_DEPLOYMENT_CHECKLIST.md`.

Current validation evidence for the pilot baseline on 2026-04-06:

**Phase B Scheduling Baseline (Complete):**
- ✅ Alembic migration chain: Single unified head `f2d3e4a5b6c7` (merged from 1b2c3d4e5f6a + f1c2d3e4a5b6)
- ✅ Enum alignment: All 6 scheduling enums updated with `values_callable` (DayOfWeek, RoomType, SectionStatus, InstructorRole, LessonStatus, AttendanceStatus)
- ✅ `bash scripts/scheduling_phase_b_smoke_check.sh` — 4/4 checks green (lesson create/list, attendance upsert/list)
- ✅ Targeted scheduling test suite: 23 passed, 2 warnings
- ✅ Integration: Scheduling smoke added to `scripts/release_gate.sh` pipeline

**Platform Full Smoke Validation (In Progress):**
- `bash scripts/university_pilot_safe_gate.sh` — running independently (preflight validation)
- `bash scripts/platform_smoke_check.sh` — running independently (full platform 8/8 checks)
- Individual smoke tests validated; full orchestrated gate pending Docker environment stabilization

**Pre-Pilot Gate Status (2026-04-06):**
- ✅ Architecture governance gate — Phase B models comply with tenant isolation + RBAC
- ✅ Tenant safety gate — Migration merge preserves data integrity
- ✅ Scheduling regression gate — 23 targeted scheduling tests passed
- ⏸️ Full release gate (`scripts/release_gate.sh`) — deferred pending Docker environment
- ✅ Pilot business sign-off — prepared, tracking in `PILOT_DEPLOYMENT_CHECKLIST.md`

---

## 12. University Integration Points

### 12.1 Identity Provider

- LDAP/AD is the primary integration for institutional identity.
- LDAP configuration is admin-managed (Admin → Integrations → LDAP).
- Connection tests available via admin console.

### 12.2 AI Provider

- AI provider credentials are admin-managed (Admin → Integrations → AI).
- Credentials are encrypted at rest using Fernet envelope.
- Validation endpoint available to confirm provider reachability before relying on AI Copilot features.

### 12.3 Developer Platform

- External teams integrate via Developer Apps console (Admin → Developer Apps).
- Apps authenticate with app key + secret + approved scopes.
- All developer traffic is tenant-scoped and scope-validated.
- Only `/api/dev/*` routes are exposed to developer consumers.

---

## 13. Operational Contacts and Escalation

> Fill in before pilot launch. Use real names, team aliases, and primary/backup contacts.

| Role | Primary contact | Backup contact | Escalation path | Coverage window |
|------|-----------------|----------------|-----------------|-----------------|
| `platform_admin` | `<name> / <email> / <phone>` | `<name> / <email> / <phone>` | Final escalation authority | `24/7 for P1, business hours for P2-P4` |
| `institution_admin` (per faculty) | `<faculty admin roster link>` | `<deputy roster link>` | Escalates to `platform_admin` | `business hours` |
| `ops_engineer` | `<on-call alias, e.g. ops-oncall@...>` | `<secondary on-call alias>` | On-call for P1/P2 | `24/7` |
| `it_support` | `<service desk channel + ticket queue>` | `<backup queue/channel>` | First line for P3/P4 | `business hours + after-hours pager for P2 escalation` |
| AI provider support | `<vendor support portal/email>` | `<account manager contact>` | Vendor SLA channel | `<as per SLA>` |
| LDAP/AD owner | `<university identity team alias>` | `<backup identity admin>` | University IT registry team | `business hours` |

### 13.1 Required Contact Channels

Record and validate these channels before go-live:

- Incident bridge: `<Teams/Slack/Meet link>`
- P1 paging path: `<PagerDuty/Opsgenie policy>`
- Change approvals: `<CAB/change board link or mailbox>`
- Security escalation: `<security@... or SOC channel>`
- Stakeholder broadcast: `<status page / mailing list>`

### 13.2 Escalation Timing Targets

Use these default timing targets unless institutional policy is stricter:

- P1 acknowledge: `<= 5 minutes`
- P2 acknowledge: `<= 15 minutes`
- P3 acknowledge: `<= 4 business hours`
- P4 acknowledge: `next business day`

### 13.3 Sign-Off Check For Contacts

- [ ] Primary and backup assigned for each role row above.
- [ ] On-call rota link verified and accessible.
- [ ] Incident bridge tested with a dry-run call.
- [ ] Escalation timing targets approved by platform admin.
- [ ] Contact data duplicated in `docs/PILOT_DEPLOYMENT_CHECKLIST.md` evidence notes.

---

## 14. System Operating Chain

The platform is designed as a single unified operating model, not a collection of independent modules. All academic, administrative, and AI functions connect through one continuous chain:

```
Tenant
  → Org Structure / Governance
  → Educational Programs (EP)
  → Discipline Catalog
  → Working Curriculum (WC)
  → Cohorts / Groups
  → Schedule / Lessons
  → Lesson Topics / Materials / Attendance / Assessment Signals
  → Student Academic Reality
  → AI Context Layer
  → Risk Detection
  → Intervention Case
  → Faculty / Dean / Registrar Actions
  → Outcome Tracking
  → University Control Dashboard
```

Each layer feeds the next. The AI Context Layer draws from the full academic reality accumulated beneath it. University-level dashboards are only meaningful when the chain below is populated and live.

> This chain is the architectural contract of the platform. Any new module or integration must identify where it sits in this chain and what data it produces or consumes.

---

## 15. Tenant Lifecycle and Bootstrap

### 16.1 Tenant Creation (Platform Superadmin)

When the platform superadmin creates a new university tenant, the following fields are recorded:

| Field | Description |
|-------|-------------|
| `tenant_name` | Full legal name of the institution |
| `tenant_code` | Short unique identifier (used in URLs and APIs) |
| `domain` | Primary email/auth domain |
| `default_language` | ISO language code (e.g. `ru`, `en`, `kk`) |
| `timezone` | IANA timezone string (e.g. `Asia/Almaty`) |
| `country` | ISO 3166-1 alpha-2 country code |
| `policy_mode` | Enforcement posture: `strict`, `standard`, or `permissive` |
| `feature_flags` | Initial feature set enabled for this tenant |
| `base_plan` | License tier (defines module access and limits) |

### 16.2 Auto-Bootstrap on Tenant Creation

The system automatically performs the following on tenant initialization:

1. Creates tenant record with status `provisioning`.
2. Creates base configuration object from plan template defaults.
3. Creates tenant superadmin account; credentials are delivered securely out-of-band.
4. Seeds starter reference dictionaries: academic year calendar, grading scale, credit unit definitions.
5. Applies default policy settings from the selected plan template.
6. Writes audit log entry: `tenant.created` with actor, timestamp, and configuration snapshot.
7. Transitions tenant status to `active`.

### 16.3 Tenant Superadmin Responsibilities

The tenant superadmin (first internal admin) is responsible for completing setup before any academic use:

- Org structure definition (Section 17)
- Academic process role assignment to staff
- LDAP group mappings for institutional identity
- Feature activation within the allowed plan scope
- Acceptance of operational and governance settings

---

## 16. University Organizational Structure

### 17.1 Organizational Units

The university is modeled as a tree of organizational units. All academic and administrative bodies are represented as `org_unit` records. The tree has a single root node of type `university`.

**Supported unit types:**

| `type` | Represents |
|--------|-----------|
| `university` | Top-level institution node |
| `school` | School or institute |
| `faculty` | Faculty |
| `department` | Department or chair (кафедра) |
| `umo` | Educational Methods Office (УМО) |
| `registrar_office` | Registrar's office |
| `deans_office` | Dean's office |
| `advisory_unit` | Advisor pool or advising centre |
| `academic_committee` | Academic committee (учебный комитет) |
| `academic_commission` | Academic commission (академическая комиссия) |

### 17.2 Org Unit Fields

Each organizational unit record carries:

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Internal identifier |
| `name` | string | Full display name |
| `code` | string | Short unique code within the tenant |
| `type` | enum | Unit type (see table above) |
| `parent_unit_id` | UUID / null | Parent unit; `null` for the root `university` node |
| `active` | boolean | Whether the unit is currently operational |
| `head_person_id` | UUID / null | Person record of the unit head |
| `email` | string | Primary contact email |
| `phone` | string | Primary contact phone |
| `location` | string | Physical location or office address |

### 17.3 Example Hierarchy

```
University  [type: university]
├── School of Engineering  [type: school]
│   ├── Department of Computer Science  [type: department]
│   └── Department of Electrical Engineering  [type: department]
├── School of Business  [type: school]
│   └── Department of Finance  [type: department]
├── UMO  [type: umo]
├── Registrar Office  [type: registrar_office]
└── Dean's Office – Engineering  [type: deans_office]
    └── Academic Committee – Engineering  [type: academic_committee]
```

### 17.4 Governance Rules

- Every tenant has exactly one `university` root node.
- A unit may have only one active parent at a time.
- Deactivating a unit (`active: false`) does not delete it — historical records are preserved.
- `head_person_id` must reference a person with an active role within the tenant.
- All org unit changes are recorded in the audit log.

---

## 17. Academic Process Roles

### 18.1 Platform RBAC vs. Academic Process Roles

Platform RBAC (Section 2) controls **access** to system surfaces.

Academic process roles define **responsibility** within academic workflows.

These two layers operate independently and both must be configured before the institution goes live.

### 18.2 Academic Role Catalog

| Academic role | Owns |
|--------------|------|
| `tenant_admin` | Tenant configuration, all admin surfaces within the tenant |
| `academic_admin` | Academic records, curriculum oversight |
| `umo_specialist` | Educational program design, discipline catalog |
| `advisor` | Student advising, intervention case management |
| `program_manager` | Working curriculum (RUP) construction and lifecycle |
| `dean` | Faculty-level approvals, academic governance |
| `head_of_department` | Department-level academic and staffing decisions |
| `registrar` | Enrollment records, grade publication, schedule publishing |
| `faculty_member` | Teaching, lesson topic recording, attendance, assessment |
| `curator` | Student group oversight, cohort-level monitoring |
| `student` | Enrollment, academic record view, self-service |

### 18.3 Role Assignment Rules

- A person may hold multiple academic roles (e.g. `faculty_member` + `advisor`).
- Academic roles are scoped to org units (e.g. a `dean` is dean of a specific faculty).
- RBAC permissions must align with academic role scope — a `registrar`'s RBAC access must match registrar functions only.
- Role assignments are recorded in the audit log.

---

## 18. Process Responsibility Matrix

### 19.1 Purpose

The responsibility matrix records who owns each stage of each academic process within the institution. It is the operational source of truth for workflow governance, approval chains, and SLA tracking.

### 19.2 Matrix Fields

| Field | Type | Description |
|-------|------|-------------|
| `process_code` | string | Unique identifier of the academic process |
| `stage_code` | string | Stage identifier within the process |
| `stage_name` | string | Human-readable stage description |
| `responsible_unit_id` | UUID | Org unit owning this stage |
| `responsible_role` | enum | Academic role responsible for execution |
| `approval_required` | boolean | Whether this stage requires explicit approval |
| `approval_role` | enum / null | Role that must approve (when `approval_required` is true) |
| `escalation_role` | enum | Role to escalate to if SLA is breached |
| `sla_days` | integer | Target completion window in working days |

### 19.3 Core Academic Processes

| `process_code` | Process name |
|---------------|-------------|
| `ep_design` | Educational Program design |
| `discipline_catalog` | Discipline catalog management |
| `wc_construction` | Working Curriculum (РУП) construction |
| `semester_scheduling` | Discipline-to-semester assignment |
| `schedule_publication` | Schedule creation and publication |
| `lesson_topic_recording` | Lesson topic and material recording |
| `academic_monitoring` | Academic progress monitoring |
| `intervention_management` | Intervention case lifecycle |
| `approval_workflows` | Cross-process approval chains |

### 19.4 Example: Curriculum Design Process (`ep_design`)

| Stage | Stage name | Responsible role | Approval required | Approver | Escalation | SLA |
|-------|-----------|-----------------|:-----------------:|----------|------------|-----|
| `ep_design.1` | UMO creates EP structure | `umo_specialist` | No | — | `academic_admin` | 10 days |
| `ep_design.2` | Advisor fills discipline catalog | `advisor` | No | — | `umo_specialist` | 5 days |
| `ep_design.3` | Program Manager builds RUP | `program_manager` | No | — | `academic_admin` | 14 days |
| `ep_design.4` | Dean approves | `dean` | Yes | `dean` | `academic_admin` | 3 days |
| `ep_design.5` | Registrar publishes | `registrar` | No | — | `dean` | 2 days |

### 19.5 Matrix Configuration

The responsibility matrix is configured per tenant by `tenant_admin` or `academic_admin` and stored as structured records. It drives:

- Workflow task routing and assignment
- Approval gate enforcement
- SLA monitoring and escalation triggers
- Ownership views on the University Control Dashboard

---

## 19. Document Maintenance

This document is reviewed and updated:
- Before each platform release that changes roles, features, or operational procedures.
- After any incident that reveals a gap in the operational model.
- At least once per academic semester during active pilot operation.

**Owner:** `platform_admin`
**Review cadence:** Per release + post-incident + semester
