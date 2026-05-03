"""Phase XLVII: Digital Signature + Certificate Issuance Tests (15 tests)."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

import app.modules.digital_documents.service as svc

TENANT = "uni-xlvii"
BAD_TENANT = "bad-tenant"

# ─── Helpers ──────────────────────────────────────────────────────────────────

def _make_doc(doc_id="doc-1", status="DRAFT", cert=None, qr=None):
    return {
        "id": doc_id,
        "title": "Thesis",
        "doc_type": "THESIS",
        "content": "Some content",
        "status": status,
        "qr_code": qr,
        "signed_by": cert,
        "tenant_id": TENANT,
    }


def _make_cert(cert_id="cert-1", cert_type="GRADUATION", qr="qr-abc"):
    return {
        "id": cert_id,
        "student_id": "s-1",
        "cert_type": cert_type,
        "data": {},
        "qr_code": qr,
        "tenant_id": TENANT,
    }


# ─── 1. Constants ─────────────────────────────────────────────────────────────

class TestConstants:
    def test_doc_states_complete(self):
        assert {"DRAFT", "PENDING_SIGNATURE", "SIGNED", "REVOKED"} == svc.DOC_STATES

    def test_cert_types_complete(self):
        assert {"GRADUATION", "TRANSCRIPT", "DIPLOMA"} == svc.CERT_TYPES


# ─── 2. create_document ───────────────────────────────────────────────────────

class TestCreateDocument:
    def test_create_document_success(self):
        with patch("app.modules.digital_documents.service.create_entity_for_tenant") as m:
            m.return_value = _make_doc()
            doc = svc.create_document(TENANT, title="Thesis", doc_type="THESIS", content="text")
        assert doc["status"] == "DRAFT"
        assert m.called

    def test_create_document_missing_title(self):
        with pytest.raises(ValueError, match="title"):
            svc.create_document(TENANT, title="", doc_type="THESIS", content="text")

    def test_create_document_missing_content(self):
        with pytest.raises(ValueError, match="content"):
            svc.create_document(TENANT, title="T", doc_type="THESIS", content="")

    def test_create_document_invalid_tenant(self):
        with pytest.raises(ValueError, match="tenant"):
            svc.create_document(BAD_TENANT, title="T", doc_type="THESIS", content="c")


# ─── 3. request_signature ─────────────────────────────────────────────────────

class TestRequestSignature:
    def test_request_signature_success(self):
        doc = _make_doc()
        with patch("app.modules.digital_documents.service.list_entities_for_tenant", return_value=[doc]):
            result = svc.request_signature(TENANT, doc_id="doc-1", cert="CERT-001")
        assert result["status"] == "PENDING_SIGNATURE"
        assert result["signed_by"] == "CERT-001"

    def test_request_signature_wrong_status(self):
        doc = _make_doc(status="SIGNED")
        with patch("app.modules.digital_documents.service.list_entities_for_tenant", return_value=[doc]):
            with pytest.raises(ValueError, match="transition"):
                svc.request_signature(TENANT, doc_id="doc-1", cert="CERT-001")

    def test_request_signature_missing_cert(self):
        with pytest.raises(ValueError, match="cert"):
            svc.request_signature(TENANT, doc_id="doc-1", cert="")


# ─── 4. sign_document ─────────────────────────────────────────────────────────

class TestSignDocument:
    def test_sign_document_fires_event(self):
        doc = _make_doc(status="PENDING_SIGNATURE", cert="CERT-001")
        publisher = MagicMock()
        with patch("app.modules.digital_documents.service.list_entities_for_tenant", return_value=[doc]):
            with patch("app.modules.digital_documents.service.EventPublisher", publisher):
                result = svc.sign_document(TENANT, doc_id="doc-1")
        assert result["status"] == "SIGNED"
        assert result["qr_code"] is not None
        publisher.publish.assert_called_once()
        event_name = publisher.publish.call_args[0][0]
        assert event_name == "document.signed"

    def test_sign_document_wrong_status(self):
        doc = _make_doc(status="DRAFT")
        with patch("app.modules.digital_documents.service.list_entities_for_tenant", return_value=[doc]):
            with pytest.raises(ValueError, match="transition"):
                svc.sign_document(TENANT, doc_id="doc-1")

    def test_sign_document_not_found(self):
        with patch("app.modules.digital_documents.service.list_entities_for_tenant", return_value=[]):
            with pytest.raises(ValueError, match="not found"):
                svc.sign_document(TENANT, doc_id="no-such")


# ─── 5. revoke_document ───────────────────────────────────────────────────────

class TestRevokeDocument:
    def test_revoke_signed_success(self):
        doc = _make_doc(status="SIGNED", qr="qr-xyz")
        with patch("app.modules.digital_documents.service.list_entities_for_tenant", return_value=[doc]):
            result = svc.revoke_document(TENANT, doc_id="doc-1")
        assert result["status"] == "REVOKED"

    def test_revoke_draft_raises(self):
        doc = _make_doc(status="DRAFT")
        with patch("app.modules.digital_documents.service.list_entities_for_tenant", return_value=[doc]):
            with pytest.raises(ValueError, match="transition"):
                svc.revoke_document(TENANT, doc_id="doc-1")


# ─── 6. issue_certificate ─────────────────────────────────────────────────────

class TestIssueCertificate:
    def test_issue_certificate_graduation_fires_event(self):
        publisher = MagicMock()
        with patch("app.modules.digital_documents.service.create_entity_for_tenant", return_value=_make_cert()):
            with patch("app.modules.digital_documents.service.EventPublisher", publisher):
                cert = svc.issue_certificate(TENANT, student_id="s-1", cert_type="GRADUATION", data={})
        assert cert["cert_type"] == "GRADUATION"
        publisher.publish.assert_called_once()
        assert publisher.publish.call_args[0][0] == "certificate.issued"

    def test_issue_certificate_invalid_type(self):
        with pytest.raises(ValueError, match="cert_type"):
            svc.issue_certificate(TENANT, student_id="s-1", cert_type="UNKNOWN", data={})

    def test_issue_certificate_missing_student(self):
        with pytest.raises(ValueError, match="student_id"):
            svc.issue_certificate(TENANT, student_id="", cert_type="DIPLOMA", data={})


# ─── 7. verify_document ───────────────────────────────────────────────────────

class TestVerifyDocument:
    def test_verify_finds_signed_document(self):
        doc = _make_doc(status="SIGNED", qr="qr-signed-doc")
        publisher = MagicMock()
        with patch("app.modules.digital_documents.service.list_entities_for_tenant", return_value=[doc]):
            with patch("app.modules.digital_documents.service.EventPublisher", publisher):
                result = svc.verify_document(TENANT, qr_code="qr-signed-doc")
        assert result["found"] is True
        assert result["entity_type"] == "document"
        assert result["status"] == "SIGNED"
        publisher.publish.assert_called_once()
        assert publisher.publish.call_args[0][0] == "verification.requested"

    def test_verify_not_found_returns_false(self):
        publisher = MagicMock()
        with patch("app.modules.digital_documents.service.list_entities_for_tenant", return_value=[]):
            with patch("app.modules.digital_documents.service.EventPublisher", publisher):
                result = svc.verify_document(TENANT, qr_code="unknown-qr")
        assert result["found"] is False

    def test_verify_missing_qr_raises(self):
        with pytest.raises(ValueError, match="qr_code"):
            svc.verify_document(TENANT, qr_code="")


# ─── 8. list_documents ────────────────────────────────────────────────────────

class TestListDocuments:
    def test_list_documents_filter_by_status(self):
        docs = [
            _make_doc("d1", "DRAFT"),
            _make_doc("d2", "SIGNED"),
            _make_doc("d3", "DRAFT"),
        ]
        with patch("app.modules.digital_documents.service.list_entities_for_tenant", return_value=docs):
            result = svc.list_documents(TENANT, status="DRAFT")
        assert len(result) == 2
        assert all(d["status"] == "DRAFT" for d in result)
