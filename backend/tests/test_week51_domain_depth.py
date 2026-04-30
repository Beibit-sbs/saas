"""W51 depth tests - academic_integrity: case cap + escalation alerts."""
from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_integrity_case_status_cap_dict_structure():
    from app.modules.academic_integrity.service import _INTEGRITY_CASE_STATUS_MAX_ACTIVE

    assert isinstance(_INTEGRITY_CASE_STATUS_MAX_ACTIVE, dict)
    assert _INTEGRITY_CASE_STATUS_MAX_ACTIVE["flagged"] == 400
    assert _INTEGRITY_CASE_STATUS_MAX_ACTIVE["under_review"] == 250
    assert _INTEGRITY_CASE_STATUS_MAX_ACTIVE["escalated"] == 120
    assert all(isinstance(v, int) and v > 0 for v in _INTEGRITY_CASE_STATUS_MAX_ACTIVE.values())


@pytest.mark.asyncio
async def test_active_case_statuses_and_escalation_risk_statuses():
    from app.modules.academic_integrity.service import (
        _ACTIVE_INTEGRITY_CASE_STATUSES,
        _INTEGRITY_ESCALATION_RISK_STATUSES,
    )

    assert isinstance(_ACTIVE_INTEGRITY_CASE_STATUSES, frozenset)
    assert "flagged" in _ACTIVE_INTEGRITY_CASE_STATUSES
    assert "under_review" in _ACTIVE_INTEGRITY_CASE_STATUSES
    assert "escalated" in _ACTIVE_INTEGRITY_CASE_STATUSES
    assert "resolved" not in _ACTIVE_INTEGRITY_CASE_STATUSES

    assert isinstance(_INTEGRITY_ESCALATION_RISK_STATUSES, frozenset)
    assert "escalated" in _INTEGRITY_ESCALATION_RISK_STATUSES


class _CapStubEntityService:
    async def list_entities(self, **kwargs):  # type: ignore[no-untyped-def]
        return ([{"status": "flagged"} for _ in range(400)], 400)

    async def create_entity(self, **kwargs):  # type: ignore[no-untyped-def]
        raise AssertionError("create_entity should not be called when cap is reached")


@pytest.mark.asyncio
async def test_create_integrity_case_raises_when_cap_reached():
    from app.modules.academic_integrity.schemas import IntegrityCaseCreateSchema, IntegrityCaseType
    from app.modules.academic_integrity.service import AcademicIntegrityService

    svc = AcademicIntegrityService(tenant_entity_service=_CapStubEntityService())
    payload = IntegrityCaseCreateSchema(
        student_id="s-1",
        course_id="c-1",
        assignment_id="a-1",
        case_type=IntegrityCaseType.PLAGIARISM,
        description="Possible plagiarism detected in assignment submission.",
        evidence_url=None,
        priority="normal",
    )

    with pytest.raises(ValueError, match="active cap reached"):
        await svc.create_integrity_case(tenant_id="7", actor="u-1", payload=payload)


class _AlertStubEntityService:
    def __init__(self) -> None:
        self.created: list[dict] = []

    async def list_entities(self, **kwargs):  # type: ignore[no-untyped-def]
        entity_type = kwargs.get("entity_type")
        if entity_type == "integrity_escalation_alerts":
            return ([{"integration_source": "academic_integrity_escalation_queue", "source_entity_id": "42"}], 1)
        return ([], 0)

    async def create_entity(self, **kwargs):  # type: ignore[no-untyped-def]
        self.created.append(kwargs.get("entity_data") or {})
        return kwargs.get("entity_data") or {}


@pytest.mark.asyncio
async def test_ensure_integrity_escalation_alert_record_is_idempotent(monkeypatch):
    from app.modules.academic_integrity.service import AcademicIntegrityService

    svc_backend = _AlertStubEntityService()
    svc = AcademicIntegrityService(tenant_entity_service=svc_backend)

    monkeypatch.setattr(
        "app.platform.events.publisher.EventPublisher.publish_event",
        lambda self, **kwargs: None,
    )

    await svc._ensure_integrity_escalation_alert_record(
        tenant_id="7",
        case={"id": "42", "student_id": "s-1"},
    )

    assert len(svc_backend.created) == 0
