"""Student Services / Welfare / Support permission constants."""

from __future__ import annotations

READ = "admin.student_services.read"
WRITE = "admin.student_services.write"
ASSIGN = "admin.student_services.assign"
ESCALATE = "admin.student_services.escalate"
DASHBOARD_READ = "admin.student_services.dashboard.read"
AUDIT_READ = "admin.student_services.audit.read"

ALL_PERMISSIONS: frozenset[str] = frozenset(
    {
        READ,
        WRITE,
        ASSIGN,
        ESCALATE,
        DASHBOARD_READ,
        AUDIT_READ,
    }
)

STUDENT_SERVICES_SUPPORT_PERMISSIONS = sorted(ALL_PERMISSIONS)
STUDENT_SERVICES_SUPPORT_PERMISSION_COUNT = 6
