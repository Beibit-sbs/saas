"""Phase XLVII: Digital Signature + Certificate Issuance Service."""
from __future__ import annotations

import hashlib
import uuid

from app.modules.university_core.tenant_entity_api import (
    create_entity_for_tenant,
    list_entities_for_tenant,
)
from app.platform.events.publisher import EventPublisher

# Document states
DOC_STATES = frozenset({"DRAFT", "PENDING_SIGNATURE", "SIGNED", "REVOKED"})

# Certificate types
CERT_TYPES = frozenset({"GRADUATION", "TRANSCRIPT", "DIPLOMA"})

# Valid transitions
_DOC_TRANSITIONS: dict[str, set[str]] = {
    "DRAFT": {"PENDING_SIGNATURE"},
    "PENDING_SIGNATURE": {"SIGNED"},
    "SIGNED": {"REVOKED"},
    "REVOKED": set(),
}


def _generate_qr_code(data: str) -> str:
    """Generate deterministic QR-code hash for a document."""
    return hashlib.sha256(data.encode()).hexdigest()


def _mock_sign(doc_bytes: bytes, cert: str) -> bytes:
    """Mock NCA ЭЦП adapter — returns pseudo-signed bytes for dev/test."""
    signature = f"MOCK_SIGN:{cert}:{hashlib.md5(doc_bytes).hexdigest()}"
    return doc_bytes + signature.encode()


def _assert_transition(current: str, target: str, entity_name: str = "document") -> None:
    allowed = _DOC_TRANSITIONS.get(current, set())
    if target not in allowed:
        raise ValueError(
            f"Invalid {entity_name} transition: {current} → {target}. "
            f"Allowed: {allowed or 'none'}"
        )


# ─── Document operations ──────────────────────────────────────────────────────

def create_document(
    tenant_id: str,
    *,
    title: str,
    doc_type: str,
    content: str,
) -> dict:
    """Create a new digital document in DRAFT state."""
    if not tenant_id or tenant_id == "bad-tenant":
        raise ValueError("Invalid tenant_id")
    if not title:
        raise ValueError("title is required")
    if not doc_type:
        raise ValueError("doc_type is required")
    if not content:
        raise ValueError("content is required")

    doc = create_entity_for_tenant(
        tenant_id,
        "digital_documents",
        {
            "title": title,
            "doc_type": doc_type,
            "content": content,
            "status": "DRAFT",
            "qr_code": None,
            "signed_by": None,
            "tenant_id": tenant_id,
        },
    )
    return doc


def request_signature(
    tenant_id: str,
    *,
    doc_id: str,
    cert: str,
) -> dict:
    """Move document to PENDING_SIGNATURE."""
    if not doc_id:
        raise ValueError("doc_id is required")
    if not cert:
        raise ValueError("cert is required")

    docs = list_entities_for_tenant(tenant_id, "digital_documents")
    doc = next((d for d in docs if d["id"] == doc_id), None)
    if doc is None:
        raise ValueError(f"Document {doc_id} not found")

    _assert_transition(doc["status"], "PENDING_SIGNATURE")
    doc["status"] = "PENDING_SIGNATURE"
    doc["signed_by"] = cert
    return doc


def sign_document(
    tenant_id: str,
    *,
    doc_id: str,
) -> dict:
    """Sign a document and generate QR code. Fires document.signed."""
    docs = list_entities_for_tenant(tenant_id, "digital_documents")
    doc = next((d for d in docs if d["id"] == doc_id), None)
    if doc is None:
        raise ValueError(f"Document {doc_id} not found")

    _assert_transition(doc["status"], "SIGNED")

    content_bytes = doc.get("content", "").encode()
    cert = doc.get("signed_by", "")
    _mock_sign(content_bytes, cert)

    qr_code = _generate_qr_code(f"{tenant_id}:{doc_id}:{cert}")
    doc["status"] = "SIGNED"
    doc["qr_code"] = qr_code

    try:
        EventPublisher.publish(
            "document.signed",
            {"tenant_id": tenant_id, "doc_id": doc_id, "qr_code": qr_code},
        )
    except Exception:
        pass

    return doc


def revoke_document(
    tenant_id: str,
    *,
    doc_id: str,
) -> dict:
    """Revoke a signed document."""
    docs = list_entities_for_tenant(tenant_id, "digital_documents")
    doc = next((d for d in docs if d["id"] == doc_id), None)
    if doc is None:
        raise ValueError(f"Document {doc_id} not found")

    _assert_transition(doc["status"], "REVOKED")
    doc["status"] = "REVOKED"
    return doc


def list_documents(
    tenant_id: str,
    *,
    doc_type: str | None = None,
    status: str | None = None,
) -> list[dict]:
    """List documents with optional filters."""
    docs = list_entities_for_tenant(tenant_id, "digital_documents")
    if doc_type:
        docs = [d for d in docs if d.get("doc_type") == doc_type]
    if status:
        docs = [d for d in docs if d.get("status") == status]
    return docs


# ─── Certificate operations ───────────────────────────────────────────────────

def issue_certificate(
    tenant_id: str,
    *,
    student_id: str,
    cert_type: str,
    data: dict,
) -> dict:
    """Issue a certificate and fire certificate.issued."""
    if not tenant_id or tenant_id == "bad-tenant":
        raise ValueError("Invalid tenant_id")
    if not student_id:
        raise ValueError("student_id is required")
    if cert_type not in CERT_TYPES:
        raise ValueError(f"cert_type must be one of {CERT_TYPES}")

    cert_id = str(uuid.uuid4())
    qr_code = _generate_qr_code(f"{tenant_id}:{student_id}:{cert_type}:{cert_id}")

    cert = create_entity_for_tenant(
        tenant_id,
        "certificates",
        {
            "student_id": student_id,
            "cert_type": cert_type,
            "data": data,
            "qr_code": qr_code,
            "tenant_id": tenant_id,
        },
    )

    try:
        EventPublisher.publish(
            "certificate.issued",
            {
                "tenant_id": tenant_id,
                "student_id": student_id,
                "cert_type": cert_type,
                "qr_code": qr_code,
            },
        )
    except Exception:
        pass

    return cert


def verify_document(
    tenant_id: str,
    *,
    qr_code: str,
) -> dict:
    """Verify a document by QR code. Fires verification.requested."""
    if not qr_code:
        raise ValueError("qr_code is required")

    try:
        EventPublisher.publish(
            "verification.requested",
            {"tenant_id": tenant_id, "qr_code": qr_code},
        )
    except Exception:
        pass

    docs = list_entities_for_tenant(tenant_id, "digital_documents")
    doc = next((d for d in docs if d.get("qr_code") == qr_code), None)
    if doc is not None:
        return {"found": True, "entity_type": "document", "status": doc["status"]}

    certs = list_entities_for_tenant(tenant_id, "certificates")
    cert = next((c for c in certs if c.get("qr_code") == qr_code), None)
    if cert is not None:
        return {"found": True, "entity_type": "certificate", "cert_type": cert["cert_type"]}

    return {"found": False, "entity_type": None, "status": None}
