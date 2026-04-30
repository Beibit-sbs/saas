"""W79 — academic_records: Published Record Immutability Lock.

Business invariant: once an academic record reaches 'published' status,
it is an official institutional document and must not be mutated via direct update.
update_record() must raise ValueError for any published record.
"""
from __future__ import annotations

from unittest.mock import patch

import pytest

from app.modules.academic_records.service import _check_record_not_published


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _make_record(record_id: int, status: str, tenant_id: int = 1) -> dict:
    return {"id": record_id, "tenant_id": tenant_id, "status": status, "data": "x"}


# ---------------------------------------------------------------------------
# 1. _check_record_not_published guard exists
# ---------------------------------------------------------------------------

def test_w79_check_record_not_published_guard_exists():
    assert callable(_check_record_not_published), (
        "_check_record_not_published not found in academic_records.service"
    )


# ---------------------------------------------------------------------------
# 2. update_record raises ValueError for a published record
# ---------------------------------------------------------------------------

def test_w79_update_blocked_when_record_is_published():
    records = [_make_record(record_id=42, status="published")]

    with patch(
        "app.modules.academic_records.service.list_entities_for_tenant",
        return_value=records,
    ):
        with pytest.raises(ValueError) as exc_info:
            _check_record_not_published(record_id=42, tenant_id=1)

    assert "published" in str(exc_info.value).lower()
    assert "42" in str(exc_info.value)


# ---------------------------------------------------------------------------
# 3. update_record proceeds for a draft record
# ---------------------------------------------------------------------------

def test_w79_update_allowed_when_record_is_draft():
    records = [_make_record(record_id=10, status="draft")]

    with patch(
        "app.modules.academic_records.service.list_entities_for_tenant",
        return_value=records,
    ):
        # Must not raise
        _check_record_not_published(record_id=10, tenant_id=1)


# ---------------------------------------------------------------------------
# 4. update_record proceeds for a pending record
# ---------------------------------------------------------------------------

def test_w79_update_allowed_when_record_is_pending():
    records = [_make_record(record_id=7, status="pending")]

    with patch(
        "app.modules.academic_records.service.list_entities_for_tenant",
        return_value=records,
    ):
        _check_record_not_published(record_id=7, tenant_id=1)


# ---------------------------------------------------------------------------
# 5. Guard silently proceeds when record not found (not-found is separate concern)
# ---------------------------------------------------------------------------

def test_w79_update_allowed_when_record_not_found():
    with patch(
        "app.modules.academic_records.service.list_entities_for_tenant",
        return_value=[],
    ):
        # No record found → no false positive block
        _check_record_not_published(record_id=999, tenant_id=1)


# ---------------------------------------------------------------------------
# 6. Error message contains record_id and "immutable" / "correction workflow"
# ---------------------------------------------------------------------------

def test_w79_error_message_is_actionable():
    records = [_make_record(record_id=55, status="published")]

    with patch(
        "app.modules.academic_records.service.list_entities_for_tenant",
        return_value=records,
    ):
        with pytest.raises(ValueError) as exc_info:
            _check_record_not_published(record_id=55, tenant_id=1)

    msg = str(exc_info.value).lower()
    assert "55" in msg, "Error must reference record_id"
    assert "immutable" in msg or "correction" in msg, (
        "Error must indicate immutability and correction workflow"
    )
