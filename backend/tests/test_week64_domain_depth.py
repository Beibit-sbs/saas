"""W64 domain-depth tests: financial_aid — disbursement risk cap + alert + event."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest


# ---------------------------------------------------------------------------
# 1. Cap dict structure
# ---------------------------------------------------------------------------

def test_w64_aid_type_max_active_dict_structure() -> None:
    from app.modules.financial_aid.service import _AID_TYPE_MAX_ACTIVE

    assert isinstance(_AID_TYPE_MAX_ACTIVE, dict)
    assert len(_AID_TYPE_MAX_ACTIVE) >= 4
    for aid_type, cap in _AID_TYPE_MAX_ACTIVE.items():
        assert isinstance(aid_type, str) and len(aid_type) > 0
        assert isinstance(cap, int) and cap > 0


# ---------------------------------------------------------------------------
# 2. Frozensets present and correct types
# ---------------------------------------------------------------------------

def test_w64_disbursement_risk_statuses_frozenset() -> None:
    from app.modules.financial_aid.service import (
        _ACTIVE_AID_STATUSES,
        _DISBURSEMENT_RISK_STATUSES,
    )

    assert isinstance(_ACTIVE_AID_STATUSES, frozenset)
    assert isinstance(_DISBURSEMENT_RISK_STATUSES, frozenset)
    assert len(_DISBURSEMENT_RISK_STATUSES) >= 1
    assert all(isinstance(s, str) for s in _DISBURSEMENT_RISK_STATUSES)


# ---------------------------------------------------------------------------
# 3. Cap guard raises ValueError
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_w64_cap_guard_raises_when_exceeded(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.modules.financial_aid import service as svc
    from app.modules.financial_aid.schemas import FinancialAidRecordCreateSchema
    monkeypatch.setattr(svc, "_check_student_enrollment_for_aid_creation", lambda *a, **kw: None)

    # Build fake active records filling the cap for "stipend" (cap=300)
    cap = svc._AID_TYPE_MAX_ACTIVE["stipend"]
    fake_rows = [
        {"aid_type": "stipend", "status": "pending"}
        for _ in range(cap)
    ]
    monkeypatch.setattr(svc, "list_entities_for_tenant", lambda entity, tid: fake_rows)

    payload = FinancialAidRecordCreateSchema(
        student_id=1,
        aid_type="stipend",
        amount=500.0,
        term="2026-S1",
    )
    with pytest.raises(ValueError, match="cap"):
        svc.create_financial_aid_record(tenant_id=1, request=payload, actor="test")


# ---------------------------------------------------------------------------
# 4. Idempotent alert + event fired on first call
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_w64_disbursement_risk_alert_idempotent_creates_once(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.modules.financial_aid import service as svc

    created_entities: list[str] = []
    mock_publish = MagicMock()

    monkeypatch.setattr(
        "app.platform.events.publisher.EventPublisher.publish_event",
        mock_publish,
    )

    def fake_list(entity: str, tenant_id: int) -> list[dict]:
        if entity == "financial_aid_disbursement_risk_alerts":
            return []  # none yet
        return []

    def fake_create(entity: str, data: dict, tenant_id: int) -> dict:
        created_entities.append(entity)
        return {**data, "id": 42}

    monkeypatch.setattr(svc, "list_entities_for_tenant", fake_list)
    monkeypatch.setattr(svc, "create_entity_for_tenant", fake_create)

    svc._ensure_disbursement_risk_alert_record(
        tenant_id=1,
        record_id=99,
        aid_data={"student_id": 7, "aid_type": "grant", "amount": 8000.0, "term": "2026-S1"},
    )

    assert "financial_aid_disbursement_risk_alerts" in created_entities
    mock_publish.assert_called_once()
    call_kwargs = mock_publish.call_args.kwargs
    assert call_kwargs["event_type"] == "campus.financial_aid.disbursement_risk_detected"
    assert call_kwargs["tenant_id"] == 1


# ---------------------------------------------------------------------------
# 5. Idempotent: no duplicate created when record already exists
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_w64_disbursement_risk_alert_skips_if_exists(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.modules.financial_aid import service as svc

    mock_publish = MagicMock()
    monkeypatch.setattr(
        "app.platform.events.publisher.EventPublisher.publish_event",
        mock_publish,
    )

    def fake_list(entity: str, tenant_id: int) -> list[dict]:
        if entity == "financial_aid_disbursement_risk_alerts":
            return [
                {
                    "integration_source": "disbursement_risk",
                    "source_entity_id": "99",
                }
            ]
        return []

    created_entities: list[str] = []

    def fake_create(entity: str, data: dict, tenant_id: int) -> dict:
        created_entities.append(entity)
        return {**data, "id": 10}

    monkeypatch.setattr(svc, "list_entities_for_tenant", fake_list)
    monkeypatch.setattr(svc, "create_entity_for_tenant", fake_create)

    svc._ensure_disbursement_risk_alert_record(
        tenant_id=1,
        record_id=99,
        aid_data={"student_id": 7, "aid_type": "grant", "amount": 8000.0, "term": "2026-S1"},
    )

    assert "financial_aid_disbursement_risk_alerts" not in created_entities
    mock_publish.assert_not_called()
