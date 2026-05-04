"""Phase CXI: Career Services Service Hardening Tests

Validates outcome + metric recording (post-persist hooks) and fail-safe exception handling.
"""
import pytest
from unittest.mock import MagicMock

from app.modules.career_services.schemas import (
    CareerOpportunityCreateSchema,
    CareerOpportunityStatusUpdateSchema,
)
from app.modules.career_services.service import (
    create_career_opportunity,
    update_career_opportunity_status,
)


def test_create_career_opportunity_records_outcome_and_metric(monkeypatch):
    """Verify create_career_opportunity calls _record_outcome and _metric post-persist."""
    outcome_calls = []
    metric_calls = []

    monkeypatch.setattr("app.modules.career_services.service._record_outcome",
        lambda entity_id, outcome_type, actor_id: outcome_calls.append(
            {"entity_id": entity_id, "outcome_type": outcome_type, "actor_id": actor_id}))
    monkeypatch.setattr("app.modules.career_services.service._metric",
        lambda tenant_id, metric, value=1: metric_calls.append(
            {"tenant_id": tenant_id, "metric": metric, "value": value}))

    monkeypatch.setattr(
        "app.modules.career_services.service._check_student_is_actively_enrolled_for_career_opportunity",
        lambda **kwargs: None
    )
    # Return empty list so inline cap checks pass
    monkeypatch.setattr(
        "app.modules.career_services.service.list_entities_for_tenant",
        lambda *args, **kwargs: []
    )

    created_result = {
        "id": 801, "student_id": 501, "opportunity_type": "internship",
        "title": "Dev Intern", "company": "TechCo", "status": "open"
    }
    monkeypatch.setattr(
        "app.modules.career_services.service.create_entity_for_tenant",
        lambda *args, **kwargs: created_result
    )
    monkeypatch.setattr("app.modules.career_services.service._emit_audit", lambda **kwargs: None)
    monkeypatch.setattr(
        "app.modules.career_services.service.CareerOpportunitySchema.model_validate",
        lambda x: {"id": 801}
    )

    request = CareerOpportunityCreateSchema(
        student_id=501, title="Dev Intern", company="TechCo",
        opportunity_type="internship", owner_id="career@example.com", notes="test"
    )
    result = create_career_opportunity(tenant_id=1, request=request, actor="career@example.com")

    assert len(outcome_calls) == 1
    assert outcome_calls[0]["entity_id"] == 801
    assert outcome_calls[0]["outcome_type"] == "career_opportunity_created"
    assert len(metric_calls) == 1
    assert metric_calls[0]["tenant_id"] == 1
    assert metric_calls[0]["metric"] == "career_opportunities_created"


def test_update_career_opportunity_status_records_outcome_and_metric(monkeypatch):
    """Verify update_career_opportunity_status calls _record_outcome and _metric post-persist."""
    outcome_calls = []
    metric_calls = []

    monkeypatch.setattr("app.modules.career_services.service._record_outcome",
        lambda entity_id, outcome_type, actor_id: outcome_calls.append(
            {"entity_id": entity_id, "outcome_type": outcome_type, "actor_id": actor_id}))
    monkeypatch.setattr("app.modules.career_services.service._metric",
        lambda tenant_id, metric, value=1: metric_calls.append(
            {"tenant_id": tenant_id, "metric": metric, "value": value}))

    existing = {
        "id": 802, "student_id": 502, "opportunity_type": "job",
        "title": "Engineer", "company": "Corp", "status": "open",
        "owner_id": "career@example.com", "start_date": "2026-06-01", "notes": "test"
    }
    monkeypatch.setattr(
        "app.modules.career_services.service.list_entities_for_tenant",
        lambda *args, **kwargs: [existing]
    )
    updated_result = {**existing, "status": "in_review"}
    monkeypatch.setattr(
        "app.modules.career_services.service.update_entity_for_tenant",
        lambda *args, **kwargs: updated_result
    )
    monkeypatch.setattr("app.modules.career_services.service._emit_audit", lambda **kwargs: None)
    monkeypatch.setattr(
        "app.modules.career_services.service._ensure_placement_record",
        lambda *args, **kwargs: None
    )
    monkeypatch.setattr(
        "app.modules.career_services.service._emit_career_opportunity_at_risk_signal",
        lambda **kwargs: None
    )
    monkeypatch.setattr(
        "app.modules.career_services.service.CareerOpportunitySchema.model_validate",
        lambda x: {"id": 802, "status": "in_review"}
    )

    payload = CareerOpportunityStatusUpdateSchema(status="in_review")
    result = update_career_opportunity_status(
        tenant_id=1, opportunity_id=802, request=payload, actor="career@example.com"
    )

    assert len(outcome_calls) == 1
    assert outcome_calls[0]["entity_id"] == 802
    assert outcome_calls[0]["outcome_type"] == "career_opportunity_status_updated"
    assert len(metric_calls) == 1
    assert metric_calls[0]["tenant_id"] == 1
    assert metric_calls[0]["metric"] == "career_opportunities_updated"


def test_metric_fail_safe(monkeypatch):
    """Verify _metric gracefully handles exceptions (fail-safe)."""
    from app.modules.career_services.service import _metric

    monkeypatch.setattr(
        "app.modules.career_services.service.record_usage_event",
        lambda **kwargs: (_ for _ in ()).throw(RuntimeError("metric service down"))
    )
    # Should not raise
    _metric(tenant_id=1, metric="career_opportunities_created")


def test_outcome_fail_safe(monkeypatch):
    """Verify _record_outcome gracefully handles exceptions (fail-safe)."""
    import sys
    from types import ModuleType
    from app.modules.career_services.service import _record_outcome

    fake_bc = ModuleType("app.modules.brain_core.service")
    def _raise(*a, **k):
        raise RuntimeError("brain_core down")
    fake_bc.record_dispatch_outcome = _raise
    monkeypatch.setitem(sys.modules, "app.modules.brain_core", ModuleType("app.modules.brain_core"))
    monkeypatch.setitem(sys.modules, "app.modules.brain_core.service", fake_bc)

    # Should not raise
    _record_outcome(entity_id=804, outcome_type="career_opportunity_created", actor_id="test")
