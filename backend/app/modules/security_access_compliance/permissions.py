"""Security / Access / Compliance permission constants."""

from __future__ import annotations

OVERVIEW_READ = "security_access_compliance.overview.read"
READINESS_READ = "security_access_compliance.readiness.read"
DASHBOARD_READ = "security_access_compliance.dashboard.read"
LIMITATIONS_READ = "security_access_compliance.limitations.read"
ROLES_READ = "security_access_compliance.roles.read"
PERMISSIONS_READ = "security_access_compliance.permissions.read"
ACCESS_GOVERNANCE_READ = "security_access_compliance.access_governance.read"
ACCESS_GOVERNANCE_METADATA = "security_access_compliance.access_governance.metadata"
RBAC_EVIDENCE_READ = "security_access_compliance.rbac_evidence.read"
RBAC_EVIDENCE_WRITE = "security_access_compliance.rbac_evidence.write"
ABAC_EVIDENCE_READ = "security_access_compliance.abac_evidence.read"
ABAC_EVIDENCE_WRITE = "security_access_compliance.abac_evidence.write"
SESSIONS_READ = "security_access_compliance.sessions.read"
LOGIN_EVENTS_READ = "security_access_compliance.login_events.read"
MFA_READINESS_READ = "security_access_compliance.mfa_readiness.read"
TENANT_ISOLATION_READ = "security_access_compliance.tenant_isolation.read"
INCIDENTS_READ = "security_access_compliance.incidents.read"
INCIDENTS_METADATA = "security_access_compliance.incidents.metadata"
INCIDENT_REVIEW_READ = "security_access_compliance.incident_review.read"
INCIDENT_REVIEW_METADATA = "security_access_compliance.incident_review.metadata"
REMEDIATION_READ = "security_access_compliance.remediation.read"
REMEDIATION_METADATA = "security_access_compliance.remediation.metadata"
RISKS_READ = "security_access_compliance.risks.read"
RISKS_METADATA = "security_access_compliance.risks.metadata"
COMPLIANCE_CONTROLS_READ = "security_access_compliance.compliance_controls.read"
COMPLIANCE_CONTROLS_METADATA = "security_access_compliance.compliance_controls.metadata"
POLICY_CONTROLS_READ = "security_access_compliance.policy_controls.read"
POLICY_CONTROLS_METADATA = "security_access_compliance.policy_controls.metadata"
AUDIT_EVENTS_READ = "security_access_compliance.audit_events.read"
AUDIT_EVENTS_METADATA = "security_access_compliance.audit_events.metadata"
SENSITIVE_ACTIONS_READ = "security_access_compliance.sensitive_actions.read"
SENSITIVE_ACTIONS_REVIEW = "security_access_compliance.sensitive_actions.review"
DATA_PROTECTION_READ = "security_access_compliance.data_protection.read"
DATA_PROTECTION_EVIDENCE = "security_access_compliance.data_protection.evidence"
PRIVACY_READINESS_READ = "security_access_compliance.privacy_readiness.read"
PRIVACY_READINESS_EVIDENCE = "security_access_compliance.privacy_readiness.evidence"
EXCEPTIONS_READ = "security_access_compliance.exceptions.read"
EXCEPTIONS_METADATA = "security_access_compliance.exceptions.metadata"
VISITOR_ACCESS_READ = "security_access_compliance.visitor_access.read"
VISITOR_ACCESS_METADATA = "security_access_compliance.visitor_access.metadata"
BRIDGES_HR = "security_access_compliance.bridges.hr"
BRIDGES_FINANCE = "security_access_compliance.bridges.finance"
BRIDGES_DOCUMENTS = "security_access_compliance.bridges.documents"
BRIDGES_STUDENT_SERVICES = "security_access_compliance.bridges.student_services"

ALL_PERMISSIONS: frozenset[str] = frozenset(
    {
        OVERVIEW_READ,
        READINESS_READ,
        DASHBOARD_READ,
        LIMITATIONS_READ,
        ROLES_READ,
        PERMISSIONS_READ,
        ACCESS_GOVERNANCE_READ,
        ACCESS_GOVERNANCE_METADATA,
        RBAC_EVIDENCE_READ,
        RBAC_EVIDENCE_WRITE,
        ABAC_EVIDENCE_READ,
        ABAC_EVIDENCE_WRITE,
        SESSIONS_READ,
        LOGIN_EVENTS_READ,
        MFA_READINESS_READ,
        TENANT_ISOLATION_READ,
        INCIDENTS_READ,
        INCIDENTS_METADATA,
        INCIDENT_REVIEW_READ,
        INCIDENT_REVIEW_METADATA,
        REMEDIATION_READ,
        REMEDIATION_METADATA,
        RISKS_READ,
        RISKS_METADATA,
        COMPLIANCE_CONTROLS_READ,
        COMPLIANCE_CONTROLS_METADATA,
        POLICY_CONTROLS_READ,
        POLICY_CONTROLS_METADATA,
        AUDIT_EVENTS_READ,
        AUDIT_EVENTS_METADATA,
        SENSITIVE_ACTIONS_READ,
        SENSITIVE_ACTIONS_REVIEW,
        DATA_PROTECTION_READ,
        DATA_PROTECTION_EVIDENCE,
        PRIVACY_READINESS_READ,
        PRIVACY_READINESS_EVIDENCE,
        EXCEPTIONS_READ,
        EXCEPTIONS_METADATA,
        VISITOR_ACCESS_READ,
        VISITOR_ACCESS_METADATA,
        BRIDGES_HR,
        BRIDGES_FINANCE,
        BRIDGES_DOCUMENTS,
        BRIDGES_STUDENT_SERVICES,
    }
)

SECURITY_ACCESS_COMPLIANCE_PERMISSIONS = sorted(ALL_PERMISSIONS)
SECURITY_ACCESS_COMPLIANCE_PERMISSION_COUNT = 44
