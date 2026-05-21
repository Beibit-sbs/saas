"""Document Workflow OS — Module package.

UCE-009 (document_workflow) + UCE-011 (order_decree_registry)
+ UCE-013 (incoming_outgoing_correspondence) productized vertical.

PRODUCT_VERTICAL: DOCUMENT_DECREE_CORRESPONDENCE_WORKFLOW_OS
Module: document_workflow_os
Spec: A-032.1-SPEC commit f2ee367
Runtime: A-032.1-RUNTIME

Anti-fake contract:
- PROVIDER_INTEGRATION_ENABLED = False (immutable)
- AUTO_SIGNATURE_ENABLED = False (immutable)
- AUTO_APPROVAL_ENABLED = False (immutable)
- FAKE_METRICS_ENABLED = False (immutable)
- NO_HARD_DELETE = True (immutable)
"""

from __future__ import annotations

MODULE_NAME = "document_workflow_os"
MODULE_VERSION = "A-032.1"
PRODUCT_VERTICAL = "DOCUMENT_DECREE_CORRESPONDENCE_WORKFLOW_OS"
TARGET_LEVEL = "PRODUCTIZED_BACKEND_RUNTIME"

# Anti-fake safety flags — do NOT change to True
PROVIDER_INTEGRATION_ENABLED = False
AUTO_SIGNATURE_ENABLED = False
AUTO_APPROVAL_ENABLED = False
FAKE_METRICS_ENABLED = False
NO_HARD_DELETE = True

# UCE scope
UCE_PRIMARY = ["UCE-009", "UCE-011", "UCE-013"]
UCE_LINKED = ["UCE-099", "UCE-031"]

# A-031 integration boundary
A031_INTEGRATION_HUMAN_INITIATED_ONLY = True
A031_ASSIGNMENT_TABLE_MUTATIONS_ALLOWED = False
A031_CROSS_MODULE_FK_CONSTRAINT = False  # BigInteger ID only; no ORM FK
