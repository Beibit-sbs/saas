"""W68 domain-depth tests: advising — no-show risk alert + event."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest


# ---------------------------------------------------------------------------
# 1. Cap dict structure
# ---------------------------------------------------------------------------

def test_w68_session_type_max_active_dict_structure() -> None:
    from app.modules.advising.service import _SESSION_TYPE_MAX_ACTIVE

    assert isinstance(_SESSION_TYPE_MAX_ACTIVE, dict)
    assert len(_SESSION_TYPE_MAX_ACTIVE) >= 3
    for session_type, cap in _SESSION_TYPE_MAX_ACTIVE.items():
        assert isinstance(session_type, str) and len(session_type) > 0
        assert isinstance(cap, int) and cap > 0


# ---------------------------------------------------------------------------
# 2. No-show risk frozenset present and correct
# ---------------------------------------------------------------------------

def test_w68_no_show_risk_statuses_frozenset() -> None:
    from app.modules.advising.service import (
        _ACTIVE_SESSION_STATUSES,
        _NO_SHOW_RISK_STATUSES,
    )

    assert isinstance(_ACTIVE_SESSION_STATUSES, frozenset)
    assert isinstance(_NO_SHOW_RISK_STATUSES, frozenset)
    assert len(_NO_SHOW_RISK_STATUSES) >= 1
    assert "no_show" in _NO_SHOW_RISK_STATUSES
    assert all(isinstance(s, str) for s in _NO_SHOW_RISK_STATUSES)


# ---------------------------------------------------------------------------
# 3. Cap guard raises ValueError when sessions exceed cap
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_w68_cap_guard_raises_when_exceeded(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.modules.advising import service as svc
    from app.modules.advising.schemas import AdvisingSessionCreateSchema
    monkeypatch.setattr(svc, "_check_advisor_is_active_faculty_for_advising", lambda *a, **kw: None)
    monkeypatch.setattr(svc, "_check_student_has_active_enrollment_for_advising", lambda *a, **kw: None)

    cap = svc._SESSION_TYPE_MAX_ACTIVE["personal"]
    fake_rows = [
        {"session_type": "personal", "status": "scheduled"}
        for _ in range(cap)
    ]
    monkeypatch.setattr(svc, "list_entities_for_tenant", lambda entity, tid: fake_rows)

    payload = AdvisingSessionCreateSchema(
        student_id=1,
        advisor_id="ADV-1",
        session_type="personal",
    )
    with pytest.raises(ValueError, match="cap"):
        svc.create_advising_session(tenant_id=1, request=payload, actor="test")


# ---------------------------------------------------------------------------
# 4. Idempotent no-show risk alert + event fired on first call
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_w68_no_show_risk_alert_idempotent_creates_once(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.modules.advising import service as svc

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
        return {**data, "id": 55}

    monkeypatch.setattr(svc, "list_entities_for_tenant", fake_list)
    monkeypatch.setattr(svc, "create_entity_for_tenant", fake_create)

    svc._ensure_no_show_risk_alert(
        tenant_id=1,
        session_id=99,
        session_data={"student_id": 42, "advisor_id": "ADV-1", "session_type": "academic"},
    )

    assert "advising_no_show_risk_alerts" in created_entities
    mock_publish.assert_called_once()
    call_kwargs = mock_publish.call_args.kwargs
    assert call_kwargs["event_type"] == "campus.advising.no_show_risk_detected"
    assert call_kwargs["tenant_id"] == 1


# ---------------------------------------------------------------------------
# 5. Idempotent: no duplicate created when alert already exists
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_w68_no_show_risk_alert_skips_if_exists(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.modules.advising import service as svc

    mock_publish = MagicMock()
    monkeypatch.setattr(
        "app.platform.events.publisher.EventPublisher.publish_event",
        mock_publish,
    )
    created_entities: list[str] = []

    existing = [
        {
            "integration_source": "advising_no_show_queue",
            "source_entity_id": "99",
            "alert_status": "open",
        }
    ]

    def fake_list(entity: str, tenant_id: int) -> list[dict]:
        return existing if entity == "advising_no_show_risk_alerts" else []

    def fake_create(entity: str, data: dict, tenant_id: int) -> dict:
        created_entities.append(entity)
        return {**data, "id": 56}

    monkeypatch.setattr(svc, "list_entities_for_tenant", fake_list)
    monkeypatch.setattr(svc, "create_entity_for_tenant", fake_create)

    svc._ensure_no_show_risk_alert(
        tenant_id=1,
        session_id=99,
        session_data={"student_id": 42, "advisor_id": "ADV-1", "session_type": "academic"},
    )

    assert created_entities == []
    mock_publish.assert_not_called()
