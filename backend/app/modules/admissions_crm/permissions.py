"""Admissions CRM Batch 1 permission constants."""

from __future__ import annotations

READ = "admin.admissions_crm.read"
WRITE = "admin.admissions_crm.write"
QUALIFY = "admin.admissions_crm.qualify"
CONVERT = "admin.admissions_crm.convert"
SUBMIT = "admin.admissions_crm.submit"
AUDIT_READ = "admin.admissions_crm.audit.read"

ALL_PERMISSIONS: frozenset[str] = frozenset(
    {
        READ,
        WRITE,
        QUALIFY,
        CONVERT,
        SUBMIT,
        AUDIT_READ,
    }
)

ADMISSIONS_CRM_PERMISSIONS = sorted(ALL_PERMISSIONS)
ADMISSIONS_CRM_PERMISSION_COUNT = 6
