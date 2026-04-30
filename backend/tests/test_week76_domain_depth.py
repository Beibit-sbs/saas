"""W76 — transcripts: graduated-student transcript lock.

Gap: generate_transcript() updated transcript records even when student.current_status=GRADUATED.
     An official transcript is immutable once graduation is confirmed.
Fix: TranscriptRules.validate_transcript_not_locked() called in generate_transcript()
     before any DB writes.  Raises DomainValidationError for GRADUATED students.

Cross-entity invariant: transcripts × students.current_status(GRADUATED)
"""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _make_student(status: str = "active") -> MagicMock:
    s = MagicMock()
    s.id = 5
    s.tenant_id = 1
    s.current_status = status
    s.full_name = "Test Student"
    return s


def _make_service(student_status: str = "active"):
    from app.modules.transcripts.service import TranscriptService

    db = MagicMock()
    student = _make_student(student_status)
    # _load_student → db.execute.scalar_one_or_none
    db.execute.return_value.scalar_one_or_none.return_value = student
    # _load_enrollments → db.execute.scalars().all()
    db.execute.return_value.scalars.return_value.all.return_value = []
    return TranscriptService(db)


# ---------------------------------------------------------------------------
# test 1: validate_transcript_not_locked is importable and exists in TranscriptRules
# ---------------------------------------------------------------------------

def test_w76_transcript_rules_has_lock_validator():
    from app.modules.transcripts.business_rules import TranscriptRules
    assert callable(getattr(TranscriptRules, "validate_transcript_not_locked", None))


# ---------------------------------------------------------------------------
# test 2: GRADUATED student raises DomainValidationError
# ---------------------------------------------------------------------------

def test_w76_lock_raises_for_graduated_student():
    from app.core.module_helpers.service_validation import DomainValidationError
    from app.modules.transcripts.business_rules import TranscriptRules

    with pytest.raises(DomainValidationError, match="locked"):
        TranscriptRules.validate_transcript_not_locked("graduated", student_profile_id=5)


# ---------------------------------------------------------------------------
# test 3: Non-graduated student does not raise (active)
# ---------------------------------------------------------------------------

def test_w76_lock_does_not_raise_for_active_student():
    from app.modules.transcripts.business_rules import TranscriptRules
    # Should not raise
    TranscriptRules.validate_transcript_not_locked("active", student_profile_id=5)


# ---------------------------------------------------------------------------
# test 4: None status does not raise (no status data → do not block)
# ---------------------------------------------------------------------------

def test_w76_lock_does_not_raise_for_none_status():
    from app.modules.transcripts.business_rules import TranscriptRules
    TranscriptRules.validate_transcript_not_locked(None, student_profile_id=5)


# ---------------------------------------------------------------------------
# test 5: generate_transcript blocked for GRADUATED student
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_w76_generate_transcript_blocked_for_graduated_student():
    from app.core.module_helpers.service_validation import DomainValidationError

    svc = _make_service(student_status="graduated")

    with pytest.raises(DomainValidationError, match="immutable|locked"):
        await svc.generate_transcript(
            tenant_id=1,
            student_profile_id=5,
            actor_id="admin",
        )


# ---------------------------------------------------------------------------
# test 6: Error message identifies the student_profile_id
# ---------------------------------------------------------------------------

def test_w76_lock_error_message_names_student():
    from app.core.module_helpers.service_validation import DomainValidationError
    from app.modules.transcripts.business_rules import TranscriptRules

    with pytest.raises(DomainValidationError) as exc_info:
        TranscriptRules.validate_transcript_not_locked("graduated", student_profile_id=42)

    assert "42" in str(exc_info.value)
    assert "graduated" in str(exc_info.value).lower()
