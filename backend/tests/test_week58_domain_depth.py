"""Week 58 domain-depth tests: alumni — engagement type cap + disengagement risk alert."""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch


# ---------------------------------------------------------------------------
# Test 1: Cap dict structure
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_alumni_engagement_type_max_active_dict_structure():
    from app.modules.alumni.service import _ENGAGEMENT_TYPE_MAX_ACTIVE

    assert isinstance(_ENGAGEMENT_TYPE_MAX_ACTIVE, dict)
    assert len(_ENGAGEMENT_TYPE_MAX_ACTIVE) >= 2
    for k, v in _ENGAGEMENT_TYPE_MAX_ACTIVE.items():
        assert isinstance(k, str) and len(k) > 0
        assert isinstance(v, int) and v > 0


# ---------------------------------------------------------------------------
# Test 2: Frozenset constants
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_alumni_inactive_risk_statuses_is_frozenset():
    from app.modules.alumni.service import _ALUMNI_INACTIVE_RISK_STATUSES, _DISENGAGEMENT_TRIGGER_STATUSES

    assert isinstance(_ALUMNI_INACTIVE_RISK_STATUSES, frozenset)
    assert isinstance(_DISENGAGEMENT_TRIGGER_STATUSES, frozenset)
    assert len(_ALUMNI_INACTIVE_RISK_STATUSES) >= 1
    assert all(isinstance(s, str) for s in _ALUMNI_INACTIVE_RISK_STATUSES)


# ---------------------------------------------------------------------------
# Test 3: create_alumni_record raises when engagement cap reached
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_create_alumni_record_raises_when_engagement_cap_reached(monkeypatch):
    from app.modules.alumni import service
    from app.modules.alumni.schemas import AlumniRecordCreateSchema
    monkeypatch.setattr(service, "_check_student_has_graduated_for_alumni_record", lambda *a, **kw: None)

    engagement_type = next(iter(service._ENGAGEMENT_TYPE_MAX_ACTIVE))
    cap = service._ENGAGEMENT_TYPE_MAX_ACTIVE[engagement_type]

    fake_records = [
        {"student_id": 1, "engagement_type": engagement_type, "status": "active", "id": i}
        for i in range(cap)
    ]

    monkeypatch.setattr(
        service, "list_entities_for_tenant",
        lambda entity, tenant_id: fake_records,
    )

    request = AlumniRecordCreateSchema(
        student_id=1,
        graduation_year=2020,
        engagement_type=engagement_type,
    )

    with pytest.raises(ValueError, match="already has"):
        service.create_alumni_record(tenant_id=1, request=request, actor="test")


# ---------------------------------------------------------------------------
# Test 4: _ensure_alumni_disengagement_risk_alert is idempotent
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_ensure_alumni_disengagement_risk_alert_is_idempotent(monkeypatch):
    from app.modules.alumni import service

    calls_to_create: list = []
    event_mock = MagicMock()

    monkeypatch.setattr(
        service, "list_entities_for_tenant",
        lambda entity, tenant_id: (
            [{"integration_source": "alumni_disengagement_queue", "source_entity_id": "77"}]
            if entity == "alumni_disengagement_risk_alerts"
            else []
        ),
    )
    monkeypatch.setattr(
        service, "create_entity_for_tenant",
        lambda entity, data, tenant_id: calls_to_create.append((entity, data)) or data,
    )

    with patch(
        "app.platform.events.publisher.EventPublisher.publish_event",
        event_mock,
    ):
        service._ensure_alumni_disengagement_risk_alert(
            tenant_id=1,
            record_id=77,
            record_data={
                "student_id": 1,
                "engagement_type": "mentoring",
                "graduation_year": 2018,
                "status": "inactive",
            },
        )

    # Already exists → no new create, no event emitted
    assert len(calls_to_create) == 0
    event_mock.assert_not_called()
