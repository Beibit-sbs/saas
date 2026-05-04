"""Phase CXII: Internship Service Hardening Tests

Validates outcome + metric recording (post-persist hooks) and fail-safe exception handling.
"""
import pytest
from unittest.mock import MagicMock

from app.modules.internship.service import (
    create_posting,
    create_contract,
)


def test_create_posting_records_outcome_and_metric(monkeypatch):
    """Verify create_posting calls _record_outcome and _metric post-persist."""
    outcome_calls = []
    metric_calls = []

    monkeypatch.setattr("app.modules.internship.service._record_outcome",
        lambda entity_id, outcome_type, actor_id: outcome_calls.append(
            {"entity_id": entity_id, "outcome_type": outcome_type, "actor_id": actor_id}))
    monkeypatch.setattr("app.modules.internship.service._metric",
        lambda tenant_id, metric, value=1: metric_calls.append(
            {"tenant_id": tenant_id, "metric": metric, "value": value}))

    monkeypatch.setattr(
        "app.modules.internship.service.create_entity_for_tenant",
        lambda *args, **kwargs: {"id": 901}
    )

    result = create_posting(
        tenant_id=1, company_id="corp-1", title="Dev Intern", description="Python", slots=2
    )

    assert result["posting_id"] == 901
    assert result["status"] == "OPEN"
    assert len(outcome_calls) == 1
    assert outcome_calls[0]["entity_id"] == 901
    assert outcome_calls[0]["outcome_type"] == "internship_posting_created"
    assert len(metric_calls) == 1
    assert metric_calls[0]["tenant_id"] == 1
    assert metric_calls[0]["metric"] == "internship_postings_created"


def test_create_contract_records_outcome_and_metric(monkeypatch):
    """Verify create_contract calls _record_outcome and _metric post-persist."""
    outcome_calls = []
    metric_calls = []

    monkeypatch.setattr("app.modules.internship.service._record_outcome",
        lambda entity_id, outcome_type, actor_id: outcome_calls.append(
            {"entity_id": entity_id, "outcome_type": outcome_type, "actor_id": actor_id}))
    monkeypatch.setattr("app.modules.internship.service._metric",
        lambda tenant_id, metric, value=1: metric_calls.append(
            {"tenant_id": tenant_id, "metric": metric, "value": value}))

    monkeypatch.setattr(
        "app.modules.internship.service.create_entity_for_tenant",
        lambda *args, **kwargs: {"id": 902}
    )

    result = create_contract(
        tenant_id=1, application_id="app-1", student_id="stu-1",
        company_id="corp-1", start_date="2026-06-01", end_date="2026-09-01"
    )

    assert result["contract_id"] == 902
    assert result["status"] == "DRAFT"
    assert len(outcome_calls) == 1
    assert outcome_calls[0]["entity_id"] == 902
    assert outcome_calls[0]["outcome_type"] == "internship_contract_created"
    assert len(metric_calls) == 1
    assert metric_calls[0]["tenant_id"] == 1
    assert metric_calls[0]["metric"] == "internship_contracts_created"


def test_metric_fail_safe(monkeypatch):
    """Verify _metric gracefully handles exceptions (fail-safe)."""
    from app.modules.internship.service import _metric

    monkeypatch.setattr(
        "app.modules.internship.service.record_usage_event",
        lambda **kwargs: (_ for _ in ()).throw(RuntimeError("metric service down"))
    )
    # Should not raise
    _metric(tenant_id=1, metric="internship_postings_created")


def test_outcome_fail_safe(monkeypatch):
    """Verify _record_outcome gracefully handles exceptions (fail-safe)."""
    import sys
    from types import ModuleType
    from app.modules.internship.service import _record_outcome

    fake_bc = ModuleType("app.modules.brain_core.service")
    def _raise(*a, **k):
        raise RuntimeError("brain_core down")
    fake_bc.record_dispatch_outcome = _raise
    monkeypatch.setitem(sys.modules, "app.modules.brain_core", ModuleType("app.modules.brain_core"))
    monkeypatch.setitem(sys.modules, "app.modules.brain_core.service", fake_bc)

    # Should not raise
    _record_outcome(entity_id=901, outcome_type="internship_posting_created", actor_id="corp-1")
