# 7-Year Audit Retention — Compliance Certification

**Document ID:** GCC-AUDIT-RETENTION-7Y-ENFORCEMENT-20260501  
**Issue Date:** 2026-05-01  
**Regulation:** PDPL-SA / GCC-SEC-003  
**Requirement:** Minimum 7-year retention of all audit events  
**Status:** ✅ CONFIGURED & ENFORCED

---

## Summary

The platform enforces a 7-year (2,555-day) minimum retention period on all audit events stored in `app_audit_events`.

## Implementation

### Database Migration

**File:** `backend/alembic/versions/vm01wx23yz45_add_7y_audit_retention_policy.py`

Changes applied:
1. `COMMENT ON TABLE app_audit_events` — documents the policy
2. `retention_expires_at` computed column (`timestamp + 7 years`)
3. `ix_audit_events_retention_expires_at` partial index for efficient purge
4. `audit_enforce_7y_retention()` SQL function (SECURITY DEFINER)
5. pg_cron job `audit-7y-retention-purge` (nightly at 02:00 UTC, when pg_cron available)

### Enforcement Function

```sql
SELECT * FROM audit_enforce_7y_retention();
-- Returns: (deleted_count BIGINT, purge_before TIMESTAMPTZ)
-- Only removes rows older than 7 years
-- Safe to call multiple times (idempotent)
```

### Retention Logic

```
retention_expires_at = audit_event.timestamp + INTERVAL '7 years'
Rows with retention_expires_at > NOW() are NEVER deleted
```

## Compliance Evidence

| Control | Implementation | Status |
|---------|----------------|--------|
| Policy declaration | TABLE COMMENT | ✅ |
| Computed expiry field | `retention_expires_at` column | ✅ |
| Purge index | `ix_audit_events_retention_expires_at` | ✅ |
| Enforcement function | `audit_enforce_7y_retention()` | ✅ |
| Scheduled purge | pg_cron `0 2 * * *` | ✅ (when available) |
| Downgrade-safe | `downgrade()` function in migration | ✅ |

## Prior Artifact

Policy documentation was previously captured in:
`artifacts/compliance/GCC_AUDIT_TRAIL_RETENTION_POLICY_7Y_20260501.md`

This artifact adds the **enforcement implementation** proof.

---
*Signed by: SBS AI Platform Compliance Automation*
