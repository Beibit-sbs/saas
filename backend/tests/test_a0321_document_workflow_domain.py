"""A-032.1 document workflow domain tests."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from sqlalchemy.orm import Session

from app.core.module_helpers.service_validation import DomainValidationError, TenantRequiredError
from app.modules.document_workflow_os import permissions
from app.modules.document_workflow_os.models import (
    AuditEventType,
    CorrespondenceDirection,
    DecreeStatus,
    Document,
    DocumentAssignmentLink,
    DocumentStatus,
    DocumentType,
    OrderDecree,
    Resolution,
)
from app.modules.document_workflow_os.service import _validate_transition, get_documents


class TestModuleContract:
    def test_permissions_are_registered(self):
        assert permissions.CREATE == "admin.documents.create"
        assert permissions.DECREES_REGISTER == "admin.decrees.register"
        assert permissions.CORRESPONDENCE_ROUTE == "admin.correspondence.route"
        assert permissions.DASHBOARD_READ == "admin.documents.dashboard.read"
        assert len(permissions.ALL_PERMISSIONS) == 28

    def test_model_tablenames(self):
        assert Document.__tablename__ == "doc_documents"
        assert OrderDecree.__tablename__ == "doc_order_decrees"
        assert Resolution.__tablename__ == "doc_resolutions"
        assert DocumentAssignmentLink.__tablename__ == "doc_document_assignment_links"

    def test_document_types_include_correspondence(self):
        assert DocumentType.CORRESPONDENCE in DocumentType.ALL

    def test_audit_event_type_contract(self):
        assert AuditEventType.DASHBOARD_VIEWED in AuditEventType.ALL
        assert AuditEventType.DOCUMENT_CREATED in AuditEventType.ALL


class TestStatusTransitions:
    def test_document_draft_can_register(self):
        assert DocumentStatus.REGISTERED in DocumentStatus.ALLOWED_TRANSITIONS[DocumentStatus.DRAFT]

    def test_document_approved_can_sign(self):
        assert DocumentStatus.SIGNED in DocumentStatus.ALLOWED_TRANSITIONS[DocumentStatus.APPROVED]

    def test_document_archived_is_terminal(self):
        assert DocumentStatus.ARCHIVED in DocumentStatus.TERMINAL
        assert not DocumentStatus.ALLOWED_TRANSITIONS[DocumentStatus.ARCHIVED]

    def test_decree_legal_review_to_rector_review(self):
        assert DecreeStatus.RECTOR_REVIEW in DecreeStatus.ALLOWED_TRANSITIONS[DecreeStatus.LEGAL_REVIEW]

    def test_correspondence_direction_enum(self):
        assert CorrespondenceDirection.INCOMING in CorrespondenceDirection.ALL
        assert CorrespondenceDirection.OUTGOING in CorrespondenceDirection.ALL

    def test_invalid_document_transition_raises(self):
        with pytest.raises(DomainValidationError):
            _validate_transition(DocumentStatus.DRAFT, DocumentStatus.APPROVED, DocumentStatus.ALLOWED_TRANSITIONS)


class TestTenantValidation:
    def test_list_documents_requires_tenant(self):
        db = MagicMock(spec=Session)
        with pytest.raises((TenantRequiredError, ValueError)):
            get_documents(db, None)

    def test_list_documents_rejects_zero_tenant(self):
        db = MagicMock(spec=Session)
        with pytest.raises((TenantRequiredError, ValueError)):
            get_documents(db, 0)
