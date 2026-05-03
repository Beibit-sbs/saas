"""Phase LII — Student ID Card service (NFC/QR issuance & validation)."""
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

CARD_STATES = {"pending", "active", "suspended", "revoked", "expired"}
CARD_TYPES = {"nfc", "qr", "hybrid"}
ACCESS_RESULTS = {"granted", "denied"}


class StudentIdCardError(Exception):
    """Raised on invalid student ID card service input."""


@dataclass
class StudentIdCard:
    card_id: int
    student_id: int
    card_type: str
    card_number: str
    qr_code: str
    nfc_uid: str | None
    status: str
    tenant_id: int


@dataclass
class CardScanResult:
    scan_id: int
    card_id: int
    student_id: int
    location: str
    result: str
    tenant_id: int


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _generate_card_number(student_id: int, tenant_id: int) -> str:
    """Deterministic card number based on student + tenant."""
    raw = f"{tenant_id}:{student_id}:card"
    return hashlib.sha256(raw.encode()).hexdigest()[:16].upper()


def _generate_qr_payload(card_number: str, tenant_id: int) -> str:
    return f"UNIV-{tenant_id}-{card_number}"


# ---------------------------------------------------------------------------
# Card issuance
# ---------------------------------------------------------------------------


def issue_card(
    *,
    student_id: int,
    card_type: str,
    nfc_uid: str | None = None,
    tenant_id: int,
) -> StudentIdCard:
    """Issue a new student ID card (NFC, QR, or hybrid)."""
    if not student_id or student_id <= 0:
        raise StudentIdCardError("student_id is required")
    if card_type not in CARD_TYPES:
        raise StudentIdCardError(f"invalid card_type: {card_type!r}; must be one of {CARD_TYPES}")
    if card_type in ("nfc", "hybrid") and not nfc_uid:
        raise StudentIdCardError("nfc_uid is required for nfc/hybrid card types")

    card_number = _generate_card_number(student_id, tenant_id)
    qr_code = _generate_qr_payload(card_number, tenant_id)

    record = create_entity_for_tenant(
        "student_id_cards",
        {
            "student_id": student_id,
            "card_type": card_type,
            "card_number": card_number,
            "qr_code": qr_code,
            "nfc_uid": nfc_uid or "",
            "status": "active",
        },
        tenant_id,
    )

    try:
        EventPublisher.publish(
            tenant_id=tenant_id,
            event_type="id_card.issued",
            payload={"student_id": student_id, "card_type": card_type},
        )
    except Exception:
        pass

    return StudentIdCard(
        card_id=record["id"],
        student_id=student_id,
        card_type=card_type,
        card_number=card_number,
        qr_code=qr_code,
        nfc_uid=nfc_uid,
        status="active",
        tenant_id=tenant_id,
    )


def suspend_card(*, card_id: int, tenant_id: int) -> StudentIdCard:
    """Suspend an active student ID card."""
    if not card_id or card_id <= 0:
        raise StudentIdCardError("card_id is required")

    cards = list_entities_for_tenant("student_id_cards", tenant_id)
    matched = [c for c in cards if c["id"] == card_id]
    if not matched:
        raise StudentIdCardError(f"card {card_id} not found for tenant {tenant_id}")

    card = matched[0]
    if card["status"] != "active":
        raise StudentIdCardError(
            f"cannot suspend card in status {card['status']!r}; must be 'active'"
        )

    update_entity_for_tenant("student_id_cards", card_id, {"status": "suspended"}, tenant_id)

    try:
        EventPublisher.publish(
            tenant_id=tenant_id,
            event_type="id_card.suspended",
            payload={"student_id": card["student_id"], "card_id": card_id},
        )
    except Exception:
        pass

    return StudentIdCard(
        card_id=card_id,
        student_id=card["student_id"],
        card_type=card["card_type"],
        card_number=card["card_number"],
        qr_code=card["qr_code"],
        nfc_uid=card.get("nfc_uid") or None,
        status="suspended",
        tenant_id=tenant_id,
    )


def reactivate_card(*, card_id: int, tenant_id: int) -> StudentIdCard:
    """Reactivate a suspended card."""
    if not card_id or card_id <= 0:
        raise StudentIdCardError("card_id is required")

    cards = list_entities_for_tenant("student_id_cards", tenant_id)
    matched = [c for c in cards if c["id"] == card_id]
    if not matched:
        raise StudentIdCardError(f"card {card_id} not found for tenant {tenant_id}")

    card = matched[0]
    if card["status"] != "suspended":
        raise StudentIdCardError(
            f"cannot reactivate card in status {card['status']!r}; must be 'suspended'"
        )

    update_entity_for_tenant("student_id_cards", card_id, {"status": "active"}, tenant_id)

    return StudentIdCard(
        card_id=card_id,
        student_id=card["student_id"],
        card_type=card["card_type"],
        card_number=card["card_number"],
        qr_code=card["qr_code"],
        nfc_uid=card.get("nfc_uid") or None,
        status="active",
        tenant_id=tenant_id,
    )


def revoke_card(*, card_id: int, tenant_id: int) -> StudentIdCard:
    """Permanently revoke a student ID card."""
    if not card_id or card_id <= 0:
        raise StudentIdCardError("card_id is required")

    cards = list_entities_for_tenant("student_id_cards", tenant_id)
    matched = [c for c in cards if c["id"] == card_id]
    if not matched:
        raise StudentIdCardError(f"card {card_id} not found for tenant {tenant_id}")

    card = matched[0]
    if card["status"] == "revoked":
        raise StudentIdCardError("card is already revoked")

    update_entity_for_tenant("student_id_cards", card_id, {"status": "revoked"}, tenant_id)

    try:
        EventPublisher.publish(
            tenant_id=tenant_id,
            event_type="id_card.revoked",
            payload={"student_id": card["student_id"], "card_id": card_id},
        )
    except Exception:
        pass

    return StudentIdCard(
        card_id=card_id,
        student_id=card["student_id"],
        card_type=card["card_type"],
        card_number=card["card_number"],
        qr_code=card["qr_code"],
        nfc_uid=card.get("nfc_uid") or None,
        status="revoked",
        tenant_id=tenant_id,
    )


# ---------------------------------------------------------------------------
# Card scanning / access control
# ---------------------------------------------------------------------------


def scan_card(
    *,
    card_number: str,
    location: str,
    tenant_id: int,
) -> CardScanResult:
    """Scan a student ID card at a location; returns granted/denied."""
    if not card_number or not card_number.strip():
        raise StudentIdCardError("card_number is required")
    if not location or not location.strip():
        raise StudentIdCardError("location is required")

    cards = list_entities_for_tenant("student_id_cards", tenant_id)
    matched = [c for c in cards if c.get("card_number") == card_number.strip()]

    result = "denied"
    student_id = 0
    card_id = 0
    if matched:
        card = matched[0]
        card_id = card["id"]
        student_id = card["student_id"]
        if card["status"] == "active":
            result = "granted"

    record = create_entity_for_tenant(
        "card_scans",
        {
            "card_number": card_number.strip(),
            "location": location.strip(),
            "result": result,
            "student_id": student_id,
            "tenant_id": tenant_id,
        },
        tenant_id,
    )

    if result == "denied":
        try:
            EventPublisher.publish(
                tenant_id=tenant_id,
                event_type="id_card.access_denied",
                payload={"card_number": card_number.strip(), "location": location},
            )
        except Exception:
            pass

    return CardScanResult(
        scan_id=record["id"],
        card_id=card_id,
        student_id=student_id,
        location=location.strip(),
        result=result,
        tenant_id=tenant_id,
    )


def list_cards(*, student_id: int, tenant_id: int) -> list[StudentIdCard]:
    """Return all ID cards for a student."""
    rows = list_entities_for_tenant("student_id_cards", tenant_id)
    result = []
    for row in rows:
        if row.get("student_id") == student_id:
            result.append(
                StudentIdCard(
                    card_id=row["id"],
                    student_id=row["student_id"],
                    card_type=row["card_type"],
                    card_number=row["card_number"],
                    qr_code=row["qr_code"],
                    nfc_uid=row.get("nfc_uid") or None,
                    status=row["status"],
                    tenant_id=tenant_id,
                )
            )
    return result
