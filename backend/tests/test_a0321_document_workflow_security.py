"""A-032.1 document workflow security tests."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from sqlalchemy.orm import Session

from app.main import app
from app.modules.document_workflow_os.dependencies import get_doc_workflow_db
from tests.conftest import ADMIN_HEADERS, _auth_headers, client

BASE = "/api/admin/documents"
VIEWER_HEADERS = _auth_headers("viewer-security@example.com", ["viewer"], tenant_id=1)
REVIEWER_HEADERS = _auth_headers("reviewer-security@example.com", ["reviewer"], tenant_id=1)


@pytest.fixture(autouse=True)
def _override_db():
    session = MagicMock(spec=Session)
    app.dependency_overrides[get_doc_workflow_db] = lambda: session
    yield
    app.dependency_overrides.pop(get_doc_workflow_db, None)


class TestTenantBoundary:
    def test_cross_tenant_header_override_denied(self):
        resp = client.get(BASE, headers={**ADMIN_HEADERS, "X-Tenant-ID": "2"})
        assert resp.status_code == 403

    def test_body_tenant_spoof_rejected_by_schema(self):
        resp = client.post(
            BASE,
            headers=ADMIN_HEADERS,
            json={
                "title": "Memo",
                "document_type": "INTERNAL_MEMO",
                "tenant_id": 999,
            },
        )
        assert resp.status_code in (201, 400, 403, 422)
        if resp.status_code == 201:
            assert resp.json()["tenant_id"] == 1


class TestPermissionBoundary:
    def test_viewer_cannot_archive_document(self):
        resp = client.post(f"{BASE}/1/archive", headers=VIEWER_HEADERS, json={"version": 1})
        assert resp.status_code == 403

    def test_reviewer_cannot_register_decree(self):
        resp = client.post(
            f"{BASE}/decrees/1/register",
            headers=REVIEWER_HEADERS,
            json={"registry_number": "DEC-1", "version": 1},
        )
        assert resp.status_code == 403

    def test_viewer_cannot_link_assignment(self):
        resp = client.post(
            f"{BASE}/1/link-assignment/99",
            headers=VIEWER_HEADERS,
            json={"link_type": "SOURCE_DOCUMENT"},
        )
        assert resp.status_code == 403
