"""Phase CVIII: Financial Aid Service Hardening Tests

Validates outcome + metric recording (post-persist hooks) and fail-safe exception handling.
"""
import pytest
from unittest.mock import MagicMock, patch
from decimal import Decimal

from app.modules.financial_aid.schemas import (
    FinancialAidRecordCreateSchema,
    FinancialAidRecordStatusUpdateSchema,
)
from app.modules.financial_aid.service import (
    create_financial_aid_record,
    update_financial_aid_status,
)


def test_create_financial_aid_record_records_outcome_and_metric(monkeypatch):
    """Verify create_financial_aid_record calls _record_outcome and _metric post-persist."""
    outcome_calls = []
    metric_calls = []

    def mock_record_outcome(entity_id, outcome_type, actor_id):
        outcome_calls.append({"entity_id": entity_id, "outcome_type": outcome_type, "actor_id": actor_id})

    def mock_metric(tenant_id, metric, value=1):
        metric_calls.append({"tenant_id": tenant_id, "metric": metric, "value": value})

    monkeypatch.setattr("app.modules.financial_aid.service._record_outcome", mock_record_outcome)
    monkeypatch.setattr("app.modules.financial_aid.service._metric", mock_metric)
    monkeypatch.setattr(
        "app.modules.financial_aid.service._check_student_enrollment_for_aid_creation",
        lambda **kwargs: None
    )
    monkeypatch.setattr(
        "app.modules.financial_aid.service.list_entities_for_tenant",
        lambda *args, **kwargs: []
    )
    
    created_result = {"id": 501, "student_id": 201, "aid_type": "grant", "status": "pending", "amount": 5000}
    monkeypatch.setattr(
        "app.modules.financial_aid.service.create_entity_for_tenant",
        lambda *args, **kwargs: created_result
    )
    monkeypatch.setattr(
        "app.modules.financial_aid.service._emit_audit",
        lambda **kwargs: None
    )
    monkeypatch.setattr(
        "app.modules.financial_aid.service.FinancialAidRecordCreateSchema",
        MagicMock
    )
    monkeypatch.setattr(
        "app.modules.financial_aid.service.FinancialAidRecordSchema.model_validate",
        lambda x: {"id": 501}
    )

    request = FinancialAidRecordCreateSchema(
        student_id=201,
        aid_type="grant",
        amount=Decimal("5000.00"),
        currency="USD",
        term="2026-SPRING",
        notes="test"
    )

    result = create_financial_aid_record(tenant_id=1, request=request, actor="registrar@example.com")

    # Verify outcome recorded
    assert len(outcome_calls) == 1
    assert outcome_calls[0]["entity_id"] == 501
    assert outcome_calls[0]["outcome_type"] == "financial_aid_record_created"
    assert "registrar" in outcome_calls[0]["actor_id"]

    # Verify metric recorded
    assert len(metric_calls) == 1
    assert metric_calls[0]["tenant_id"] == 1
    assert metric_calls[0]["metric"] == "financial_aid_records_created"
    assert metric_calls[0]["value"] == 1


def test_update_financial_aid_status_records_outcome_and_metric(monkeypatch):
    """Verify update_financial_aid_status calls _record_outcome and _metric post-persist."""
    outcome_calls = []
    metric_calls = []

    def mock_record_outcome(entity_id, outcome_type, actor_id):
        outcome_calls.append({"entity_id": entity_id, "outcome_type": outcome_type, "actor_id": actor_id})

    def mock_metric(tenant_id, metric, value=1):
        metric_calls.append({"tenant_id": tenant_id, "metric": metric, "value": value})

    monkeypatch.setattr("app.modules.financial_aid.service._record_outcome", mock_record_outcome)
    monkeypatch.setattr("app.modules.financial_aid.service._metric", mock_metric)
    
    existing = {
        "id": 502,
        "student_id": 202,
        "aid_type": "scholarship",
        "status": "pending",
        "amount": 10000,
        "currency": "USD",
        "term": "2026-SPRING",
        "reviewer_id": "aid-office",
        "notes": "test"
    }
    
    monkeypatch.setattr(
        "app.modules.financial_aid.service.list_entities_for_tenant",
        lambda *args, **kwargs: [existing]
    )
    monkeypatch.setattr(
        "app.modules.financial_aid.service._check_student_has_active_enrollment",
        lambda *args, **kwargs: None
    )
    
    updated_result = {**existing, "status": "approved"}
    monkeypatch.setattr(
        "app.modules.financial_aid.service.update_entity_for_tenant",
        lambda *args, **kwargs: updated_result
    )
    monkeypatch.setattr(
        "app.modules.financial_aid.service._emit_audit",
        lambda **kwargs: None
    )
    monkeypatch.setattr(
        "app.modules.financial_aid.service._emit_financial_aid_warning_signal",
        lambda **kwargs: None
    )
    monkeypatch.setattr(
        "app.modules.financial_aid.service._ensure_disbursement_record",
        lambda *args, **kwargs: None
    )
    monkeypatch.setattr(
        "app.modules.financial_aid.service.FinancialAidRecordSchema.model_validate",
        lambda x: {"id": 502, "status": "approved"}
    )

    request = FinancialAidRecordStatusUpdateSchema(status="approved")

    result = update_financial_aid_status(
        tenant_id=1, record_id=502, request=request, actor="registrar@example.com"
    )

    # Verify outcome recorded
    assert len(outcome_calls) == 1
    assert outcome_calls[0]["entity_id"] == 502
    assert outcome_calls[0]["outcome_type"] == "financial_aid_status_updated"
    assert "registrar" in outcome_calls[0]["actor_id"]

    # Verify metric recorded
    assert len(metric_calls) == 1
    assert metric_calls[0]["tenant_id"] == 1
    assert metric_calls[0]["metric"] == "financial_aid_records_updated"
    assert metric_calls[0]["value"] == 1


def test_metric_fail_safe(monkeypatch):
    """Verify _metric gracefully handles exceptions (fail-safe)."""
    monkeypatch.setattr(
        "app.modules.financial_aid.service._check_student_enrollment_for_aid_creation",
        lambda **kwargs: None
    )
    monkeypatch.setattr(
        "app.modules.financial_aid.service.list_entities_for_tenant",
        lambda *args, **kwargs: []
    )
    
    created_result = {"id": 503, "student_id": 203, "aid_type": "grant", "status": "pending", "amount": 3000}
    monkeypatch.setattr(
        "app.modules.financial_aid.service.create_entity_for_tenant",
        lambda *args, **kwargs: created_result
    )
    monkeypatch.setattr(
        "app.modules.financial_aid.service._emit_audit",
        lambda **kwargs: None
    )

    def mock_record_outcome(entity_id, outcome_type, actor_id):
        pass  # OK if it's called

    def mock_metric_broken(tenant_id, metric, value=1):
        raise RuntimeError("metric service down")

    monkeypatch.setattr("app.modules.financial_aid.service._record_outcome", mock_record_outcome)
    monkeypatch.setattr("app.modules.financial_aid.service._metric", mock_metric_broken)
    monkeypatch.setattr(
        "app.modules.financial_aid.service.FinancialAidRecordSchema.model_validate",
        lambda x: {"id": 503}
    )

    request = FinancialAidRecordCreateSchema(
        student_id=203,
        aid_type="grant",
        amount=Decimal("3000.00"),
        currency="USD",
        term="2026-SPRING",
        notes="test"
    )

    # Should NOT raise despite _metric exception
    result = create_financial_aid_record(tenant_id=1, request=request, actor="registrar@example.com")
    assert result is not None


def test_outcome_fail_safe(monkeypatch):
    """Verify _record_outcome gracefully handles exceptions (fail-safe)."""
    monkeypatch.setattr(
        "app.modules.financial_aid.service._check_student_enrollment_for_aid_creation",
        lambda **kwargs: None
    )
    monkeypatch.setattr(
        "app.modules.financial_aid.service.list_entities_for_tenant",
        lambda *args, **kwargs: []
    )
    
    created_result = {"id": 504, "student_id": 204, "aid_type": "grant", "status": "pending", "amount": 4000}
    monkeypatch.setattr(
        "app.modules.financial_aid.service.create_entity_for_tenant",
        lambda *args, **kwargs: created_result
    )
    monkeypatch.setattr(
        "app.modules.financial_aid.service._emit_audit",
        lambda **kwargs: None
    )

    def mock_outcome_broken(entity_id, outcome_type, actor_id):
        raise RuntimeError("brain_core down")

    def mock_metric(tenant_id, metric, value=1):
        pass  # OK if it's called

    monkeypatch.setattr("app.modules.financial_aid.service._record_outcome", mock_outcome_broken)
    monkeypatch.setattr("app.modules.financial_aid.service._metric", mock_metric)
    monkeypatch.setattr(
        "app.modules.financial_aid.service.FinancialAidRecordSchema.model_validate",
        lambda x: {"id": 504}
    )

    request = FinancialAidRecordCreateSchema(
        student_id=204,
        aid_type="grant",
        amount=Decimal("4000.00"),
        currency="USD",
        term="2026-SPRING",
        notes="test"
    )

    # Should NOT raise despite _record_outcome exception
    result = create_financial_aid_record(tenant_id=1, request=request, actor="registrar@example.com")
    assert result is not None
