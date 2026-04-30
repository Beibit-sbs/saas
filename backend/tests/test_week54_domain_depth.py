"""Week 54: career_services domain depth — pipeline cap + stalled opportunity alerts."""

import pytest
from unittest.mock import MagicMock

from app.modules.career_services import service
from app.modules.career_services.schemas import CareerOpportunityCreateSchema


@pytest.mark.asyncio
async def test_opportunity_pipeline_cap_dict_structure():
    """Test that _OPPORTUNITY_PIPELINE_MAX_REVIEW has the expected structure."""
    assert isinstance(service._OPPORTUNITY_PIPELINE_MAX_REVIEW, dict)
    assert "internship" in service._OPPORTUNITY_PIPELINE_MAX_REVIEW
    assert "job" in service._OPPORTUNITY_PIPELINE_MAX_REVIEW
    assert "mentorship" in service._OPPORTUNITY_PIPELINE_MAX_REVIEW
    assert "work_study" in service._OPPORTUNITY_PIPELINE_MAX_REVIEW

    for opportunity_type, cap in service._OPPORTUNITY_PIPELINE_MAX_REVIEW.items():
        assert isinstance(opportunity_type, str)
        assert isinstance(cap, int)
        assert cap > 0


@pytest.mark.asyncio
async def test_stalled_opportunity_statuses_and_risk_statuses():
    """Test that status constants are properly defined."""
    assert isinstance(service._STALLED_OPPORTUNITY_STATUSES, frozenset)
    assert isinstance(service._STALLED_RISK_STATUSES, frozenset)
    assert "in_review" in service._STALLED_OPPORTUNITY_STATUSES
    assert "in_review" in service._STALLED_RISK_STATUSES


@pytest.mark.asyncio
async def test_create_opportunity_raises_when_pipeline_cap_reached(monkeypatch):
    """Test that creating an opportunity raises ValueError when pipeline cap is reached."""
    tenant_id = 1
    request = CareerOpportunityCreateSchema(
        student_id=100,
        title="Test internship",
        company="Test Corp",
        opportunity_type="internship",
    )
    actor = "test_user"
    monkeypatch.setattr(service, "_check_student_is_actively_enrolled_for_career_opportunity", lambda *a, **kw: None)

    # Mock list_entities_for_tenant to return enough opportunities to hit the cap
    # internship pipeline cap is 3, so we return 3 existing in_review opportunities
    existing_opportunities = [
        {
            "id": i,
            "student_id": 100,
            "opportunity_type": "internship",
            "status": "in_review",
            "title": f"Opportunity {i}",
            "company": f"Company {i}",
        }
        for i in range(1, 4)  # 3 in_review opportunities
    ]

    monkeypatch.setattr(
        "app.modules.career_services.service.list_entities_for_tenant",
        lambda entity_name, tid: existing_opportunities if entity_name == "career_opportunities" else [],
    )

    with pytest.raises(ValueError) as exc_info:
        service.create_career_opportunity(tenant_id, request, actor)
    assert "pipeline cap reached" in str(exc_info.value)


@pytest.mark.asyncio
async def test_ensure_stalled_opportunity_alert_record_is_idempotent(monkeypatch):
    """Test that _ensure_stalled_opportunity_alert_record is idempotent via integration_source deduplication."""
    tenant_id = 1
    opportunity_id = 42
    opportunity_data = {
        "id": opportunity_id,
        "student_id": 100,
        "opportunity_type": "internship",
        "company": "Test Corp",
        "status": "in_review",
    }

    # Mock publish_event to track if it's called (it should be called once)
    publish_event_mock = MagicMock()
    monkeypatch.setattr(
        "app.platform.events.publisher.EventPublisher.publish_event",
        publish_event_mock,
    )

    # On first call, return no existing alerts
    create_count = [0]
    def mock_list_entities(entity_name, tid):
        if entity_name == "career_stalled_opportunity_alerts":
            return []
        return []

    def mock_create_entity(*args, **kwargs):
        create_count[0] += 1
        return {"id": 1}

    monkeypatch.setattr(
        "app.modules.career_services.service.list_entities_for_tenant",
        mock_list_entities,
    )
    monkeypatch.setattr(
        "app.modules.career_services.service.create_entity_for_tenant",
        mock_create_entity,
    )

    # First call should create alert and publish event
    service._ensure_stalled_opportunity_alert_record(tenant_id, opportunity_id, opportunity_data)
    assert create_count[0] == 1
    assert publish_event_mock.call_count == 1

    # Second call should find existing alert and skip creation
    def mock_list_entities_with_existing(entity_name, tid):
        if entity_name == "career_stalled_opportunity_alerts":
            return [
                {
                    "id": 1,
                    "integration_source": "career_services_stalled_queue",
                    "source_entity_id": str(opportunity_id),
                }
            ]
        return []

    monkeypatch.setattr(
        "app.modules.career_services.service.list_entities_for_tenant",
        mock_list_entities_with_existing,
    )

    # Second call should skip creation and event publishing
    service._ensure_stalled_opportunity_alert_record(tenant_id, opportunity_id, opportunity_data)
    assert create_count[0] == 1  # No additional creation
    assert publish_event_mock.call_count == 1  # No additional event
