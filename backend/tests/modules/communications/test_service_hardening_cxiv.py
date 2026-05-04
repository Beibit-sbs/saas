"""Phase CXIV: Communications Service Hardening Tests.

Validates outcome + metric recording (post-persist hooks) and fail-safe behavior.
"""

from app.modules.communications.service import create_message


def test_create_message_records_outcome_and_metric(monkeypatch):
    outcome_calls = []
    metric_calls = []

    monkeypatch.setattr(
        "app.modules.communications.service._record_outcome",
        lambda entity_id, outcome_type, actor_id="system": outcome_calls.append(
            {"entity_id": entity_id, "outcome_type": outcome_type, "actor_id": actor_id}
        ),
    )
    monkeypatch.setattr(
        "app.modules.communications.service._metric",
        lambda tenant_id, metric, value=1: metric_calls.append(
            {"tenant_id": tenant_id, "metric": metric, "value": value}
        ),
    )

    def _list_entities(entity_type, tenant_id):
        if entity_type == "communication_messages":
            return []
        return []

    monkeypatch.setattr("app.modules.communications.service.list_entities_for_tenant", _list_entities)
    monkeypatch.setattr(
        "app.modules.communications.service.create_entity_for_tenant",
        lambda entity_type, payload, tenant_id: {"id": 1401, **payload},
    )

    payload = {
        "message_code": "MSG-CXIV-001",
        "title": "Welcome",
        "message_type": "announcement",
        "target_audience": "all",
        "status": "draft",
        "recipients_count": 100,
    }
    result = create_message(payload, tenant_id=1)

    assert result["id"] == 1401
    assert len(outcome_calls) == 1
    assert outcome_calls[0]["entity_id"] == 1401
    assert outcome_calls[0]["outcome_type"] == "communication_message_created"
    assert len(metric_calls) == 1
    assert metric_calls[0]["metric"] == "communication_messages_created"


def test_create_message_records_hooks_when_large_audience(monkeypatch):
    outcome_calls = []
    metric_calls = []

    monkeypatch.setattr(
        "app.modules.communications.service._record_outcome",
        lambda entity_id, outcome_type, actor_id="system": outcome_calls.append(
            {"entity_id": entity_id, "outcome_type": outcome_type, "actor_id": actor_id}
        ),
    )
    monkeypatch.setattr(
        "app.modules.communications.service._metric",
        lambda tenant_id, metric, value=1: metric_calls.append(
            {"tenant_id": tenant_id, "metric": metric, "value": value}
        ),
    )

    def _list_entities(entity_type, tenant_id):
        if entity_type in {
            "communication_messages",
            "communication_broadcast_audits",
            "communication_broadcast_risk_alerts",
        }:
            return []
        return []

    monkeypatch.setattr("app.modules.communications.service.list_entities_for_tenant", _list_entities)
    monkeypatch.setattr(
        "app.modules.communications.service.create_entity_for_tenant",
        lambda entity_type, payload, tenant_id: {"id": 1402, **payload},
    )
    monkeypatch.setattr(
        "app.modules.communications.service.EventPublisher.publish_event",
        lambda *args, **kwargs: None,
    )

    payload = {
        "message_code": "MSG-CXIV-002",
        "title": "Emergency",
        "message_type": "emergency",
        "target_audience": "all",
        "status": "sent",
        "recipients_count": 800,
    }
    result = create_message(payload, tenant_id=1)

    assert result["id"] == 1402
    assert len(outcome_calls) == 1
    assert outcome_calls[0]["outcome_type"] == "communication_message_created"
    assert len(metric_calls) == 1
    assert metric_calls[0]["metric"] == "communication_messages_created"


def test_metric_fail_safe(monkeypatch):
    from app.modules.communications.service import _metric

    monkeypatch.setattr(
        "app.modules.communications.service.record_usage_event",
        lambda **kwargs: (_ for _ in ()).throw(RuntimeError("metric service down")),
    )

    _metric(tenant_id=1, metric="communication_messages_created")


def test_outcome_fail_safe(monkeypatch):
    import sys
    from types import ModuleType

    from app.modules.communications.service import _record_outcome

    fake_bc = ModuleType("app.modules.brain_core.service")

    def _raise(*args, **kwargs):
        raise RuntimeError("brain_core down")

    fake_bc.record_dispatch_outcome = _raise
    monkeypatch.setitem(sys.modules, "app.modules.brain_core", ModuleType("app.modules.brain_core"))
    monkeypatch.setitem(sys.modules, "app.modules.brain_core.service", fake_bc)

    _record_outcome(entity_id=1403, outcome_type="communication_message_created", actor_id="ops-1")
