"""Research / Science backend foundation permission constants."""

from __future__ import annotations

OVERVIEW_READ = "research_science.overview.read"
DASHBOARD_READ = "research_science.dashboard.read"
HEALTH_READ = "research_science.health.read"
MATRIX_READ = "research_science.matrix.read"
LIMITATIONS_READ = "research_science.limitations.read"

PROJECTS_READ = "research_science.projects.read"
PROJECTS_CREATE = "research_science.projects.create"
PROJECTS_UPDATE = "research_science.projects.update"

STUDENT_RESEARCH_READ = "research_science.student_research.read"
STUDENT_RESEARCH_CREATE = "research_science.student_research.create"
STUDENT_RESEARCH_UPDATE = "research_science.student_research.update"

SUPERVISION_READ = "research_science.supervision.read"
SUPERVISION_CREATE = "research_science.supervision.create"
SUPERVISION_UPDATE = "research_science.supervision.update"

PUBLICATIONS_READ = "research_science.publications.read"
PUBLICATIONS_CREATE = "research_science.publications.create"
PUBLICATIONS_UPDATE = "research_science.publications.update"

CONFERENCES_READ = "research_science.conferences.read"
CONFERENCES_CREATE = "research_science.conferences.create"
CONFERENCES_UPDATE = "research_science.conferences.update"

GRANTS_READ = "research_science.grants.read"
GRANTS_CREATE = "research_science.grants.create"
GRANTS_UPDATE = "research_science.grants.update"
GRANT_DELIVERABLES_READ = "research_science.grant_deliverables.read"
GRANT_DELIVERABLES_CREATE = "research_science.grant_deliverables.create"
GRANT_DELIVERABLES_UPDATE = "research_science.grant_deliverables.update"

ETHICS_READ = "research_science.ethics.read"
ETHICS_CREATE = "research_science.ethics.create"
ETHICS_UPDATE = "research_science.ethics.update"
ETHICS_AMENDMENTS_READ = "research_science.ethics_amendments.read"
ETHICS_AMENDMENTS_CREATE = "research_science.ethics_amendments.create"
ETHICS_AMENDMENTS_UPDATE = "research_science.ethics_amendments.update"

EVIDENCE_READ = "research_science.evidence.read"
EVIDENCE_ATTACH = "research_science.evidence.attach"
AUDIT_READ = "research_science.audit.read"
BRIDGES_READ = "research_science.bridges.read"
BRIDGES_CREATE = "research_science.bridges.create"
BRIDGES_UPDATE = "research_science.bridges.update"

ADMIN_READ = "research_science.admin.read"
ADMIN_CONFIGURE = "research_science.admin.configure"

ALL_PERMISSIONS: frozenset[str] = frozenset({
    OVERVIEW_READ,
    DASHBOARD_READ,
    HEALTH_READ,
    MATRIX_READ,
    LIMITATIONS_READ,
    PROJECTS_READ,
    PROJECTS_CREATE,
    PROJECTS_UPDATE,
    STUDENT_RESEARCH_READ,
    STUDENT_RESEARCH_CREATE,
    STUDENT_RESEARCH_UPDATE,
    SUPERVISION_READ,
    SUPERVISION_CREATE,
    SUPERVISION_UPDATE,
    PUBLICATIONS_READ,
    PUBLICATIONS_CREATE,
    PUBLICATIONS_UPDATE,
    CONFERENCES_READ,
    CONFERENCES_CREATE,
    CONFERENCES_UPDATE,
    GRANTS_READ,
    GRANTS_CREATE,
    GRANTS_UPDATE,
    GRANT_DELIVERABLES_READ,
    GRANT_DELIVERABLES_CREATE,
    GRANT_DELIVERABLES_UPDATE,
    ETHICS_READ,
    ETHICS_CREATE,
    ETHICS_UPDATE,
    ETHICS_AMENDMENTS_READ,
    ETHICS_AMENDMENTS_CREATE,
    ETHICS_AMENDMENTS_UPDATE,
    EVIDENCE_READ,
    EVIDENCE_ATTACH,
    AUDIT_READ,
    BRIDGES_READ,
    BRIDGES_CREATE,
    BRIDGES_UPDATE,
    ADMIN_READ,
    ADMIN_CONFIGURE,
})

RESEARCH_SCIENCE_PERMISSIONS = sorted(ALL_PERMISSIONS)