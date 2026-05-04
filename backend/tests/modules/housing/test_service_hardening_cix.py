"""Phase CIX: Housing Service Hardening Tests

Validates outcome + metric recording (post-persist hooks) and fail-safe exception handling.
"""
import pytest
from unittest.mock import MagicMock

from app.modules.housing.schemas import (
    HousingRequestCreateSchema,
    HousingRequestStatusUpdateSchema,
)
from app.modules.housing.service import (
    create_housing_request,
    update_housing_request_status,
)


def test_create_housing_request_records_outcome_and_metric(monkeypatch):
    """Verify create_housing_request calls _record_outcome and _metric post-persist."""
    outcome_calls = []
    metric_calls = []

    def mock_record_outcome(entity_id, outcome_type, actor_id):
        outcome_calls.append({"entity_id": entity_id, "outcome_type": outcome_type, "actor_id": actor_id})

    def mock_metric(tenant_id, metric, value=1):
        metric_calls.append({"tenant_id": tenant_id, "metric": metric, "value": value})

    monkeypatch.setattr("app.modules.housing.service._record_outcome", mock_record_outcome)
    monkeypatch.setattr("app.modules.housing.service._metric", mock_metric)
    monkeypatch.setattr(
        "app.modules.housing.service.list_entities_for_tenant",
        lambda *args, **kwargs: []
    )
    
    created_result = {
        "id": 601,
        "student_id": 301,
        "request_type": "assignment",
        "dormitory": "Dorm A",
        "status": "submitted"
    }
    monkeypatch.setattr(
        "app.modules.housing.service.create_entity_for_tenant",
        lambda *args, **kwargs: created_result
    )
    monkeypatch.setattr(
        "app.modules.housing.service._emit_audit",
        lambda **kwargs: None
    )
    monkeypatch.setattr(
        "app.modules.housing.service.HousingRequestSchema.model_validate",
        lambda x: {"id": 601}
    )

    request = HousingRequestCreateSchema(
        student_id=301,
        request_type="assignment",
        dormitory="Dorm A",
        room_preference="single",
        manager_id="housing@example.com",
        notes="test"
    )

    result = create_housing_request(tenant_id=1, request=request, actor="housing@example.com")

    # Verify outcome recorded
    assert len(outcome_calls) == 1
    assert outcome_calls[0]["entity_id"] == 601
    assert outcome_calls[0]["outcome_type"] == "housing_request_created"
    assert "housing" in outcome_calls[0]["actor_id"]

    # Verify metric recorded
    assert len(metric_calls) == 1
    assert metric_calls[0]["tenant_id"] == 1
    assert metric_calls[0]["metric"] == "housing_requests_created"
    assert metric_calls[0]["value"] == 1


def test_update_housing_request_status_records_outcome_and_metric(monkeypatch):
    """Verify update_housing_request_status calls _record_outcome and _metric post-persist."""
    outcome_calls = []
    metric_calls = []

    def mock_record_outcome(entity_id, outcome_type, actor_id):
        outcome_calls.append({"entity_id": entity_id, "outcome_type": outcome_type, "actor_id": actor_id})

    def mock_metric(tenant_id, metric, value=1):
        metric_calls.append({"tenant_id": tenant_id, "metric": metric, "value": value})

    monkeypatch.setattr("app.modules.housing.service._record_outcome", mock_record_outcome)
    monkeypatch.setattr("app.modules.housing.service._metric", mock_metric)
    
    existing = {
        "id": 602,
        "student_id": 302,
        "request_type": "assignment",
        "dormitory": "Dorm B",
        "status": "submitted",
        "manager_id": "housing@example.com",
        "notes": "test"
    }
    
    monkeypatch.setattr(
        "app.modules.housing.service.list_entities_for_tenant",
        lambda *args, **kwargs: [existing]
    )
    monkeypatch.setattr(
        "app.modules.housing.service._check_no_active_room_assignment",
        lambda **kwargs: None
    )
    
    updated_result = {**existing, "status": "in_review"}
    monkeypatch.setattr(
        "app.modules.housing.service.update_entity_for_tenant",
        lambda *args, **kwargs: updated_result
    )
    monkeypatch.setattr(
        "app.modules.housing.service._emit_audit",
        lambda **kwargs: None
    )
    monkeypatch.setattr(
        "app.modules.housing.service._emit_housing_status_signal",
        lambda **kwargs: None
    )
    monkeypatch.setattr(
        "app.modules.housing.service._ensure_room_assignment_record",
        lambda *args, **kwargs: None
    )
    monkeypatch.setattr(
        "app.modules.housing.service.HousingRequestSchema.model_validate",
        lambda x: {"id": 602, "status": "in_review"}
    )

    payload = HousingRequestStatusUpdateSchema(status="in_review")

    result = update_housing_request_status(
        tenant_id=1, request_id=602, payload=payload, actor="housing@example.com"
    )

    # Verify outcome recorded
    assert len(outcome_calls) == 1
    assert outcome_calls[0]["entity_id"] == 602
    assert outcome_calls[0]["outcome_type"] == "housing_request_status_updated"
    assert "housing" in outcome_calls[0]["actor_id"]

    # Verify metric recorded
    assert len(metric_calls) == 1
    assert metric_calls[0]["tenant_id"] == 1
    assert metric_calls[0]["metric"] == "housing_requests_updated"
    assert metric_calls[0]["value"] == 1


def test_metric_fail_safe(monkeypatch):
    """Verify _metric gracefully handles exceptions (fail-safe)."""
    monkeypatch.setattr(
        "app.modules.housing.service.list_entities_for_tenant",
        lambda *args, **kwargs: []
    )
    
    created_result = {
        "id": 603,
        "student_id": 303,
        "request_type": "assignment",
        "dormitory": "Dorm C",
        "status": "submitted"
    }
    monkeypatch.setattr(
        "app.modules.housing.service.create_entity_for_tenant",
        lambda *args, **kwargs: created_result
    )
    monkeypatch.setattr(
        "app.modules.housing.service._emit_audit",
        lambda **kwargs: None
    )

    def mock_record_outcome(entity_id, outcome_type, actor_id):
        pass  # OK if it's called

    def mock_metric_broken(tenant_id, metric, value=1):
        raise RuntimeError("metric service down")

    monkeypatch.setattr("app.modules.housing.service._record_outcome", mock_record_outcome)
    monkeypatch.setattr("app.modules.housing.service._metric", mock_metric_broken)
    monkeypatch.setattr(
        "app.modules.housing.service.HousingRequestSchema.model_validate",
        lambda x: {"id": 603}
    )

    request = HousingRequestCreateSchema(
        student_id=303,
        request_type="assignment",
        dormitory="Dorm C",
        room_preference="any",
        manager_id="housing@example.com",
        notes="test"
    )

    # Should NOT raise despite _metric exception
    result = create_housing_request(tenant_id=1, request=request, actor="housing@example.com")
    assert result is not None


def test_outcome_fail_safe(monkeypatch):
    """Verify _record_outcome gracefully handles exceptions (fail-safe)."""
    monkeypatch.setattr(
        "app.modules.housing.service.list_entities_for_tenant",
        lambda *args, **kwargs: []
    )
    
    created_result = {
        "id": 604,
        "student_id": 304,
        "request_type": "assignment",
        "dormitory": "Dorm D",
        "status": "submitted"
    }
    monkeypatch.setattr(
        "app.modules.housing.service.create_entity_for_tenant",
        lambda *args, **kwargs: created_result
    )
    monkeypatch.setattr(
        "app.modules.housing.service._emit_audit",
        lambda **kwargs: None
    )

    def mock_outcome_broken(entity_id, outcome_type, actor_id):
        raise RuntimeError("brain_core down")

    def mock_metric(tenant_id, metric, value=1):
        pass  # OK if it's called

    monkeypatch.setattr("app.modules.housing.service._record_outcome", mock_outcome_broken)
    monkeypatch.setattr("app.modules.housing.service._metric", mock_metric)
    monkeypatch.setattr(
        "app.modules.housing.service.HousingRequestSchema.model_validate",
        lambda x: {"id": 604}
    )

    request = HousingRequestCreateSchema(
        student_id=304,
        request_type="assignment",
        dormitory="Dorm D",
        room_preference="any",
        manager_id="housing@example.com",
        notes="test"
    )

    # Should NOT raise despite _record_outcome exception
    result = create_housing_request(tenant_id=1, request=request, actor="housing@example.com")
    assert result is not None
