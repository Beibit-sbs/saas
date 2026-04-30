"""W52 depth tests - research: grant cap + delay alerts."""
from __future__ import annotations

import pytest


def test_research_grant_status_cap_dict_structure():
    from app.modules.research.service import _RESEARCH_GRANT_STATUS_MAX_ACTIVE

    assert isinstance(_RESEARCH_GRANT_STATUS_MAX_ACTIVE, dict)
    assert _RESEARCH_GRANT_STATUS_MAX_ACTIVE["planned"] == 250
    assert _RESEARCH_GRANT_STATUS_MAX_ACTIVE["active"] == 180
    assert _RESEARCH_GRANT_STATUS_MAX_ACTIVE["submitted"] == 120
    assert _RESEARCH_GRANT_STATUS_MAX_ACTIVE["delayed"] == 80
    assert all(isinstance(v, int) and v > 0 for v in _RESEARCH_GRANT_STATUS_MAX_ACTIVE.values())


def test_active_grant_statuses_and_delay_risk_statuses():
    from app.modules.research.service import (
        _ACTIVE_RESEARCH_GRANT_STATUSES,
        _GRANT_DELAY_RISK_STATUSES,
    )

    assert isinstance(_ACTIVE_RESEARCH_GRANT_STATUSES, frozenset)
    assert "planned" in _ACTIVE_RESEARCH_GRANT_STATUSES
    assert "active" in _ACTIVE_RESEARCH_GRANT_STATUSES
    assert "submitted" in _ACTIVE_RESEARCH_GRANT_STATUSES
    assert "closed" not in _ACTIVE_RESEARCH_GRANT_STATUSES

    assert isinstance(_GRANT_DELAY_RISK_STATUSES, frozenset)
    assert "delayed" in _GRANT_DELAY_RISK_STATUSES


def test_create_research_grant_raises_when_cap_reached(monkeypatch):
    from app.modules.research import service as svc
    from app.modules.research.schemas import ResearchGrantCreateSchema

    monkeypatch.setattr(
        svc,
        "list_entities_for_tenant",
        lambda entity_type, tid: (
            [{"status": "active"} for _ in range(180)]
            if entity_type == "research_grants"
            else []
        ),
    )
    monkeypatch.setattr(
        svc,
        "create_entity_for_tenant",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("create must not be called")),
    )

    payload = ResearchGrantCreateSchema(
        grant_code="RG-52-001",
        title="Distributed Campus Learning Analytics",
        pi_faculty_id="FAC-7",
        deadline="2026-12-31",
        funding_amount=250000,
        status="active",
        sponsor_notes="Consortium-backed study with monthly checkpoints.",
    )

    with pytest.raises(ValueError, match="active cap reached"):
        svc.create_research_grant(tenant_id=7, request=payload, actor="u-1")


def test_ensure_grant_delay_alert_record_is_idempotent(monkeypatch):
    from app.modules.research import service as svc

    created: list[dict] = []

    def fake_list(entity_type, tid):
        if entity_type == "research_grant_delay_alerts":
            return [{"integration_source": "research_grant_delay_queue", "source_entity_id": "52"}]
        return []

    def fake_create(entity_type, payload, tid):
        created.append(payload)
        return {**payload, "id": 1}

    monkeypatch.setattr(svc, "list_entities_for_tenant", fake_list)
    monkeypatch.setattr(svc, "create_entity_for_tenant", fake_create)
    monkeypatch.setattr(
        "app.platform.events.publisher.EventPublisher.publish_event",
        lambda self, **kwargs: None,
    )

    svc._ensure_grant_delay_alert_record(
        tenant_id=7,
        grant_id=52,
        grant_data={"grant_code": "RG-52-001", "pi_faculty_id": "FAC-7", "status": "delayed"},
    )

    assert len(created) == 0
