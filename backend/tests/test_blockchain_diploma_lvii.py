"""Phase LVII — Blockchain Diploma Verification — tests (25 cases)."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

MODULE = "app.modules.blockchain_diploma.service"


def _make_diploma_record(
    id: int = 1,
    student_id: int = 101,
    degree: str = "BSc Computer Science",
    specialization: str = "AI",
    issued_year: int = 2024,
    gpa: float | None = 3.8,
    certificate_hash: str = "deadbeef" * 8,
    tx_hash: str = "0x" + "aa" * 32,
    status: str = "issued",
    tenant_id: int = 1,
) -> dict:
    return dict(
        id=id,
        student_id=student_id,
        degree=degree,
        specialization=specialization,
        issued_year=issued_year,
        gpa=gpa,
        certificate_hash=certificate_hash,
        tx_hash=tx_hash,
        status=status,
        tenant_id=tenant_id,
    )


# ─────────────────────────────────────────────
# issue_diploma
# ─────────────────────────────────────────────


def test_issue_diploma_success():
    created = _make_diploma_record()
    with (
        patch(f"{MODULE}.create_entity_for_tenant", return_value=created) as mock_create,
        patch(f"{MODULE}.EventPublisher") as mock_ep,
    ):
        from app.modules.blockchain_diploma import service

        diploma = service.issue_diploma(
            student_id=101,
            degree="BSc Computer Science",
            specialization="AI",
            issued_year=2024,
            gpa=3.8,
            tenant_id=1,
        )

    assert diploma.diploma_id == 1
    assert diploma.student_id == 101
    assert diploma.degree == "BSc Computer Science"
    assert diploma.status == "issued"
    assert diploma.tx_hash.startswith("0x")
    mock_create.assert_called_once()
    mock_ep.publish.assert_called_once()


def test_issue_diploma_event_fields():
    created = _make_diploma_record()
    with (
        patch(f"{MODULE}.create_entity_for_tenant", return_value=created),
        patch(f"{MODULE}.EventPublisher") as mock_ep,
    ):
        from app.modules.blockchain_diploma import service

        service.issue_diploma(
            student_id=101,
            degree="MSc Data Science",
            specialization="",
            issued_year=2023,
            gpa=None,
            tenant_id=2,
        )

    call_kwargs = mock_ep.publish.call_args.kwargs
    assert call_kwargs["event_type"] == "blockchain_diploma.issued"
    assert call_kwargs["tenant_id"] == 2


def test_issue_diploma_invalid_student_id():
    from app.modules.blockchain_diploma.service import BlockchainDiplomaError, issue_diploma

    with pytest.raises(BlockchainDiplomaError, match="student_id"):
        issue_diploma(student_id=0, degree="BSc", specialization="", issued_year=2024, gpa=None, tenant_id=1)


def test_issue_diploma_empty_degree():
    from app.modules.blockchain_diploma.service import BlockchainDiplomaError, issue_diploma

    with pytest.raises(BlockchainDiplomaError, match="degree"):
        issue_diploma(student_id=1, degree="   ", specialization="", issued_year=2024, gpa=None, tenant_id=1)


def test_issue_diploma_invalid_year():
    from app.modules.blockchain_diploma.service import BlockchainDiplomaError, issue_diploma

    with pytest.raises(BlockchainDiplomaError, match="issued_year"):
        issue_diploma(student_id=1, degree="BSc", specialization="", issued_year=1800, gpa=None, tenant_id=1)


def test_issue_diploma_event_suppressed_on_error():
    """Event publisher failure must not propagate."""
    created = _make_diploma_record()
    with (
        patch(f"{MODULE}.create_entity_for_tenant", return_value=created),
        patch(f"{MODULE}.EventPublisher") as mock_ep,
    ):
        mock_ep.publish.side_effect = RuntimeError("broker down")
        from app.modules.blockchain_diploma import service

        diploma = service.issue_diploma(
            student_id=101, degree="BSc", specialization="", issued_year=2024, gpa=None, tenant_id=1
        )
    assert diploma.diploma_id == 1


# ─────────────────────────────────────────────
# revoke_diploma
# ─────────────────────────────────────────────


def test_revoke_diploma_success():
    existing = _make_diploma_record()
    with (
        patch(f"{MODULE}.list_entities_for_tenant", return_value=[existing]),
        patch(f"{MODULE}.update_entity_for_tenant") as mock_update,
        patch(f"{MODULE}.create_entity_for_tenant") as mock_create,
        patch(f"{MODULE}.EventPublisher") as mock_ep,
    ):
        from app.modules.blockchain_diploma import service

        diploma = service.revoke_diploma(diploma_id=1, reason="Fraud detected", tenant_id=1)

    assert diploma.status == "revoked"
    mock_update.assert_called_once_with("blockchain_diplomas", 1, {"status": "revoked"}, 1)
    mock_create.assert_called_once()
    mock_ep.publish.assert_called_once()


def test_revoke_diploma_not_found():
    with patch(f"{MODULE}.list_entities_for_tenant", return_value=[]):
        from app.modules.blockchain_diploma.service import BlockchainDiplomaError, revoke_diploma

        with pytest.raises(BlockchainDiplomaError, match="not found"):
            revoke_diploma(diploma_id=999, reason="fraud", tenant_id=1)


def test_revoke_diploma_already_revoked():
    existing = _make_diploma_record(status="revoked")
    with patch(f"{MODULE}.list_entities_for_tenant", return_value=[existing]):
        from app.modules.blockchain_diploma.service import BlockchainDiplomaError, revoke_diploma

        with pytest.raises(BlockchainDiplomaError, match="already revoked"):
            revoke_diploma(diploma_id=1, reason="fraud", tenant_id=1)


def test_revoke_diploma_missing_reason():
    from app.modules.blockchain_diploma.service import BlockchainDiplomaError, revoke_diploma

    with pytest.raises(BlockchainDiplomaError, match="reason"):
        revoke_diploma(diploma_id=1, reason="", tenant_id=1)


def test_revoke_diploma_event_suppressed_on_error():
    existing = _make_diploma_record()
    with (
        patch(f"{MODULE}.list_entities_for_tenant", return_value=[existing]),
        patch(f"{MODULE}.update_entity_for_tenant"),
        patch(f"{MODULE}.create_entity_for_tenant"),
        patch(f"{MODULE}.EventPublisher") as mock_ep,
    ):
        mock_ep.publish.side_effect = RuntimeError("broker down")
        from app.modules.blockchain_diploma import service

        diploma = service.revoke_diploma(diploma_id=1, reason="Fraud", tenant_id=1)
    assert diploma.status == "revoked"


# ─────────────────────────────────────────────
# get_diploma
# ─────────────────────────────────────────────


def test_get_diploma_success():
    existing = _make_diploma_record()
    with patch(f"{MODULE}.list_entities_for_tenant", return_value=[existing]):
        from app.modules.blockchain_diploma import service

        diploma = service.get_diploma(diploma_id=1, tenant_id=1)

    assert diploma.diploma_id == 1
    assert diploma.degree == "BSc Computer Science"


def test_get_diploma_not_found():
    with patch(f"{MODULE}.list_entities_for_tenant", return_value=[]):
        from app.modules.blockchain_diploma.service import BlockchainDiplomaError, get_diploma

        with pytest.raises(BlockchainDiplomaError, match="not found"):
            get_diploma(diploma_id=999, tenant_id=1)


# ─────────────────────────────────────────────
# list_student_diplomas
# ─────────────────────────────────────────────


def test_list_student_diplomas_returns_filtered():
    rows = [
        _make_diploma_record(id=1, student_id=101),
        _make_diploma_record(id=2, student_id=202),
        _make_diploma_record(id=3, student_id=101),
    ]
    with patch(f"{MODULE}.list_entities_for_tenant", return_value=rows):
        from app.modules.blockchain_diploma import service

        result = service.list_student_diplomas(student_id=101, tenant_id=1)

    assert len(result) == 2
    assert all(d.student_id == 101 for d in result)


def test_list_student_diplomas_empty():
    with patch(f"{MODULE}.list_entities_for_tenant", return_value=[]):
        from app.modules.blockchain_diploma import service

        result = service.list_student_diplomas(student_id=999, tenant_id=1)

    assert result == []


# ─────────────────────────────────────────────
# verify_diploma
# ─────────────────────────────────────────────


def test_verify_diploma_valid():
    cert_hash = "abc123"
    existing = _make_diploma_record(certificate_hash=cert_hash, status="issued")
    verification_record = {"id": 1}
    with (
        patch(f"{MODULE}.list_entities_for_tenant", return_value=[existing]),
        patch(f"{MODULE}.create_entity_for_tenant", return_value=verification_record),
        patch(f"{MODULE}.EventPublisher"),
    ):
        from app.modules.blockchain_diploma import service

        record = service.verify_diploma(certificate_hash=cert_hash, verifier_id=55, tenant_id=1)

    assert record.result == "valid"
    assert record.diploma_id == 1


def test_verify_diploma_revoked():
    cert_hash = "abc123"
    existing = _make_diploma_record(certificate_hash=cert_hash, status="revoked")
    with (
        patch(f"{MODULE}.list_entities_for_tenant", return_value=[existing]),
        patch(f"{MODULE}.create_entity_for_tenant", return_value={"id": 2}),
        patch(f"{MODULE}.EventPublisher"),
    ):
        from app.modules.blockchain_diploma import service

        record = service.verify_diploma(certificate_hash=cert_hash, verifier_id=None, tenant_id=1)

    assert record.result == "revoked"


def test_verify_diploma_not_found():
    with (
        patch(f"{MODULE}.list_entities_for_tenant", return_value=[]),
        patch(f"{MODULE}.create_entity_for_tenant", return_value={"id": 3}),
        patch(f"{MODULE}.EventPublisher"),
    ):
        from app.modules.blockchain_diploma import service

        record = service.verify_diploma(certificate_hash="unknown_hash", verifier_id=None, tenant_id=1)

    assert record.result == "not_found"
    assert record.diploma_id is None


def test_verify_diploma_empty_hash():
    from app.modules.blockchain_diploma.service import BlockchainDiplomaError, verify_diploma

    with pytest.raises(BlockchainDiplomaError, match="certificate_hash"):
        verify_diploma(certificate_hash="   ", verifier_id=None, tenant_id=1)


def test_verify_diploma_event_published():
    cert_hash = "xyz789"
    existing = _make_diploma_record(certificate_hash=cert_hash, status="issued")
    with (
        patch(f"{MODULE}.list_entities_for_tenant", return_value=[existing]),
        patch(f"{MODULE}.create_entity_for_tenant", return_value={"id": 5}),
        patch(f"{MODULE}.EventPublisher") as mock_ep,
    ):
        from app.modules.blockchain_diploma import service

        service.verify_diploma(certificate_hash=cert_hash, verifier_id=10, tenant_id=1)

    call_kwargs = mock_ep.publish.call_args.kwargs
    assert call_kwargs["event_type"] == "blockchain_diploma.verified"


def test_verify_diploma_event_suppressed_on_error():
    cert_hash = "xyz789"
    existing = _make_diploma_record(certificate_hash=cert_hash, status="issued")
    with (
        patch(f"{MODULE}.list_entities_for_tenant", return_value=[existing]),
        patch(f"{MODULE}.create_entity_for_tenant", return_value={"id": 5}),
        patch(f"{MODULE}.EventPublisher") as mock_ep,
    ):
        mock_ep.publish.side_effect = RuntimeError("broker down")
        from app.modules.blockchain_diploma import service

        record = service.verify_diploma(certificate_hash=cert_hash, verifier_id=10, tenant_id=1)
    assert record.result == "valid"


# ─────────────────────────────────────────────
# get_verification_history
# ─────────────────────────────────────────────


def test_get_verification_history_returns_filtered():
    rows = [
        {"id": 1, "diploma_id": 1, "certificate_hash": "aaa", "result": "valid", "verifier_id": 10},
        {"id": 2, "diploma_id": 2, "certificate_hash": "bbb", "result": "revoked", "verifier_id": None},
        {"id": 3, "diploma_id": 1, "certificate_hash": "aaa", "result": "valid", "verifier_id": 20},
    ]
    with patch(f"{MODULE}.list_entities_for_tenant", return_value=rows):
        from app.modules.blockchain_diploma import service

        history = service.get_verification_history(diploma_id=1, tenant_id=1)

    assert len(history) == 2
    assert all(h.diploma_id == 1 for h in history)


def test_get_verification_history_empty():
    with patch(f"{MODULE}.list_entities_for_tenant", return_value=[]):
        from app.modules.blockchain_diploma import service

        history = service.get_verification_history(diploma_id=999, tenant_id=1)

    assert history == []


# ─────────────────────────────────────────────
# certificate_hash determinism
# ─────────────────────────────────────────────


def test_certificate_hash_is_deterministic():
    from app.modules.blockchain_diploma.service import _compute_certificate_hash

    h1 = _compute_certificate_hash(101, "BSc CS", 2024, 1)
    h2 = _compute_certificate_hash(101, "BSc CS", 2024, 1)
    assert h1 == h2
    assert len(h1) == 64  # SHA-256 hex


def test_certificate_hash_differs_by_student():
    from app.modules.blockchain_diploma.service import _compute_certificate_hash

    h1 = _compute_certificate_hash(101, "BSc CS", 2024, 1)
    h2 = _compute_certificate_hash(102, "BSc CS", 2024, 1)
    assert h1 != h2


# ─────────────────────────────────────────────
# tx_hash uniqueness
# ─────────────────────────────────────────────


def test_tx_hash_unique_per_call():
    from app.modules.blockchain_diploma.service import _generate_tx_hash

    hashes = {_generate_tx_hash() for _ in range(50)}
    assert len(hashes) == 50
