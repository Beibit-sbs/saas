"""Document Workflow OS — Permission constants.

28 permissions across document, decree, correspondence, resolution, dashboard.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Document permissions (9)
# ---------------------------------------------------------------------------
READ = "admin.documents.read"
CREATE = "admin.documents.create"
UPDATE = "admin.documents.update"
REGISTER = "admin.documents.register"
REVIEW = "admin.documents.review"
APPROVE = "admin.documents.approve"
SIGNED_METADATA_RECORD = "admin.documents.signed_metadata.record"
ARCHIVE = "admin.documents.archive"
AUDIT_READ = "admin.documents.audit.read"

# ---------------------------------------------------------------------------
# Decree permissions (8)
# ---------------------------------------------------------------------------
DECREES_READ = "admin.decrees.read"
DECREES_CREATE = "admin.decrees.create"
DECREES_UPDATE = "admin.decrees.update"
DECREES_LEGAL_REVIEW = "admin.decrees.legal_review"
DECREES_APPROVE_SIGNING = "admin.decrees.approve_signing"
DECREES_SIGNED_METADATA = "admin.decrees.signed_metadata.record"
DECREES_REGISTER = "admin.decrees.register"
DECREES_ARCHIVE = "admin.decrees.archive"

# ---------------------------------------------------------------------------
# Correspondence permissions (6)
# ---------------------------------------------------------------------------
CORRESPONDENCE_READ = "admin.correspondence.read"
CORRESPONDENCE_CREATE = "admin.correspondence.create"
CORRESPONDENCE_REGISTER = "admin.correspondence.register"
CORRESPONDENCE_ROUTE = "admin.correspondence.route"
CORRESPONDENCE_SENT_METADATA = "admin.correspondence.sent_metadata.record"
CORRESPONDENCE_ARCHIVE = "admin.correspondence.archive"

# ---------------------------------------------------------------------------
# Resolution / integration permissions (3)
# ---------------------------------------------------------------------------
RESOLUTIONS_CREATE = "admin.resolutions.create"
RESOLUTIONS_LINK_ASSIGNMENT = "admin.resolutions.link_assignment"
DOCUMENTS_LINK_ASSIGNMENT = "admin.documents.link_assignment"

# ---------------------------------------------------------------------------
# Dashboard / admin permissions (2)
# ---------------------------------------------------------------------------
DASHBOARD_READ = "admin.documents.dashboard.read"
ADMIN = "admin.documents.admin"

# ---------------------------------------------------------------------------
# Master set
# ---------------------------------------------------------------------------
ALL_PERMISSIONS: frozenset[str] = frozenset({
    READ, CREATE, UPDATE, REGISTER, REVIEW, APPROVE, SIGNED_METADATA_RECORD,
    ARCHIVE, AUDIT_READ,
    DECREES_READ, DECREES_CREATE, DECREES_UPDATE, DECREES_LEGAL_REVIEW,
    DECREES_APPROVE_SIGNING, DECREES_SIGNED_METADATA, DECREES_REGISTER,
    DECREES_ARCHIVE,
    CORRESPONDENCE_READ, CORRESPONDENCE_CREATE, CORRESPONDENCE_REGISTER,
    CORRESPONDENCE_ROUTE, CORRESPONDENCE_SENT_METADATA, CORRESPONDENCE_ARCHIVE,
    RESOLUTIONS_CREATE, RESOLUTIONS_LINK_ASSIGNMENT, DOCUMENTS_LINK_ASSIGNMENT,
    DASHBOARD_READ, ADMIN,
})

DOCUMENT_WORKFLOW_PERMISSIONS = sorted(ALL_PERMISSIONS)
