"""Phase CXIII: Scholarship Service Hardening Tests.

Validates outcome + metric recording (post-persist hooks) and fail-safe behavior.
"""

from app.modules.scholarship.service import (
    create_scholarship_application,
    create_scholarship_award,
)


def test_create_scholarship_application_records_outcome_and_metric(monkeypatch):
    outcome_calls = []
    metric_calls = []

    monkeypatch.setattr(
        "app.modules.scholarship.service._record_outcome",
        lambda entity_id, outcome_type, actor_id: outcome_calls.append(
            {"entity_id": entity_id, "outcome_type": outcome_type, "actor_id": actor_id}
        ),
    )
    monkeypatch.setattr(
        "app.modules.scholarship.service._metric",
        lambda tenant_id, metric, value=1: metric_calls.append(
            {"tenant_id": tenant_id, "metric": metric, "value": value}
        ),
    )
    monkeypatch.setattr(
        "app.modules.scholarship.service._check_student_is_enrolled_for_scholarship",
        lambda **kwargs: None,
    )

    def _list_entities(entity_type, tenant_id):
        if entity_type == "scholarship_applications":
            return []
        return []

    monkeypatch.setattr("app.modules.scholarship.service.list_entities_for_tenant", _list_entities)
    monkeypatch.setattr(
        "app.modules.scholarship.service.create_entity_for_tenant",
        lambda entity_type, payload, tenant_id: {"id": 1001, **payload},
    )

    payload = {
        "student_id": "stu-1",
        "scholarship_type": "merit",
        "gpa": 3.5,
        "status": "pending",
        "requested_amount": 1000,
    }
    result = create_scholarship_application(payload, tenant_id=1)

    assert result["id"] == 1001
    assert len(outcome_calls) == 1
    assert outcome_calls[0]["entity_id"] == 1001
    assert outcome_calls[0]["outcome_type"] == "scholarship_application_created"
    assert len(metric_calls) == 1
    assert metric_calls[0]["metric"] == "scholarship_applications_created"


def test_create_scholarship_award_records_outcome_and_metric(monkeypatch):
    outcome_calls = []
    metric_calls = []

    monkeypatch.setattr(
        "app.modules.scholarship.service._record_outcome",
        lambda entity_id, outcome_type, actor_id: outcome_calls.append(
            {"entity_id": entity_id, "outcome_type": outcome_type, "actor_id": actor_id}
        ),
    )
    monkeypatch.setattr(
        "app.modules.scholarship.service._metric",
        lambda tenant_id, metric, value=1: metric_calls.append(
            {"tenant_id": tenant_id, "metric": metric, "value": value}
        ),
    )
    monkeypatch.setattr(
        "app.modules.scholarship.service.create_entity_for_tenant",
        lambda entity_type, payload, tenant_id: {"id": 1002, **payload},
    )

    payload = {
        "award_code": "A-1",
        "student_id": "stu-2",
        "scholarship_type": "merit",
        "current_gpa": 3.7,
        "gpa_threshold": 3.0,
        "status": "active",
    }
    result = create_scholarship_award(payload, tenant_id=1)

    assert result["id"] == 1002
    assert len(outcome_calls) == 1
    assert outcome_calls[0]["entity_id"] == 1002
    assert outcome_calls[0]["outcome_type"] == "scholarship_award_created"
    assert len(metric_calls) == 1
    assert metric_calls[0]["metric"] == "scholarship_awards_created"


def test_metric_fail_safe(monkeypatch):
    from app.modules.scholarship.service import _metric

    monkeypatch.setattr(
        "app.modules.scholarship.service.record_usage_event",
        lambda **kwargs: (_ for _ in ()).throw(RuntimeError("metric service down")),
    )

    _metric(tenant_id=1, metric="scholarship_applications_created")


def test_outcome_fail_safe(monkeypatch):
    import sys
    from types import ModuleType

    from app.modules.scholarship.service import _record_outcome

    fake_bc = ModuleType("app.modules.brain_core.service")

    def _raise(*args, **kwargs):
        raise RuntimeError("brain_core down")

    fake_bc.record_dispatch_outcome = _raise
    monkeypatch.setitem(sys.modules, "app.modules.brain_core", ModuleType("app.modules.brain_core"))
    monkeypatch.setitem(sys.modules, "app.modules.brain_core.service", fake_bc)

    _record_outcome(entity_id=1003, outcome_type="scholarship_award_created", actor_id="stu-3")
