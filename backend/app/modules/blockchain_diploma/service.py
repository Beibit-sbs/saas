"""Phase LVII — Blockchain Diploma Verification service."""
from __future__ import annotations

import hashlib
import secrets
from dataclasses import dataclass

from app.modules.university_core.tenant_entity_api import (
    create_entity_for_tenant,
    list_entities_for_tenant,
    update_entity_for_tenant,
)
from app.platform.events.publisher import EventPublisher

DIPLOMA_STATUSES = {"issued", "revoked", "expired"}
VERIFICATION_RESULTS = {"valid", "invalid", "revoked", "not_found"}


class BlockchainDiplomaError(Exception):
    """Raised on invalid Blockchain Diploma service input."""


@dataclass
class Diploma:
    diploma_id: int
    tenant_id: int
    student_id: int
    degree: str
    issued_year: int
    status: str
    tx_hash: str
    certificate_hash: str


@dataclass
class VerificationRecord:
    record_id: int
    tenant_id: int
    diploma_id: int | None
    certificate_hash: str
    result: str
    verifier_id: int | None


@dataclass
class RevocationRecord:
    record_id: int
    tenant_id: int
    diploma_id: int
    reason: str


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _compute_certificate_hash(student_id: int, degree: str, issued_year: int, tenant_id: int) -> str:
    """Compute a deterministic SHA-256 hash for the diploma certificate."""
    raw = f"{tenant_id}:{student_id}:{degree}:{issued_year}"
    return hashlib.sha256(raw.encode()).hexdigest()


def _generate_tx_hash() -> str:
    """Simulate a blockchain transaction hash (32 random bytes, hex)."""
    return "0x" + secrets.token_hex(32)


# ---------------------------------------------------------------------------
# Diploma issuance
# ---------------------------------------------------------------------------


def issue_diploma(
    *,
    student_id: int,
    degree: str,
    specialization: str,
    issued_year: int,
    gpa: float | None,
    tenant_id: int,
) -> Diploma:
    """Issue a new blockchain-anchored diploma."""
    if student_id <= 0:
        raise BlockchainDiplomaError("student_id is required")
    if not degree or not degree.strip():
        raise BlockchainDiplomaError("degree is required")
    if issued_year < 1900 or issued_year > 2200:
        raise BlockchainDiplomaError("issued_year is out of range")

    certificate_hash = _compute_certificate_hash(student_id, degree, issued_year, tenant_id)
    tx_hash = _generate_tx_hash()

    record = create_entity_for_tenant(
        "blockchain_diplomas",
        {
            "student_id": student_id,
            "degree": degree.strip(),
            "specialization": specialization.strip() if specialization else "",
            "issued_year": issued_year,
            "gpa": gpa,
            "certificate_hash": certificate_hash,
            "tx_hash": tx_hash,
            "status": "issued",
        },
        tenant_id,
    )

    try:
        EventPublisher.publish(
            tenant_id=tenant_id,
            event_type="blockchain_diploma.issued",
            payload={
                "diploma_id": record["id"],
                "student_id": student_id,
                "tx_hash": tx_hash,
                "certificate_hash": certificate_hash,
            },
        )
    except Exception:
        pass

    return Diploma(
        diploma_id=record["id"],
        tenant_id=tenant_id,
        student_id=student_id,
        degree=degree,
        issued_year=issued_year,
        status="issued",
        tx_hash=tx_hash,
        certificate_hash=certificate_hash,
    )


def revoke_diploma(*, diploma_id: int, reason: str, tenant_id: int) -> Diploma:
    """Revoke a previously issued diploma."""
    if not reason or not reason.strip():
        raise BlockchainDiplomaError("reason is required")

    diplomas = list_entities_for_tenant("blockchain_diplomas", tenant_id)
    matched = [d for d in diplomas if d["id"] == diploma_id]
    if not matched:
        raise BlockchainDiplomaError(f"diploma {diploma_id} not found")

    diploma = matched[0]
    if diploma["status"] == "revoked":
        raise BlockchainDiplomaError("diploma is already revoked")

    update_entity_for_tenant(
        "blockchain_diplomas", diploma_id, {"status": "revoked"}, tenant_id
    )

    create_entity_for_tenant(
        "diploma_revocations",
        {"diploma_id": diploma_id, "reason": reason.strip()},
        tenant_id,
    )

    try:
        EventPublisher.publish(
            tenant_id=tenant_id,
            event_type="blockchain_diploma.revoked",
            payload={"diploma_id": diploma_id, "reason": reason},
        )
    except Exception:
        pass

    return Diploma(
        diploma_id=diploma_id,
        tenant_id=tenant_id,
        student_id=diploma["student_id"],
        degree=diploma["degree"],
        issued_year=diploma["issued_year"],
        status="revoked",
        tx_hash=diploma["tx_hash"],
        certificate_hash=diploma["certificate_hash"],
    )


def get_diploma(*, diploma_id: int, tenant_id: int) -> Diploma:
    """Retrieve a diploma by ID."""
    diplomas = list_entities_for_tenant("blockchain_diplomas", tenant_id)
    matched = [d for d in diplomas if d["id"] == diploma_id]
    if not matched:
        raise BlockchainDiplomaError(f"diploma {diploma_id} not found")

    d = matched[0]
    return Diploma(
        diploma_id=diploma_id,
        tenant_id=tenant_id,
        student_id=d["student_id"],
        degree=d["degree"],
        issued_year=d["issued_year"],
        status=d["status"],
        tx_hash=d["tx_hash"],
        certificate_hash=d["certificate_hash"],
    )


def list_student_diplomas(*, student_id: int, tenant_id: int) -> list[Diploma]:
    """List all diplomas for a student."""
    rows = list_entities_for_tenant("blockchain_diplomas", tenant_id)
    return [
        Diploma(
            diploma_id=r["id"],
            tenant_id=tenant_id,
            student_id=r["student_id"],
            degree=r["degree"],
            issued_year=r["issued_year"],
            status=r["status"],
            tx_hash=r["tx_hash"],
            certificate_hash=r["certificate_hash"],
        )
        for r in rows
        if r.get("student_id") == student_id
    ]


# ---------------------------------------------------------------------------
# Verification
# ---------------------------------------------------------------------------


def verify_diploma(
    *,
    certificate_hash: str,
    verifier_id: int | None,
    tenant_id: int,
) -> VerificationRecord:
    """Verify a diploma by its certificate hash."""
    if not certificate_hash or not certificate_hash.strip():
        raise BlockchainDiplomaError("certificate_hash is required")

    diplomas = list_entities_for_tenant("blockchain_diplomas", tenant_id)
    matched = [d for d in diplomas if d.get("certificate_hash") == certificate_hash.strip()]

    if not matched:
        result = "not_found"
        diploma_id = None
    else:
        diploma = matched[0]
        diploma_id = diploma["id"]
        if diploma["status"] == "revoked":
            result = "revoked"
        elif diploma["status"] == "expired":
            result = "invalid"
        else:
            result = "valid"

    record = create_entity_for_tenant(
        "diploma_verifications",
        {
            "certificate_hash": certificate_hash.strip(),
            "diploma_id": diploma_id,
            "result": result,
            "verifier_id": verifier_id,
        },
        tenant_id,
    )

    try:
        EventPublisher.publish(
            tenant_id=tenant_id,
            event_type="blockchain_diploma.verified",
            payload={
                "verification_id": record["id"],
                "certificate_hash": certificate_hash,
                "result": result,
            },
        )
    except Exception:
        pass

    return VerificationRecord(
        record_id=record["id"],
        tenant_id=tenant_id,
        diploma_id=diploma_id,
        certificate_hash=certificate_hash,
        result=result,
        verifier_id=verifier_id,
    )


def get_verification_history(*, diploma_id: int, tenant_id: int) -> list[VerificationRecord]:
    """Get all verification attempts for a diploma."""
    rows = list_entities_for_tenant("diploma_verifications", tenant_id)
    return [
        VerificationRecord(
            record_id=r["id"],
            tenant_id=tenant_id,
            diploma_id=r.get("diploma_id"),
            certificate_hash=r["certificate_hash"],
            result=r["result"],
            verifier_id=r.get("verifier_id"),
        )
        for r in rows
        if r.get("diploma_id") == diploma_id
    ]
