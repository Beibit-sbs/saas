"""W65 domain-depth tests: housing — maintenance risk cap + alert + event."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest


# ---------------------------------------------------------------------------
# 1. Cap dict structure
# ---------------------------------------------------------------------------

def test_w65_request_type_max_active_dict_structure() -> None:
    from app.modules.housing.service import _REQUEST_TYPE_MAX_ACTIVE

    assert isinstance(_REQUEST_TYPE_MAX_ACTIVE, dict)
    assert len(_REQUEST_TYPE_MAX_ACTIVE) >= 4
    for req_type, cap in _REQUEST_TYPE_MAX_ACTIVE.items():
        assert isinstance(req_type, str) and len(req_type) > 0
        assert isinstance(cap, int) and cap > 0


# ---------------------------------------------------------------------------
# 2. Frozensets present and correct types
# ---------------------------------------------------------------------------

def test_w65_maintenance_risk_statuses_frozenset() -> None:
    from app.modules.housing.service import (
        _ACTIVE_REQUEST_STATUSES,
        _MAINTENANCE_RISK_STATUSES,
    )

    assert isinstance(_ACTIVE_REQUEST_STATUSES, frozenset)
    assert isinstance(_MAINTENANCE_RISK_STATUSES, frozenset)
    assert len(_MAINTENANCE_RISK_STATUSES) >= 1
    assert all(isinstance(s, str) for s in _MAINTENANCE_RISK_STATUSES)


# ---------------------------------------------------------------------------
# 3. Cap guard raises ValueError
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_w65_cap_guard_raises_when_exceeded(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.modules.housing import service as svc
    from app.modules.housing.schemas import HousingRequestCreateSchema

    # maintenance cap = 3; fill it up for student 5
    cap = svc._REQUEST_TYPE_MAX_ACTIVE["maintenance"]
    fake_rows = [
        {"student_id": 5, "request_type": "maintenance", "status": "submitted"}
        for _ in range(cap)
    ]
    monkeypatch.setattr(svc, "list_entities_for_tenant", lambda entity, tid: fake_rows)

    payload = HousingRequestCreateSchema(
        student_id=5,
        request_type="maintenance",
        dormitory="Block-A",
    )
    with pytest.raises(ValueError, match="max"):
        svc.create_housing_request(tenant_id=1, request=payload, actor="test")


# ---------------------------------------------------------------------------
# 4. Idempotent alert + event fired on first call
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_w65_maintenance_risk_alert_idempotent_creates_once(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.modules.housing import service as svc

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

    svc._ensure_maintenance_risk_alert_record(
        tenant_id=1,
        request_id=55,
        request_data={"student_id": 3, "dormitory": "Block-B", "request_type": "maintenance"},
    )

    assert "housing_maintenance_risk_alerts" in created_entities
    mock_publish.assert_called_once()
    call_kwargs = mock_publish.call_args.kwargs
    assert call_kwargs["event_type"] == "campus.housing.maintenance_overdue_risk_detected"
    assert call_kwargs["tenant_id"] == 1


# ---------------------------------------------------------------------------
# 5. Idempotent: no duplicate created when record already exists
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_w65_maintenance_risk_alert_skips_if_exists(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.modules.housing import service as svc

    mock_publish = MagicMock()
    monkeypatch.setattr(
        "app.platform.events.publisher.EventPublisher.publish_event",
        mock_publish,
    )

    def fake_list(entity: str, tenant_id: int) -> list[dict]:
        if entity == "housing_maintenance_risk_alerts":
            return [
                {
                    "integration_source": "maintenance_risk",
                    "source_entity_id": "55",
                }
            ]
        return []

    created_entities: list[str] = []

    def fake_create(entity: str, data: dict, tenant_id: int) -> dict:
        created_entities.append(entity)
        return {**data, "id": 10}

    monkeypatch.setattr(svc, "list_entities_for_tenant", fake_list)
    monkeypatch.setattr(svc, "create_entity_for_tenant", fake_create)

    svc._ensure_maintenance_risk_alert_record(
        tenant_id=1,
        request_id=55,
        request_data={"student_id": 3, "dormitory": "Block-B", "request_type": "maintenance"},
    )

    assert "housing_maintenance_risk_alerts" not in created_entities
    mock_publish.assert_not_called()
