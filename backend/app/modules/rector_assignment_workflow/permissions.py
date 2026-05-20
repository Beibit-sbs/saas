"""Rector Assignment Workflow — Permission constants."""

from __future__ import annotations

CREATE = "admin.rector_assignments.create"
READ = "admin.rector_assignments.read"
READ_ALL = "admin.rector_assignments.read_all"
READ_DEPARTMENT = "admin.rector_assignments.read_department"
ASSIGN = "admin.rector_assignments.assign"
ACCEPT = "admin.rector_assignments.accept"
REPORT_SUBMIT = "admin.rector_assignments.report.submit"
REPORT_REVIEW = "admin.rector_assignments.report.review"
EVIDENCE_ATTACH = "admin.rector_assignments.evidence.attach"
COMMENT = "admin.rector_assignments.comment"
STATUS_CHANGE = "admin.rector_assignments.status.change"
COMPLETE = "admin.rector_assignments.complete"
RETURN = "admin.rector_assignments.return"
ESCALATE = "admin.rector_assignments.escalate"
CANCEL = "admin.rector_assignments.cancel"
ARCHIVE = "admin.rector_assignments.archive"
AUDIT_READ = "admin.rector_assignments.audit.read"
TEMPLATES_MANAGE = "admin.rector_assignments.templates.manage"
DASHBOARD_READ = "admin.rector_assignments.dashboard.read"
ADMIN = "admin.rector_assignments.admin"
# A-031.5-RUNTIME additions
OUTBOX_READ = "admin.rector_assignments.outbox.read"
OUTBOX_MANAGE = "admin.rector_assignments.outbox.manage"
SLA_MANAGE = "admin.rector_assignments.sla.manage"
ESCALATION_POLICY_MANAGE = "admin.rector_assignments.escalation_policy.manage"

ALL_PERMISSIONS = frozenset({
    CREATE, READ, READ_ALL, READ_DEPARTMENT, ASSIGN, ACCEPT,
    REPORT_SUBMIT, REPORT_REVIEW, EVIDENCE_ATTACH, COMMENT,
    STATUS_CHANGE, COMPLETE, RETURN, ESCALATE, CANCEL, ARCHIVE,
    AUDIT_READ, TEMPLATES_MANAGE, DASHBOARD_READ, ADMIN,
    OUTBOX_READ, OUTBOX_MANAGE, SLA_MANAGE, ESCALATION_POLICY_MANAGE,
})
