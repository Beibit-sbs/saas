"""W74 — students: GRADUATED transition requires degree_progress eligibility gate."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.modules.students.models import StudentStatus


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _make_profile(status: str = "active", version: int = 1) -> MagicMock:
    p = MagicMock()
    p.id = 10
    p.current_status = status
    p.version = version
    p.tenant_id = 1
    p.full_name = "Test Student"
    return p


def _make_eligibility(eligible: bool, credits_earned: int = 120, minimum_credits: int = 120,
                      remaining: int = 0) -> MagicMock:
    e = MagicMock()
    e.eligible = eligible
    e.credits_earned = credits_earned
    e.minimum_credits = minimum_credits
    e.remaining_required_items = remaining
    return e


def _make_request(to_status: StudentStatus, expected_version: int = 1) -> MagicMock:
    r = MagicMock()
    r.to_status = to_status
    r.expected_version = expected_version
    r.reason = "test"
    r.metadata_json = {}
    return r


# ---------------------------------------------------------------------------
# test 1: FSM constant includes GRADUATED as reachable from ACTIVE
# ---------------------------------------------------------------------------

def test_w74_student_status_graduated_is_reachable_from_active():
    from app.modules.students.business_rules import StudentLifecycleRules
    allowed = StudentLifecycleRules._ALLOWED_STATUS_TRANSITIONS[StudentStatus.ACTIVE]
    assert StudentStatus.GRADUATED in allowed, "GRADUATED must be reachable from ACTIVE"


# ---------------------------------------------------------------------------
# test 2: GRADUATED transition blocked when degree_progress says not eligible
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_w74_graduation_blocked_when_not_eligible():
    from app.core.module_helpers.service_validation import DomainValidationError
    from app.modules.students.service import StudentLifecycleService

    db = MagicMock()
    # DB returns a live student profile
    profile = _make_profile("active", version=1)
    db.execute.return_value.scalar_one_or_none.return_value = profile

    ineligible = _make_eligibility(eligible=False, credits_earned=80, minimum_credits=120, remaining=5)

    with patch(
        "app.modules.degree_progress.service.DegreeProgressService.is_student_eligible_for_graduation",
        new=AsyncMock(return_value=ineligible),
    ):
        svc = StudentLifecycleService(db)
        req = _make_request(StudentStatus.GRADUATED, expected_version=1)
        with pytest.raises(DomainValidationError, match="not eligible for graduation"):
            await svc.change_student_status(
                tenant_id=1,
                student_profile_id=10,
                request=req,
                actor_id="admin",
            )


# ---------------------------------------------------------------------------
# test 3: GRADUATED transition succeeds when degree_progress says eligible
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_w74_graduation_succeeds_when_eligible():
    from app.modules.students.schemas import StudentProfileReadSchema
    from app.modules.students.service import StudentLifecycleService

    db = MagicMock()
    profile = _make_profile("active", version=1)
    db.execute.return_value.scalar_one_or_none.return_value = profile

    eligible = _make_eligibility(eligible=True, credits_earned=120, minimum_credits=120, remaining=0)

    # patch StudentProfileReadSchema.model_validate to avoid full schema validation
    with patch(
        "app.modules.degree_progress.service.DegreeProgressService.is_student_eligible_for_graduation",
        new=AsyncMock(return_value=eligible),
    ), patch.object(StudentProfileReadSchema, "model_validate", return_value=MagicMock()):
        svc = StudentLifecycleService(db)
        req = _make_request(StudentStatus.GRADUATED, expected_version=1)
        # Should NOT raise
        result = await svc.change_student_status(
            tenant_id=1,
            student_profile_id=10,
            request=req,
            actor_id="admin",
        )
    assert result is not None


# ---------------------------------------------------------------------------
# test 4: Non-graduation transition does NOT call degree_progress service
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_w74_non_graduation_transition_skips_degree_check():
    from app.modules.students.schemas import StudentProfileReadSchema
    from app.modules.students.service import StudentLifecycleService

    db = MagicMock()
    profile = _make_profile("active", version=1)
    db.execute.return_value.scalar_one_or_none.return_value = profile

    degree_check = AsyncMock()

    with patch(
        "app.modules.degree_progress.service.DegreeProgressService.is_student_eligible_for_graduation",
        new=degree_check,
    ), patch.object(StudentProfileReadSchema, "model_validate", return_value=MagicMock()):
        svc = StudentLifecycleService(db)
        req = _make_request(StudentStatus.SUSPENDED, expected_version=1)
        await svc.change_student_status(
            tenant_id=1,
            student_profile_id=10,
            request=req,
            actor_id="admin",
        )

    degree_check.assert_not_called()


# ---------------------------------------------------------------------------
# test 5: Error message is actionable — contains credits and remaining items
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_w74_graduation_error_message_is_actionable():
    from app.core.module_helpers.service_validation import DomainValidationError
    from app.modules.students.service import StudentLifecycleService

    db = MagicMock()
    profile = _make_profile("active", version=1)
    db.execute.return_value.scalar_one_or_none.return_value = profile

    ineligible = _make_eligibility(eligible=False, credits_earned=60, minimum_credits=120, remaining=8)

    with patch(
        "app.modules.degree_progress.service.DegreeProgressService.is_student_eligible_for_graduation",
        new=AsyncMock(return_value=ineligible),
    ):
        svc = StudentLifecycleService(db)
        req = _make_request(StudentStatus.GRADUATED, expected_version=1)
        with pytest.raises(DomainValidationError) as exc_info:
            await svc.change_student_status(
                tenant_id=1,
                student_profile_id=10,
                request=req,
                actor_id="admin",
            )
    msg = str(exc_info.value)
    assert "credits_earned=60/120" in msg
    assert "remaining_required_items=8" in msg
