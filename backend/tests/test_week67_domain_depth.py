"""W67 domain-depth tests: delinquency_collections — legal escalation risk cap + alert + event."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest


# ---------------------------------------------------------------------------
# 1. Cap dict structure
# ---------------------------------------------------------------------------

def test_w67_escalation_stage_max_active_dict_structure() -> None:
    from app.modules.delinquency_collections.service import _ESCALATION_STAGE_MAX_ACTIVE

    assert isinstance(_ESCALATION_STAGE_MAX_ACTIVE, dict)
    assert len(_ESCALATION_STAGE_MAX_ACTIVE) >= 3
    for stage, cap in _ESCALATION_STAGE_MAX_ACTIVE.items():
        assert isinstance(stage, str) and len(stage) > 0
        assert isinstance(cap, int) and cap > 0


# ---------------------------------------------------------------------------
# 2. Legal risk frozenset present and correct type
# ---------------------------------------------------------------------------

def test_w67_legal_risk_stages_frozenset() -> None:
    from app.modules.delinquency_collections.service import (
        _ACTIVE_STATUSES_DC,
        _LEGAL_RISK_STAGES,
    )

    assert isinstance(_ACTIVE_STATUSES_DC, frozenset)
    assert isinstance(_LEGAL_RISK_STAGES, frozenset)
    assert len(_LEGAL_RISK_STAGES) >= 1
    assert "legal" in _LEGAL_RISK_STAGES
    assert all(isinstance(s, str) for s in _LEGAL_RISK_STAGES)


# ---------------------------------------------------------------------------
# 3. Cap guard raises ValueError when active records exceed cap
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_w67_cap_guard_raises_when_exceeded(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.modules.delinquency_collections import service as svc
    from app.modules.delinquency_collections.schemas import DelinquencyRecordCreateSchema

    cap = svc._ESCALATION_STAGE_MAX_ACTIVE["stage_3"]
    fake_rows = [
        {"student_id": "STU-1", "escalation_stage": "stage_3", "status": "open"}
        for _ in range(cap)
    ]
    monkeypatch.setattr(svc, "list_entities_for_tenant", lambda entity, tid: fake_rows)

    payload = DelinquencyRecordCreateSchema(
        student_id="STU-1",
        invoice_code="INV-99",
        amount_due=500.0,
        days_overdue=30,
        escalation_stage="stage_3",
        status="open",
    )
    with pytest.raises(ValueError, match="already has"):
        svc.create_delinquency_record(tenant_id=1, request=payload, actor="test")


# ---------------------------------------------------------------------------
# 4. Idempotent legal escalation risk alert + event fired on first call
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_w67_legal_escalation_risk_alert_idempotent_creates_once(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.modules.delinquency_collections import service as svc

    created_entities: list[str] = []
    mock_publish = MagicMock()

    monkeypatch.setattr(
        "app.platform.events.publisher.EventPublisher.publish_event",
        mock_publish,
    )

    def fake_list(entity: str, tenant_id: int) -> list[dict]:
        return []

    def fake_create(entity: str, data: dict, tenant_id: int) -> dict:
        created_entities.append(entity)
        return {**data, "id": 77}

    monkeypatch.setattr(svc, "list_entities_for_tenant", fake_list)
    monkeypatch.setattr(svc, "create_entity_for_tenant", fake_create)

    svc._ensure_legal_escalation_risk_alert(
        tenant_id=1,
        record_id=101,
        record_data={"student_id": "STU-77", "escalation_stage": "legal", "amount_due": 1200.0},
    )

    assert "delinquency_legal_escalation_alerts" in created_entities
    mock_publish.assert_called_once()
    call_kwargs = mock_publish.call_args.kwargs
    assert call_kwargs["event_type"] == "campus.delinquency_collections.legal_escalation_risk_detected"
    assert call_kwargs["tenant_id"] == 1


# ---------------------------------------------------------------------------
# 5. Idempotent: no duplicate created when alert record already exists
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_w67_legal_escalation_risk_alert_skips_if_exists(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.modules.delinquency_collections import service as svc

    mock_publish = MagicMock()
    monkeypatch.setattr(
        "app.platform.events.publisher.EventPublisher.publish_event",
        mock_publish,
    )
    created_entities: list[str] = []

    existing = [
        {
            "integration_source": "delinquency_legal_queue",
            "source_entity_id": "101",
            "alert_status": "open",
        }
    ]

    def fake_list(entity: str, tenant_id: int) -> list[dict]:
        return existing if entity == "delinquency_legal_escalation_alerts" else []

    def fake_create(entity: str, data: dict, tenant_id: int) -> dict:
        created_entities.append(entity)
        return {**data, "id": 78}

    monkeypatch.setattr(svc, "list_entities_for_tenant", fake_list)
    monkeypatch.setattr(svc, "create_entity_for_tenant", fake_create)

    svc._ensure_legal_escalation_risk_alert(
        tenant_id=1,
        record_id=101,
        record_data={"student_id": "STU-77", "escalation_stage": "legal", "amount_due": 1200.0},
    )

    assert created_entities == []
    mock_publish.assert_not_called()
