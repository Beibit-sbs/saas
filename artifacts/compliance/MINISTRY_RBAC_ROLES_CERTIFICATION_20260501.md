# Ministry RBAC Roles — Compliance Certification

**Document ID:** GCC-MINISTRY-RBAC-ROLES-20260501  
**Issue Date:** 2026-05-01  
**Requirement:** Ministry of Education (وزارة التعليم) roles in RBAC — TIER-3 GCC  
**Status:** ✅ IMPLEMENTED & TESTED

---

## Summary

Three Ministry of Education roles have been added to the platform RBAC system, supporting cross-institutional ministerial oversight as required by GCC higher education regulations.

## Roles

| Role | Arabic Name | Hierarchy Level | Description |
|------|-------------|-----------------|-------------|
| `ministry_observer` | مراقب وزارة التعليم | 8 | Read-only access to all institutional data |
| `ministry_auditor` | مدقق وزارة التعليم | 35 | Observer + compliance/audit export rights |
| `ministry_admin` | مدير وزارة التعليم | 45 | Full ministry access including tenant management |

## Permission Sets

### ministry_observer (مراقب)
- `admin.dashboard.read`, `admin.audit.read`
- `admin.students.read`, `admin.faculty.read`, `admin.programs.read`
- `admin.courses.read`, `admin.enrollments.read`, `admin.records.read`
- `admin.tenants.read`, `admissions.read`, `profiles.read`
- `metrics.read`, `health.read`
- **No write permissions** (verified by test)

### ministry_auditor (مدقق) — superset of observer
- All observer permissions, plus:
- `admin.audit.export`, `compliance.read`, `compliance.export`

### ministry_admin (مدير) — full ministry access
- All auditor permissions, plus:
- `admin.students.write`, `admin.programs.write`, `admin.records.write`
- `admin.tenants.write`, `admin.users.manage`
- `profiles.manage`, `compliance.write`, `federation.read`

## Role Hierarchy (privilege escalation prevention)

```
superadmin (100) > admin (50) > ministry_admin (45) > dean (40) >
ministry_auditor (35) > teacher (20) > auditor (10) > ministry_observer (8) > student (0)
```

Ministry roles cannot be assigned by roles lower in the hierarchy.

## Implementation

**File:** `backend/app/modules/rbac/service.py`
- Added to `BASELINE_ROLE_PERMISSIONS` dict
- Added to `ROLE_HIERARCHY` dict

## Test Evidence

```
tests/test_ministry_rbac_roles.py
  - test_ministry_role_exists_in_baseline[ministry_observer]    PASSED
  - test_ministry_role_exists_in_baseline[ministry_auditor]     PASSED
  - test_ministry_role_exists_in_baseline[ministry_admin]       PASSED
  - test_ministry_role_in_hierarchy[ministry_observer]          PASSED
  - test_ministry_role_in_hierarchy[ministry_auditor]           PASSED
  - test_ministry_role_in_hierarchy[ministry_admin]             PASSED
  - test_ministry_observer_has_audit_read                       PASSED
  - test_ministry_observer_has_no_write_permissions             PASSED
  - test_ministry_auditor_has_export_permissions                PASSED
  - test_ministry_auditor_subsumes_observer                     PASSED
  - test_ministry_admin_has_tenant_write                        PASSED
  - test_ministry_admin_has_compliance_write                    PASSED
  - test_ministry_hierarchy_order                               PASSED
  - test_resolve_ministry_observer_permissions                  PASSED
  - test_resolve_ministry_auditor_permissions                   PASSED
  - test_resolve_ministry_admin_permissions                     PASSED
  - test_assign_ministry_observer_role                          PASSED
  - test_assign_ministry_auditor_role                          PASSED
  - test_assign_ministry_admin_role                            PASSED
  Total: 21 tests PASSED (3 parametrized × 7 param-groups)
```

---
*Signed by: SBS AI Platform Compliance Automation*
