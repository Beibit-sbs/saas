"""Permission constants and normalized inventory for Integration Provider Readiness."""

from __future__ import annotations

REGISTRY_READ = "admin.integration_provider_readiness.registry.read"
REGISTRY_LIST = "admin.integration_provider_readiness.registry.list"
REGISTRY_CREATE = "admin.integration_provider_readiness.registry.create"
REGISTRY_UPDATE = "admin.integration_provider_readiness.registry.update"

PROFILE_READ = "admin.integration_provider_readiness.profile.read"
PROFILE_LIST = "admin.integration_provider_readiness.profile.list"
PROFILE_CREATE = "admin.integration_provider_readiness.profile.create"
PROFILE_UPDATE = "admin.integration_provider_readiness.profile.update"

CAPABILITY_READ = "admin.integration_provider_readiness.capability.read"
CAPABILITY_LIST = "admin.integration_provider_readiness.capability.list"
CAPABILITY_CREATE = "admin.integration_provider_readiness.capability.create"
CAPABILITY_UPDATE = "admin.integration_provider_readiness.capability.update"

READINESS_READ = "admin.integration_provider_readiness.readiness_assessment.read"
READINESS_LIST = "admin.integration_provider_readiness.readiness_assessment.list"
READINESS_CREATE = "admin.integration_provider_readiness.readiness_assessment.create"
READINESS_UPDATE = "admin.integration_provider_readiness.readiness_assessment.update"

EVIDENCE_READ = "admin.integration_provider_readiness.evidence.read"
EVIDENCE_LIST = "admin.integration_provider_readiness.evidence.list"
EVIDENCE_CREATE = "admin.integration_provider_readiness.evidence.create"
EVIDENCE_UPDATE = "admin.integration_provider_readiness.evidence.update"
EVIDENCE_DELETE = "admin.integration_provider_readiness.evidence.delete"

COMPLIANCE_READ = "admin.integration_provider_readiness.compliance_security.compliance.read"
COMPLIANCE_REVIEW = "admin.integration_provider_readiness.compliance_security.compliance.review"
COMPLIANCE_APPROVE = "admin.integration_provider_readiness.compliance_security.compliance.approve"
SECURITY_READ = "admin.integration_provider_readiness.compliance_security.security.read"
SECURITY_REVIEW = "admin.integration_provider_readiness.compliance_security.security.review"
SECURITY_APPROVE = "admin.integration_provider_readiness.compliance_security.security.approve"

RISK_READ = "admin.integration_provider_readiness.risk_exception.read"
RISK_LIST = "admin.integration_provider_readiness.risk_exception.list"
RISK_CREATE = "admin.integration_provider_readiness.risk_exception.create"
RISK_UPDATE = "admin.integration_provider_readiness.risk_exception.update"

AUDIT_READ = "admin.integration_provider_readiness.audit.read"
AUDIT_LIST = "admin.integration_provider_readiness.audit.list"
AUDIT_APPEND = "admin.integration_provider_readiness.audit.append"

PLAN_READ = "admin.integration_provider_readiness.integration_plan.read"
PLAN_LIST = "admin.integration_provider_readiness.integration_plan.list"
PLAN_CREATE = "admin.integration_provider_readiness.integration_plan.create"
PLAN_UPDATE = "admin.integration_provider_readiness.integration_plan.update"

DASHBOARD_OVERVIEW_READ = "admin.integration_provider_readiness.dashboard.overview.read"
DASHBOARD_READINESS_READ = "admin.integration_provider_readiness.dashboard.readiness.read"
DASHBOARD_RISK_READ = "admin.integration_provider_readiness.dashboard.risk.read"
DASHBOARD_ROADMAP_READ = "admin.integration_provider_readiness.dashboard.roadmap.read"

PERMISSION_INVENTORY: tuple[dict[str, object], ...] = (
    {"slug": REGISTRY_READ, "family": "registry", "route_family": "provider-registry", "workflow": "Provider Registry Workflow", "dashboard": "Provider Overview", "roles": ("platform_admin", "integration_admin", "security_admin", "auditor")},
    {"slug": REGISTRY_LIST, "family": "registry", "route_family": "provider-registry", "workflow": "Provider Registry Workflow", "dashboard": "Provider Overview", "roles": ("platform_admin", "integration_admin", "security_admin", "auditor", "executive_viewer")},
    {"slug": REGISTRY_CREATE, "family": "registry", "route_family": "provider-registry", "workflow": "Provider Registry Workflow", "dashboard": None, "roles": ("platform_admin", "integration_admin")},
    {"slug": REGISTRY_UPDATE, "family": "registry", "route_family": "provider-registry", "workflow": "Provider Registry Workflow", "dashboard": None, "roles": ("platform_admin", "integration_admin")},
    {"slug": PROFILE_READ, "family": "profile", "route_family": "provider-profile", "workflow": "Provider Profile Workflow", "dashboard": "Provider Overview", "roles": ("platform_admin", "integration_admin", "security_admin", "auditor")},
    {"slug": PROFILE_LIST, "family": "profile", "route_family": "provider-profile", "workflow": "Provider Profile Workflow", "dashboard": "Provider Overview", "roles": ("platform_admin", "integration_admin", "security_admin", "auditor")},
    {"slug": PROFILE_CREATE, "family": "profile", "route_family": "provider-profile", "workflow": "Provider Profile Workflow", "dashboard": None, "roles": ("platform_admin", "integration_admin")},
    {"slug": PROFILE_UPDATE, "family": "profile", "route_family": "provider-profile", "workflow": "Provider Profile Workflow", "dashboard": None, "roles": ("platform_admin", "integration_admin")},
    {"slug": CAPABILITY_READ, "family": "capability", "route_family": "capability-matrix", "workflow": "Capability Matrix Workflow", "dashboard": "Capability Matrix", "roles": ("platform_admin", "integration_admin", "security_admin", "auditor")},
    {"slug": CAPABILITY_LIST, "family": "capability", "route_family": "capability-matrix", "workflow": "Capability Matrix Workflow", "dashboard": "Capability Matrix", "roles": ("platform_admin", "integration_admin", "security_admin", "auditor", "executive_viewer")},
    {"slug": CAPABILITY_CREATE, "family": "capability", "route_family": "capability-matrix", "workflow": "Capability Matrix Workflow", "dashboard": None, "roles": ("platform_admin", "integration_admin")},
    {"slug": CAPABILITY_UPDATE, "family": "capability", "route_family": "capability-matrix", "workflow": "Capability Matrix Workflow", "dashboard": None, "roles": ("platform_admin", "integration_admin", "security_admin")},
    {"slug": READINESS_READ, "family": "readiness_assessment", "route_family": "readiness-assessment", "workflow": "Readiness Assessment Workflow", "dashboard": "Provider Readiness", "roles": ("platform_admin", "integration_admin", "security_admin", "auditor")},
    {"slug": READINESS_LIST, "family": "readiness_assessment", "route_family": "readiness-assessment", "workflow": "Readiness Assessment Workflow", "dashboard": "Provider Readiness", "roles": ("platform_admin", "integration_admin", "security_admin", "auditor", "executive_viewer")},
    {"slug": READINESS_CREATE, "family": "readiness_assessment", "route_family": "readiness-assessment", "workflow": "Readiness Assessment Workflow", "dashboard": None, "roles": ("platform_admin", "integration_admin")},
    {"slug": READINESS_UPDATE, "family": "readiness_assessment", "route_family": "readiness-assessment", "workflow": "Readiness Assessment Workflow", "dashboard": None, "roles": ("platform_admin", "integration_admin", "security_admin")},
    {"slug": EVIDENCE_READ, "family": "evidence", "route_family": "evidence-management", "workflow": "Evidence Collection Workflow", "dashboard": "Evidence Dashboard", "roles": ("platform_admin", "integration_admin", "security_admin", "auditor")},
    {"slug": EVIDENCE_LIST, "family": "evidence", "route_family": "evidence-management", "workflow": "Evidence Collection Workflow", "dashboard": "Evidence Dashboard", "roles": ("platform_admin", "integration_admin", "security_admin", "auditor", "executive_viewer")},
    {"slug": EVIDENCE_CREATE, "family": "evidence", "route_family": "evidence-management", "workflow": "Evidence Collection Workflow", "dashboard": None, "roles": ("platform_admin", "integration_admin", "auditor")},
    {"slug": EVIDENCE_UPDATE, "family": "evidence", "route_family": "evidence-management", "workflow": "Evidence Collection Workflow", "dashboard": None, "roles": ("platform_admin", "integration_admin")},
    {"slug": EVIDENCE_DELETE, "family": "evidence", "route_family": "evidence-management", "workflow": "Evidence Collection Workflow", "dashboard": None, "roles": ("platform_admin",)},
    {"slug": COMPLIANCE_READ, "family": "compliance_security", "route_family": "compliance-security-review", "workflow": "Compliance Review Workflow", "dashboard": "Evidence Dashboard", "roles": ("platform_admin", "security_admin", "auditor")},
    {"slug": COMPLIANCE_REVIEW, "family": "compliance_security", "route_family": "compliance-security-review", "workflow": "Compliance Review Workflow", "dashboard": None, "roles": ("platform_admin", "security_admin")},
    {"slug": COMPLIANCE_APPROVE, "family": "compliance_security", "route_family": "compliance-security-review", "workflow": "Compliance Review Workflow", "dashboard": None, "roles": ("platform_admin", "security_admin")},
    {"slug": SECURITY_READ, "family": "compliance_security", "route_family": "compliance-security-review", "workflow": "Security Review Workflow", "dashboard": "Risk Dashboard", "roles": ("platform_admin", "security_admin", "auditor")},
    {"slug": SECURITY_REVIEW, "family": "compliance_security", "route_family": "compliance-security-review", "workflow": "Security Review Workflow", "dashboard": None, "roles": ("platform_admin", "security_admin")},
    {"slug": SECURITY_APPROVE, "family": "compliance_security", "route_family": "compliance-security-review", "workflow": "Security Review Workflow", "dashboard": None, "roles": ("platform_admin", "security_admin")},
    {"slug": RISK_READ, "family": "risk_exception", "route_family": "risk-exception", "workflow": "Exception and Risk Escalation Workflow", "dashboard": "Risk Dashboard", "roles": ("platform_admin", "security_admin", "auditor")},
    {"slug": RISK_LIST, "family": "risk_exception", "route_family": "risk-exception", "workflow": "Exception and Risk Escalation Workflow", "dashboard": "Risk Dashboard", "roles": ("platform_admin", "security_admin", "auditor", "executive_viewer")},
    {"slug": RISK_CREATE, "family": "risk_exception", "route_family": "risk-exception", "workflow": "Exception and Risk Escalation Workflow", "dashboard": None, "roles": ("platform_admin", "security_admin")},
    {"slug": RISK_UPDATE, "family": "risk_exception", "route_family": "risk-exception", "workflow": "Exception and Risk Escalation Workflow", "dashboard": None, "roles": ("platform_admin", "security_admin")},
    {"slug": AUDIT_READ, "family": "audit", "route_family": "audit-review", "workflow": "Provider Audit Review Workflow", "dashboard": "Evidence Dashboard", "roles": ("platform_admin", "auditor", "security_admin")},
    {"slug": AUDIT_LIST, "family": "audit", "route_family": "audit-review", "workflow": "Provider Audit Review Workflow", "dashboard": "Evidence Dashboard", "roles": ("platform_admin", "auditor", "security_admin", "executive_viewer")},
    {"slug": AUDIT_APPEND, "family": "audit", "route_family": "audit-review", "workflow": "Provider Audit Review Workflow", "dashboard": None, "roles": ("platform_admin", "auditor")},
    {"slug": PLAN_READ, "family": "integration_plan", "route_family": "integration-plan-roadmap", "workflow": "Integration Planning Workflow", "dashboard": "Integration Roadmap", "roles": ("platform_admin", "integration_admin", "security_admin", "auditor")},
    {"slug": PLAN_LIST, "family": "integration_plan", "route_family": "integration-plan-roadmap", "workflow": "Integration Planning Workflow", "dashboard": "Integration Roadmap", "roles": ("platform_admin", "integration_admin", "security_admin", "auditor", "executive_viewer")},
    {"slug": PLAN_CREATE, "family": "integration_plan", "route_family": "integration-plan-roadmap", "workflow": "Integration Planning Workflow", "dashboard": None, "roles": ("platform_admin", "integration_admin")},
    {"slug": PLAN_UPDATE, "family": "integration_plan", "route_family": "integration-plan-roadmap", "workflow": "Integration Planning Workflow", "dashboard": None, "roles": ("platform_admin", "integration_admin")},
    {"slug": DASHBOARD_OVERVIEW_READ, "family": "dashboard", "route_family": "dashboard-backend-contracts", "workflow": "Provider Dashboard Publication Workflow", "dashboard": "Provider Overview", "roles": ("platform_admin", "integration_admin", "security_admin", "auditor", "executive_viewer")},
    {"slug": DASHBOARD_READINESS_READ, "family": "dashboard", "route_family": "dashboard-backend-contracts", "workflow": "Provider Dashboard Publication Workflow", "dashboard": "Provider Readiness,Capability Matrix", "roles": ("platform_admin", "integration_admin", "security_admin", "auditor", "executive_viewer")},
    {"slug": DASHBOARD_RISK_READ, "family": "dashboard", "route_family": "dashboard-backend-contracts", "workflow": "Provider Dashboard Publication Workflow", "dashboard": "Risk Dashboard,Evidence Dashboard", "roles": ("platform_admin", "security_admin", "auditor", "executive_viewer")},
    {"slug": DASHBOARD_ROADMAP_READ, "family": "dashboard", "route_family": "dashboard-backend-contracts", "workflow": "Provider Dashboard Publication Workflow", "dashboard": "Integration Roadmap", "roles": ("platform_admin", "integration_admin", "security_admin", "auditor", "executive_viewer")},
)

ALL_PERMISSIONS = tuple(item["slug"] for item in PERMISSION_INVENTORY)
PERMISSION_COUNT = len(ALL_PERMISSIONS)

