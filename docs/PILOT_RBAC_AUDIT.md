# Pilot RBAC Audit

## Purpose

This audit translates the pilot governance requirement into concrete backend/frontend access surfaces without introducing a new authorization subsystem.

## Current Backend Baseline

Implemented baseline backend roles today:

- `superadmin`
- `admin`
- `auditor`

These roles are seeded in `backend/app/modules/rbac/service.py` and remain the source of truth for current permission enforcement.

## Required Pilot Named Roles

The pilot requires the following named operational roles:

- `platform_admin`
- `institution_admin`
- `academic_admin`
- `it_support`
- `developer`
- `ops_engineer`

## Audit Finding

The named pilot roles above are not yet first-class backend seed roles. Current enforcement can still satisfy the pilot if identity-provider groups or local role assignment workflows map these names onto the existing backend permission sets below.

This is acceptable for pilot readiness, but it is a governance gap rather than a code-path failure.

## Recommended Pilot Mapping

| Pilot role | Current backend role/profile | Intended scope | Notes |
| --- | --- | --- | --- |
| `platform_admin` | `superadmin` | cross-tenant platform administration | only role that should approve cross-tenant or federation-wide actions |
| `institution_admin` | `admin` | single tenant administrative control | no cross-tenant escalation; may manage developer apps and federation config within tenant context |
| `academic_admin` | custom tenant role derived from `admin` subset | academic records, students, courses, enrollments, KPI review | should not manage backups, integrations, or tenant-level governance |
| `it_support` | custom tenant role derived from audit + jobs/backup subset | incident handling, jobs, operational triage | should not mutate academic data except documented recovery actions |
| `developer` | custom tenant role using `developer_platform.read/write` | developer app lifecycle and API onboarding | should not have tenant admin, backup, or federation write access |
| `ops_engineer` | custom platform role using dashboard/audit/jobs/backup plus ops console visibility | worker/webhook/ops troubleshooting | should not own tenant academic mutations |

## Access Surface Review

Admin and console surfaces relevant to the pilot:

| Surface | Primary permission signal | Pilot role expectation |
| --- | --- | --- |
| Ops Console | frontend `ops.read` / `ops.write` | `ops_engineer`, `platform_admin` |
| Developer Apps console | `developer_platform.read` / `developer_platform.write` | `developer`, `institution_admin`, `platform_admin` |
| Federation console | `federation.read` / `federation.write` | `institution_admin`, `platform_admin` |
| KPI dashboard / rector view | dashboard + tenant academic reads | `academic_admin`, `institution_admin`, `platform_admin` |
| Backup / jobs operations | `admin.backup.manage`, `admin.jobs.read`, `admin.jobs.write` | `it_support`, `ops_engineer`, `platform_admin` |

## Cross-Tenant Escalation Review

Verified pilot expectation:

- standard tenant-scoped admin flows must not read or mutate another tenant's data
- cross-tenant queries remain restricted to platform-level roles and explicit platform endpoints
- developer app listings, webhook subscriptions, analytics views, and tenant data must stay tenant-filtered by default

Evidence already present in the repository:

- tenant safety audit tests for platform components
- tenant isolation tests for university, audit, jobs, and RBAC flows

## Pilot Approval Conditions

Before pilot launch, complete all of the following:

1. Map identity-provider or local user groups to the six named pilot roles.
2. Bind each named pilot role to one of the current backend permission profiles listed above.
3. Confirm that only `platform_admin` retains cross-tenant operational approval paths.
4. Confirm frontend navigation exposure matches the role matrix in a staging login walkthrough.
5. Record the mapping in the deployment checklist and change-management artifact.

## Residual Risks

- backend does not yet seed the named pilot roles directly
- frontend ops-console visibility uses `ops.read` / `ops.write`, while backend baseline roles do not yet expose an equivalent first-class permission pair
- until role mapping is recorded operationally, authorization intent depends on human procedure rather than explicit seeded role names