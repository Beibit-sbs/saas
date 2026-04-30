"""W48 domain depth tests — faculty contracts cap + termination alert."""
from unittest.mock import patch

import pytest

from app.modules.faculty.service import (
    _ACTIVE_CONTRACT_STATUSES,
    _CONTRACT_TERMINATION_RISK_STATUSES,
    _FACULTY_CONTRACT_STATUS_MAX_ACTIVE,
    _ensure_contract_termination_alert_record,
    create_faculty_contract,
)


def test_faculty_contract_status_cap_dict_structure():
    assert "active" in _FACULTY_CONTRACT_STATUS_MAX_ACTIVE
    assert "draft" in _FACULTY_CONTRACT_STATUS_MAX_ACTIVE
    assert "pending" in _FACULTY_CONTRACT_STATUS_MAX_ACTIVE
    assert _FACULTY_CONTRACT_STATUS_MAX_ACTIVE["active"] >= 100
    assert all(isinstance(v, int) for v in _FACULTY_CONTRACT_STATUS_MAX_ACTIVE.values())


def test_active_contract_statuses_and_termination_risk_statuses():
    assert "active" in _ACTIVE_CONTRACT_STATUSES
    assert "draft" in _ACTIVE_CONTRACT_STATUSES
    assert "pending" in _ACTIVE_CONTRACT_STATUSES
    assert "terminated" in _CONTRACT_TERMINATION_RISK_STATUSES
    # Risk statuses must not overlap with active statuses
    assert _ACTIVE_CONTRACT_STATUSES.isdisjoint(_CONTRACT_TERMINATION_RISK_STATUSES)


def test_create_faculty_contract_raises_when_cap_reached():
    tid = 42
    cap = _FACULTY_CONTRACT_STATUS_MAX_ACTIVE.get("pending", 150)
    # Simulate cap-many existing active contracts (all "pending")
    fake_existing = [{"status": "pending"} for _ in range(cap)]
    # Simulate faculty exists
    fake_faculty = [{"faculty_id": "FAC001"}]

    def fake_list(entity_type, tenant_id):
        if entity_type == "faculty":
            return fake_faculty
        if entity_type == "faculty_contracts":
            return fake_existing
        return []

    with patch("app.modules.faculty.service.list_entities_for_tenant", side_effect=fake_list):
        with pytest.raises(ValueError, match="cap reached"):
            create_faculty_contract(
                {"faculty_id": "FAC001", "contract_type": "full_time", "start_date": "2026-01-01",
                 "fte_ratio": 1.0, "max_credit_hours": 12, "status": "pending"},
                tid,
            )


def test_ensure_contract_termination_alert_record_is_idempotent():
    tid = 10
    contract_id = 77
    existing_alert = {
        "integration_source": "faculty_contract_termination_queue",
        "source_entity_id": str(contract_id),
        "alert_status": "open",
    }
    created: list[dict] = []

    def fake_list(entity_type, tenant_id):
        if entity_type == "faculty_contract_termination_alerts":
            return [existing_alert]
        return []

    def fake_create(entity_type, payload, tenant_id):
        created.append(payload)
        return payload

    with patch("app.modules.faculty.service.list_entities_for_tenant", side_effect=fake_list):
        with patch("app.modules.faculty.service.create_entity_for_tenant", side_effect=fake_create):
            _ensure_contract_termination_alert_record(contract_id, tid)

    assert len(created) == 0
