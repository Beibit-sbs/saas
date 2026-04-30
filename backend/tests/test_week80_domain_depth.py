"""W80 — academic_integrity: case closure documentation enforcement.

Real business invariant: RESOLVED/DISMISSED transitions require non-empty
resolution_notes; ESCALATED requires non-empty recommended_action.
Without enforcement, cases can be closed with zero accountability trail —
accreditation risk and discrimination liability.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from app.modules.academic_integrity.service import (
    AcademicIntegrityService,
    _CLOSURE_REQUIRES_NOTES,
)
from app.modules.academic_integrity.schemas import (
    IntegrityCaseStatus,
    IntegrityCaseStatusUpdateSchema,
)


def _make_service():
    svc = AcademicIntegrityService(tenant_entity_service=MagicMock())
    return svc


def _make_case(status: str) -> dict:
    return {
        "id": "case-uuid-001",
        "status": status,
        "student_id": "student-uuid",
        "course_id": "course-uuid",
        "case_type": "plagiarism",
        "description": "Test case",
        "evidence_url": None,
        "priority": "normal",
        "resolution_notes": None,
        "recommended_action": None,
        "created_at": "2026-01-01T00:00:00",
        "updated_at": "2026-01-01T00:00:00",
        "created_by": "admin",
        "tenant_id": "1",
    }


# ---------------------------------------------------------------------------
# Test 1: frozenset structure
# ---------------------------------------------------------------------------
def test_w80_closure_requires_notes_frozenset():
    assert isinstance(_CLOSURE_REQUIRES_NOTES, frozenset)
    assert IntegrityCaseStatus.RESOLVED in _CLOSURE_REQUIRES_NOTES
    assert IntegrityCaseStatus.DISMISSED in _CLOSURE_REQUIRES_NOTES
    assert IntegrityCaseStatus.FLAGGED not in _CLOSURE_REQUIRES_NOTES
    assert IntegrityCaseStatus.UNDER_REVIEW not in _CLOSURE_REQUIRES_NOTES


# ---------------------------------------------------------------------------
# Test 2: RESOLVED blocked without resolution_notes
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_w80_resolved_without_notes_blocked():
    svc = _make_service()
    svc.tenant_entity_service.get_entity = AsyncMock(
        return_value=_make_case("under_review")
    )
    payload = IntegrityCaseStatusUpdateSchema(
        status=IntegrityCaseStatus.RESOLVED,
        resolution_notes=None,
        recommended_action=None,
    )
    with pytest.raises(ValueError) as exc_info:
        await svc.update_integrity_case_status(
            tenant_id="1",
            case_id="case-uuid-001",
            actor="admin",
            payload=payload,
        )
    err = str(exc_info.value)
    assert "resolved" in err.lower()
    assert "resolution_notes" in err


# ---------------------------------------------------------------------------
# Test 3: DISMISSED blocked without resolution_notes
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_w80_dismissed_without_notes_blocked():
    svc = _make_service()
    svc.tenant_entity_service.get_entity = AsyncMock(
        return_value=_make_case("under_review")
    )
    payload = IntegrityCaseStatusUpdateSchema(
        status=IntegrityCaseStatus.DISMISSED,
        resolution_notes="   ",   # whitespace-only — also invalid
        recommended_action=None,
    )
    with pytest.raises(ValueError) as exc_info:
        await svc.update_integrity_case_status(
            tenant_id="1",
            case_id="case-uuid-001",
            actor="admin",
            payload=payload,
        )
    assert "dismissed" in str(exc_info.value).lower()


# ---------------------------------------------------------------------------
# Test 4: RESOLVED with notes — allowed
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_w80_resolved_with_notes_allowed():
    svc = _make_service()
    svc.tenant_entity_service.get_entity = AsyncMock(
        return_value=_make_case("under_review")
    )
    svc.tenant_entity_service.update_entity = AsyncMock(return_value=None)
    payload = IntegrityCaseStatusUpdateSchema(
        status=IntegrityCaseStatus.RESOLVED,
        resolution_notes="Student admitted copying. Grade penalty applied.",
        recommended_action=None,
    )
    result = await svc.update_integrity_case_status(
        tenant_id="1",
        case_id="case-uuid-001",
        actor="admin",
        payload=payload,
    )
    assert result["status"] == IntegrityCaseStatus.RESOLVED.value


# ---------------------------------------------------------------------------
# Test 5: ESCALATED blocked without recommended_action
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_w80_escalated_without_action_blocked():
    svc = _make_service()
    svc.tenant_entity_service.get_entity = AsyncMock(
        return_value=_make_case("under_review")
    )
    payload = IntegrityCaseStatusUpdateSchema(
        status=IntegrityCaseStatus.ESCALATED,
        resolution_notes=None,
        recommended_action=None,
    )
    with pytest.raises(ValueError) as exc_info:
        await svc.update_integrity_case_status(
            tenant_id="1",
            case_id="case-uuid-001",
            actor="admin",
            payload=payload,
        )
    err = str(exc_info.value)
    assert "escalat" in err.lower()
    assert "recommended_action" in err


# ---------------------------------------------------------------------------
# Test 6: ESCALATED with recommended_action — allowed
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_w80_escalated_with_action_allowed():
    svc = _make_service()
    svc.tenant_entity_service.get_entity = AsyncMock(
        return_value=_make_case("under_review")
    )
    svc.tenant_entity_service.update_entity = AsyncMock(return_value=None)
    # Mock out the escalation alert helper to avoid real DB
    svc._ensure_integrity_escalation_alert_record = AsyncMock(return_value=None)
    payload = IntegrityCaseStatusUpdateSchema(
        status=IntegrityCaseStatus.ESCALATED,
        resolution_notes=None,
        recommended_action="Refer to Dean of Students for formal hearing.",
    )
    from unittest.mock import patch
    with patch(
        "app.platform.events.publisher.EventPublisher"
    ) as mock_pub:
        mock_pub.return_value.publish_event = MagicMock()
        result = await svc.update_integrity_case_status(
            tenant_id="1",
            case_id="case-uuid-001",
            actor="admin",
            payload=payload,
        )
    assert result["status"] == IntegrityCaseStatus.ESCALATED.value
