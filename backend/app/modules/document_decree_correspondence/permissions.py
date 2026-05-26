"""Document / Decree / Correspondence permission constants."""

from __future__ import annotations

OVERVIEW_READ = "document_decree_correspondence.overview.read"
READINESS_READ = "document_decree_correspondence.readiness.read"
LIMITATIONS_READ = "document_decree_correspondence.limitations.read"
DASHBOARD_READ = "document_decree_correspondence.dashboard.read"
DOCUMENTS_READ = "document_decree_correspondence.documents.read"
DOCUMENT_INTAKE_READ = "document_decree_correspondence.document_intake.read"
DOCUMENT_INTAKE_MANAGE = "document_decree_correspondence.document_intake.manage"
DOCUMENT_REGISTRATION_MANAGE = "document_decree_correspondence.document_registration.manage"
DOCUMENT_ROUTING_READ = "document_decree_correspondence.document_routing.read"
DOCUMENT_ROUTING_MANAGE = "document_decree_correspondence.document_routing.manage"
RECTOR_RESOLUTIONS_READ = "document_decree_correspondence.rector_resolutions.read"
RECTOR_RESOLUTIONS_METADATA = "document_decree_correspondence.rector_resolutions.metadata"
DECREES_READ = "document_decree_correspondence.decrees.read"
DECREES_METADATA = "document_decree_correspondence.decrees.metadata"
DECREE_DRAFTS_READ = "document_decree_correspondence.decree_drafts.read"
DECREE_DRAFTS_MANAGE = "document_decree_correspondence.decree_drafts.manage"
INCOMING_CORRESPONDENCE_READ = "document_decree_correspondence.incoming_correspondence.read"
INCOMING_CORRESPONDENCE_MANAGE = "document_decree_correspondence.incoming_correspondence.manage"
OUTGOING_CORRESPONDENCE_READ = "document_decree_correspondence.outgoing_correspondence.read"
OUTGOING_CORRESPONDENCE_MANAGE = "document_decree_correspondence.outgoing_correspondence.manage"
TEMPLATES_READ = "document_decree_correspondence.templates.read"
TEMPLATES_METADATA = "document_decree_correspondence.templates.metadata"
COMMITTEE_DECISIONS_READ = "document_decree_correspondence.committee_decisions.read"
COMMITTEE_DECISIONS_BRIDGE = "document_decree_correspondence.committee_decisions.bridge"
ASSIGNMENTS_READ = "document_decree_correspondence.assignments.read"
ASSIGNMENTS_BRIDGE = "document_decree_correspondence.assignments.bridge"
EXECUTION_CONTROL_READ = "document_decree_correspondence.execution_control.read"
EXECUTION_CONTROL_METADATA = "document_decree_correspondence.execution_control.metadata"
SLA_DEADLINES_READ = "document_decree_correspondence.sla_deadlines.read"
SLA_DEADLINES_METADATA = "document_decree_correspondence.sla_deadlines.metadata"
EVIDENCE_READ = "document_decree_correspondence.evidence.read"
EVIDENCE_WRITE = "document_decree_correspondence.evidence.write"
ATTACHMENTS_READ = "document_decree_correspondence.attachments.read"
ATTACHMENTS_METADATA = "document_decree_correspondence.attachments.metadata"
AUDIT_READ = "document_decree_correspondence.audit.read"
AUDIT_WRITE = "document_decree_correspondence.audit.write"
ARCHIVE_READ = "document_decree_correspondence.archive.read"
ARCHIVE_READINESS = "document_decree_correspondence.archive.readiness"
RETENTION_READ = "document_decree_correspondence.retention.read"
RETENTION_METADATA = "document_decree_correspondence.retention.metadata"
SIGNATURE_READINESS_READ = "document_decree_correspondence.signature_readiness.read"
SIGNATURE_READINESS_EVIDENCE = "document_decree_correspondence.signature_readiness.evidence"
DELIVERY_READINESS_READ = "document_decree_correspondence.delivery_readiness.read"
DELIVERY_READINESS_EVIDENCE = "document_decree_correspondence.delivery_readiness.evidence"
BRIDGES_EXECUTIVE_READ = "document_decree_correspondence.bridges.executive.read"
BRIDGES_EXECUTIVE_WRITE = "document_decree_correspondence.bridges.executive.write"
BRIDGES_ASSIGNMENTS_READ = "document_decree_correspondence.bridges.assignments.read"
BRIDGES_ASSIGNMENTS_WRITE = "document_decree_correspondence.bridges.assignments.write"
ROLES_READ = "document_decree_correspondence.roles.read"
METADATA_READ = "document_decree_correspondence.metadata.read"

ALL_PERMISSIONS: frozenset[str] = frozenset(
    {
        OVERVIEW_READ,
        READINESS_READ,
        LIMITATIONS_READ,
        DASHBOARD_READ,
        DOCUMENTS_READ,
        DOCUMENT_INTAKE_READ,
        DOCUMENT_INTAKE_MANAGE,
        DOCUMENT_REGISTRATION_MANAGE,
        DOCUMENT_ROUTING_READ,
        DOCUMENT_ROUTING_MANAGE,
        RECTOR_RESOLUTIONS_READ,
        RECTOR_RESOLUTIONS_METADATA,
        DECREES_READ,
        DECREES_METADATA,
        DECREE_DRAFTS_READ,
        DECREE_DRAFTS_MANAGE,
        INCOMING_CORRESPONDENCE_READ,
        INCOMING_CORRESPONDENCE_MANAGE,
        OUTGOING_CORRESPONDENCE_READ,
        OUTGOING_CORRESPONDENCE_MANAGE,
        TEMPLATES_READ,
        TEMPLATES_METADATA,
        COMMITTEE_DECISIONS_READ,
        COMMITTEE_DECISIONS_BRIDGE,
        ASSIGNMENTS_READ,
        ASSIGNMENTS_BRIDGE,
        EXECUTION_CONTROL_READ,
        EXECUTION_CONTROL_METADATA,
        SLA_DEADLINES_READ,
        SLA_DEADLINES_METADATA,
        EVIDENCE_READ,
        EVIDENCE_WRITE,
        ATTACHMENTS_READ,
        ATTACHMENTS_METADATA,
        AUDIT_READ,
        AUDIT_WRITE,
        ARCHIVE_READ,
        ARCHIVE_READINESS,
        RETENTION_READ,
        RETENTION_METADATA,
        SIGNATURE_READINESS_READ,
        SIGNATURE_READINESS_EVIDENCE,
        DELIVERY_READINESS_READ,
        DELIVERY_READINESS_EVIDENCE,
        BRIDGES_EXECUTIVE_READ,
        BRIDGES_EXECUTIVE_WRITE,
        BRIDGES_ASSIGNMENTS_READ,
        BRIDGES_ASSIGNMENTS_WRITE,
        ROLES_READ,
        METADATA_READ,
    }
)

DOCUMENT_DECREE_CORRESPONDENCE_PERMISSIONS = sorted(ALL_PERMISSIONS)
DOCUMENT_DECREE_CORRESPONDENCE_PERMISSION_COUNT = 50
