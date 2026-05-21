"""A-032.1 document workflow API tests."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from app.main import app
from app.modules.auth.token_service import create_access_token
from app.modules.document_workflow_os.dependencies import get_doc_workflow_db
from app.modules.document_workflow_os.permissions import ALL_PERMISSIONS
from tests.conftest import _auth_headers, client

BASE = "/api/admin/documents"
VIEWER_HEADERS = _auth_headers("viewer-docs@example.com", ["viewer"], tenant_id=1)


def _docs_headers() -> dict[str, str]:
    token = create_access_token(
        user_id="101",
        roles=["admin"],
        auth_source="test",
        tenant_id=1,
        permissions=sorted(ALL_PERMISSIONS),
    )
    return {"Authorization": f"Bearer {token}"}


DOCS_HEADERS = _docs_headers()


@pytest.fixture(autouse=True)
def _override_db():
    session = MagicMock(spec=Session)
    app.dependency_overrides[get_doc_workflow_db] = lambda: session
    yield
    app.dependency_overrides.pop(get_doc_workflow_db, None)


class TestNoAuth:
    def test_list_documents_requires_auth(self):
        resp = client.get(BASE)
        assert resp.status_code in (401, 403)

    def test_dashboard_requires_auth(self):
        resp = client.get(f"{BASE}/dashboard/summary")
        assert resp.status_code in (401, 403)

    def test_get_decree_requires_auth(self):
        resp = client.get(f"{BASE}/decrees/1")
        assert resp.status_code in (401, 403)


class TestAdminRoutes:
    @patch("app.modules.document_workflow_os.router.service.get_documents")
    def test_list_documents(self, mock_get_documents):
        mock_get_documents.return_value = ([
            SimpleNamespace(
                id=1,
                tenant_id=1,
                title="Memo",
                document_type="INTERNAL_MEMO",
                status="DRAFT",
                registry_number=None,
                registry_date=None,
                source_department_id=None,
                owner_user_id=None,
                created_by_user_id=1,
                linked_assignment_id=None,
                linked_decree_id=None,
                version=1,
                created_at="2025-01-01T00:00:00Z",
                updated_at="2025-01-01T00:00:00Z",
                archived_at=None,
            )
        ], 1)
        resp = client.get(BASE, headers=DOCS_HEADERS)
        assert resp.status_code == 200
        assert resp.json()["total"] == 1

    @patch("app.modules.document_workflow_os.router.service.create_document")
    def test_create_document(self, mock_create_document):
        mock_create_document.return_value = SimpleNamespace(
            id=1,
            tenant_id=1,
            title="Memo",
            document_type="INTERNAL_MEMO",
            status="DRAFT",
            registry_number=None,
            registry_date=None,
            source_department_id=None,
            owner_user_id=None,
            created_by_user_id=1,
            linked_assignment_id=None,
            linked_decree_id=None,
            version=1,
            created_at="2025-01-01T00:00:00Z",
            updated_at="2025-01-01T00:00:00Z",
            archived_at=None,
        )
        resp = client.post(
            BASE,
            headers=DOCS_HEADERS,
            json={"title": "Memo", "document_type": "INTERNAL_MEMO"},
        )
        assert resp.status_code == 201
        assert resp.json()["title"] == "Memo"

    @patch("app.modules.document_workflow_os.router.service.get_document_workflow_dashboard_summary")
    def test_dashboard_summary(self, mock_dashboard):
        mock_dashboard.return_value = {
            "tenant_id": 1,
            "total_documents": 10,
            "registered_documents": 2,
            "under_review_count": 1,
            "returned_for_revision_count": 1,
            "approved_count": 1,
            "signed_count": 1,
            "archived_count": 1,
            "incoming_correspondence_count": 2,
            "outgoing_correspondence_count": 1,
            "overdue_document_reviews": 0,
            "documents_linked_to_assignments": 1,
            "decrees_pending_signature": 1,
            "average_review_cycle_days": None,
            "data_source": "computed_from_documents",
            "fake_metrics": False,
            "generated_at": "2025-01-01T00:00:00Z",
            "incomplete_data": False,
        }
        resp = client.get(f"{BASE}/dashboard/summary", headers=DOCS_HEADERS)
        assert resp.status_code == 200
        assert resp.json()["fake_metrics"] is False

    @patch("app.modules.document_workflow_os.router.service.create_incoming_correspondence")
    def test_create_incoming_correspondence(self, mock_create_incoming):
        mock_create_incoming.return_value = SimpleNamespace(
            id=5,
            tenant_id=1,
            direction="INCOMING",
            subject="Letter",
            correspondence_type="LETTER",
            sender_name="Sender",
            sender_organization="Org",
            recipient_name=None,
            recipient_organization=None,
            status="RECEIVED",
            registry_number=None,
            registry_date=None,
            received_at=None,
            sent_at=None,
            linked_document_id=None,
            linked_assignment_id=None,
            created_by_user_id=1,
            created_at="2025-01-01T00:00:00Z",
            updated_at="2025-01-01T00:00:00Z",
            archived_at=None,
        )
        resp = client.post(
            f"{BASE}/correspondence/incoming",
            headers=DOCS_HEADERS,
            json={"subject": "Letter", "correspondence_type": "LETTER"},
        )
        assert resp.status_code == 201
        assert resp.json()["direction"] == "INCOMING"


class TestPermissionBoundary:
    def test_viewer_cannot_create_document(self):
        resp = client.post(
            BASE,
            headers=VIEWER_HEADERS,
            json={"title": "Memo", "document_type": "INTERNAL_MEMO"},
        )
        assert resp.status_code == 403
