# PDPL Data Deletion API — Compliance Certification

**Document ID:** GCC-PDPL-DELETION-API-20260501  
**Issue Date:** 2026-05-01  
**Regulation:** PDPL-SA (Personal Data Protection Law, Kingdom of Saudi Arabia)  
**Article:** 14 — Right to Erasure  
**Status:** ✅ IMPLEMENTED & TESTED

---

## Summary

The platform implements the PDPL-SA Article 14 Right-to-Erasure as a production-ready FastAPI endpoint with full audit trail.

## Endpoint

```
DELETE /api/admin/pdpl/users/{user_id}/data
Authorization: Bearer <admin-token>
```

### Response (200 OK)

```json
{
  "receipt_id": "uuid-v4",
  "user_id": "string",
  "tenant_id": 1,
  "action": "personal_data_erased",
  "regulation": "PDPL-SA",
  "article": "14",
  "issued_at": "2026-05-01T12:56:00.000000+00:00",
  "status": "completed"
}
```

## Implementation

| Component | File | Description |
|-----------|------|-------------|
| Router | `backend/app/modules/pdpl/router.py` | FastAPI DELETE endpoint |
| Registration | `backend/app/main.py` | `app.include_router(pdpl_router)` |
| Tests | `backend/tests/test_pdpl_data_deletion.py` | 6 pytest tests |

## Security Controls

- Requires `admin.users.manage` permission (RBAC-enforced)
- Returns 401/403 for unauthenticated/unauthorized requests
- Returns 404 for cross-tenant user access (tenant isolation)
- All erasures produce immutable audit events (action=`pdpl.erasure`)

## Audit Evidence

```
action=pdpl.erasure entity=user result=success
metadata.regulation=PDPL-SA metadata.article=14 metadata.receipt_id=<uuid>
```

## Test Results

```
tests/test_pdpl_data_deletion.py ......  [6/6 PASSED]
```

All 6 tests passing as of 2026-05-01.

---
*Signed by: SBS AI Platform Compliance Automation*
