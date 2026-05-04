"""Phase CX: Alumni Service Hardening Tests

Validates outcome + metric recording (post-persist hooks) and fail-safe exception handling.
"""
import pytest
from unittest.mock import MagicMock

from app.modules.alumni.schemas import (
    AlumniRecordCreateSchema,
    AlumniRecordStatusUpdateSchema,
)
from app.modules.alumni.service import (
    create_alumni_record,
    update_alumni_status,
)


def test_create_alumni_record_records_outcome_and_metric(monkeypatch):
    """Verify create_alumni_record calls _record_outcome and _metric post-persist."""
    outcome_calls = []
    metric_calls = []

    def mock_record_outcome(entity_id, outcome_type, actor_id):
        outcome_calls.append({"entity_id": entity_id, "outcome_type": outcome_type, "actor_id": actor_id})

    def mock_metric(tenant_id, metric, value=1):
        metric_calls.append({"tenant_id": tenant_id, "metric": metric, "value": value})

    monkeypatch.setattr("app.modules.alumni.service._record_outcome", mock_record_outcome)
    monkeypatch.setattr("app.modules.alumni.service._metric", mock_metric)
    monkeypatch.setattr(
        "app.modules.alumni.service._check_student_has_graduated_for_alumni_record",
        lambda **kwargs: None
    )
    monkeypatch.setattr(
        "app.modules.alumni.service._check_engagement_cap",
        lambda **kwargs: None
    )
    
    created_result = {
        "id": 701,
        "student_id": 401,
        "graduation_year": 2025,
        "engagement_type": "mentoring",
        "employer": "TechCorp",
        "status": "active"
    }
    monkeypatch.setattr(
        "app.modules.alumni.service.create_entity_for_tenant",
        lambda *args, **kwargs: created_result
    )
    monkeypatch.setattr(
        "app.modules.alumni.service._emit_audit",
        lambda **kwargs: None
    )
    monkeypatch.setattr(
        "app.modules.alumni.service.AlumniRecordSchema.model_validate",
        lambda x: {"id": 701}
    )

    request = AlumniRecordCreateSchema(
        student_id=401,
        graduation_year=2025,
        engagement_type="mentoring",
        employer="TechCorp",
        contact_email="alum@example.com",
        notes="test"
    )

    result = create_alumni_record(tenant_id=1, request=request, actor="alumni@example.com")

    # Verify outcome recorded
    assert len(outcome_calls) == 1
    assert outcome_calls[0]["entity_id"] == 701
    assert outcome_calls[0]["outcome_type"] == "alumni_record_created"
    assert "alumni" in outcome_calls[0]["actor_id"]

    # Verify metric recorded
    assert len(metric_calls) == 1
    assert metric_calls[0]["tenant_id"] == 1
    assert metric_calls[0]["metric"] == "alumni_records_created"
    assert metric_calls[0]["value"] == 1


def test_update_alumni_status_records_outcome_and_metric(monkeypatch):
    """Verify update_alumni_status calls _record_outcome and _metric post-persist."""
    outcome_calls = []
    metric_calls = []

    def mock_record_outcome(entity_id, outcome_type, actor_id):
        outcome_calls.append({"entity_id": entity_id, "outcome_type": outcome_type, "actor_id": actor_id})

    def mock_metric(tenant_id, metric, value=1):
        metric_calls.append({"tenant_id": tenant_id, "metric": metric, "value": value})

    monkeypatch.setattr("app.modules.alumni.service._record_outcome", mock_record_outcome)
    monkeypatch.setattr("app.modules.alumni.service._metric", mock_metric)
    
    existing = {
        "id": 702,
        "student_id": 402,
        "graduation_year": 2025,
        "engagement_type": "event",
        "employer": "TechCorp",
        "status": "active",
        "contact_email": "alum@example.com",
        "notes": "test"
    }
    
    monkeypatch.setattr(
        "app.modules.alumni.service.list_entities_for_tenant",
        lambda *args, **kwargs: [existing]
    )
    
    updated_result = {**existing, "status": "engaged"}
    monkeypatch.setattr(
        "app.modules.alumni.service.update_entity_for_tenant",
        lambda *args, **kwargs: updated_result
    )
    monkeypatch.setattr(
        "app.modules.alumni.service._emit_audit",
        lambda **kwargs: None
    )
    monkeypatch.setattr(
        "app.modules.alumni.service._ensure_engagement_event",
        lambda **kwargs: None
    )
    monkeypatch.setattr(
        "app.modules.alumni.service._ensure_alumni_disengagement_risk_alert",
        lambda *args, **kwargs: None
    )
    monkeypatch.setattr(
        "app.modules.alumni.service.AlumniRecordSchema.model_validate",
        lambda x: {"id": 702, "status": "engaged"}
    )

    payload = AlumniRecordStatusUpdateSchema(status="engaged")

    result = update_alumni_status(
        tenant_id=1, record_id=702, request=payload, actor="alumni@example.com"
    )

    # Verify outcome recorded
    assert len(outcome_calls) == 1
    assert outcome_calls[0]["entity_id"] == 702
    assert outcome_calls[0]["outcome_type"] == "alumni_record_status_updated"
    assert "alumni" in outcome_calls[0]["actor_id"]

    # Verify metric recorded
    assert len(metric_calls) == 1
    assert metric_calls[0]["tenant_id"] == 1
    assert metric_calls[0]["metric"] == "alumni_records_updated"
    assert metric_calls[0]["value"] == 1


def test_metric_fail_safe(monkeypatch):
    """Verify _metric gracefully handles exceptions (fail-safe)."""
    monkeypatch.setattr(
        "app.modules.alumni.service._check_student_has_graduated_for_alumni_record",
        lambda **kwargs: None
    )
    monkeypatch.setattr(
        "app.modules.alumni.service._check_engagement_cap",
        lambda **kwargs: None
    )
    
    created_result = {
        "id": 703,
        "student_id": 403,
        "graduation_year": 2025,
        "engagement_type": "mentoring",
        "employer": "TechCorp",
        "status": "active"
    }
    monkeypatch.setattr(
        "app.modules.alumni.service.create_entity_for_tenant",
        lambda *args, **kwargs: created_result
    )
    monkeypatch.setattr(
        "app.modules.alumni.service._emit_audit",
        lambda **kwargs: None
    )

    def mock_record_outcome(entity_id, outcome_type, actor_id):
        pass  # OK if it's called

    def mock_metric_broken(tenant_id, metric, value=1):
        raise RuntimeError("metric service down")

    monkeypatch.setattr("app.modules.alumni.service._record_outcome", mock_record_outcome)
    monkeypatch.setattr("app.modules.alumni.service._metric", mock_metric_broken)
    monkeypatch.setattr(
        "app.modules.alumni.service.AlumniRecordSchema.model_validate",
        lambda x: {"id": 703}
    )

    request = AlumniRecordCreateSchema(
        student_id=403,
        graduation_year=2025,
        engagement_type="mentoring",
        employer="TechCorp",
        contact_email="alum@example.com",
        notes="test"
    )

    # Should NOT raise despite _metric exception
    result = create_alumni_record(tenant_id=1, request=request, actor="alumni@example.com")
    assert result is not None


def test_outcome_fail_safe(monkeypatch):
    """Verify _record_outcome gracefully handles exceptions (fail-safe)."""
    monkeypatch.setattr(
        "app.modules.alumni.service._check_student_has_graduated_for_alumni_record",
        lambda **kwargs: None
    )
    monkeypatch.setattr(
        "app.modules.alumni.service._check_engagement_cap",
        lambda **kwargs: None
    )
    
    created_result = {
        "id": 704,
        "student_id": 404,
        "graduation_year": 2025,
        "engagement_type": "mentoring",
        "employer": "TechCorp",
        "status": "active"
    }
    monkeypatch.setattr(
        "app.modules.alumni.service.create_entity_for_tenant",
        lambda *args, **kwargs: created_result
    )
    monkeypatch.setattr(
        "app.modules.alumni.service._emit_audit",
        lambda **kwargs: None
    )

    def mock_outcome_broken(entity_id, outcome_type, actor_id):
        raise RuntimeError("brain_core down")

    def mock_metric(tenant_id, metric, value=1):
        pass  # OK if it's called

    monkeypatch.setattr("app.modules.alumni.service._record_outcome", mock_outcome_broken)
    monkeypatch.setattr("app.modules.alumni.service._metric", mock_metric)
    monkeypatch.setattr(
        "app.modules.alumni.service.AlumniRecordSchema.model_validate",
        lambda x: {"id": 704}
    )

    request = AlumniRecordCreateSchema(
        student_id=404,
        graduation_year=2025,
        engagement_type="mentoring",
        employer="TechCorp",
        contact_email="alum@example.com",
        notes="test"
    )

    # Should NOT raise despite _record_outcome exception
    result = create_alumni_record(tenant_id=1, request=request, actor="alumni@example.com")
    assert result is not None
